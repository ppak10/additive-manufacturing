import click
import json
import shutil
import tempfile

from pathlib import Path
from pytest import fixture

from am.cli.utils import get_workspace_path
from am.workspace import Workspace

@fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_path = Path(tempfile.mkdtemp())

    workspace = Workspace(name="test_utils_workspace", out_path = temp_path)
    workspace_config = workspace.create_workspace(out_path = temp_path)

    yield "test_utils_workspace"
    shutil.rmtree(temp_path, ignore_errors=True)


# def test_get_workspace_path_with_none():
#     """
#     Test get_workspace_path raises exception since not called inside workspace.
#     """
#     result = get_workspace_path(None)

#
# def test_get_workspace_path_with_workspace_name(temp_workspace):
#     """Test get_workspace_path with workspace name."""
#     with pytest.raises(SystemExit):
#         get_workspace_path(temp_workspace)
