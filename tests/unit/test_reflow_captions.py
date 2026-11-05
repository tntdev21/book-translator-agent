"""Repair of paragraphs split by a top-of-page figure/table caption (data migration)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from utils.reflow_captions import reflow_files, reflow_split_captions  # noqa: E402


def test_caption_moved_after_rejoined_paragraph():
    md = ("The rule (or\n\n<!-- Page 37 -->\n\n(a) Map (b) Tree\n\nFig. 3.2: Cap\n\n"
          "pixels) relaxed.\n\nNext para.")
    out, ids = reflow_split_captions(md)
    assert ids == ["F3.2"]
    assert out == ("The rule (or\n<!-- Page 37 -->\npixels) relaxed.\n\n(a) Map (b) Tree\n\n"
                   "Fig. 3.2: Cap\n\nNext para.")


def test_complete_sentence_and_heading_untouched():
    for md in ("Done.\n\nHình 1.1: Cap\n\nđoạn mới.", "Text\n\nHình 1.1: Cap\n\n## 1.2 Mục",
               "```\ncode\n```\n\nFig. 1.1: Cap\n\nlower start."):
        assert reflow_split_captions(md) == (md, [])


def test_continuation_after_citation_bracket_or_backtick():
    for cont in ("[13] is another game.", "(blocks and bricks), coins.", "`minimize` statement tells."):
        md = f"Games such as Tiny Wings\n\nFig. 1.1: Cap\n\n{cont}"
        out, ids = reflow_split_captions(md)
        assert ids == ["F1.1"] and out.rstrip() == f"Games such as Tiny Wings\n{cont}\n\nFig. 1.1: Cap"
    md = "Run the program\n\nFig. 1.1: Cap\n\n``` clingo maze.lp ```"
    assert reflow_split_captions(md) == (md, [])


def test_forced_ids_repair_uppercase_continuation():
    md = "Cuối câu là\n\nHình 2.1: Cap\n\nDijkstra tìm đường."
    assert reflow_split_captions(md)[1] == []
    out, ids = reflow_split_captions(md, force={"F2.1"})
    assert ids == ["F2.1"] and out.startswith("Cuối câu là\nDijkstra tìm đường.\n\nHình 2.1")


def test_table_marker_and_numbered_rows_are_part_of_block():
    vi = 'cần thiết để các\n\n<!-- Page 9 -->\n\nBảng 7.1: Kế hoạch\n\n<!-- figure id="table-7-1" -->\n\nhành động sau.'
    out, ids = reflow_split_captions(vi)
    assert ids == ["T7.1"]
    assert out == ('cần thiết để các\n<!-- Page 9 -->\nhành động sau.\n\nBảng 7.1: Kế hoạch\n\n'
                   '<!-- figure id="table-7-1" -->\n')
    en = "for subsequent\n\nTable 7.1: Plan\n\n1. Take (a)\n2. Kill (b)\n\nactions to occur."
    out, _ = reflow_split_captions(en)
    assert out.endswith("actions to occur.\n\nTable 7.1: Plan\n\n1. Take (a)\n2. Kill (b)\n")


def test_split_across_chunk_files_lands_in_first_chunk():
    a = "Intro.\n\nThe digger is\n"
    b = "<!-- Page 42 -->\n\nFig. 3.6: Cap\n\ninformed about it.\n\nNew para.\n"
    (na, nb), ids = reflow_files([a, b])
    assert ids == ["F3.6"]
    assert na == "Intro.\n\nThe digger is\n<!-- Page 42 -->\ninformed about it.\n\nFig. 3.6: Cap\n"
    assert nb == "New para.\n"


def test_unchanged_files_returned_verbatim():
    texts = ["A.\n", "\nB.\n\n"]
    assert reflow_files(texts) == (texts, [])


def test_paragraph_split_twice_is_fully_rejoined():
    md = ("1. Item text\n\n<!-- Page 88 -->\n\nFig. 5.15: A\n\n<!-- Page 89 -->\n\nFig. 5.16: B\n\n"
          "Fig. 5.17: C\n\nof a game space is still highly\n\nabstract. However.")
    out, ids = reflow_split_captions(md)
    assert "still highly\nabstract. However." in out
    assert out.index("abstract.") < out.index("Fig. 5.15") < out.index("Fig. 5.17")
    assert sorted(ids) == ["F5.15", "F5.16", "F5.17"]


def test_forced_id_applies_once():
    md = "Cuối câu là\n\nHình 2.1: Cap\n\nDijkstra xong.\n\nĐoạn mới."
    out, ids = reflow_split_captions(md, force={"F2.1"})
    assert ids == ["F2.1"] and out.endswith("Dijkstra xong.\n\nHình 2.1: Cap\n\nĐoạn mới.")


def test_join_fragments_outside_code():
    from utils.reflow_captions import join_fragments
    md = ("a. generating two points at random in different directions: one works as an\n\n"
          "attractor and more.\n\nThis method allows multiple agents to work on the map while pre-\n\n"
          "serving it.\n\nIf a 3x3 block is empty\n\nmark the block\n\n"
          "```\nx = a very long line of code that goes on and on and on\n\ny\n```\n\n"
          "Định nghĩa này dài hơn bốn mươi ký tự nhưng không có dấu chấm\n\nĐây là đoạn mới.")
    out, n = join_fragments(md)
    assert n == 2
    assert "one works as an attractor and more." in out and "while pre-serving it." in out
    assert "is empty\n\nmark the block" in out and "on and on\n\ny" in out
    assert "dấu chấm\n\nĐây là" in out
