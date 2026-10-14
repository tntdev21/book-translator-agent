#!/usr/bin/env python3
"""Tests for scripts/utils/fonts.py — folder-per-family font resolution."""

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from utils import fonts  # noqa: E402


def _family(root: Path, name: str, variants=("Regular", "Bold", "Italic", "BoldItalic"), ext=".ttf"):
    folder = root / name
    folder.mkdir(parents=True)
    for v in variants:
        (folder / f"{v}{ext}").write_bytes(b"\0font")
    return folder


def test_resolve_all_four_variants_in_order(tmp_path):
    _family(tmp_path, "Serif")
    fam = fonts.resolve_font("Serif", tmp_path)
    assert fam.name == "Serif"
    assert [f.variant for f in fam.files] == ["Regular", "Bold", "Italic", "BoldItalic"]
    assert [(f.weight, f.style) for f in fam.files][3] == ("bold", "italic")


def test_missing_optional_variant_is_skipped(tmp_path):
    _family(tmp_path, "Serif", variants=("Regular", "Bold"))
    assert [f.variant for f in fonts.resolve_font("Serif", tmp_path).files] == ["Regular", "Bold"]


def test_otf_accepted(tmp_path):
    _family(tmp_path, "Serif", variants=("Regular",), ext=".otf")
    f = fonts.resolve_font("Serif", tmp_path).files[0]
    assert f.media_type == "font/otf"


def test_missing_regular_raises_with_available_list(tmp_path):
    _family(tmp_path, "Good")
    _family(tmp_path, "NoRegular", variants=("Bold",))
    with pytest.raises(fonts.FontNotFoundError, match=r"available: Good\)"):
        fonts.resolve_font("NoRegular", tmp_path)
    with pytest.raises(fonts.FontNotFoundError):
        fonts.resolve_font("Typo", tmp_path)


def test_default_name_used_when_empty(tmp_path):
    _family(tmp_path, fonts.DEFAULT_FONT)
    assert fonts.resolve_font("", tmp_path).name == fonts.DEFAULT_FONT


def test_font_face_css_and_stack(tmp_path):
    _family(tmp_path, "Serif", variants=("Regular", "Italic"))
    fam = fonts.resolve_font("Serif", tmp_path)
    css = fam.font_face_css(lambda f: f"x/{f.variant}")
    assert css.count("@font-face") == 2
    assert "src: url('x/Italic')" in css and "font-style: italic" in css
    assert fam.css_stack == "'Serif', Georgia, serif"


def test_repo_default_font_is_shipped():
    """The bundled default must resolve with all four variants and its licence."""
    fam = fonts.resolve_font()
    assert len(fam.files) == 4
    assert (fonts.FONTS_DIR / fonts.DEFAULT_FONT / "OFL.txt").exists()


def test_epub_embeds_family_folder_and_css_points_to_it(tmp_path):
    from ebooklib import epub
    from utils import export_epub

    _family(tmp_path, "Serif")
    book = export_epub.create_epub("<h1>Chương 1</h1><p>Xin chào</p>", title="T",
                                   font="Serif", fonts_dir=tmp_path)
    out = tmp_path / "t.epub"
    epub.write_epub(str(out), book, {})
    names = zipfile.ZipFile(out).namelist()
    assert "EPUB/fonts/Serif/Bold.ttf" in names
    css = zipfile.ZipFile(out).read("EPUB/style/style.css").decode()
    assert "url('../fonts/Serif/Regular.ttf')" in css
    assert "font-family: 'Serif', Georgia, serif" in css


def test_html_embeds_data_uri(tmp_path):
    from utils import export_html

    _family(tmp_path, "Serif", variants=("Regular",))
    html = export_html.create_html("<p>x</p>", font="Serif", fonts_dir=tmp_path)
    assert "data:font/ttf;base64," in html
    assert "font-family: 'Serif', Georgia, serif" in html
