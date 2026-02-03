import argparse
import tempfile
import shutil
import sys
from git import Repo
from .engine import analyze_commit

def main():
    parser = argparse.ArgumentParser(description="Impact Analysis Tool for Code Repositories")
    
    # Updated: Changed 'sha' from positional to a named argument '--commit'
    parser.add_argument(
        '--commit', 
        required=True, 
        help="The Commit SHA to analyze"
    )
    
    parser.add_argument(
        '--repo', 
        required=True, 
        help="Path to local repository OR GitHub URL"
    )
    
    args = parser.parse_args()
    
    repo_location = args.repo
    is_temp = False

    # Handle Auto-Cloning for URLs
    if args.repo.startswith(('http://', 'https://', 'git@')):
        print(f"Detected remote URL. Cloning to temporary directory...")
        temp_dir = tempfile.mkdtemp()
        try:
            Repo.clone_from(args.repo, temp_dir)
            repo_location = temp_dir
            is_temp = True
            print(f"Cloned successfully to {temp_dir}\n")
        except Exception as e:
            print(f"Failed to clone repo: {e}")
            shutil.rmtree(temp_dir)
            sys.exit(1)

    try:
        # Pass args.commit instead of args.sha
        analyze_commit(repo_location, args.commit)
    finally:
        if is_temp:
            print(f"\nCleaning up temporary files...")
            shutil.rmtree(repo_location)

if __name__ == "__main__":
    main()