#!/usr/bin/env python3
"""
Per-book configuration for the multi-book translation pipeline.

Each book lives under ``books/<book-id>/`` and carries a ``book.yaml`` that
declares its title/author, category, and paths. Scripts resolve the active book
once and read every path from the returned :class:`BookConfig` instead of
hardcoding ``translated/``, ``style/``, etc.

Active-book resolution order (first match wins):

1. explicit ``--book <id>`` flag
2. ``BOOK_ID`` environment variable
3. auto-detect when exactly one book exists under ``books/``
4. otherwise: exit with a descriptive error

There is deliberately no "current book" pointer file — a stale pointer is a
much worse failure mode than typing ``BOOK_ID=x`` once.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BOOKS_DIR = REPO_ROOT / "books"

# Shared formatting conventions live at the repo root; a book may override them
# by placing its own copy under the book's style/ directory.
SHARED_FORMATTING_RULES = REPO_ROOT / "style" / "formatting_rules.md"

DEFAULT_PATHS = {
    "source": "source/full_text.md",
    "chunks": "chunks",
    "translated": "translated",
    "style": "style",
    "output": "output",
    "cover": "cover.jpg",
}


class BookConfigError(SystemExit):
    """Raised when the active book cannot be resolved or loaded."""


@dataclass
class BookConfig:
    """Resolved configuration for one book."""

    id: str
    root: Path

    title_en: str = ""
    title_vi: str = ""
    subtitle_vi: str = ""  # optional; shown on the generated title page
    author: str = ""
    translator: str = ""
    language_pair: str = "en-vi"
    category: str = "literary"
    epub_identifier: str = ""
    chunk_size: int = 3000
    font: str = ""  # folder name under fonts/; empty = fonts.DEFAULT_FONT
    derivation: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)
    page_sizes: dict = field(default_factory=dict)
    rights: dict = field(default_factory=dict)

    # -- resolved paths ---------------------------------------------------

    def _path(self, key: str) -> Path:
        return self.root / self.paths.get(key, DEFAULT_PATHS[key])

    @property
    def source_file(self) -> Path:
        return self._path("source")

    @property
    def chunks_dir(self) -> Path:
        return self._path("chunks")

    @property
    def translated_dir(self) -> Path:
        return self._path("translated")

    @property
    def style_dir(self) -> Path:
        return self._path("style")

    @property
    def output_dir(self) -> Path:
        return self._path("output")

    @property
    def cover_path(self) -> Path:
        return self._path("cover")

    @property
    def samples_dir(self) -> Path:
        """Reference translations used to derive this book's DNA.

        One subdirectory per sample (``samples/<name>/`` holding ``en.md`` and
        ``vi.md``). A sample is raw material for style derivation, never
        translation input — nothing here is ever chunked or exported.
        """
        return self.root / "samples"

    @property
    def dna_path(self) -> Path:
        """Author DNA derived from every sample, merged into one file."""
        return self.root / "dna.md"

    @property
    def corrections_path(self) -> Path:
        """Running log of editor findings — read by translators on each run."""
        return self.style_dir / "corrections.md"

    @property
    def manifest_path(self) -> Path:
        return self.chunks_dir / "manifest.json"

    @property
    def style_guide_path(self) -> Path:
        return self.style_dir / "translation_style_guide.md"

    @property
    def glossary_path(self) -> Path:
        return self.style_dir / "glossary.csv"

    @property
    def new_terms_path(self) -> Path:
        return self.style_dir / "new_terms.txt"

    @property
    def book_names_path(self) -> Path:
        return self.style_dir / "book_names.json"

    @property
    def formatting_rules_path(self) -> Path:
        """Book-local override if present, else the shared root copy."""
        local = self.style_dir / "formatting_rules.md"
        return local if local.exists() else SHARED_FORMATTING_RULES

    # -- language ---------------------------------------------------------

    @property
    def source_language(self) -> str:
        return self.language_pair.split("-")[0]

    @property
    def target_language(self) -> str:
        parts = self.language_pair.split("-")
        return parts[1] if len(parts) > 1 else "vi"

    @property
    def display_title(self) -> str:
        """Title used for exports: Vietnamese title, falling back to English."""
        return self.title_vi or self.title_en or self.id


def resolve_book_id(cli_book: Optional[str] = None) -> str:
    """Determine which book to operate on. Exits with a message on ambiguity."""
    if cli_book:
        return cli_book

    env_book = os.environ.get("BOOK_ID")
    if env_book:
        return env_book

    if not BOOKS_DIR.is_dir():
        raise BookConfigError(
            f"No books directory at {BOOKS_DIR}.\n"
            "Create one with: books/<book-id>/book.yaml"
        )

    candidates = sorted(p.parent.name for p in BOOKS_DIR.glob("*/book.yaml"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise BookConfigError(f"No books found under {BOOKS_DIR}/.")
    raise BookConfigError(
        f"Multiple books found: {', '.join(candidates)}.\n"
        "Select one with --book <id> or the BOOK_ID environment variable."
    )


def load_book(book_id: Optional[str] = None) -> BookConfig:
    """Load the resolved book's ``book.yaml`` into a :class:`BookConfig`."""
    bid = resolve_book_id(book_id)
    book_root = BOOKS_DIR / bid
    yaml_path = book_root / "book.yaml"

    if not yaml_path.exists():
        raise BookConfigError(f"book.yaml not found: {yaml_path}")

    try:
        import yaml
    except ImportError as e:  # pragma: no cover - dependency is in requirements
        raise BookConfigError(
            "PyYAML is required to read book.yaml. Install with: pip install PyYAML"
        ) from e

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise BookConfigError(f"Invalid YAML in {yaml_path}: {e}") from e

    if not isinstance(data, dict):
        raise BookConfigError(f"{yaml_path} must contain a YAML mapping")

    data.setdefault("id", bid)
    # Merge book overrides over the defaults rather than replacing the mapping,
    # so a book.yaml may declare just one path and inherit the rest.
    data["paths"] = {**DEFAULT_PATHS, **data.get("paths", {})}

    known = {
        "id", "title_en", "title_vi", "author", "translator", "language_pair",
        "category", "epub_identifier", "chunk_size", "font",
        "derivation", "paths", "page_sizes", "rights",
    }
    unknown = set(data) - known
    if unknown:
        raise BookConfigError(
            f"Unknown key(s) in {yaml_path}: {', '.join(sorted(unknown))}"
        )

    return BookConfig(root=book_root, **data)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def strip_book_flag(argv: list[str]) -> tuple[list[str], Optional[str]]:
    """Pull ``--book <id>`` / ``--book=<id>`` out of an argv list.

    Handles both argparse and hand-rolled ``sys.argv`` scripts: the flag is
    removed before argparse parses, so callers may index positional args
    normally without worrying about shifting offsets.

    Returns ``(remaining_args, book_id)``.
    """
    remaining: list[str] = []
    book_id: Optional[str] = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--book":
            if i + 1 >= len(argv):
                raise BookConfigError("--book requires a value")
            book_id = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--book="):
            book_id = arg.split("=", 1)[1]
            i += 1
            continue
        remaining.append(arg)
        i += 1
    return remaining, book_id


def add_book_argument(parser) -> None:
    """Register ``--book`` on an argparse parser."""
    parser.add_argument(
        "--book",
        default=None,
        metavar="ID",
        help="Book id under books/ (default: $BOOK_ID, or the only book present)",
    )


def get_config_from_args(args) -> BookConfig:
    """Load the book selected via an argparse namespace."""
    return load_book(getattr(args, "book", None))


def bootstrap_argv(argv: Optional[list[str]] = None) -> tuple[list[str], BookConfig]:
    """Convenience for hand-rolled ``sys.argv`` scripts.

    Returns the program arguments (with ``--book`` removed) and the loaded
    config, so callers can keep using positional indexing.

    Example::

        argv, cfg = bootstrap_argv(sys.argv)
        input_file = argv[1] if len(argv) > 1 else str(cfg.source_file)
    """
    raw = list(sys.argv if argv is None else argv)
    remaining, book_id = strip_book_flag(raw[1:])
    return [raw[0], *remaining], load_book(book_id)
