#!/usr/bin/env python3
"""Unit tests for is_toc_end function"""

import pytest
from scripts.utils.markdown_converter import is_toc_end


class TestIsTocEnd:
    """Test suite for is_toc_end function"""

    def test_not_in_toc(self):
        """Verify returns False when not in TOC"""
        # Should always return False if not in TOC
        assert is_toc_end("", 3, False) == False
        assert is_toc_end("# Heading", 0, False) == False
        assert is_toc_end("Long body text that would normally end TOC", 0, False) == False

    def test_toc_end_blank_lines(self):
        """Verify 3+ consecutive blank lines end TOC"""
        # Should NOT end with 2 blank lines
        assert is_toc_end("", 2, True) == False

        # Should end with 3 blank lines
        assert is_toc_end("", 3, True) == True

        # Should end with 4+ blank lines
        assert is_toc_end("", 5, True) == True

    def test_toc_end_markdown_heading(self):
        """Verify markdown heading marks end of TOC"""
        # H1 heading should end TOC
        assert is_toc_end("# Chapter 1", 0, True) == True

        # H2 heading should end TOC
        assert is_toc_end("## Subsection", 0, True) == True

        # H3 heading should end TOC
        assert is_toc_end("### Sub-subsection", 0, True) == True

        # Not a heading
        assert is_toc_end("Regular text", 0, True) == False

    def test_toc_end_body_text(self):
        """Verify long body text ends TOC"""
        # Long paragraph (>30 chars) should end TOC
        long_text = "Dành tặng cho biên tập viên và người bạn thân nhất"
        assert is_toc_end(long_text, 0, True) == True

        # Another trigger phrase
        long_text2 = "Ngày khoa học bắt đầu nghiên cứu những hiện tượng"
        assert is_toc_end(long_text2, 0, True) == True

        # Long uppercase (>50 chars) should end TOC
        uppercase_text = "THIS IS A VERY LONG CHAPTER TITLE THAT EXCEEDS FIFTY CHARACTERS EASILY"
        assert is_toc_end(uppercase_text, 0, True) == True

        # Short uppercase (<=50 chars) should NOT end TOC
        short_uppercase = "SHORT TITLE HERE"
        assert is_toc_end(short_uppercase, 0, True) == False

        # Short text should NOT end TOC
        assert is_toc_end("Short text", 0, True) == False

        # Chapter entries should NOT end TOC
        assert is_toc_end("Chương 1", 0, True) == False
        assert is_toc_end("Chapter 5", 0, True) == False

        # Long text starting with lowercase should NOT end TOC
        lowercase_text = "this is a long text starting with lowercase character here"
        assert is_toc_end(lowercase_text, 0, True) == False

    def test_toc_end_page_marker(self):
        """Verify page markers don't end TOC"""
        # Page comment should NOT end TOC
        assert is_toc_end("<!-- Page 5 -->", 0, True) == False

        # Alternative page format
        assert is_toc_end("<!- - - Page 10 -->", 0, True) == False

        # Page marker with blank lines should also not end
        assert is_toc_end("<!-- Page 1 -->", 2, True) == False

    def test_toc_end_trigger_phrases(self):
        """Verify specific trigger phrases end TOC"""
        # "Dành tặng cho" prefix
        assert is_toc_end("Dành tặng cho tất cả mọi người", 0, True) == True

        # "Ngày khoa học" prefix
        assert is_toc_end("Ngày khoa học phát triển mạnh mẽ", 0, True) == True

        # Partial match should NOT trigger
        assert is_toc_end("Xin Dành tặng cho", 0, True) == False

    def test_toc_end_edge_cases(self):
        """Verify edge cases and boundary conditions"""
        # Empty string with no blank lines
        assert is_toc_end("", 0, True) == False

        # Exactly 30 chars (boundary for body text detection)
        text_30 = "A" * 30
        assert is_toc_end(text_30, 0, True) == False

        # Exactly 31 chars uppercase (triggers body text condition: len > 30 and first char is upper)
        text_31 = "A" * 31
        assert is_toc_end(text_31, 0, True) == True

        # Exactly 50 chars uppercase (triggers body text condition: len > 30)
        text_50_upper = "A" * 50
        assert is_toc_end(text_50_upper, 0, True) == True

        # Exactly 51 chars uppercase (triggers both conditions)
        text_51_upper = "A" * 51
        assert is_toc_end(text_51_upper, 0, True) == True

        # 30 chars lowercase should NOT end TOC
        text_30_lower = "a" * 30
        assert is_toc_end(text_30_lower, 0, True) == False

        # 31 chars lowercase should NOT end TOC (no uppercase first char)
        text_31_lower = "a" * 31
        assert is_toc_end(text_31_lower, 0, True) == False

    @pytest.mark.parametrize("stripped,blank_count,in_toc,expected", [
        ("", 3, True, True),           # 3 blank lines
        ("", 2, True, False),          # 2 blank lines (not enough)
        ("# Heading", 0, True, True),  # Markdown heading
        ("Chương 1", 0, True, False),  # TOC entry
        ("", 5, False, False),         # Not in TOC
        ("<!-- Page 5 -->", 0, True, False),  # Page marker
        ("Dành tặng cho ai đó", 0, True, True),  # Trigger phrase
        ("VERY LONG UPPERCASE TEXT THAT IS MORE THAN FIFTY CHARACTERS LONG", 0, True, True),  # Long uppercase
        ("Short", 0, True, False),  # Short text
    ])
    def test_various_conditions(self, stripped, blank_count, in_toc, expected):
        """Test various conditions with parametrization"""
        result = is_toc_end(stripped, blank_count, in_toc)
        assert result == expected
