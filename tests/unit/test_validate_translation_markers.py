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



SRC = '<!-- Page 3 -->\n\n<!-- front id="ban-quyen" class="copyright" -->\n<small>Copyright</small>\n<!-- /front -->\n'


def test_markers_preserved_is_clean():
    vi = SRC.replace("Copyright", "Bản quyền")
    assert validate_translation.check_structure_markers(SRC, vi) == []


def test_dropped_front_marker_is_error():
    vi = '<!-- Page 3 -->\n\n<small>Bản quyền</small>\n'
    errors = validate_translation.check_structure_markers(SRC, vi)
    assert errors and "front" in errors[0]


def test_validate_fails_on_dropped_marker(tmp_path):
    s, t = tmp_path / "s.md", tmp_path / "t.md"
    s.write_text(SRC, encoding="utf-8")
    t.write_text('<!-- Page 3 -->\n\n<small>Bản quyền</small>\n', encoding="utf-8")
    assert validate_translation.validate(s, t)["valid"] is False


def test_small_caps_copied_verbatim_is_clean():
    src = 'on my way—<span class="sc">LET AGREED</span>, one says\n'
    vi = 'trên đường - <span class="sc">LET AGREED</span>, một tấm biển\n'
    assert validate_translation.check_small_caps(src, vi) == []


def test_translated_small_caps_label_is_error():
    src = '<span class="sc">JUDGE</span>: *Hi*\n'
    vi = '<span class="sc">GIÁM KHẢO</span>: *Chào*\n'
    assert validate_translation.check_small_caps(src, vi)


def test_inline_small_caps_may_be_localised_but_not_dropped():
    src = 'in 500 <span class="sc">B.C.</span>, and <span class="sc">B.C</span>\n'
    vi = 'năm 500 <span class="sc">TCN</span>, và <span class="sc">TCN</span>\n'
    assert validate_translation.check_small_caps(src, vi) == []
    assert validate_translation.check_small_caps(src, 'năm 500 <span class="sc">TCN</span>, và TCN\n')


def test_orphaned_inline_small_block_is_error():
    torn = "the signs I pass on my way - , one says, prominently, in\n\n<small>LET AGREED</small>\n\nlarge print.\n"
    assert validate_translation.check_orphan_small(torn, "source")


def test_display_small_block_between_sentences_is_clean():
    ok = "He wrote it down.\n\n<small>DAVID FOSTER WALLACE</small>\n\nNext chapter begins.\n"
    assert validate_translation.check_orphan_small(ok) == []


def test_speaker_turn_without_label_is_error():
    torn = ": *What is your opinion*?\n\n<small>JUDGE</small>\n\n: *That is general*\n"
    assert len(validate_translation.check_orphan_small(torn)) == 2
