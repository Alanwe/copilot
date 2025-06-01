#!/usr/bin/env python3
"""Fix long lines in the test_runtime_coverage.py file."""
import re

filename = "tests/runtime/test_runtime_coverage.py"

with open(filename, 'r') as f:
    content = f.read()

# Fix long lines with pytest.raises
pattern = r"(    with pytest\.raises\(mock_fastapi_components\['fastapi'\]\.HTTPException\)) (as exc_info:)"
replacement = r"\1\n        \2"
content = re.sub(pattern, replacement, content)

with open(filename, 'w') as f:
    f.write(content)

print("Fixed long lines in", filename)
