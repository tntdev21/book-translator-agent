#!/usr/bin/env python3
"""Unit tests for scan_existing_headings function"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from scripts.utils.markdown_converter import scan_existing_headings


class TestScanExistingHeadings:
    """Test suite for scan_existing_headings function"""

    def test_scan_markdown_headings(self):
        """Verify detection of markdown headings (# syntax)"""
        lines = [
            "# Lời cống hiến",
            "Some content here",
            "## Chapter 1",
            "More content",
            "### Subsection",
            "",
            "# Đề từ",
        ]

        result = scan_existing_headings(lines)

        # Should detect all markdown headings
        assert "loi-cong-hien" in result
        assert "chapter-1" in result
        assert "subsection" in result
        assert "de-tu" in result
        assert len(result) == 4

    def test_scan_uppercase_headings(self):
        """Verify detection of uppercase chapter headings"""
        lines = [
            "CHƯƠNG 1",
            "Content here",
            "",
            "CHƯƠNG 2",
            "More content",
            "",
            "CHAPTER 3",  # English format (must be uppercase)
            "Content",
        ]

        result = scan_existing_headings(lines)

        # Should detect chapter numbers
        assert "chuong-1" in result
        assert "chuong-2" in result
        assert "chuong-3" in result
        assert len(result) == 3

    def test_scan_special_sections(self):
        """Verify detection of special sections (SPECIAL_SECTIONS mapping)"""
        lines = [
            "Lời cống hiến",
            "Prologue content here",
            "",
            "Regular content",
            "",
            "CHƯƠNG 1",
        ]

        result = scan_existing_headings(lines)

        # Should detect special section mapped to 'loi-cong-hien'
        assert "loi-cong-hien" in result
        # Should also detect the chapter
        assert "chuong-1" in result
        assert len(result) == 2

    def test_scan_mixed_content(self):
        """Verify scanning mixed markdown, uppercase, and special sections"""
        lines = [
            "# Lời nói đầu",
            "Content",
            "",
            "CHƯƠNG 1",
            "Chapter content",
            "",
            "## Section 1.1",
            "More content",
            "",
            "Đề từ",
        ]

        result = scan_existing_headings(lines)

        # Should detect all types
        assert "loi-noi-dau" in result
        assert "chuong-1" in result
        # Note: text_to_anchor removes periods, so "1.1" becomes "11"
        assert "section-11" in result
        assert "de-tu" in result
        assert len(result) == 4

    def test_scan_empty_lines(self):
        """Verify handling of empty input"""
        lines = []

        result = scan_existing_headings(lines)

        assert result == set()
        assert len(result) == 0

    def test_scan_no_headings(self):
        """Verify behavior when no headings present"""
        lines = [
            "Just regular text",
            "No headings here",
            "More text",
        ]

        result = scan_existing_headings(lines)

        assert result == set()

    def test_scan_returns_set(self):
        """Verify function returns set, not list"""
        lines = ["# Test"]

        result = scan_existing_headings(lines)

        assert isinstance(result, set)

    def test_scan_all_special_sections(self):
        """Verify all SPECIAL_SECTIONS are detected correctly"""
        lines = [
            "Lời cống hiến",
            "",
            "Đề từ",
            "",
            "Lời nói đầu của tác giả",
        ]

        result = scan_existing_headings(lines)

        # All special sections should be detected
        assert "loi-cong-hien" in result
        assert "de-tu" in result
        assert "loi-noi-dau-cua-tac-gia" in result
        assert len(result) == 3

    def test_scan_chapter_case_insensitive(self):
        """Verify chapter detection with regex (case-insensitive when uppercase condition met)"""
        lines = [
            "CHƯƠNG 1",     # Uppercase with CHƯƠNG prefix
            "CHAPTER 2",    # Uppercase English format
            "CHƯƠNG 3",     # Uppercase Vietnamese format
        ]

        result = scan_existing_headings(lines)

        # All should be detected as chapters
        assert "chuong-1" in result
        assert "chuong-2" in result
        assert "chuong-3" in result
        assert len(result) == 3

    def test_scan_lowercase_chapter_not_detected(self):
        """Verify lowercase chapter headings not detected by uppercase logic"""
        lines = [
            "Chương 1",     # Not uppercase
            "Chapter 2",    # Not uppercase
        ]

        result = scan_existing_headings(lines)

        # These won't be detected as chapters because they're not uppercase
        # They would need to be markdown headings (# Chương 1) to be detected
        assert len(result) == 0

    def test_scan_whitespace_handling(self):
        """Verify proper handling of leading/trailing whitespace"""
        lines = [
            "  # Test Heading  ",
            "   CHƯƠNG 1   ",
            "  Lời cống hiến  ",
        ]

        result = scan_existing_headings(lines)

        assert "test-heading" in result
        assert "chuong-1" in result
        assert "loi-cong-hien" in result
        assert len(result) == 3

    def test_scan_duplicate_headings(self):
        """Verify duplicates are handled (set should contain unique values)"""
        lines = [
            "# Test",
            "Content",
            "# Test",
            "",
            "CHƯƠNG 1",
            "More content",
            "CHƯƠNG 1",
        ]

        result = scan_existing_headings(lines)

        # Set should only contain unique values
        assert "test" in result
        assert "chuong-1" in result
        assert len(result) == 2

    def test_scan_multiple_hash_levels(self):
        """Verify detection of different heading levels"""
        lines = [
            "# Level 1",
            "## Level 2",
            "### Level 3",
            "#### Level 4",
            "##### Level 5",
            "###### Level 6",
        ]

        result = scan_existing_headings(lines)

        assert "level-1" in result
        assert "level-2" in result
        assert "level-3" in result
        assert "level-4" in result
        assert "level-5" in result
        assert "level-6" in result
        assert len(result) == 6

    def test_scan_uppercase_non_chapter(self):
        """Verify uppercase text that isn't a chapter"""
        lines = [
            "HELLO WORLD",
            "ANOTHER UPPERCASE LINE",
        ]

        result = scan_existing_headings(lines)

        # Should still detect uppercase as headings
        assert "hello-world" in result
        assert "another-uppercase-line" in result
        assert len(result) == 2
