#!/usr/bin/env python3
"""Unit tests for fix_sentence_breaks module"""

import pytest
from pathlib import Path
from scripts.utils.fix_sentence_breaks import fix_sentence_breaks


class TestFixSentenceBreaks:
    """Test suite for fix_sentence_breaks function"""

    def test_fix_sentence_breaks_basic(self, tmp_path: Path) -> None:
        """Test joining broken sentences."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This is a\nbroken sentence.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "This is a broken sentence." in content
        assert "\nbroken" not in content

    def test_fix_sentence_breaks_preserve_paragraphs(self, tmp_path: Path) -> None:
        """Test that paragraph breaks are preserved."""
        test_file = tmp_path / "test.md"
        content = """This is paragraph one.

This is paragraph two.

This is paragraph three."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        # No fixes should be made since paragraphs are proper
        assert fixes == 0
        result = test_file.read_text()
        assert result == content

    def test_fix_sentence_breaks_vietnamese(self, tmp_path: Path) -> None:
        """Test Vietnamese lowercase joining."""
        test_file = tmp_path / "test.md"
        # "tôi" is pronoun, should join with next line and lowercase next char
        test_file.write_text("Ông ấy nói với\ntôi\nĐang đi đâu đấy?")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        # Should join all lines
        assert "tôi" in content

    def test_fix_sentence_breaks_dialogue(self, tmp_path: Path) -> None:
        """Test dialogue attribution handling."""
        test_file = tmp_path / "test.md"
        # Line ending with dash should join with next line (dialogue attribution)
        test_file.write_text('"Anh có khỏe không?" -\nAnh ấy hỏi.')

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        # Should join the two lines
        assert "?" in content and "hỏi" in content

    def test_fix_sentence_breaks_max_passes(self, tmp_path: Path) -> None:
        """Test max passes prevents infinite loops."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This\nis\na\nsentence\nbroken\nacross\nmany\nlines.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "This is a sentence broken across many lines." in content

    def test_fix_sentence_breaks_no_changes(self, tmp_path: Path) -> None:
        """Test no changes when content is clean."""
        test_file = tmp_path / "test.md"
        content = """# Chapter 1

This is a proper sentence.

Another proper sentence here.

Yet another one."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 0
        result = test_file.read_text()
        assert result == content

    def test_fix_sentence_breaks_multiple_broken_sequences(self, tmp_path: Path) -> None:
        """Test multiple broken sentences in sequence."""
        test_file = tmp_path / "test.md"
        content = """This is the
first broken sentence.

This is the
second broken
sentence.

This is proper."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes >= 3
        result = test_file.read_text()
        assert "first broken sentence" in result
        assert "second broken sentence" in result

    def test_fix_sentence_breaks_vietnamese_articles(self, tmp_path: Path) -> None:
        """Test Vietnamese articles trigger joining."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Đây là một\nVí dụ hay.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "một ví dụ" in content.lower()

    def test_fix_sentence_breaks_does_not_cross_blank_block_boundary(
        self, tmp_path: Path
    ) -> None:
        """Blank lines separate source-preserved blocks and cannot be joined across."""
        test_file = tmp_path / "test.md"
        content = "Đây là một\n\nVí dụ ở block tiếp theo.\n"
        test_file.write_text(content, encoding="utf-8")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 0
        assert test_file.read_text(encoding="utf-8") == content

    def test_fix_sentence_breaks_traverses_comment_within_block(
        self, tmp_path: Path
    ) -> None:
        """Non-page comments do not prevent joins inside one block."""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            "Đây là một\n<!-- translator note -->\nVí dụ hay.\n",
            encoding="utf-8",
        )

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 1
        assert test_file.read_text(encoding="utf-8") == (
            "Đây là một Ví dụ hay.\n<!-- translator note -->\n"
        )

    def test_fix_sentence_breaks_vietnamese_prepositions(self, tmp_path: Path) -> None:
        """Test Vietnamese prepositions trigger joining."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Anh ấy sống ở\nPrague.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "ở prague" in content.lower()

    def test_fix_sentence_breaks_preserve_headings(self, tmp_path: Path) -> None:
        """Test markdown headings are preserved."""
        test_file = tmp_path / "test.md"
        content = """# Chapter 1

