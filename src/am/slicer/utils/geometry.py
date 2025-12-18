from pathlib import Path
from shapely import from_wkb, from_wkt, to_wkb, to_wkt, Geometry


def save_geometries(
    geometries: list[Geometry],
    out_path: Path,
    binary: bool = True,
) -> Path:
    """
    Save geometries to a file in WKB or WKT format.

    Args:
        geometries: List of Shapely geometries to save
        out_path: Path along with file extension where geometries will be saved.
        binary: If True, save as WKB (.wkb), otherwise as WKT (.txt)

    Returns:
        Path to the saved file
    """
    if binary:
        geometries_list = [to_wkb(g) for g in geometries]
        output = [g_bytes.hex() for g_bytes in geometries_list]
    else:
        output = [to_wkt(g) for g in geometries]

    with open(out_path, "w") as f:
        f.write("\n".join(output))

    return out_path


def load_geometries(file_path: Path, binary: bool) -> list[Geometry]:
    """
    Load geometries from a toolpath file.
    """

    geometries = []
    if binary:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        g_bytes = bytes.fromhex(line)
                        geometries.append(from_wkb(g_bytes))
                    except Exception as e:
                        print(
                            f"Warning: Skipping malformed geometry in {file_path.name}: {e}"
                        )
    else:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        geometries.append(from_wkt(line))
                    except Exception as e:
                        print(
                            f"Warning: Skipping malformed geometry in {file_path.name}: {e}"
                        )

    return geometries
