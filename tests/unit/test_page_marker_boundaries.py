#!/usr/bin/env python3
"""Unit tests for page-marker boundary preservation (source ↔ VI)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
SCRIPTS_UTILS = SCRIPTS / "utils"
for _path in (PROJECT_ROOT, SCRIPTS, SCRIPTS_UTILS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.utils.fix_sentence_breaks import (  # noqa: E402
    _ensure_standalone_markers,
    fix_sentence_breaks,
)
from scripts.utils.page_marker_boundaries import (  # noqa: E402
    compare_boundaries,
    find_standalone_drift,
    marker_boundaries,
)


class TestMarkerBoundaries:
    def test_standalone_and_inline(self):
        text = "Câu 1.\n\n<!-- Page 3 -->\n\nCâu 2.\n\nCâu 3\n<!-- Page 4 -->\ncâu 4.\n"
        assert marker_boundaries(text) == {'3': 'standalone', '4': 'inline'}

    def test_compare_reports_only_mismatches(self):
        src = "Câu 1.\n\n<!-- Page 3 -->\n\nCâu 2.\n"
        vi = "Câu 1.\n<!-- Page 3 -->\nCâu 2.\n"
        assert compare_boundaries(src, vi) == [
            {'page': '3', 'source': 'standalone', 'translated': 'inline'}
        ]

    def test_matching_boundaries_empty(self):
        src = vi = "Câu 1.\n\n<!-- Page 3 -->\n\nCâu 2.\n"
        assert compare_boundaries(src, vi) == []

    def test_find_standalone_drift(self, tmp_path: Path):
        src = tmp_path / "chunks" / "chunk_001.md"
        vi = tmp_path / "translated" / "chunk_001.md"
        src.parent.mkdir(), vi.parent.mkdir()
        src.write_text("Câu 1.\n\n<!-- Page 7 -->\n\nCâu 2.\n", encoding="utf-8")
        vi.write_text("Câu 1.\n<!-- Page 7 -->\nCâu 2.\n", encoding="utf-8")
        assert find_standalone_drift(src, vi) == ['7']


class TestFixSentenceBreaksPreservation:
    def test_restores_standalone_marker(self, tmp_path: Path):
        f = tmp_path / "chunk.md"
        f.write_text(
            "Câu trước đó.\n<!-- Page 1 -->\ncâu sau continuation lowercase.\n",
            encoding="utf-8",
        )
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers={'1'})
        assert f.read_text(encoding="utf-8") == (
            "Câu trước đó.\n\n<!-- Page 1 -->\n\ncâu sau continuation lowercase.\n"
        )

    def test_leaves_inline_marker_alone(self, tmp_path: Path):
        f = tmp_path / "chunk.md"
        content = "Câu trước.\n<!-- Page 2 -->\ncâu sau continuation lowercase.\n"
        f.write_text(content, encoding="utf-8")
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers=set())
        assert f.read_text(encoding="utf-8") == content

    def test_still_joins_without_markers(self, tmp_path: Path):
        f = tmp_path / "chunk.md"
        f.write_text("Ông ấy nói với\ntôi\nĐang đi đâu đấy?\n", encoding="utf-8")
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers={'9'})
        assert "tôi" in f.read_text(encoding="utf-8")
        assert "\ntôi" not in f.read_text(encoding="utf-8")


class TestFixPySourcePairing:
    def test_resolve_source_pair_explicit_file(self, tmp_path: Path):
        from scripts.fix import resolve_source_pair

        src = tmp_path / "src" / "chunk_001.md"
        src.parent.mkdir()
        src.write_text("x", encoding="utf-8")
        vi = tmp_path / "chunk_001.md"
        assert resolve_source_pair(vi, str(src), None) == src

    def test_resolve_source_pair_explicit_dir(self, tmp_path: Path):
        from scripts.fix import resolve_source_pair

        srcdir = tmp_path / "chunks"
        srcdir.mkdir()
        (srcdir / "chunk_001.md").write_text("x", encoding="utf-8")
        vi = tmp_path / "chunk_001.md"
        assert resolve_source_pair(vi, str(srcdir), None) == srcdir / "chunk_001.md"

    def test_resolve_source_pair_fallback_to_book_chunks(self, tmp_path: Path):
        from scripts.fix import resolve_source_pair

        class _Cfg:
            chunks_dir = tmp_path / "chunks"

        _Cfg.chunks_dir.mkdir()
        (_Cfg.chunks_dir / "chunk_001.md").write_text("x", encoding="utf-8")
        vi = tmp_path / "chunk_001.md"
        assert resolve_source_pair(vi, None, _Cfg) == _Cfg.chunks_dir / "chunk_001.md"

    def test_resolve_source_pair_missing(self, tmp_path: Path):
        from scripts.fix import resolve_source_pair

        class _Cfg:
            chunks_dir = tmp_path / "chunks"

        _Cfg.chunks_dir.mkdir()
        vi = tmp_path / "chunk_001.md"
        assert resolve_source_pair(vi, None, _Cfg) is None


class TestEnsureStandaloneMarkers:
    """Edge cases for the marker-standalone restoration pass."""

    def test_unrelated_double_blank_line_survives(self):
        # Regression for #1: a blank-line pair far from the marker must not be
        # collapsed just because some marker is being protected.
        lines = ['Câu 1.\n', '\n', '\n', 'Câu 2.\n', '<!-- Page 9 -->\n', 'x\n']
        assert _ensure_standalone_markers(lines, {'9'}) == [
            'Câu 1.\n', '\n', '\n', 'Câu 2.\n',
            '\n', '<!-- Page 9 -->\n', '\n', 'x\n',
        ]

    def test_prefix_glued_marker_is_split_out(self):
        # Regression for #3: a marker glued mid-line must not be silently skipped.
        lines = ['Câu 2 trước đó <!-- Page 2 --> hết.\n']
        out = _ensure_standalone_markers(lines, {'2'})
        assert out == [
            'Câu 2 trước đó\n', '\n', '<!-- Page 2 -->\n', '\n', 'hết.\n',
        ]
        assert marker_boundaries(''.join(out)) == {'2': 'standalone'}

    def test_multiline_block_containing_marker(self):
        lines = ['line1\nline2 <!-- Page 9 --> line3\nline4\n']
        out = _ensure_standalone_markers(lines, {'9'})
        assert out == [
            'line1\nline2\n', '\n', '<!-- Page 9 -->\n', '\n', 'line3\nline4\n',
        ]
        assert marker_boundaries(''.join(out)) == {'9': 'standalone'}

    def test_adjacent_protected_markers_separated(self):
        # Regression for N1: two contiguous source-standalone markers must each
        # get their own blank-line block, not be emitted back-to-back.
        lines = ['a.\n', '<!-- Page 3 -->\n', '<!-- Page 4 -->\n', 'b.\n']
        out = _ensure_standalone_markers(lines, {'3', '4'})
        assert out == [
            'a.\n', '\n', '<!-- Page 3 -->\n', '\n', '<!-- Page 4 -->\n', '\n', 'b.\n',
        ]
        assert marker_boundaries(''.join(out)) == {'3': 'standalone', '4': 'standalone'}

    def test_adjacent_markers_is_idempotent(self):
        lines = ['a.\n', '<!-- Page 3 -->\n', '<!-- Page 4 -->\n', 'b.\n']
        first = _ensure_standalone_markers(lines, {'3', '4'})
        second = _ensure_standalone_markers(list(first), {'3', '4'})
        assert first == second

    def test_duplicate_page_number_both_forms_resolves_inline(self):
        # The module reports 'inline' when a page appears in both forms.
        text = (
            'a\n\n<!-- Page 9 -->\n\nb\n\nc\n<!-- Page 9 -->\nd\n'
        )
        assert marker_boundaries(text)['9'] == 'inline'

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "chunk.md"
        f.write_text("", encoding="utf-8")
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers={'9'})
        assert f.read_text(encoding="utf-8") == ""


class TestFixSentenceBreaksIdempotency:
    def test_second_run_is_identical(self, tmp_path: Path):
        f = tmp_path / "chunk.md"
        f.write_text(
            "Câu trước đó.\n<!-- Page 1 -->\ncâu sau continuation lowercase.\n",
            encoding="utf-8",
        )
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers={'1'})
        first = f.read_text(encoding="utf-8")
        fix_sentence_breaks(f, backup=False, preserve_standalone_markers={'1'})
        assert f.read_text(encoding="utf-8") == first


class TestCompareStructureExitCode:
    COMPARE_STRUCTURE = (
        PROJECT_ROOT / ".claude" / "skills" / "translating" / "scripts"
        / "compare-structure.py"
    )

    def _run(self, src_text: str, tr_text: str, tmp_path: Path, *extra: str):
        import subprocess

        src, tr = tmp_path / "src.md", tmp_path / "tr.md"
        src.write_text(src_text, encoding="utf-8")
        tr.write_text(tr_text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.COMPARE_STRUCTURE),
             "--source", str(src), "--translated", str(tr), *extra],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_exit_code_when_only_boundary_issues(self, tmp_path: Path):
        # Paragraph block counts match (5 each); only the marker boundary differs.
        src = "A\n\nB\n\n<!-- Page 5 -->\n\nC\n\nD\n"
        tr = "A\n\nB\n\n<!-- Page 5 -->\nline A line B.\n\nC\n\nD\n"
        assert marker_boundaries(src)['5'] == 'standalone'
        assert marker_boundaries(tr)['5'] == 'inline'
        result = self._run(src, tr, tmp_path)
        assert "Page-Marker Boundary Mismatches" in result.stdout
        assert "STRUCTURES MATCH" in result.stdout
        assert result.returncode == 1

    def test_exit_code_zero_when_structures_and_boundaries_match(self, tmp_path: Path):
        text = "Para one.\n\n<!-- Page 5 -->\n\nPara two.\n\nExtra.\n"
        result = self._run(text, text, tmp_path)
        assert "STRUCTURES MATCH" in result.stdout
        assert result.returncode == 0

    def test_ignore_boundary_exits_zero_on_boundary_only(self, tmp_path: Path):
        """Accept gate (runbook Rule 1a): residual marker mismatch is accepted."""
        src = "A\n\nB\n\n<!-- Page 5 -->\n\nC\n\nD\n"
        tr = "A\n\nB\n\n<!-- Page 5 -->\nline A line B.\n\nC\n\nD\n"
        result = self._run(src, tr, tmp_path, "--ignore-boundary")
        assert "Page-Marker Boundary Mismatches" in result.stdout  # still reported
        assert result.returncode == 0

    def test_ignore_boundary_still_fails_on_paragraph_mismatch(self, tmp_path: Path):
        result = self._run("A\n\nB\n\nC\n", "A\n\nB\n", tmp_path, "--ignore-boundary")
        assert result.returncode == 1
