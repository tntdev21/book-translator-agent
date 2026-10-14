#!/usr/bin/env python3
"""
E2E tests for the export pipeline.
Tests the complete export.py script with actual subprocess calls.

The book under test is selected with $BOOK_ID (default: the only book under
books/). Tests skip when that book has no translated chunks — a fresh clone
has nothing to export, and seeding fake translations would test the seed
rather than the pipeline.
"""

import os
import subprocess
import pytest
from pathlib import Path
from typing import List


# Project root for running scripts
PROJECT_ROOT = Path(__file__).parent.parent.parent
BOOKS_DIR = PROJECT_ROOT / "books"


def _active_book_id() -> str:
    """Book under test: $BOOK_ID, else the single book present."""
    env_book = os.environ.get("BOOK_ID")
    if env_book:
        return env_book

    books = sorted(p.parent.name for p in BOOKS_DIR.glob("*/book.yaml"))
    if len(books) != 1:
        pytest.skip(f"Ambiguous book selection: {books or 'none found'}")
    return books[0]


def _book_dirs():
    """(translated_dir, output_dir) for the book under test."""
    root = BOOKS_DIR / _active_book_id()
    return root / "translated", root / "output"


def _require_translations() -> tuple:
    """Skip unless the book has at least one translated chunk."""
    translated_dir, output_dir = _book_dirs()
    if not sorted(translated_dir.glob("chunk_*.md")):
        pytest.skip(f"No translated chunks in {translated_dir}")
    return translated_dir, output_dir


def run_export_script(args: List[str]) -> subprocess.CompletedProcess:
    """
    Run export.py script with given arguments.

    The book is passed explicitly so the subprocess never has to guess, and
    stdin is closed so a TOC-validation prompt can't hang the run.

    Args:
        args: Command line arguments for export.py

    Returns:
        CompletedProcess with stdout, stderr, and returncode
    """
    cmd = ["python3", "scripts/export.py", "--book", _active_book_id()] + args
    env = {**os.environ, "BOOK_ID": _active_book_id()}
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=120  # 2 minute timeout
    )


def cleanup_test_outputs(suffix: str = "_test") -> None:
    """Clean up test output files for the book under test."""
    _, output_dir = _book_dirs()
    if not output_dir.exists():
        return

    patterns = [
        f"*{suffix}.pdf",
        f"*{suffix}.epub",
        f"*{suffix}.html",
        f"*{suffix}_debug.html",
        f"*{suffix}_epub_debug.html"
    ]

    for pattern in patterns:
        for file in output_dir.glob(pattern):
            try:
                file.unlink()
            except Exception:
                pass


@pytest.mark.slow
def test_export_test_mode() -> None:
    """Test export in test mode (chunk 1 only)."""
    _require_translations()
    cleanup_test_outputs("_test")

    # Run export script with --test flag
    result = run_export_script(["--test", "--force"])

    # Verify script executed successfully
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"

    # Verify output mentions test mode
    assert "Test (Chunk 1)" in result.stdout or "chunk 1" in result.stdout.lower()

    _, output_dir = _book_dirs()
    assert output_dir.exists()

    # Check for PDF, EPUB, and HTML files with _test suffix
    pdf_files = list(output_dir.glob("*_test.pdf"))
    epub_files = list(output_dir.glob("*_test.epub"))
    html_files = list(output_dir.glob("*_test.html"))

    assert len(pdf_files) > 0
    assert len(epub_files) > 0
    assert len(html_files) > 0

    # Verify files are not empty
    for file in pdf_files + epub_files + html_files:
        assert file.stat().st_size > 0
        assert file.stat().st_size > 1024


@pytest.mark.slow
def test_export_range() -> None:
    """Test export with chunk range (1-3)."""
    translated_dir, output_dir = _require_translations()
    available = sorted(translated_dir.glob("chunk_*.md"))
    if len(available) < 3:
        pytest.skip(f"Need at least 3 chunks, found {len(available)}")

    cleanup_test_outputs("_chunks_1_3")

    result = run_export_script(["--chunks", "1-3", "-f", "pdf", "--force"])

    assert result.returncode == 0

    pdf_files = list(output_dir.glob("*_chunks_1_3.pdf"))

    assert len(pdf_files) > 0
    assert pdf_files[0].stat().st_size > 10 * 1024


@pytest.mark.slow
def test_export_full_book() -> None:
    """Test export all chunks (full book mode)."""
    translated_dir, output_dir = _require_translations()
    chunks = list(translated_dir.glob("chunk_*.md"))

    if len(chunks) < 3:
        pytest.skip("Need at least 3 translated chunks for full book test")

    cleanup_test_outputs("")

    result = run_export_script(["-f", "pdf", "--force"])

    assert result.returncode == 0

    pdf_files = list(output_dir.glob("document.pdf"))

    assert len(pdf_files) > 0
    assert pdf_files[0].stat().st_size > 50 * 1024


@pytest.mark.slow
def test_export_all_formats() -> None:
    """Test export all formats (PDF, EPUB, HTML) simultaneously."""
    _require_translations()
    cleanup_test_outputs("_test")

    result = run_export_script(["--test", "--format", "all", "--force"])

    assert result.returncode == 0

    stdout_lower = result.stdout.lower()
    assert "pdf" in stdout_lower
    assert "epub" in stdout_lower
    assert "html" in stdout_lower

    _, output_dir = _book_dirs()

    pdf_files = list(output_dir.glob("*_test.pdf"))
    epub_files = list(output_dir.glob("*_test.epub"))
    html_files = list(output_dir.glob("*_test.html"))

    assert len(pdf_files) > 0
    assert len(epub_files) > 0
    assert len(html_files) > 0

    for file in pdf_files + epub_files + html_files:
        assert file.stat().st_size > 0


@pytest.mark.slow
def test_export_with_custom_metadata() -> None:
    """Test export with custom title and author."""
    _require_translations()
    cleanup_test_outputs("_test")

    custom_title = "Test Book Title"
    custom_author = "Test Author"

    result = run_export_script([
        "--test",
        "-f", "epub",
        "--title", custom_title,
        "--author", custom_author,
        "--force",
    ])

    assert result.returncode == 0

    _, output_dir = _book_dirs()
    epub_files = list(output_dir.glob("*_test.epub"))

    assert len(epub_files) > 0
    assert epub_files[0].stat().st_size > 0


@pytest.mark.slow
def test_export_defaults_title_and_author_from_book_yaml() -> None:
    """Without --title/--author, metadata comes from the book's book.yaml."""
    _require_translations()
    cleanup_test_outputs("_test")

    result = run_export_script(["--test", "-f", "epub", "--force"])
    assert result.returncode == 0

    _, output_dir = _book_dirs()
    epub_files = list(output_dir.glob("*_test.epub"))
    assert epub_files, "no EPUB produced"

    # Read the EPUB's OPF metadata without pulling in ebooklib
    import zipfile
    import re

    with zipfile.ZipFile(epub_files[0]) as zf:
        opf_name = next(n for n in zf.namelist() if n.endswith(".opf"))
        opf = zf.read(opf_name).decode("utf-8")

    titles = re.findall(r"<dc:title[^>]*>([^<]*)</dc:title>", opf)
    assert titles, "EPUB has no dc:title"
    assert "None" not in titles[0], f"title fell back to the string None: {titles[0]!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
