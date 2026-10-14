#!/usr/bin/env python3
"""
Detect and fix word merging issues in Vietnamese text.

Common issues:
1. Missing spaces between words (thầnthoọ → thần thoại)
2. Compound words broken incorrectly
3. Character corruption from encoding issues
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/detect_word_merging.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import re
from pathlib import Path
from typing import List, Dict, Tuple


# Known Vietnamese compound words that should NEVER be broken
COMPOUND_WORDS = {
    'thần thoại': r'thầ?n\s*tho[aạ][iọ]?[a-z]?',  # matches: thần thoại, thầnthoọ, thần thoạic, thần thoọi
    'ngôn ngữ': r'ngôn\s*ng[ữư]',
    'tín ngưỡng': r'tín\s*ngưỡng',
    'xã hội': r'xã\s*h[ộọ]i',
    'lịch sử': r'l[ịi]ch\s*s[ửứ]',
    'văn hóa': r'văn\s*hóa',  # 'văn hoa' (ornate) is a real word
    'tư tưởng': r'tư\s*tưởng',
    'triết học': r'tri[ếê]t\s*h[ọo]c',
    'khoa học': r'khoa\s*h[ọo]c',
    'tôn giáo': r'tôn\s*giáo',
    'chính trị': r'chính\s*tr[ịi]',
    'kinh tế': r'kinh\s*t[ếê]',
    'văn học': r'văn\s*h[ọo]c',
    'nghệ thuật': r'ngh[ệê]\s*thu[ậa]t',
    'âm nhạc': r'âm\s*nh[ạa]c',
    'hội họa': r'h[ộọ]i\s*họa',  # never 'hội hoa' (lễ hội hoa, Quốc hội Hoa Kỳ)
    'điêu khắc': r'đi[êe]u\s*kh[ắa]c',
    'kiến trúc': r'ki[ếe]n\s*tr[úu]c',
    'tiếng Anh': r'ti[ếê]ng\s*Anh',
    'tiếng Việt': r'ti[ếê]ng\s*Vi[ệê]t',
    'tiếng Pháp': r'ti[ếê]ng\s*Pháp',
    'tiếng Đức': r'ti[ếê]ng\s*[ĐD][ứu]c',
    'tiếng Nga': r'ti[ếê]ng\s*Nga',
    'tiếng Trung': r'ti[ếê]ng\s*Trung',
}


# Patterns for detecting merged words (no space between)
MERGE_PATTERNS = [
    # Pattern: Vietnamese word followed by capital letter without space
    # Example: "thầnthoọc" → should be "thần thoại"
    (r'([àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđa-z]{2,})([àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđa-z]{2,})',
     r'\1 \2',
     'Missing space between Vietnamese words'),

    # Pattern: Multiple combining diacritics without proper spacing
    (r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+[\u0300-\u036f]{2,})([a-z])',
     r'\1 \2',
     'Diacritic corruption causing word merge'),
]


def detect_merged_words(text: str) -> List[Dict]:
    """
    Detect potential word merging issues in text.

    Returns:
        List of dictionaries with 'pattern', 'match', 'line', 'suggestion'
    """
    issues = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Check against known compound words
        for correct_form, pattern in COMPOUND_WORDS.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                matched_text = match.group()
                # If matched text doesn't match correct form exactly (ignoring case/spaces)
                normalized_match = matched_text.replace(' ', '').lower()
                normalized_correct = correct_form.replace(' ', '').lower()

                # Check if it's corrupted (extra chars, missing chars, wrong chars)
                if normalized_match != normalized_correct:
                    issues.append({
                        'line': line_num,
                        'pattern': 'corrupted_compound',
                        'match': matched_text,
                        'suggestion': correct_form,
                        'context': line.strip()
                    })

        # Check generic merge patterns
        for pattern, replacement, description in MERGE_PATTERNS:
            if re.search(pattern, line):
                # Special check: avoid false positives for legitimate single words
                # Only flag if the merged text looks like 2+ distinct Vietnamese syllables
                potential_merges = re.finditer(pattern, line)
                for match in potential_merges:
                    merged = match.group()
                    # Count syllable-like patterns (CV, CVC, V)
                    syllables = re.findall(r'[bcdfghjklmnpqrstvwxyz]*[aăâeêioôơuưy][àáảãạằắẳẵặầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]*[a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]*',
                                            merged, re.IGNORECASE)
                    if len(syllables) >= 2:
                        issues.append({
                            'line': line_num,
                            'pattern': description,
                            'match': merged,
                            'suggestion': re.sub(pattern, replacement, merged),
                            'context': line.strip()
                        })

    return issues


def fix_merged_words(text: str, auto_fix: bool = True) -> Tuple[str, int]:
    """
    Fix word merging issues in text.

    Args:
        text: Input text
        auto_fix: If True, automatically apply fixes. If False, only detect.

    Returns:
        Tuple of (fixed_text, number_of_fixes)
    """
    if not auto_fix:
        issues = detect_merged_words(text)
        return text, len(issues)

    fixes = 0
    result = text

    # Fix known compound words first (more reliable). Whole words only; a match with an
    # uppercase letter after its first is a proper noun ("Quốc hội Hoa Kỳ") and is left
    # alone; a leading capital (sentence start) is kept.
    for correct_form, pattern in COMPOUND_WORDS.items():
        form_has_upper = any(c.isupper() for c in correct_form[1:])

        def repl(m, correct_form=correct_form, form_has_upper=form_has_upper):
            nonlocal fixes
            got = m.group(0)
            if any(c.isupper() for c in got[1:]) and not form_has_upper:
                return got  # proper noun
            out = correct_form[0].upper() + correct_form[1:] if got[0].isupper() else correct_form
            fixes += out != got
            return out

        result = re.sub(rf"(?<!\w){pattern}(?!\w)", repl, result, flags=re.IGNORECASE)

    return result, fixes


def scan_file(filepath: Path) -> List[Dict]:
    """Scan a file for word merging issues."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        return detect_merged_words(text)
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
        return []


