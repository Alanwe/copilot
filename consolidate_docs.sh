#!/usr/bin/env bash
# Consolidate documentation and remove redundant .md files

echo "Consolidating documentation files..."

# Essential documentation files to keep
ESSENTIAL_DOCS=(
    "README.md"
    "USER_GUIDE.md"
)

# Folder for archived documentation
mkdir -p /workspaces/copilot/docs/archived

# Move redundant documentation files to archived folder
cd /workspaces/copilot
for file in *.md; do
    # Check if file is in essential docs list
    KEEP=false
    for essential in "${ESSENTIAL_DOCS[@]}"; do
        if [ "$file" == "$essential" ]; then
            KEEP=true
            break
        fi
    done
    
    # Move to archived if not essential
    if [ "$KEEP" == "false" ] && [ "$file" != "USER_GUIDE.md" ]; then
        echo "Moving $file to docs/archived/"
        mv "$file" docs/archived/
    else
        echo "Keeping essential doc: $file"
    fi
done

# Keep only the new USER_GUIDE.md and README.md
echo "Documentation consolidation complete!"
