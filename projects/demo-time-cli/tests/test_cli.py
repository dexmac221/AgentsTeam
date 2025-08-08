import subprocess
import sys
import re
import datetime
import pytest

CLI_MODULE = "mycli.cli"

def run_cli(args=None):
"""
Helper to execute the CLI as a subprocess and capture its output.
"""
if args is None:
args = []
cmd = [sys.executable, "-m", CLI_MODULE] + args
result = subprocess.run(
cmd,
stdout=subprocess.PIPE,
stderr=subprocess.PIPE,
text=True,
)
return result


def test_cli_exit_code():
"""
The CLI should exit with status code 0 on normal execution.
"""
result = run_cli()
assert result.returncode == 0, f"Unexpected exit code: {result.returncode}"


def test_cli_output_format():
"""
The CLI should print the current date/time in ISO 8601 format.
"""
result = run_cli()
output = result.stdout.strip()
iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
assert re.match(iso_regex, output), f"Output does not match ISO format: {output}"
parsed_time = datetime.datetime.fromisoformat(output.replace("Z", "+00:00"))
now = datetime.datetime.now(tz=parsed_time.tzinfo)
delta = abs((now - parsed_time).total_seconds())
assert delta < 5, f"Time difference too large: {delta} seconds"


def test_cli_help():
"""
The CLI should display a help message when invoked with --help.
"""
result = run_cli(["--help"])
assert result.returncode == 0, f"Help command exited with code {result.returncode}"
assert "usage:" in result.stdout.lower(), "Help output missing 'usage:'"
assert "options:" in result.stdout.lower() or "options" in result.stdout.lower(), "Help output missing 'options'"


def test_cli_version():
"""
If the CLI supports a --version flag, it should print the version string.
"""
result = run_cli(["--version"])
if result.returncode != 0:
pytest.skip("CLI does not support --version flag")
output = result.stdout.strip()
assert re.match(r"^\d+\.\d+\.\d+$", output), f"Unexpected version format: {output}"
assert result.returncode == 0, f"Version command exited with code {result.returncode}"