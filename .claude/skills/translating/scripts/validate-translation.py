#!/usr/bin/env python3
"""
Translation Quality Validator

Validates translated files against source for quality metrics:
- Paragraph count match
- Word count variance
- Untranslated text detection
- Glossary consistency
- Format compliance

Usage:
    python validate-translation.py --source chunks/chunk_001.md --translated translated/chunk_001.md
    python validate-translation.py --source chunks/chunk_001.md --translated translated/chunk_001.md --glossary style/glossary.csv
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.utils.terminology import load_terminology


def count_paragraphs(text: str) -> int:
    """Count non-empty paragraphs."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return len(paragraphs)


def count_words(text: str) -> int:
    """Count words in text."""
    # Remove markdown formatting
    clean = re.sub(r'[#*_`\[\]()]', '', text)
    words = clean.split()
    return len(words)


def load_book_name_exceptions(book_names_path: Path | None = None) -> List[str]:
    """Load proper-noun exceptions from a book's name database.

    Falls back to an empty list when the database is absent, so a missing
    file never silently whitelists nothing unexpectedly.
    """
    if book_names_path is None:
        book_names_path = Path('style/book_names.json')
    if not book_names_path.exists():
        return []
    try:
        import json
        data = json.loads(book_names_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return []
    names = set(data.get('full_names', {})) | set(data.get('individual_names', []))
    return [re.escape(n) for n in sorted(names) if len(n) > 1]


def detect_english_text(text: str, exceptions: List[str] | None = None) -> List[Tuple[int, str]]:
    """Detect potentially untranslated English text.

    Args:
        text: Translated text to scan.
        exceptions: Regex patterns for proper nouns / technical terms to allow.
            Callers should pass book-specific names (see load_book_name_exceptions).
    """
    issues = []
    lines = text.split('\n')

    # Common English words that shouldn't appear in Vietnamese translation
    english_patterns = [
        r'\b(the|and|or|but|with|from|have|has|had|was|were|been|being)\b',
        r'\b(this|that|these|those|which|what|when|where|who|how)\b',
        r'\b(would|could|should|might|must|will|shall)\b',
        r'\b(because|although|however|therefore|meanwhile)\b',
    ]

    exceptions = exceptions or []

    for i, line in enumerate(lines, 1):
        # Skip empty lines and markdown headers
        if not line.strip() or line.startswith('#'):
            continue

        for pattern in english_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                # Check if it's an exception
                is_exception = any(re.search(exc, line, re.IGNORECASE) for exc in exceptions)
                if not is_exception:
                    issues.append((i, f"Possible untranslated: '{matches[0]}' in: {line[:60]}..."))

    return issues


def check_glossary_consistency(
    source_text: str,
    translated_text: str,
    glossary_path: Path | None,
    new_terms_path: Path | None = None,
) -> List[str]:
    """Require merged terminology targets only for terms present in the source."""
    if glossary_path is None or not glossary_path.exists():
        return []

    if new_terms_path is None:
        new_terms_path = glossary_path.with_name("new_terms.txt")

    issues = []
    translated_folded = translated_text.casefold()
    for term in load_terminology(glossary_path, new_terms_path).values():
        target = term.target.casefold()
        if "first mention" in term.context.casefold():
            base_target = re.sub(r"\s*\([^)]*\)", "", target).strip()
            if base_target:
                target = base_target
        source_pattern = rf"(?<!\w){re.escape(term.source)}(?!\w)"
        if re.search(source_pattern, source_text, re.IGNORECASE) and target not in translated_folded:
            issues.append(
                f"Term '{term.source}' found in source but translation '{term.target}' not used"
            )
    return issues


def check_formatting(text: str) -> List[str]:
    """Check for common formatting issues."""
    issues = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        # Check dialogue formatting (should use -, not quotes for dialogue)
        if re.match(r'^[""].*[""]$', line.strip()):
            issues.append(f"Line {i}: Dialogue should use dash (-), not quotes")

        # Check for double spaces
        if '  ' in line:
            issues.append(f"Line {i}: Double space detected")

        # Check for mid-sentence line breaks (lowercase start after newline)
        if i > 1 and lines[i-2].strip() and not lines[i-2].strip().endswith(('.', '?', '!', ':', '-')):
            if line.strip() and line.strip()[0].islower():
                issues.append(f"Line {i}: Possible mid-sentence break")

    return issues


# Structural markers the export depends on: front-matter blocks (TOC link
# targets, styling) and page markers. Copied verbatim, never translated or dropped.
STRUCTURE_MARKER_RE = re.compile(r'<!--\s*(?:/front|front\b[^>]*?|Page\s*\d+)\s*-->')


def check_structure_markers(source_text: str, translated_text: str) -> List[str]:
    """Errors when the translation's marker sequence differs from the source's."""
    def markers(text):
        return [re.sub(r'\s+', ' ', m) for m in STRUCTURE_MARKER_RE.findall(text)]

    src, dst = markers(source_text), markers(translated_text)
    if src == dst:
        return []
    missing = [m for m in src if m not in dst]
    extra = [m for m in dst if m not in src]
    detail = f"missing {missing}" if missing else ""
    detail += ("; " if detail and extra else "") + (f"unexpected {extra}" if extra else "")
    return [f"Structure markers differ from source ({detail or 'order changed'}): "
            "copy <!-- front ... -->, <!-- /front --> and <!-- Page N --> verbatim"]


# Inline small caps (speaker labels, `LET AGREED`, `B.C.`) are kept in English
# and copied verbatim: same spans, same order. See docs/markup-conventions.md.
SMALL_CAPS_RE = re.compile(r'<span class="sc">(.*?)</span>')
# A whole-paragraph `<small>` with letters, wedged mid-sentence (previous
# paragraph unfinished, next one lowercase), is an inline run the extractor
# tore out of its line (`my way - , one says` + `<small>LET AGREED</small>`).
ORPHAN_SMALL_RE = re.compile(r'^<small>(?=[^<]*[^\W\d_])[^<]*</small>$')
SENTENCE_END_RE = re.compile(r'[.?!…:;"”’)*\]]$')


def check_small_caps(source_text: str, translated_text: str) -> List[str]:
    """Errors when `<span class="sc">` spans drift from the source's.

    Speaker labels (a span opening a paragraph, `LABEL</span>:`) stay English,
    verbatim and in order. Inline spans (B.C., a sign's text) may be localised
    (B.C. -> TCN) but their count must match, so none is dropped or added.
    """
    def split(text):
        labels = re.findall(r'^<span class="sc">(.*?)</span>:', text, re.M)
        return labels, len(SMALL_CAPS_RE.findall(text)) - len(labels)

    (src_labels, src_inline), (dst_labels, dst_inline) = split(source_text), split(translated_text)
    issues = []
    if src_labels != dst_labels:
        issues.append(f"Speaker labels differ from source (source {src_labels[:5]}…, "
                      f"translated {dst_labels[:5]}…): copy <span class=\"sc\">LABEL</span> verbatim, in English")
    if src_inline != dst_inline:
        issues.append(f"Inline small-caps count differs from source ({src_inline} vs {dst_inline}): "
                      'keep one <span class="sc">…</span> per source span')
    return issues


def check_orphan_small(text: str, label: str = "translated") -> List[str]:
    """Errors for standalone `<small>` paragraphs that split a sentence."""
    paras = [p.strip() for p in re.split(r'\n\s*\n', text)]
    issues = []
    for i in range(1, len(paras) - 1):
        prev, cur, nxt = paras[i - 1], paras[i], paras[i + 1]
        if (ORPHAN_SMALL_RE.match(cur) and prev and not prev.startswith(('<', '#'))
                and not SENTENCE_END_RE.search(prev) and nxt.lstrip('*_')[:1].islower()):
            issues.append(f"Orphaned inline <small> in {label}: {cur!r} splits a sentence; "
                          'inline small caps must be <span class="sc"> inside the sentence')
    # A transcript turn whose label was torn away starts with the bare colon.
    issues.extend(f"Speaker turn without label in {label}: {p[:40]!r}; "
                  'expected <span class="sc">LABEL</span>: …'
                  for p in paras if re.match(r'^:\s', p))
    return issues


def validate(
    source_path: Path,
    translated_path: Path,
    glossary_path: Path = None,
    book_names_path: Path = None,
) -> Dict:
    """Run all validations and return results."""
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'metrics': {}
    }

    # Read files
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            source_text = f.read()
        with open(translated_path, 'r', encoding='utf-8') as f:
            translated_text = f.read()
    except FileNotFoundError as e:
        results['valid'] = False
        results['errors'].append(f"File not found: {e}")
        return results

    results['errors'].extend(check_structure_markers(source_text, translated_text))
    results['errors'].extend(check_small_caps(source_text, translated_text))
    results['errors'].extend(check_orphan_small(source_text, "source"))
    results['errors'].extend(check_orphan_small(translated_text))

    # Paragraph count
    source_para = count_paragraphs(source_text)
    translated_para = count_paragraphs(translated_text)
    results['metrics']['source_paragraphs'] = source_para
    results['metrics']['translated_paragraphs'] = translated_para

    if source_para != translated_para:
        diff = translated_para - source_para
        results['warnings'].append(
            f"Paragraph count mismatch: source={source_para}, translated={translated_para} ({diff:+d})"
        )

    # Word count variance
    source_words = count_words(source_text)
    translated_words = count_words(translated_text)
    variance = abs(translated_words - source_words) / source_words * 100 if source_words > 0 else 0
    results['metrics']['source_words'] = source_words
    results['metrics']['translated_words'] = translated_words
    results['metrics']['word_variance_percent'] = round(variance, 1)

    if variance > 30:
        results['warnings'].append(
            f"High word count variance: {variance:.1f}% (source={source_words}, translated={translated_words})"
        )

    # Untranslated text detection
    english_issues = detect_english_text(
        translated_text,
        exceptions=load_book_name_exceptions(book_names_path),
    )
    for line_num, issue in english_issues:
        results['warnings'].append(f"Line {line_num}: {issue}")

    # Glossary consistency
    if glossary_path:
        glossary_issues = check_glossary_consistency(
            source_text,
            translated_text,
            glossary_path,
        )
        for issue in glossary_issues:
            results['warnings'].append(f"Glossary: {issue}")

    # Formatting check
    format_issues = check_formatting(translated_text)
    for issue in format_issues:
        results['warnings'].append(f"Format: {issue}")

    # Determine overall validity
    if results['errors']:
        results['valid'] = False

    return results


