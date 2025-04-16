import os

class PortfolioBase:
    """
    Main portfolio methods that do not rely on other classes.
    """

    def __init__(self, portfolio_path = "out", verbose = False, **kwargs):
        """
        Initializes portfolio variables and creates output directory.

        @param portfolio_path: `portfolio` folder path
        @param verbose: Displays verbose outputs.
        """
        self.create_portfolio_directory(portfolio_path)
        self.verbose = verbose

        # TODO: Is this needed?
        self.current_path = os.path.dirname(__file__)
        if self.verbose:
            print(f"self.current_path: {self.current_path}")

        super().__init__(**kwargs)

    def create_portfolio_directory(self, portfolio_path):
        """
        Creates `portfolio` output directory for `workspaces`.

        @param portfolio_path: path to `portfolio` directory
        """
        self.portfolio_path = portfolio_path

        if not os.path.isdir(self.portfolio_path):
            # Creates portfolio directory to store am workspaces.
            os.makedirs(self.portfolio_path)

        return self.portfolio_path
