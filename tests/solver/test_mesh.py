import jax.numpy as jnp
import numpy as np
import pytest
import tempfile

from pathlib import Path
from pint import Quantity

from am.config import Segment
from am.solver.mesh import SolverMesh
from am.config import MeshParameters


@pytest.fixture
def mesh_config():
    """Create a simple MeshConfig for testing."""
    return MeshParameters(
        x_step=Quantity(0.1, "mm"),
        y_step=Quantity(0.1, "mm"),
        z_step=Quantity(0.1, "mm"),
        x_min=Quantity(0.0, "mm"),
        x_max=Quantity(1.0, "mm"),
        y_min=Quantity(0.0, "mm"),
        y_max=Quantity(1.0, "mm"),
        z_min=Quantity(0.0, "mm"),
        z_max=Quantity(0.5, "mm"),
        x_initial=Quantity(0.5, "mm"),
        y_initial=Quantity(0.5, "mm"),
        z_initial=Quantity(0.0, "mm"),
        x_start_pad=Quantity(0.1, "mm"),
        y_start_pad=Quantity(0.1, "mm"),
        z_start_pad=Quantity(0.0, "mm"),
        x_end_pad=Quantity(0.1, "mm"),
        y_end_pad=Quantity(0.1, "mm"),
        z_end_pad=Quantity(0.1, "mm"),
        boundary_condition="temperature",
    )


@pytest.fixture
def solver_mesh():
    """Create a SolverMesh instance for testing."""
    return SolverMesh()


