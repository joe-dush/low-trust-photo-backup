"""
Duplicate file finder module.

This module provides functionality to find duplicate files in a directory
using multi-stage comparison (size -> partial hash -> full hash).

Public API:
    DuplicateFinder - Main entry point for finding duplicates
    DuplicateResult - Data class containing detection results
"""
from .core import DuplicateFinder, DuplicateResult

__all__ = ['DuplicateFinder', 'DuplicateResult']
