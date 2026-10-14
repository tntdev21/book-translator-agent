#!/usr/bin/env python3
"""
Validate dialogue formatting to prevent isolated dialogue lines from being
misinterpreted as headings by the markdown converter.

Usage:
    python scripts/utils/validate_dialogue.py translated/
    python scripts/utils/validate_dialogue.py translated/chunk_006.md
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def check_isolated_dialogue(file_path: Path) -> List[Tuple[int, str]]:
    """
    Check for isolated single-line dialogue that might be misinterpreted as headings.

    Criteria for potentially problematic dialogue:
    - Starts with '- '
    - Very short (< 30 chars)
    - No speaker attribution (' - ' in middle)
    - Preceded by non-dialogue line (not blank, not dialogue)
    - Followed by non-dialogue line (not blank, not dialogue)

    Args:
        file_path: Path to markdown file

    Returns:
        List of (line_number, line_text) tuples for problematic lines
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    issues = []
    for i in range(1, len(lines) - 1):
        curr = lines[i].strip()
        prev = lines[i-1].strip()
        next_line = lines[i+1].strip()

        # Check if current line is dialogue
        if not curr.startswith('- '):
            continue

        # Skip long dialogue (likely has context)
        if len(curr) >= 30:
            continue

        # Skip if has attribution marker (' - ' in middle)
        dialogue_text = curr[2:]  # Remove '- ' prefix
        if ' - ' in dialogue_text:
            continue

        # Check if surrounded by non-dialogue, non-blank lines
        if prev and not prev.startswith('- ') and not prev.startswith('#') and \
           next_line and not next_line.startswith('- ') and not next_line.startswith('#'):
            issues.append((i + 1, curr))

    return issues


def validate_file(file_path: Path, verbose: bool = True) -> bool:
    """Validate a single file for dialogue issues."""
    issues = check_isolated_dialogue(file_path)

    if issues:
        if verbose:
            print(f"\n⚠️  {file_path.name}:")
            for line_num, text in issues:
                print(f"  Line {line_num}: {text}")
        return False

    return True


def validate_directory(dir_path: Path, verbose: bool = True) -> bool:
    """Validate all markdown files in a directory."""
    files = sorted(dir_path.glob('chunk_*.md'))

    if not files:
        print(f"❌ No chunk files found in {dir_path}")
        return False

    print(f"🔍 Validating dialogue formatting in {len(files)} files...")
    print("=" * 70)

    all_valid = True
    total_issues = 0

    for file_path in files:
        issues = check_isolated_dialogue(file_path)
        if issues:
            all_valid = False
            total_issues += len(issues)
            print(f"\n⚠️  {file_path.name}: {len(issues)} issue(s)")
            for line_num, text in issues:
                print(f"  Line {line_num}: {text[:60]}")

    print("\n" + "=" * 70)
    if all_valid:
        print("✅ PASSED - No isolated dialogue issues found")
        return True
    else:
        print(f"⚠️  WARNINGS - Found {total_issues} potentially problematic dialogue line(s)")
        print("\nNote: These lines might be misinterpreted as headings by the markdown converter.")
        print("Consider adding speaker attribution or grouping with adjacent dialogue.")
        return False


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_dialogue.py <directory|file>")
        print("Example: python validate_dialogue.py translated/")
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"❌ Path not found: {path}")
        sys.exit(1)

    if path.is_file():
        result = validate_file(path)
        sys.exit(0 if result else 1)
    elif path.is_dir():
        result = validate_directory(path)
        sys.exit(0 if result else 1)
    else:
        print(f"❌ Invalid path: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
