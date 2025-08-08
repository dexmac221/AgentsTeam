"""
Tiny CLI package for printing the current date and time.

This package exposes a simple API to retrieve the current datetime
and to print it to the console. It also provides a command-line
entry point that can be used by the project's console_scripts
configuration.
"""

from __future__ import annotations

import datetime
import sys
from typing import Iterable

__all__: Iterable[str] = (
"get_current_datetime",
"format_current_datetime",
"print_current_datetime",
"main",
"__version__",
)

__version__: str = "0.1.0"


def get_current_datetime() -> datetime.datetime:
"""
Return the current local date and time.

Returns:
datetime.datetime: The current local datetime.
"""
return datetime.datetime.now()


def format_current_datetime(dt: datetime.datetime | None = None) -> str:
"""
Format a datetime object into a human-readable string.

If no datetime is provided, the current datetime is used.

Args:
dt: The datetime to format. Defaults to None.

Returns:
str: The formatted datetime string.
"""
if dt is None:
dt = get_current_datetime()
return dt.strftime("%Y-%m-%d %H:%M:%S")


def print_current_datetime() -> None:
"""
Print the current datetime to stdout.

This function is intended to be used as the main entry point
for the command-line interface.
"""
print(format_current_datetime())


def main(argv: list[str] | None = None) -> None:
"""
Main entry point for the CLI.

Args:
argv: Optional list of command-line arguments. If None,
sys.argv[1:] is used.
"""
print_current_datetime()


if __name__ == "__main__":
main(sys.argv[1:])