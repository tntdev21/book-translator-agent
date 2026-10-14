#!/usr/bin/env python3
"""Regression test: `fix.py --no-backup` must not leave `.bak` files.

Bug (P9 V2): the CJK and word-merging steps called `fix_file(..., backup=True)`
unconditionally, so a translator's `fix.py --no-backup` still dropped
`chunk_NNN.md.bak` into translated/.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIX = REPO_ROOT / "scripts" / "fix.py"
# One CJK char (step 1 fix path) inside Vietnamese prose.
TEXT = "Xin chào các bạn 们 hôm nay.\n\nĐây là một đoạn khác.\n"


def _run(path: Path, *flags: str) -> None:
    subprocess.run([sys.executable, str(FIX), str(path), *flags],
                   cwd=REPO_ROOT, check=True, capture_output=True, text=True)


def test_no_backup_flag_creates_no_bak(tmp_path):
    chunk = tmp_path / "chunk_001.md"
    chunk.write_text(TEXT, encoding="utf-8")
    _run(chunk, "--no-backup", "--skip-name-extraction")
    assert "们" not in chunk.read_text(encoding="utf-8")  # the CJK step did run
    assert list(tmp_path.glob("*.bak")) == []


def test_default_still_creates_bak(tmp_path):
    chunk = tmp_path / "chunk_001.md"
    chunk.write_text(TEXT, encoding="utf-8")
    _run(chunk, "--skip-name-extraction")
    assert list(tmp_path.glob("*.bak")) != []
