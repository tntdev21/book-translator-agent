#!/usr/bin/env python3
"""
Unified fix script - runs all formatting fixes on translated files.
Combines: fix_sentence_breaks, normalize_dashes, fix_formatting, CJK detection, name extraction

Usage:
    python scripts/fix.py                        # Fix all files (auto-runs all steps)
    python scripts/fix.py file.md                # Fix specific file
    python scripts/fix.py --check-only           # Check without fixing
    python scripts/fix.py --skip-dashes          # Skip dash normalization
    python scripts/fix.py --skip-sentence-breaks # Skip sentence break fixing
    python scripts/fix.py --skip-cjk             # Skip CJK corruption detection
    python scripts/fix.py --skip-name-extraction # Skip name database extraction

AUTOMATIC WORKFLOW:
    Step 0: Extract book-specific names (creates style/book_names.json)
    Step 1: Detect & fix CJK corruption (Chinese/Japanese characters)
    Step 1.5: Detect & fix word merging issues
    Step 1.6: Normalize page markers (<!-- Page N -->)
    Step 2: Fix sentence breaks (uses auto-extracted names)
    Step 3: Normalize dashes
    Step 4: Fix person name capitalization
    Step 5: Check formatting
"""

import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict, Optional

from utils.book_config import (
    BookConfig,
    BookConfigError,
    add_book_argument,
    get_config_from_args,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fix formatting issues in Vietnamese translated files'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Files to fix (default: all chunk_*.md in translated/)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check for issues, do not fix'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files (.bak)'
    )
    parser.add_argument(
        '--skip-sentence-breaks',
        action='store_true',
        help='Skip sentence break fixing'
    )
    parser.add_argument(
        '--skip-dashes',
        action='store_true',
        help='Skip dash normalization'
    )
    parser.add_argument(
        '--skip-person-names',
        action='store_true',
        help='Skip person name capitalization fixes'
    )
    parser.add_argument(
        '--skip-cjk',
        action='store_true',
        help='Skip CJK corruption detection and fixing'
    )
    parser.add_argument(
        '--skip-name-extraction',
        action='store_true',
        help='Skip automatic name database extraction'
    )
    parser.add_argument(
        '--source',
        default=None,
        help='Source file (or directory of source files) for page-marker boundary '
             'preservation; auto-resolved to <book>/chunks/<same-name> when omitted'
    )
    parser.add_argument(
        '--preserve-page-marker-boundaries',
        action='store_true',
        help='Keep each <!-- Page N --> boundary (standalone vs inline) identical to '
             'the paired source file; requires --source (or a resolvable pair)'
    )
    add_book_argument(parser)
    return parser.parse_args()


def get_files_to_process(file_args: List[str], cfg: BookConfig) -> List[Path]:
    """Determine which files to process."""
    if file_args:
        return [Path(f) for f in file_args]

    translated_dir = cfg.translated_dir
    if not translated_dir.exists():
        print(f"❌ Error: translated directory not found: {translated_dir}")
        sys.exit(1)

    files = sorted(translated_dir.glob('chunk_*.md'))
    if not files:
        print("❌ No files to process")
        sys.exit(1)

    return files


def extract_names_step(cfg: BookConfig) -> bool:
    """Step 0: Extract book-specific names for sentence break fixing."""
    print("\n📖 Step 0: Extracting book-specific names...")

    names_db_path = cfg.book_names_path

    # Check if database already exists and is recent
    if names_db_path.exists():
        import time
        age_days = (time.time() - names_db_path.stat().st_mtime) / 86400
        if age_days < 7:  # Less than 7 days old
            print(f"  ✓ Using existing name database (age: {age_days:.1f} days)")
            return True

    # Extract names from source
    try:
        from utils.extract_proper_names import main as extract_main
        import io
        import contextlib

        # Capture output to avoid cluttering
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            extract_main(['--book', cfg.id])

        print("  ✓ Name database created/updated")
        return True

    except Exception as e:
        print(f"  ⚠️  Could not extract names: {e}")
        print("  → Sentence break fixing will use fallback patterns")
        return False


