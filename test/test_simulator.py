import pytest

from am import Simulator
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
def s():
    return Simulator()


def is_list_of(value, item_type):
    if not isinstance(value, list):
        return False
    return all(isinstance(item, item_type) for item in value)


def test_init(s):
    # TODO: Add tests for Eagar Tsai class
    assert s.gcode_commands == []
    assert s.gcode_layer_change_indexes == []


def test_load_gcode_commands(s):
    with pytest.raises(TypeError):
        s.load_gcode_commands()

    gcode_commands = s.load_gcode_commands("example/3DBenchy.gcode")
    assert is_list_of(gcode_commands, dict)
    assert is_list_of(s.gcode_commands, dict)
    assert is_list_of(s.gcode_layer_numbers, int)


def test_get_gcode_commands_by_layer_change_index(s):
    with pytest.raises(TypeError):
        s.get_gcode_commands_by_layer_change_index()

    for index in range(2):
        gcode_commands = s.get_gcode_commands_by_layer_change_index(index)
        assert is_list_of(gcode_commands, dict)


def test_gcode_commands_to_segments(s):
    with pytest.raises(TypeError):
        s.gcode_commands_to_segments()

    for index in range(2):
        gcode_commands = s.get_gcode_commands_by_layer_change_index(index)
        segments = s.gcode_commands_to_segments(gcode_commands)
        assert is_list_of(segments, dict)

        if len(segments):
            assert segment_validator.validate(segments[0])
