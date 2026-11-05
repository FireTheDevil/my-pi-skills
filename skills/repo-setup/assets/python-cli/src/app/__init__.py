"""Application behavior independent of the command-line interface."""


def greet(name: str) -> str:
    """Return a greeting for a nonempty, trimmed name."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Name must not be empty")
    return f"Hello, {clean_name}!"
