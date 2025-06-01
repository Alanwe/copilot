#!/usr/bin/env python3
"""Fix syntax errors with pytest.raises in the test_runtime_coverage.py file."""

filename = "tests/runtime/test_runtime_coverage.py"

with open(filename, 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for the broken pytest.raises pattern
    if "with pytest.raises" in line and i + 1 < len(lines) and lines[i + 1].strip().startswith("as exc_info:"):
        # Fix by combining the lines correctly
        fixed_line = line.rstrip()[:-1] + " as exc_info:\n"  # Remove trailing newline and add as exc_info
        fixed_lines.append(fixed_line)
        i += 2  # Skip the next line since we combined it
    else:
        fixed_lines.append(line)
        i += 1

with open(filename, 'w') as f:
    f.writelines(fixed_lines)

print("Fixed pytest.raises syntax in", filename)
