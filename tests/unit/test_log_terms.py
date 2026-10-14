"""Tests for validated terminology logging and script-native maintenance."""

import subprocess
import sys
from pathlib import Path

from scripts.log_terms import (
    log_term,
    remove_invalid_entries,
    remove_term,
    replace_translation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "log_terms.py"
VALID = "site-specificity | tính đặc thù theo trường hợp | contextual care | chunk_009"


def test_log_term_adds_valid_entry_and_rejects_duplicate(tmp_path):
    terms_file = tmp_path / "new_terms.txt"

    assert log_term(VALID, str(terms_file))
    assert not log_term(VALID, str(terms_file))
    assert terms_file.read_text(encoding="utf-8").count("site-specificity") == 1


def test_log_term_rejects_term_already_in_glossary(tmp_path):
    terms_file = tmp_path / "new_terms.txt"
    (tmp_path / "glossary.csv").write_text(
        "source_term,target_term,context,chunk_id\nRobot,rô-bốt,,\n", encoding="utf-8"
    )

    assert not log_term("robot | người máy | ctx | chunk_009", str(terms_file))
    assert "robot" not in terms_file.read_text(encoding="utf-8").lower()
    assert log_term(VALID, str(terms_file))


def test_invalid_entries_do_not_create_or_mutate_term_file(tmp_path):
    terms_file = tmp_path / "new_terms.txt"

    for invalid in (
        "--help",
        "term | translation | context",
        "term |  | context | chunk_001",
        "term | translation | context | unknown",
        "term | translation | context | chunk_001\nextra",
    ):
        assert not log_term(invalid, str(terms_file))
        assert not terms_file.exists()


def test_remove_invalid_entries_preserves_valid_records(tmp_path):
    terms_file = tmp_path / "new_terms.txt"
    terms_file.write_text(
        f"# New Terms Log\n\n## Chunk 009\n\n{VALID}\n\n## Unknown\n\n--help\n",
        encoding="utf-8",
    )

    assert remove_invalid_entries(str(terms_file)) == ["--help"]
    content = terms_file.read_text(encoding="utf-8")
    assert VALID in content
    assert "--help" not in content
    assert "## Unknown" not in content


def test_replace_translation_updates_exactly_one_valid_term(tmp_path):
    terms_file = tmp_path / "new_terms.txt"
    terms_file.write_text(f"# New Terms Log\n\n## Chunk 009\n\n{VALID}\n", encoding="utf-8")

    assert replace_translation("site-specificity", "tính đặc thù theo địa điểm", str(terms_file))
    content = terms_file.read_text(encoding="utf-8")
    assert "site-specificity | tính đặc thù theo địa điểm | contextual care | chunk_009" in content


def test_replace_translation_failures_do_not_mutate_file(tmp_path):
    terms_file = tmp_path / "new_terms.txt"
    terms_file.write_text(
        f"# New Terms Log\n\n## Chunk 009\n\n{VALID}\n{VALID}\n", encoding="utf-8"
    )
    before = terms_file.read_text(encoding="utf-8")

    assert not replace_translation("missing", "mới", str(terms_file))
    assert not replace_translation("site-specificity", "mới", str(terms_file))
    assert terms_file.read_text(encoding="utf-8") == before


def test_help_does_not_mutate_active_term_log():
    terms_file = REPO_ROOT / "books" / "help-probe-book" / "style" / "new_terms.txt"
    assert not terms_file.exists()

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help", "--book", "help-probe-book"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert not terms_file.exists()


def test_remove_term_removes_exactly_one_entry(tmp_path):
    terms_file = tmp_path / "new_terms.txt"
    terms_file.write_text("exception | ngoại lệ | pun | chunk_004\nthể chai | corpus | x | chunk_006\n", encoding="utf-8")
    assert remove_term("Exception", str(terms_file))
    assert terms_file.read_text(encoding="utf-8") == "thể chai | corpus | x | chunk_006\n"
    assert not remove_term("missing", str(terms_file))
