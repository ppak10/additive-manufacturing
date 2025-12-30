import pytest
import importlib.metadata

from typer.testing import CliRunner
from am.cli import app


@pytest.fixture
def runner():
    return CliRunner(env={"NO_COLOR": "1"})


def test_main_help(runner):
    """Test main CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Additive Manufacturing" in result.stdout
    assert "solver" in result.stdout
    assert "mcp" in result.stdout


def test_main_no_args(runner):
    """Test main CLI with no arguments shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Additive Manufacturing" in result.stdout


def test_version_command(runner):
    """Test version command."""
    result = runner.invoke(app, ["version"])
    version = importlib.metadata.version("additive-manufacturing")
    assert result.exit_code == 0
    assert f"{version}" in result.stdout


def test_invalid_command(runner):
    """Test invalid command returns error."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0


def test_solver_subcommand_exists(runner):
    """Test solver subcommand is available."""
    result = runner.invoke(app, ["solver", "--help"])
    assert result.exit_code == 0
    assert "Solver management" in result.stdout


def test_mcp_subcommand_exists(runner):
    """Test mcp subcommand is available."""
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
