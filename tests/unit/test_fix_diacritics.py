"""fix_diacritics (extraction-artefact repair) and person-name lowercase-term guard."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from utils.fix_diacritics import fix_diacritics_file, load_replacements, repair_text  # noqa: E402
from utils.fix_person_names import fix_person_names_in_text, load_person_names  # noqa: E402


@pytest.mark.parametrize("src,out", [
    ("Go¨del", "Gödel"),
    ("Altho¨fer", "Althöfer"),
    ("Be´zier", "Bézier"),
    ("Popovic´, Z.", "Popović, Z."),
    ("Mart´ınez", "Martínez"),
    ("Mart´ ınez", "Martínez"),
    ("Holmga˚rd", "Holmgård"),
    ("Schu¨rr", "Schürr"),
])
def test_recombines_spacing_accents(src, out):
    assert repair_text(src) == (out, 1)


def test_vietnamese_and_plain_text_untouched():
    text = "Thuật toán diamond-square của Perlin, đó là điều tốt. It's 5´ long?"
    fixed, n = repair_text(text)
    assert fixed == text.replace("5´", "5´") and n == 0


def test_no_composite_left_alone():
    assert repair_text("t´ and q¨") == ("t´ and q¨", 0)


def test_code_is_skipped():
    text = "dùng `a¨b` và Go¨del\n```\nGo¨del = 1\n```\nBe´zier"
    fixed, n = repair_text(text)
    assert fixed == "dùng `a¨b` và Gödel\n```\nGo¨del = 1\n```\nBézier"
    assert n == 2


def test_literal_replacements_longest_first():
    reps = {"(cid:54)=": "≠", "(cid:32)": "(", "Sch on ¨": "Schön"}
    fixed, n = repair_text("a (cid:54)= b; (cid:32) N; Donald Sch on ¨ said", reps)
    assert fixed == "a ≠ b; ( N; Donald Schön said" and n == 3


def test_file_check_only_and_fix(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("Go¨del\n", encoding="utf-8")
    assert fix_diacritics_file(f, check_only=True) == 1
    assert f.read_text(encoding="utf-8") == "Go¨del\n"
    assert fix_diacritics_file(f, backup=False) == 1
    assert f.read_text(encoding="utf-8") == "Gödel\n"
    assert fix_diacritics_file(f, backup=False) == 0  # idempotent


def test_load_replacements(tmp_path):
    assert load_replacements(tmp_path / "none.json") == {}
    p = tmp_path / "g.json"
    p.write_text(json.dumps({"replacements": {"a": "b"}}))
    assert load_replacements(p) == {"a": "b"}
    p.write_text(json.dumps({"replacements": {"a": 1}}))
    with pytest.raises(ValueError):
        load_replacements(p)


def test_lowercase_common_term_not_treated_as_person_name(tmp_path):
    terms = tmp_path / "new_terms.txt"
    terms.write_text(
        "diamond-square | diamond-square | algorithm name kept in English | chunk_009\n"
        "Julian Togelius | Julian Togelius | author name | chunk_001\n",
        encoding="utf-8")
    names = load_person_names(terms)
    assert "diamond-square" not in names and "Julian Togelius" in names
    text = "thuật toán diamond-square, và julian togelius"
    fixed, _ = fix_person_names_in_text(text, names)
    assert "diamond-square" in fixed and "Julian Togelius" in fixed
