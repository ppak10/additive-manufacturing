import os
import multiprocessing
import pickle
import imageio.v2 as imageio

from tqdm import tqdm


class WorkspaceSimulationVisualize:
    """
    Workspace SimulationVisualize class abstraction layer.
    """

    def simulation_visualize_layer_segments(self, num_proc=1, **kwargs):
        """
        Visualize segments from layer. 
        """

        simulation_folder = self.select_folder("simulations")

        # Locations of saved Simulation, Solver, and Segmenter classes.
        simulation_path = os.path.join(
            "simulations", simulation_folder, "simulation.pkl"
        )

        # Load pickled objects
        with open(simulation_path, "rb") as f:
            simulation = pickle.load(f)

        # TODO: Adds parsing of `layer_index` argument
        # Folder name is prepended with 0's using zfill
        simulation_layers_directory = os.path.join(
            "simulations", simulation_folder, "layers"
        )
        layer_folder = self.select_folder(simulation_layers_directory)

        segments_path = os.path.join(
            "simulations", simulation_folder, "layers", layer_folder, "segments"
        )

        segment_files = sorted(os.listdir(segments_path))

        out_dir = os.path.join(
            "simulations", simulation_folder, "layers", layer_folder, "temperatures"
        )
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if num_proc > 1:
            tasks = [
                (os.path.join(segments_path, segment_file), out_dir)
                for segment_file in segment_files
            ]

            with multiprocessing.get_context("spawn").Pool(processes=num_proc) as pool:
                pool.starmap(simulation.visualize_layer_segment, tasks)
        else:
            for segment_file in tqdm(segment_files):
                segment_path = os.path.join(segments_path, segment_file)
                simulation.visualize_layer_segment(segment_path, out_dir)

        # Saves images as .gif
        # images = []
        # if self.verbose: print("Compiling images to .gif")
        # for image_filename in tqdm(sorted(os.listdir(out_dir))):
        #     if image_filename.endswith(".png"):
        #         image_path = os.path.join(out_dir, image_filename)
        #         images.append(imageio.imread(image_path))

        # gif_path = os.path.join(
        #     "simulations", simulation_folder, "layers", layer_folder, "temperatures.gif"
        # )

        # imageio.mimwrite(gif_path, images, fps=60, loop=0)

        # Ensure filenames are sequential: frame_0000.png, frame_0001.png, etc.
        for idx, fname in enumerate(sorted(os.listdir(out_dir))):
            if fname.endswith(".png"):
                src = os.path.join(out_dir, fname)
                dst = os.path.join(out_dir, f"frame_{idx:04d}.png")
                if src != dst:
                    os.rename(src, dst)

        if self.verbose:
            print("Compiling images to video using imageio-ffmpeg")

        video_path = os.path.join(
            "simulations", simulation_folder, "layers", layer_folder, "temperatures.mp4"
        )

        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        # Use imageio's ffmpeg plugin to compile the frames into a video
        with imageio.get_writer(video_path, fps=60) as writer:
            for idx in tqdm(range(len(sorted(os.listdir(out_dir)))), desc="Writing frames"):
                image_path = os.path.join(out_dir, f"frame_{idx:04d}.png")
                image = imageio.imread(image_path)
                writer.append_data(image)

        if self.verbose:
            print(f"Saved video to: {video_path}")

        # Creates initial folders if not already made.
        # Should already be made from running `create_segmenter`
        # self.create_segmenter_folders(segmenter)

        # segmenter.visualize_layer_index(layer_index)

    # def segmenter_visualize_all_layers(self, num_proc=1, **kwargs):
    #     """
    #     Initialize Segmenter class and parse gcode commands from selected file.
    #     """
    #     segmenter_folder = kwargs.get("segmenter_folder_name")
    #     if not segmenter_folder:
    #         segmenter_folder = self.select_folder("segmenters")

    #     segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")

    #     with open(segmenter_path, "rb") as f:
    #         segmenter = pickle.load(f)

    #     # Creates initial folders if not already made.
    #     # Should already be made from running `create_segmenter`
    #     self.create_segmenter_folders(segmenter)

    #     if num_proc > 1:
    #         with multiprocessing.Pool(processes=num_proc) as pool:

    #             for layer_index in range(segmenter.gcode_layer_count):
    #                 pool.apply_async(
    #                     segmenter.visualize_layer_index, args=(layer_index,)
    #                 )
    #             pool.close()
    #             pool.join()
    #     else:
    #         for layer_index in tqdm(range(segmenter.gcode_layer_count)):
    #             segmenter.visualize_layer_index(layer_index)
