#!/usr/bin/env python3
"""Tests for EPUB extraction.

Two shapes matter:

* **Paged EPUBs** (Internet Archive scans) — one XHTML file per printed page.
  Page numbers must survive as ``<!-- Page N -->`` markers, because the chunker
  sections on those markers. Without them a whole book becomes one chunk.
* **Flowable EPUBs** — chapter documents with headings and no pagination.
  Headings must survive as Markdown headings.
"""

import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_UTILS = REPO_ROOT / "scripts" / "utils"
for p in (SCRIPTS_UTILS, REPO_ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from utils.extract_epub import extract_epub  # noqa: E402

_PAGE_TEMPLATE = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Page {n}</title></head>
<body><p>{text}</p></body></html>"""

_CHAPTER_TEMPLATE = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{title}</title></head>
<body><h1>{title}</h1><p>{text}</p></body></html>"""


def _write_epub(path: Path, entries: list[tuple[str, str]]) -> Path:
    """Build a minimal EPUB zip with the given (name, xhtml) entries."""
    container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf"
    media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    manifest = "\n".join(
        f'<item id="i{i}" href="{name}" media-type="application/xhtml+xml"/>'
        for i, (name, _) in enumerate(entries)
    )
    spine = "\n".join(f'<itemref idref="i{i}"/>' for i in range(len(entries)))
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="id">test-epub</dc:identifier>
    <dc:title>Test</dc:title><dc:language>en</dc:language>
  </metadata>
  <manifest>{manifest}</manifest>
  <spine>{spine}</spine>
</package>"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", opf)
        for name, xhtml in entries:
            zf.writestr(f"OEBPS/{name}", xhtml)
    return path


@pytest.fixture
def paged_epub(tmp_path: Path) -> Path:
    entries = [
        (f"page_{n}.html", _PAGE_TEMPLATE.format(n=n, text=f"Content of printed page {n} here."))
        for n in range(1, 8)
    ]
    return _write_epub(tmp_path / "paged.epub", entries)


@pytest.fixture
def flowable_epub(tmp_path: Path) -> Path:
    entries = [
        ("ch1.xhtml", _CHAPTER_TEMPLATE.format(title="The First Chapter", text="Body of chapter one.")),
        ("ch2.xhtml", _CHAPTER_TEMPLATE.format(title="The Second Chapter", text="Body of chapter two.")),
    ]
    return _write_epub(tmp_path / "flowable.epub", entries)


def test_paged_epub_emits_page_markers(paged_epub: Path, tmp_path: Path) -> None:
    """Page numbers must survive — the chunker sections on these markers."""
    out = tmp_path / "full_text.md"
    extract_epub(str(paged_epub), str(out))

    text = out.read_text(encoding="utf-8")
    assert "<!-- Page 1 -->" in text
    assert "<!-- Page 7 -->" in text
    assert text.count("<!-- Page") == 7


def test_paged_epub_preserves_page_content(paged_epub: Path, tmp_path: Path) -> None:
    out = tmp_path / "full_text.md"
    extract_epub(str(paged_epub), str(out))

    text = out.read_text(encoding="utf-8")
    for n in range(1, 8):
        assert f"Content of printed page {n} here." in text


def test_flowable_epub_keeps_headings(flowable_epub: Path, tmp_path: Path) -> None:
    out = tmp_path / "full_text.md"
    extract_epub(str(flowable_epub), str(out))

    text = out.read_text(encoding="utf-8")
    assert "# The First Chapter" in text
    assert "# The Second Chapter" in text
    assert "Body of chapter one." in text


def test_ocr_standalone_one_is_repaired(tmp_path: Path) -> None:
    """'1 live in Seattle' is an OCR error for 'I live in Seattle'."""
    entries = [
        ("page_1.html", _PAGE_TEMPLATE.format(n=1, text="3. 1 live in Seattle, which has rain.")),
    ]
    epub_path = _write_epub(tmp_path / "ocr.epub", entries)
    out = tmp_path / "full_text.md"

    extract_epub(str(epub_path), str(out))

    text = out.read_text(encoding="utf-8")
    assert "I live in Seattle" in text
    assert "1 live in Seattle" not in text


def test_real_numerals_are_not_turned_into_letter_i(tmp_path: Path) -> None:
    """A genuine '1' followed by a number or capital must survive."""
    entries = [
        ("page_1.html", _PAGE_TEMPLATE.format(n=1, text="There were 1 000 people and 1 Person left.")),
    ]
    epub_path = _write_epub(tmp_path / "nums.epub", entries)
    out = tmp_path / "full_text.md"

    extract_epub(str(epub_path), str(out))

    text = out.read_text(encoding="utf-8")
    assert "1 000 people" in text, "numeric '1' was rewritten to 'I'"
    assert "1 Person" in text, "capitalised follower wrongly triggered the repair"


def test_curly_quotes_and_ligatures_are_normalised(tmp_path: Path) -> None:
    entries = [
        ("page_1.html", _PAGE_TEMPLATE.format(n=1, text="“The ﬁrst ﬂaw,” she said…")),
    ]
    epub_path = _write_epub(tmp_path / "typo.epub", entries)
    out = tmp_path / "full_text.md"

    extract_epub(str(epub_path), str(out))

    text = out.read_text(encoding="utf-8")
    assert '"The first flaw,"' in text
    assert "..." in text


def test_max_pages_limits_output(paged_epub: Path, tmp_path: Path) -> None:
    out = tmp_path / "sample.md"
    extract_epub(str(paged_epub), str(out), max_pages=3)

    text = out.read_text(encoding="utf-8")
    assert "<!-- Page 3 -->" in text
    assert "<!-- Page 4 -->" not in text


def test_extraction_is_deterministic(paged_epub: Path, tmp_path: Path) -> None:
    """Same input twice must produce byte-identical output."""
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    extract_epub(str(paged_epub), str(a))
    extract_epub(str(paged_epub), str(b))
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises((FileNotFoundError, zipfile.BadZipFile)):
        extract_epub(str(tmp_path / "nope.epub"), str(tmp_path / "out.md"))
