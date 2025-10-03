import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
from low_trust_photo_backup.client.tracking import _get_file_info


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = Path(tmp.name)
    
    yield tmp_path
    
    # Cleanup
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def empty_temp_file():
    """Create an empty temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    yield tmp_path
    
    # Cleanup
    if tmp_path.exists():
        tmp_path.unlink()


def test_get_file_info_with_real_file(temp_file):
    """Test with an actual temporary file."""
    info = _get_file_info(temp_file)
    
    # Verify basic fields exist
    assert 'size' in info
    assert 'mtime' in info
    
    # Verify size is correct
    assert info['size'] == 12
    
    # Verify mtime is a float timestamp
    assert isinstance(info['mtime'], float)
    assert info['mtime'] > 0
    
    # inode may or may not exist depending on OS
    if 'inode' in info:
        assert isinstance(info['inode'], int)


def test_get_file_info_with_inode():
    """Test that inode is included on Unix-like systems."""
    mock_stat = Mock()
    mock_stat.st_size = 1024
    mock_stat.st_mtime = 1234567890.5
    mock_stat.st_ino = 98765
    
    mock_path = Mock(spec=Path)
    mock_path.stat.return_value = mock_stat
    
    info = _get_file_info(mock_path)
    
    assert info['size'] == 1024
    assert info['mtime'] == 1234567890.5
    assert info['inode'] == 98765


def test_get_file_info_without_inode():
    """Test that function works when inode is not available (Windows)."""
    mock_stat = Mock(spec=['st_size', 'st_mtime']) # By using spec, st_ino won't exist and will raise AttributeError
    mock_stat.st_size = 2048
    mock_stat.st_mtime = 9876543210.1
    
    mock_path = Mock(spec=Path)
    mock_path.stat.return_value = mock_stat
    
    info = _get_file_info(mock_path)
    
    assert info['size'] == 2048
    assert info['mtime'] == 9876543210.1
    assert 'inode' not in info


def test_get_file_info_nonexistent_file():
    """Test with a non-existent file."""
    non_existent_path = Path("/path/that/does/not/exist/file.txt")
    with pytest.raises(OSError):
        info = _get_file_info(non_existent_path)


def test_get_file_info_ioerror():
    """Test that IOError is caught"""
    mock_path = Mock(spec=Path)
    mock_path.stat.side_effect = IOError("Permission denied")
    
    with pytest.raises(IOError):
        info = _get_file_info(mock_path)


def test_get_file_info_oserror():
    """Test that OSError is caught""" 
    mock_path = Mock(spec=Path)
    mock_path.stat.side_effect = OSError("File not found")
    
    with pytest.raises(OSError):
        info = _get_file_info(mock_path)


def test_get_file_info_zero_size_file(empty_temp_file):
    """Test with an empty file."""
    info = _get_file_info(empty_temp_file)
    
    assert info['size'] == 0
    assert 'mtime' in info


def test_get_file_info_large_file():
    """Test with a mock large file."""
    mock_stat = Mock()
    mock_stat.st_size = 10 * 1024 * 1024 * 1024  # 10 GB
    mock_stat.st_mtime = 1609459200.0
    mock_stat.st_ino = 12345
    
    mock_path = Mock(spec=Path)
    mock_path.stat.return_value = mock_stat
    
    info = _get_file_info(mock_path)
    
    assert info['size'] == 10 * 1024 * 1024 * 1024
