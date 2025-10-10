import hashlib
from pathlib import Path
from typing import Optional, Union


def hash_file(
    file_path: Union[str, Path],
    algorithm: str = "blake2b",
    digest_size: int = 32,
    partial_bytes: Optional[int] = None,
    chunk_size: int = 65536,
) -> Optional[str]:
    """
    Hash a file using the specified algorithm.

    This is a shared utility function that can be used across the entire package
    for consistent file hashing operations.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm ('blake2b', 'sha256', 'md5', etc.)
        digest_size: Digest size in bytes (only for blake2b/blake2s)
        partial_bytes: If set, only hash this many bytes from start of file.
                      If None, hash entire file.
        chunk_size: Size of chunks to read (default: 64KB)

    Returns:
        Hex digest string, or None if file cannot be read

    Example:
        # Full file hash
        full_hash = hash_file('/path/to/file.txt')

        # Partial hash (first 8KB only)
        partial_hash = hash_file('/path/to/file.txt', partial_bytes=8192)

        # Use SHA256 instead
        sha_hash = hash_file('/path/to/file.txt', algorithm='sha256')
    """
    file_path = Path(file_path)

    # Create hasher based on algorithm
    if algorithm in ("blake2b", "blake2s"):
        hasher = hashlib.new(algorithm, digest_size=digest_size)
    else:
        hasher = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            if partial_bytes is not None:
                # Read only specified number of bytes
                data = f.read(partial_bytes)
                hasher.update(data)
            else:
                # Read entire file in chunks
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hasher.update(chunk)

        return hasher.hexdigest()

    except (OSError, PermissionError, FileNotFoundError):
        return None
