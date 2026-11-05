"""Chapter heading mapping + figure injection (export-time, opt-in)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from utils.export_enhance import apply_chapter_headings, inject_figures  # noqa: E402
from utils.markdown_converter import make_toc_links_clickable, markdown_to_html_with_dialogue  # noqa: E402

H = {"chapter_format": "Chương {n}: {title}", "appendix_format": "Phụ lục {n}: {title}"}

DOC = """# Mục lục

Lời nói đầu

1. Giới thiệu

2. Tiếp cận

A. Phỏng vấn các nhà thiết kế trò chơi

# Lời nói đầu

Text.

# 1. Giới thiệu

## 1.1 Mục

# 2. Tiếp cận

# A. Phỏng vấn các nhà thiết kế trò chơi
"""


def test_headings_noop_without_config():
    assert apply_chapter_headings(DOC, {}) == DOC
    assert apply_chapter_headings(DOC, None) == DOC


def test_headings_mapped_in_toc_and_body_not_sections():
    out = apply_chapter_headings(DOC, H)
    assert "# Chương 1: Giới thiệu" in out
    assert "# Phụ lục A: Phỏng vấn các nhà thiết kế trò chơi" in out
    assert "\nChương 2: Tiếp cận\n" in out
    assert "\nPhụ lục A: Phỏng vấn các nhà thiết kế trò chơi\n" in out
    assert "## 1.1 Mục" in out
    assert "# Lời nói đầu" in out


def test_toc_links_resolve_after_mapping():
    md = make_toc_links_clickable(apply_chapter_headings(DOC, H))
    assert "[Chương 2: Tiếp cận](#chuong-2-tiep-can)" in md
    assert "[Phụ lục A: Phỏng vấn các nhà thiết kế trò chơi](#phu-luc-a-phong-van-cac-nha-thiet-ke-tro-choi)" in md


def test_long_toc_entry_naming_a_heading_stays_in_toc():
    md = make_toc_links_clickable(
        "# Mục lục\n\nLời kết: Niềm vui là điều quan trọng, thưa ông\n\nLời bạt: Mười năm sau\n\n"
        "# Lời kết: Niềm vui là điều quan trọng, thưa ông\n\nBody.\n\n# Lời bạt: Mười năm sau\n")
    assert "[Lời kết: Niềm vui là điều quan trọng, thưa ông](#" in md
    assert "[Lời bạt: Mười năm sau](#" in md


def test_inject_figures(tmp_path):
    (tmp_path / "fig-2-1.png").write_bytes(b"x")
    md = "Intro.\nHình 2.1: Cap\n\n**Hình 2.2: Missing**\n\nHình 2.1: again"
    warns = []
    out, used = inject_figures(md, tmp_path, "relative", warn=warns.append)
    assert used == ["fig-2-1.png"]
    assert out.count("![Hình 2.1](images/fig-2-1.png)") == 1
    assert out.index("![Hình 2.1]") < out.index("Hình 2.1: Cap")
    assert len(warns) == 1 and "2.2" in warns[0]
    html = markdown_to_html_with_dialogue(out)
    assert '<figure class="figure-image"><img src="images/fig-2-1.png"' in html
    assert "<p>![" not in html


def test_inject_figures_file_mode_and_absent_dir(tmp_path):
    (tmp_path / "fig-1-1.png").write_bytes(b"x")
    out, _ = inject_figures("Hình 1.1: c", tmp_path, "file")
    assert f"file://{tmp_path.resolve()}/fig-1-1.png" in out
    same, used = inject_figures("Hình 1.1: c", tmp_path / "nope")
    assert same == "Hình 1.1: c" and used == []


def test_figure_marker_replaced_and_missing_dropped(tmp_path):
    (tmp_path / "table-7-1.png").write_bytes(b"x")
    (tmp_path / "figures.json").write_text(
        '[{"id": "table-7-1", "file": "table-7-1.png", "bbox": [0, 0, 100, 50]}]')
    md = 'Before.\n<!-- figure id="table-7-1" -->\nAfter.\n<!-- figure id="eq-9-9" -->\nEnd.'
    warns = []
    out, used = inject_figures(md, tmp_path, "relative", warn=warns.append)
    assert used == ["table-7-1.png"]
    assert "![](images/table-7-1.png){width=140pt}" in out
    assert "<!-- figure" not in out and "eq-9-9" not in out.replace(warns[0], "")
    assert len(warns) == 1 and "eq-9-9" in warns[0]
    html = markdown_to_html_with_dialogue(out)
    assert '<figure class="figure-image"><img src="images/table-7-1.png" alt="" style="width:140pt"/>' in html
    assert "figcaption" not in html and "<p>![" not in html and "figure id" not in html


def test_figure_marker_without_images_dir_is_dropped():
    warns = []
    out, used = inject_figures('A\n<!-- figure id="x" -->\nB', None, warn=warns.append)
    assert out == "A\nB" and used == [] and len(warns) == 1


def test_subfigure_labels_dropped_before_injected_caption(tmp_path):
    (tmp_path / "fig-3-1.png").write_bytes(b"x")
    md = ("Body paragraph.\n\n(b) Quadtree\n\n<!-- Page 5 -->\n\n(a) Ảnh và phép phân hoạch\n\n"
          "Hình 3.1: Cap\n\n(a) not a label\n\nHình 3.2: Other")
    out, used = inject_figures(md, tmp_path, "relative", warn=lambda m: None)
    assert used == ["fig-3-1.png"]
    assert "(b) Quadtree" not in out and "(a) Ảnh" not in out
    assert "Body paragraph." in out and "<!-- Page 5 -->" in out
    assert out.index("![Hình 3.1]") < out.index("Hình 3.1: Cap")
    # label-like line after the caption / before a caption without image is kept
    assert "(a) not a label" in out


def test_subfigure_labels_kept_when_caption_has_no_image(tmp_path):
    (tmp_path / "other.png").write_bytes(b"x")
    md = "Body.\n\n(a) Left (b) Right\n\nHình 3.5: Cap"
    out, used = inject_figures(md, tmp_path, "relative", warn=lambda m: None)
    assert used == [] and "(a) Left (b) Right" in out


def test_subfigure_label_drop_stops_at_body_text(tmp_path):
    (tmp_path / "fig-3-1.png").write_bytes(b"x")
    md = "(a) first list item of the body\n\nBody text line.\n(a) Label\nHình 3.1: Cap"
    out, _ = inject_figures(md, tmp_path, "relative", warn=lambda m: None)
    assert "(a) first list item of the body" in out and "Body text line." in out
    assert "(a) Label" not in out


def test_body_reference_is_not_a_caption(tmp_path):
    # "Hình 7.9 cho thấy..." in body text must not pull the image away from its real caption.
    (tmp_path / "fig-7-9.png").write_bytes(b"x")
    md = "Hình 7.9 cho thấy một ví dụ.\n\n## 7.6.2 Mục\n\nHình 7.9: Ví dụ thế giới trò chơi."
    out, used = inject_figures(md, tmp_path, "relative", warn=lambda _: None)
    assert used == ["fig-7-9.png"]
    assert out.index("## 7.6.2") < out.index("![Hình 7.9]") < out.index("Hình 7.9: Ví dụ")


def test_caption_splitting_sentence_warns_but_is_not_patched(tmp_path):
    # Export never rewrites text: the split is repaired in the data by reflow_captions.py.
    (tmp_path / "fig-7-9.png").write_bytes(b"x")
    md = ("Hành vi diễn một sự kiện như\n\n<!-- Page 139 -->\n\n"
          "Hình 7.9: Ví dụ.\n\nmột người quản lý sân khấu.\n\n## 7.7 Bài")
    warns = []
    out, _ = inject_figures(md, tmp_path, "relative", warn=warns.append)
    assert any("F7.9" in w and "reflow_captions" in w for w in warns)
    assert out.index("![Hình 7.9]") < out.index("một người quản lý")


def test_caption_after_complete_sentence_untouched(tmp_path):
    (tmp_path / "fig-1-1.png").write_bytes(b"x")
    md = "Câu hoàn chỉnh.\n\nHình 1.1: Cap\n\nđoạn mới viết thường."
    out, _ = inject_figures(md, tmp_path, "relative", warn=lambda _: None)
    assert out.index("Hình 1.1: Cap") < out.index("đoạn mới")


def test_figure_and_table_captions_get_caption_class():
    html = markdown_to_html_with_dialogue("Hình 7.9: Ví dụ.\n\nBảng 7.1: Kế hoạch\n\nHình 7.9 cho thấy một ví dụ.")
    assert '<p class="caption">Hình 7.9: Ví dụ.</p>' in html
    assert '<p class="caption">Bảng 7.1: Kế hoạch</p>' in html
    assert 'class="caption">Hình 7.9 cho thấy' not in html



def test_quote_lines_render_as_caption_paragraphs():
    html = markdown_to_html_with_dialogue("> Vui thật.\n> NYAAH!\n\nĐoạn văn thường.")
    assert '<p class="caption">Vui thật.</p>' in html and '<p class="caption">NYAAH!</p>' in html
    assert "&gt;" not in html and "> Vui" not in html

def test_double_asterisk_renders_strong_not_literal():
    html = markdown_to_html_with_dialogue("**Tóm tắt** Chương này giới thiệu *PCG*.\n\nVol. **2**(3), 1–10. Đỉnh v**n** là phòng **n**")
    assert "<strong>Tóm tắt</strong> Chương" in html and "<em>PCG</em>" in html
    assert "<strong>2</strong>(3)" in html and "v<strong>n</strong> là" in html and "**" not in html


def test_code_fence_keeps_indentation_and_row_breaks():
    html = markdown_to_html_with_dialogue(
        "**Room algorithm**\n\n```\nN=0\n    If a 3x3 block is empty\n        mark it\nEnd Scan\n```\n\nOnce marked.")
    assert '<pre class="code-listing">N=0\n    If a 3x3 block is empty\n        mark it\nEnd Scan</pre>' in html
    assert "<p>Once marked.</p>" in html or ">Once marked.<" in html


def test_praise_blurb_renders_quote_and_right_attribution():
    html = markdown_to_html_with_dialogue(
        '"Cuốn sách hay nhất."\n\n- David Jaffe, giám đốc sáng tạo\n\n⭐️⭐️⭐️\n\n- Midwest Book Review\n\n'
        '"Kinh điển."\n\n- Tom Chatfield, Fun, Inc.\n\n'
        'Anh ấy nói:\n\n- Đi thôi.\n\n"Câu trích."\n\n- Một\n- Hai')
    assert '<blockquote class="praise"><p>"Cuốn sách hay nhất."</p></blockquote>' in html
    assert '<p class="quote-attribution">— David Jaffe, giám đốc sáng tạo</p>' in html
    assert '<blockquote class="praise"><p>⭐️⭐️⭐️</p></blockquote>' in html
    assert '<p class="quote-attribution">— Tom Chatfield, Fun, Inc.</p>' in html
    # dialogue (ends in punctuation) and dash runs stay dialogue
    assert 'class="dialogue-line">- Đi thôi.' in html and 'class="dialogue-line">- Một' in html


def test_image_inside_front_block_renders_as_figure():
    html = markdown_to_html_with_dialogue(
        '<!-- front id="dedication" -->\n\n![](images/comic-dedication.png)\n\nTặng các con.\n\n<!-- /front -->')
    assert '<figure class="figure-image"><img src="images/comic-dedication.png"' in html
    assert '<p>![' not in html
