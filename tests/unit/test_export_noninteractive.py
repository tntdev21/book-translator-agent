#!/usr/bin/env python3
"""Regression tests for export.py's TOC-failure prompt.

Bug: on TOC validation failure, export.py called ``input()`` unconditionally.
In a non-interactive session (CI, subprocess with piped stdio, cron) that blocks
forever waiting on stdin.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT = REPO_ROOT / "scripts" / "export.py"
BOOK_ID = "_noninteractive_fixture"


@pytest.fixture
def book(*, valid_toc: bool = False):
    """Build a throwaway book under the repo's books/ and select it via BOOK_ID.

    Book paths resolve against the repo root, not the cwd, so ``BOOK_ID`` can
    only name a book that actually lives in ``books/``. The directory is
    removed on teardown.
    """
    book_root = REPO_ROOT / "books" / BOOK_ID
    shutil.rmtree(book_root, ignore_errors=True)
    translated = book_root / "translated"
    translated.mkdir(parents=True)
    (book_root / "book.yaml").write_text(
        f'id: {BOOK_ID}\ntitle_vi: "Sách thử"\nauthor: "Tác giả"\n',
        encoding="utf-8",
    )
    if valid_toc:
        (translated / "chunk_001.md").write_text(
            "MỤC LỤC\nCHƯƠNG 1\nCHƯƠNG 2\n\n# CHƯƠNG 1\n\nNội dung một.\n\n# CHƯƠNG 2\n\nNội dung hai.\n",
            encoding="utf-8",
        )
    else:
        # Lowercase 'Chương' and a TOC/content mismatch => validation fails.
        (translated / "chunk_001.md").write_text(
            "MỤC LỤC\nChương 1\nChương 9\n\n# Chương 1\n\nNội dung.\n",
            encoding="utf-8",
        )
    try:
        yield translated
    finally:
        shutil.rmtree(book_root, ignore_errors=True)


def _run_export(*flags: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "BOOK_ID": BOOK_ID}
    return subprocess.run(
        [sys.executable, str(EXPORT), *flags],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestNonInteractiveDoesNotHang:
    def test_failing_toc_exits_without_hanging(self, book):
        """stdin=DEVNULL + failing TOC must exit fast instead of blocking."""
        result = _run_export("-f", "pdf", "--test")
        assert result.returncode == 1, (
            f"expected clean exit 1, got {result.returncode}\n"
            f"stdout: {result.stdout[-800:]}\nstderr: {result.stderr[-800:]}"
        )
        assert "TOC validation failed" in result.stdout
        assert "--force" in result.stdout, "should hint at the escape hatch"

    def test_no_prompt_output_when_not_a_tty(self, book):
        result = _run_export("-f", "pdf", "--test")
        assert "Continue with export anyway?" not in result.stdout


class TestForceFlag:
    def test_help_lists_force_flag(self):
        result = subprocess.run(
            [sys.executable, str(EXPORT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert "--force" in result.stdout
        assert "-y" in result.stdout

    def test_force_and_y_are_aliases(self):
        for flag in ("--force", "-y"):
            result = subprocess.run(
                [sys.executable, str(EXPORT), "--help"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert flag in result.stdout

    def test_force_flag_does_not_abort_on_failing_toc(self, book):
        """With --force the run must get past validation (may still fail later)."""
        result = _run_export("-f", "pdf", "--test", "--force")
        assert "❌ Export cancelled (non-interactive session)" not in result.stdout


class TestSourceGuardsPrompt:
    def test_input_call_is_guarded_by_isatty(self):
        src = EXPORT.read_text(encoding="utf-8")
        assert "isatty()" in src, "the input() prompt is not guarded by a tty check"
        assert "args.force" in src