def detect_cjk_step(files: List[Path], fix: bool = True, backup: bool = True) -> int:
    """Step 1: Detect and optionally fix CJK corruption."""
    print("\n🔍 Step 1: Detecting CJK character corruption...")

    try:
        from utils.detect_cjk_corruption import scan_file, fix_file

        corrupted_files = {}
        total_corruptions = 0

        # Scan all files
        for filepath in files:
            issues = scan_file(filepath)
            if issues:
                corrupted_files[filepath] = issues
                total_corruptions += len(issues)

        if not corrupted_files:
            print("  ✅ No CJK corruption detected")
            return 0

        # Report findings
        print(f"  ❌ Found {total_corruptions} CJK character(s) in {len(corrupted_files)} file(s)")
        for filepath, issues in corrupted_files.items():
            print(f"     {filepath.name}: {len(issues)} issue(s)")

        # Fix if requested
        if fix:
            total_fixes = 0
            for filepath in corrupted_files.keys():
                fixes = fix_file(filepath, backup=backup)
                if fixes > 0:
                    total_fixes += fixes
                    print(f"  ✓ {filepath.name}: {fixes} fix(es)")
                else:
                    print(f"  ⚠️  {filepath.name}: Manual fix needed")

            if total_fixes < total_corruptions:
                print(f"\n  ⚠️  {total_corruptions - total_fixes} corruptions need manual fixing")

            return total_fixes
        else:
            print("  💡 Run without --check-only to auto-fix")
            return 0

    except Exception as e:
        print(f"  ⚠️  CJK detection error: {e}")
        return 0


def detect_word_merging_step(files: List[Path], fix: bool = True, backup: bool = True) -> int:
    """Step 1.5: Detect and optionally fix word merging issues."""
    print("\n🔗 Step 1.5: Detecting word merging issues...")

    try:
        from utils.detect_word_merging import scan_file, fix_file

        merged_files = {}
        total_merges = 0

        # Scan all files
        for filepath in files:
            issues = scan_file(filepath)
            if issues:
                merged_files[filepath] = issues
                total_merges += len(issues)

        if not merged_files:
            print("  ✅ No word merging detected")
            return 0

        # Report findings
        print(f"  ❌ Found {total_merges} merged word(s) in {len(merged_files)} file(s)")
        for filepath, issues in merged_files.items():
            print(f"     {filepath.name}: {len(issues)} issue(s)")
            # Show first issue as example
            if issues:
                ex = issues[0]
                print(f"       Example: {ex['match']} → {ex['suggestion']}")

        # Fix if requested
        if fix:
            total_fixes = 0
            for filepath in merged_files.keys():
                fixes = fix_file(filepath, backup=backup)
                if fixes > 0:
                    total_fixes += fixes
                    print(f"  ✓ {filepath.name}: {fixes} fix(es)")

            return total_fixes
        else:
            print("  💡 Run without --check-only to auto-fix")
            return 0

    except Exception as e:
        print(f"  ⚠️  Word merging detection error: {e}")
        return 0


# Regex for corrupted page markers produced by some upstream sources:
#   <! -  -  Page N  -  - >
# (spaces around the dashes inside the HTML-comment markers).
# Clean `<!-- Page N -->` markers do NOT match because there are no
# spaces between `<!` and `-`, so this step is safe to re-run.
_PAGE_MARKER_CORRUPT_RE = re.compile(
    r'<\!\s+-\s+-\s+Page\s+(\d+)\s+-\s+-\s+>'
)


def normalize_page_markers_step(files: List[Path], backup: bool) -> int:
    """Step 1.6: Normalize corrupted page markers.

    Converts ``<! -  -  Page N  -  - >`` -> ``<!-- Page N -->`` so that
    downstream QA regexes (which match the clean form) succeed.
    Already-clean markers are left untouched.
    """
    print("\n🔖 Step 1.6: Normalizing page markers...")

    total_changes = 0
    for filepath in files:
        original = filepath.read_text(encoding='utf-8')
        normalized = _PAGE_MARKER_CORRUPT_RE.sub(
            lambda m: f'<!-- Page {m.group(1)} -->',
            original,
        )
        if normalized == original:
            continue

        changes = len(_PAGE_MARKER_CORRUPT_RE.findall(original))
        if backup:
            bak_path = filepath.with_suffix(filepath.suffix + '.bak')
            if not bak_path.exists():
                bak_path.write_text(original, encoding='utf-8')
        filepath.write_text(normalized, encoding='utf-8')
        print(f"  ✓ {filepath.name}: {changes} marker(s) normalized")
        total_changes += changes

    if total_changes == 0:
        print("  ✅ No page markers to normalize")
    return total_changes


