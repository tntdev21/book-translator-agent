#!/usr/bin/env python3
"""
Standardize new_terms.txt format to consistent pipe-separated format.
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/standardize-new-terms.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import re
from pathlib import Path


def parse_entry(line: str) -> tuple[str, str, str, str] | None:
    """Parse different term formats into standardized tuple."""
    line = line.strip()

    # Skip empty lines, headers, separators
    if not line or line.startswith('#') or line == '---':
        return None

    # Format 1: Pipe-separated (already standard)
    # DNA11 | DNA11 | Imaging company | chunk_010
    # - test term | thuật ngữ test | test context | chunk_001 (with dash prefix)
    if '|' in line and line.count('|') == 3:
        # Remove leading dash if present
        clean_line = line.lstrip('- ')
        parts = [p.strip() for p in clean_line.split('|')]
        if len(parts) == 4:
            return tuple(parts)

    # Format 2: Dash-prefixed with arrow
    # - Alice Chen (name) → Alice Chen
    # - noeticist → nhà khoa học noetic
    arrow_match = re.match(r'^-\s*(.+?)\s*→\s*(.+?)(?:\s*\((.+?)\))?\s*$', line)
    if arrow_match:
        english = arrow_match.group(1).strip()
        vietnamese = arrow_match.group(2).strip()
        context = arrow_match.group(3) if arrow_match.group(3) else "Term"

        # Extract context from english if in parentheses
        if '(' in english and ')' in english:
            parts = english.split('(')
            english = parts[0].strip()
            context = parts[1].rstrip(')').strip()

        return (english, vietnamese, context, "unknown")

    return None


def extract_chunk_id(section_header: str) -> str:
    """Extract chunk ID from section headers."""
    # ## Chunk 010
    # # New terms from chunk_003.md (2025-11-27)
    # ## Chunk 007 (2025-11-27)

    match = re.search(r'chunk[_\s]?(\d+)', section_header.lower())
    if match:
        return f"chunk_{match.group(1)}"
    return "unknown"


def standardize_new_terms(input_path: Path, output_path: Path):
    """Standardize new_terms.txt format."""

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    standardized = []
    current_chunk = "unknown"

    # Header
    standardized.append("# New Terms Log\n")
    standardized.append("\n")
    standardized.append("Log new terms discovered during translation.\n")
    standardized.append("After translation, review and add to main glossary.\n")
    standardized.append("\n")
    standardized.append("Format: English | Vietnamese | Context | Chunk ID\n")
    standardized.append("\n")
    standardized.append("---\n")
    standardized.append("\n")

    entries_by_chunk = {}

    # Skip the existing header, whatever shape it is. A fixed lines[8:] slice
    # silently ate the whole file when the header was shorter than 8 lines —
    # which is exactly the state log_terms.py creates on first use (2 lines).
    # Drop lines up to and including the "---" separator instead, and fall back
    # to the whole file when there is no separator.
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            start = i + 1
            break
    else:
        start = 0

    for line in lines[start:]:
        line = line.rstrip('\n')

        # Track chunk sections
        if line.startswith('#'):
            chunk_id = extract_chunk_id(line)
            if chunk_id != "unknown":
                current_chunk = chunk_id
            continue

        # Parse entry
        entry = parse_entry(line)
        if entry:
            english, vietnamese, context, chunk = entry
            # Use current_chunk if entry doesn't have chunk ID
            if chunk == "unknown":
                chunk = current_chunk

            if chunk not in entries_by_chunk:
                entries_by_chunk[chunk] = []
            entries_by_chunk[chunk].append((english, vietnamese, context, chunk))

    # Write entries sorted by chunk
    for chunk_id in sorted(entries_by_chunk.keys(),
                          key=lambda x: int(x.split('_')[1]) if '_' in x and x.split('_')[1].isdigit() else 0):

        # Chunk header
        chunk_num = chunk_id.split('_')[1] if '_' in chunk_id else chunk_id
        standardized.append(f"## Chunk {chunk_num}\n")
        standardized.append("\n")

        # Entries
        for english, vietnamese, context, _ in entries_by_chunk[chunk_id]:
            standardized.append(f"{english} | {vietnamese} | {context} | {chunk_id}\n")

        standardized.append("\n")

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(standardized)

    print(f"✅ Standardized {sum(len(v) for v in entries_by_chunk.values())} entries")
    print(f"📊 Chunks: {', '.join(sorted(entries_by_chunk.keys()))}")


if __name__ == "__main__":
    from .book_config import load_book
    style_dir = load_book().style_dir
    input_file = style_dir / "new_terms.txt"
    output_file = style_dir / "new_terms_standardized.txt"

    print(f"📖 Reading: {input_file}")
    standardize_new_terms(input_file, output_file)
    print(f"💾 Written: {output_file}")
    # Deliberately no auto-overwrite. new_terms.txt is the live log that
    # log_terms.py appends to; replacing it wholesale would discard any term
    # logged between this run and the review. Review the output, copy across
    # the entries you want, then delete the scratch file.
