"""
Tiny CLI package for printing the current date and time.

This package exposes a simple API to retrieve and format the current datetime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

__all__: Iterable[str] = (
    "get_current_datetime",
    "format_current_datetime",
    "__version__",
)

__version__: str = "0.1.0"


def get_current_datetime() -> datetime:
    """Return the current local date and time."""
    return datetime.now()


def format_current_datetime(dt: datetime | None = None) -> str:
    """Format a datetime object into a human-readable string.

    If no datetime is provided, the current datetime is used.
    """
    if dt is None:
        dt = get_current_datetime()
    return dt.strftime("%Y-%m-%d %H:%M:%S")