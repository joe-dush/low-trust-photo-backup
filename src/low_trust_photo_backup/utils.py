import hashlib
import os
from typing import Generator, Union
from pathlib import Path

def compute_file_hash(file_path: Union[str, Path], algorithm: str = 'blake2b', chunk_size: int = 65536) -> str:
    """
    Compute hash of a file efficiently for change detection.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use ('sha256', 'md5', 'sha1', 'blake2b')
            blake2b chosen as default as it's faster than md5 and still pretty
            colision resistant
        chunk_size: Size of chunks to read at a time in bytes (default 64KB)
    
    Returns:
        Hexadecimal string representation of the file hash
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
        ValueError: If the hash algorithm is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Validate algorithm
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    
    return hasher.hexdigest()


def walk_files_generator(directory: Union[str, Path]) -> Generator[str, None, None]:
    """
    Yields the full filepath of all files under a parent directory (recursively)
    Uses os.walk as more efficient for large trees than pathlib
    Uses a generator pattern so we don't have to store a large list of files
    in memory
    
    Args:
        directory: Path to the parent directory
    
    Yields:
        Absolute file paths one at a time
    """
    directory = str(directory)
    
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            yield os.path.abspath(file_path)