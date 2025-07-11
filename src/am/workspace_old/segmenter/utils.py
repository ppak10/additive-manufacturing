import os
import pickle


class WorkspaceSegmenterUtils:
    """
    Utility functions for workspace segmenter class.
    """

    def create_segmenter_folders(self, segmenter, save=False):
        """
        Creates folder for `segmenter` and parent `segmenters` folder if needed.
        Also saves passed segmenter into `segmenter.pkl` within created folder.
        """
        # Creates `segmenters` folder path within workspace if not created.
        segmenters_path = os.path.join(
            # `/out/<self.workspace_path>/segmenters/`
            self.workspace_path,
            "segmenters",
        )
        if not os.path.isdir(segmenters_path):
            os.makedirs(segmenters_path)

        # Create `segmenter` folder within workspace path
        segmenter_path = os.path.join(
            # `/out/<self.workspace_path>/segmenters/<segmenter.filename>/`
            self.workspace_path,
            "segmenters",
            segmenter.filename,
        )

        # Creates folder for segmenter layers.
        segmenter_layers_path = os.path.join(
            # `/out/<self.workspace_path>/segmenter/<segmenter.filename>/layers/`
            self.workspace_path,
            "segmenters",
            segmenter.filename,
            "layers",
        )

        if not os.path.isdir(segmenter_layers_path):
            os.makedirs(segmenter_layers_path)

        if save:
            # Save segmenter class object to pickle file.
            segmenter_pkl_path = os.path.join(
                # `/out/<self.workspace_path>/segmenter/<segmenter.filename>/segmenter.pkl`
                segmenter_path,
                "segmenter.pkl",
            )
            with open(segmenter_pkl_path, "wb") as file:
                pickle.dump(segmenter, file)

        return segmenter_path
