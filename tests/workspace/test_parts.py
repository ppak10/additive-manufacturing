import pytest
from pathlib import Path
from unittest.mock import patch

from am.workspace.parts import initialize_parts


# -------------------------------
# Basic functionality tests
# -------------------------------


def test_initialize_parts_basic(isolated_workspace):
    """Test creating a basic parts folder without examples."""
    parts_dir = initialize_parts(isolated_workspace, include_examples=False)

    assert parts_dir.exists()
    assert parts_dir.is_dir()
    assert parts_dir == isolated_workspace / "parts"


def test_initialize_parts_idempotent(isolated_workspace):
    """Test that creating parts folder multiple times is idempotent."""
    # Create once
    parts_dir_1 = initialize_parts(isolated_workspace, include_examples=False)
    assert parts_dir_1.exists()

    # Create again (should not error)
    parts_dir_2 = initialize_parts(isolated_workspace, include_examples=False)
    assert parts_dir_2.exists()
    assert parts_dir_2 == parts_dir_1


# -------------------------------
# Tests with examples
# -------------------------------


def test_initialize_parts_with_examples(isolated_workspace):
    """Test creating parts folder with example files."""
    parts_dir = initialize_parts(isolated_workspace, include_examples=True)

    assert parts_dir.exists()
    assert parts_dir.is_dir()
    assert parts_dir == isolated_workspace / "parts"

    # Verify expected example files are copied
    expected_files = ["overhang.STL", "overhang.gcode", "README.md"]
    for file_name in expected_files:
        assert (parts_dir / file_name).exists()


def test_initialize_parts_with_examples_verifies_file_contents(isolated_workspace):
    """Test that copied files are identical to source files."""
    parts_dir = initialize_parts(isolated_workspace, include_examples=True)

    from am.data import DATA_DIR

    data_parts_dir = DATA_DIR / "parts"

    # Verify each copied file matches the source
    for file_path in data_parts_dir.iterdir():
        if file_path.is_file():
            dest_file = parts_dir / file_path.name

            assert dest_file.exists()
            assert dest_file.stat().st_size == file_path.stat().st_size

            # For text files, verify content matches
            if file_path.name.endswith((".md", ".gcode")):
                assert dest_file.read_text() == file_path.read_text()


def test_initialize_parts_with_examples_overwrites_existing(isolated_workspace):
    """Test that creating with examples overwrites existing files."""
    parts_dir = isolated_workspace / "parts"
    parts_dir.mkdir()

    # Create a dummy file
    test_file = parts_dir / "overhang.STL"
    test_file.write_text("dummy content")
    original_size = test_file.stat().st_size

    # Create with examples should overwrite
    parts_dir = initialize_parts(isolated_workspace, include_examples=True)

    assert test_file.exists()
    # Verify file was overwritten (size should be different)
    assert test_file.stat().st_size != original_size


# -------------------------------
# Error handling tests
# -------------------------------


def test_initialize_parts_missing_data_directory(isolated_workspace):
    """Test error when data directory doesn't exist."""
    with patch("am.data.DATA_DIR", isolated_workspace / "nonexistent"):
        with pytest.raises(FileNotFoundError):
            initialize_parts(isolated_workspace, include_examples=True)


def test_initialize_parts_invalid_workspace_path(tmp_path):
    """Test error when workspace path is invalid."""
    invalid_path = tmp_path / "nonexistent" / "path" / "to" / "workspace"

    # Should create parent directories and succeed
    parts_dir = initialize_parts(invalid_path, include_examples=False)
    assert parts_dir.exists()


def test_initialize_parts_permission_error(isolated_workspace):
    """Test handling of permission errors when creating directory."""
    parts_dir = isolated_workspace / "parts"
    parts_dir.mkdir()

    # Make the parts directory read-only
    parts_dir.chmod(0o444)

    try:
        # Try to create a file inside (should fail on most systems)
        with pytest.raises(PermissionError):
            test_file = parts_dir / "test.txt"
            test_file.write_text("test")
    finally:
        # Restore permissions for cleanup
        parts_dir.chmod(0o755)


# -------------------------------
# Return value tests
# -------------------------------


def test_initialize_parts_return_values_without_examples(isolated_workspace):
    """Test the structure of return values when not including examples."""
    parts_dir = initialize_parts(isolated_workspace, include_examples=False)

    assert isinstance(parts_dir, Path)


def test_initialize_parts_return_values_with_examples(isolated_workspace):
    """Test the structure of return values when including examples."""
    parts_dir = initialize_parts(isolated_workspace, include_examples=True)

    assert isinstance(parts_dir, Path)


# -------------------------------
# Edge case tests
# -------------------------------


def test_initialize_parts_with_existing_parts_dir(isolated_workspace):
    """Test creating parts folder when directory already exists."""
    # Pre-create the parts directory
    parts_dir = isolated_workspace / "parts"
    parts_dir.mkdir()

    # Should not raise an error
    result_dir = initialize_parts(isolated_workspace, include_examples=False)

    assert result_dir.exists()
    assert result_dir == parts_dir


def test_initialize_parts_with_existing_files_no_examples(isolated_workspace):
    """Test that existing files are preserved when not including examples."""
    parts_dir = isolated_workspace / "parts"
    parts_dir.mkdir()

    # Create an existing file
    existing_file = parts_dir / "my_custom_part.stl"
    existing_file.write_text("custom content")

    # Create without examples
    result_dir = initialize_parts(isolated_workspace, include_examples=False)

    assert existing_file.exists()
    assert existing_file.read_text() == "custom content"


def test_initialize_parts_empty_data_directory(isolated_workspace):
    """Test behavior when data/parts directory exists but is empty."""
    # Create an empty data directory structure
    mock_data_dir = isolated_workspace / "mock_data"
    mock_data_parts = mock_data_dir / "parts"
    mock_data_parts.mkdir(parents=True)

    with patch("am.data.DATA_DIR", mock_data_dir):
        parts_dir = initialize_parts(
            isolated_workspace / "workspace", include_examples=True
        )

        assert parts_dir.exists()
        # No files should be copied from empty directory
        assert len(list(parts_dir.iterdir())) == 0
