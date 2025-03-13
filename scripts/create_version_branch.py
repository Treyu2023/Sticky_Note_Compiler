import os
import subprocess
import json
import sys
import re
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('c:', 'LocalStorage', 'Sticky_Note_Compiler', 'logs', 'version_control.log'), mode='a')
    ]
)
logger = logging.getLogger('version_control')

def get_project_dir():
    """Return the project directory path."""
    return os.path.join('c:', 'LocalStorage', 'Sticky_Note_Compiler')

def get_config_path():
    """Return the configuration file path."""
    return os.path.join(get_project_dir(), 'config', 'repo_config.json')

def get_version_file_path():
    """Return the version file path."""
    return os.path.join(get_project_dir(), 'version.json')

def load_config():
    """Load repository configuration with enhanced error handling."""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}. Please run init_repo.py first.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config_data = f.read()
            
        # Check if file is empty
        if not config_data.strip():
            logger.error("Config file is empty")
            raise ValueError("Config file is empty")
            
        config = json.loads(config_data)
        
        # Validate essential configuration fields
        if 'repository' not in config:
            logger.error("Missing 'repository' section in config file")
            raise ValueError("Missing 'repository' section in config file")
            
        # Ensure current_version exists with default value if not
        if 'current_version' not in config['repository']:
            logger.warning("'current_version' not found in config, using default '0.1.0'")
            config['repository']['current_version'] = '0.1.0'
            save_config(config)
            
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        logger.debug(f"Config file content: {config_data[:100]}...")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        sys.exit(1)

def save_config(config):
    """Save repository configuration with error handling."""
    config_path = get_config_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Validate config structure before saving
        if not isinstance(config, dict) or 'repository' not in config:
            raise ValueError("Invalid configuration structure")
            
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        logger.debug(f"Configuration saved successfully to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config file: {e}")
        sys.exit(1)

def save_version_file(version_info):
    """Save version information to version file with error handling."""
    version_file = get_version_file_path()
    
    try:
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=4)
            
        logger.debug(f"Version info saved successfully to {version_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving version file: {e}")
        return False

def run_git_command(command, error_message=None):
    """Run a git command with proper error handling."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        msg = error_message or f"Git command failed: {' '.join(command)}"
        logger.error(f"{msg}: {e}")
        logger.error(f"Git error output: {e.stderr}")
        raise

def increment_version(version, level='patch'):
    """Increment version number at the specified level."""
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        logger.warning(f"Invalid version format: {version}. Using 0.1.0 instead.")
        return "0.1.0"
    
    major, minor, patch = map(int, version.split('.'))
    
    if level == 'major':
        return f"{major + 1}.0.0"
    elif level == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"

def create_version_branch(level='patch', prefix='v', description=None):
    """Create a new branch with an incremented version number."""
    project_dir = get_project_dir()
    os.chdir(project_dir)
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(project_dir, 'logs'), exist_ok=True)
    
    # Ensure we're in a git repository
    if not os.path.exists(os.path.join(project_dir, '.git')):
        logger.error("Not a git repository. Please run init_repo.py first.")
        sys.exit(1)
    
    try:
        # Check git status before proceeding
        status = run_git_command(['git', 'status', '--porcelain'])
        if status:
            logger.warning("Working directory is not clean. Uncommitted changes might be included in version commit.")
            
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        current_version = config['repository'].get('current_version', '0.1.0')
        logger.info(f"Current version: {current_version}")
        
        # Increment version based on specified level
        new_version = increment_version(current_version, level)
        logger.info(f"New version: {new_version}")
        
        # Branch name includes version and optional description
        branch_name = f"{prefix}{new_version}"
        if description:
            # Replace spaces with dashes and remove special characters for branch name
            safe_description = re.sub(r'[^a-zA-Z0-9\-]', '', description.replace(' ', '-'))
            branch_name = f"{branch_name}-{safe_description}"
        
        # Create and checkout the new branch
        logger.info(f"Creating new branch: {branch_name}")
        run_git_command(['git', 'checkout', '-b', branch_name], 
                       f"Failed to create branch {branch_name}")
        
        # Update version in config
        config['repository']['current_version'] = new_version
        save_config(config)
        
        # Create or update version file
        version_info = {
            "version": new_version,
            "branch_name": branch_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description or "Version update"
        }
        
        if not save_version_file(version_info):
            # If saving version file fails, try to revert to previous branch
            logger.error("Failed to update version file, attempting to revert changes")
            try:
                run_git_command(['git', 'checkout', '-'])
                sys.exit(1)
            except:
                logger.critical("Failed to revert branch change. Manual intervention required.")
                sys.exit(2)
        
        # Stage and commit version changes
        logger.info("Committing version changes")
        run_git_command(['git', 'add', get_version_file_path(), get_config_path()],
                      "Failed to stage version files")
                      
        commit_message = f"Bump version to {new_version}"
        if description:
            commit_message += f" - {description}"
        
        run_git_command(['git', 'commit', '-m', commit_message],
                      "Failed to commit version changes")
        
        logger.info(f"Created and switched to new branch: {branch_name}")
        logger.info(f"Version bumped to {new_version}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in git operations: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a new version branch')
    parser.add_argument('--level', choices=['patch', 'minor', 'major'], default='patch',
                        help='Version increment level (default: patch)')
    parser.add_argument('--prefix', default='v', help='Version prefix (default: v)')
    parser.add_argument('--description', help='Optional branch description')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
        
    create_version_branch(level=args.level, prefix=args.prefix, description=args.description)
