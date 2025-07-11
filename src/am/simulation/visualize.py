# import gzip
import os

# import torch
import numpy as np

import matplotlib.pyplot as plt

from am.units import MMGS


class SimulationVisualize:
    """
    Method for visualizing simulations.
    """

    # TODO: Find a way to decouple this from cuda so that when running
    # multiprocessing visualizations does eat up a bunch of vram.
    # Potentially due to the fact that self.solver is part of the simulation now
    def visualize_layer_segment(self, X, Y, segment_path, out_dir="temperatures"):
        """
        Creates `.gif` animation of layer segments.
        """
        filename = os.path.basename(segment_path)
        # if filename.endswith(".pt"):
        #     temperatures = torch.load(segment_path)
        # elif filename.endswith(".pt.gz"):
        #     with gzip.open(segment_path, "rb") as f:
        #         temperatures = torch.load(f)

        data = np.load(segment_path)
        temperatures = data["temperatures"]
        print(np.unique(temperatures))

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        # if self.units == MMGS:
        #     ax.pcolormesh(X * 1000, Y * 1000, temperatures[:, :, -1].T * 1000, cmap= "jet", vmin=300, vmax = 1923)
        # else:
        #     ax.pcolormesh(X, Y, temperatures[:, :, -1].T, cmap= "jet", vmin=300, vmax = 1923)
        mesh = ax.pcolormesh(
            X * 1000,
            Y * 1000,
            temperatures[:, :, -1].T,
            cmap="jet",
            vmin=300,
            vmax=1923,
        )

        fig.colorbar(mesh, ax=ax, label="Temperature (K)")

        figure_filename = f"{filename.split('.')[0]}.png"
        fig.savefig(
            os.path.join(out_dir, figure_filename), dpi=600, bbox_inches="tight"
        )
        plt.close(fig)