class TestSolverMeshInitialization:
    """Test SolverMesh initialization."""

    def test_create_instance(self, solver_mesh):
        """Test that SolverMesh can be instantiated."""
        assert isinstance(solver_mesh, SolverMesh)

    def test_initialize_grid(self, solver_mesh, mesh_config):
        """Test grid initialization with MeshConfig."""
        fill_value = 300.0
        grid = solver_mesh.initialize_grid(mesh_config, fill_value)

        # Check grid shape matches expected dimensions
        x_size = len(solver_mesh.x_range)
        y_size = len(solver_mesh.y_range)
        z_size = len(solver_mesh.z_range)

        assert grid.shape == (x_size, y_size, z_size)
        assert jnp.allclose(grid, fill_value)

    def test_initialize_grid_ranges(self, solver_mesh, mesh_config):
        """Test that x, y, z ranges are correctly initialized."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Check that ranges are non-empty
        assert len(solver_mesh.x_range) > 0
        assert len(solver_mesh.y_range) > 0
        assert len(solver_mesh.z_range) > 0

        # Check start and end values
        assert solver_mesh.x_start == mesh_config.x_start.to("meter").magnitude
        assert solver_mesh.x_end == mesh_config.x_end.to("meter").magnitude
        assert solver_mesh.y_start == mesh_config.y_start.to("meter").magnitude
        assert solver_mesh.y_end == mesh_config.y_end.to("meter").magnitude
        assert solver_mesh.z_start == mesh_config.z_start.to("meter").magnitude
        assert solver_mesh.z_end == mesh_config.z_end.to("meter").magnitude

    def test_initialize_grid_step_sizes(self, solver_mesh, mesh_config):
        """Test that step sizes are correctly set."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        assert solver_mesh.x_step == mesh_config.x_step.to("meter").magnitude
        assert solver_mesh.y_step == mesh_config.y_step.to("meter").magnitude
        assert solver_mesh.z_step == mesh_config.z_step.to("meter").magnitude

    def test_initialize_grid_initial_positions(self, solver_mesh, mesh_config):
        """Test that initial positions are correctly set."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        assert solver_mesh.x == mesh_config.x_initial.to("m").magnitude
        assert solver_mesh.y == mesh_config.y_initial.to("m").magnitude
        assert solver_mesh.z == mesh_config.z_initial.to("m").magnitude

    def test_initialize_grid_centered_ranges(self, solver_mesh, mesh_config):
        """Test that centered ranges are computed correctly."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Check that centered x and y ranges are centered around 0
        x_mid = solver_mesh.x_range[len(solver_mesh.x_range) // 2]
        y_mid = solver_mesh.y_range[len(solver_mesh.y_range) // 2]

        assert jnp.allclose(
            solver_mesh.x_range_centered[len(solver_mesh.x_range) // 2], 0.0, atol=1e-6
        )
        assert jnp.allclose(
            solver_mesh.y_range_centered[len(solver_mesh.y_range) // 2], 0.0, atol=1e-6
        )
        # z_range_centered should be the same as z_range
        assert jnp.allclose(solver_mesh.z_range_centered, solver_mesh.z_range)


class TestSolverMeshDiffusion:
    """Test diffusion functionality."""

    def test_diffuse_zero_time(self, solver_mesh, mesh_config):
        """Test that diffusion with zero time does nothing."""
        solver_mesh.initialize_grid(mesh_config, 300.0)
        grid_before = solver_mesh.grid.copy()

        solver_mesh.diffuse(
            delta_time=Quantity(0.0, "s"),
            diffusivity=Quantity(1e-5, "m**2/s"),
            grid_offset=300.0,
        )

        assert jnp.allclose(solver_mesh.grid, grid_before)

    def test_diffuse_with_positive_time(self, solver_mesh, mesh_config):
        """Test that diffusion with positive time changes the grid."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Add a hot spot in the center
        mid_x = len(solver_mesh.x_range) // 2
        mid_y = len(solver_mesh.y_range) // 2
        mid_z = len(solver_mesh.z_range) // 2
        solver_mesh.grid = solver_mesh.grid.at[mid_x, mid_y, mid_z].set(1000.0)

        grid_before = solver_mesh.grid.copy()

        solver_mesh.diffuse(
            delta_time=Quantity(1e-3, "s"),
            diffusivity=Quantity(1e-5, "m**2/s"),
            grid_offset=300.0,
        )

        # The grid should change after diffusion
        assert not jnp.allclose(solver_mesh.grid, grid_before)

    def test_diffuse_temperature_boundary_condition(self, solver_mesh, mesh_config):
        """Test diffusion with temperature boundary condition."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        solver_mesh.diffuse(
            delta_time=Quantity(1e-3, "s"),
            diffusivity=Quantity(1e-5, "m**2/s"),
            grid_offset=300.0,
            boundary_condition="temperature",
        )

        # Should complete without error
        assert solver_mesh.grid is not None

    def test_diffuse_flux_boundary_condition(self, solver_mesh, mesh_config):
        """Test diffusion with flux boundary condition."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        solver_mesh.diffuse(
            delta_time=Quantity(1e-3, "s"),
            diffusivity=Quantity(1e-5, "m**2/s"),
            grid_offset=300.0,
            boundary_condition="flux",
        )

        # Should complete without error
        assert solver_mesh.grid is not None


class TestSolverMeshUpdateXY:
    """Test update_xy functionality."""

    def test_update_xy_absolute_mode(self, solver_mesh, mesh_config):
        """Test updating x, y positions in absolute mode."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        segment = Segment(
            x=Quantity(0.5, "mm"),
            y=Quantity(0.5, "mm"),
            z=Quantity(0.0, "mm"),
            e=Quantity(0.0, "mm"),
            x_next=Quantity(0.7, "mm"),
            y_next=Quantity(0.8, "mm"),
            z_next=Quantity(0.0, "mm"),
            e_next=Quantity(1.0, "mm"),
            angle_xy=Quantity(45.0, "degree"),
            distance_xy=Quantity(0.3, "mm"),
            travel=False,
        )

        x_before = solver_mesh.x
        y_before = solver_mesh.y

        solver_mesh.update_xy(segment, mode="absolute")

        # Positions should have changed
        assert solver_mesh.x != x_before
        assert solver_mesh.y != y_before

        # Check that new positions match segment
        assert np.isclose(
            solver_mesh.x, segment.x_next.to("m").magnitude, rtol=1e-5
        )
        assert np.isclose(
            solver_mesh.y, segment.y_next.to("m").magnitude, rtol=1e-5
        )

    def test_update_xy_updates_indices(self, solver_mesh, mesh_config):
        """Test that update_xy also updates x_index and y_index."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        segment = Segment(
            x=Quantity(0.5, "mm"),
            y=Quantity(0.5, "mm"),
            z=Quantity(0.0, "mm"),
            e=Quantity(0.0, "mm"),
            x_next=Quantity(0.7, "mm"),
            y_next=Quantity(0.8, "mm"),
            z_next=Quantity(0.0, "mm"),
            e_next=Quantity(1.0, "mm"),
            angle_xy=Quantity(45.0, "degree"),
            distance_xy=Quantity(0.3, "mm"),
            travel=False,
        )

        x_index_before = solver_mesh.x_index
        y_index_before = solver_mesh.y_index

        solver_mesh.update_xy(segment, mode="absolute")

        # Indices should have changed
        assert solver_mesh.x_index != x_index_before or solver_mesh.y_index != y_index_before


class TestSolverMeshGraft:
    """Test graft functionality."""

    def test_graft_adds_to_grid(self, solver_mesh, mesh_config):
        """Test that graft adds values to the grid."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Create a theta array with some values
        theta = jnp.ones_like(solver_mesh.grid) * 400.0

        grid_before = solver_mesh.grid.copy()

        solver_mesh.graft(theta, grid_offset=300.0)

        # Grid values should have increased
        assert jnp.any(solver_mesh.grid > grid_before)


class TestSolverMeshSaveLoad:
    """Test save and load functionality."""

    def test_save_creates_file(self, solver_mesh, mesh_config):
        """Test that save creates a file."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_mesh.npz"
            result_path = solver_mesh.save(save_path)

            assert result_path.exists()
            assert result_path == save_path

    def test_load_restores_mesh(self, solver_mesh, mesh_config):
        """Test that load restores a saved mesh."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Modify the grid
        solver_mesh.grid = solver_mesh.grid.at[0, 0, 0].set(1000.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_mesh.npz"
            solver_mesh.save(save_path)

            # Load into a new instance
            loaded_mesh = SolverMesh.load(save_path)

            # Check that ranges match
            assert jnp.allclose(loaded_mesh.x_range, solver_mesh.x_range)
            assert jnp.allclose(loaded_mesh.y_range, solver_mesh.y_range)
            assert jnp.allclose(loaded_mesh.z_range, solver_mesh.z_range)

            # Check that grid matches
            assert jnp.allclose(loaded_mesh.grid, solver_mesh.grid)

            # Check that start/end/step values match
            assert loaded_mesh.x_start == solver_mesh.x_start
            assert loaded_mesh.y_start == solver_mesh.y_start
            assert loaded_mesh.z_start == solver_mesh.z_start
            assert loaded_mesh.x_end == solver_mesh.x_end
            assert loaded_mesh.y_end == solver_mesh.y_end
            assert loaded_mesh.z_end == solver_mesh.z_end
            assert loaded_mesh.x_step == solver_mesh.x_step
            assert loaded_mesh.y_step == solver_mesh.y_step
            assert loaded_mesh.z_step == solver_mesh.z_step


class TestSolverMeshVisualization:
    """Test visualization functionality."""

    def test_visualize_2d_creates_plot(self, solver_mesh, mesh_config):
        """Test that visualize_2D creates a plot."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        fig, ax, mesh = solver_mesh.visualize_2D()

        assert fig is not None
        assert ax is not None
        assert mesh is not None

    def test_visualize_2d_with_parameters(self, solver_mesh, mesh_config):
        """Test visualize_2D with custom parameters."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        fig, ax, mesh = solver_mesh.visualize_2D(
            cmap="viridis",
            include_axis=False,
            label="Custom Label",
            vmin=250.0,
            vmax=500.0,
            transparent=True,
            units="um",
        )

        assert fig is not None
        assert ax is not None
        assert mesh is not None

    def test_visualize_2d_transparent_mode(self, solver_mesh, mesh_config):
        """Test that transparent mode masks low values."""
        solver_mesh.initialize_grid(mesh_config, 300.0)

        # Add a hot spot
        mid_x = len(solver_mesh.x_range) // 2
        mid_y = len(solver_mesh.y_range) // 2
        solver_mesh.grid = solver_mesh.grid.at[mid_x, mid_y, -1].set(1000.0)

        fig, ax, mesh = solver_mesh.visualize_2D(vmin=300.0, transparent=True)

        # Should complete without error
        assert fig is not None
