#!/usr/bin/env python3
"""Verify test fixtures are set up correctly"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_temp_chunks_dir_fixture(temp_chunks_dir):
    """Verify temp_chunks_dir fixture creates files"""
    assert temp_chunks_dir.exists()

    chunk_files = list(temp_chunks_dir.glob("chunk_*.md"))
    assert len(chunk_files) == 5

    # Check first chunk has content
    chunk_001 = temp_chunks_dir / "chunk_001.md"
    assert chunk_001.exists()
    content = chunk_001.read_text()
    assert "Chapter 1" in content


def test_sample_toc_content_fixture(sample_toc_content):
    """Verify sample_toc_content fixture"""
    assert "MỤC LỤC" in sample_toc_content
    assert "Lời cống hiến" in sample_toc_content
    assert "Chương 1" in sample_toc_content


def test_sample_headings_fixture(sample_headings):
    """Verify sample_headings fixture"""
    assert isinstance(sample_headings, set)
    assert "loi-cong-hien" in sample_headings
    assert "chuong-1" in sample_headings
    assert len(sample_headings) >= 5


def test_expected_toc_links_fixture(expected_toc_links):
    """Verify expected_toc_links fixture"""
    assert "MỤC LỤC" in expected_toc_links
    assert "[Lời cống hiến](#loi-cong-hien)" in expected_toc_links
    assert "[Chương 1](#chuong-1)" in expected_toc_links


def test_minimal_chunk_fixture(minimal_chunk):
    """Verify minimal_chunk fixture"""
    assert "# Test Chapter" in minimal_chunk
    assert len(minimal_chunk) > 0


def test_chunk_with_vietnamese_fixture(chunk_with_vietnamese):
    """Verify chunk_with_vietnamese fixture"""
    assert "# Lời cống hiến" in chunk_with_vietnamese
    assert "# Đề từ" in chunk_with_vietnamese


def test_invalid_utf8_file_fixture(invalid_utf8_file):
    """Verify invalid_utf8_file fixture creates invalid file"""
    assert invalid_utf8_file.exists()
    # Reading as bytes should work
    content = invalid_utf8_file.read_bytes()
    assert len(content) > 0


def test_empty_chunks_dir_fixture(empty_chunks_dir):
    """Verify empty_chunks_dir fixture creates empty directory"""
    assert empty_chunks_dir.exists()
    assert empty_chunks_dir.is_dir()
    # Should have no markdown files
    chunk_files = list(empty_chunks_dir.glob("*.md"))
    assert len(chunk_files) == 0


def test_complex_toc_content_fixture(complex_toc_content):
    """Verify complex_toc_content fixture"""
    assert "TABLE OF CONTENTS" in complex_toc_content
    assert "Dedication" in complex_toc_content
    assert "Chapter 1" in complex_toc_content
    assert "Chương 3" in complex_toc_content
