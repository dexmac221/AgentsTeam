import re
import sys
from pathlib import Path
from datetime import datetime

import pytest

# Add the package src directory to sys.path for direct import during tests
THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from tiny_cli_datetime.main import main  # noqa: E402


def test_main_prints_datetime(capsys, monkeypatch):
    """
    Verify that the main function prints the current date and time
    in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) and does not raise an exception.
    """
    # Prevent the test from exiting the interpreter
    monkeypatch.setattr(sys, "exit", lambda code=0: None)

    main()

    captured = capsys.readouterr()
    output = captured.out.strip()

    iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
    assert re.match(iso_regex, output), f"Output '{output}' does not match ISO format"

    printed_time = datetime.strptime(output, "%Y-%m-%dT%H:%M:%S")
    now = datetime.now()
    assert abs((now - printed_time).total_seconds()) < 5, (
        f"Printed time {printed_time} is not close to current time {now}"
    )


def test_main_exits_with_code_0(monkeypatch):
    """
    Verify that the main function calls sys.exit with code 0.
    """
    exit_called = {"code": None}

    def fake_exit(code=0):
        exit_called["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", fake_exit)

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert exit_called["code"] == 0, f"sys.exit called with {exit_called['code']} instead of 0"
    assert excinfo.value.code == 0, f"SystemExit raised with code {excinfo.value.code} instead of 0"