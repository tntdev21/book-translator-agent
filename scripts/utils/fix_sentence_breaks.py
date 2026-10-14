#!/usr/bin/env python3
"""
Script to automatically fix unexpected line breaks in the middle of sentences.
Joins broken sentences back together while preserving proper paragraph breaks.

Enhanced with smart name continuation detection using auto-extracted book names.
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/fix_sentence_breaks.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import os
import re
import sys
from pathlib import Path
from .constants import MAX_SENTENCE_FIX_PASSES, MIN_LINE_LENGTH_FOR_JOIN
from .book_config import add_book_argument, get_config_from_args

PAGE_MARKER_RE = re.compile(r'<!-- Page \d+ -->')
PAGE_MARKER_NUM_RE = re.compile(r'<!-- Page (\d+) -->')

# Import name continuation detector (optional - uses fallback if not available)
try:
    from .name_continuation_detector import should_join_for_name
    NAME_DETECTOR_AVAILABLE = True
except ImportError:
    NAME_DETECTOR_AVAILABLE = False
    def should_join_for_name(current, next_line):
        return False

# Import language break detector (optional - uses fallback if not available)
try:
    from .detect_language_breaks import should_preserve_line_break
    LANGUAGE_DETECTOR_AVAILABLE = True
except ImportError:
    LANGUAGE_DETECTOR_AVAILABLE = False
    def should_preserve_line_break(current, next_line):
        return False


def fix_sentence_breaks(filepath, backup=True, preserve_standalone_markers=None):
    """
    Fix sentence breaks in a file by joining improperly broken lines.
    Uses multiple passes to handle sentences broken across many lines.

    Args:
        filepath: Path to the file to fix
        backup: If True, create a .bak backup before modifying
        preserve_standalone_markers: Optional set of page-number strings whose
            marker the source keeps as its own blank-line-delimited block.
            Those markers are restored to standalone (blank line before and
            after) and the seam around them is never joined — so a marker the
            source keeps standalone cannot collapse into surrounding prose.
            Source-inline markers are left alone; use
            ``--preserve-page-marker-boundaries`` on ``fix.py`` to load this
            from the paired source chunk.

    Returns:
        Number of fixes applied
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if backup:
        backup_path = str(filepath) + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"📋 Backup created: {backup_path}")

    # Pre-processing: Split lines that contain TOC headers embedded within
    # This fixes: "...<Author> MỤC LỤC Lời cống hiến" → separate lines
    TOC_HEADERS = ('MỤC LỤC', 'TABLE OF CONTENTS', 'CONTENTS')
    preprocessed_lines = []
    for line in lines:
        line_modified = False
        for header in TOC_HEADERS:
            if header in line and line.strip() != header:
                # Header is embedded within line - split it out
                parts = line.split(header)
                if len(parts) == 2:
                    before, after = parts
                    # Add before text (if not just whitespace)
                    if before.strip():
                        preprocessed_lines.append(before.rstrip() + '\n')
                    # Add blank line
                    preprocessed_lines.append('\n')
                    # Add TOC header on its own line
                    preprocessed_lines.append(header + '\n')
                    # Add blank line
                    preprocessed_lines.append('\n')
                    # Add after text (if not just whitespace)
                    if after.strip():
                        preprocessed_lines.append(after.lstrip())
                    line_modified = True
                    break
        if not line_modified:
            preprocessed_lines.append(line)

    lines = preprocessed_lines

    total_fixes = 0
    pass_num = 0

    # Page numbers whose boundary the source keeps standalone. Emitted as
    # their own block with a blank line on both sides.
    protect_pages = set(preserve_standalone_markers or ())

    # Keep processing until no more fixes are needed
    while pass_num < MAX_SENTENCE_FIX_PASSES:
        fixed_lines = []
        i = 0
        fixes_this_pass = 0
        in_toc = False  # Track if we're in TOC section
        in_copyright = False  # Track if we're in copyright/book list section

        while i < len(lines):
            line = lines[i].rstrip()
            line_original = lines[i].rstrip('\n')  # Keep trailing spaces/dashes

            # Detect copyright/book listing section (lines with "Tác phẩm" or "Bản quyền")
            if 'Tác phẩm' in line or 'Bản quyền' in line:
                in_copyright = True

            # Detect copyright section end (MỤC LỤC header or <!-- Page comment)
            if in_copyright and (line.strip() in ('MỤC LỤC', 'TABLE OF CONTENTS', 'CONTENTS') or line.startswith('<!-- Page')):
                in_copyright = False

            # Skip processing lines within copyright section
            if in_copyright:
                fixed_lines.append(lines[i])
                i += 1
                continue

            # Detect TOC section start
            if line.strip() in ('MỤC LỤC', 'TABLE OF CONTENTS', 'CONTENTS'):
                in_toc = True
                # Ensure TOC header is on its own line by adding blank line before
                # if previous line has content (not blank, not comment)
                if fixed_lines and fixed_lines[-1].strip() and not fixed_lines[-1].strip().startswith('<!--'):
                    # Previous line has content - ensure separation
                    if not fixed_lines[-1].endswith('\n\n'):
                        fixed_lines.append('\n')

                fixed_lines.append(lines[i])
                i += 1

                # Ensure blank line after TOC header
                if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('<!--'):
                    fixed_lines.append('\n')

                continue

            # Detect TOC section end (first chapter or major heading starting with #)
            if in_toc and (line.startswith('# ') or line.startswith('## ') or line.startswith('CHƯƠNG')):
                in_toc = False

            # Skip processing lines within TOC section
            if in_toc:
                fixed_lines.append(lines[i])
                i += 1
                continue

            # Skip numbered list items (e.g., "7. Barging In", "12. Epilogue")
            # These are list-like entries that should not be joined with adjacent lines
            if re.match(r'^\d+\.\s+\S', line):
                fixed_lines.append(lines[i])
                i += 1
                continue

            # Always add empty lines and markdown headings as-is
            if not line or line.startswith(('#', '*', '>')):
                fixed_lines.append(lines[i])
                i += 1
                continue

            # Skip markdown list items (but not Vietnamese dialogue which also uses -)
            # Vietnamese dialogue: "- Ở Prague?" (has capital letter or Vietnamese quote)
            # Markdown list: "- item text" (usually enters here already normalized)
            # A "- " line is ambiguous: prose dialogue uses the same marker. Only
            # treat it as a list when the neighbour is also a list, so a lone
            # "- Câu thoại" in prose keeps being processed as dialogue.
            if line.startswith('- '):
                prev_is_list = (
                    fixed_lines
                    and fixed_lines[-1].strip().startswith('- ')
                    and not fixed_lines[-1].strip().startswith('<!--')
                )
                next_is_list = any(
                    lines[k].strip().startswith('- ')
                    for k in range(i + 1, min(i + 3, len(lines)))
                )
                if prev_is_list or next_is_list:
                    fixed_lines.append(lines[i])
                    i += 1
                    continue

            # Page comments - add but check if we should join across them
            if line.startswith('<!--'):
                fixed_lines.append(lines[i])
                i += 1
                continue

            # Check if this line needs to be joined with the next
            should_join = False
            comments_between = []
            next_content_idx = None

            # Look ahead to find next non-comment, non-empty line
            j = i + 1
            while j < len(lines):
                peek_line = lines[j].rstrip()

                # A page marker is a hard source boundary. Joining across it
                # relocates page content and leaves later pages marker-only.
                if PAGE_MARKER_RE.fullmatch(peek_line):
                    break

                # Any page marker is a boundary: never join across it, whether
                # or not the page number is in protect_pages. Covers markers
                # with leading whitespace and marker+trailing-prose lines too.
                if peek_line.strip().startswith('<!-- Page'):
                    break

                # A blank line is a source-preserved block boundary. Never
                # join across it, even when the next block looks like a
                # lowercase continuation.
                if not peek_line:
                    break

                # Non-page HTML comments may remain within a block, so retain
                # the established traversal behavior for those comments.
                if peek_line.startswith('<!--'):
                    comments_between.append(j)
                    j += 1
                    continue

                # Found next content line
                # Check if it's a markdown element (but not Vietnamese dialogue)
                is_markdown = False
                if peek_line.startswith(('#', '*', '>')):
                    is_markdown = True
                elif peek_line.startswith('- '):
                    # Check if markdown list or dialogue
                    after_dash = peek_line[2:].strip()
                    if not (after_dash and (after_dash[0].isupper() or after_dash[0] in '"«"\'')):
                        is_markdown = True

                if not is_markdown:
                    next_content_idx = j
                    break
                else:
                    break

            if next_content_idx is not None:
                next_line = lines[next_content_idx].rstrip()

                # SPECIAL CASE: Don't join if current line contains TOC header
                # This prevents: "...<Author> MỤC LỤC Lời cống hiến"
                TOC_HEADERS = ('MỤC LỤC', 'TABLE OF CONTENTS', 'CONTENTS')
                if any(header in line for header in TOC_HEADERS):
                    should_join = False
                    fixed_lines.append(lines[i])
                    i += 1
                    continue

                # SPECIAL CASE: Don't join if next line contains TOC header
                if any(header in next_line for header in TOC_HEADERS):
                    should_join = False
                    fixed_lines.append(lines[i])
                    i += 1
                    continue

                # Define sentence-ending punctuation
                sentence_endings = ('.', '!', '?', '...', '—', '"', '»', ')', ']', '…')
                ends_properly = line.endswith(sentence_endings)

                # Exception: dialogue attribution markers (- at end) should continue
                # Example: "? -" is not a proper ending
                if line_original.endswith(' -') or line_original.endswith('-'):
                    ends_properly = False

                # Exception: If next line is very short or single word, likely a break even if current ends properly
                next_stripped = next_line.strip()
                next_is_very_short = len(next_stripped) <= 3 and len(next_stripped) > 0
                next_words = next_stripped.split()
                next_is_single_short = len(next_words) == 1 and len(next_stripped) <= 12

                # If next line looks like a broken continuation, check it
                if ends_properly and (next_is_very_short or next_is_single_short):
                    # Check if it's NOT a legitimate new sentence (heading, list, etc.)
                    if not next_line.startswith(('#', '*', '>', '-')):
                        # This is likely a compound word or mid-sentence break
                        ends_properly = False

                if not ends_properly:
                    next_stripped = next_line.lstrip()
                    if next_stripped:
                        first_char = next_stripped[0]

                        # Check if next line continues the sentence
                        is_lowercase = (first_char.islower() or
                                          first_char in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')

                        # If line ends with common prepositions/conjunctions/commas, join with next (even if capitalized)
                        common_joiners = ('qua', 'ở', 'tại', 'trong', 'ngoài', 'trên', 'dưới',
                                        'và', 'hoặc', 'nhưng', 'mà', 'với', 'của', 'cho',
                                        'đến', 'từ', 'về', 'ra', 'vào', 'lên', 'xuống', 'bên', 'khi',
                                        'hình thức', 'những người', 'các', 'một', 'những', 'này', 'đó')
                        ends_with_joiner = any(line.strip().lower().endswith(' ' + word) for word in common_joiners)

                        # Also join if ends with comma (common continuation)
                        ends_with_comma = line.strip().endswith(',')

                        # Common verbs that indicate continuation when at end of line
                        common_verbs = ('nói', 'hỏi', 'trả lời', 'thốt', 'nói thêm', 'tiếp tục',
                                      'giải thích', 'thì thầm', 'hét', 'thét', 'la', 'gọi')
                        ends_with_verb = any(line.strip().lower().endswith(' ' + word) for word in common_verbs)

                        # If previous line ends with dialogue dash, always join (dialogue attribution)
                        prev_ends_dash = line_original.endswith(' -') or line_original.endswith('-')

                        # ===== ENHANCED VIETNAMESE PATTERNS =====

                        # Pattern 1: Current line is short pronoun (high confidence join)
                        vietnamese_pronouns = ('nó', 'tôi', 'cô', 'anh', 'chúng', 'họ', 'em',
                                             'ta', 'chị', 'mình', 'bạn', 'ông', 'bà')
                        is_pronoun_line = line.strip().lower() in vietnamese_pronouns

                        # Pattern 2: Current line ends with articles (always continue to next word)
                        articles = ('một', 'các', 'những', 'mọi', 'hai', 'ba', 'bốn', 'năm',
                                  'sáu', 'bảy', 'tám', 'chín', 'mười', 'nhiều', 'ít', 'vài')
                        ends_with_article = any(line.strip().lower().endswith(' ' + art) for art in articles)

                        # Pattern 3: Current line ends with common nouns preceding proper nouns/specifics
                        common_nouns = ('chai', 'ly', 'cốc', 'bình', 'hộp', 'túi',
                                      'ông', 'bà', 'bác', 'chú', 'cô', 'thầy', 'cậu', 'dì',
                                      'cuốn', 'quyển', 'tờ', 'tập', 'bức', 'bài', 'bản',
                                      'căn', 'tòa', 'ngôi', 'con', 'chiếc', 'cái', 'quả',
                                      'thành phố', 'quận', 'huyện', 'phố', 'đường', 'số',
                                      'ngày', 'tháng', 'năm', 'thế kỷ', 'thập kỷ')
                        ends_with_common_noun = any(line.strip().lower().endswith(' ' + noun) for noun in common_nouns)

                        # Pattern 4: Current line is very short (likely mid-word/mid-phrase breaks)
                        is_very_short = len(line.strip()) <= 3 and len(line.strip()) > 0

                        # Pattern 5: Current line is single short word (compound word break)
                        words = line.strip().split()
                        is_single_short_word = len(words) == 1 and len(line.strip()) <= 12

                        # Pattern 6: Current line ends with possessive/connecting particles
                        connectors = ('của', 'về', 'cho', 'với', 'bởi', 'từ', 'đến',
                                    'theo', 'để', 'khi', 'nếu', 'vì', 'mà', 'nhưng',
                                    'như', 'thì', 'vẫn', 'đã', 'sẽ', 'đang', 'còn')
                        ends_with_connector = any(line.strip().lower().endswith(' ' + conn) for conn in connectors)

                        # Pattern 7: NEXT line is very short or single word (also indicates break)
                        next_is_very_short_word = next_stripped and (
                            len(next_stripped) <= 3 or
                            (len(next_stripped.split()) == 1 and len(next_stripped) <= 12)
                        )

                        # Pattern 8: SMART NAME DETECTION (uses auto-extracted book names)
                        is_name_split = False
                        if NAME_DETECTOR_AVAILABLE:
                            is_name_split = should_join_for_name(line, next_line)

                        # Pattern 9: LANGUAGE NAME BOUNDARY DETECTION
                        # Check if this is a language name or proper noun boundary that should be preserved
                        should_preserve = False
                        if LANGUAGE_DETECTOR_AVAILABLE:
                            should_preserve = should_preserve_line_break(line, next_line)

                        # If we should preserve the break, override all join indicators
                        if should_preserve:
                            should_join = False
                        elif (is_lowercase or ends_with_joiner or ends_with_comma or
                            ends_with_verb or prev_ends_dash or
                            is_pronoun_line or ends_with_article or ends_with_common_noun or
                            is_very_short or is_single_short_word or ends_with_connector or
                            next_is_very_short_word or is_name_split):
                            should_join = True

            if should_join and next_content_idx is not None:
                # Join current line with next content line
                next_line = lines[next_content_idx].strip()

                # If line ends with a joiner/verb/connector/pronoun, lowercase the first char of next line
                # because it was only capitalized due to being at line start
                lowercase_triggers = ('qua', 'ở', 'tại', 'trong', 'ngoài', 'trên', 'dưới',
                                    'và', 'hoặc', 'nhưng', 'mà', 'với', 'của', 'cho',
                                    'đến', 'từ', 'về', 'ra', 'vào', 'lên', 'xuống', 'bên', 'khi',
                                    'nói', 'hỏi', 'trả lời', 'thốt', 'nói thêm', 'tiếp tục',
                                    'giải thích', 'thì thầm', 'hét', 'thét', 'la', 'gọi',
                                    'của', 'về', 'cho', 'với', 'bởi', 'từ', 'đến',
                                    'theo', 'để', 'khi', 'nếu', 'vì', 'mà', 'nhưng',
                                    'như', 'thì', 'vẫn', 'đã', 'sẽ', 'đang', 'còn',
                                    'nó', 'tôi', 'cô', 'anh', 'chúng', 'họ', 'em',
                                    'ta', 'chị', 'mình', 'bạn')

                # Check if should lowercase
                should_lowercase = (
                    any(line.strip().lower().endswith(' ' + word) for word in lowercase_triggers) or
                    line.strip().lower() in ('nó', 'tôi', 'cô', 'anh', 'chúng', 'họ', 'em', 'ta', 'chị', 'mình', 'bạn', 'ông', 'bà')
                )

                if should_lowercase:
                    # Lowercase first character
                    if next_line and next_line[0].isupper():
                        next_line = next_line[0].lower() + next_line[1:]

                joined = line + ' ' + next_line + '\n'
                fixed_lines.append(joined)

                # Add any comments that were between them
                for comment_idx in comments_between:
                    fixed_lines.append(lines[comment_idx])

                fixes_this_pass += 1
                i = next_content_idx + 1  # Skip to after the joined line
            else:
                # Keep line as-is
                fixed_lines.append(lines[i])
                i += 1

        total_fixes += fixes_this_pass
        lines = fixed_lines
        pass_num += 1

        # If no fixes in this pass, we're done
        if fixes_this_pass == 0:
            break

    # Restore blank lines around markers whose source boundary is standalone.
    # A join (or an earlier pass) may have glued adjacent prose to the marker;
    # re-separate it so the block structure matches the source again.
    if protect_pages:
        lines = _ensure_standalone_markers(lines, protect_pages)

    # Write fixed content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return total_fixes


def _ensure_standalone_markers(lines, protect_pages):
    """Force a blank line before/after each protected page marker.

    ``lines`` is a list of raw lines (some may not end with newline after a
    join). Returns a new list with the marker isolated as its own block.

    Only ever inserts blank lines around protected markers — it never removes
    or rewrites content it did not add, so unrelated blank lines elsewhere in
    the document are left untouched. At most one trailing blank line is trimmed
    if this function itself appended one at end-of-file.
    """
    out = []
    factory_trailing = False
    need_blank_after = False
    for raw in lines:
        # A marker we just emitted still needs a blank line before whatever
        # follows it — insert it on the next line that is not already blank
        # (including an adjacent marker), or once at end-of-file if the marker
        # is the last line. Blank lines already present are left as-is.
        if need_blank_after and not PAGE_MARKER_NUM_RE.fullmatch(raw.strip()):
            if raw.strip():
                out.append('\n')
            need_blank_after = False

        text = raw.rstrip('\n')
        stripped = text.strip()
        full = PAGE_MARKER_NUM_RE.fullmatch(stripped)
        glued = None if full else PAGE_MARKER_NUM_RE.search(text)
        is_protected = bool(
            (full and full.group(1) in protect_pages)
            or (glued and glued.group(1) in protect_pages and not stripped.startswith('<!--'))
        )
        if is_protected:
            # A marker glued mid-line to preceding prose (only reachable when
            # the line does not start with `<!--`, which the main loop already
            # passes through untouched) — split the marker onto its own line
            # rather than silently leaving the drift in place.
            if glued:
                prefix, suffix = text[:glued.start()].rstrip(), text[glued.end():].strip()
                if prefix:
                    out.append(prefix + '\n')
                    out.append('\n')
                out.append(f'<!-- Page {glued.group(1)} -->\n')
                if suffix:
                    out.append('\n')
                    out.append(suffix + '\n')
                    factory_trailing = False
                    need_blank_after = False
                else:
                    factory_trailing = True
                    need_blank_after = True
                continue

            # Already its own line — only insert separators that are missing,
            # so repeated runs are idempotent. A preceding marker (an adjacent
            # protected one) needs a blank line between it and this one too.
            if out and out[-1].strip():
                out.append('\n')
            out.append(f'<!-- Page {full.group(1)} -->\n')
            factory_trailing = True
            need_blank_after = True
            continue

        out.append(raw if raw.endswith('\n') else raw + '\n' if raw else raw)
        factory_trailing = False

    if need_blank_after:
        out.append('\n')
        factory_trailing = True

    # Trim at most one trailing blank line, and only if we appended it.
    if factory_trailing and out and not out[-1].strip():
        out.pop()
    while len(out) >= 2 and not out[-1].strip() and not out[-2].strip():
        out.pop()
    return out

def main():
    """Fix sentence breaks in translated files."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix unexpected sentence breaks in Vietnamese translated files'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Files to fix (default: all chunk_*.md in translated/)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check for issues, do not fix'
    )
    add_book_argument(parser)

    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # Default: all translated Vietnamese files for the active book
        translated_dir = get_config_from_args(args).translated_dir
        if not translated_dir.exists():
            print(f"Error: translated directory not found: {translated_dir}")
            return
        files = sorted(translated_dir.glob('chunk_*.md'))

    if not files:
        print("No files to process")
        return

    print(f"Processing {len(files)} files...\n")

    total_fixes = 0
    files_fixed = 0

    for filepath in files:
        if args.check_only:
            # Just report issues
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            issue_count = 0
            for i in range(len(lines) - 1):
                line = lines[i].rstrip()
                next_line = lines[i + 1].rstrip()

                if not line or not next_line:
                    continue
                if line.startswith(('#', '<!--', '-', '*', '>')):
                    continue
                if next_line.startswith(('#', '<!--', '-', '*', '>')):
                    continue

                sentence_endings = ('.', '!', '?', '...', '—', '"', '»', ')', ']', '…')
                if not line.endswith(sentence_endings):
                    next_stripped = next_line.lstrip()
                    if next_stripped:
                        first_char = next_stripped[0]
                        if (first_char.islower() or
                            first_char in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'):
                            if len(line.strip()) > 10:
                                issue_count += 1

            if issue_count > 0:
                print(f"  {filepath.name}: {issue_count} issues")
                total_fixes += issue_count
        else:
            # Apply fixes
            fixes = fix_sentence_breaks(filepath, backup=not args.no_backup)
            if fixes > 0:
                print(f"✓ {filepath.name}: Fixed {fixes} sentence breaks")
                total_fixes += fixes
                files_fixed += 1

    print(f"\n{'=' * 60}")
    if args.check_only:
        print(f"Found {total_fixes} sentence breaks across {len(files)} files")
        print("Run without --check-only to fix them")
    else:
        print(f"Fixed {total_fixes} sentence breaks in {files_fixed} files")
        if total_fixes > 0 and not args.no_backup:
            print("Backup files created with .bak extension")


if __name__ == '__main__':
    main()
