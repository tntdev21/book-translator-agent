#!/usr/bin/env python3
"""Regression test: docs/toc-standards.md is referenced by export.py and
validate_toc.py, so it must exist and document every rule the validator enforces.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOC = REPO_ROOT / "docs" / "toc-standards.md"
EXPORT = REPO_ROOT / "scripts" / "export.py"
VALIDATE_TOC = REPO_ROOT / "scripts" / "utils" / "validate_toc.py"


@pytest.fixture(scope="module")
def doc_text():
    assert DOC.exists(), f"docs/toc-standards.md is missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


class TestDocExists:
    def test_file_exists(self):
        assert DOC.is_file()

    def test_not_empty(self, doc_text):
        assert len(doc_text.strip()) > 200


class TestDocumentsValidatorRules:
    @pytest.mark.parametrize("header", ["MỤC LỤC", "TABLE OF CONTENTS", "CONTENTS"])
    def test_documents_toc_headers(self, doc_text, header):
        assert header in doc_text

    def test_documents_uppercase_chapter_rule(self, doc_text):
        assert "CHƯƠNG" in doc_text
        assert "Chương" in doc_text  # documents what NOT to do

    def test_documents_chapter_pattern(self, doc_text):
        assert re.search(r"\^CHƯƠNG \\?\(?\\d", doc_text) or "^CHƯƠNG (\\d+)$" in doc_text

    def test_documents_chunk_naming(self, doc_text):
        assert "chunk_001.md" in doc_text

    def test_documents_sequential_numbering(self, doc_text):
        assert "sequential" in doc_text.lower() or "tuần tự" in doc_text.lower()

    def test_documents_toc_content_crosscheck(self, doc_text):
        assert "not in content" in doc_text
        assert "not in TOC" in doc_text


class TestReferencersPointAtRealFile:
    def test_export_reference_resolves(self):
        """export.py mentions docs/toc-standards.md — that path must exist."""
        src = EXPORT.read_text(encoding="utf-8")
        assert "docs/toc-standards.md" in src
        assert (REPO_ROOT / "docs" / "toc-standards.md").is_file()

    def test_validate_toc_docstring_reference_resolves(self):
        src = VALIDATE_TOC.read_text(encoding="utf-8")
        assert "docs/toc-standards.md" in src
        assert (REPO_ROOT / "docs" / "toc-standards.md").is_file()

    def test_validator_patterns_documented_verbatim(self, doc_text):
        """Cross-check the doc against the validator's actual constants."""
        for p in (REPO_ROOT / "scripts", REPO_ROOT / "scripts" / "utils"):
            if str(p) not in __import__("sys").path:
                __import__("sys").path.insert(0, str(p))
        from validate_toc import TOCValidator

        for header in TOCValidator.TOC_HEADERS:
            assert header in doc_text, f"doc omits TOC header {header!r}"
