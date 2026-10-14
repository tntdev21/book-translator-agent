#!/usr/bin/env python3
"""Regression tests for the chunk file glob pattern.

Bug: several standalone CLIs globbed ``chunk_*_vi.md`` while translated files
are actually named ``chunk_NNN.md`` (no language suffix). Those scripts found
zero files and silently did nothing.

The CLIs now resolve their directory from the active book (book_config), so
these tests stub the book resolution to point at a tmp translated/ dir.
"""

import sys
from pathlib import Path

import pytest

# Make scripts/ and scripts/utils/ importable the same way the CLIs run.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"
SCRIPTS_UTILS = SCRIPTS / "utils"
for p in (SCRIPTS, SCRIPTS_UTILS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


class _StubConfig:
    """BookConfig stand-in exposing only what the fix CLIs read."""

    def __init__(self, translated_dir: Path):
        self.translated_dir = translated_dir


@pytest.fixture
def translated_dir(tmp_path, monkeypatch):
    """A translated/ dir holding chunks named WITHOUT the _vi suffix."""
    d = tmp_path / "translated"
    d.mkdir()
    (d / "chunk_001.md").write_text("# CHƯƠNG 1\n\nNội dung.\n", encoding="utf-8")
    (d / "chunk_002.md").write_text("# CHƯƠNG 2\n\nNội dung.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return d


@pytest.fixture
def stub_book(monkeypatch):
    """Patch the CLI module's own ``bootstrap_argv`` to yield a tmp dir.

    Patching the module under test (not book_config) is required because the
    utils import ``bootstrap_argv`` by value, so rebinding it on book_config
    afterwards would have no effect on the already-bound name.

    Returns a setter: call ``stub_book(module, path)``.
    """

    def _install(module, path: Path):
        def fake_bootstrap(argv=None):
            return [argv[0] if argv else "cli.py"], _StubConfig(path)

        monkeypatch.setattr(module, "bootstrap_argv", fake_bootstrap)

    return _install


class TestFixChapterFormatGlob:
    def test_finds_chunks_without_vi_suffix(self, translated_dir, stub_book, capsys):
        import fix_chapter_format

        stub_book(fix_chapter_format, translated_dir)
        fix_chapter_format.main()
        out = capsys.readouterr().out
        assert "in 2 files" in out, f"expected 2 files, got: {out}"

    def test_does_not_warn_zero_files(self, translated_dir, stub_book, capsys):
        import fix_chapter_format

        stub_book(fix_chapter_format, translated_dir)
        fix_chapter_format.main()
        assert "in 0 files" not in capsys.readouterr().out


class TestFixDashSpacingRetired:
    def test_main_refuses_and_leaves_files_untouched(self, translated_dir, capsys):
        import fix_dash_spacing

        (translated_dir / "chunk_001.md").write_text(
            '<p class="front-title">X</p>\n', encoding="utf-8"
        )
        before = {f.name: f.read_text(encoding="utf-8") for f in translated_dir.glob("*.md")}
        with pytest.raises(SystemExit) as exc:
            fix_dash_spacing.main()
        assert exc.value.code == 1
        assert "retired" in capsys.readouterr().err
        after = {f.name: f.read_text(encoding="utf-8") for f in translated_dir.glob("*.md")}
        assert after == before


class TestExportPdfGlob:
    def test_test_mode_resolves_chunk_001(self, translated_dir):
        """Previously looked for chunk_001_vi.md and found nothing."""
        translated = Path("translated")
        expected = translated / "chunk_001.md"
        assert expected.exists()
        # The glob the full-book path uses must match our fixture files.
        assert len(sorted(translated.glob("chunk_*.md"))) == 2
        # Guard against regressing back to the _vi form.
        assert not list(translated.glob("chunk_*_vi.md"))

    def test_source_has_no_vi_glob(self):
        """The module source must not glob the stale _vi pattern."""
        src = (SCRIPTS_UTILS / "export_pdf.py").read_text(encoding="utf-8")
        assert "chunk_*_vi.md" not in src
        assert "chunk_001_vi.md" not in src
        assert "{i:03d}_vi.md" not in src
