"""Regression tests for glossary validation and terminology precedence."""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_SCRIPTS = REPO_ROOT / ".claude" / "skills" / "translating" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

_spec = importlib.util.spec_from_file_location(
    "validate_translation", SKILL_SCRIPTS / "validate-translation.py"
)
validate_translation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_translation)


@pytest.fixture
def glossary_csv(tmp_path):
    path = tmp_path / "glossary.csv"
    path.write_text(
        "source_term,target_term,context,chunk_id\n"
        "artificial intelligence,trí tuệ nhân tạo,domain,chunk_001\n",
        encoding="utf-8",
    )
    return path


def test_missing_glossary_is_skipped(tmp_path):
    assert validate_translation.check_glossary_consistency(
        "source", "translation", tmp_path / "missing.csv"
    ) == []


def test_none_glossary_is_skipped():
    assert validate_translation.check_glossary_consistency("source", "translation", None) == []


def test_csv_glossary_checks_source_not_translation(glossary_csv):
    assert validate_translation.check_glossary_consistency(
        "Artificial intelligence is useful.", "Hữu ích.", glossary_csv
    ) == [
        "Term 'artificial intelligence' found in source but translation "
        "'trí tuệ nhân tạo' not used"
    ]


def test_glossary_passes_when_target_is_used(glossary_csv):
    assert validate_translation.check_glossary_consistency(
        "Artificial intelligence is useful.",
        "Trí tuệ nhân tạo rất hữu ích.",
        glossary_csv,
    ) == []


def test_legacy_pipe_glossary_is_supported(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        "English | Vietnamese | Context | Chunk ID\n"
        "mind | tâm trí | concept | chunk_001\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "The mind matters.", "Tâm trí rất quan trọng.", glossary
    ) == []


def test_csv_supports_quoted_pipes_and_newlines(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        "source_term,target_term,context,chunk_id\n"
        'machine learning,học máy,"uses | and a\nnewline",\n',
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Machine learning matters.", "Học máy rất quan trọng.", glossary
    ) == []


def test_new_terms_override_case_insensitively(glossary_csv, tmp_path):
    terms = tmp_path / "new_terms.txt"
    terms.write_text(
        "# New Terms Log\n\n## Chunk 001\n\n"
        "Artificial Intelligence | AI | acronym decision | chunk_001\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Artificial intelligence is useful.",
        "AI rất hữu ích.",
        glossary_csv,
        terms,
    ) == []
    issues = validate_translation.check_glossary_consistency(
        "Artificial intelligence is useful.",
        "Trí tuệ nhân tạo rất hữu ích.",
        glossary_csv,
        terms,
    )
    assert "'AI' not used" in issues[0]


def test_first_mention_new_term_allows_base_rendering(glossary_csv, tmp_path):
    terms = tmp_path / "new_terms.txt"
    terms.write_text(
        "# New Terms Log\n\n## Chunk 001\n\n"
        "artificial intelligence | trí tuệ nhân tạo (AI) | First mention | chunk_001\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Artificial intelligence changes society.",
        "Trí tuệ nhân tạo thay đổi xã hội.",
        glossary_csv,
        terms,
    ) == []


def test_validate_without_glossary_has_no_glossary_warning(tmp_path):
    source = tmp_path / "source.md"
    translated = tmp_path / "translated.md"
    source.write_text("Hello world.\n", encoding="utf-8")
    translated.write_text("Xin chào thế giới.\n", encoding="utf-8")
    results = validate_translation.validate(source, translated)
    assert not any("Glossary" in warning for warning in results["warnings"])


def test_csv_header_supports_quoted_pipe(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        'source_term,target_term,"context | note",chunk_id\n'
        "machine learning,học máy,domain,\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Machine learning matters.", "Học máy rất quan trọng.", glossary
    ) == []


def test_csv_with_utf8_bom_is_supported(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        "source_term,target_term,context,chunk_id\n"
        "machine learning,học máy,domain,\n",
        encoding="utf-8-sig",
    )
    assert validate_translation.check_glossary_consistency(
        "Machine learning matters.", "Học máy rất quan trọng.", glossary
    ) == []


def test_csv_supports_reordered_standard_headers(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        "target_term,source_term,chunk_id,context\n"
        "học máy,machine learning,,domain\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Machine learning matters.", "Học máy rất quan trọng.", glossary
    ) == []


def test_glossary_source_matching_respects_word_boundaries(tmp_path):
    glossary = tmp_path / "glossary.csv"
    glossary.write_text(
        "source_term,target_term,context,chunk_id\n"
        "mind,tâm trí,concept,\n",
        encoding="utf-8",
    )
    assert validate_translation.check_glossary_consistency(
        "Please remind me tomorrow.", "Hãy nhắc tôi vào ngày mai.", glossary
    ) == []


def test_parenthetical_first_mention_target_is_not_skipped(tmp_path):
    glossary = tmp_path / "glossary.csv"
    terms = tmp_path / "new_terms.txt"
    glossary.write_text("source_term,target_term,context,chunk_id\n", encoding="utf-8")
    terms.write_text(
        "AI | (AI) | First mention acronym | chunk_001\n",
        encoding="utf-8",
    )
    issues = validate_translation.check_glossary_consistency(
        "AI is useful.", "Hữu ích.", glossary, terms
    )
    assert "'(AI)' not used" in issues[0]


def test_book_name_exceptions_load(tmp_path):
    import json

    names = tmp_path / "book_names.json"
    names.write_text(
        json.dumps({"full_names": {"Anna Smith": 5}, "individual_names": ["Anna"]}),
        encoding="utf-8",
    )
    assert any("Anna" in pattern for pattern in validate_translation.load_book_name_exceptions(names))
