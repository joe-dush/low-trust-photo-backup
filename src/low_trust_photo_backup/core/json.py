import json
from pathlib import Path
from typing import Dict, Optional


def read_json_file(file_path: Path) -> Optional[Dict]:
    if not file_path.exists():
        return None
    with open(file_path, "r") as f:
        return json.load(f)

def write_json_file(file_path: Path, data: Dict) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f)