import json
from pathlib import Path
from datetime import datetime
from typing import Any


def append_jsonl(path: Path, obj: Any):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj) + '\n')


def write_text(path: Path, content: str):
    with path.open('w', encoding='utf-8') as f:
        f.write(content)
