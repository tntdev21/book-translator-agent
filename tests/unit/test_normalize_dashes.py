#!/usr/bin/env python3
"""Unit tests for contextual em-dash normalization."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.normalize_dashes import (  # noqa: E402
    main,
    normalize_dash_string,
    normalize_dashes_file,
)


class TestNormalizeDashString:
    def test_normalizes_leading_em_dash_as_dialogue(self):
        assert normalize_dash_string("— Xin chào.") == "- Xin chào."
        assert normalize_dash_string("—Xin chào.") == "- Xin chào."

    def test_normalizes_prose_em_dash_with_spaces(self):
        assert (
            normalize_dash_string("Điều đó—thật bất ngờ—đã xảy ra.")
            == "Điều đó - thật bất ngờ - đã xảy ra."
        )
        assert normalize_dash_string("Điều đó — thật bất ngờ — đã xảy ra.") == (
            "Điều đó - thật bất ngờ - đã xảy ra."
        )

    def test_keeps_dialogue_and_prose_contexts_in_multiline_input(self):
        text = "—Xin chào.\nĐó—là điều bất ngờ.\n— Tạm biệt.\n"
        assert normalize_dash_string(text) == (
            "- Xin chào.\nĐó - là điều bất ngờ.\n- Tạm biệt.\n"
        )

    def test_normalizes_prose_em_dash_after_dialogue_marker(self):
        assert normalize_dash_string("—Hello—there") == "- Hello - there"

    def test_preserves_fenced_and_indented_code_blocks(self):
        text = "```\n    — keep indent\n```\n\n    — also literal\n"
        assert normalize_dash_string(text) == text

    def test_preserves_existing_ranges_and_compounds(self):
        text = "Khoảng 10–20%, một người self-aware và well-known."
        assert normalize_dash_string(text) == text

    def test_leaves_content_without_em_dash_unchanged(self):
        text = "Nội dung không có em-dash."
        assert normalize_dash_string(text) == text
        assert normalize_dash_string("") == ""


class TestNormalizeDashesFile:
    def test_writes_normalized_content_and_reports_em_dash_count(self, tmp_path):
        target = tmp_path / "chunk_001.md"
        target.write_text("—Hello\nfirst—second—third\n", encoding="utf-8")

        assert normalize_dashes_file(target) == 3
        assert target.read_text(encoding="utf-8") == "- Hello\nfirst - second - third\n"

    def test_accepts_string_path_and_preserves_utf8(self, tmp_path):
        target = tmp_path / "unicode.md"
        target.write_text("Tiếng Việt—rõ ràng", encoding="utf-8")

        assert normalize_dashes_file(str(target)) == 1
        assert target.read_text(encoding="utf-8") == "Tiếng Việt - rõ ràng"

    def test_does_not_rewrite_file_without_em_dash(self, tmp_path):
        target = tmp_path / "unchanged.md"
        content = "10–20% và self-aware"
        target.write_text(content, encoding="utf-8")

        assert normalize_dashes_file(target) == 0
        assert target.read_text(encoding="utf-8") == content


class TestMainFunction:
    def test_reports_modified_files_and_total_replacements(self, tmp_path, capsys):
        translated_dir = tmp_path / "translated"
        translated_dir.mkdir()
        (translated_dir / "chunk_001.md").write_text("One—two", encoding="utf-8")
        (translated_dir / "chunk_002.md").write_text("—Hello", encoding="utf-8")

        main(translated_dir)

        captured = capsys.readouterr().out
        assert "Files processed: 2" in captured
        assert "Files modified: 2" in captured
        assert "Total em-dashes replaced: 2" in captured

    def test_reports_missing_directory(self, tmp_path, capsys):
        main(tmp_path / "missing")
        assert "Error: translated directory not found" in capsys.readouterr().out
