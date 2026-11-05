"""Run non-mutating quality checks, then smoke-test the installed CLI."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    ["ruff", "format", "--check", "."],
    ["ruff", "check", "."],
    ["ty", "check"],
    ["pytest"],
    ["app", "Developer"],
]


def main() -> int:
    for command in COMMANDS:
        print("$ uv run --locked " + " ".join(command), flush=True)
        result = subprocess.run(
            ["uv", "run", "--locked", *command], cwd=ROOT, check=False
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
