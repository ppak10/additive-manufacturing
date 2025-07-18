import configparser
import os

from datetime import datetime
from importlib.resources import files
from pprint import pprint

from am import data


class SolverUtils:
    """
    Class for handling solver utility functions
    """

    def set_name(self, name=None, filename=None, model=None):
        """
        Sets the `name` and `filename` values of the class.

        @param name: Name of segmenter
        @param filename: `filename` override of segmenter (no spaces)
        """
        if name:
            self.name = name
        if model is not None:
            self.name = model
        else:
            # Sets `name` to approximate timestamp.
            self.name = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Autogenerates `filename` from `name` if not provided.
        if filename == None:
            self.filename = self.name.replace(" ", "_")
        else:
            self.filename = filename

    def load_config_file(self, config_dir, config_file):
        """
        Loads configs from prescribed file and also applies given overrides.
        """

        config = configparser.ConfigParser()
        config_file_path = os.path.join("solver", config_dir, config_file)
        config_resource = files(data).joinpath(config_file_path)
        config.read(config_resource)
        output = {}

        for section in config.sections():
            for key, value in config[section].items():
                if section == "float":
                    # output[key] = float(value)
                    setattr(self, key, float(value))
                else:
                    # Defaults to string
                    # output[key] = value
                    setattr(self, key, value)

        if self.verbose:
            print(f"\n{config_dir}")
            pprint(config)

        return output
