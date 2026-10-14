#!/usr/bin/env python3
"""Regression tests for chunk splitting of sources without page markers.

Bug: ``split_into_chunks`` sectioned the source by ``<!-- Page N -->`` markers.
Sources extracted from plain text (``.txt``) or some EPUBs carry no such
markers, so the whole book became a single section — and therefore a single
chunk — regardless of ``chunk_size``. A 96,000-word book produced one chunk.

The splitter now falls back to paragraph boundaries when no page markers are
present, so ``chunk_size`` is honoured for both kinds of source.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from split_chunks import split_into_chunks  # noqa: E402
from utils.fix_sentence_breaks import fix_sentence_breaks  # noqa: E402


class _StubConfig:
    """BookConfig stand-in exposing only what the splitter reads."""

    def __init__(self, source_file: Path, chunks_dir: Path):
        self.id = "stub"
        self.source_file = source_file
        self.chunks_dir = chunks_dir
        self.translated_dir = chunks_dir.parent / "translated"
        self.source_language = "en"
        self.target_language = "vi"
        self.style_guide_path = str(chunks_dir.parent / "style" / "translation_style_guide.md")


def _paragraph(word: str, count: int) -> str:
    """A paragraph of `count` identical words."""
    return " ".join([word] * count)


@pytest.fixture
def no_page_markers(tmp_path):
    """A source with no page markers: 10 paragraphs of 500 words (= 5,000)."""
    source = tmp_path / "full_text.md"
    source.write_text(
        "\n\n".join(_paragraph(f"word{i}xx", 500) for i in range(10)),
        encoding="utf-8",
    )
    chunks_dir = tmp_path / "chunks"
    return source, chunks_dir


def test_txt_source_without_page_markers_splits_into_multiple_chunks(no_page_markers):
    """5,000 words at chunk_size=1000 must yield more than one chunk."""
    source, chunks_dir = no_page_markers
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    written = sorted(chunks_dir.glob("chunk_*.md"))
    assert len(written) > 1, (
        "a 5,000-word source became a single chunk — paragraph fallback missing"
    )


def test_txt_source_chunks_respect_approximate_size(no_page_markers):
    """No chunk may exceed chunk_size by more than one paragraph's worth."""
    source, chunks_dir = no_page_markers
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    for chunk_file in sorted(chunks_dir.glob("chunk_*.md")):
        words = len(chunk_file.read_text(encoding="utf-8").split())
        assert words <= 1000 + 500, f"{chunk_file.name} has {words} words (cap 1500)"


def test_all_content_preserved_in_fallback_mode(no_page_markers):
    """Splitting on paragraphs must not lose or duplicate words."""
    source, chunks_dir = no_page_markers
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    source_words = source.read_text(encoding="utf-8").split()
    chunk_words = []
    for chunk_file in sorted(chunks_dir.glob("chunk_*.md")):
        chunk_words.extend(chunk_file.read_text(encoding="utf-8").split())
    assert len(chunk_words) == len(source_words)


def test_page_marker_source_still_splits_on_pages(tmp_path):
    """A PDF-style source keeps the original page-marker behaviour."""
    source = tmp_path / "full_text.md"
    source.write_text(
        "\n\n".join(
            f"<!-- Page {i} -->\n\n" + _paragraph(f"word{i}xx", 400) for i in range(1, 6)
        ),
        encoding="utf-8",
    )
    chunks_dir = tmp_path / "chunks"
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=500, category="non-fiction", cfg=cfg)

    written = sorted(chunks_dir.glob("chunk_*.md"))
    assert len(written) > 1


def test_chunk_files_are_reported_in_manifest(no_page_markers):
    """Every chunk written must appear in manifest.json."""
    import json

    source, chunks_dir = no_page_markers
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    manifest = json.loads((chunks_dir / "manifest.json").read_text(encoding="utf-8"))
    written = {f.name for f in chunks_dir.glob("chunk_*.md")}
    listed = {c["source"] for c in manifest["chunks"]}
    assert written == listed


def test_sentence_fixer_never_joins_across_page_marker(tmp_path):
    """Page markers remain before their page's prose after repeated cleanup."""
    source = tmp_path / "full_text.md"
    source.write_text(
        "<!-- Page 42 -->\n\nunfinished sentence\n\n<!-- Page 43 -->\n\ncontinues here.",
        encoding="utf-8",
    )

    assert fix_sentence_breaks(source, backup=False) == 0
    assert fix_sentence_breaks(source, backup=False) == 0
    assert source.read_text(encoding="utf-8") == (
        "<!-- Page 42 -->\n\nunfinished sentence\n\n<!-- Page 43 -->\n\ncontinues here."
    )


def test_marker_source_splits_oversized_page_at_paragraph_boundaries(tmp_path):
    """A long page must not become one oversized translation unit."""
    source = tmp_path / "full_text.md"
    source.write_text(
        "<!-- Page 1 -->\n\n"
        + "\n\n".join(_paragraph(f"word{i}xx", 400) for i in range(4)),
        encoding="utf-8",
    )
    chunks_dir = tmp_path / "chunks"
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    written = sorted(chunks_dir.glob("chunk_*.md"))
    assert len(written) == 2
    assert all(len(chunk.read_text(encoding="utf-8").split()) <= 1200 for chunk in written)
    assert sum(chunk.read_text(encoding="utf-8").count("<!-- Page 1 -->") for chunk in written) == 1


def test_regeneration_removes_stale_pending_chunks(no_page_markers):
    """A shorter safe regeneration must not leave an orphaned chunk file."""
    source, chunks_dir = no_page_markers
    cfg = _StubConfig(source, chunks_dir)
    chunks_dir.mkdir()
    (chunks_dir / "chunk_999.md").write_text("stale", encoding="utf-8")

    split_into_chunks(source, chunks_dir, chunk_size=1000, category="non-fiction", cfg=cfg)

    assert not (chunks_dir / "chunk_999.md").exists()


def test_marker_only_pages_attach_to_following_prose(tmp_path):
    """Consecutive blank source pages never form a marker-only output chunk."""
    source = tmp_path / "full_text.md"
    source.write_text(
        "<!-- Page 1 -->\n\n" + _paragraph("firstxx", 500)
        + "\n\n<!-- Page 2 -->\n\n<!-- Page 3 -->\n\n"
        + _paragraph("secondxx", 500),
        encoding="utf-8",
    )
    chunks_dir = tmp_path / "chunks"
    cfg = _StubConfig(source, chunks_dir)

    split_into_chunks(source, chunks_dir, chunk_size=600, category="non-fiction", cfg=cfg)

    written = sorted(chunks_dir.glob("chunk_*.md"))
    assert len(written) == 2
    assert all("firstxx" in chunk.read_text(encoding="utf-8") or "secondxx" in chunk.read_text(encoding="utf-8") for chunk in written)
    combined = "\n".join(chunk.read_text(encoding="utf-8") for chunk in written)
    assert combined.count("<!-- Page 1 -->") == 1
    assert combined.count("<!-- Page 2 -->") == 1
    assert combined.count("<!-- Page 3 -->") == 1
