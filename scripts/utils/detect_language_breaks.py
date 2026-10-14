#!/usr/bin/env python3
"""
Detect and prevent false-positive sentence joins for language names and proper nouns.

Prevents joins like:
- "thầy giáo tiếng" + "Anh trường..." → should NOT join (tiếng Anh is complete)
- "<Name> liếc nhìn" + "<Name2>, ánh mắt..." → should NOT join (new sentence subject)
"""

import json
import re
from typing import List, Set, Tuple


# Language names in Vietnamese that start with capital letters
VIETNAMESE_LANGUAGE_NAMES = {
    'Anh',      # English
    'Việt',     # Vietnamese
    'Pháp',     # French
    'Đức',      # German
    'Nga',      # Russian
    'Trung',    # Chinese
    'Nhật',     # Japanese
    'Hàn',      # Korean
    'Ý',        # Italian
    'Tây Ban Nha',  # Spanish
    'Bồ Đào Nha',   # Portuguese
    'Ả Rập',    # Arabic
    'Thổ Nhĩ Kỳ',   # Turkish
    'Hy Lạp',   # Greek
    'La Tinh',  # Latin
    'Sanskrit', # Sanskrit
    'Hebrew',   # Hebrew
}


def load_book_proper_nouns() -> Set[str]:
    """
    Load proper nouns from the active book's ``style/book_names.json``.

    Returns an empty set when no database exists, which disables the
    proper-noun sentence-start heuristic rather than guessing at names.
    """
    try:
        from .book_config import load_book
        names_path = load_book().book_names_path
    except (Exception, SystemExit):  # BookConfigError subclasses SystemExit
        return set()

    if not names_path.exists():
        return set()

    try:
        data = json.loads(names_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return set()

    return set(data.get('full_names', {})) | set(data.get('individual_names', []))


# Words that commonly precede language names
LANGUAGE_PRECURSORS = {
    'tiếng',        # tiếng Anh (English language)
    'người',        # người Pháp (French people)
    'nước',         # nước Đức (Germany)
    'văn',          # văn Nga (Russian literature)
    'ngôn ngữ',     # ngôn ngữ Trung (Chinese language)
    'giọng',        # giọng Nga (Russian accent)
    'dân tộc',      # dân tộc Pháp (French nationality)
    'quốc gia',     # quốc gia Đức (Germany as country)
}


# Common Vietnamese nouns that precede proper nouns (should not join)
PROPER_NOUN_PRECURSORS = {
    'ông', 'bà', 'anh', 'chị', 'em', 'cô',  # titles
    'giáo sư', 'tiến sĩ', 'bác sĩ',  # academic titles
    'thầy', 'cô giáo',  # teacher titles
}


def is_language_name_boundary(current_line: str, next_line: str) -> bool:
    """
    Check if the boundary between two lines is a language name that should NOT be joined.

    Examples that should return True (do NOT join):
    - current: "thầy giáo tiếng"
      next: "Anh trường trung học"
      → "tiếng Anh" is complete, don't join with "trường trung học"

    Returns:
        True if this is a language name boundary that should be preserved
    """
    current_stripped = current_line.strip().lower()
    next_stripped = next_line.strip()

    # Check if next line starts with a language name
    for lang in VIETNAMESE_LANGUAGE_NAMES:
        if next_stripped.startswith(lang + ' ') or next_stripped == lang:
            # Check if current line ends with a language precursor
            for precursor in LANGUAGE_PRECURSORS:
                if current_stripped.endswith(precursor) or current_stripped.endswith(precursor + ' '):
                    # This is a language name boundary - do NOT join
                    return True

    return False


def is_proper_noun_sentence_start(current_line: str, next_line: str) -> bool:
    """
    Check if next line starts a new sentence with a proper noun (character name).

    Examples that should return True (do NOT join):
    - current: "<Name> liếc nhìn"
      next: "<Name2>, ánh mắt họ khóa vào nhau"
      → "<Name2>" starts new sentence with subject

    - current: "không phải"
      next: "Dmitri Sysevich."
      → "Dmitri Sysevich" is proper noun completing previous phrase

    Returns:
        True if next line starts a new sentence with proper noun subject
        False if next line continues previous sentence with proper noun object
    """
    current_stripped = current_line.strip().lower()
    next_stripped = next_line.strip()

    # Check if next line starts with a proper noun
    starts_with_proper = False
    proper_noun_used = None

    for name in load_book_proper_nouns():
        if next_stripped.startswith(name):
            starts_with_proper = True
            proper_noun_used = name
            break

    if not starts_with_proper:
        return False

    # Now check context to determine if it's a new sentence or continuation
    # Indicators of CONTINUATION (should join):
    continuation_indicators = [
        'không phải',  # "không phải Dmitri" (not Dmitri)
        'là',          # "là <Name>" (is <Name>)
        'gặp',         # "gặp <Name>" (meet <Name>)
        'với',         # "với <Name>" (with <Name>)
        'của',         # "của <Name>" (<Name>'s)
        'cho',         # "cho Michael" (for Michael)
        'đến',         # "đến Nagel" (to Nagel)
    ]

    for indicator in continuation_indicators:
        if current_stripped.endswith(indicator):
            # This is a continuation - should join
            return False

    # Indicators of NEW SENTENCE (do NOT join):
    # 1. Next line has comma after name (appositive or list)
    after_name = next_stripped[len(proper_noun_used):].strip()
    if after_name.startswith(','):
        # "<Name>, ánh mắt..." → new sentence with appositive
        return True

    # 2. Current line ends with complete thought
    sentence_endings = ('.', '!', '?', '..."', '"', '»')
    if any(current_stripped.endswith(end) for end in sentence_endings):
        # Clear sentence boundary
        return True

    # 3. Current line ends with verb indicating observation/action completed
    observation_verbs = ['nhìn', 'thấy', 'nghe', 'liếc nhìn', 'quan sát']
    if any(current_stripped.endswith(verb) for verb in observation_verbs):
        # "<Name> liếc nhìn" [new sentence] "<Name2>, ánh mắt..."
        return True

    # Default: not enough evidence for new sentence
    return False


def should_preserve_line_break(current_line: str, next_line: str) -> bool:
    """
    Master function to check if a line break should be preserved (not joined).

    Returns:
        True if the break should be preserved (do NOT join lines)
        False if lines can be joined
    """
    # Check language name boundaries
    if is_language_name_boundary(current_line, next_line):
        return True

    # Check proper noun sentence starts
    if is_proper_noun_sentence_start(current_line, next_line):
        return True

    return False


def get_problematic_patterns() -> List[Tuple[str, str, str]]:
    """
    Get list of problematic patterns that the standard fix_sentence_breaks might mis-handle.

    Returns:
        List of (current_line_pattern, next_line_pattern, reason)
    """
    patterns = []

    # Language name patterns
    for precursor in LANGUAGE_PRECURSORS:
        for lang in VIETNAMESE_LANGUAGE_NAMES:
            patterns.append((
                f"ends with '{precursor}'",
                f"starts with '{lang}'",
                f"Language name boundary: '{precursor} {lang}' should not be broken or wrongly joined"
            ))

    # Proper noun patterns — names come from the active book, never hardcoded.
    for verb in ['nhìn', 'liếc nhìn', 'quan sát']:
        for name in sorted(load_book_proper_nouns()):
            patterns.append((
                f"ends with '{verb}'",
                f"starts with '{name},'",
                f"New sentence with proper noun subject after observation verb"
            ))

    return patterns


if __name__ == '__main__':
    # Test cases. Names are taken from the active book so this script stays
    # book-agnostic; it degrades to the language-name cases when no
    # book_names.json exists yet.
    names = sorted(load_book_proper_nouns())
    name_a = names[0] if names else 'Alice'
    name_b = names[1] if len(names) > 1 else 'Bob'

    test_cases = [
        # Should preserve break (NOT join)
        ("thầy giáo tiếng", "Anh trường trung học", True),
        (f"{name_a} liếc nhìn", f"{name_b}, ánh mắt họ", True),
        ("giọng yếu ớt với giọng", "Nga đậm", True),

        # Should join
        ("không phải", "Dmitri Sysevich.", False),
        (f"{name_a} quay trở lại chỗ ngồi bên cạnh", name_b, False),
    ]

    print("Testing line break detection:\n")
    for current, next_line, expected in test_cases:
        result = should_preserve_line_break(current, next_line)
        status = "✓" if result == expected else "✗"
        action = "PRESERVE" if result else "JOIN"
        print(f"{status} {action:8s} | '{current}' → '{next_line}'")
        if result != expected:
            print(f"           Expected: {'PRESERVE' if expected else 'JOIN'}")

    print("\n" + "=" * 60)
    print("Problematic patterns to watch:")
    for current_pat, next_pat, reason in get_problematic_patterns()[:5]:
        print(f"\n- {reason}")
        print(f"  Current: {current_pat}")
        print(f"  Next: {next_pat}")
