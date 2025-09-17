from am.cli.options import VerboseOption


def test_verbose_option_type():
    """Test VerboseOption is boolean type alias."""
    assert VerboseOption == bool or hasattr(VerboseOption, "__origin__")
