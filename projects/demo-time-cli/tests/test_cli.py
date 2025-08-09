import subprocess
import sys
import re
import datetime
import os
from pathlib import Path

CLI_MODULE = "tiny_cli_datetime.main"

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent / "src"


def run_cli(args=None):
    """
    Helper to execute the CLI as a subprocess and capture its output.
    """
    if args is None:
        args = []
    cmd = [sys.executable, "-m", CLI_MODULE] + args
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}{os.pathsep}{existing}" if existing else str(SRC_DIR)
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(THIS_DIR.parent),
    )
    return result


def test_cli_exit_code():
    """
    The CLI should exit with status code 0 on normal execution.
    """
    result = run_cli()
    assert result.returncode == 0, f"Unexpected exit code: {result.returncode} (stderr: {result.stderr})"


def test_cli_output_format():
    """
    The CLI should print the current date/time in ISO 8601 format without timezone.
    """
    result = run_cli()
    output = result.stdout.strip()
    iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
    assert re.match(iso_regex, output), f"Output does not match ISO format: {output}"

    printed = datetime.datetime.strptime(output, "%Y-%m-%dT%H:%M:%S")
    now = datetime.datetime.now()
    delta = abs((now - printed).total_seconds())
    assert delta < 5, f"Time difference too large: {delta} seconds (output={output})"