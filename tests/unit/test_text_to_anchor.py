#!/usr/bin/env python3
"""Unit tests for text_to_anchor function"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from scripts.utils.markdown_converter import text_to_anchor


class TestTextToAnchor:
    """Test suite for text_to_anchor function"""

    def test_basic_conversion(self):
        """Verify basic text to anchor conversion"""
        result = text_to_anchor("Chapter 1")

        assert result == "chapter-1"
        assert result.islower()
        assert " " not in result

    def test_vietnamese_text(self):
        """Verify Vietnamese accent removal"""
        result = text_to_anchor("Lời cống hiến")

        assert result == "loi-cong-hien"
        # Verify no Vietnamese characters remain
        assert "ờ" not in result
        assert "ế" not in result

    def test_special_characters(self):
        """Verify special character removal"""
        result = text_to_anchor("Author's Note!?")

        assert result == "authors-note"
        assert "'" not in result
        assert "!" not in result
        assert "?" not in result

    def test_empty_string(self):
        """Verify empty string handling"""
        result = text_to_anchor("")

        assert result == ""
        assert isinstance(result, str)

    @pytest.mark.parametrize("input_text,expected", [
        ("Multiple   Spaces", "multiple-spaces"),
        ("Trailing-hyphens---", "trailing-hyphens"),
        ("---Leading-hyphens", "leading-hyphens"),
        ("MixedCASE", "mixedcase"),
        ("UPPERCASE", "uppercase"),
        ("123 Numbers", "123-numbers"),
        ("Chương 1", "chuong-1"),
        ("Đề từ", "de-tu"),
    ])
    def test_edge_cases(self, input_text, expected):
        """Test various edge cases with parametrization"""
        result = text_to_anchor(input_text)

        assert result == expected

    def test_unicode_normalization(self):
        """Verify Unicode normalization works"""
        # Test café with different Unicode representations
        result = text_to_anchor("café")

        assert result == "cafe"
        assert "é" not in result

    def test_very_long_text(self):
        """Verify long text handling"""
        long_text = "This is a very long chapter title with many words" * 10
        result = text_to_anchor(long_text)

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify multiple spaces collapsed to single hyphen
        assert "--" not in result
