#!/usr/bin/env python3
"""Normalize em-dashes while preserving Vietnamese punctuation contexts."""

import re
from pathlib import Path


def normalize_dash_string(content: str) -> str:
    """Normalize em-dashes to the project's contextual ASCII-hyphen policy.

    Dialogue lines use ``- ``. Parenthetical prose interruptions use `` - ``.
    Existing en-dash numeric ranges and lexical hyphens are deliberately left
    untouched.
    """
    normalized_lines = []
    in_fenced_code_block = False
    for line in content.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        newline = line[len(body):]
        stripped = body.lstrip()

        if stripped.startswith(("```", "~~~")):
            in_fenced_code_block = not in_fenced_code_block
            normalized_lines.append(body + newline)
            continue

        # Fenced and indented code blocks are literal Markdown content. Never
        # rewrite punctuation or indentation inside them.
        if in_fenced_code_block or body.startswith(("    ", "\t")):
            normalized_lines.append(body + newline)
            continue

        indentation_match = re.match(r"[ \t]*", body)
        indentation = indentation_match.group(0)
        text = body[len(indentation):]

        # A leading em-dash denotes dialogue, even when the source omitted its
        # following space. This must not become spaced parenthetical punctuation.
        if text.startswith("—"):
            text = "- " + text[1:].lstrip(" \t")

        # A prose em-dash and incidental adjacent inline whitespace become one
        # spaced ASCII hyphen. Keeping indentation outside this replacement
        # prevents a dash at the start of an indented prose line from consuming
        # its Markdown structure.
        text = re.sub(r"[ \t]*—[ \t]*", " - ", text)
        normalized_lines.append(indentation + text + newline)

    return "".join(normalized_lines)

def normalize_dashes_file(filepath: Path | str) -> int:
    """
    Process a single file, replacing em-dashes with hyphens.

    Args:
        filepath: Path to the markdown file

    Returns:
        Number of dashes replaced
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    content = normalize_dash_string(content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Count changes
        changes = original_content.count('—')
        return changes

    return 0

def main(translated_dir=None):
    """Process all markdown files in a book's translated/ directory.

    Args:
        translated_dir: Directory to walk. Defaults to the active book's
            translated/ directory, resolved via book_config.
    """
    if translated_dir is None:
        try:  # script-style run
            from book_config import bootstrap_argv
        except ImportError:  # package-style run
            from .book_config import bootstrap_argv
        _, cfg = bootstrap_argv()
        translated_dir = cfg.translated_dir

    translated_dir = Path(translated_dir)

    if not translated_dir.exists():
        print(f"Error: translated directory not found: {translated_dir}")
        return

    files = sorted(translated_dir.glob('*.md'))

    print(f"Normalizing dashes in {len(files)} files...\n")

    total_changes = 0
    files_modified = 0

    for filepath in files:
        changes = normalize_dashes_file(filepath)
        if changes > 0:
            files_modified += 1
            total_changes += changes
            print(f"✓ {filepath.name}: {changes} em-dashes → hyphens")

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Files processed: {len(files)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Total em-dashes replaced: {total_changes}")
    print("=" * 60)

if __name__ == "__main__":
    main()
