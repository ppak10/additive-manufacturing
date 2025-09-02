import pytest
import json
import tempfile
from pathlib import Path
from pint import Quantity

from am.process_map.schema import ProcessMap, ProcessMapDict


class TestProcessMap:
    def test_empty_initialization(self):
        process_map = ProcessMap()
        assert process_map.parameters == []
        assert process_map.points == []

    def test_initialization_with_parameters(self):
        parameters = ["temperature", "velocity", "power"]
        process_map = ProcessMap(parameters=parameters)
        assert process_map.parameters == parameters
        assert process_map.points == []

    def test_initialization_with_points(self):
        points = [
            [Quantity(100, "kelvin"), Quantity(0.5, "m/s")],
            [Quantity(200, "kelvin"), Quantity(1.0, "m/s")],
        ]
        process_map = ProcessMap(points=points)
        assert process_map.parameters == []
        assert len(process_map.points) == 2
        assert process_map.points[0][0] == Quantity(100, "kelvin")
        assert process_map.points[1][1] == Quantity(1.0, "m/s")

    def test_full_initialization(self):
        parameters = ["temperature", "velocity"]
        points = [
            [Quantity(100, "kelvin"), Quantity(0.5, "m/s")],
            [Quantity(200, "kelvin"), Quantity(1.0, "m/s")],
        ]
        process_map = ProcessMap(parameters=parameters, points=points)
        assert process_map.parameters == parameters
        assert len(process_map.points) == 2


class TestQuantityConversionMethods:
    def test_quantity_to_dict_simple(self):
        q = Quantity(100, "kelvin")
        result = ProcessMap._quantity_to_dict(q)
        expected = {"magnitude": 100.0, "units": "kelvin"}
        assert result == expected

    def test_quantity_to_dict_float(self):
        q = Quantity(3.14159, "meter")
        result = ProcessMap._quantity_to_dict(q)
        expected = {"magnitude": 3.14159, "units": "meter"}
        assert result == expected

    def test_quantity_to_dict_complex_units(self):
        q = Quantity(9.8, "meter/second**2")
        result = ProcessMap._quantity_to_dict(q)
        expected = {"magnitude": 9.8, "units": "meter / second ** 2"}
        assert result == expected

    def test_dict_to_quantity_simple(self):
        d = {"magnitude": 100.0, "units": "kelvin"}
        result = ProcessMap._dict_to_quantity(d)
        expected = Quantity(100.0, "kelvin")
        assert result == expected

    def test_dict_to_quantity_float(self):
        d = {"magnitude": 3.14159, "units": "meter"}
        result = ProcessMap._dict_to_quantity(d)
        expected = Quantity(3.14159, "meter")
        assert result == expected

    def test_dict_to_quantity_complex_units(self):
        d = {"magnitude": 9.8, "units": "meter/second**2"}
        result = ProcessMap._dict_to_quantity(d)
        expected = Quantity(9.8, "meter/second**2")
        assert result == expected

    def test_quantity_conversion_roundtrip(self):
        original = Quantity(42.5, "watts/meter**2")
        dict_form = ProcessMap._quantity_to_dict(original)
        converted_back = ProcessMap._dict_to_quantity(dict_form)
        assert converted_back == original


class TestProcessMapSerialization:
    def test_empty_serialization(self):
        process_map = ProcessMap()
        result = process_map.model_dump()
        expected = {"parameters": [], "points": []}
        assert result == expected

    def test_parameters_only_serialization(self):
        process_map = ProcessMap(parameters=["temp", "power"])
        result = process_map.model_dump()
        expected = {"parameters": ["temp", "power"], "points": []}
        assert result == expected

    def test_single_point_serialization(self):
        parameters = ["temperature", "power"]
        points = [[Quantity(200, "kelvin"), Quantity(100, "watts")]]
        process_map = ProcessMap(parameters=parameters, points=points)
        result = process_map.model_dump()

        expected = {
            "parameters": ["temperature", "power"],
            "points": [
                {
                    "temperature": {"magnitude": 200.0, "units": "kelvin"},
                    "power": {"magnitude": 100.0, "units": "watt"},
                }
            ],
        }
        assert result == expected

    def test_multiple_points_serialization(self):
        parameters = ["temperature", "velocity", "power"]
        points = [
            [Quantity(100, "kelvin"), Quantity(0.5, "m/s"), Quantity(150, "watts")],
            [Quantity(200, "kelvin"), Quantity(1.0, "m/s"), Quantity(200, "watts")],
            [Quantity(300, "kelvin"), Quantity(1.5, "m/s"), Quantity(250, "watts")],
        ]
        process_map = ProcessMap(parameters=parameters, points=points)
        result = process_map.model_dump()

        print(result)

        expected = {
            "parameters": ["temperature", "velocity", "power"],
            "points": [
                {
                    "temperature": {"magnitude": 100.0, "units": "kelvin"},
                    "velocity": {"magnitude": 0.5, "units": "meter / second"},
                    "power": {"magnitude": 150.0, "units": "watt"},
                },
                {
                    "temperature": {"magnitude": 200.0, "units": "kelvin"},
                    "velocity": {"magnitude": 1.0, "units": "meter / second"},
                    "power": {"magnitude": 200.0, "units": "watt"},
                },
                {
                    "temperature": {"magnitude": 300.0, "units": "kelvin"},
                    "velocity": {"magnitude": 1.5, "units": "meter / second"},
                    "power": {"magnitude": 250.0, "units": "watt"},
                },
            ],
        }
        assert result == expected

    def test_mismatched_parameters_and_points(self):
        parameters = ["temperature", "power"]
        points = [
            [Quantity(100, "kelvin"), Quantity(50, "watts"), Quantity(0.5, "m/s")]
        ]
        process_map = ProcessMap(parameters=parameters, points=points)
        result = process_map.model_dump()

        assert len(result["points"]) == 1
        assert len(result["points"][0]) == 2
        assert "temperature" in result["points"][0]
        assert "power" in result["points"][0]

    def test_complex_units_serialization(self):
        parameters = ["acceleration", "density"]
        points = [
            [Quantity(9.8, "meter/second**2"), Quantity(2.7, "gram/centimeter**3")]
        ]
        process_map = ProcessMap(parameters=parameters, points=points)
        result = process_map.model_dump()

        expected = {
            "parameters": ["acceleration", "density"],
            "points": [
                {
                    "acceleration": {"magnitude": 9.8, "units": "meter / second ** 2"},
                    "density": {"magnitude": 2.7, "units": "gram / centimeter ** 3"},
                }
            ],
        }
        assert result == expected


