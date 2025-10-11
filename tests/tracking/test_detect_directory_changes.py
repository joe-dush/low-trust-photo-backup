import pytest
from pathlib import Path
import tempfile
import shutil
from low_trust_photo_backup.tracking import detect_directory_changes  


@pytest.fixture
def temp_dir():
    """Create a temporary directory for each test and clean it up after."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


def test_empty_directory_initial_snapshot(temp_dir):
    """Test that an empty directory creates initial snapshot with no changes."""
    result = detect_directory_changes(temp_dir)
    
    assert result == {}
    assert (temp_dir / ".snapshot.json").exists()


def test_initial_run_with_existing_files(temp_dir):
    """Test that initial run with existing files reports them in the result."""
    # Create some initial files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("file1.txt") in result
    assert Path("file2.txt") in result
    assert len(result) == 2
    assert (temp_dir / ".snapshot.json").exists()


def test_detect_created_file(temp_dir):
    """Test that newly created files are detected with correct relative paths."""
    # Initial run - create snapshot
    detect_directory_changes(temp_dir)
    
    # Create a new file
    (temp_dir / "new_file.txt").write_text("new content")
    
    # Second run - detect changes
    result = detect_directory_changes(temp_dir)
    
    assert Path("new_file.txt") in result
    assert len(result) == 1


def test_detect_multiple_created_files(temp_dir):
    """Test that multiple created files are all detected."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create multiple new files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    (temp_dir / "file3.txt").write_text("content3")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("file1.txt") in result
    assert Path("file2.txt") in result
    assert Path("file3.txt") in result
    assert len(result) == 3


def test_detect_modified_file(temp_dir):
    """Test that modified files are detected with correct relative paths."""
    # Create initial file
    (temp_dir / "existing.txt").write_text("original content")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Modify the file
    (temp_dir / "existing.txt").write_text("modified content")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("existing.txt") in result
    assert len(result) == 1


def test_detect_created_and_modified_files(temp_dir):
    """Test detection of both created and modified files."""
    # Create initial file
    (temp_dir / "existing.txt").write_text("original")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Modify existing and create new
    (temp_dir / "existing.txt").write_text("modified")
    (temp_dir / "new.txt").write_text("new")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("existing.txt") in result
    assert Path("new.txt") in result
    assert len(result) == 2


def test_nested_directory_created_file(temp_dir):
    """Test that files in subdirectories have correct relative paths."""
    # Create subdirectory structure
    subdir = temp_dir / "subdir" / "nested"
    subdir.mkdir(parents=True)
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create file in nested directory
    (subdir / "nested_file.txt").write_text("content")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("subdir/nested/nested_file.txt") in result
    assert len(result) == 1


def test_multiple_nested_files(temp_dir):
    """Test detection across multiple subdirectories."""
    # Create directory structure
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()
    (temp_dir / "dir1/subdir").mkdir()
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create files in various locations
    (temp_dir / "root.txt").write_text("root")
    (temp_dir / "dir1/file1.txt").write_text("file1")
    (temp_dir / "dir2/file2.txt").write_text("file2")
    (temp_dir / "dir1/subdir/file3.txt").write_text("file3")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("root.txt") in result
    assert Path("dir1/file1.txt") in result
    assert Path("dir2/file2.txt") in result
    assert Path("dir1/subdir/file3.txt") in result
    assert len(result) == 4


def test_no_changes_returns_empty(temp_dir):
    """Test that no changes between runs returns empty dict."""
    # Create initial files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Second run with no changes
    result = detect_directory_changes(temp_dir)
    
    assert result == {}


