"""Tests for build_terms_compact + CLI compact output (phase 3, D13/D24)."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.extract_term_map import (  # noqa: E402
    build_terms_compact,
    load_glossary_rows,
    load_new_terms_rows,
)

ROOT = Path(__file__).resolve().parents[2]
NEW_TERMS = """# New Terms Log


## Chunk 001

artificial intelligence | trí tuệ nhân tạo (AI) | First mention of the AI field | chunk_001
Most Human Human | Người Người Nhất | Loebner Prize title and book title | chunk_001
Most Human Computer | Máy tính giống người nhất | Loebner Prize title | chunk_001
human confederate | người đồng minh con người | Turing-test human participant | chunk_001
Turing test | phép thử Turing | Named AI evaluation test | chunk_001
computer | computer | Historical occupation and later technical term; deliberately retained to preserve the chapter's semantic contrast | chunk_001
"""


def test_glossary_wins_on_conflict():
    out = build_terms_compact([("Turing test", "bài kiểm tra Turing", "")],
                              [("turing test", "phép thử Turing", "")])
    assert "Turing test → bài kiểm tra Turing" in out
    assert "phép thử" not in out
    assert out.count("→") == 1


def test_sort_dedup_deterministic():
    rows = [("b", "B", ""), ("A", "x", ""), ("b", "B", "")]
    out = build_terms_compact([], rows)
    assert out == build_terms_compact([], list(rows))
    lines = [l for l in out.splitlines() if "→" in l]
    assert lines == ["A → x", "b → B"]
    assert "2 terms" in out


def test_empty_inputs():
    out = build_terms_compact([], [])
    assert out.startswith("# Terms")
    assert "0 terms" in out
    assert "## Drift\n(none)" in out


def test_header_only_new_terms(tmp_path):
    nt = tmp_path / "new_terms.txt"
    nt.write_text("# New Terms Log\n\n", encoding="utf-8")
    assert load_new_terms_rows(nt) == []
    out = build_terms_compact([("robot", "rô-bốt", "")], load_new_terms_rows(nt))
    assert "robot → rô-bốt" in out and "1 terms" in out


def test_missing_files(tmp_path):
    assert load_new_terms_rows(tmp_path / "x") == []
    assert load_glossary_rows(tmp_path / "y") == []


def test_drift_section():
    tm = {"terms": [
        {"source": "foo", "drift": True, "renderings": [
            {"vi": "một", "chunks": ["chunk_001", "chunk_002"], "count": 2},
            {"vi": "hai", "chunks": ["chunk_003"], "count": 1}]},
        {"source": "bar", "drift": False, "renderings": [
            {"vi": "ba", "chunks": ["chunk_001"], "count": 1}]},
    ]}
    out = build_terms_compact([("bar", "ba", "")], [("foo", "một", "")], tm)
    drift = out.split("## Drift\n", 1)[1]
    assert drift.strip() == "foo → một (chunk_001, chunk_002); hai (chunk_003)"
    assert "bar" not in drift


def test_real_new_terms_context_rule(tmp_path):
    nt = tmp_path / "new_terms.txt"
    nt.write_text(NEW_TERMS, encoding="utf-8")
    rows = load_new_terms_rows(nt)
    assert len(rows) == 6
    out = build_terms_compact([], rows)
    comp = [l for l in out.splitlines() if l.startswith("computer →")][0]
    assert comp.startswith("computer → computer (Historical")
    assert len(comp[len("computer → computer ("):-1]) <= 60
    assert "Turing test → phép thử Turing\n" in out
    assert "Named AI" not in out


def test_retained_term_without_context_has_no_parens():
    out = build_terms_compact([("computer", "Computer", "")], [])
    assert "computer → Computer\n" in out


def _book(tmp_path):
    b = tmp_path / "b"
    (b / "translated").mkdir(parents=True)
    (b / "style").mkdir()
    (b / "style" / "glossary.csv").write_text(
        "source_term,target_term,context,chunk_id\nrobot,rô-bốt,x,\n", encoding="utf-8")
    (b / "style" / "new_terms.txt").write_text("# h\n", encoding="utf-8")
    return b


def _run(b, *extra):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "extract_term_map.py"), "--quiet",
         "--translated-dir", str(b / "translated"),
         "--new-terms", str(b / "style" / "new_terms.txt"),
         "--glossary", str(b / "style" / "glossary.csv"),
         "--output", str(b / "style" / "term_map.json"), *extra],
        capture_output=True, text=True)


def test_cli_writes_compact_and_no_compact(tmp_path):
    b = _book(tmp_path)
    r = _run(b)
    assert r.returncode == 0, r.stderr
    p = b / "style" / "_terms_compact.md"
    first = p.read_bytes()
    assert b"robot \xe2\x86\x92 r\xc3\xb4-b\xe1\xbb\x91t" in first
    _run(b)
    assert p.read_bytes() == first
    p.unlink()
    assert _run(b, "--no-compact").returncode == 0
    assert not p.exists()
    assert (b / "style" / "term_map.json").exists()
