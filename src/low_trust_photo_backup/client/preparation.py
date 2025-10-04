from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import zipfile


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