def test_incremental_changes_across_multiple_runs(temp_dir):
    """Test that only new changes are detected between consecutive runs."""
    # First run: initial snapshot (empty directory)
    result1 = detect_directory_changes(temp_dir)
    assert result1 == {}
    
    # Create some files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    # Second run: detect the newly created files
    result2 = detect_directory_changes(temp_dir)
    assert Path("file1.txt") in result2
    assert Path("file2.txt") in result2
    assert len(result2) == 2
    
    # Make additional changes
    (temp_dir / "file1.txt").write_text("modified content")  # Modify existing
    (temp_dir / "file3.txt").write_text("content3")  # Create new
    # file2.txt unchanged
    
    # Third run: detect only the new changes (not file2.txt)
    result3 = detect_directory_changes(temp_dir)
    assert Path("file1.txt") in result3  # Modified
    assert Path("file3.txt") in result3  # Created
    assert Path("file2.txt") not in result3  # Unchanged since last run
    assert len(result3) == 2


def test_paths_are_relative_not_absolute(temp_dir):
    """Test that returned paths are relative to the directory, not absolute."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create a file
    (temp_dir / "test_file.txt").write_text("content")
    
    result = detect_directory_changes(temp_dir)
    
    # Check that the path is relative (not absolute)
    for path in result.keys():
        assert not path.is_absolute()
        assert path == Path("test_file.txt")


def test_snapshot_file_is_ignored(temp_dir):
    """Test that the snapshot file itself is not reported as a change."""
    # Initial run creates snapshot
    detect_directory_changes(temp_dir)
    
    # Second run should not report the snapshot file as a change
    result = detect_directory_changes(temp_dir)
    
    assert Path(".snapshot.json") not in result
    assert result == {}


def test_detect_deleted_file(temp_dir):
    """Test that deleted files are NOT reported (only created/modified are returned)."""
    # Create initial files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Delete a file
    (temp_dir / "file1.txt").unlink()
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("file1.txt") not in result
    assert Path("file2.txt") not in result
    assert result == {}


def test_detect_multiple_deleted_files(temp_dir):
    """Test that multiple deleted files are NOT reported."""
    # Create initial files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    (temp_dir / "file3.txt").write_text("content3")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Delete multiple files
    (temp_dir / "file1.txt").unlink()
    (temp_dir / "file3.txt").unlink()
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("file1.txt") not in result
    assert Path("file3.txt") not in result
    assert result == {}


def test_detect_deleted_nested_file(temp_dir):
    """Test that deleted files in subdirectories are NOT reported."""
    # Create nested structure
    subdir = temp_dir / "subdir" / "nested"
    subdir.mkdir(parents=True)
    (subdir / "file.txt").write_text("content")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Delete nested file
    (subdir / "file.txt").unlink()
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("subdir/nested/file.txt") not in result
    assert result == {}


def test_detect_renamed_file(temp_dir):
    """Test that renaming a file only reports the new name (creation), not deletion."""
    # Create initial file
    (temp_dir / "old_name.txt").write_text("content")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Rename file
    (temp_dir / "old_name.txt").rename(temp_dir / "new_name.txt")
    
    result = detect_directory_changes(temp_dir)
    
    # Only the new file should be reported (deletion not tracked)
    assert Path("old_name.txt") not in result
    assert Path("new_name.txt") in result
    assert len(result) == 1


def test_detect_moved_file_between_directories(temp_dir):
    """Test that moving a file between directories only reports the new location."""
    # Create directory structure
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()
    (temp_dir / "dir1/file.txt").write_text("content")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Move file from dir1 to dir2
    (temp_dir / "dir1/file.txt").rename(temp_dir / "dir2/file.txt")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("dir1/file.txt") not in result  # Old location not reported
    assert Path("dir2/file.txt") in result  # New location reported
    assert len(result) == 1


def test_mixed_operations(temp_dir):
    """Test detection of created and modified files (deletions not reported)."""
    # Create initial files
    (temp_dir / "to_modify.txt").write_text("original")
    (temp_dir / "to_delete.txt").write_text("will be deleted")
    (temp_dir / "unchanged.txt").write_text("stays same")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Perform mixed operations
    (temp_dir / "to_modify.txt").write_text("modified")
    (temp_dir / "to_delete.txt").unlink()
    (temp_dir / "newly_created.txt").write_text("new")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("to_modify.txt") in result
    assert Path("to_delete.txt") not in result  # Deletions not reported
    assert Path("newly_created.txt") in result
    assert Path("unchanged.txt") not in result
    assert len(result) == 2


def test_empty_file_creation(temp_dir):
    """Test that empty files are detected."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create empty file
    (temp_dir / "empty.txt").touch()
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("empty.txt") in result


