from pathlib import Path

from am.config import BuildParameters, Material, MeshParameters

def initialize_configs(workspace_path: Path) -> Path:
    """
    Initialize configs subfolder within workspace with defaults.
    """

    # Create parts directory
    configs_path = workspace_path / "configs"
    configs_path.mkdir(parents=True, exist_ok=True)

    build_parameters = BuildParameters()
    build_parameters_path = configs_path / "build_parameters" / "default.json"
    _ = build_parameters.save(build_parameters_path)

    material = Material()
    material_path = configs_path / "materials" / "default.json"
    _ = material.save(material_path)

    mesh_parameters = MeshParameters()
    mesh_parameters_path = configs_path / "mesh_parameters" / "default.json"
    _ = mesh_parameters.save(mesh_parameters_path)

    return configs_path

