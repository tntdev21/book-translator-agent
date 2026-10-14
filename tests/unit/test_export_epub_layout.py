#!/usr/bin/env python3
"""EPUB layout regressions: `##` section headings centred, cover a full-bleed first page."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from utils import export_epub  # noqa: E402


def test_section_heading_h2_is_centred():
    # markdown_converter emits `## X` as <div class="section-heading"><h2>X</h2></div>
    rule = re.search(r"([^{}]*\.section-heading h2[^{}]*)\{([^}]*)\}", export_epub._BASE_CSS)
    assert rule and "text-align: center" in rule.group(2)


def test_cover_is_first_linear_page_without_margins(tmp_path):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"\xff\xd8\xff\xd9")
    book = export_epub.create_epub("<h1>One</h1><p>x</p>", title="T", cover_path=cover)
    assert book.spine[0] == "cover"
    page = book.get_item_with_id("cover")
    assert page.is_linear
    assert any(link["href"] == "style/cover.css" for link in page.links)
    assert "margin: 0" in export_epub.COVER_CSS