def fix_file(filepath: Path, backup: bool = True) -> int:
    """
    Fix word merging issues in a file.

    Returns:
        Number of fixes applied
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()

        fixed, fixes = fix_merged_words(original, auto_fix=True)

        if fixes > 0:
            if backup:
                backup_path = str(filepath) + '.bak'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)

        return fixes

    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return 0


def main():
    """Main entry point for standalone usage."""
    import argparse

    from .book_config import add_book_argument, get_config_from_args

    parser = argparse.ArgumentParser(description='Detect and fix word merging issues')
    parser.add_argument('files', nargs='*', help='Files to check/fix')
    parser.add_argument('--check-only', action='store_true', help='Only detect, do not fix')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    add_book_argument(parser)

    args = parser.parse_args()

    if not args.files:
        # Default to all translated files for the active book
        files = sorted(get_config_from_args(args).translated_dir.glob('chunk_*.md'))
    else:
        files = [Path(f) for f in args.files]

    print(f"Checking {len(files)} files for word merging issues...\n")

    total_issues = 0
    total_fixes = 0

    for filepath in files:
        if args.check_only:
            issues = scan_file(filepath)
            if issues:
                print(f"\n{filepath.name}:")
                for issue in issues[:5]:  # Show first 5
                    print(f"  Line {issue['line']}: {issue['match']} → {issue['suggestion']}")
                    print(f"    Context: {issue['context'][:80]}...")
                total_issues += len(issues)
        else:
            fixes = fix_file(filepath, backup=not args.no_backup)
            if fixes > 0:
                print(f"✓ {filepath.name}: {fixes} fixes")
                total_fixes += fixes

    print(f"\n{'=' * 60}")
    if args.check_only:
        print(f"Found {total_issues} potential merging issues")
    else:
        print(f"Fixed {total_fixes} word merging issues")


if __name__ == '__main__':
    main()
