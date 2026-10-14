#!/usr/bin/env python3
"""Unit tests for convert_toc_entry_to_link function"""

import pytest
from scripts.utils.markdown_converter import convert_toc_entry_to_link


class TestConvertTocEntryToLink:
    """Test suite for convert_toc_entry_to_link function"""

    def test_convert_chapter(self):
        """Verify chapter entry conversion to link"""
        # All chapter patterns use chuong-{number} anchor format
        existing_headings = {"chuong-1", "chuong-2", "chuong-3"}

        # Vietnamese chapter format
        result = convert_toc_entry_to_link("Chương 1", existing_headings)
        assert result == "[Chương 1](#chuong-1)"

        # Uppercase Vietnamese
        result = convert_toc_entry_to_link("CHƯƠNG 2", existing_headings)
        assert result == "[CHƯƠNG 2](#chuong-2)"

        # English chapter format (also uses chuong- anchor)
        result = convert_toc_entry_to_link("Chapter 3", existing_headings)
        assert result == "[Chapter 3](#chuong-3)"

    def test_convert_section(self):
        """Verify section entry conversion to link"""
        # Note: Đ/đ is converted to d (đầu -> dau, Đề -> de)
        existing_headings = {"loi-cong-hien", "de-tu", "loi-noi-dau-cua-tac-gia"}

        # Vietnamese section
        result = convert_toc_entry_to_link("Lời cống hiến", existing_headings)
        assert result == "[Lời cống hiến](#loi-cong-hien)"

        # Another section - Đ becomes d when normalized
        result = convert_toc_entry_to_link("Đề từ", existing_headings)
        assert result == "[Đề từ](#de-tu)"

        # Longer section name - đầu becomes "dau"
        result = convert_toc_entry_to_link("Lời nói đầu của tác giả", existing_headings)
        assert result == "[Lời nói đầu của tác giả](#loi-noi-dau-cua-tac-gia)"

    def test_convert_missing_heading(self):
        """Verify None returned when heading doesn't exist"""
        existing_headings = {"chuong-1", "chuong-2"}

        # Chapter not in existing headings
        result = convert_toc_entry_to_link("Chương 999", existing_headings)
        assert result is None

        # Section not in existing headings
        result = convert_toc_entry_to_link("Nonexistent Section", existing_headings)
        assert result is None

    def test_skip_page_number(self):
        """Verify page numbers are skipped (return None)"""
        existing_headings = {"chuong-1"}

        # Digit-only lines should return None
        assert convert_toc_entry_to_link("42", existing_headings) is None
        assert convert_toc_entry_to_link("123", existing_headings) is None
        assert convert_toc_entry_to_link("1", existing_headings) is None

    def test_skip_roman_numerals(self):
        """Verify roman numeral page numbers are skipped"""
        existing_headings = {"chuong-1"}

        # Roman numerals should return None
        assert convert_toc_entry_to_link("xiv", existing_headings) is None
        assert convert_toc_entry_to_link("XIV", existing_headings) is None
        assert convert_toc_entry_to_link("iii", existing_headings) is None
        assert convert_toc_entry_to_link("IX", existing_headings) is None
        assert convert_toc_entry_to_link("MMXXIII", existing_headings) is None

    def test_skip_short_empty(self):
        """Verify short and empty lines are skipped"""
        existing_headings = {"chuong-1"}

        # Empty string
        assert convert_toc_entry_to_link("", existing_headings) is None

        # Very short (1 char)
        assert convert_toc_entry_to_link("a", existing_headings) is None

    @pytest.mark.parametrize("entry,headings,expected", [
        ("Chương 1", {"chuong-1"}, "[Chương 1](#chuong-1)"),
        ("Chapter 5", {"chuong-5"}, "[Chapter 5](#chuong-5)"),  # Chapter patterns use chuong- anchor
        ("Lời cống hiến", {"loi-cong-hien"}, "[Lời cống hiến](#loi-cong-hien)"),
        ("Chương 999", {"chuong-1"}, None),  # Missing
        ("42", {"chuong-1"}, None),  # Page number
        ("xiv", {"chuong-1"}, None),  # Roman numeral
        ("", {"chuong-1"}, None),  # Empty
        ("a", {"chuong-1"}, None),  # Too short
    ])
    def test_various_entries(self, entry, headings, expected):
        """Test various TOC entries with parametrization"""
        result = convert_toc_entry_to_link(entry, headings)
        assert result == expected

    def test_multilingual_chapters(self):
        """Test support for multiple chapter formats"""
        existing_headings = {
            "chuong-1", "chuong-2", "chuong-3", "chuong-4", "chuong-5"
        }

        # Vietnamese
        result = convert_toc_entry_to_link("Chương 1", existing_headings)
        assert result == "[Chương 1](#chuong-1)"

        # English
        result = convert_toc_entry_to_link("Chapter 2", existing_headings)
        assert result == "[Chapter 2](#chuong-2)"

        # French
        result = convert_toc_entry_to_link("Chapitre 3", existing_headings)
        assert result == "[Chapitre 3](#chuong-3)"

        # Spanish
        result = convert_toc_entry_to_link("Capítulo 4", existing_headings)
        assert result == "[Capítulo 4](#chuong-4)"

        # Italian
        result = convert_toc_entry_to_link("Capitolo 5", existing_headings)
        assert result == "[Capitolo 5](#chuong-5)"
