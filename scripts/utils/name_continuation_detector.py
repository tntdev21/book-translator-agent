#!/usr/bin/env python3
"""
Name continuation detector for sentence break fixing.

This module provides smart detection for proper names that are split across lines,
using auto-extracted book-specific names from extract_proper_names.py.

Used by fix_sentence_breaks.py to improve detection of:
- Person names: "Alice" + "Chen"
- Location names: "Prague" + "Castle"
- Organization names: "Secret" + "Service"
- Title splits: "Kinh" + "Thánh"
"""

import json
import os
import re
from pathlib import Path
from typing import Set, Optional


class NameContinuationDetector:
    """Detects if a line break splits a proper name."""

    def __init__(self, names_db_path: Optional[Path] = None):
        """
        Initialize detector with book-specific names database.

        Args:
            names_db_path: Path to names JSON database (default: style/book_names.json)
        """
        if names_db_path is None:
            from .book_config import BookConfigError, load_book
            try:
                names_db_path = load_book().book_names_path
            except BookConfigError:
                # No active book (e.g. fresh clone): run without name knowledge.
                names_db_path = Path(os.devnull) / "book_names.json"

        self.individual_names: Set[str] = set()
        self.full_names: Set[str] = set()

        # Load database if exists
        if names_db_path.exists():
            self._load_database(names_db_path)
        else:
            # Use fallback patterns if database doesn't exist
            self._use_fallback_patterns()

    def _load_database(self, path: Path):
        """Load names from JSON database."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.individual_names = set(data.get('individual_names', []))
                self.full_names = set(data.get('full_names', {}).keys())
        except Exception as e:
            print(f"⚠️  Could not load names database: {e}")
            self._use_fallback_patterns()

    def _use_fallback_patterns(self):
        """No book-specific database → no name knowledge.

        Deliberately empty: guessing at a generic list of first names produces
        false joins on books whose characters those names don't belong to. The
        caller falls back to its own structural heuristics instead.
        """
        self.individual_names = set()

    def is_name_split(self, current_line: str, next_line: str) -> bool:
        """
        Check if line break splits a proper name.

        Args:
            current_line: Current line text
            next_line: Next line text

        Returns:
            True if this looks like a name split
        """
        current = current_line.strip()
        next_text = next_line.strip()

        if not current or not next_text:
            return False

        # Get last word from current line
        current_words = current.split()
        if not current_words:
            return False
        last_word = current_words[-1]

        # Get first word from next line
        next_words = next_text.split()
        if not next_words:
            return False
        first_word = next_words[0]

        # Pattern 1: Last word is a known first/last name
        if last_word in self.individual_names:
            # Check if next word is also capitalized (likely last name)
            if first_word and first_word[0].isupper():
                return True

        # Pattern 2: Capitalized + Capitalized (general proper noun)
        if (last_word and last_word[0].isupper() and
            first_word and first_word[0].isupper() and
            len(last_word) >= 3 and len(first_word) >= 3):
            # Both capitalized, likely proper noun continuation
            # Exclude common sentence starters
            SENTENCE_STARTERS = {
                'The', 'A', 'An', 'This', 'That', 'These', 'Those',
                'He', 'She', 'It', 'They', 'When', 'Where', 'What',
            }
            if first_word not in SENTENCE_STARTERS:
                return True

        # Pattern 3: Title + Name (Vietnamese patterns)
        # Example: "Tiến sĩ" + "Brigita Gessner"
        VIETNAMESE_TITLES = {
            'ông', 'bà', 'cô', 'anh', 'chị',
            'tiến sĩ', 'giáo sư', 'bác sĩ', 'kỹ sư',
        }
        if len(current_words) >= 2:
            last_two = ' '.join(current_words[-2:]).lower()
            if last_two in VIETNAMESE_TITLES:
                if first_word and first_word[0].isupper():
                    return True

        # Pattern 4: Very short last word (likely broken syllable/prefix)
        # Example: "th" + "ượng nghị sĩ"
        if len(last_word) <= 3 and last_word.isalpha():
            # Short word, could be broken Vietnamese word or English prefix
            return True

        # Pattern 5: Location/Building name patterns
        # Example: "Cầu" + "Mánesův", "Thư viện" + "Strahov"
        LOCATION_INDICATORS = {
            'cầu', 'đền', 'nhà thờ', 'thư viện', 'bảo tàng',
            'trung tâm', 'viện', 'bộ', 'cung điện', 'lâu đài',
        }
        if last_word.lower() in LOCATION_INDICATORS:
            if first_word and first_word[0].isupper():
                return True

        # Pattern 6: Title/Book name patterns
        # Example: "Kinh" + "Thánh", or a multi-word work title split across lines
        TITLE_WORDS = {'kinh', 'thánh', 'bộ', 'chương', 'the', 'a', 'an'}
        if last_word.lower() in TITLE_WORDS:
            if first_word and first_word[0].isupper():
                return True

        return False

    def get_name_database_stats(self) -> dict:
        """Get statistics about loaded name database."""
        return {
            'individual_names_count': len(self.individual_names),
            'full_names_count': len(self.full_names),
            'has_database': len(self.individual_names) > 20,  # Heuristic
        }


# Singleton instance for performance (load once)
_detector_instance: Optional[NameContinuationDetector] = None


def get_detector() -> NameContinuationDetector:
    """
    Get singleton instance of NameContinuationDetector.

    Returns:
        Shared detector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = NameContinuationDetector()
    return _detector_instance


def should_join_for_name(current_line: str, next_line: str) -> bool:
    """
    Convenience function to check if lines should be joined due to name split.

    Args:
        current_line: Current line text
        next_line: Next line text

    Returns:
        True if lines should be joined
    """
    detector = get_detector()
    return detector.is_name_split(current_line, next_line)
