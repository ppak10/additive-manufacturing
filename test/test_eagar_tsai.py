import numpy as np
import pytest

from am import EagarTsai


@pytest.fixture(scope="module")
def et():
    mesh = {
        "b_c": "temp",
        "x_min": -1000e-5,
        "x_max": 1000e-5,
        "y_min": -1000e-5,
        "y_max": 1000e-5,
        "z_min": -200e-6,
        "z_max": 0,
    }
    return EagarTsai(mesh=mesh)


def test_meltpool(et):
    timestep = 1000e-6
    et.forward(timestep, 0)
    et.forward(timestep, np.pi / 2)
    results = et.meltpool(True, True)
    assert results == (
        0.0007068471341075093,
        0.0011168172228484458,
        -0.00018828654068492814,
    )
