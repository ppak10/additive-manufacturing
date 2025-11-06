import shutil

from pathlib import Path

def initialize_parts(
    workspace_path: Path,
    include_examples: bool = False,
) -> Path:
    """
    Create parts subfolder within workspace.
    """
    # Create parts directory
    parts_dir = workspace_path / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    copied_files = None

    if include_examples:
        # Get the data/parts directory
        from am.data import DATA_DIR

        data_parts_dir = DATA_DIR / "parts"

        # Copy all files from data/parts to workspace/parts
        copied_files = []
        for file_path in data_parts_dir.iterdir():
            dest_path = parts_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            copied_files.append(file_path.name)

    return parts_dir

