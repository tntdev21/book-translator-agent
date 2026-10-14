#!/usr/bin/env python3
"""
Detect and optionally fix CJK (Chinese/Japanese/Korean) character corruption in Vietnamese files.

This script scans translation files for CJK characters that don't belong in Vietnamese text,
which typically indicate:
1. IME (Input Method Editor) switching errors
2. Copy-paste corruption from Chinese/English bilingual sources
3. Auto-completion errors
4. Unicode encoding issues

Usage:
    python scripts/utils/detect_cjk_corruption.py                  # Report only
    python scripts/utils/detect_cjk_corruption.py --strict         # Exit 1 if found (for CI/CD)
    python scripts/utils/detect_cjk_corruption.py --fix            # Auto-fix known patterns
    python scripts/utils/detect_cjk_corruption.py --fix --backup   # Fix with backup
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/detect_cjk_corruption.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import sys
import argparse

from .book_config import add_book_argument, get_config_from_args
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple


# Known CJK corruption patterns → Vietnamese corrections
# Expanded from actual findings in the codebase
CJK_CORRECTIONS = {
    # Common corruption patterns found (Chinese)
    '险些': 'suýt nữa',
    '参議員': 'ượng nghị sĩ',  # Context: th参議員 → thượng nghị sĩ
    '参議险': 'ượng nghị sĩ',  # Context: th参議险 → thượng nghị sĩ
    '螺': '',  # Context: xo螺n → xoắn (螺 = empty, will be removed)
    '化': '',  # Context: thần化 → thần (will add thoại later)

    # Korean Hangul patterns found
    '기사': '',  # Context: ngôi sao ma địa phương - 기사 (artifact, remove)
    '진영': '',  # Context: tách mình khỏi진영 → tách mình khỏi (remove)
    '상징': 'ượng trưng',  # Context: về t상징학 → về tượng trưng học (symbolism)
    '목욕': 'ắm',  # Context: áo choàng t목욕 → áo choàng tắm (bathrobe)
    '장애물': 'ướng ngại vật',  # Context: qua ch장애물 → qua chướng ngại vật (obstacles)
    '장애': 'ướng ngại',  # Context: shorter version
    '물': 'ại vật',  # Context: remaining part of 장애물
    '화': 'tho',  # Context: trong thần화ọc → trong thần thoại học (mythology)

    # Common Chinese words that might leak in during translation
    '的': 'của',
    '是': 'là',
    '和': 'và',
    '在': 'ở',
    '有': 'có',
    '这': 'này',
    '那': 'đó',
    '他': 'anh ấy',
    '她': 'cô ấy',
    '们': '',  # plural marker, context-dependent
    '不': 'không',
    '了': '',  # aspect marker, context-dependent
    '很': 'rất',
    '说': 'nói',
    '看': 'nhìn',
    '去': 'đi',
    '来': 'đến',
    '会': 'sẽ',
    '能': 'có thể',
    '要': 'muốn',
    '上': 'lên',
    '下': 'xuống',

    # Japanese particles that might leak
    'の': 'của',
    'は': '',
    'を': '',
    'に': '',
    'が': '',
    'で': '',
    'と': 'và',
    'か': '',
    'も': 'cũng',
    'や': '',
}


def is_cjk_char(char: str) -> bool:
    """
    Check if a character is CJK (Chinese/Japanese/Korean).

    Args:
        char: Single character to check

    Returns:
        True if character is from CJK Unicode blocks
    """
    code_point = ord(char)

    # CJK Unified Ideographs and extension blocks
    cjk_ranges = [
        (0x4E00, 0x9FFF),   # CJK Unified Ideographs (most common)
        (0x3400, 0x4DBF),   # CJK Extension A
        (0x20000, 0x2A6DF), # CJK Extension B
        (0x2A700, 0x2B73F), # CJK Extension C
        (0x2B740, 0x2B81F), # CJK Extension D
        (0x2B820, 0x2CEAF), # CJK Extension E
        (0x2CEB0, 0x2EBEF), # CJK Extension F
        (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
        (0x2F800, 0x2FA1F), # CJK Compatibility Ideographs Supplement
        # Japanese-specific
        (0x3040, 0x309F),   # Hiragana
        (0x30A0, 0x30FF),   # Katakana
        # Korean-specific
        (0xAC00, 0xD7AF),   # Hangul Syllables
        (0x1100, 0x11FF),   # Hangul Jamo
    ]

    return any(start <= code_point <= end for start, end in cjk_ranges)


def scan_file(filepath: Path) -> List[Dict]:
    """
    Scan a file for CJK characters.

    Args:
        filepath: Path to file to scan

    Returns:
        List of issue dictionaries with context
    """
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Track position in line
                for pos, char in enumerate(line):
                    if is_cjk_char(char):
                        # Get context (20 chars before and after)
                        context_start = max(0, pos - 20)
                        context_end = min(len(line), pos + 21)
                        context = line[context_start:context_end]

                        issues.append({
                            'line': line_num,
                            'pos': pos,
                            'char': char,
                            'unicode': f'U+{ord(char):04X}',
                            'name': unicodedata.name(char, 'UNKNOWN'),
                            'context': context.strip(),
                            'full_line': line.rstrip('\n')
                        })
    except Exception as e:
        print(f"⚠️  Error scanning {filepath}: {e}")

    return issues


def auto_fix_line(line: str) -> Tuple[str, int]:
    """
    Automatically fix known CJK corruption patterns in a line.

    Args:
        line: Line of text to fix

    Returns:
        Tuple of (fixed_line, number_of_fixes)
    """
    fixed = line
    fix_count = 0

    for cjk_pattern, vietnamese in CJK_CORRECTIONS.items():
        if cjk_pattern in fixed:
            fixed = fixed.replace(cjk_pattern, vietnamese)
            fix_count += 1

    return fixed, fix_count


def fix_file(filepath: Path, backup: bool = True) -> int:
    """
    Fix CJK corruption in a file.

    Args:
        filepath: Path to file to fix
        backup: Create .bak backup before fixing

    Returns:
        Number of fixes applied
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Create backup if requested
        if backup:
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  📋 Backup: {backup_path.name}")

        # Fix each line
        fixed_lines = []
        total_fixes = 0

        for line in lines:
            fixed_line, fix_count = auto_fix_line(line)
            fixed_lines.append(fixed_line)
            total_fixes += fix_count

        # Write fixed content
        if total_fixes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)

        return total_fixes

    except Exception as e:
        print(f"⚠️  Error fixing {filepath}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description='Detect and fix CJK character corruption in Vietnamese files'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with code 1 if corruption found (for CI/CD)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix known corruption patterns'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create .bak backup before fixing (requires --fix)'
    )
    parser.add_argument(
        '--translated-dir',
        default=None,
        help="Directory containing translated files (default: the book's translated/)"
    )
    add_book_argument(parser)

    args = parser.parse_args()

    translated_dir = Path(args.translated_dir) if args.translated_dir \
        else get_config_from_args(args).translated_dir

    if not translated_dir.exists():
        print(f"❌ Directory not found: {translated_dir}")
        return 1

    # Scan all markdown files
    md_files = sorted(translated_dir.glob('chunk_*.md'))

    if not md_files:
        print(f"⚠️  No chunk_*.md files found in {translated_dir}")
        return 0

    print("=" * 60)
    print("CJK CHARACTER CORRUPTION DETECTION")
    print("=" * 60)
    print(f"Scanning {len(md_files)} files...")
    print()

    all_issues = {}
    total_corruptions = 0

    # Scan phase
    for md_file in md_files:
        issues = scan_file(md_file)
        if issues:
            all_issues[md_file.name] = issues
            total_corruptions += len(issues)

    # Report phase
    if all_issues:
        print(f"❌ Found {total_corruptions} CJK character(s) in {len(all_issues)} file(s)\n")

        for filename, issues in all_issues.items():
            print(f"📄 {filename}: {len(issues)} issue(s)")
            for issue in issues:
                print(f"  Line {issue['line']:3d}: '{issue['char']}' ({issue['unicode']}) - {issue['name']}")
                print(f"    Context: ...{issue['context']}...")
            print()

        # Fix phase (if requested)
        if args.fix:
            print("=" * 60)
            print("FIXING CORRUPTIONS")
            print("=" * 60)

            total_fixes = 0
            for filename in all_issues.keys():
                filepath = translated_dir / filename
                fixes = fix_file(filepath, backup=args.backup)
                if fixes > 0:
                    print(f"✅ {filename}: {fixes} fix(es)")
                    total_fixes += fixes
                else:
                    print(f"⚠️  {filename}: No auto-fix available (manual fix needed)")

            print()
            print(f"✅ Total fixes applied: {total_fixes}")

            if total_fixes < total_corruptions:
                print()
                print("⚠️  Some corruptions require manual fixing:")
                print("   Review the files and fix remaining CJK characters manually.")
        else:
            print("💡 Run with --fix to automatically correct known patterns")

        # Exit with error if strict mode
        if args.strict:
            return 1

    else:
        print("✅ No CJK character corruption detected")
        print(f"   Scanned {len(md_files)} files")

    print("=" * 60)
    return 0




if __name__ == "__main__":
    # Allow direct execution (``python scripts/utils/detect_cjk_corruption.py``) despite the
    # package-relative imports above, which otherwise raise ImportError.
    import sys as _sys
    from pathlib import Path as _Path
    _r = _Path(__file__).resolve().parents[2]
    if str(_r) not in _sys.path:
        _sys.path.insert(0, str(_r))
    from scripts.utils.detect_cjk_corruption import main as _main
    _sys.exit(_main())
