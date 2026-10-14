#!/usr/bin/env python3
"""
TOC Validation Script

Validates Table of Contents format according to standards in docs/toc-standards.md
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/validate_toc.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

from .markdown_converter import make_toc_links_clickable, text_to_anchor

# TOC lines that are page numbers / artifacts, never link targets
_SKIP_ENTRY_RE = re.compile(r'^([ivxlcdm]+|\d+|.)$', re.IGNORECASE)
_NUMBER_PREFIX_RE = re.compile(r'^\d+\.\s+')


def _title_key(text: str) -> str:
    """Comparable form of a title: no markup, no "N. " prefix."""
    plain = re.sub(r'<[^>]+>|[*_]', '', text).strip()
    return text_to_anchor(_NUMBER_PREFIX_RE.sub('', plain))


def check_toc_links(content: str) -> Tuple[List[str], List[str]]:
    """Check every TOC entry resolves to a top-level target, as export links it.

    Returns ``(errors, warnings)``:
    - error: entry with no target (missing ``# `` heading or ``<!-- front id -->`` block);
    - warning: entry linked by chapter number whose wording differs from the heading.
    """
    report: list = []
    make_toc_links_clickable(content, report)

    heading_text = {}
    for line in content.split('\n'):
        if line.startswith('# '):
            heading_text.setdefault(text_to_anchor(line[2:].strip()), line[2:].strip())

    errors, warnings = [], []
    for entry, anchor in report:
        if _SKIP_ENTRY_RE.match(entry.strip()) or entry.lstrip().startswith('<!--'):
            continue
        if anchor is None:
            errors.append(f"❌ TOC entry has no target: '{entry}' "
                          "(align with a '# ' heading or add a <!-- front id=... --> block)")
        elif anchor in heading_text and _title_key(entry) != _title_key(heading_text[anchor]):
            warnings.append(f"⚠️  TOC wording differs from heading: '{entry}' vs '# {heading_text[anchor]}'")
    return errors, warnings


class TOCValidator:
    """Validates TOC format and chapter headings"""

    TOC_HEADERS = ('MỤC LỤC', 'TABLE OF CONTENTS', 'CONTENTS')
    CHAPTER_PATTERN = re.compile(r'^CHƯƠNG (\d+)$')
    MERGED_TEXT_PATTERN = re.compile(r'^CHƯƠNG \d+ [A-ZÁÀẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]', re.IGNORECASE)
    LOWERCASE_PATTERN = re.compile(r'^Chương \d+$')

    def __init__(self, chunk_dir: Path):
        self.chunk_dir = chunk_dir
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating TOC format...\n")

        chunk_001 = self.chunk_dir / "chunk_001.md"
        if not chunk_001.exists():
            self.errors.append(f"❌ chunk_001.md not found")
            return False

        toc_entries = self.validate_toc_format(chunk_001)
        chapter_headings = self.validate_chapter_headings()

        if toc_entries and chapter_headings:
            self.validate_toc_matches_content(toc_entries, chapter_headings)

        self.validate_toc_links()

        self.print_results()
        return len(self.errors) == 0

    def validate_toc_format(self, chunk_001: Path) -> List[str]:
        """Validate TOC format"""
        print("📋 Checking TOC format...")

        with open(chunk_001, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        toc_start = None
        for i, line in enumerate(lines):
            if line.strip().lstrip('#').strip().upper() in self.TOC_HEADERS:
                toc_start = i
                print(f"  ✓ TOC header found at line {i+1}")
                break

        if toc_start is None:
            self.errors.append("❌ TOC header not found")
            return []

        toc_entries = []
        i = toc_start + 1
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('#') or (line.startswith('CHƯƠNG') and '<!--' in lines[i-1]):
                break

            if line and not line.startswith('<!--'):
                toc_entries.append((i+1, line))

            i += 1

        print(f"  ✓ Found {len(toc_entries)} entries\n")

        chapter_entries = []
        for line_num, entry in toc_entries:
            if self.LOWERCASE_PATTERN.match(entry):
                self.errors.append(f"❌ Line {line_num}: Use 'CHƯƠNG' not 'Chương'")

            chapter_match = self.CHAPTER_PATTERN.match(entry)
            if chapter_match:
                chapter_entries.append(int(chapter_match.group(1)))

            if re.match(r'^CHƯƠNG \d+ [A-Z]', entry):
                self.errors.append(f"❌ Line {line_num}: Merged text: {entry[:50]}")

        if chapter_entries:
            self.validate_sequential_numbering(chapter_entries)

        return [entry for _, entry in toc_entries]

    def validate_chapter_headings(self) -> Dict[int, Tuple[str, int]]:
        """Validate chapter headings in content"""
        print("📖 Checking chapter headings...")

        chapter_headings = {}
        chunk_files = sorted(self.chunk_dir.glob("chunk_*.md"))

        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                stripped = line.strip()

                chapter_match = self.CHAPTER_PATTERN.match(stripped)
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    chapter_headings[chapter_num] = (chunk_file.name, i+1)

                if self.MERGED_TEXT_PATTERN.match(stripped):
                    self.errors.append(f"❌ {chunk_file.name}:{i+1}: Merged text")

                if self.LOWERCASE_PATTERN.match(stripped):
                    self.errors.append(f"❌ {chunk_file.name}:{i+1}: Use 'CHƯƠNG' not 'Chương'")

        print(f"  ✓ Found {len(chapter_headings)} chapters\n")
        return chapter_headings

    def validate_toc_links(self):
        """Every TOC entry must resolve to a target in the merged book."""
        print("🔗 Checking TOC links...")
        files = sorted(self.chunk_dir.glob("chunk_*.md"))
        merged = '\n\n'.join(f.read_text(encoding='utf-8') for f in files)
        errors, warnings = check_toc_links(merged)
        self.errors.extend(errors)
        self.warnings.extend(warnings)
        print(f"  ✓ {len(errors)} unlinked, {len(warnings)} wording drift\n")

    def validate_sequential_numbering(self, chapter_numbers: List[int]):
        """Check sequential numbering"""
        print("🔢 Checking numbering...")

        chapter_numbers.sort()
        expected = 1
        for num in chapter_numbers:
            if num > expected:
                self.warnings.append(f"⚠️  Gap: {expected}-{num-1}")
                expected = num + 1
            elif num == expected:
                expected += 1

        print(f"  ✓ Chapters: {chapter_numbers[0]}-{chapter_numbers[-1]}\n")

    def validate_toc_matches_content(self, toc_entries, chapter_headings):
        """Verify TOC matches content"""
        print("🔗 Checking TOC vs content...")

        toc_chapters = set()
        for entry in toc_entries:
            match = self.CHAPTER_PATTERN.match(entry)
            if match:
                toc_chapters.add(int(match.group(1)))

        content_chapters = set(chapter_headings.keys())

        missing_in_content = toc_chapters - content_chapters
        for num in missing_in_content:
            self.errors.append(f"❌ CHƯƠNG {num} in TOC but not in content")

        missing_in_toc = content_chapters - toc_chapters
        for num in missing_in_toc:
            file, line = chapter_headings[num]
            self.errors.append(f"❌ CHƯƠNG {num} in {file} but not in TOC")

        if not missing_in_content and not missing_in_toc:
            print(f"  ✓ All {len(toc_chapters)} match\n")

    def print_results(self):
        """Print results"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60 + "\n")

        if self.warnings:
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.errors:
            print(f"❌ FAILED ({len(self.errors)} errors):")
            for error in self.errors:
                print(f"  {error}")
            print()
        else:
            print("✅ PASSED\n")


def main():
    from .book_config import bootstrap_argv
    argv, cfg = bootstrap_argv()

    translated_dir = Path(argv[1]) if len(argv) > 1 else cfg.translated_dir
    validator = TOCValidator(translated_dir)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
