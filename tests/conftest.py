#!/usr/bin/env python3
"""Shared pytest fixtures for all test sessions"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_chunks_dir(tmp_path):
    """
    Create temporary chunks directory with test files.

    Used by: chunk_loader tests, integration tests
    """
    chunks_dir = tmp_path / "translated"
    chunks_dir.mkdir()

    # Create 5 test chunk files
    for i in range(1, 6):
        chunk_file = chunks_dir / f"chunk_{i:03d}.md"
        content = f"""# Chapter {i}

This is test content for chunk {i}.

## Section {i}.1

Sample paragraph with some text.

## Section {i}.2

Another paragraph here.
"""
        chunk_file.write_text(content, encoding='utf-8')

    return chunks_dir


@pytest.fixture
def sample_toc_content():
    """
    Sample markdown content with TOC section.

    Used by: TOC conversion tests, integration tests
    """
    return """MỤC LỤC
Lời cống hiến
Đề từ
Lời nói đầu của tác giả
Chương 1
Chương 2
Chương 3


<!-- Page 12 -->

# Lời cống hiến

Dành tặng cho biên tập viên và người bạn thân nhất của tôi.


<!-- Page 13 -->

# Đề từ

Ngày khoa học bắt đầu nghiên cứu những hiện tượng phi vật chất.

—


<!-- Page 14 -->

# Lời nói đầu của tác giả

SỰ THẬT

Tất cả các tác phẩm nghệ thuật trong tiểu thuyết này đều có thật.


<!-- Page 15 -->

# CHƯƠNG 1

This is the first chapter content.


# CHƯƠNG 2

This is the second chapter content.


# CHƯƠNG 3

This is the third chapter content.
"""


@pytest.fixture
def sample_headings():
    """
    Sample set of existing headings for TOC link conversion.

    Used by: convert_toc_entry tests
    """
    return {
        "loi-cong-hien",
        "de-tu",
        "loi-noi-dau-cua-tac-gia",
        "chuong-1",
        "chuong-2",
        "chuong-3",
        "chapter-4",
        "chapter-5",
    }


@pytest.fixture
def expected_toc_links():
    """
    Expected TOC with clickable links.

    Used by: integration tests to verify conversion
    """
    return """MỤC LỤC
[Lời cống hiến](#loi-cong-hien)
[Đề từ](#de-tu)
[Lời nói đầu của tác giả](#loi-noi-dau-cua-tac-gia)
[Chương 1](#chuong-1)
[Chương 2](#chuong-2)
[Chương 3](#chuong-3)
"""


@pytest.fixture
def minimal_chunk():
    """
    Minimal valid chunk for basic tests.

    Used by: unit tests
    """
    return """# Test Chapter

This is minimal test content.
"""


@pytest.fixture
def chunk_with_vietnamese():
    """
    Chunk with Vietnamese content and special characters.

    Used by: anchor generation tests, Vietnamese handling tests
    """
    return """# Lời cống hiến

Dành tặng cho biên tập viên và người bạn thân nhất của tôi.

# Đề từ

Ngày khoa học bắt đầu nghiên cứu những hiện tượng phi vật chất, nó sẽ đạt được nhiều tiến bộ.
"""


@pytest.fixture
def invalid_utf8_file(tmp_path):
    """
    Create a file with invalid UTF-8 encoding.

    Used by: error handling tests
    """
    invalid_file = tmp_path / "invalid.md"
    # Write invalid UTF-8 bytes
    invalid_file.write_bytes(b'\xff\xfe Invalid UTF-8')
    return invalid_file


@pytest.fixture
def empty_chunks_dir(tmp_path):
    """
    Create an empty chunks directory (no files).

    Used by: error handling tests
    """
    chunks_dir = tmp_path / "empty_translated"
    chunks_dir.mkdir()
    return chunks_dir


@pytest.fixture
def complex_toc_content():
    """
    Complex TOC with multiple languages and edge cases.

    Used by: integration tests
    """
    return """TABLE OF CONTENTS
Dedication
Epigraph
Author's Note
Prologue
Chapter 1
Chapter 2
42
xiv
Chương 3
Chapitre 4


# Dedication

This is the dedication.

# Epigraph

This is the epigraph.

# CHAPTER 1

Chapter content here.
"""


# Helper functions

def load_fixture(filename):
    """
    Load a fixture file from tests/fixtures directory.

    Args:
        filename: Relative path from tests/fixtures/

    Returns:
        File contents as string
    """
    fixture_path = Path(__file__).parent / "fixtures" / filename
    return fixture_path.read_text(encoding='utf-8')


def create_temp_chunk(tmp_path, chunk_num, content):
    """
    Create a temporary chunk file for testing.

    Args:
        tmp_path: pytest tmp_path fixture
        chunk_num: Chunk number (int)
        content: Markdown content (str)

    Returns:
        Path to created chunk file
    """
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    chunk_file = chunks_dir / f"chunk_{chunk_num:03d}.md"
    chunk_file.write_text(content, encoding='utf-8')

    return chunk_file
