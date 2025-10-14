import pytest
import tempfile
import shutil
from pathlib import Path

from am.part.initialize import initialize_parts_folder


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Create a temporary data directory with sample part files."""
    temp_path = Path(tempfile.mkdtemp())
    parts_dir = temp_path / "parts"
    parts_dir.mkdir()

    # Create sample part files
    (parts_dir / "sample.gcode").write_text("G1 X10 Y10\n")
    (parts_dir / "test.STL").write_text("solid test\nendsolid test\n")
    (parts_dir / "README.md").write_text("# README\n")

    # Mock the DATA_DIR
    import am.data

    monkeypatch.setattr(am.data, "DATA_DIR", temp_path)

    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


class TestInitializePartsFolder:
    """Tests for initialize_parts_folder function."""

    def test_creates_parts_directory(self, temp_workspace):
        """Test that parts directory is created."""
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=False
        )

        assert parts_dir.exists()
        assert parts_dir.is_dir()
        assert parts_dir == temp_workspace / "parts"
        assert copied_files is None

    def test_creates_parts_directory_with_parents(self):
        """Test that parts directory is created with parents."""
        temp_path = Path(tempfile.mkdtemp())
        workspace_path = temp_path / "nested" / "workspace"

        try:
            parts_dir, copied_files = initialize_parts_folder(
                workspace_path, include_defaults=False
            )

            assert parts_dir.exists()
            assert parts_dir.is_dir()
            assert parts_dir == workspace_path / "parts"
            assert copied_files is None
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def test_idempotent_when_parts_exists(self, temp_workspace):
        """Test that function is idempotent when parts directory already exists."""
        # Create parts directory first
        parts_dir_path = temp_workspace / "parts"
        parts_dir_path.mkdir()
        (parts_dir_path / "existing.gcode").write_text("existing content\n")

        # Run initialize
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=False
        )

        assert parts_dir.exists()
        assert (parts_dir / "existing.gcode").exists()
        assert copied_files is None

    def test_include_defaults_copies_files(self, temp_workspace, temp_data_dir):
        """Test that default files are copied when include_defaults=True."""
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=True
        )

        assert parts_dir.exists()
        assert copied_files is not None
        assert len(copied_files) == 2  # sample.gcode and test.STL, but not README.md
        assert "sample.gcode" in copied_files
        assert "test.STL" in copied_files
        assert "README.md" not in copied_files

        # Verify files were actually copied
        assert (parts_dir / "sample.gcode").exists()
        assert (parts_dir / "test.STL").exists()
        assert not (parts_dir / "README.md").exists()

    def test_include_defaults_preserves_content(self, temp_workspace, temp_data_dir):
        """Test that file content is preserved when copying."""
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=True
        )

        assert (parts_dir / "sample.gcode").read_text() == "G1 X10 Y10\n"
        assert (parts_dir / "test.STL").read_text() == "solid test\nendsolid test\n"

    def test_include_defaults_no_files_to_copy(self, temp_workspace, monkeypatch):
        """Test behavior when data directory is empty."""
        # Create empty data directory
        temp_path = Path(tempfile.mkdtemp())
        parts_dir_empty = temp_path / "parts"
        parts_dir_empty.mkdir()

        import am.data

        monkeypatch.setattr(am.data, "DATA_DIR", temp_path)

        try:
            parts_dir, copied_files = initialize_parts_folder(
                temp_workspace, include_defaults=True
            )

            assert parts_dir.exists()
            assert copied_files is not None
            assert len(copied_files) == 0
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def test_include_defaults_data_dir_not_found(self, temp_workspace, monkeypatch):
        """Test that FileNotFoundError is raised when data directory doesn't exist."""
        # Mock DATA_DIR to non-existent path
        import am.data

        monkeypatch.setattr(am.data, "DATA_DIR", Path("/non/existent/path"))

        with pytest.raises(FileNotFoundError) as exc_info:
            initialize_parts_folder(temp_workspace, include_defaults=True)

        assert "Data parts directory not found" in str(exc_info.value)

    def test_returns_correct_types(self, temp_workspace):
        """Test that function returns correct types."""
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=False
        )

        assert isinstance(parts_dir, Path)
        assert copied_files is None

    def test_returns_correct_types_with_defaults(self, temp_workspace, temp_data_dir):
        """Test that function returns correct types when copying defaults."""
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=True
        )

        assert isinstance(parts_dir, Path)
        assert isinstance(copied_files, list)
        assert all(isinstance(f, str) for f in copied_files)

    def test_overwrites_existing_files_when_copying(
        self, temp_workspace, temp_data_dir
    ):
        """Test that existing files are overwritten when copying defaults."""
        # Create parts directory with existing file
        parts_dir_path = temp_workspace / "parts"
        parts_dir_path.mkdir()
        (parts_dir_path / "sample.gcode").write_text("old content\n")

        # Run initialize with defaults
        parts_dir, copied_files = initialize_parts_folder(
            temp_workspace, include_defaults=True
        )

        # Verify file was overwritten
        assert (parts_dir / "sample.gcode").read_text() == "G1 X10 Y10\n"
        assert "sample.gcode" in copied_files
