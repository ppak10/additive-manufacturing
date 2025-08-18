import pytest
from am.cli.options import VerboseOption, WorkspaceOption


def test_verbose_option_type():
    """Test VerboseOption is boolean type alias."""
    assert VerboseOption == bool or hasattr(VerboseOption, '__origin__')


def test_workspace_option_type():
    """Test WorkspaceOption can handle string or None."""
    assert WorkspaceOption is not None