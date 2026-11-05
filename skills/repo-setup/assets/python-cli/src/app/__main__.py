"""Run with `uv run app NAME` or `uv run python -m app NAME`."""

import argparse

from app import greet


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a personal greeting")
    parser.add_argument("name", nargs="?", default="world")
    args = parser.parse_args()
    try:
        message = greet(args.name)
    except ValueError as error:
        parser.error(str(error))
    print(message)


if __name__ == "__main__":
    main()
