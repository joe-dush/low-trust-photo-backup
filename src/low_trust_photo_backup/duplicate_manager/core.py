"Main functionality of duplicate_manager"
import hashlib
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from low_trust_photo_backup.common.hashing import hash_file


@dataclass
class DuplicateResult:
    """
    Result of duplicate file detection.
    
    Attributes:
        duplicates: Dict mapping hash to list of duplicate file paths
        total_groups: Number of duplicate groups found
        total_files: Total number of duplicate files
        wasted_bytes: Total bytes that could be saved by removing duplicates
    """
    duplicates: Dict[str, List[Path]] = field(default_factory=dict)
    total_groups: int = 0
    total_files: int = 0
    wasted_bytes: int = 0
    
    @property
    def wasted_mb(self) -> float:
        """Wasted space in megabytes."""
        return self.wasted_bytes / (1024 * 1024)
    
    @property
    def wasted_gb(self) -> float:
        """Wasted space in gigabytes."""
        return self.wasted_bytes / (1024 * 1024 * 1024)


class DuplicateFinder:
    """
    Main entry point for duplicate file detection.
    
    Uses multi-stage comparison strategy:
    1. Group files by size (fast filter)
    2. Compare partial hash (first 8KB) for same-size files
    3. Compare full hash only when partial hashes match
    
    Example:
        # Basic usage
        finder = DuplicateFinder('/path/to/directory')
        result = finder.find()
        
        # With configuration
        finder = DuplicateFinder('/path/to/directory', min_size=1024)
        result = finder.find()
        
        # Access results
        for hash_val, files in result.duplicates.items():
            print(f"Found {len(files)} duplicates:")
            for file in files:
                print(f"  - {file}")
        
        print(f"Could save {result.wasted_gb:.2f} GB")
    """
    
    CHUNK_SIZE = 65536  # 64KB chunks for reading files
    PARTIAL_SIZE = 8192  # 8KB for partial hash comparison
    
    def __init__(
        self,
        root_path: str,
        min_size: int = 0,
        digest_size: int = 32
    ):
        """
        Initialize duplicate finder.
        
        Args:
            root_path: Root directory to scan for duplicates
            min_size: Minimum file size in bytes (files smaller are ignored)
            digest_size: BLAKE2b digest size in bytes (default: 32)
        """
        self.root_path = Path(root_path)
        self.min_size = min_size
        self.digest_size = digest_size
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
    
    def find(self) -> DuplicateResult:
        """
        Find all duplicate files in the configured directory.
        
        Returns:
            DuplicateResult containing all detected duplicates and statistics
        """
        # Stage 1: Scan and group by size
        files = self._scan_files()
        size_groups = self._group_by_size(files)
        
        # Stage 2 & 3: Detect duplicates using partial and full hashes
        duplicates = self._detect_duplicates(size_groups)
        
        # Calculate statistics
        total_groups = len(duplicates)
        total_files = sum(len(files) for files in duplicates.values())
        wasted_bytes = self._calculate_waste(duplicates)
        
        return DuplicateResult(
            duplicates=duplicates,
            total_groups=total_groups,
            total_files=total_files,
            wasted_bytes=wasted_bytes
        )
    
    def _scan_files(self) -> List[Path]:
        """Recursively scan directory and return list of files."""
        files = []
        for item in self.root_path.rglob('*'):
            try:
                if item.is_file() and item.stat().st_size >= self.min_size:
                    files.append(item)
            except (OSError, PermissionError):
                # Skip files we can't access
                continue
        return files
    
    def _group_by_size(self, files: List[Path]) -> Dict[int, List[Path]]:
        """Group files by size. Returns only groups with 2+ files."""
        size_groups = defaultdict(list)
        
        for file_path in files:
            try:
                size = file_path.stat().st_size
                size_groups[size].append(file_path)
            except (OSError, PermissionError):
                continue
        
        # Return only sizes with potential duplicates
        return {size: paths for size, paths in size_groups.items() if len(paths) > 1}
    
    def _detect_duplicates(self, size_groups: Dict[int, List[Path]]) -> Dict[str, List[Path]]:
        """
        Detect duplicates using multi-stage comparison.
        
        Args:
            size_groups: Files already grouped by size
            
        Returns:
            Dict mapping full hash to list of duplicate files
        """
        duplicates = {}
        
        for size, files in size_groups.items():
            # Stage 2: Partial hash for files of same size
            partial_groups = self._group_by_partial_hash(files, size)
            
            # Stage 3: Full hash for files with matching partial hashes
            for partial_files in partial_groups.values():
                if len(partial_files) > 1:
                    full_hash_groups = self._group_by_full_hash(partial_files)
                    duplicates.update(full_hash_groups)
        
        return duplicates
    
    def _group_by_partial_hash(self, files: List[Path], size: int) -> Dict[str, List[Path]]:
        """Group files by partial hash (first 8KB). Skip for very small files."""
        # For files smaller than partial size, skip partial hashing
        if size <= self.PARTIAL_SIZE:
            return {"skip_partial": files}
        
        partial_groups = defaultdict(list)
        for file_path in files:
            partial_hash = hash_file(file_path, partial_bytes=self.PARTIAL_SIZE)
            if partial_hash:
                partial_groups[partial_hash].append(file_path)
        
        return {h: f for h, f in partial_groups.items() if len(f) > 1}
    
    def _group_by_full_hash(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by full content hash."""
        full_groups = defaultdict(list)
        for file_path in files:
            full_hash = hash_file(file_path)
            if full_hash:
                full_groups[full_hash].append(file_path)
        
        return {h: f for h, f in full_groups.items() if len(f) > 1}
    
    def _calculate_waste(self, duplicates: Dict[str, List[Path]]) -> int:
        """Calculate total wasted space from duplicates (keeping one copy)."""
        total_waste = 0
        for files in duplicates.values():
            if files:
                try:
                    file_size = files[0].stat().st_size
                    # Count n-1 files as waste (keep one)
                    total_waste += file_size * (len(files) - 1)
                except (OSError, PermissionError):
                    continue
        return total_waste

