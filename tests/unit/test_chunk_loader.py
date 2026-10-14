#!/usr/bin/env python3
"""Unit tests for chunk_loader module"""

import pytest
from pathlib import Path
from scripts.utils.chunk_loader import load_chunks


@pytest.fixture
def temp_chunks_dir(tmp_path):
    """Create temporary chunks directory with test files"""
    chunks_dir = tmp_path / "translated"
    chunks_dir.mkdir()

    # Create 5 test chunk files
    for i in range(1, 6):
        chunk_file = chunks_dir / f"chunk_{i:03d}.md"
        chunk_file.write_text(f"# Chapter {i}\n\nTest content for chunk {i}")

    return chunks_dir


class TestLoadChunks:
    """Test suite for load_chunks function"""

    def test_load_chunks_test_mode(self, temp_chunks_dir):
        """Verify test mode loads only chunk_001.md"""
        files, suffix, mode = load_chunks(
            test=True,
            chunks=None,
            translated_dir=temp_chunks_dir
        )

        assert len(files) == 1
        assert files[0].name == "chunk_001.md"
        assert suffix == "_test"
        assert "Test" in mode

    def test_load_chunks_range_valid(self, temp_chunks_dir):
        """Verify range parsing works correctly"""
        files, suffix, mode = load_chunks(
            test=False,
            chunks="1-3",
            translated_dir=temp_chunks_dir
        )

        assert len(files) == 3
        assert files[0].name == "chunk_001.md"
        assert files[1].name == "chunk_002.md"
        assert files[2].name == "chunk_003.md"
        assert "_chunks_1_3" in suffix

    def test_load_chunks_range_invalid_format(self, temp_chunks_dir):
        """Verify error on malformed range like '1-abc'"""
        with pytest.raises(ValueError) as exc_info:
            load_chunks(
                test=False,
                chunks="1-abc",
                translated_dir=temp_chunks_dir
            )

        assert "Invalid chunk specification" in str(exc_info.value)

    def test_load_chunks_range_invalid_order(self, temp_chunks_dir):
        """Verify error when start > end"""
        with pytest.raises(ValueError) as exc_info:
            load_chunks(
                test=False,
                chunks="5-1",
                translated_dir=temp_chunks_dir
            )

        assert "start <= end" in str(exc_info.value)

    def test_load_chunks_list_valid(self, temp_chunks_dir):
        """Verify comma-separated list parsing"""
        files, suffix, mode = load_chunks(
            test=False,
            chunks="1,3,5",
            translated_dir=temp_chunks_dir
        )

        assert len(files) == 3
        assert files[0].name == "chunk_001.md"
        assert files[1].name == "chunk_003.md"
        assert files[2].name == "chunk_005.md"

    def test_load_chunks_missing_file(self, temp_chunks_dir):
        """Verify error when chunk file doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_chunks(
                test=False,
                chunks="999",
                translated_dir=temp_chunks_dir
            )

        assert "chunk_999.md" in str(exc_info.value)

    def test_load_chunks_missing_directory(self):
        """Verify error when translated directory doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_chunks(
                test=False,
                chunks=None,
                translated_dir=Path("nonexistent_directory")
            )

        assert "not found" in str(exc_info.value).lower()

    def test_load_chunks_full_book_mode(self, temp_chunks_dir):
        """Verify full book mode loads all chunks"""
        files, suffix, mode = load_chunks(
            test=False,
            chunks=None,
            translated_dir=temp_chunks_dir
        )

        assert len(files) == 5
        assert suffix == ""
        assert mode == "Full Book"
        assert all(f.name.startswith("chunk_") for f in files)

    def test_load_chunks_default_translated_dir(self, temp_chunks_dir, monkeypatch):
        """Verify the active book's translated dir is used when none is given"""
        # load_chunks resolves the default from the active book; stub the
        # resolver so the test doesn't depend on the repo's books/ contents.
        # chunk_loader imports load_book by value, so patch it there.
        from scripts.utils import chunk_loader

        class _Cfg:
            translated_dir = temp_chunks_dir

        monkeypatch.setattr(chunk_loader, "load_book", lambda book_id=None: _Cfg())

        files, suffix, mode = load_chunks(
            test=True,
            chunks=None,
            translated_dir=None  # Should resolve to the active book's dir
        )

        assert len(files) == 1
        assert files[0].name == "chunk_001.md"

    def test_load_chunks_test_mode_missing_chunk(self, tmp_path):
        """Verify error when chunk_001.md doesn't exist in test mode"""
        chunks_dir = tmp_path / "translated"
        chunks_dir.mkdir()

        # Don't create chunk_001.md
        with pytest.raises(FileNotFoundError) as exc_info:
            load_chunks(
                test=True,
                chunks=None,
                translated_dir=chunks_dir
            )

        assert "chunk_001.md" in str(exc_info.value)

    def test_load_chunks_range_multiple_parts_invalid(self, temp_chunks_dir):
        """Verify error on range with multiple dashes like '1-2-3'"""
        with pytest.raises(ValueError) as exc_info:
            load_chunks(
                test=False,
                chunks="1-2-3",
                translated_dir=temp_chunks_dir
            )

        assert "Invalid" in str(exc_info.value)

    def test_load_chunks_range_missing_chunk_file(self, temp_chunks_dir):
        """Verify error when chunk file in range doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_chunks(
                test=False,
                chunks="1-10",  # chunk_010.md doesn't exist
                translated_dir=temp_chunks_dir
            )

        assert "chunk_" in str(exc_info.value)

    def test_load_chunks_full_book_empty_directory(self, tmp_path):
        """Verify error when no chunks found in full book mode"""
        chunks_dir = tmp_path / "translated"
        chunks_dir.mkdir()

        # Don't create any chunk files
        with pytest.raises(FileNotFoundError) as exc_info:
            load_chunks(
                test=False,
                chunks=None,
                translated_dir=chunks_dir
            )

        assert "No translated files found" in str(exc_info.value)
