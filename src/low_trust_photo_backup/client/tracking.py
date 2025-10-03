#!/usr/bin/env python3
"""
Directory Change Tracker

This script monitors a directory for file changes by comparing the current state
with a previously saved snapshot. It detects created, modified, and deleted files.

Usage:
    python track_changes.py [directory_path]

If no directory is specified, it uses the current directory.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Tuple, Optional


def _get_file_info(file_path: Path) -> Dict:
    """Get file information: size, mtime, and inode if available."""
    try:
        stat = file_path.stat()
        info = {
            'size': stat.st_size,
            'mtime': stat.st_mtime
        }
        
        # Add inode if available (Unix-like systems)
        try:
            info['inode'] = stat.st_ino
        except AttributeError:
            pass  # Windows doesn't have inodes
        
        return info
    except (IOError, OSError) as e:
        print(e)
        raise e

def _scan_directory(directory: Path, snapshot_filename: str = '.file_snapshot.json') -> Dict[str, Dict]:
    """
    Scan directory and return file information. File path as key, dict of 
    'size', 'mtime' and optional 'inode' as value
    """
    files_info = {}
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.name != snapshot_filename:
            relative_path = str(file_path.relative_to(directory))
            files_info[relative_path] = _get_file_info(file_path)
    
    return files_info


def _load_snapshot(snapshot_file: Path) -> Optional[Dict]:
    """Load the previous snapshot from file."""
    if not snapshot_file.exists():
        return None
    
    with open(snapshot_file, 'r') as f:
        return json.load(f)


def _save_snapshot(snapshot_file: Path, snapshot: Dict) -> None:
    """Save current snapshot to file."""
    snapshot_data = {
        'timestamp': datetime.now().isoformat(),
        'files': snapshot
    }
    
    try:
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
    except (IOError, TypeError, ValueError) as e:
        print(f"Error: Could not save snapshot: {e}")
        raise  # Re-raise the exception


def _compare_snapshots(old_snapshot: Dict, new_snapshot: Dict) -> Tuple[Dict, Dict, Dict]:
    """Compare two snapshots and return created, modified, and deleted files."""
    new_files = set(new_snapshot.keys())
    if not old_snapshot:
        return new_snapshot, dict(), dict()
    old_files = set(old_snapshot.keys())
    
    created = new_files - old_files
    deleted = old_files - new_files
    
    # Check for modifications in common files
    common_files = old_files & new_files
    modified = set()
    
    for file_path in common_files:
        old_info = old_snapshot[file_path]
        new_info = new_snapshot[file_path]
        
        # Check if file changed: size, mtime, or inode
        size_changed = old_info.get('size') != new_info.get('size')
        mtime_changed = abs(old_info.get('mtime', 0) - new_info.get('mtime', 0)) > 1
        inode_changed = (old_info.get('inode') and new_info.get('inode') and
                        old_info['inode'] != new_info['inode'])
        
        if size_changed or mtime_changed or inode_changed:
            modified.add(file_path)
    
    created_dict = {k: new_snapshot[k] for k in created}
    modified_dict = {k: new_snapshot[k] for k in modified}
    deleted_dict = {k: old_snapshot[k] for k in deleted}
    return created_dict, modified_dict, deleted_dict


def _display_changes(created: Set, modified: Set, deleted: Set, 
                   current_snapshot: Dict, previous_snapshot: Dict) -> None:
    """Display the changes found."""
    if not (created or modified or deleted):
        print("No changes detected.")
        return
    
    if created:
        print(f"📁 CREATED ({len(created)} files):")
        for file_path in sorted(created):
            file_size = current_snapshot[file_path].get('size', 0)
            print(f"  + {file_path} ({file_size:,} bytes)")
        print()
    
    if modified:
        print(f"✏️  MODIFIED ({len(modified)} files):")
        for file_path in sorted(modified):
            old_size = previous_snapshot[file_path].get('size', 0)
            new_size = current_snapshot[file_path].get('size', 0)
            size_change = new_size - old_size
            size_info = f"{new_size:,} bytes"
            if size_change != 0:
                size_info += f" ({size_change:+,})"
            print(f"  ~ {file_path} ({size_info})")
        print()
    
    if deleted:
        print(f"🗑️  DELETED ({len(deleted)} files):")
        for file_path in sorted(deleted):
            old_size = previous_snapshot[file_path].get('size', 0)
            print(f"  - {file_path} ({old_size:,} bytes)")
        print()


def detect_created_and_modified_files(directory: Path) -> set:
    """Track changes in the directory."""
    # check the dir exists
    if not os.path.exists(directory):
        raise NotADirectoryError(f"'{directory.absolute()}' does not exist")

    snapshot_file = Path(os.path.join(str(directory), '.file_snapshot.json'))
    
    print(f"Scanning directory: {directory.absolute()}")
    
    # Get current state
    current_snapshot = _scan_directory(directory)
    
    # Load previous snapshot (will return None if first run)
    previous_data = _load_snapshot(snapshot_file)
    if previous_data:
        previous_snapshot = previous_data.get('files', {}) 
        last_scan = previous_data.get('timestamp', 'unknown')
    else:
        previous_snapshot = None
        last_scan = "Never"
    
    print(f"Last scan: {last_scan}")
    print("-" * 50)
    
    # Compare snapshots
    created, modified, deleted = _compare_snapshots(previous_snapshot, current_snapshot)
    
    # Display results
    _display_changes(set(created.keys()), set(modified.keys()), set(deleted.keys()), current_snapshot, previous_snapshot)
    
    # Update snapshot
    _save_snapshot(snapshot_file, current_snapshot)
    print(f"Snapshot updated. Tracking {len(current_snapshot):,} files.")
    print("-" * 50)

    # return results
    return created | modified
