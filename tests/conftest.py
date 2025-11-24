import pytest
import tempfile
import shutil
from pathlib import Path

# Configure matplotlib to use non-interactive backend for CI environments
import matplotlib

matplotlib.use("Agg")


@pytest.fixture(scope="session")
def temp_project_root():
    """Create a temporary project root for testing."""
    temp_path = Path(tempfile.mkdtemp())

    out_dir = temp_path / "out"
    out_dir.mkdir()

    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def isolated_workspace():
    """Create an isolated workspace for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)
