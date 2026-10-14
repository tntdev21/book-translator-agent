#!/usr/bin/env python3
"""
Script to check for formatting issues in translated files:
1. Unexpected line breaks in the middle of words
2. Excessive blank lines (more than 2 consecutive)
3. Unexpected line breaks in the middle of sentences
"""

import os
import re
from pathlib import Path

def check_file(filepath):
    """Check a single file for formatting issues."""
    issues = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Check for word breaks (single letter followed by rest of word on next line)
    for i in range(len(lines) - 1):
        line = lines[i].rstrip()
        next_line = lines[i + 1].rstrip()

        # Skip empty lines and comments
        if not line or line.startswith('<!--'):
            continue

        # Check if line ends with a single capital letter (potential break)
        # or if it's a very short fragment that looks broken
        if len(line) > 0 and len(line.strip()) <= 2:
            # Skip chapter headings (number followed by "CHƯƠNG")
            if line.strip().isdigit() and next_line.strip() == "CHƯƠNG":
                continue

            # Check if next line continues the word
            if next_line and not next_line.startswith('<!--') and len(next_line.strip()) > 2:
                if not next_line.strip().startswith(('-', '*', '#', '>')):
                    issues.append({
                        'line': i + 1,
                        'type': 'word_break',
                        'text': f'Line {i+1}: "{line}" followed by "{next_line[:50]}"'
                    })

    # Check for excessive blank lines
    blank_count = 0
    for i, line in enumerate(lines):
        if line.strip() == '':
            blank_count += 1
            if blank_count > 2:
                issues.append({
                    'line': i + 1,
                    'type': 'excessive_blanks',
                    'text': f'Line {i+1}: More than 2 consecutive blank lines'
                })
        else:
            blank_count = 0

    # Check for unexpected line breaks in middle of sentences
    for i in range(len(lines) - 1):
        line = lines[i].rstrip()
        next_line = lines[i + 1].rstrip()

        # Skip empty lines, comments, and markdown elements
        if not line or not next_line:
            continue
        if line.startswith(('#', '<!--', '-', '*', '>')):
            continue
        if next_line.startswith(('#', '<!--', '-', '*', '>')):
            continue

        # Define sentence-ending punctuation
        # Vietnamese uses: . ! ? ... — " » ) ] as potential endings
        sentence_endings = ('.', '!', '?', '...', '—', '"', '»', ')', ']', '…')

        # Check if line ends without proper punctuation
        ends_properly = line.endswith(sentence_endings)

        if not ends_properly:
            # Check if next line starts with lowercase or continues sentence
            # Skip if next line starts with uppercase (new sentence)
            # Skip if next line starts with special chars
            next_stripped = next_line.lstrip()

            if next_stripped:
                first_char = next_stripped[0]

                # If next line starts with lowercase Vietnamese or continuation word
                # This indicates improper line break
                if first_char.islower() or first_char in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ':
                    # Additional check: skip if the line is very short (likely a proper break)
                    if len(line.strip()) > 10:  # Only flag substantial lines
                        issues.append({
                            'line': i + 1,
                            'type': 'sentence_break',
                            'text': f'Line {i+1}: Sentence break - "{line[-40:]}" → "{next_line[:40]}"'
                        })

    return issues

def main():
    """Scan all translated files."""
    try:  # script-style run
        from book_config import bootstrap_argv
    except ImportError:  # package-style run
        from .book_config import bootstrap_argv
    _, cfg = bootstrap_argv()
    translated_dir = cfg.translated_dir

    if not translated_dir.exists():
        print(f"Error: translated directory not found: {translated_dir}")
        return

    all_issues = {}

    files = sorted(translated_dir.glob('chunk_*.md'))

    print(f"Checking {len(files)} files...\n")

    for filepath in files:
        issues = check_file(filepath)
        if issues:
            all_issues[filepath.name] = issues

    # Report findings
    if not all_issues:
        print("✓ No formatting issues found!")
    else:
        print(f"Found issues in {len(all_issues)} files:\n")

        for filename, issues in sorted(all_issues.items()):
            print(f"\n{filename}:")
            print("-" * 60)
            for issue in issues:
                print(f"  {issue['text']}")

        # Summary
        total_issues = sum(len(issues) for issues in all_issues.values())
        word_breaks = sum(1 for issues in all_issues.values()
                         for i in issues if i['type'] == 'word_break')
        blank_issues = sum(1 for issues in all_issues.values()
                          for i in issues if i['type'] == 'excessive_blanks')
        sentence_breaks = sum(1 for issues in all_issues.values()
                             for i in issues if i['type'] == 'sentence_break')

        print("\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"  Total files with issues: {len(all_issues)}")
        print(f"  Total issues: {total_issues}")
        print(f"  Word breaks: {word_breaks}")
        print(f"  Excessive blank lines: {blank_issues}")
        print(f"  Sentence breaks: {sentence_breaks}")

if __name__ == '__main__':
    main()
