#!/usr/bin/env python3
"""
Auto-extract proper names from source/translated files for sentence break fixing.

This script builds a BOOK_SPECIFIC_NAMES database by analyzing:
1. Source English text (proper nouns, character names, locations)
2. Translated Vietnamese text (retained English names)
3. Frequency analysis (common names used throughout)

The extracted names are used by fix_sentence_breaks.py to detect name splits
like "Alice" + "Chen" or "Marcus" + "Webb" on separate lines.

Usage:
    python scripts/utils/extract_proper_names.py                    # Extract and save
    python scripts/utils/extract_proper_names.py --output names.json
    python scripts/utils/extract_proper_names.py --min-freq 3       # Filter by frequency
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/extract_proper_names.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import re
import json
import argparse
from pathlib import Path
from collections import Counter
from typing import Optional, Set, Dict, List

from .book_config import BookConfig, add_book_argument, get_config_from_args


def extract_names_from_english(filepath: Path, min_freq: int = 2) -> Dict[str, int]:
    """
    Extract proper names from English source text.

    Strategy:
    1. Find capitalized word sequences (2-3 words)
    2. Filter out common sentence starters
    3. Track frequency (names appear multiple times)

    Args:
        filepath: Path to English source file
        min_freq: Minimum frequency to include name

    Returns:
        Dictionary of {name: frequency}
    """
    if not filepath.exists():
        return {}

    names = Counter()

    # Common sentence starters to exclude
    EXCLUDE = {
        'The', 'A', 'An', 'This', 'That', 'These', 'Those',
        'He', 'She', 'It', 'They', 'We', 'You', 'I',
        'His', 'Her', 'Their', 'Our', 'Your', 'My',
        'What', 'When', 'Where', 'Why', 'How', 'Who',
        'But', 'And', 'Or', 'So', 'Yet', 'For',
        'In', 'On', 'At', 'To', 'From', 'With',
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Pattern: 2-3 capitalized words in sequence
            # Examples: "Alice Chen", "Marcus Webb", "Prague Castle"
            pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'

            for match in re.finditer(pattern, line):
                name = match.group(1)

                # Skip if starts with common word
                first_word = name.split()[0]
                if first_word in EXCLUDE:
                    continue

                # Skip if all words are too short (likely acronyms or abbrev)
                words = name.split()
                if all(len(w) <= 2 for w in words):
                    continue

                names[name] += 1

    # Filter by frequency
    return {name: count for name, count in names.items() if count >= min_freq}


def extract_names_from_vietnamese(filepath: Path, min_freq: int = 2) -> Dict[str, int]:
    """
    Extract retained English names from Vietnamese translation.

    In Vietnamese translations, proper names (people, places, organizations)
    are often kept in English. This extracts those.

    Args:
        filepath: Path to Vietnamese translated file
        min_freq: Minimum frequency to include name

    Returns:
        Dictionary of {name: frequency}
    """
    if not filepath.exists():
        return {}

    names = Counter()

    # Pattern for English names in Vietnamese text
    # Examples: "Alice", "Chen", "CIA", "Prague"
    pattern = r'\b([A-Z][a-zA-Z]+)\b'

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            for match in re.finditer(pattern, line):
                name = match.group(1)

                # Must be at least 3 chars (skip short particles like "Da", "Van")
                if len(name) < 3:
                    continue

                # Skip if looks like Vietnamese (has diacritics nearby)
                # This is a heuristic - English names shouldn't have Vietnamese chars around them
                context_start = max(0, match.start() - 5)
                context_end = min(len(line), match.end() + 5)
                context = line[context_start:context_end]

                # Vietnamese diacritics
                if any(c in context for c in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'):
                    # Name is surrounded by Vietnamese, might be false positive
                    # But still count if it appears frequently
                    pass

                names[name] += 1

    # Filter by frequency
    return {name: count for name, count in names.items() if count >= min_freq}


def extract_multi_word_names(names_dict: Dict[str, int]) -> Set[str]:
    """
    Extract individual words from multi-word names.

    Example:
        "Alice Chen" (freq: 10) → {"Alice", "Chen"}
        "Marcus Webb" (freq: 15) → {"Marcus", "Webb"}

    This helps detect broken names like "Alice" + "Chen" on separate lines.

    Args:
        names_dict: Dictionary of {full_name: frequency}

    Returns:
        Set of individual name words
    """
    individual_names = set()

    for name in names_dict.keys():
        words = name.split()
        if len(words) >= 2:
            # Multi-word name, extract each word
            individual_names.update(words)

    return individual_names


def merge_name_databases(*name_dicts: Dict[str, int]) -> Dict[str, int]:
    """
    Merge multiple name frequency dictionaries.

    Args:
        *name_dicts: Multiple dictionaries to merge

    Returns:
        Merged dictionary with combined frequencies
    """
    merged = Counter()

    for name_dict in name_dicts:
        for name, count in name_dict.items():
            merged[name] += count

    return dict(merged)


def save_names_database(names: Dict[str, int], individual_names: Set[str], output_path: Path):
    """
    Save extracted names to JSON file.

    Args:
        names: Full names with frequencies
        individual_names: Individual name words
        output_path: Output file path
    """
    database = {
        'full_names': names,
        'individual_names': sorted(individual_names),
        'metadata': {
            'total_full_names': len(names),
            'total_individual_names': len(individual_names),
            'most_common': sorted(names.items(), key=lambda x: x[1], reverse=True)[:20]
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved to {output_path}")


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description='Auto-extract proper names from book files'
    )
    parser.add_argument(
        '--source-dir',
        default=None,
        help="Directory containing source files (default: the book's source/)"
    )
    parser.add_argument(
        '--translated-dir',
        default=None,
        help="Directory containing translated files (default: the book's translated/)"
    )
    parser.add_argument(
        '--output',
        default=None,
        help="Output JSON file (default: the book's style/book_names.json)"
    )
    parser.add_argument(
        '--min-freq',
        type=int,
        default=2,
        help='Minimum frequency to include name (default: 2)'
    )
    add_book_argument(parser)

    args = parser.parse_args(argv)
    cfg = get_config_from_args(args)

    source_dir = Path(args.source_dir) if args.source_dir else cfg.source_file.parent
    translated_dir = Path(args.translated_dir) if args.translated_dir else cfg.translated_dir
    output_path = Path(args.output) if args.output else cfg.book_names_path

    print("=" * 60)
    print("BOOK-SPECIFIC NAME EXTRACTION")
    print("=" * 60)

    # Extract from English source
    print("\n📖 Analyzing English source...")
    eng_source = source_dir / 'full_text.md'
    eng_names = extract_names_from_english(eng_source, args.min_freq)
    print(f"  Found {len(eng_names)} names from English source")

    # Extract from Vietnamese translation
    print("\n📖 Analyzing Vietnamese translation...")
    vie_names = Counter()

    translated_files = sorted(translated_dir.glob('chunk_*.md'))
    if translated_files:
        print(f"  Scanning {len(translated_files)} translated files...")
        for md_file in translated_files:
            file_names = extract_names_from_vietnamese(md_file, min_freq=1)
            vie_names.update(file_names)

        # Filter by total frequency across all files
        vie_names = {name: count for name, count in vie_names.items() if count >= args.min_freq}
        print(f"  Found {len(vie_names)} names from Vietnamese translation")
    else:
        print("  ⚠️  No translated files found")

    # Merge databases
    print("\n🔄 Merging databases...")
    merged_names = merge_name_databases(eng_names, vie_names)
    individual_names = extract_multi_word_names(merged_names)

    print(f"  Total unique names: {len(merged_names)}")
    print(f"  Individual name words: {len(individual_names)}")

    # Show top names
    print("\n📊 Top 20 most frequent names:")
    top_names = sorted(merged_names.items(), key=lambda x: x[1], reverse=True)[:20]
    for name, count in top_names:
        print(f"  {count:4d}x  {name}")

    # Save to file
    print(f"\n💾 Saving database...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_names_database(merged_names, individual_names, output_path)

    print("\n" + "=" * 60)
    print("✅ Extraction complete!")
    print("=" * 60)
    print(f"\n💡 Usage:")
    print(f"   This database will be automatically loaded by fix_sentence_breaks.py")
    print(f"   to detect broken proper names across lines.")

    return 0




if __name__ == "__main__":
    # Allow direct execution (``python scripts/utils/extract_proper_names.py``) despite the
    # package-relative imports above, which otherwise raise ImportError.
    import sys as _sys
    from pathlib import Path as _Path
    _r = _Path(__file__).resolve().parents[2]
    if str(_r) not in _sys.path:
        _sys.path.insert(0, str(_r))
    from scripts.utils.extract_proper_names import main as _main
    _sys.exit(_main())