def resolve_source_pair(filepath: Path, source_arg: Optional[str], cfg: Optional[BookConfig]) -> Optional[Path]:
    """Find the source chunk paired with a translated file, if any.

    ``source_arg`` (from ``--source``) may be a single file or a directory of
    source chunks; when it is a directory the translated filename is looked up
    inside it. When omitted, falls back to ``<book>/chunks/<same-name>``.
    Returns None when no pair exists (callers then skip preservation).
    """
    if source_arg:
        candidate = Path(source_arg)
        if candidate.is_dir():
            candidate = candidate / filepath.name
        if candidate.is_file():
            return candidate
        return None

    if cfg is None:
        return None

    default = cfg.chunks_dir / filepath.name
    return default if default.is_file() else None


def fix_sentence_breaks_step(
    files: List[Path],
    backup: bool,
    source_arg: Optional[str] = None,
    preserve_boundaries: bool = False,
    cfg: Optional[BookConfig] = None,
) -> int:
    """Step 2: Fix sentence breaks in all files.

    When ``preserve_boundaries`` is set, each file's page-marker boundary
    (standalone vs inline) is locked to its paired source chunk, so sentence-break
    fixing cannot collapse a source-standalone marker into surrounding prose.
    """
    print("\n📝 Step 2: Fixing sentence breaks...")
    from utils.fix_sentence_breaks import fix_sentence_breaks
    from utils.page_marker_boundaries import marker_boundaries

    total_fixes = 0
    for filepath in files:
        preserve_pages = None
        if preserve_boundaries:
            source_path = resolve_source_pair(filepath, source_arg, cfg)
            if source_path is None:
                print(f"  ⚠️  {filepath.name}: no paired source found, skipping boundary preservation")
            else:
                source_boundaries = marker_boundaries(source_path.read_text(encoding='utf-8'))
                preserve_pages = {p for p, kind in source_boundaries.items() if kind == 'standalone'}

        fixes = fix_sentence_breaks(
            filepath,
            backup=backup,
            preserve_standalone_markers=preserve_pages,
        )
        if fixes > 0:
            print(f"  ✓ {filepath.name}: {fixes} breaks fixed")
            total_fixes += fixes

    if total_fixes == 0:
        print("  ✅ No sentence breaks to fix")

    return total_fixes


def normalize_dashes_step(files: List[Path]) -> int:
    """Step 3: Normalize dashes in all files."""
    print("\n➖ Step 3: Normalizing dashes...")
    from utils.normalize_dashes import normalize_dashes_file

    total_changes = 0
    for filepath in files:
        changes = normalize_dashes_file(str(filepath))
        if changes > 0:
            print(f"  ✓ {filepath.name}: {changes} dashes normalized")
            total_changes += changes

    if total_changes == 0:
        print("  ✅ No dashes to normalize")

    return total_changes


def fix_person_names_step(files: List[Path], backup: bool) -> int:
    """Step 4: Fix person name capitalization in all files."""
    print("\n👤 Step 4: Fixing person name capitalization...")
    from utils.fix_person_names import fix_person_names_file

    total_fixes = 0
    for filepath in files:
        fixes = fix_person_names_file(filepath, backup=backup)
        if fixes > 0:
            print(f"  ✓ {filepath.name}: {fixes} names fixed")
            total_fixes += fixes

    if total_fixes == 0:
        print("  ✅ No person names to fix")

    return total_fixes


