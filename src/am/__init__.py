__author__ = "Peter Pak"
__email__ = "ppak10@gmail.com"

# Set multiprocessing start method to 'spawn' for compatibility with MCP server
# This ensures consistent behavior across platforms (Linux uses 'fork' by default,
# macOS uses 'spawn') and prevents issues with forking async/MCP server state
import multiprocessing
import sys
import warnings

if sys.platform != "win32":  # spawn is already default on Windows
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        # Method already set, ignore
        pass

# Suppress tqdm experimental warning for rich integration
warnings.filterwarnings("ignore", message=".*rich is experimental.*")
