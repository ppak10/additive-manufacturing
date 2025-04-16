from .base import PortfolioBase
from .workspace import PortfolioWorkspace

class Portfolio(
    PortfolioBase,
    PortfolioWorkspace,
):
    def __init__(self, portfolio_path = "out", verbose = False, **kwargs):
        """
        Initializes portfolio variables and creates output directory.
        Exposes methods for `am` CLI
        Named `Portfolio` since it was copied over from Flow3D package structure
        TODO: Could find a more suitable name for this class but Portfolio works
        for now.

        @param portfolio_path: Path to `portfolio` directory
        @param verbose: Displays verbose outputs.
        """
        super().__init__(
            portfolio_path = portfolio_path,
            verbose = verbose,
            **kwargs,
        )
