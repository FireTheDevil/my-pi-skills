import subprocess
import sys

import pytest

from app import greet


def test_greeting_trims_name() -> None:
    assert greet("  Ada  ") == "Hello, Ada!"


@pytest.mark.parametrize("name", ["", " ", "\t"])
def test_empty_name_is_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        greet(name)


def test_cli_prints_greeting() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app", "Ada"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "Hello, Ada!\n"


def test_cli_reports_invalid_input() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app", " "],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Name must not be empty" in result.stderr
