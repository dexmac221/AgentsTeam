import argparse
import datetime
from typing import Optional

__all__ = ["main"]


def _parse_args() -> argparse.Namespace:
"""
Parse command line arguments.

Returns:
argparse.Namespace: Parsed arguments.
"""
parser = argparse.ArgumentParser(
description="Print the current date and time."
)
parser.add_argument(
"-f",
"--format",
type=str,
default="%Y-%m-%d %H:%M:%S",
help="Date/time format string (default: '%Y-%m-%d %H:%M:%S').",
)
parser.add_argument(
"-u",
"--utc",
action="store_true",
help="Use UTC instead of local time.",
)
return parser.parse_args()


def _get_current_datetime(utc: bool = False) -> datetime.datetime:
"""
Retrieve the current datetime.

Args:
utc: If True, return UTC datetime; otherwise, local time.

Returns:
datetime.datetime: Current datetime.
"""
if utc:
return datetime.datetime.utcnow()
return datetime.datetime.now()


def _format_datetime(dt_obj: datetime.datetime, fmt: str) -> str:
"""
Format a datetime object according to the given format string.

Args:
dt_obj: The datetime object to format.
fmt: The format string.

Returns:
str: Formatted datetime string.
"""
return dt_obj.strftime(fmt)


def main() -> None:
"""
Entry point for the CLI. Parses arguments, obtains the current datetime,
formats it, and prints the result.
"""
args = _parse_args()
current_dt = _get_current_datetime(utc=args.utc)
formatted = _format_datetime(current_dt, args.format)
print(formatted)


if __name__ == "__main__":
main()