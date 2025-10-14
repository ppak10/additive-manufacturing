from pathlib import Path
import shutil
from typing import Optional, List


def initialize_parts_folder(
    workspace_path: Path,
    include_defaults: bool = False,
) -> tuple[Path, Optional[List[str]]]:
    """
    Initialize parts folder within workspace.

    Args:
        workspace_path: Path to the workspace directory
        include_defaults: If True, copies default part files from data directory

    Returns:
        A tuple of (parts_dir_path, copied_files_list or None)

    Raises:
        FileNotFoundError: If data parts directory not found when include_defaults is True
        PermissionError: If permission denied when creating directories or copying files
        Exception: For other errors during initialization
    """
    # Create parts directory
    parts_dir = workspace_path / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    copied_files = None

    if include_defaults:
        # Get the data/parts directory
        from am.data import DATA_DIR

        data_parts_dir = DATA_DIR / "parts"

        if not data_parts_dir.exists():
            raise FileNotFoundError(
                f"Data parts directory not found at {data_parts_dir}"
            )

        # Copy all files from data/parts to workspace/parts
        copied_files = []
        for file_path in data_parts_dir.iterdir():
            if file_path.is_file() and file_path.name != "README.md":
                dest_path = parts_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                copied_files.append(file_path.name)

    return parts_dir, copied_files
