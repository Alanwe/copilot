#!/usr/bin/env python3
"""
Script to fix common linting issues in Python files:
- Fix line length by breaking long lines
- Fix continuation line indentation
- Remove trailing whitespace
- Remove whitespace in blank lines
"""
import sys
import re

def fix_file(filename):
    print(f"Fixing linter issues in {filename}")
    
    # Read the file content
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Process each line
    fixed_lines = []
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip() + '\n'
        
        # Fix blank lines with whitespace
        if line.strip() == '':
            line = '\n'
            
        fixed_lines.append(line)
    
    # Write the fixed content back to the file
    with open(filename, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed whitespace issues in {filename}")
    
    # Now apply autopep8 for more complex fixes
    print("Applying autopep8 for more complex fixes...")
    import subprocess
    subprocess.run(['autopep8', '--in-place', '--aggressive', '--aggressive', filename])
    
    print("Done")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_linting.py <filename>")
        sys.exit(1)
        
    for filename in sys.argv[1:]:
        fix_file(filename)
