from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set
import zipfile

from low_trust_photo_backup.core.hash import hash


def group_files_by_size(base_path: Path, data: Dict[Path, int], max_size_gb=2):
    """
    Groups file paths into sets where each set's total size is <= max_size_gb.

    Args:
        data: Dict with structure {'base_path': str, 'files': {filename: {'size': int, ...}}}
        max_size_gb: Maximum size in GB for each group (default: 2)

    Returns:
        List of sets of Path objects, each set totaling <= max_size_gb
    """
    # TODO error handling for individual files larger than 2Gb
    max_bytes = max_size_gb * 1024 * 1024 * 1024  # Convert GB to bytes

    groups = []
    current_group = set()
    current_size = 0

    for filename, file_size in data.items():
        file_path = base_path / filename

        # If adding this file exceeds max_size, start a new group
        if current_size + file_size > max_bytes and current_group:
            groups.append(current_group)
            current_group = set()
            current_size = 0

        current_group.add(file_path)
        current_size += file_size

    # Add the last group if it has any files
    if current_group:
        groups.append(current_group)

    return groups


def zip_file_groups(
    groups: List[Set[Path]], output_dir: Path, base_name: str = "archive"
) -> List[Path]:
    """
    Creates a zip file for each group of files.
    Args:
        groups: List of sets of Path objects to zip
        output_dir: Directory where zip files will be created
        base_name: Base name for the zip files (default: "archive")
    Returns:
        List of created zip file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created_zips = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, group in enumerate(groups, 1):
        zip_filename = f"{base_name}_group{i}_{timestamp}.zip"
        zip_path = output_dir / zip_filename

        print(f"Creating {zip_filename} with {len(group)} files...")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in sorted(group):
                if file_path.exists():
                    zipf.write(file_path)
                    print(f"  Added: {file_path.name}")
                else:
                    raise FileNotFoundError()

        created_zips.append(zip_path)
        print(f"Created: {zip_path}\n")

    return created_zips


def get_checksum_file_name(zip_file_path: Path) -> Path:
    if not zip_file_path.is_absolute():
        raise ValueError(f"zip_file_path must be absolute, got: {zip_file_path}")
    return zip_file_path.parent / f"{zip_file_path.stem}_checksum.json"
