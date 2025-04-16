import pytest

from am import GCodeSegmenter
from cerberus import Validator

segment_validator = Validator(
    {
        "X": {"type": "list"},
        "Y": {"type": "list"},
        "Z": {"type": "list"},
        "E": {"type": "list"},
        "angle_xy": {"type": "float"},
        "distance_xy": {"type": "float"},
        "travel": {"type": "boolean"},
    }
)


@pytest.fixture(scope="module")
def gs():
    return GCodeSegmenter()


def is_list_of(value, item_type):
    if not isinstance(value, list):
        return False
    return all(isinstance(item, item_type) for item in value)


def test_init(gs):
    assert gs.gcode_commands == []
    assert gs.gcode_layer_change_indexes == []


def test_load_gcode_commands(gs):
    with pytest.raises(TypeError):
        gs.load_gcode_commands()

    gcode_commands = gs.load_gcode_commands("example/3DBenchy.gcode")
    assert is_list_of(gcode_commands, dict)
    assert is_list_of(gs.gcode_commands, dict)
    assert is_list_of(gs.gcode_layer_numbers, int)


def test_get_gcode_commands_by_layer_change_index(gs):
    with pytest.raises(TypeError):
        gs.get_gcode_commands_by_layer_change_index()

    for index in range(2):
        gcode_commands = gs.get_gcode_commands_by_layer_change_index(index)
        assert is_list_of(gcode_commands, dict)


def test_gcode_commands_to_segments(gs):
    with pytest.raises(TypeError):
        gs.gcode_commands_to_segments()

    for index in range(2):
        gcode_commands = gs.get_gcode_commands_by_layer_change_index(index)
        segments = gs.gcode_commands_to_segments(gcode_commands)
        assert is_list_of(segments, dict)

        if len(segments):
            assert segment_validator.validate(segments[0])
