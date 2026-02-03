import os
import re
from git import Repo
from .languages import EXTENSION_MAP
from .parser import find_tests_in_code
from .git_utils import parse_patch_for_changed_lines

def analyze_commit(repo_path: str, sha: str):
    print(f"--- Impact Analysis for {sha} ---\n")
    
    try:
        repo = Repo(repo_path)
        commit = repo.commit(sha)
    except Exception as e:
        print(f"Error: Could not find commit {sha} in {repo_path}.\n{e}")
        return
    
    # Print the commit message (filter out co-author-like lines)
    raw_msg = commit.message.strip()
    filtered_lines = [
        line for line in raw_msg.splitlines()
        if not re.search(r'co-?auth', line, flags=re.I)
    ]
    clean_msg = '\n'.join(filtered_lines).strip()
    if clean_msg:
        print(f"Commit Message: {clean_msg}")
        print("-" * 50 + "\n")
    
    parent = commit.parents[0] if commit.parents else None
    if not parent:
        print("Initial commit - everything is new.")
        return

    diffs = parent.diff(commit, create_patch=True)
    found_any = False

    def status_label_for_diff(d):
        status_map = {
            'A': 'ADDED',
            'D': 'DELETED',
            'M': 'MODIFIED',
            'R': 'RENAMED',
            'T': 'TYPE-CHANGED',
        }
        if d.change_type in status_map:
            return status_map[d.change_type]
        if getattr(d, "new_file", False):
            return "ADDED"
        if getattr(d, "deleted_file", False):
            return "DELETED"
        if getattr(d, "renamed", False):
            return "RENAMED"
        return "CHANGED"

    for diff in diffs:
        file_path = diff.b_path or diff.a_path
        
        # 1. Check if we can parse this file (is it code we support?)
        _, ext = os.path.splitext(file_path)
        is_supported = ext in EXTENSION_MAP
        
        tests = []
        
        # 2. Try to find tests only if supported
        if is_supported:
            try:
                # Read content based on change type
                if diff.change_type == 'A':
                    content = diff.b_blob.data_stream.read()
                    tests = find_tests_in_code(file_path, content)
                elif diff.change_type == 'D':
                    content = diff.a_blob.data_stream.read()
                    tests = find_tests_in_code(file_path, content)
                elif diff.change_type == 'M':
                    # For modified files, we look at the NEW content to find test blocks
                    content = diff.b_blob.data_stream.read()
                    tests = find_tests_in_code(file_path, content)
            except Exception:
                # If parsing fails (e.g. syntax error), we treat it as a normal file change
                tests = []

        # 3. Output Logic
        if tests:
            # It is a Test File (contains identifiable tests)
            found_any = True
            
            if diff.change_type == 'A':
                for t in tests:
                    print(f'1 test added: "{t["name"]}" in {file_path}')

            elif diff.change_type == 'D':
                for t in tests:
                    print(f'1 test removed: "{t["name"]}" in {file_path}')

            elif diff.change_type == 'M':
                changed_lines_indices = parse_patch_for_changed_lines(diff.diff)
                impacted = False
                for t in tests:
                    test_range = range(t['start'], t['end'] + 1)
                    if not changed_lines_indices.isdisjoint(test_range):
                        print(f'1 test modified: "{t["name"]}" in {file_path}')
                        impacted = True
                
                if not impacted:
                    # File modified but no tests touched (maybe imports or formatting)
                    print(f'File modified (no specific test impacted): {file_path}')

        else:
            # Non-Test File (or unsupported)
            # We print these to satisfy "Universal" requirement
            found_any = True

            status_label = status_label_for_diff(diff)
            print(f"[{status_label}] File: {file_path}")
            
            # Add extra context if it looks like source code
            if is_supported and diff.change_type == 'M':
                print(f"  (Dependency change in source code)")
    
    if not found_any:
        print("No changes detected in this commit.")
