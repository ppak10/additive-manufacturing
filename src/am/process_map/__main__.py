from datetime import datetime
from pathlib import Path

class ProcessMap:
    """
    Class for utilizing solver to generate process map.
    """

    def generate_process_map(
        self,
        workspace_path: Path,
        run_name: str | None = None,
    ) -> Path:
        if run_name is None:
            run_name = datetime.now().strftime("solver_%Y%m%d_%H%M%S")

        out_path = workspace_path / "process_map" / run_name
        return out_path