class TestProcessMapSaveLoad:
    def test_save_empty_process_map(self):
        process_map = ProcessMap()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_empty.json"
            returned_path = process_map.save(path)

            assert returned_path == path
            assert path.exists()

            with open(path) as f:
                data = json.load(f)

            expected = {"parameters": [], "points": []}
            assert data == expected

    def test_save_process_map_with_data(self):
        parameters = ["temperature", "power"]
        points = [
            [Quantity(100, "kelvin"), Quantity(50, "watts")],
            [Quantity(200, "kelvin"), Quantity(100, "watts")],
        ]
        process_map = ProcessMap(parameters=parameters, points=points)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_data.json"
            process_map.save(path)

            with open(path) as f:
                data = json.load(f)

            expected = {
                "parameters": ["temperature", "power"],
                "points": [
                    {
                        "temperature": {"magnitude": 100.0, "units": "kelvin"},
                        "power": {"magnitude": 50.0, "units": "watt"},
                    },
                    {
                        "temperature": {"magnitude": 200.0, "units": "kelvin"},
                        "power": {"magnitude": 100.0, "units": "watt"},
                    },
                ],
            }
            assert data == expected

    def test_load_empty_process_map(self):
        data = {"parameters": [], "points": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_load_empty.json"
            with open(path, "w") as f:
                json.dump(data, f)

            loaded_map = ProcessMap.load(path)
            assert loaded_map.parameters == []
            assert loaded_map.points == []

    def test_load_process_map_with_data(self):
        data = {
            "parameters": ["temperature", "velocity"],
            "points": [
                {
                    "temperature": {"magnitude": 150.0, "units": "kelvin"},
                    "velocity": {"magnitude": 0.8, "units": "meter / second"},
                },
                {
                    "temperature": {"magnitude": 250.0, "units": "kelvin"},
                    "velocity": {"magnitude": 1.2, "units": "meter / second"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test_load_data.json"
            with open(path, "w") as f:
                json.dump(data, f)

            loaded_map = ProcessMap.load(path)
            assert loaded_map.parameters == ["temperature", "velocity"]
            assert len(loaded_map.points) == 2
            assert loaded_map.points[0][0] == Quantity(150.0, "kelvin")
            assert loaded_map.points[0][1] == Quantity(0.8, "meter / second")
            assert loaded_map.points[1][0] == Quantity(250.0, "kelvin")
            assert loaded_map.points[1][1] == Quantity(1.2, "meter / second")

    def test_save_load_roundtrip(self):
        parameters = ["acceleration", "force"]
        points = [
            [Quantity(9.8, "meter/second**2"), Quantity(100, "newton")],
            [Quantity(4.9, "meter/second**2"), Quantity(50, "newton")],
        ]
        original_map = ProcessMap(parameters=parameters, points=points)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roundtrip.json"
            original_map.save(path)
            loaded_map = ProcessMap.load(path)

            assert loaded_map.parameters == original_map.parameters
            assert len(loaded_map.points) == len(original_map.points)
            for i, point in enumerate(loaded_map.points):
                for j, quantity in enumerate(point):
                    assert quantity == original_map.points[i][j]


class TestProcessMapFromDict:
    def test_from_dict_empty(self):
        data = {"parameters": [], "points": []}
        process_map = ProcessMap.from_dict(data)
        assert process_map.parameters == []
        assert process_map.points == []

    def test_from_dict_with_data(self):
        data = {
            "parameters": ["temperature", "power"],
            "points": [
                {
                    "temperature": {"magnitude": 300.0, "units": "kelvin"},
                    "power": {"magnitude": 75.0, "units": "watt"},
                }
            ],
        }

        process_map = ProcessMap.from_dict(data)
        assert process_map.parameters == ["temperature", "power"]
        assert len(process_map.points) == 1
        assert process_map.points[0][0] == Quantity(300.0, "kelvin")
        assert process_map.points[0][1] == Quantity(75.0, "watt")

    def test_from_dict_missing_parameters(self):
        data = {"points": []}
        process_map = ProcessMap.from_dict(data)
        assert process_map.parameters == []
        assert process_map.points == []

    def test_from_dict_missing_points(self):
        data = {"parameters": ["temp"]}
        process_map = ProcessMap.from_dict(data)
        assert process_map.parameters == ["temp"]
        assert process_map.points == []
