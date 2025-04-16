import os
import pickle

class WorkspaceSegmenterUtils:
    """
    Utility functions for workspace segmenter class.
    """
    def create_segmenter_folder(self, segmenter):
        """
        Creates folder for `segmenter` and parent `segmenters` folder if needed.
        Also saves passed segmenter into `segmenter.pkl` within created folder.
        """
        # Creates `segmenters` folder path within workspace if not created.
        segmenters_path = os.path.join(self.workspace_path, "segmenters")
        if not os.path.isdir(segmenters_path):
            os.makedirs(segmenters_path)

        # Create `segmenter` folder within workspace path 
        segmenter_path = os.path.join(self.workspace_path, "segmenters", segmenter.filename)
        if not os.path.isdir(segmenter_path):
            os.makedirs(segmenter_path)

        # Save segmenter class object to pickle file
        segmenter_pkl_path = os.path.join(segmenter_path, "segmenter.pkl")
        with open(segmenter_pkl_path, "wb") as file:
            pickle.dump(segmenter, file)
        
        return segmenter_path