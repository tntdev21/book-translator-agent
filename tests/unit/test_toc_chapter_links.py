#!/usr/bin/env python3
"""Regression: TOC links target top-level chapters, ids are unique.

Translated TOC wording can drift from the chapter heading, and a Notes chapter
can repeat chapter titles as ``##`` subheadings. TOC links must still land on
the ``# `` chapter heading, never on the Notes subheading.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from utils.export_epub import extract_anchor_map  # noqa: E402
from utils.markdown_converter import (  # noqa: E402
    dedupe_ids,
    make_toc_links_clickable,
    markdown_to_html_with_dialogue,
    scan_chapter_headings,
)

BOOK = """# Mục lục

3. Linh hồn di trú

6. Phản chuyên gia

# 3. Linh hồn di cư

Text.

# 6. Kẻ phản chuyên gia

Text.

# Ghi chú

## 3. Linh hồn di cư

## 6. Phản chuyên gia
"""


def test_scan_chapter_headings_numbers_first_occurrence():
    top, by_number = scan_chapter_headings(BOOK.splitlines())
    assert by_number["3"] == "3-linh-hon-di-cu"
    assert by_number["6"] == "6-ke-phan-chuyen-gia"
    assert "3-linh-hon-di-cu" in top


def test_numbered_entry_links_by_number_despite_wording():
    out = make_toc_links_clickable(BOOK)
    assert "[3. Linh hồn di trú](#3-linh-hon-di-cu)" in out


def test_entry_does_not_link_to_notes_subheading():
    out = make_toc_links_clickable(BOOK)
    # "6. Phản chuyên gia" matches the Notes ## exactly, but must go to chapter 6
    assert "[6. Phản chuyên gia](#6-ke-phan-chuyen-gia)" in out
    assert "(#6-phan-chuyen-gia)" not in out


def test_dedupe_ids_suffixes_repeats():
    html = '<div id="a"></div><div id="b"></div><div id="a"></div><div id="a"></div>'
    assert dedupe_ids(html) == '<div id="a"></div><div id="b"></div><div id="a-2"></div><div id="a-3"></div>'


def test_rendered_html_has_unique_ids():
    import re

    html = markdown_to_html_with_dialogue(make_toc_links_clickable(BOOK + "\n# 3. Linh hồn di cư\n"))
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))


def test_epub_anchor_map_first_occurrence_wins():
    chapters = [{"content": '<div id="x"></div>'}, {"content": '<div id="x"></div>'}]
    assert extract_anchor_map(chapters)["x"] == 0


# --- validate_toc.check_toc_links (export + book-close gate) -------------------

from utils.validate_toc import check_toc_links  # noqa: E402


def test_check_toc_links_drift_is_warning_not_error():
    errors, warnings = check_toc_links(BOOK)
    assert errors == []
    assert any("Linh hồn di trú" in w for w in warnings)


def test_check_toc_links_unlinked_entry_is_error():
    book = BOOK.replace("6. Phản chuyên gia\n", "6. Phản chuyên gia\n\nChú thích\n", 1)
    errors, _ = check_toc_links(book)
    assert any("'Chú thích'" in e for e in errors)


def test_check_toc_links_front_entry_needs_front_block():
    book = BOOK.replace("# Mục lục\n", "# Mục lục\n\nLời tặng\n", 1)
    assert any("'Lời tặng'" in e for e in check_toc_links(book)[0])
    marked = '<!-- front id="loi-tang" -->\n*Cho thầy cô*\n<!-- /front -->\n\n' + book
    assert not any("'Lời tặng'" in e for e in check_toc_links(marked)[0])


def test_toc_ends_at_front_block():
    """An epigraph page after the TOC is not a list of unlinked entries."""
    book = BOOK.replace("# 3. Linh hồn di cư", '<!-- front id="de-tu-2" -->\nCái đẹp đổi thay\n<!-- /front -->\n\n# 3. Linh hồn di cư', 1)
    assert not any("Cái đẹp" in e for e in check_toc_links(book)[0])


# --- front-matter blocks: language-neutral ids + generated title page ----------

from utils.markdown_converter import fill_title_page  # noqa: E402

FRONT = ('<!-- front id="title-page" -->\n<!-- /front -->\n\n'
         '<!-- front id="copyright" -->\n<small>Bản quyền © 2011</small>\n<!-- /front -->\n\n')


def test_translated_front_entry_links_to_neutral_id():
    book = FRONT + BOOK.replace("# Mục lục\n", "# Mục lục\n\nTrang tựa\n\nBản quyền\n", 1)
    out = make_toc_links_clickable(book)
    assert "[Trang tựa](#title-page)" in out and "[Bản quyền](#copyright)" in out
    assert check_toc_links(book)[0] == []


def test_source_front_entry_links_in_italics():
    book = FRONT + BOOK.replace("# Mục lục\n", "# Mục lục\n\n<small>*Copyright*</small>\n", 1)
    assert "<small>[*Copyright*](#copyright)</small>" in make_toc_links_clickable(book)


def test_fill_title_page_fills_only_empty_block():
    out = fill_title_page(FRONT, "Người Người Nhất", "Brian Christian", "Phụ đề & thêm")
    assert '<p class="front-title">Người Người Nhất</p>' in out
    assert '<p class="front-sub">Phụ đề &amp; thêm</p>' in out
    assert '<p class="front-author">Brian Christian</p>' in out
    assert fill_title_page(out, "Khác") == out  # already filled → untouched


def test_fill_title_page_without_block_is_noop():
    assert fill_title_page(BOOK, "Tựa") == BOOK
