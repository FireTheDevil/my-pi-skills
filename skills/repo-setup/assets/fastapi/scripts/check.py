"""Non-mutating formatting, lint, type checks and real HTTP smoke."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    for command in (
        ["ruff", "format", "--check", "."],
        ["ruff", "check", "."],
        ["ty", "check"],
        ["python", "scripts/smoke.py"],
    ):
        print("$ uv run --no-sync --offline " + " ".join(command), flush=True)
        result = subprocess.run(
            ["uv", "run", "--no-sync", "--offline", *command], cwd=ROOT, check=False
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
