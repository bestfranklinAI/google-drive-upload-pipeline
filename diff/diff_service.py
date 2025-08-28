import difflib
from typing import List


def unified_diff(old: str, new: str) -> str:
    diff_lines = difflib.unified_diff(
        old.splitlines(), new.splitlines(), lineterm=""
    )
    return "\n".join(diff_lines)
