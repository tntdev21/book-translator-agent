#!/usr/bin/env python3
"""Tests for scripts/utils/book_config.py — book resolution and path derivation."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from utils import book_config as bc  # noqa: E402


BOOK_YAML = """\
id: {bid}
title_en: "English Title"
title_vi: "Tiêu đề tiếng Việt"
author: "Some Author"
translator: "Some Translator"
language_pair: en-vi
category: non-fiction
epub_identifier: {bid}-vi
chunk_size: 2500
"""


def make_book(books_dir: Path, bid: str, body: str | None = None, extra: str = "") -> Path:
    root = books_dir / bid
    root.mkdir(parents=True, exist_ok=True)
    text = body if body is not None else BOOK_YAML.format(bid=bid) + extra
    (root / "book.yaml").write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def books_dir(tmp_path, monkeypatch):
    """Point BOOKS_DIR at a temp directory so tests never touch the real repo."""
    d = tmp_path / "books"
    d.mkdir()
    monkeypatch.setattr(bc, "BOOKS_DIR", d)
    monkeypatch.delenv("BOOK_ID", raising=False)
    return d


# ---------------------------------------------------------------------------
# resolve_book_id — priority order
# ---------------------------------------------------------------------------

class TestResolveBookId:
    def test_explicit_flag_wins_over_env(self, books_dir, monkeypatch):
        monkeypatch.setenv("BOOK_ID", "from-env")
        make_book(books_dir, "from-env")
        make_book(books_dir, "from-flag")
        assert bc.resolve_book_id("from-flag") == "from-flag"

    def test_env_wins_when_no_flag(self, books_dir, monkeypatch):
        monkeypatch.setenv("BOOK_ID", "from-env")
        make_book(books_dir, "from-env")
        make_book(books_dir, "other")
        assert bc.resolve_book_id() == "from-env"

    def test_auto_detect_single_book(self, books_dir):
        make_book(books_dir, "only-one")
        assert bc.resolve_book_id() == "only-one"

    def test_no_books_raises(self, books_dir):
        with pytest.raises(bc.BookConfigError, match="No books found"):
            bc.resolve_book_id()

    def test_multiple_books_without_selection_raises(self, books_dir):
        make_book(books_dir, "alpha")
        make_book(books_dir, "beta")
        with pytest.raises(bc.BookConfigError, match="Multiple books found"):
            bc.resolve_book_id()

    def test_multiple_books_error_names_the_candidates(self, books_dir):
        make_book(books_dir, "alpha")
        make_book(books_dir, "beta")
        with pytest.raises(bc.BookConfigError) as exc:
            bc.resolve_book_id()
        assert "alpha" in str(exc.value) and "beta" in str(exc.value)


# ---------------------------------------------------------------------------
# load_book — parsing and defaults
# ---------------------------------------------------------------------------

class TestLoadBook:
    def test_loads_declared_fields(self, books_dir):
        make_book(books_dir, "life-3-0")
        cfg = bc.load_book("life-3-0")
        assert cfg.id == "life-3-0"
        assert cfg.title_en == "English Title"
        assert cfg.title_vi == "Tiêu đề tiếng Việt"
        assert cfg.author == "Some Author"
        assert cfg.category == "non-fiction"
        assert cfg.chunk_size == 2500
        assert cfg.epub_identifier == "life-3-0-vi"

    def test_root_is_the_book_directory(self, books_dir):
        root = make_book(books_dir, "life-3-0")
        assert bc.load_book("life-3-0").root == root

    def test_missing_yaml_raises(self, books_dir):
        (books_dir / "ghost").mkdir()
        with pytest.raises(bc.BookConfigError, match="book.yaml not found"):
            bc.load_book("ghost")

    def test_unknown_key_raises(self, books_dir):
        make_book(books_dir, "life-3-0", extra="typo_key: 1\n")
        with pytest.raises(bc.BookConfigError, match="Unknown key"):
            bc.load_book("life-3-0")

    def test_non_mapping_yaml_raises(self, books_dir):
        make_book(books_dir, "life-3-0", body="- just\n- a\n- list\n")
        with pytest.raises(bc.BookConfigError, match="YAML mapping"):
            bc.load_book("life-3-0")

    def test_invalid_yaml_raises(self, books_dir):
        make_book(books_dir, "life-3-0", body="id: x\n  bad indent: [\n")
        with pytest.raises(bc.BookConfigError, match="Invalid YAML"):
            bc.load_book("life-3-0")

    def test_minimal_yaml_gets_defaults(self, books_dir):
        make_book(books_dir, "bare", body="id: bare\n")
        cfg = bc.load_book("bare")
        assert cfg.language_pair == "en-vi"
        assert cfg.category == "literary"
        assert cfg.chunk_size == 3000
        assert cfg.paths == bc.DEFAULT_PATHS


# ---------------------------------------------------------------------------
# Path derivation
# ---------------------------------------------------------------------------

class TestPathDerivation:
    def test_default_paths_are_book_root_relative(self, books_dir):
        root = make_book(books_dir, "life-3-0")
        cfg = bc.load_book("life-3-0")
        assert cfg.source_file == root / "source" / "full_text.md"
        assert cfg.chunks_dir == root / "chunks"
        assert cfg.translated_dir == root / "translated"
        assert cfg.style_dir == root / "style"
        assert cfg.output_dir == root / "output"
        assert cfg.cover_path == root / "cover.jpg"

    def test_derived_file_paths(self, books_dir):
        root = make_book(books_dir, "life-3-0")
        cfg = bc.load_book("life-3-0")
        assert cfg.manifest_path == root / "chunks" / "manifest.json"
        assert cfg.style_guide_path == root / "style" / "translation_style_guide.md"
        assert cfg.glossary_path == root / "style" / "glossary.csv"
        assert cfg.new_terms_path == root / "style" / "new_terms.txt"
        assert cfg.book_names_path == root / "style" / "book_names.json"

    def test_book_may_override_a_single_path(self, books_dir):
        root = make_book(
            books_dir, "life-3-0",
            body="id: life-3-0\npaths:\n  translated: out/vi\n",
        )
        cfg = bc.load_book("life-3-0")
        assert cfg.translated_dir == root / "out" / "vi"
        # Unspecified paths keep their defaults rather than being wiped.
        assert cfg.chunks_dir == root / "chunks"

    def test_language_pair_splitting(self, books_dir):
        make_book(books_dir, "jp", body="id: jp\nlanguage_pair: ja-vi\n")
        cfg = bc.load_book("jp")
        assert cfg.source_language == "ja"
        assert cfg.target_language == "vi"

    def test_language_pair_without_target_defaults_to_vi(self, books_dir):
        make_book(books_dir, "odd", body="id: odd\nlanguage_pair: en\n")
        assert bc.load_book("odd").target_language == "vi"

    def test_display_title_prefers_vietnamese(self, books_dir):
        make_book(books_dir, "life-3-0")
        assert bc.load_book("life-3-0").display_title == "Tiêu đề tiếng Việt"

    def test_display_title_falls_back_to_english(self, books_dir):
        make_book(books_dir, "x", body='id: x\ntitle_en: "Only English"\n')
        assert bc.load_book("x").display_title == "Only English"

    def test_display_title_falls_back_to_id(self, books_dir):
        make_book(books_dir, "x", body="id: x\n")
        assert bc.load_book("x").display_title == "x"


# ---------------------------------------------------------------------------
# formatting_rules: local override vs shared fallback
# ---------------------------------------------------------------------------

class TestFormattingRules:
    def test_falls_back_to_shared_when_book_has_none(self, books_dir, tmp_path, monkeypatch):
        shared = tmp_path / "shared_formatting_rules.md"
        shared.write_text("# Shared\n", encoding="utf-8")
        monkeypatch.setattr(bc, "SHARED_FORMATTING_RULES", shared)

        make_book(books_dir, "life-3-0")
        assert bc.load_book("life-3-0").formatting_rules_path == shared

    def test_book_local_override_wins(self, books_dir, tmp_path, monkeypatch):
        shared = tmp_path / "shared_formatting_rules.md"
        shared.write_text("# Shared\n", encoding="utf-8")
        monkeypatch.setattr(bc, "SHARED_FORMATTING_RULES", shared)

        root = make_book(books_dir, "life-3-0")
        local = root / "style" / "formatting_rules.md"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text("# Local\n", encoding="utf-8")

        assert bc.load_book("life-3-0").formatting_rules_path == local


# ---------------------------------------------------------------------------
# strip_book_flag / CLI helpers
# ---------------------------------------------------------------------------

class TestStripBookFlag:
    def test_removes_separate_flag_and_value(self):
        remaining, bid = bc.strip_book_flag(["a", "--book", "life-3-0", "b"])
        assert remaining == ["a", "b"]
        assert bid == "life-3-0"

    def test_removes_equals_form(self):
        remaining, bid = bc.strip_book_flag(["--book=life-3-0", "x"])
        assert remaining == ["x"]
        assert bid == "life-3-0"

    def test_absent_flag_returns_none(self):
        remaining, bid = bc.strip_book_flag(["a", "--force"])
        assert remaining == ["a", "--force"]
        assert bid is None

    def test_dangling_flag_raises(self):
        with pytest.raises(bc.BookConfigError, match="--book requires a value"):
            bc.strip_book_flag(["a", "--book"])

    def test_preserves_positional_order_for_indexing(self):
        """Hand-rolled scripts index argv[1:]; the flag must not shift offsets."""
        remaining, _ = bc.strip_book_flag(["in.md", "out.md", "--book", "x", "3000"])
        assert remaining[0] == "in.md"
        assert remaining[1] == "out.md"
        assert remaining[2] == "3000"

    def test_empty_argv(self):
        assert bc.strip_book_flag([]) == ([], None)


class TestAddBookArgument:
    def test_registers_book_flag(self):
        import argparse

        parser = argparse.ArgumentParser()
        bc.add_book_argument(parser)
        assert parser.parse_args(["--book", "life-3-0"]).book == "life-3-0"
        assert parser.parse_args([]).book is None

    def test_get_config_from_args(self, books_dir):
        import argparse

        make_book(books_dir, "life-3-0")
        args = argparse.Namespace(book="life-3-0")
        assert bc.get_config_from_args(args).id == "life-3-0"

    def test_get_config_from_args_without_book_attr(self, books_dir):
        import argparse

        make_book(books_dir, "solo")
        assert bc.get_config_from_args(argparse.Namespace()).id == "solo"


class TestBootstrapArgv:
    def test_strips_flag_and_loads_config(self, books_dir):
        make_book(books_dir, "life-3-0")
        argv, cfg = bc.bootstrap_argv(["extract.py", "--book", "life-3-0", "in.pdf"])
        assert argv == ["extract.py", "in.pdf"]
        assert cfg.id == "life-3-0"

    def test_argv_indexing_still_works(self, books_dir):
        make_book(books_dir, "life-3-0")
        argv, _ = bc.bootstrap_argv(["split.py", "src.md", "--book", "life-3-0", "chunks/"])
        assert argv[1] == "src.md"
        assert argv[2] == "chunks/"


# ---------------------------------------------------------------------------
# Real repo sanity — the module's own constants must line up with reality
# ---------------------------------------------------------------------------

class TestRepoConstants:
    def test_books_dir_is_under_repo_root(self):
        assert bc.BOOKS_DIR == bc.REPO_ROOT / "books"

    def test_repo_root_contains_scripts_dir(self):
        assert (bc.REPO_ROOT / "scripts").is_dir()

    def test_default_paths_cover_every_key_used_by_properties(self):
        for key in ("source", "chunks", "translated", "style", "output", "cover"):
            assert key in bc.DEFAULT_PATHS
