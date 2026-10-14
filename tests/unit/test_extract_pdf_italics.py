"""Tests for italic-run marking and font-change word gluing in PDF extraction."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from utils import extract_pdf as extractor  # noqa: E402

ROMAN, ITALIC, BOLD_ITALIC = "AAAAAA+CharisSIL", "AAAAAB+CharisSIL-Italic", "AAAAAC+CharisSIL-BoldItalic"


def _words(*specs, top=100, size=14.4, start=50):
    """Build a line from (text, font, glued_to_previous) specs."""
    words, x = [], start
    for text, font, glued in specs:
        if words:
            x = words[-1]["x1"] + (0.3 if glued else 4.5)
        words.append({"text": text, "x0": x, "x1": x + len(text) * 7, "top": top,
                      "bottom": top + size, "fontname": font, "size": size})
    return words


def _text(words, cid_repairs=None):
    return extractor._line_groups(words, cid_repairs or {}, set())[0]["text"]


def test_emphasis_shift_is_preserved():
    words = _words(("talking", ROMAN, False), ("with", ROMAN, False), ("a", ROMAN, False),
                   ("human", ITALIC, False), ("as", ROMAN, False), ("with", ROMAN, False),
                   ("a", ITALIC, False), ("human", ROMAN, False))
    assert _text(words) == "talking with a *human* as with *a* human"


def test_glued_roman_punctuation_stays_outside_without_space():
    words = _words(("a", ROMAN, False), ("human", ITALIC, False), (".", ROMAN, True),
                   ("Users", ROMAN, False), ("are", ITALIC, False), (",", ROMAN, True))
    assert _text(words) == "a *human*. Users *are*,"


def test_mixed_font_word_fragments_are_not_spaced():
    words = _words(("Terminator", ITALIC, False), ("’s", ROMAN, True), ("un", ITALIC, False),
                   ("-creative", ROMAN, True), ("[", ROMAN, False), ("sic", ITALIC, True), ("]", ROMAN, True))
    assert _text(words) == "*Terminator*’s *un*-creative [*sic*]"


def test_multi_word_run_and_inner_punctuation_outside_marks():
    words = _words(("in", ROMAN, False), ("“The", ITALIC, False), ("Singularity", ITALIC, False),
                   ("Is", ITALIC, False), ("Near,”", ITALIC, False), ("he", ROMAN, False))
    assert _text(words) == "in “*The Singularity Is Near*,” he"


def test_bold_italic_heading_is_not_marked_and_keeps_font():
    words = _words(("One", BOLD_ITALIC, False), ("Self", BOLD_ITALIC, False))
    line = extractor._line_groups(words, {}, set())[0]
    assert line["text"] == "One Self"
    assert "bolditalic" in line["font"]


def test_punctuation_only_and_literal_asterisk_runs_are_left_bare():
    words = _words(("word", ROMAN, False), ("—", ITALIC, True), ("then", ROMAN, True),
                   ("*sigh*", ITALIC, False))
    assert _text(words) == "word—then *sigh*"


def test_superscript_marker_stays_outside_emphasis():
    words = _words(("a", ROMAN, False), ("mathematician", ITALIC, False), (".", ROMAN, True))
    marker = {"text": "3", "x0": words[1]["x1"] + 0.1, "x1": words[1]["x1"] + 5, "top": 97,
              "bottom": 106, "fontname": ITALIC, "size": 8.6}
    words[2]["x0"] += 5.2
    words[2]["x1"] += 5.2
    assert _text([*words, marker]) == "a *mathematician*<small>3</small>."


def test_cid_repair_happens_before_marking():
    words = _words(("(cid:999)ction", ITALIC, False))
    assert _text(words, {"999": "fi"}) == "*fiction*"


def test_italic_run_split_by_line_break_is_rejoined():
    assert extractor._join_lines(["the *quickest loss*", "*of his career*. Then"]) == \
        "the *quickest loss of his career*. Then"
    assert extractor._join_lines(["*a* and", "*b*"]) == "*a* and *b*"
