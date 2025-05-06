import os
import multiprocessing
import pickle

from tqdm import tqdm


class WorkspaceSegmenterVisualize:
    """
    Workspace SegmeneterVisualize class abstraction layer.
    """

    def segmenter_visualize_layer_index(self, layer_index: int, **kwargs):
        """
        Initialize Segmenter class and parse gcode commands from selected file.
        """
        segmenter_folder = kwargs.get("segmenter_folder_name")
        if not segmenter_folder:
            segmenter_folder = self.select_folder("segmenters")

        segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")

        with open(segmenter_path, "rb") as f:
            segmenter = pickle.load(f)

        # Creates initial folders if not already made.
        # Should already be made from running `create_segmenter`
        self.create_segmenter_folders(segmenter)

        segmenter.visualize_layer_index(layer_index)

    def segmenter_visualize_all_layers(self, num_proc=1, **kwargs):
        """
        Initialize Segmenter class and parse gcode commands from selected file.
        """
        segmenter_folder = kwargs.get("segmenter_folder_name")
        if not segmenter_folder:
            segmenter_folder = self.select_folder("segmenters")

        segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")

        with open(segmenter_path, "rb") as f:
            segmenter = pickle.load(f)

        # Creates initial folders if not already made.
        # Should already be made from running `create_segmenter`
        self.create_segmenter_folders(segmenter)

        if num_proc > 1:
            with multiprocessing.Pool(processes=num_proc) as pool:

                for layer_index in range(segmenter.gcode_layer_count):
                    pool.apply_async(
                        segmenter.visualize_layer_index, args=(layer_index,)
                    )
                pool.close()
                pool.join()
        else:
            for layer_index in tqdm(range(segmenter.gcode_layer_count)):
                segmenter.visualize_layer_index(layer_index)
