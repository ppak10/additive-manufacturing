from mcp.server.fastmcp import FastMCP
from typing import Union

from am.mcp.types import ToolSuccess, ToolError
from am.mcp.utils import tool_success, tool_error
from am.config.build_parameters import BuildParametersInput
from am.config.material import MaterialInput
from am.config.mesh_parameters import MeshParametersInput


def register_config(app: FastMCP):

    @app.tool(
        title="AM Configuration Manager",
        description="Create AM configuration files for build parameters, material properties, and mesh parameters. Provide one or more config objects to create the corresponding files.",
        structured_output=True,
    )
    async def config(
        workspace: str,
        name: str = "default",
        build_parameters: BuildParametersInput | None = None,
        material: MaterialInput | None = None,
        mesh_parameters: MeshParametersInput | None = None,
    ) -> Union[ToolSuccess[dict], ToolError]:
        """
        Create AM configuration files.

        Provide one or more config objects to create the corresponding files.
        Each config is optional - only provided configs will be created.

        Args:
            workspace: Folder name of existing workspace
            name: Used in generating file names for saved configurations (defaults to "default")
            build_parameters: Build parameters configuration (beam diameter, power, velocity, etc.)
            material: Material properties configuration (density, thermal conductivity, etc.)
            mesh_parameters: Mesh parameters configuration (step sizes, bounds, padding, etc.)

        Returns:
            Dictionary with list of created configuration file paths
        """
        from am.config import BuildParameters, Material, MeshParameters
        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace)
            created_files = []

            # Create build parameters config if provided
            if build_parameters is not None:
                # Handle both dict and Pydantic model inputs
                bp_data = (
                    build_parameters
                    if isinstance(build_parameters, dict)
                    else build_parameters.model_dump()
                )
                bp = BuildParameters(**bp_data)
                save_path = (
                    workspace_path / "configs" / "build_parameters" / f"{name}.json"
                )
                bp.save(save_path)
                created_files.append(str(save_path))

            # Create material config if provided
            if material is not None:
                # Handle both dict and Pydantic model inputs
                mat_data = (
                    material if isinstance(material, dict) else material.model_dump()
                )
                mat = Material(name=name, **mat_data)
                save_path = workspace_path / "configs" / "materials" / f"{name}.json"
                mat.save(save_path)
                created_files.append(str(save_path))

            # Create mesh parameters config if provided
            if mesh_parameters is not None:
                # Handle both dict and Pydantic model inputs
                mesh_data = (
                    mesh_parameters
                    if isinstance(mesh_parameters, dict)
                    else mesh_parameters.model_dump()
                )
                mesh = MeshParameters(**mesh_data)
                save_path = (
                    workspace_path / "configs" / "mesh_parameters" / f"{name}.json"
                )
                mesh.save(save_path)
                created_files.append(str(save_path))

            if not created_files:
                return tool_error(
                    "No configuration objects provided. Please provide at least one of: build_parameters, material, or mesh_parameters.",
                    "NO_CONFIG_PROVIDED",
                    workspace_name=workspace,
                )

            return tool_success({"created_files": created_files, "name": name})

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating configuration file.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create configuration file",
                "CONFIG_CREATION_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = config