def test_binary_file_changes(temp_dir):
    """Test that binary files are detected correctly."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create a binary file
    (temp_dir / "binary.bin").write_bytes(b'\x00\x01\x02\x03')
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("binary.bin") in result


def test_modified_binary_file(temp_dir):
    """Test that modifications to binary files are detected."""
    # Create initial binary file
    (temp_dir / "binary.bin").write_bytes(b'\x00\x01\x02\x03')
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Modify binary file
    (temp_dir / "binary.bin").write_bytes(b'\x04\x05\x06\x07')
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("binary.bin") in result


def test_hidden_files(temp_dir):
    """Test that hidden files (starting with .) are detected."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create hidden file (but not the snapshot file)
    (temp_dir / ".hidden").write_text("hidden content")
    
    result = detect_directory_changes(temp_dir)
    
    # Hidden files should be detected
    assert Path(".hidden") in result
    assert len(result) == 1


def test_very_large_filename(temp_dir):
    """Test handling of files with very long names."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create file with long name
    long_name = "a" * 200 + ".txt"
    (temp_dir / long_name).write_text("content")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path(long_name) in result


def test_special_characters_in_filename(temp_dir):
    """Test files with special characters in names."""
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create files with special characters
    special_names = [
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
    ]
    
    for name in special_names:
        (temp_dir / name).write_text("content")
    
    result = detect_directory_changes(temp_dir)
    
    for name in special_names:
        assert Path(name) in result
    assert len(result) == len(special_names)


def test_deeply_nested_directory(temp_dir):
    """Test handling of deeply nested directory structures."""
    # Create deeply nested structure
    deep_path = temp_dir / "a" / "b" / "c" / "d" / "e" / "f"
    deep_path.mkdir(parents=True)
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create file in deep location
    (deep_path / "deep_file.txt").write_text("deep content")
    
    result = detect_directory_changes(temp_dir)
    
    assert Path("a/b/c/d/e/f/deep_file.txt") in result


def test_concurrent_modifications(temp_dir):
    """Test multiple modifications to the same file between snapshots."""
    # Create initial file
    (temp_dir / "multi_mod.txt").write_text("version 1")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Modify multiple times (only last state matters)
    (temp_dir / "multi_mod.txt").write_text("version 2")
    (temp_dir / "multi_mod.txt").write_text("version 3")
    
    result = detect_directory_changes(temp_dir)
    
    # Should only appear once
    assert Path("multi_mod.txt") in result
    assert len(result) == 1


def test_file_replaced_with_directory(temp_dir):
    """Test edge case where a file is deleted and directory with same name is created."""
    # Create initial file
    (temp_dir / "item").write_text("I'm a file")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Replace file with directory
    (temp_dir / "item").unlink()
    (temp_dir / "item").mkdir()
    
    result = detect_directory_changes(temp_dir)
    
    # The file deletion should not be reported (only creations/modifications)
    assert Path("item") not in result
    assert result == {}


def test_symlink_handling(temp_dir):
    """Test handling of symbolic links (if supported by OS)."""
    import os
    
    # Skip if symlinks not supported
    if not hasattr(os, 'symlink'):
        pytest.skip("Symlinks not supported on this platform")
    
    # Create target file
    (temp_dir / "target.txt").write_text("target content")
    
    # Initial run
    detect_directory_changes(temp_dir)
    
    # Create symlink
    try:
        (temp_dir / "link.txt").symlink_to(temp_dir / "target.txt")
    except OSError:
        pytest.skip("Unable to create symlinks (permission issue)")
    
    result = detect_directory_changes(temp_dir)
    
    # Behavior depends on implementation - this documents it
    # Either the symlink is detected or it's ignored
    assert isinstance(result, dict)
