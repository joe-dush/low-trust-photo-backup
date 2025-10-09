"""Module dealing with verifying the integrity of zip files"""
import hashlib
from pathlib import Path
from typing import Dict
from dataclasses import dataclass
import zipfile
from pydantic import BaseModel, Field, field_validator

from src.low_trust_photo_backup.core.hash import hash
from src.low_trust_photo_backup.core.json import read_json_file


class Checksum(BaseModel):
    zip_file_name: str = Field(..., min_length=1)
    zip_hash: str = Field(..., min_length=1)
    zip_size_bytes: int = Field(..., ge=0)
    file_count: int = Field(..., ge=0)


def generate_zip_checksum(zip_path: Path) -> Checksum:
    """
    Generates a checksum for the zip file.
    Args:
        zip_path: Path to the zip file
    Returns:
        Dict containing zip checksum and metadata
    """
    zip_hash = hash(zip_path)

    # Get file count from zip
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        file_count = len(zipf.namelist())
    
    return Checksum(
        zip_file_name=zip_path.name,
        zip_hash=zip_hash.hexdigest(),
        zip_size_bytes=zip_path.stat().st_size,
        file_count=file_count
    )


def verify_zip_integrity(zip_path: Path, checksum_file: Path) -> bool:
    """
    Verifies a zip file against its checksum file.
    Args:
        zip_path: Path to the zip file to verify
        checksum_file: Path to the checksum JSON file
    Returns:
        True if verification passes, False otherwise
    """
    expected = read_json_file(zip_path)
    
    # Verify zip file checksum
    zip_hash = hash(zip_path)
    actual_zip_hash = zip_hash.hexdigest()
    
    # if actual_zip_hash != expected['zip_sha256']:
    #     print(f"FAILED: Zip file checksum mismatch!")
    #     print(f"  Expected: {expected['zip_sha256']}")
    #     print(f"  Actual:   {actual_zip_hash}")
    #     return False
    
    # print(f"✓ Zip file checksum verified: {zip_path.name}")
    
    # # Verify file count
    # with zipfile.ZipFile(zip_path, 'r') as zipf:
    #     actual_file_count = len(zipf.namelist())
    
    # if actual_file_count != expected['file_count']:
    #     print(f"FAILED: File count mismatch!")
    #     print(f"  Expected: {expected['file_count']} files")
    #     print(f"  Actual:   {actual_file_count} files")
    #     return False
    
    # print(f"✓ File count verified: {actual_file_count} files")
    
    # return True