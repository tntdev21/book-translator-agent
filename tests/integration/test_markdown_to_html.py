#!/usr/bin/env python3
"""
Integration tests: Markdown to HTML conversion workflow.

Tests the interaction between markdown_converter functions to ensure
markdown content is properly converted to HTML with TOC links.
"""

import pytest
from scripts.utils.markdown_converter import (
    make_toc_links_clickable,
    markdown_to_html_with_dialogue,
)


def test_markdown_to_html_basic() -> None:
    """Convert chapter and section headings to semantic HTML."""
    markdown_content = """# CHƯƠNG 1

This is the first paragraph.

## A section heading

This is the second paragraph.

# CHƯƠNG 2

Content in chapter 2.
"""

    # Convert to HTML
    html_result = markdown_to_html_with_dialogue(markdown_content)

    # Verify HTML structure - function generates <div> + <h1> for chapters
    assert '<h1' in html_result
    assert 'CHƯƠNG 1' in html_result
    assert 'CHƯƠNG 2' in html_result
    assert '<p>' in html_result or '<p ' in html_result
    assert 'first paragraph' in html_result
    assert 'second paragraph' in html_result
    # Verify chapter and section headings have semantic markup and anchors.
    assert 'id="chuong-1"' in html_result
    assert 'id="chuong-2"' in html_result
    assert '<div id="a-section-heading" class="section-heading">' in html_result
    assert '<h2>A section heading</h2>' in html_result
    assert '<p>## A section heading</p>' not in html_result


def test_structured_footnote_reflows_as_semantic_note() -> None:
    html = markdown_to_html_with_dialogue(
        '<aside class="footnote">25 Citation text continues across original lines.</aside>'
    )

    assert '<aside class="footnote"><p>25 Citation text continues across original lines.</p></aside>' in html
    assert 'preserve-break' not in html


def test_page_markers_preserve_structural_paragraph_boundaries() -> None:
    content = """First paragraph.\n\n<!-- Page 2 -->\n\nSecond paragraph.\n\nThird page continues\n<!-- Page 3 -->\nwith this sentence."""

    html = markdown_to_html_with_dialogue(content)

    assert "<!-- Page" not in html
    assert "<p>First paragraph.</p>" in html
    assert "<p>Second paragraph.</p>" in html
    assert "<p>Third page continues with this sentence.</p>" in html


def test_markdown_to_html_with_toc_links() -> None:
    """Test markdown to HTML conversion with clickable TOC links.

    Integration flow:
    1. Create content with TOC section (book format)
    2. Convert TOC entries to links
    3. Convert to HTML
    4. Verify TOC links become anchor tags in HTML

    Note: TOC conversion happens before HTML conversion, so all "CHƯƠNG X"
    instances become links. The actual chapter headings need to be in content
    BEFORE TOC conversion, or use different format.
    """
    # Use book format with headings that won't be converted by TOC
    # The TOC lists chapters, and headings appear as CHƯƠNG (which gets ID)
    markdown_content = """TABLE OF CONTENTS
Chương 1
Chương 2


CHƯƠNG 1

This is chapter 1 content.

CHƯƠNG 2

This is chapter 2 content.
"""

    # First, make TOC clickable
    content_with_toc = make_toc_links_clickable(markdown_content)

    # Verify markdown links were created in TOC section
    assert '[Chương 1](#chuong-1)' in content_with_toc
    assert '[Chương 2](#chuong-2)' in content_with_toc

    # Convert to HTML
    html_result = markdown_to_html_with_dialogue(content_with_toc)

    # Verify HTML has TOC anchor tags
    assert 'href="#chuong-1"' in html_result
    assert 'href="#chuong-2"' in html_result

    # The CHƯƠNG headings also get converted to links by TOC function
    # This is expected behavior - TOC scans entire document
    # Verify content is present
    assert 'chapter 1 content' in html_result
    assert 'chapter 2 content' in html_result

    # Verify TOC structure exists
    assert 'toc-link' in html_result or 'toc-entry' in html_result


def test_markdown_to_html_vietnamese() -> None:
    """Test markdown to HTML conversion preserves Vietnamese text.

    Integration flow:
    1. Create markdown with Vietnamese content and TOC
    2. Convert TOC to clickable links
    3. Convert to HTML
    4. Verify Vietnamese text is preserved correctly
    """
    markdown_content = """MỤC LỤC
Lời cống hiến
Đề từ
Chương 1


# Lời cống hiến

Dành tặng cho biên tập viên và người bạn thân nhất của tôi.

# Đề từ

Ngày khoa học bắt đầu nghiên cứu những hiện tượng phi vật chất, nó sẽ đạt được nhiều tiến bộ trong thế kỷ tới.

— Nikola Tesla, 1901

# CHƯƠNG 1

Nhà nghiên cứu Katherine Solomon sống trong một thế giới của những bí ẩn cổ xưa.
"""

    # Make TOC clickable
    content_with_toc = make_toc_links_clickable(markdown_content)

    # Convert to HTML
    html_result = markdown_to_html_with_dialogue(content_with_toc)

    # Verify Vietnamese text is preserved in HTML
    assert 'Lời cống hiến' in html_result
    assert 'Đề từ' in html_result
    assert 'Chương 1' in html_result or 'CHƯƠNG 1' in html_result
    assert 'Dành tặng cho biên tập viên' in html_result
    assert 'Ngày khoa học bắt đầu nghiên cứu' in html_result
    assert 'Nikola Tesla' in html_result
    assert 'Katherine Solomon' in html_result

    # Verify HTML structure exists
    assert '<h1' in html_result or '<h2' in html_result
    assert '<p>' in html_result or '<p ' in html_result

    # Verify Vietnamese characters are properly encoded
    assert 'ế' in html_result or '&#' in html_result  # Vietnamese tone marks
    assert 'ữ' in html_result or '&#' in html_result
    assert 'ộ' in html_result or '&#' in html_result
