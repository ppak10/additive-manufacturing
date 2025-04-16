from datetime import datetime

class SegmenterBase:
    """
    Base file for Segmenter class.
    """

    def __init__(self, name=None, filename=None, verbose = False, **kwargs):
        self.set_name(name, filename)

        self.verbose = verbose
        super().__init__(**kwargs)

    def set_name(self, name = None, filename = None):
        """
        Sets the `name` and `filename` values of the class.

        @param name: Name of segmenter 
        @param filename: `filename` override of segmenter (no spaces)
        """
        # Sets `name` to approximate timestamp.
        if name is None:
            self.name = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.name = name

        # Autogenerates `filename` from `name` if not provided.
        if filename == None:
            self.filename = self.name.replace(" ", "_")
        else:
            self.filename = filename
