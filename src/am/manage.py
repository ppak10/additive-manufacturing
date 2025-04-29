import argparse
import ast

from am import Portfolio


def parse_value(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip()  # Return as string if it can't be parsed


def main():
    parser = argparse.ArgumentParser(
        description="Manage and execute methods for `workspace`."
    )
    parser.add_argument(
        "method",
        help="Method within class (e.g., `create_job`).",
    )

    parser.add_argument(
        "--portfolio_path",
        default="out",
        help="Defaults to `out`.",
    )

    parser.add_argument("--verbose", help="Defaults to `False`.", action="store_true")

    args, unknown_args = parser.parse_known_args()

    portfolio = Portfolio(
        portfolio_path=args.portfolio_path,
        verbose=args.verbose,
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
        method = getattr(portfolio, args.method)
        method(*positional_args, **kwargs)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
