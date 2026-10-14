#!/usr/bin/env python3
"""
Script to fix chapter heading format from:
1
CHƯƠNG

to:
CHƯƠNG 1

This matches proper Vietnamese chapter heading format.
"""

import re
from pathlib import Path

try:  # script-style run (python scripts/utils/fix_chapter_format.py)
    from book_config import bootstrap_argv, load_book
except ImportError:  # package-style run (import utils.fix_chapter_format)
    from .book_config import bootstrap_argv, load_book

def fix_file(filepath):
    """Fix chapter heading format in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0
    changes = 0

    while i < len(lines):
        current_line = lines[i].rstrip()

        # Check if this is a chapter number followed by CHƯƠNG
        if i < len(lines) - 1:
            next_line = lines[i + 1].rstrip() if i + 1 < len(lines) else ''

            # Pattern: line with just a number, next line is "CHƯƠNG"
            if current_line.strip().isdigit() and next_line.strip() == "CHƯƠNG":
                # Combine them as "CHƯƠNG {number}"
                chapter_num = current_line.strip()
                fixed_lines.append(f"CHƯƠNG {chapter_num}\n")
                changes += 1
                i += 2  # Skip both lines
                continue

        # Keep the line as is
        fixed_lines.append(lines[i])
        i += 1

    return fixed_lines, changes

def main():
    """Fix chapter headings in all translated files."""
    _, cfg = bootstrap_argv()
    translated_dir = cfg.translated_dir

    if not translated_dir.exists():
        print(f"Error: translated directory not found: {translated_dir}")
        return

    files = sorted(translated_dir.glob('chunk_*.md'))

    print(f"Fixing chapter heading format in {len(files)} files...\n")

    total_changes = 0
    files_modified = 0

    for filepath in files:
        fixed_content, changes = fix_file(filepath)

        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_content)

            files_modified += 1
            total_changes += changes
            print(f"✓ {filepath.name}: {changes} chapter headings fixed")

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Files modified: {files_modified}")
    print(f"  Total chapter headings converted to 'CHƯƠNG X' format: {total_changes}")

if __name__ == '__main__':
    main()
