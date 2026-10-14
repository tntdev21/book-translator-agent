"""Tests for typography-aware PDF extraction."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from utils import extract_pdf as extractor  # noqa: E402


class FakePage:
    width = 600

    def __init__(self, words):
        self.words = words

    def extract_words(self, extra_attrs):
        assert extra_attrs == ["fontname", "size"]
        return self.words


class FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _word(text, x0, top, font="Book", size=14.4):
    return {"text": text, "x0": x0, "x1": x0 + len(text) * 7, "top": top, "fontname": font, "size": size}


KNOWN_SOURCE = "32f0117b598fa18ab343f099129214e624239301f3c6970ff3ade8c14a659ea2"


def _extract(tmp_path, monkeypatch, pages, fingerprint=KNOWN_SOURCE):
    monkeypatch.setattr(extractor.pdfplumber, "open", lambda _: FakePdf([FakePage(page) for page in pages]))
    monkeypatch.setattr(extractor, "_source_fingerprint", lambda _: fingerprint)
    output = tmp_path / "structured.md"
    extractor.extract_pdf("input.pdf", str(output))
    return output.read_text(encoding="utf-8")


def test_extract_pdf_preserves_structure_and_repairs_cids(tmp_path, monkeypatch):
    words = [
        _word("1.", 260, 50, "Book-Bold", 16.6), _word("Introduction", 280, 50, "Book-Bold", 16.6),
        _word("First", 50, 100), _word("line", 90, 100), _word("continues", 50, 118), _word("here.", 120, 118),
        _word("A", 180, 145, "Book", 10.8), _word("footnote", 195, 145, "Book", 10.8),
        _word("Second", 70, 150), _word("arti(cid:999)cial", 130, 150), _word("paragraph.", 250, 150),
        _word("Section", 260, 190, "Book-BoldItalic"), _word("title", 320, 190, "Book-BoldItalic"),
        _word("After", 50, 220), _word("section.", 90, 220),
    ]
    text = _extract(tmp_path, monkeypatch, [words])
    assert "# 1. Introduction" in text
    assert "Second artificial paragraph." in text
    assert "<small>A footnote</small>" in text
    assert "## Section title" in text


def test_cid_repairs_apply_only_to_validated_source(tmp_path, monkeypatch):
    text = _extract(tmp_path, monkeypatch, [[_word("arti(cid:999)cial", 50, 100)]])
    assert "artificial" in text


def test_cid_repairs_preserve_unknown_codes(tmp_path, monkeypatch, capsys):
    words = [
        _word("fi(cid:999)", 50, 100), _word("fl(cid:1001)", 110, 100),
        _word("ffi(cid:1003)", 180, 100), _word("ffl(cid:1006)", 260, 100),
        _word("ff(cid:1009)", 340, 100), _word("unknown(cid:42)", 400, 100),
    ]
    text = _extract(tmp_path, monkeypatch, [words])
    assert "fifi flfl ffiffi fflffl ffff unknown(cid:42)" in text
    assert "Warning: preserved unrecognized CID glyphs: 42" in capsys.readouterr().out


def test_cid_number_is_preserved_for_different_source(tmp_path, monkeypatch, capsys):
    text = _extract(
        tmp_path, monkeypatch, [[_word("not-a-ligature(cid:999)", 50, 100)]], fingerprint="other-source"
    )
    assert "not-a-ligature(cid:999)" in text
    assert "Warning: preserved unrecognized CID glyphs: 999" in capsys.readouterr().out


def test_inline_numeric_reference_glyphs_are_not_citations():
    lines = [
        {"text": "crowd-", "x0": 50, "x1": 100, "size": 14.4, "font": "book"},
        {"text": "1 2", "x0": 187, "x1": 205, "size": 10.8, "font": "book"},
        {"text": "control", "x0": 105, "x1": 150, "size": 14.4, "font": "book"},
        {"text": "5 6", "x0": 117, "x1": 135, "size": 10.8, "font": "book"},
    ]
    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)
    assert not any('class="footnote"' in block for block in blocks)
    assert '<small>1 2</small>' in blocks
    assert '<small>5 6</small>' in blocks


def test_margin_aligned_numeric_folio_without_continuation_is_not_citation():
    lines = [
        {"text": "12", "x0": 50, "x1": 62, "top": 740, "bottom": 751, "size": 10.8, "font": "book"},
    ]

    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)

    assert blocks == ["<small>12</small>"]


def test_numeric_display_after_valid_note_is_not_a_citation():
    lines = [
        {"text": "A body line before the notes.", "x0": 50, "x1": 220, "top": 60, "bottom": 75, "size": 14.4, "font": "book"},
        {"text": "1 A valid citation.", "x0": 50, "x1": 150, "top": 500, "bottom": 511, "size": 10.8, "font": "book"},
        {"text": "Its hanging continuation.", "x0": 61, "x1": 190, "top": 522, "bottom": 533, "size": 10.8, "font": "book"},
        {"text": "2 A numeric display line.", "x0": 50, "x1": 185, "top": 544, "bottom": 555, "size": 10.8, "font": "book"},
        {"text": "A body line after the notes.", "x0": 50, "x1": 220, "top": 600, "bottom": 615, "size": 14.4, "font": "book"},
    ]

    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)

    assert '<aside class="footnote">1 A valid citation. Its hanging continuation.</aside>' in blocks
    assert "<small>2 A numeric display line.</small>" in blocks


def test_dense_note_page_promotes_single_line_citations():
    lines = [
        {"text": "20 First source.", "x0": 50, "x1": 150, "top": 100, "bottom": 111, "size": 10.8, "font": "book"},
        {"text": "21 Second source.", "x0": 50, "x1": 160, "top": 122, "bottom": 133, "size": 10.8, "font": "book"},
        {"text": "22 Third source.", "x0": 50, "x1": 160, "top": 144, "bottom": 155, "size": 10.8, "font": "book"},
    ]

    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)

    assert blocks == [
        '<aside class="footnote">20 First source.</aside>',
        '<aside class="footnote">21 Second source.</aside>',
        '<aside class="footnote">22 Third source.</aside>',
    ]


def test_sparse_body_page_keeps_numbered_display_lines_as_small():
    lines = [
        {"text": "A body line before the notes.", "x0": 50, "x1": 220, "top": 60, "bottom": 75, "size": 14.4, "font": "book"},
        {"text": "1. First numbered display line", "x0": 50, "x1": 220, "top": 500, "bottom": 511, "size": 10.8, "font": "book"},
        {"text": "2. Second numbered display line", "x0": 50, "x1": 230, "top": 522, "bottom": 533, "size": 10.8, "font": "book"},
        {"text": "A body line after the notes.", "x0": 50, "x1": 220, "top": 600, "bottom": 615, "size": 14.4, "font": "book"},
    ]

    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)

    assert "<small>1. First numbered display line</small>" in blocks
    assert "<small>2. Second numbered display line</small>" in blocks
    assert not any('class="footnote"' in block for block in blocks)


def test_citation_continuation_requires_matching_indent_and_vertical_adjacency():
    lines = [
        {"text": "1 A citation starts.", "x0": 50, "x1": 150, "top": 100, "bottom": 111, "size": 10.8, "font": "book"},
        {"text": "Wrong indent must stay separate.", "x0": 95, "x1": 250, "top": 120, "bottom": 131, "size": 10.8, "font": "book"},
        {"text": "2 A second citation starts.", "x0": 50, "x1": 170, "top": 200, "bottom": 211, "size": 10.8, "font": "book"},
        {"text": "A delayed continuation stays separate.", "x0": 61, "x1": 250, "top": 240, "bottom": 251, "size": 10.8, "font": "book"},
    ]

    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)

    assert not any('class="footnote"' in block for block in blocks)
    assert "<small>1 A citation starts.</small>" in blocks
    assert "<small>Wrong indent must stay separate.</small>" in blocks


def test_multiline_citation_reflows_but_display_lines_remain_separate(tmp_path, monkeypatch):
    words = [
        _word("This", 50, 50), _word("body", 85, 50), _word("line", 120, 50), _word("establishes", 155, 50),
        _word("the", 235, 50), _word("larger", 265, 50), _word("document", 315, 50), _word("body", 380, 50), _word("font", 420, 50), _word("size.", 455, 50),
        _word("1", 50, 100, size=10.8), _word("A", 65, 100, size=10.8), _word("three-line", 80, 100, size=10.8),
        _word("citation", 145, 100, size=10.8), _word("starts.", 205, 100, size=10.8),
        _word("It", 61, 120, size=10.8), _word("continues", 76, 120, size=10.8),
        _word("on", 145, 120, size=10.8), _word("the", 165, 120, size=10.8), _word("next", 190, 120, size=10.8), _word("line.", 225, 120, size=10.8),
        _word("Then", 61, 140, size=10.8), _word("ends.", 96, 140, size=10.8),
        _word("a", 50, 180, size=10.8), _word("display", 65, 180, size=10.8), _word("line", 115, 180, size=10.8),
        _word("another", 50, 200, size=10.8), _word("display", 105, 200, size=10.8), _word("line", 155, 200, size=10.8),
    ]
    lines = extractor._line_groups(words, {}, set())
    blocks, _ = extractor._page_blocks(lines, 14.4, 50, 10, 600)
    text = "\n".join(blocks)
    assert '<aside class="footnote">1 A three-line citation starts. It continues on the next line. Then ends.</aside>' in text
    assert '<small>a display line</small>' in text
    assert '<small>another display line</small>' in text


def test_citation_continues_across_page_marker(tmp_path, monkeypatch):
    page_one = [
        *[_word(f"body{index}", 50 + index * 30, 50) for index in range(10)],
        _word("1", 50, 100, size=10.8), _word("Citation", 65, 100, size=10.8),
        _word("continues", 61, 120, size=10.8),
    ]
    page_two = [
        _word("here.", 61, 100, size=10.8),
        _word("Still", 61, 120, size=10.8), _word("continues.", 95, 120, size=10.8),
        _word("2", 50, 145, size=10.8), _word("Next", 65, 145, size=10.8),
        _word("citation.", 95, 145, size=10.8),
    ]

    text = _extract(tmp_path, monkeypatch, [page_one, page_two])

    assert '<aside class="footnote">1 Citation continues <!-- Page 2 --> here. Still continues.</aside>' in text
    assert '<small>2 Next citation.</small>' in text


def test_multiline_chapter_heading_is_coalesced(tmp_path, monkeypatch):
    words = [
        _word("1.", 260, 50, "Book-Bold", 16.6), _word("A", 280, 50, "Book-Bold", 16.6),
        _word("Long", 250, 70, "Book-Bold", 16.6), _word("Chapter", 290, 70, "Book-Bold", 16.6),
        _word("This", 50, 110), _word("ordinary", 85, 110), _word("body", 145, 110),
        _word("text", 180, 110), _word("establishes", 220, 110), _word("the", 300, 110),
        _word("document", 330, 110), _word("body", 400, 110), _word("size.", 440, 110),
    ]
    text = _extract(tmp_path, monkeypatch, [words])
    assert "# 1. A Long Chapter" in text
    assert text.count("# ") == 1


def test_page_start_indentation_preserves_paragraph_boundary(tmp_path, monkeypatch):
    page_one = [_word("First", 50, 100), _word("page.", 100, 100)]
    page_two = [_word("New", 70, 100), _word("paragraph.", 110, 100)]
    text = _extract(tmp_path, monkeypatch, [page_one, page_two])
    assert "First page.\n\n<!-- Page 2 -->\n\nNew paragraph." in text


def test_page_start_continuation_stays_with_previous_paragraph(tmp_path, monkeypatch):
    page_one = [_word("First", 50, 100), _word("page", 100, 100)]
    page_two = [_word("continues.", 50, 100)]
    text = _extract(tmp_path, monkeypatch, [page_one, page_two])
    assert "First page\n<!-- Page 2 -->\ncontinues." in text


def test_multi_column_page_fails_before_interleaving(tmp_path, monkeypatch):
    words = []
    for top in (100, 120, 140):
        words.extend([_word("left", 50, top), _word("right", 400, top)])
    with pytest.raises(ValueError, match="multi-column layout"):
        _extract(tmp_path, monkeypatch, [words])


def test_staggered_multi_column_page_fails_before_interleaving(tmp_path, monkeypatch):
    words = []
    for left_top, right_top in ((100, 101), (120, 121), (140, 141)):
        words.extend([_word("left", 50, left_top), _word("right", 400, right_top)])
    with pytest.raises(ValueError, match="multi-column layout"):
        _extract(tmp_path, monkeypatch, [words])


def test_extract_pdf_emits_marker_for_empty_page(tmp_path, monkeypatch):
    assert _extract(tmp_path, monkeypatch, [[]]) == "<!-- Page 1 -->\n"


def _sc(text, x0, top, size=8.64):
    """Small-caps word sharing a 14.4pt body baseline (lower `top`, same `bottom`)."""
    return dict(_word(text, x0, top, size=size), bottom=top + 8.64)


def test_inline_small_caps_stay_in_their_sentence():
    # Real geometry (p.9): body top 256.88/bottom 271.28, small caps top 260.11/bottom 268.75.
    words = [
        dict(_word("my", 50, 256.88), bottom=271.28), dict(_word("way—", 75, 256.88), bottom=271.28),
        _sc("LET", 103, 260.11), _sc("AGREED,", 125, 260.11),
        dict(_word("one", 180, 256.88), bottom=271.28), dict(_word("says,", 210, 256.88), bottom=271.28),
    ]
    lines = extractor._line_groups(words, {}, set())
    assert len(lines) == 1
    assert lines[0]["text"] == 'my way—<span class="sc">LET AGREED,</span> one says,'
    assert lines[0]["size"] == 14.4


def test_short_speaker_turn_sizes_as_body_text():
    words = [_sc("WILLIAMSON", 64, 683), dict(_word(": It", 140, 680), bottom=694.4)]
    lines = extractor._line_groups(words, {}, set())
    assert len(lines) == 1 and lines[0]["size"] == 14.4


def test_small_line_a_full_line_away_is_not_folded():
    words = [_word("Caption", 50, 100, size=10.8), _word("Body", 50, 112)]
    assert len(extractor._line_groups(words, {}, set())) == 2


def test_small_caps_beside_a_bare_dash_stays_a_display_line():
    words = [dict(_word("–", 300, 98), bottom=112.4), _sc("DAVID", 310, 101.4), _sc("WALLACE", 360, 101.4)]
    lines = extractor._line_groups(words, {}, set())
    assert len(lines) == 2 and 'class="sc"' not in "".join(line["text"] for line in lines)


def test_hanging_indent_speaker_turn_keeps_wrapped_lines(tmp_path, monkeypatch):
    def body(text, x0, top):
        return [dict(_word(w, x0 + i * 60, top), bottom=top + 14.4) for i, w in enumerate(text.split())]

    words = (
        body("Narrative at the margin.", 50, 100) + body("more narrative here ok.", 50, 117)
        + [_sc("JUDGE", 57, 137)] + body(": What do you think of", 90, 134)
        + body("these plays", 71, 151)
        + [_sc("REMOTE", 57, 171)] + body(": That is general; I will just", 90, 168)
        + body("say I like them.", 71, 185)
        + body("Narrative resumes here.", 50, 202)
        + [_sc("JUDGE", 57, 222)] + body(": (I am from Montreal)", 90, 219)
        + body("An indented new paragraph.", 64, 236)
    )
    text = _extract(tmp_path, monkeypatch, [words])
    assert '<span class="sc">JUDGE</span>: What do you think of these plays\n\n' in text
    assert '<span class="sc">REMOTE</span>: That is general; I will just say I like them.\n\nNarrative resumes here.' in text
    # A normal paragraph indent (< an em right of the label) is new narrative.
    assert '(I am from Montreal)\n\nAn indented new paragraph.' in text
