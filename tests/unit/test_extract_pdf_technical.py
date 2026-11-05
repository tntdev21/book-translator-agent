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


def test_hidden_single_page_text_layer_dropped(tmp_path, monkeypatch):
    """A one-page CM* text layer under the real Nimbus text is removed; real text stays."""
    real = "NimbusRomNo9L-Regu"
    pages = [[w("x" * 210, 50, 100, font=real)] for _ in range(3)]
    pages[1] += [w("h" * 210, 50, 300, font="AB+CMR12"), w("ghost", 50, 330, font="AB+CMTI12")]
    pages[1].append(w("keep", 50, 360, font="AB+StandardSym"))
    text = run(tmp_path, monkeypatch, pages)
    assert "hhhh" not in text and "ghost" not in text
    assert "keep" in text and text.count("x" * 210) == 3


def test_single_page_font_without_body_text_kept(tmp_path, monkeypatch):
    pages = [[w("y" * 210, 50, 100, font="AB+CMR12")]]
    assert "y" * 210 in run(tmp_path, monkeypatch, pages)


def test_extract_recombines_split_accents(tmp_path, monkeypatch):
    text = run(tmp_path, monkeypatch, [body() + [w("Go¨del", 50, 500)]])
    assert "Gödel" in text


def test_caption_at_page_top_does_not_split_paragraph(tmp_path, monkeypatch):
    # A figure at the top of page 2 sits between the two halves of a sentence in reading order.
    p1 = body() + [w("The", 50, 500), w("rule", 80, 500), w("(or", 110, 500)]
    p2 = ([w("Fig.", 50, 90), w("1.1:", 80, 90), w("Caption", 110, 90)]
          + [w("pixels)", 50, 130), w("relaxed.", 100, 130)]
          + [w("filler", 50, 160 + i * 12) for i in range(30)])
    text = run(tmp_path, monkeypatch, [p1, p2])
    assert "The rule (or\n<!-- Page 2 -->\npixels) relaxed." in text
    assert text.index("pixels) relaxed.") < text.index("Fig. 1.1: Caption")


def test_caption_at_page_top_before_new_paragraph_keeps_order(tmp_path, monkeypatch):
    p1 = body() + [w("Done.", 50, 500)]
    p2 = ([w("Fig.", 50, 90), w("1.1:", 80, 90), w("Caption", 110, 90)]
          + [w("Next", 60, 130), w("para.", 100, 130)]
          + [w("filler", 50, 160 + i * 12) for i in range(30)])
    text = run(tmp_path, monkeypatch, [p1, p2])
    assert text.index("Fig. 1.1: Caption") < text.index("Next para.")


def test_indented_list_item_body_stays_one_paragraph(tmp_path, monkeypatch):
    # Hanging-indent list item: wrapped lines share the item's indent and must not each
    # become their own paragraph; the next "b. " item still starts a new one.
    item = [w("a.", 70, 500), w("one", 90, 500), w("works", 120, 500), w("as", 160, 500), w("an", 180, 500)]
    cont = [w("attractor", 70, 512), w("and", 130, 512), w("repulsor.", 160, 512)]
    nxt = [w("b.", 70, 524), w("Next", 90, 524), w("step.", 130, 524)]
    text = run(tmp_path, monkeypatch, [body() + item + cont + nxt])
    assert "a. one works as an attractor and repulsor." in text
    assert "repulsor.\n\nb. Next step." in text


def test_serif_pseudocode_under_bold_label_becomes_indented_code(tmp_path, monkeypatch):
    # Pseudocode set in the body serif (not monospace): bold label, ragged lines on several
    # indent levels -> fenced block, 4 spaces per level; the following paragraph stays prose.
    label = [w("Room", 50, 400, MEDI), w("algorithm", 80, 400, MEDI)]
    rows = [(50, "N=0"), (50, "Scan"), (72, "If empty"), (81, "mark it"), (81, "N=N+1"),
            (72, "End If"), (50, "End Scan")]
    code = [w(t, x, 424 + k * 12) for k, (x, t) in enumerate(rows)]
    after = [w("Once", 62, 540), w("marked", 100, 540), w("x" * 40, 150, 540), w("as", 50, 552)]
    text = run(tmp_path, monkeypatch, [body(20, 100) + label + code + after])
    assert "**Room algorithm**\n\n```\nN=0\nScan\n    If empty\n        mark it\n        N=N+1\n" \
           "    End If\nEnd Scan\n```" in text
    assert "```\n\nOnce marked " in text
