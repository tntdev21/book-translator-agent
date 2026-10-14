#!/usr/bin/env python3
"""Regression test for export.py's title resolution.

Bug: ``create_pdf`` was called with ``title=args.title`` and no fallback, while
the EPUB and HTML branches both had one. Omitting ``-t`` produced a PDF whose
metadata title was literally ``None``.

The fallback now comes from the book's ``book.yaml`` (title_vi/author) rather
than a hardcoded publisher string, so the test asserts on the resolved locals
rather than on the ``args.title or ...`` text.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class _StubConfig:
    """BookConfig stand-in for export.py's locals."""

    id = "stub-book"
    title_vi = "Tiêu đề sách"
    title_en = "Book Title"
    subtitle_vi = ""
    author = "Some Author"
    epub_identifier = "stub-book-vi"
    display_title = title_vi
    language_pair = "en-vi"
    font = ""

    def __init__(self, root: Path):
        self.root = root
        self.output_dir = root / "output"
        self.translated_dir = root / "translated"
        self.cover_path = root / "cover.jpg"


class TestTitleFallback:
    def test_source_does_not_pass_bare_args_title(self):
        """No branch may pass args.title straight through without a fallback."""
        src = (SCRIPTS / "export.py").read_text(encoding="utf-8")
        assert "title=args.title\n" not in src, "bare args.title still passed"
        assert "title=args.title or" not in src, "title still resolved from args alone"

    def test_title_resolved_from_book_config(self):
        """export.py must derive title/author from the resolved BookConfig."""
        src = (SCRIPTS / "export.py").read_text(encoding="utf-8")
        assert "args.title or cfg.title_vi" in src, "title has no book.yaml fallback"
        assert "args.author or cfg.author" in src, "author has no book.yaml fallback"

    def test_all_three_format_branches_use_the_resolved_title(self):
        src = (SCRIPTS / "export.py").read_text(encoding="utf-8")
        # create_pdf / create_epub / create_html each take the resolved title.
        assert src.count("title=title") == 3, "a format branch ignores the resolved title"

    def test_captures_non_none_title_end_to_end(self, tmp_path, monkeypatch):
        """Run export with --test and assert create_pdf receives a real title."""
        import export as export_mod

        book_root = tmp_path / "books" / "stub-book"
        translated = book_root / "translated"
        translated.mkdir(parents=True)
        # A TOC that passes validation so execution reaches the PDF branch.
        (translated / "chunk_001.md").write_text(
            "# MỤC LỤC\nCHƯƠNG 1\n\n# CHƯƠNG 1\n\nNội dung.\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        import utils.book_config as book_config

        cfg = _StubConfig(book_root)
        monkeypatch.setattr(book_config, "get_config_from_args", lambda args: cfg)
        monkeypatch.setattr(export_mod, "get_config_from_args", lambda args: cfg)

        captured = {}

        def fake_create_pdf(content, path, title=None, **_kwargs):
            captured["title"] = title
            Path(path).write_text("<html></html>", encoding="utf-8")
            return True

        import utils.export_pdf as export_pdf
        import utils.markdown_converter as markdown_converter

        monkeypatch.setattr(export_pdf, "create_pdf", fake_create_pdf)
        # export.py imports these lazily inside main(); patch the module attrs so
        # the PDF branch runs without invoking WeasyPrint.
        monkeypatch.setattr(
            markdown_converter,
            "markdown_to_html_with_dialogue",
            lambda md, include_cover=True, cover_path=None: "<html><body></body></html>",
        )
        monkeypatch.setattr(
            markdown_converter, "make_toc_links_clickable", lambda md: md
        )

        monkeypatch.setattr(sys, "argv", ["export.py", "-f", "pdf", "--test", "--force"])
        try:
            export_mod.main()
        except SystemExit:
            pass

        assert captured.get("title") is not None, "create_pdf received title=None"
        assert captured["title"] != "None"
        assert captured["title"] == cfg.title_vi
