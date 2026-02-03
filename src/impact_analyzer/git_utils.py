import re
from typing import Set

def parse_patch_for_changed_lines(patch: bytes) -> Set[int]:
    """Parses a unified diff patch to find changed line numbers."""
    changed_lines = set()
    patch_str = patch.decode('utf-8', errors='replace')
    hunk_re = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)

    for match in hunk_re.finditer(patch_str):
        start_line = int(match.group(1))
        # match.group(2) may be '0' which is falsy; check against None
        count = int(match.group(2)) if match.group(2) is not None else 1
        for i in range(count):
            changed_lines.add(start_line + i)
    return changed_lines