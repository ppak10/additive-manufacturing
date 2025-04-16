import configparser
import os

from am import data
from importlib.resources import files

from pprint import pprint

class SolverUtils:
    """
    Class for handling solver utility functions
    """

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
