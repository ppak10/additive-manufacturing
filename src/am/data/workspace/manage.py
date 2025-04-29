import argparse
import ast
import os

from am import Workspace


def parse_value(value):
    """
    Try to convert the value to the most appropriate type.
    Handles bool, int, float, and string.
    """
    value_lower = value.lower()
    if value_lower in {"true", "yes", "on"}:
        return True
    elif value_lower in {"false", "no", "off"}:
        return False
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip()  # Return as string if it can't be parsed


def main():
    parser = argparse.ArgumentParser(
        description="Manage and execute methods for `workspace` and `simulation`."
    )
    parser.add_argument(
        "method",
        help="Method within class (e.g., `create_simulation`).",
    )

    parser.add_argument("--verbose", help="Defaults to `False`.", action="store_true")

    args, unknown_args = parser.parse_known_args()

    verbose = args.verbose

    # Sets current directory path of `manage.py` to the workspace.
    workspace_path = os.path.dirname(__file__)

    workspace_filename = os.path.basename(workspace_path)

    if verbose:
        print(f"workspace_path: {workspace_path}")
        print(f"workspace_filename: {workspace_filename}")

    workspace = Workspace(
        workspace_path=workspace_path,
        filename=workspace_filename,
        verbose=verbose,
    )

    # Separate positional and keyword arguments
    positional_args = []
    kwargs = {}

    for item in unknown_args:
        if "=" in item:
            try:
                key, value = item.split("=", 1)  # Split only at the first '='
                kwargs[key] = parse_value(value)
            except ValueError:
                print(f"Invalid format for keyword argument: {item}")
                return
        else:
            positional_args.append(parse_value(item))

    # Handle the commands
    try:
        method = getattr(workspace, args.method)
        method(*positional_args, **kwargs)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
