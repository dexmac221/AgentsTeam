"""
Entry point for tiny_cli_datetime.
Prints the current date and time in a human‑readable format.
"""

import sys
from datetime import datetime, timezone
from typing import Optional


def get_current_datetime() -> datetime:
    """Return the current date and time as a timezone‑aware datetime object."""
    return datetime.now(timezone.utc).astimezone()


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Format a datetime object into a string using the provided format."""
    return dt.strftime(fmt)


def main() -> None:
    """Main entry point: fetch current datetime, format it, and print to stdout."""
    try:
        current_dt = get_current_datetime()
        output = format_datetime(current_dt)
        print(output)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()