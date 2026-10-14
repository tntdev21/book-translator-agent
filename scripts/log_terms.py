#!/usr/bin/env python3
"""
Safe term logging script - prevents duplicates and infinite loops.
Usage: python scripts/log_terms.py "term | translation | context | chunk_id"
"""

import argparse
import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.book_config import load_book, strip_book_flag  # noqa: E402


def _default_terms_file() -> str:
    """The active book's new_terms.txt (resolved lazily, so imports stay cheap)."""
    from scripts.utils.book_config import load_book
    return str(load_book().new_terms_path)


TERM_ENTRY_PARTS = 4
CHUNK_ID_PATTERN = re.compile(r"chunk_\d+")


def parse_term_entry(term_entry: str) -> Optional[Tuple[str, str, str, str]]:
    """Validate and split a log entry into term, translation, context, and chunk."""
    if not term_entry or "\n" in term_entry or "\r" in term_entry:
        return None

    parts = tuple(part.strip() for part in term_entry.split("|"))
    if len(parts) != TERM_ENTRY_PARTS or not all(parts):
        return None
    if not CHUNK_ID_PATTERN.fullmatch(parts[3]):
        return None
    return parts  # type: ignore[return-value]


def log_term(term_entry: str, terms_file: Optional[str] = None) -> bool:
    """
    Safely append a term to new_terms.txt, checking for duplicates.

    Args:
        term_entry: String in format "English | Vietnamese | Context | Chunk ID"
        terms_file: Path to the terms file

    Returns:
        True if term was added, False if duplicate or error
    """
    parsed_entry = parse_term_entry(term_entry)
    if parsed_entry is None:
        print("Error: Term entry must be 'term | translation | context | chunk_NNN'")
        return False

    term_entry = " | ".join(parsed_entry)
    terms_path = Path(terms_file if terms_file else _default_terms_file())
    if not terms_path.exists():
        terms_path.parent.mkdir(parents=True, exist_ok=True)
        terms_path.write_text("# New Terms Log\n\n", encoding="utf-8")

    # Read existing content
    existing_content = terms_path.read_text(encoding='utf-8')
    existing_lines = existing_content.splitlines()

    # Check for duplicate
    # Extract the core term (first part before |)
    term_key = term_entry.split('|')[0].strip() if '|' in term_entry else term_entry

    # Glossary terms are canonical; never re-log them (would show as false drift)
    from scripts.extract_term_map import load_glossary_rows
    glossary_path = terms_path.parent / "glossary.csv"
    if any(src.casefold() == term_key.casefold() for src, _, _ in load_glossary_rows(glossary_path)):
        print(f"ℹ️  Term already in glossary: {term_key}")
        return False

    # Check if this term already exists
    for line in existing_lines:
        if line.strip().startswith(('#', '-', '')):
            # Skip headers, markdown lists, and empty lines for comparison
            existing_key = line.strip().lstrip('- ').split('|')[0].strip() if '|' in line else ''
            if existing_key.lower() == term_key.lower():
                print(f"ℹ️  Term already exists: {term_key}")
                return False

    chunk_id = parsed_entry[3]

    # Find the appropriate chunk section or create it
    lines = existing_content.splitlines()
    chunk_section_index = -1
    chunk_header = f"## {chunk_id.replace('_', ' ').title()}"

    for i, line in enumerate(lines):
        if line.strip() == chunk_header:
            chunk_section_index = i
            break

    # Append the new term
    if chunk_section_index >= 0:
        # Insert after chunk header
        insert_index = chunk_section_index + 2  # After header and blank line
        # Find next chunk or end
        for i in range(insert_index, len(lines)):
            if lines[i].startswith('## '):
                insert_index = i - 1  # Before next chunk
                break
        lines.insert(insert_index, term_entry)
        new_content = '\n'.join(lines) + '\n'
        terms_path.write_text(new_content, encoding='utf-8')
    else:
        # Append new chunk section at end
        with open(terms_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{chunk_header}\n\n{term_entry}\n")

    print(f"✅ Added: {term_entry}")
    return True


def log_terms_batch(terms_list: List[str], terms_file: Optional[str] = None, chunk_id: Optional[str] = None) -> Tuple[int, int]:
    """
    Log multiple terms at once from a list.

    Args:
        terms_list: List of term entries
        terms_file: Path to the terms file
        chunk_id: Optional chunk ID to append to all entries

    Returns:
        Tuple of (added_count, skipped_count)
    """
    added_count = 0
    skipped_count = 0

    for term in terms_list:
        if chunk_id and '|' in term and not term.endswith(chunk_id):
            # Add chunk_id if not present
            term = f"{term} | {chunk_id}"

        if log_term(term, terms_file):
            added_count += 1
        else:
            skipped_count += 1

    print(f"\n📊 Summary: {added_count} added, {skipped_count} skipped (duplicates)")
    return added_count, skipped_count


def remove_invalid_entries(terms_file: Optional[str] = None) -> List[str]:
    """Remove malformed term rows while retaining headings, blanks, and valid entries."""
    terms_path = Path(terms_file if terms_file else _default_terms_file())
    if not terms_path.exists():
        print("File doesn't exist")
        return []

    lines = terms_path.read_text(encoding="utf-8").splitlines()
    removed = [line for line in lines if line.strip() and not line.startswith("#") and parse_term_entry(line) is None]
    kept = [line for line in lines if line not in removed]
    empty_section_lines = set()
    for index, line in enumerate(kept):
        if not line.startswith("## "):
            continue
        end = next(
            (next_index for next_index in range(index + 1, len(kept)) if kept[next_index].startswith("## ")),
            len(kept),
        )
        if not any(candidate.strip() and not candidate.startswith("#") for candidate in kept[index + 1:end]):
            empty_section_lines.update(range(index, end))

    repaired_lines = [line for index, line in enumerate(kept) if index not in empty_section_lines]
    if not removed and repaired_lines == lines:
        print("✅ No invalid term entries found")
        return []

    terms_path.write_text("\n".join(repaired_lines).rstrip() + "\n", encoding="utf-8")
    if removed:
        print(f"✅ Removed {len(removed)} invalid term entr{'y' if len(removed) == 1 else 'ies'}")
    else:
        print("✅ Removed empty term sections")
    return removed


def replace_translation(term: str, translation: str, terms_file: Optional[str] = None) -> bool:
    """Replace one term's translation while preserving its context and provenance."""
    if not term.strip() or not translation.strip() or "\n" in term or "\r" in term or "\n" in translation or "\r" in translation:
        print("Error: Term and translation must be non-empty single-line values")
        return False

    terms_path = Path(terms_file if terms_file else _default_terms_file())
    if not terms_path.exists():
        print("File doesn't exist")
        return False

    lines = terms_path.read_text(encoding="utf-8").splitlines()
    matches = []
    for index, line in enumerate(lines):
        parsed_entry = parse_term_entry(line)
        if parsed_entry and parsed_entry[0].casefold() == term.strip().casefold():
            matches.append((index, parsed_entry))

    if len(matches) != 1:
        outcome = "No" if not matches else "Multiple"
        print(f"Error: {outcome} valid entries found for: {term}")
        return False

    index, entry = matches[0]
    lines[index] = " | ".join((entry[0], translation.strip(), entry[2], entry[3]))
    terms_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ Updated translation: {entry[0]}")
    return True


def remove_term(term: str, terms_file: Optional[str] = None) -> bool:
    """Remove exactly one term entry (e.g. a generic word logged from a one-off pun)."""
    terms_path = Path(terms_file if terms_file else _default_terms_file())
    if not term.strip() or not terms_path.exists():
        print("Error: empty term or missing terms file")
        return False

    lines = terms_path.read_text(encoding="utf-8").splitlines()
    matches = [i for i, line in enumerate(lines)
               if (e := parse_term_entry(line)) and e[0].casefold() == term.strip().casefold()]
    if len(matches) != 1:
        print(f"Error: {'No' if not matches else 'Multiple'} valid entries found for: {term}")
        return False

    removed = lines.pop(matches[0])
    terms_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ Removed: {removed}")
    return True


def check_duplicates(terms_file: Optional[str] = None) -> List[Dict[str, any]]:
    """
    Check for and report duplicate terms in the file.

    Args:
        terms_file: Path to the terms file

    Returns:
        List of duplicate entries with term, line1, line2 keys
    """
    terms_path = Path(terms_file)
    if not terms_path.exists():
        print("File doesn't exist")
        return []

    content = terms_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    seen_terms = {}
    duplicates = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#') or not '|' in line:
            continue

        # Extract term key
        term_key = line.lstrip('- ').split('|')[0].strip().lower()

        if term_key in seen_terms:
            duplicates.append({
                'term': term_key,
                'line1': seen_terms[term_key],
                'line2': i
            })
        else:
            seen_terms[term_key] = i

    if duplicates:
        print(f"⚠️  Found {len(duplicates)} duplicate terms:")
        for dup in duplicates[:10]:  # Show first 10
            print(f"  - {dup['term']} (lines {dup['line1']}, {dup['line2']})")
    else:
        print("✅ No duplicates found")

    return duplicates


def main() -> int:
    """Run the terminology logger CLI for the explicitly resolved active book."""
    # Keeps book-resolution arguments separate from the term payload; the book is
    # loaded after parsing so --help works before any book exists.
    remaining, book_id = strip_book_flag(sys.argv[1:])
    parser = argparse.ArgumentParser(
        description="Log and maintain validated book terminology entries."
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true", help="report duplicate terms")
    actions.add_argument(
        "--remove-invalid", action="store_true", help="remove malformed term rows"
    )
    actions.add_argument(
        "--replace-translation",
        nargs=2,
        metavar=("TERM", "TRANSLATION"),
        help="replace exactly one term's translation",
    )
    actions.add_argument(
        "--remove-term", metavar="TERM", help="remove exactly one term entry"
    )
    parser.add_argument(
        "term_entry",
        nargs="?",
        help='entry: "term | translation | context | chunk_NNN"',
    )
    args = parser.parse_args(remaining)
    terms_file = str(load_book(book_id).new_terms_path)

    if args.check:
        check_duplicates(terms_file)
        return 0
    if args.remove_invalid:
        remove_invalid_entries(terms_file)
        return 0
    if args.replace_translation:
        return 0 if replace_translation(*args.replace_translation, terms_file) else 1
    if args.remove_term:
        return 0 if remove_term(args.remove_term, terms_file) else 1
    if args.term_entry:
        return 0 if log_term(args.term_entry, terms_file) else 1

    parser.print_usage(sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
