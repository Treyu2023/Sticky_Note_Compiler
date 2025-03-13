import os
import subprocess
import json
import sys

def init_repo():
    """Initialize a Git repository for the Sticky Notes Compiler project."""
    project_dir = r'c:\LocalStorage\Sticky_Note_Compiler'
    os.chdir(project_dir)
    
    # Check if the directory is already a Git repository
    if os.path.exists(os.path.join(project_dir, '.git')):
        print("Repository already initialized.")
        return
    
    try:
        # Initialize the repository
        subprocess.run(['git', 'init'], check=True)
        print("Git repository initialized.")
        
        # Create .gitignore file
        with open(os.path.join(project_dir, '.gitignore'), 'w') as f:
            f.write("__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nenv/\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\n*.egg-info/\n.installed.cfg\n*.egg\n.env\n.venv\nvenv/\nENV/\n")
        
        # Create config file for repository settings
        config = {
            "repository": {
                "name": "sticky-note-compiler",
                "remote": "",
                "current_version": "0.1.0"
            }
        }
        
        config_dir = os.path.join(project_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        with open(os.path.join(config_dir, 'repo_config.json'), 'w') as f:
            json.dump(config, f, indent=4)
        
        # Initial commit
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        
        print("Repository initialized with initial commit.")
        print("Config file created at config/repo_config.json")
        print("Please update the remote URL in the config file.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error initializing repository: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_repo()
