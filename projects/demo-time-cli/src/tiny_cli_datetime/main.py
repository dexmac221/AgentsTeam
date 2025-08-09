#!/usr/bin/env python3
"""
Entry point for tiny_cli_datetime.
Prints the current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
"""

import sys
from datetime import datetime


def get_current_datetime() -> datetime:
    """Return the current local date and time.
    Note: We intentionally use naive local time to match test expectations.
    """
    return datetime.now()


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%dT%H:%M:%S") -> str:
    """Format a datetime object into a string using the provided format."""
    return dt.strftime(fmt)


def main() -> None:
    """Main entry point: fetch current datetime, format it, and print to stdout."""
    try:
        current_dt = get_current_datetime()
        output = format_datetime(current_dt)
        print(output)
        sys.exit(0)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()