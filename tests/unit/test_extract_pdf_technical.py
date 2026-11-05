"""Opt-in `layout: technical` extraction options (extract_pdf + pdf_technical_layout)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from utils import extract_pdf as extractor  # noqa: E402
from utils import pdf_technical_layout as tech  # noqa: E402

REG, ITAL, MEDI, MONO = "AB+Regular", "AB+Ital", "AB+Medi", "AB+Mon"


class Page:
    width, height = 400, 600

    def __init__(self, words):
        self.words = words

    def extract_words(self, x_tolerance=3, extra_attrs=None):
        return self.words


class Pdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def w(text, x0, base, font=REG, size=10.0):
    return {"text": text, "x0": x0, "x1": x0 + 6 * len(text), "top": base - size, "bottom": base,
            "fontname": font, "size": size}


def body(n=30, start=100):
    """Filler paragraph lines so the body font (10pt Regular) dominates."""
    return [w("filler", 50, start + i * 12) for i in range(n)]


def run(tmp_path, monkeypatch, pages, **options):
    monkeypatch.setattr(extractor.pdfplumber, "open", lambda _: Pdf([Page(p) for p in pages]))
    monkeypatch.setattr(extractor, "_source_fingerprint", lambda _: "x")
    out = tmp_path / "o.md"
    extractor.extract_pdf("a.pdf", str(out), **{"layout": "technical", **options})
    return out.read_text()


def test_unknown_option_and_layout_raise(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="Unknown extraction option"):
        run(tmp_path, monkeypatch, [[]], bogus=1)
    with pytest.raises(ValueError, match="layout"):
        run(tmp_path, monkeypatch, [[]], layout="fancy")


def test_baseline_grouping_keeps_italic_word_in_line_order(tmp_path, monkeypatch):
    # italic word has a ~1pt different top; round(top) grouping would split it
    italic = w("really", 80, 100.4, ITAL)
    italic["top"] -= 1
    text = run(tmp_path, monkeypatch, [[w("it", 50, 100), italic, w("works", 120, 100)] + body(start=200)])
    assert "it really works" in text


def test_headings_levels_and_chapter_label(tmp_path, monkeypatch):
    words = body() + [
        w("Chapter", 50, 40, MEDI, 20), w("1", 130, 40, MEDI, 20),
        w("Introduction", 50, 70, MEDI, 20),
        w("1.1", 50, 500, MEDI, 12), w("Games", 80, 500, MEDI, 12),
        w("1.1.2", 50, 540, MEDI, 11.6), w("Deep", 90, 540, MEDI, 11.6),
    ]
    text = run(tmp_path, monkeypatch, [words])
    assert "# 1. Introduction" in text
    assert "\n## 1.1 Games" in text
    assert "\n### 1.1.2 Deep" in text


def test_bullets_and_footnote_and_code(tmp_path, monkeypatch):
    words = body(15) + [
        w("•", 60, 300), w("first", 75, 300), w("item", 110, 300),
        w("•", 60, 312), w("second", 75, 312),
        w("a", 50, 340, MONO), w("=", 62, 340, MONO),
        w("if", 60, 352, MONO), w("x", 80, 352, MONO),
        w("7", 50, 490, REG, 5.5), w("Note", 58, 490, REG, 7), w("text", 90, 490, REG, 7),
    ]
    text = run(tmp_path, monkeypatch, [words])
    assert "- first item\n- second" in text
    assert "```\na =\n  if x\n```" in text
    assert '<aside class="footnote">7. Note text</aside>' in text


def test_running_header_dropped(tmp_path, monkeypatch):
    words = body() + [w("Running", 50, 30, REG, 8), w("title", 100, 30, REG, 8)]
    assert "Running" not in run(tmp_path, monkeypatch, [words])


def test_skip_fonts_drops_figure_text(tmp_path, monkeypatch):
    words = body() + [w("FIGTEXT", 50, 500, "AB+Helvetica")]
    assert "FIGTEXT" in run(tmp_path, monkeypatch, [words])
    assert "FIGTEXT" not in run(tmp_path, monkeypatch, [words], skip_fonts=["Helvetica"])


def test_hyphen_move_rules():
    comp = {"search-based"}
    assert tech.hyphen_move("a pro-", "cedural gen", comp) == ("a ", "procedural gen", "")
    assert tech.hyphen_move("a search-", "based x", comp)[:2] == ("a ", "search-based x")
    assert tech.hyphen_move("a state-of-", "the-art", comp)[:2] == ("a ", "state-of-the-art")
    assert tech.hyphen_move("a pro-", "Cedural", comp)[2] == ""  # uppercase keeps hyphen
    assert tech.hyphen_move("a pro-", "Cedural", comp)[1] == "pro-Cedural"
    assert tech.hyphen_move("plain end", "next", comp) == ("plain end", "next", " ")


def test_join_lines_dehyphenates():
    assert tech.join_lines(["gener-", "ation of maps"], set()) == "generation of maps"


def test_cross_page_hyphen_and_page_continuity(tmp_path, monkeypatch):
    p1 = body() + [w("The", 50, 500), w("pro-", 80, 500)]
    p2 = [w("cedural", 50, 100), w("end.", 100, 100)] + [w("filler", 50, 130 + i * 12) for i in range(30)]
    text = run(tmp_path, monkeypatch, [p1, p2])
    assert "The \n<!-- Page 2 -->\nprocedural end." in text  # word moved past the marker, never split


def test_multi_pdf_pages_are_continuous(tmp_path, monkeypatch):
    pdfs = {"a.pdf": [body(), body()], "b.pdf": [body()]}
    monkeypatch.setattr(extractor.pdfplumber, "open", lambda p: Pdf([Page(x) for x in pdfs[p]]))
    monkeypatch.setattr(extractor, "_source_fingerprint", lambda _: "x")
    out = tmp_path / "o.md"
    extractor.extract_pdf(["a.pdf", "b.pdf"], str(out), layout="technical")
    text = out.read_text()
    assert [f"<!-- Page {n} -->" in text for n in (1, 2, 3)] == [True] * 3
    assert "<!-- Page 4 -->" not in text


def test_max_pages_caps_total_across_pdfs(tmp_path, monkeypatch):
    pdfs = {"a.pdf": [body(), body()], "b.pdf": [body()]}
    monkeypatch.setattr(extractor.pdfplumber, "open", lambda p: Pdf([Page(x) for x in pdfs[p]]))
    monkeypatch.setattr(extractor, "_source_fingerprint", lambda _: "x")
    out = tmp_path / "o.md"
    extractor.extract_pdf(["a.pdf", "b.pdf"], str(out), max_pages=3, layout="technical")
    assert "<!-- Page 3 -->" in out.read_text()
    extractor.extract_pdf(["a.pdf", "b.pdf"], str(out), max_pages=2, layout="technical")
    assert "<!-- Page 3 -->" not in out.read_text()