def check_formatting_step(files: List[Path]) -> Dict[str, List[Dict]]:
    """Step 5: Check formatting issues in all files."""
    print("\n🔍 Step 5: Checking formatting...")
    from utils.fix_formatting import check_file

    all_issues = {}
    for filepath in files:
        issues = check_file(filepath)
        if issues:
            all_issues[filepath.name] = issues

    return all_issues


def print_formatting_issues(all_issues: Dict[str, List[Dict]]) -> None:
    """Print formatting issues found during check."""
    if not all_issues:
        print("  ✅ No formatting issues found!")
        return

    print(f"\n⚠️  Found issues in {len(all_issues)} files:")
    for filename, issues in sorted(all_issues.items()):
        print(f"\n  {filename}:")
        for issue in issues[:5]:  # Show first 5 issues per file
            print(f"    Line {issue['line']}: {issue['type']}")

    total_issue_count = sum(len(issues) for issues in all_issues.values())
    if total_issue_count > len(all_issues) * 5:
        print(f"\n  ... and {total_issue_count - len(all_issues) * 5} more issues")


def print_summary(
    check_only: bool,
    total_fixes: int,
    all_issues: Dict[str, List[Dict]],
    no_backup: bool
) -> None:
    """Print final summary of operations."""
    print("\n" + "=" * 60)

    if check_only:
        print("📊 CHECK COMPLETE")
        if all_issues:
            print(f"   Found issues in {len(all_issues)} files")
            print("   Run without --check-only to fix them")
    else:
        print("✅ FIX COMPLETE")
        print(f"   Total fixes applied: {total_fixes}")
        if all_issues:
            print(f"   ⚠️  {len(all_issues)} files still have issues (check output above)")
        if not no_backup and total_fixes > 0:
            print("   📋 Backup files created with .bak extension")


def main() -> int:
    """Main entry point for the fix script."""
    # Parse arguments
    args = parse_arguments()
    try:
        cfg: Optional[BookConfig] = get_config_from_args(args)
    except BookConfigError:
        # Explicit files can be fixed without an active book (no name/source knowledge).
        if not args.files:
            raise
        cfg = None

    # Get files to process
    files = get_files_to_process(args.files, cfg)

    print("=" * 60)
    print("🔧 AUTOMATED FIX WORKFLOW")
    print("=" * 60)
    print(f"Book: {cfg.id if cfg else '(none)'}")
    print(f"Processing {len(files)} files...")
    print()

    total_fixes = 0

    # Step 0: Extract book-specific names (runs automatically for new books)
    if cfg and not args.skip_name_extraction and not args.check_only:
        extract_names_step(cfg)

    # Step 1: Detect & fix CJK corruption
    if not args.skip_cjk:
        total_fixes += detect_cjk_step(files, fix=not args.check_only, backup=not args.no_backup)

    # Step 1.5: Detect & fix word merging (thầnthoọ → thần thoại)
    if not args.check_only:
        total_fixes += detect_word_merging_step(files, fix=True, backup=not args.no_backup)

    # Step 1.6: Normalize page markers (<! -  -  Page N  -  - > -> <!-- Page N -->).
    # This narrow repair is idempotent and must cover QA-passed chunks too.
    if not args.check_only:
        total_fixes += normalize_page_markers_step(files, backup=not args.no_backup)

    # Step 2: Fix sentence breaks (uses auto-extracted names + language detection)
    if not args.skip_sentence_breaks and not args.check_only:
        total_fixes += fix_sentence_breaks_step(
            files,
            backup=not args.no_backup,
            source_arg=args.source,
            preserve_boundaries=args.preserve_page_marker_boundaries,
            cfg=cfg,
        )

    # Step 3: Normalize dashes
    if not args.skip_dashes and not args.check_only:
        total_fixes += normalize_dashes_step(files)

    # Step 4: Fix person names
    if not args.skip_person_names and not args.check_only:
        total_fixes += fix_person_names_step(files, backup=not args.no_backup)

    # Step 5: Check formatting
    all_issues = check_formatting_step(files)
    print_formatting_issues(all_issues)

    # Print summary
    print_summary(args.check_only, total_fixes, all_issues, args.no_backup)

    return 0


if __name__ == '__main__':
    sys.exit(main())
