import os

from am.segmenter import Segmenter

class WorkspaceSegmenterGCode:
    """
    Workspace SegmeneterGCode class abstraction layer.
    """

    def parse_gcode(self):
        """
        Initialize Segmenter class and parse gcode commands from selected file.
        """
        selected_file = self.select_file("parts", ".gcode")
        selected_file_path = os.path.join("parts", selected_file)
        segmenter = Segmenter()
        segmenter.load_gcode_commands(selected_file_path)
        segmenter.set_name(selected_file.split(".gcode")[0])
        self.create_segmenter_folder(segmenter)
    