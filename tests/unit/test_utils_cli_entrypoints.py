#!/usr/bin/env python3
"""Regression tests for direct execution of ``scripts/utils/*.py``.

Bug: the utility scripts import their siblings with package-relative imports
(``from .book_config import ...``), which raises ``ImportError: attempted
relative import with no known parent package`` when the file is run directly
as ``python scripts/utils/foo.py`` — the invocation the docstrings advertise
as "advanced usage".

Each affected file now starts with a shim that, when ``__package__`` is empty,
inserts the repo root on ``sys.path`` and sets ``__package__``. These tests run
the CLIs in a subprocess (the only faithful check) and assert they get past
import — a ``FileNotFoundError`` about a missing input is fine; an
``ImportError``/``ModuleNotFoundError`` is not.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UTILS = REPO_ROOT / "scripts" / "utils"

# Every util with a __main__ block. Run with --help; scripts that do not
# implement --help are skipped by the assertion below, not by this list.
CLIS = sorted(p.name for p in UTILS.glob("*.py") if 'if __name__' in p.read_text(encoding="utf-8"))


def _run(name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(UTILS / name), "--help"],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
        # Several utils ignore --help and run main() against the active book.
        # A nonexistent BOOK_ID makes them fail in config loading instead of
        # rewriting real books/*/translated files.
        env={**os.environ, "BOOK_ID": "__no_such_book__"},
    )


@pytest.mark.parametrize("name", CLIS)
def test_util_cli_has_no_import_error(name: str) -> None:
    """Direct execution must get past module import."""
    result = _run(name)
    combined = result.stdout + result.stderr
    assert "ImportError" not in combined, f"{name} raises ImportError when run directly:\n{combined}"
    assert "ModuleNotFoundError" not in combined, f"{name} raises ModuleNotFoundError:\n{combined}"
    assert "attempted relative import" not in combined, f"{name} has an unresolved relative import:\n{combined}"


@pytest.mark.parametrize("name", CLIS)
def test_util_cli_does_not_traceback_on_import(name: str) -> None:
    """A traceback whose first frame is not inside the script means an import failure."""
    result = _run(name)
    combined = result.stdout + result.stderr
    if "Traceback (most recent call last)" in combined:
        # Only the module-level import (inside the script file, no user frames
        # below it) is disqualifying. Later failures about missing inputs are OK.
        lines = combined.splitlines()
        frame_files = [l.strip() for l in lines if l.strip().startswith("File \"")]
        assert frame_files, f"{name} produced a traceback with no frames:\n{combined}"
        first = frame_files[0]
        assert str(UTILS / name) in first, (
            f"{name} failed before entering main() — likely an import problem:\n{combined}"
        )
