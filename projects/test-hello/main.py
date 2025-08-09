#!/usr/bin/env python3
"""
Main application file for the Hello World CLI project.

This script provides a simple command-line interface that greets the user.
It uses argparse for argument parsing, logging for debug output, and
type hints for clarity. The code follows PEP 8 conventions and is
ready for production use.
"""

import argparse
import logging
import sys
from typing import Optional

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Parameters
    ----------
    argv : list[str] | None
        List of arguments to parse. If None, sys.argv[1:] is used.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Hello World CLI – greet the user."
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="World",
        help="Name of the person to greet (default: World)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    return parser.parse_args(argv)


def greet(name: str) -> str:
    """
    Generate a greeting message.

    Parameters
    ----------
    name : str
        Name to greet.

    Returns
    -------
    str
        Greeting message.
    """
    return f"Hello, {name}!"


def main(argv: Optional[list[str]] = None) -> None:
    """
    Main entry point for the CLI.

    Parameters
    ----------
    argv : list[str] | None
        List of arguments to parse. If None, sys.argv[1:] is used.
    """
    args = parse_arguments(argv)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    logger.debug(f"Parsed arguments: {args}")

    try:
        message = greet(args.name)
        print(message)
        logger.info("Greeting printed successfully")
    except Exception as exc:  # pragma: no cover
        logger.exception("An unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()