def main():
    parser = argparse.ArgumentParser(description='Validate translation quality')
    parser.add_argument('--source', '-s', required=True, help='Source file path')
    parser.add_argument('--translated', '-t', required=True, help='Translated file path')
    parser.add_argument('--glossary', '-g', help='Glossary file path (optional)')
    parser.add_argument(
        '--book-names',
        help='Book name database (default: style/book_names.json)',
    )
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    source_path = Path(args.source)
    translated_path = Path(args.translated)
    glossary_path = Path(args.glossary) if args.glossary else None
    book_names_path = Path(args.book_names) if args.book_names else None

    results = validate(source_path, translated_path, glossary_path, book_names_path)

    if args.json:
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"Translation Validation Report")
        print(f"{'='*60}")
        print(f"Source: {source_path}")
        print(f"Translated: {translated_path}")
        print(f"{'='*60}")

        print(f"\nMetrics:")
        print(f"  Paragraphs: {results['metrics']['source_paragraphs']} → {results['metrics']['translated_paragraphs']}")
        print(f"  Words: {results['metrics']['source_words']} → {results['metrics']['translated_words']} ({results['metrics']['word_variance_percent']}% variance)")

        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for err in results['errors']:
                print(f"  [ERROR] {err}")

        if results['warnings']:
            print(f"\nWarnings ({len(results['warnings'])}):")
            for warn in results['warnings'][:10]:  # Limit to 10
                print(f"  [WARN] {warn}")
            if len(results['warnings']) > 10:
                print(f"  ... and {len(results['warnings']) - 10} more")

        print(f"\n{'='*60}")
        if results['valid'] and not results['warnings']:
            print("Result: PASSED")
        elif results['valid']:
            print(f"Result: PASSED with {len(results['warnings'])} warnings")
        else:
            print("Result: FAILED")
        print(f"{'='*60}\n")

    sys.exit(0 if results['valid'] else 1)


if __name__ == '__main__':
    main()
