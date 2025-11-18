import jax.numpy as jnp
from jax import lax
from typing import Tuple, Union


def make_gaussian_kernel_1d(sigma: float, truncate: float = 4.0) -> jnp.ndarray:
    """Build a normalized 1D Gaussian kernel."""
    radius = int(truncate * sigma + 0.5)
    xs = jnp.arange(-radius, radius + 1)
    g = jnp.exp(-0.5 * (xs / sigma) ** 2)
    g = g / jnp.sum(g)
    return g


def make_gaussian_kernel_3d(sigma: float, truncate: float = 4.0) -> jnp.ndarray:
    """Construct a separable 3D Gaussian kernel."""
    g1 = make_gaussian_kernel_1d(sigma, truncate)
    g3 = jnp.einsum("i,j,k->ijk", g1, g1, g1)
    g3 = g3 / jnp.sum(g3)
    return g3


def gaussian_blur_3d(
    grid: jnp.ndarray,
    sigma: float,
    padding: Union[
        str, Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    ] = "SAME",
    truncate: float = 4.0,
) -> jnp.ndarray:
    """
    Apply a 3D Gaussian blur using JAX.

    Args:
        grid: 3D array (X, Y, Z)
        sigma: standard deviation of the Gaussian kernel
        padding: either "SAME", "VALID", or a tuple specifying manual padding
        truncate: radius of the kernel in standard deviations

    Returns:
        Blurred grid of same shape (if padding="SAME")
    """
    kernel = make_gaussian_kernel_3d(sigma, truncate)
    in_arr = grid[None, None, :, :, :]  # (N=1, C=1, D, H, W)
    kernel_arr = kernel[None, None, :, :, :]  # (out_chan=1, in_chan=1, Kd, Kh, Kw)

    out = lax.conv_general_dilated(
        lhs=in_arr,
        rhs=kernel_arr,
        window_strides=(1, 1, 1),
        padding=padding,  # configurable padding
        dimension_numbers=("NCDHW", "OIDHW", "NCDHW"),
    )
    return out[0, 0, :, :, :]
