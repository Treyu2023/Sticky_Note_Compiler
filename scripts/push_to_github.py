import os
import subprocess
import json
import sys
import argparse

def load_config():
    """Load repository configuration."""
    config_path = r'c:\LocalStorage\Sticky_Note_Compiler\config\repo_config.json'
    
    if not os.path.exists(config_path):
        print("Config file not found. Please run init_repo.py first.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)

def push_to_github(commit_message=None):
    """Push changes to GitHub."""
    project_dir = r'c:\LocalStorage\Sticky_Note_Compiler'
    os.chdir(project_dir)
    
    # Ensure we're in a git repository
    if not os.path.exists(os.path.join(project_dir, '.git')):
        print("Not a git repository. Please run init_repo.py first.")
        sys.exit(1)
    
    try:
        # Load configuration
        config = load_config()
        remote_url = config['repository']['remote']
        
        if not remote_url:
            # Prompt for remote URL if not set
            remote_url = input("Please enter the GitHub remote URL (e.g., https://github.com/username/repo.git): ")
            if not remote_url:
                print("Remote URL is required.")
                sys.exit(1)
            
            # Update config with the new remote URL
            config['repository']['remote'] = remote_url
            with open(os.path.join(project_dir, 'config', 'repo_config.json'), 'w') as f:
                json.dump(config, f, indent=4)
        
        # Check if remote exists, add if not
        try:
            subprocess.run(['git', 'remote', 'get-url', 'origin'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
        
        # Stage changes
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes if there are any staged changes
        if commit_message is None:
            commit_message = input("Enter commit message (leave blank to use default): ")
            if not commit_message:
                commit_message = "Update Sticky Notes Compiler"
        
        try:
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print(f"Changes committed with message: '{commit_message}'")
        except subprocess.CalledProcessError:
            print("No changes to commit or commit failed.")
        
        # Push to GitHub
        try:
            current_branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                          check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
            subprocess.run(['git', 'push', '-u', 'origin', current_branch], check=True)
            print(f"Successfully pushed to {remote_url} on branch {current_branch}")
        except subprocess.CalledProcessError as e:
            print(f"Error pushing to remote: {e}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Push changes to GitHub')
    parser.add_argument('-m', '--message', help='Commit message')
    args = parser.parse_args()
    
    push_to_github(commit_message=args.message)