This is a broken
sentence.

## Section 1

Another broken
sentence."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes >= 2
        result = test_file.read_text()
        assert "# Chapter 1" in result
        assert "## Section 1" in result

    def test_fix_sentence_breaks_preserve_markdown_lists(self, tmp_path: Path) -> None:
        """Test markdown lists are preserved."""
        test_file = tmp_path / "test.md"
        content = """Regular text.

- List item one
- List item two

More text."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 0
        result = test_file.read_text()
        assert "- List item one" in result
        # Regression: the list items used to be joined into one paragraph,
        # turning "- a\n- b" into "- a - b" and destroying the list.
        assert result == content
        assert "- List item one - List item two" not in result

    def test_lone_dash_line_still_treated_as_dialogue(self, tmp_path: Path) -> None:
        """A single '- ' line in prose is dialogue, not a list, so it still joins."""
        test_file = tmp_path / "test.md"
        test_file.write_text("- Cậu\nkhỏe không?", encoding="utf-8")

        fix_sentence_breaks(test_file, backup=False)

        result = test_file.read_text(encoding="utf-8")
        assert result.strip() == "- Cậu khỏe không?"

    def test_fix_sentence_breaks_backup_creation(self, tmp_path: Path) -> None:
        """Test backup file is created when backup=True."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This is a\nbroken sentence.")
        backup_file = Path(str(test_file) + '.bak')

        fixes = fix_sentence_breaks(test_file, backup=True)

        assert fixes > 0
        assert backup_file.exists()
        backup_content = backup_file.read_text()
        assert "This is a\nbroken sentence." in backup_content

    def test_fix_sentence_breaks_no_backup_creation(self, tmp_path: Path) -> None:
        """Test backup file is not created when backup=False."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This is a\nbroken sentence.")
        backup_file = Path(str(test_file) + '.bak')

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        assert not backup_file.exists()

    def test_fix_sentence_breaks_comma_continuation(self, tmp_path: Path) -> None:
        """Test sentences ending with comma are joined."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This is a sentence with a comma,\nAnd it continues here.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "comma, and it continues" in content.lower()

    def test_fix_sentence_breaks_short_words(self, tmp_path: Path) -> None:
        """Test very short broken words are joined."""
        test_file = tmp_path / "test.md"
        test_file.write_text("This is\na\ntest.")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        content = test_file.read_text()
        assert "This is a test." in content

    def test_fix_sentence_breaks_empty_file(self, tmp_path: Path) -> None:
        """Test empty file returns zero fixes."""
        test_file = tmp_path / "test.md"
        test_file.write_text("")

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 0

    def test_fix_sentence_breaks_encoding_utf8(self, tmp_path: Path) -> None:
        """Test UTF-8 encoding is preserved."""
        test_file = tmp_path / "test.md"
        content = "Đây là một câu bị\nvỡ với nhiều ký tự: àáảãạăằắẳẵặâầấẩẫậ."
        test_file.write_text(content, encoding='utf-8')

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes > 0
        result = test_file.read_text(encoding='utf-8')
        assert "àáảãạăằắẳẵặâầấẩẫậ" in result

    def test_fix_sentence_breaks_return_value(self, tmp_path: Path) -> None:
        """Test return value accurately reflects number of fixes."""
        test_file = tmp_path / "test.md"
        content = """Line one is
broken here.

Line two is
also broken."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes == 2

    def test_fix_sentence_breaks_preserve_comments(self, tmp_path: Path) -> None:
        """Test HTML comments are preserved."""
        test_file = tmp_path / "test.md"
        content = """<!-- Page 1 -->

This is a broken
sentence.

<!-- Page 2 -->

Another sentence."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        assert fixes >= 1
        result = test_file.read_text()
        assert "<!-- Page 1 -->" in result

    def test_fix_sentence_breaks_preserve_blockquotes(self, tmp_path: Path) -> None:
        """Test blockquotes are preserved."""
        test_file = tmp_path / "test.md"
        content = """> This is a quote.

Regular text here."""
        test_file.write_text(content)

        fixes = fix_sentence_breaks(test_file, backup=False)

        result = test_file.read_text()
        assert "> This is a quote." in result
