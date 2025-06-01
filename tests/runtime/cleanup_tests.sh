#!/usr/bin/env bash
# Clean up unnecessary test files while keeping the essential ones

echo "Cleaning up redundant test files..."

# Create a backup directory
mkdir -p /workspaces/copilot/tests/runtime/backup

# Essential files to keep
ESSENTIAL_FILES=(
    "simple_coverage.py"
    "test_runtime_coverage.py"
    "run_coverage.sh"
    "COVERAGE.md"
    "__init__.py"
)

# Move non-essential files to backup
cd /workspaces/copilot/tests/runtime
for file in *.py; do
    # Check if file is in essential files list
    KEEP=false
    for essential in "${ESSENTIAL_FILES[@]}"; do
        if [ "$file" == "$essential" ]; then
            KEEP=true
            break
        fi
    done
    
    # Move to backup if not essential
    if [ "$KEEP" == "false" ]; then
        echo "Moving $file to backup/"
        mv "$file" backup/
    else
        echo "Keeping essential file: $file"
    fi
done

echo "Cleanup complete!"
