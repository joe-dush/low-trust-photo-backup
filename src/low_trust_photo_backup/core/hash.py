"""Basic stuff that's used across the application"""

import hashlib
from pathlib import Path


def hash(file_path: Path) -> hashlib.blake2b:
    """Calculate blake2b of the file"""
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot hash file, not found: {file_path}")
    zip_hash = hashlib.blake2b()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            zip_hash.update(chunk)
