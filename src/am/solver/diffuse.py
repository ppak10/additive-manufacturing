import jax
import jax.numpy as jnp

from jax import vmap
from jax.scipy.signal import convolve
from functools import partial


@partial(jax.jit, static_argnums=(1, 2, 3))
def apply_temperature_bc(
    grid: jnp.ndarray, pad_x: int, pad_y: int, pad_z: int
) -> jnp.ndarray:
    """
    Apply temperature (Dirichlet) boundary conditions.
    Reflects and negates values at boundaries to enforce T=0.
    """
    # Pad with reflection first
    padding = ((pad_x, pad_x), (pad_y, pad_y), (pad_z, pad_z))
    grid_padded = jnp.pad(grid, padding, mode="reflect")

    # Create masks for boundary regions and apply sign flip
    # More efficient than multiple .set() operations

    # X boundaries
    x_low_mask = jnp.arange(grid_padded.shape[0]) < pad_x
    x_high_mask = jnp.arange(grid_padded.shape[0]) >= grid_padded.shape[0] - pad_x
    grid_padded = jnp.where(x_low_mask[:, None, None], -grid_padded, grid_padded)
    grid_padded = jnp.where(x_high_mask[:, None, None], -grid_padded, grid_padded)

    # Y boundaries
    y_low_mask = jnp.arange(grid_padded.shape[1]) < pad_y
    y_high_mask = jnp.arange(grid_padded.shape[1]) >= grid_padded.shape[1] - pad_y
    grid_padded = jnp.where(y_low_mask[None, :, None], -grid_padded, grid_padded)
    grid_padded = jnp.where(y_high_mask[None, :, None], -grid_padded, grid_padded)

    # Z boundaries (bottom: negate, top: keep positive for free surface)
    z_low_mask = jnp.arange(grid_padded.shape[2]) < pad_z
    grid_padded = jnp.where(z_low_mask[None, None, :], -grid_padded, grid_padded)

    return grid_padded


@partial(jax.jit, static_argnums=(1, 2, 3))
def apply_flux_bc(grid: jnp.ndarray, pad_x: int, pad_y: int, pad_z: int) -> jnp.ndarray:
    """
    Apply flux (Neumann) boundary conditions.
    Enforces zero gradient (∂T/∂n = 0) at boundaries.
    """
    # For Neumann BC, we use 'edge' mode which extends edge values
    # This naturally enforces zero gradient
    padding = ((pad_x, pad_x), (pad_y, pad_y), (pad_z, pad_z))
    return jnp.pad(grid, padding, mode="edge")


@partial(jax.jit, static_argnums=(0, 1))
def create_gaussian_kernel_1d(sigma: float, truncate: float = 4.0) -> jnp.ndarray:
    """
    Create a 1D Gaussian kernel for convolution.

    Args:
        sigma: Standard deviation of Gaussian in grid units
        truncate: Number of standard deviations to include

    Returns:
        Normalized 1D Gaussian kernel
    """
    if sigma < 0.1:
        return jnp.array([1.0])

    radius = int(truncate * sigma + 0.5)
    if radius == 0:
        return jnp.array([1.0])

    x = jnp.arange(-radius, radius + 1, dtype=jnp.float32)
    kernel = jnp.exp(-0.5 * (x / sigma) ** 2)
    return kernel / kernel.sum()


@partial(jax.jit, static_argnums=2)
def convolve_1d_along_axis(
    data: jnp.ndarray, kernel: jnp.ndarray, axis: int
) -> jnp.ndarray:
    """
    Perform 1D convolution along a specific axis using JAX.

    Args:
        data: Input 3D array
        kernel: 1D convolution kernel
        axis: Axis along which to convolve (0, 1, or 2)

    Returns:
        Convolved array
    """
    # Move the target axis to the last position
    data_moved = jnp.moveaxis(data, axis, -1)

    # Get shape for reshaping
    shape = data_moved.shape
    n_elements = shape[-1]
    n_vectors = data_moved.size // n_elements

    # Reshape to 2D for vectorized convolution
    data_2d = data_moved.reshape(n_vectors, n_elements)

    # Define convolution for a single row
    def convolve_row(row):
        return convolve(row, kernel, mode="same")

    # Vectorize the convolution over all rows
    result_2d = vmap(convolve_row)(data_2d)

    # Reshape back to original shape and move axis back
    result = result_2d.reshape(shape)
    return jnp.moveaxis(result, -1, axis)


@partial(jax.jit, static_argnums=(1, 2, 3, 4))
def separable_gaussian_blur_3d(
    grid: jnp.ndarray,
    sigma_x: float,
    sigma_y: float,
    sigma_z: float,
    truncate: float = 4.0,
) -> jnp.ndarray:
    """
    Perform separable 3D Gaussian blur using three 1D convolutions.
    This reduces complexity from O(MNP*mnp) to O(MNP*(m+n+p)).

    The separability property of Gaussian:
    G(x,y,z) = G(x) * G(y) * G(z)

    Args:
        grid: 3D array to blur
        sigma_x, sigma_y, sigma_z: Standard deviations in grid units for each axis
        truncate: Number of standard deviations to include in kernel

    Returns:
        Blurred 3D array
    """
    result = grid

    # Apply 1D Gaussian filter along each axis
    # Order doesn't matter due to separability property

    # Along X-axis (axis 0)
    if sigma_x > 0.1:
        kernel_x = create_gaussian_kernel_1d(sigma_x, truncate)
        result = convolve_1d_along_axis(result, kernel_x, axis=0)

    # Along Y-axis (axis 1)
    if sigma_y > 0.1:
        kernel_y = create_gaussian_kernel_1d(sigma_y, truncate)
        result = convolve_1d_along_axis(result, kernel_y, axis=1)

    # Along Z-axis (axis 2)
    if sigma_z > 0.1:
        kernel_z = create_gaussian_kernel_1d(sigma_z, truncate)
        result = convolve_1d_along_axis(result, kernel_z, axis=2)

    return result
