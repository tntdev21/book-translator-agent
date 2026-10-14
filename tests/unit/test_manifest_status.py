#!/usr/bin/env python3
"""Tests for scripts/manifest_status.py (manifest 5-state transitions)."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import manifest_status as ms  # noqa: E402


class _Book:
    def __init__(self, root: Path):
        self.manifest_path = root / "chunks" / "manifest.json"
        self.translated_dir = root / "translated"


@pytest.fixture
def book(tmp_path, monkeypatch):
    (tmp_path / "chunks").mkdir()
    (tmp_path / "translated").mkdir()
    chunks = [
        {"id": f"{i:03d}", "status": "pending",
         "status_history": [{"status": "pending", "at": "t0"}]}
        for i in (1, 2)
    ]
    b = _Book(tmp_path)
    b.manifest_path.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
    monkeypatch.setattr(ms, "load_book", lambda _id=None: b)
    return b


def _write(book, cid, text="Nội dung.\n"):
    (book.translated_dir / f"chunk_{cid}.md").write_text(text, encoding="utf-8")


def _chunk(book, cid):
    data = json.loads(book.manifest_path.read_text(encoding="utf-8"))
    return next(c for c in data["chunks"] if c["id"] == cid), data


def test_full_legal_path_appends_history(book):
    _write(book, "001")
    for status in ("translated", "review", "rework", "translated", "review", "qa_passed"):
        assert ms.main([status, "chunk_001"]) == 0
    chunk, data = _chunk(book, "001")
    assert chunk["status"] == "qa_passed"
    assert [h["status"] for h in chunk["status_history"]] == [
        "pending", "translated", "review", "rework", "translated", "review", "qa_passed"]
    assert chunk["status_history"][-1]["at"].endswith("+00:00")
    assert data["statistics"]["chunks_qa_passed"] == 1
    assert data["statistics"]["chunks_pending"] == 1
    assert data["statistics"]["progress_percent"] == 50


def test_accepts_bare_and_prefixed_ids_in_one_call(book):
    _write(book, "001")
    _write(book, "002")
    assert ms.main(["translated", "001", "chunk_002"]) == 0
    assert _chunk(book, "001")[0]["status"] == "translated"
    assert _chunk(book, "002")[0]["status"] == "translated"


@pytest.mark.parametrize("status", ["review", "qa_passed", "rework"])
def test_illegal_from_pending_refused(book, status, capsys):
    assert ms.main([status, "chunk_001"]) == 1
    assert "illegal pending -> " + status in capsys.readouterr().err
    assert _chunk(book, "001")[0]["status"] == "pending"


def test_translated_refused_when_file_missing(book, capsys):
    assert ms.main(["translated", "chunk_001"]) == 1
    assert "missing or empty" in capsys.readouterr().err


def test_translated_refused_when_file_empty(book):
    _write(book, "001", "")
    assert ms.main(["translated", "chunk_001"]) == 1
    assert _chunk(book, "001")[0]["status"] == "pending"


def test_all_or_nothing_on_mixed_batch(book):
    _write(book, "001")  # 002 has no file
    before = book.manifest_path.read_text(encoding="utf-8")
    assert ms.main(["translated", "chunk_001", "chunk_002"]) == 1
    assert book.manifest_path.read_text(encoding="utf-8") == before


def test_unknown_chunk_refused(book, capsys):
    assert ms.main(["translated", "chunk_099"]) == 1
    assert "not in manifest" in capsys.readouterr().err


def test_qa_passed_is_terminal(book):
    _write(book, "001")
    for status in ("translated", "review", "qa_passed"):
        assert ms.main([status, "001"]) == 0
    assert ms.main(["rework", "001"]) == 1


def test_reopen_allows_only_qa_passed_to_rework(book):
    _write(book, "001")
    for status in ("translated", "review", "qa_passed"):
        assert ms.main([status, "001"]) == 0
    assert ms.main(["--reopen", "review", "001"]) == 1
    assert ms.main(["--reopen", "rework", "001"]) == 0
    assert ms.main(["--reopen", "rework", "002"]) == 1  # pending stays illegal
    assert _chunk(book, "001")[0]["status"] == "rework"


def test_pending_is_not_a_target(book):
    with pytest.raises(SystemExit):
        ms.main(["pending", "001"])


def test_unknown_book_refused_without_traceback(monkeypatch, capsys):
    def boom(_id=None):
        raise ms.BookConfigError("book.yaml not found: books/nope/book.yaml")
    monkeypatch.setattr(ms, "load_book", boom)
    assert ms.main(["translated", "001"]) == 1
    assert "REFUSED: book.yaml not found" in capsys.readouterr().err


def test_write_leaves_no_tmp_file(book):
    _write(book, "001")
    assert ms.main(["translated", "001"]) == 0
    assert not list(book.manifest_path.parent.glob("*.tmp"))
