import numpy as np

from typing import TypedDict


class SolverForwardParameters(TypedDict):
    absorptivity: float | None
    beam_diameter: float | None
    c_p: float | None
    dt: float
    k: float | None
    phi: float
    power: float | None
    rho: float | None
    t_0: float | None
    velocity: float | None
    xs = np.ndarray | None
    ys = np.ndarray | None
    zs = np.ndarray | None


class SolverForwardState(TypedDict, total=False):
    location: list[float]
    location_idx: list[int]
    theta: np.ndarray
