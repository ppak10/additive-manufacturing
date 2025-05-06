import gzip
import os
import torch

import matplotlib.pyplot as plt

class SimulationVisualize:
    """
    Method for visualizing simulations.
    """

    def visualize_layer_segment(self, segment_path, out_dir="temperatures"):
        """
        Creates `.gif` animation of layer segments.
        """

        filename = os.path.basename(segment_path)
        if filename.endswith(".pt"):
            temperatures = torch.load(segment_path)
        elif filename.endswith(".pt.gz"):
            with gzip.open(segment_path, "rb") as f:
                temperatures = torch.load(f)

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        X = self.solver.X.cpu()
        Y = self.solver.Y.cpu()
        ax.pcolormesh(X, Y, temperatures[:, :, -1].T, cmap= "jet", vmin=300, vmax = 1923)

        figure_filename = f"{filename.split('.')[0]}.png"
        fig.savefig(os.path.join(out_dir, figure_filename), dpi=600, bbox_inches="tight")
        plt.close(fig)


