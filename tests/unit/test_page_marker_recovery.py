"""Regression tests for page-marker preservation and recovery."""

import sys
from argparse import Namespace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
SCRIPTS_UTILS = SCRIPTS / "utils"
for path in (PROJECT_ROOT, SCRIPTS, SCRIPTS_UTILS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import scripts.fix as fix_script  # noqa: E402
from scripts.fix import normalize_page_markers_step  # noqa: E402
from scripts.utils.fix_dash_spacing import fix_dash_spacing  # noqa: E402


class TestLegacyDashSpacing:
    def test_preserves_page_marker_across_repeated_runs(self):
        content = "<!-- Page 29 -->\n\nNội dung-xuyên suốt.\n"

        once = fix_dash_spacing(content)
        twice = fix_dash_spacing(once)

        assert "<!-- Page 29 -->" in once
        assert "<!-- Page 29 -->" in twice
        assert "<! -" not in twice
        assert "Nội dung - xuyên suốt." in twice


class TestPageMarkerRecovery:
    def test_repairs_corrupted_marker_and_preserves_backup(self, tmp_path):
        target = tmp_path / "chunk_001.md"
        original = "<! -  -  Page 29  -  - >\n\nNội dung.\n"
        target.write_text(original, encoding="utf-8")

        assert normalize_page_markers_step([target], backup=True) == 1
        assert target.read_text(encoding="utf-8") == "<!-- Page 29 -->\n\nNội dung.\n"
        assert target.with_suffix(".md.bak").read_text(encoding="utf-8") == original

    def test_leaves_clean_marker_byte_identical(self, tmp_path):
        target = tmp_path / "chunk_001.md"
        content = "<!-- Page 29 -->\n\nNội dung.\n"
        target.write_text(content, encoding="utf-8")

        assert normalize_page_markers_step([target], backup=True) == 0
        assert target.read_text(encoding="utf-8") == content
        assert not target.with_suffix(".md.bak").exists()

    def test_main_repairs_all_selected_files_regardless_of_manifest_status(
        self, tmp_path, monkeypatch
    ):
        qa_passed = tmp_path / "chunk_001.md"
        translated = tmp_path / "chunk_004.md"
        for target in (qa_passed, translated):
            target.write_text("<! -  -  Page 29  -  - >", encoding="utf-8")

        config = type("Config", (), {"id": "test-book"})()
        args = Namespace(
            files=[str(qa_passed), str(translated)],
            check_only=False,
            no_backup=True,
            skip_name_extraction=True,
            skip_cjk=True,
            skip_sentence_breaks=True,
            skip_dashes=True,
            skip_person_names=True,
        )
        monkeypatch.setattr(fix_script, "parse_arguments", lambda: args)
        monkeypatch.setattr(fix_script, "get_config_from_args", lambda _: config)

        assert fix_script.main() == 0
        assert qa_passed.read_text(encoding="utf-8") == "<!-- Page 29 -->"
        assert translated.read_text(encoding="utf-8") == "<!-- Page 29 -->"
