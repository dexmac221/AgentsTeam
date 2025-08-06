import sys
import argparse
import logging
from typing import Any

try:
    import uvicorn
except ImportError as exc:
    sys.stderr.write("Error: uvicorn is not installed. Install it with 'pip install uvicorn'.\n")
    sys.exit(1)

if sys.version_info < (3, 8):
    sys.stderr.write("Error: Python 3.8 or higher is required.\n")
    sys.exit(1)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the system monitor startup script.
    """
    parser = argparse.ArgumentParser(
        description="Start the system monitor server with uvicorn."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname to bind the server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to bind the server to (default: 8000).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (useful for development).",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Set the logging level for the server (default: info).",
    )
    return parser.parse_args()

def configure_logging(level: str) -> None:
    """
    Configure the root logger to the specified level.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        sys.stderr.write(f"Invalid log level: {level}\n")
        sys.exit(1)
    logging.basicConfig(level=numeric_level, format="%(asctime)s [%(levelname)s] %(message)s")

def run_server(host: str, port: int, reload: bool, log_level: str) -> None:
    """
    Start the uvicorn server with the given configuration.
    """
    try:
        from app import app  # type: ignore
    except Exception as exc:
        sys.stderr.write(f"Failed to import the ASGI application: {exc}\n")
        sys.exit(1)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )

def main() -> None:
    """
    Main entry point for the startup script.
    """
    args = parse_arguments()
    configure_logging(args.log_level)

    if not (1 <= args.port <= 65535):
        sys.stderr.write("Error: Port must be between 1 and 65535.\n")
        sys.exit(1)

    logging.info(
        f"Starting server at http://{args.host}:{args.port} "
        f"with reload={args.reload} and log level={args.log_level}"
    )
    run_server(args.host, args.port, args.reload, args.log_level)

if __name__ == "__main__":
    main()