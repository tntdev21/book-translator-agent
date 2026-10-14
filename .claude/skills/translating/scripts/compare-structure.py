#!/usr/bin/env python3
"""
Translation Structure Comparator

Compares source and translated file structures:
- Paragraph alignment
- Section/chapter mapping
- Structural differences visualization

Usage:
    python compare-structure.py --source chunks/chunk_001.md --translated translated/chunk_001.md
    python compare-structure.py -s chunks/chunk_001.md -t translated/chunk_001.md --detailed
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

_REPO_ROOT = Path(__file__).resolve().parents[4]
_BOUNDARIES_PATH = _REPO_ROOT / "scripts" / "utils" / "page_marker_boundaries.py"
if _BOUNDARIES_PATH.is_file():
    _spec = importlib.util.spec_from_file_location("page_marker_boundaries", _BOUNDARIES_PATH)
    _boundaries = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_boundaries)
else:  # script copied outside the repo — degrade to no boundary reporting
    _boundaries = None
    print(
        f"Warning: page-marker boundary module not found at {_BOUNDARIES_PATH}; "
        "page-marker boundary checking is skipped for this run.",
        file=sys.stderr,
    )


@dataclass
class Paragraph:
    index: int
    text: str
    word_count: int
    is_header: bool
    header_level: int


def extract_structure(text: str) -> List[Paragraph]:
    """Extract paragraph structure from text."""
    paragraphs = []
    blocks = text.split('\n\n')

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        # Check if header
        is_header = block.startswith('#')
        header_level = 0
        if is_header:
            header_level = len(re.match(r'^#+', block).group())

        # Count words
        clean = re.sub(r'[#*_`\[\]()]', '', block)
        word_count = len(clean.split())

        paragraphs.append(Paragraph(
            index=len(paragraphs),
            text=block[:100] + ('...' if len(block) > 100 else ''),
            word_count=word_count,
            is_header=is_header,
            header_level=header_level
        ))

    return paragraphs


def compare_structures(source: List[Paragraph], translated: List[Paragraph]) -> Dict:
    """Compare two paragraph structures."""
    result = {
        'source_count': len(source),
        'translated_count': len(translated),
        'count_diff': len(translated) - len(source),
        'alignments': [],
        'issues': []
    }

    # Simple alignment (1:1 comparison)
    max_len = max(len(source), len(translated))

    for i in range(max_len):
        src = source[i] if i < len(source) else None
        tgt = translated[i] if i < len(translated) else None

        alignment = {
            'index': i,
            'source': None,
            'translated': None,
            'status': 'ok'
        }

        if src:
            alignment['source'] = {
                'preview': src.text,
                'words': src.word_count,
                'is_header': src.is_header
            }

        if tgt:
            alignment['translated'] = {
                'preview': tgt.text,
                'words': tgt.word_count,
                'is_header': tgt.is_header
            }

        # Detect issues
        if src and not tgt:
            alignment['status'] = 'missing_translation'
            result['issues'].append(f"Para {i}: Missing translation")
        elif tgt and not src:
            alignment['status'] = 'extra_paragraph'
            result['issues'].append(f"Para {i}: Extra paragraph in translation")
        elif src and tgt:
            # Check header alignment
            if src.is_header != tgt.is_header:
                alignment['status'] = 'header_mismatch'
                result['issues'].append(f"Para {i}: Header mismatch (source={src.is_header}, translated={tgt.is_header})")
            # Check significant word count difference
            elif src.word_count > 0:
                variance = abs(tgt.word_count - src.word_count) / src.word_count
                if variance > 0.5:  # 50% variance threshold
                    alignment['status'] = 'word_count_warning'

        result['alignments'].append(alignment)

    return result


def page_marker_boundary_issues(source_text: str, translated_text: str) -> List[Dict]:
    """Markers whose boundary (standalone vs inline) differs source↔translated.

    Reported separately from paragraph-alignment issues so an agent can pinpoint
    the exact seam instead of inferring it from a cascaded block-count delta.
    """
    if _boundaries is None:
        return []
    return _boundaries.compare_boundaries(source_text, translated_text)


def print_comparison(result: Dict, detailed: bool = False):
    """Print comparison in human-readable format."""
    print(f"\n{'='*70}")
    print("Structure Comparison Report")
    print(f"{'='*70}")

    print(f"\nParagraph Counts:")
    print(f"  Source:     {result['source_count']}")
    print(f"  Translated: {result['translated_count']}")
    diff = result['count_diff']
    if diff != 0:
        print(f"  Difference: {diff:+d} {'(extra)' if diff > 0 else '(missing)'}")
    else:
        print(f"  Difference: 0 (matched)")

    if result['issues']:
        print(f"\nIssues Found ({len(result['issues'])}):")
        for issue in result['issues'][:10]:
            print(f"  - {issue}")
        if len(result['issues']) > 10:
            print(f"  ... and {len(result['issues']) - 10} more")

    if detailed:
        print(f"\nDetailed Alignment:")
        print(f"{'Idx':<4} {'Source':<30} {'Words':<6} {'Translated':<30} {'Words':<6} {'Status':<10}")
        print(f"{'-'*4} {'-'*30} {'-'*6} {'-'*30} {'-'*6} {'-'*10}")

        for align in result['alignments'][:20]:  # Limit display
            src_preview = align['source']['preview'][:28] if align['source'] else '---'
            src_words = str(align['source']['words']) if align['source'] else '---'
            tgt_preview = align['translated']['preview'][:28] if align['translated'] else '---'
            tgt_words = str(align['translated']['words']) if align['translated'] else '---'

            status_icon = {
                'ok': '',
                'missing_translation': '[MISS]',
                'extra_paragraph': '[EXTRA]',
                'header_mismatch': '[HDR]',
                'word_count_warning': '[WORD]'
            }.get(align['status'], '')

            print(f"{align['index']:<4} {src_preview:<30} {src_words:<6} {tgt_preview:<30} {tgt_words:<6} {status_icon:<10}")

        if len(result['alignments']) > 20:
            print(f"... and {len(result['alignments']) - 20} more paragraphs")

    print(f"\n{'='*70}")
    boundary_issues = result.get('boundary_issues', [])
    if boundary_issues:
        print(f"\nPage-Marker Boundary Mismatches ({len(boundary_issues)}):")
        for issue in boundary_issues:
            print(f"  Page {issue['page']}: source={issue['source']}, translated={issue['translated']}")

    if not result['issues']:
        print("Result: STRUCTURES MATCH")
    else:
        print(f"Result: {len(result['issues'])} ISSUES FOUND")
    print(f"{'='*70}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare translation structure')
    parser.add_argument('--source', '-s', required=True, help='Source file path')
    parser.add_argument('--translated', '-t', required=True, help='Translated file path')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed alignment')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--ignore-boundary', action='store_true',
                        help='Exit 0 when only page-marker boundary mismatches remain '
                             '(accepted residual; orchestrator accept gate)')

    args = parser.parse_args(argv)

    source_path = Path(args.source)
    translated_path = Path(args.translated)

    # Read files
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            source_text = f.read()
        with open(translated_path, 'r', encoding='utf-8') as f:
            translated_text = f.read()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Extract and compare
    source_struct = extract_structure(source_text)
    translated_struct = extract_structure(translated_text)
    result = compare_structures(source_struct, translated_struct)
    boundary_issues = page_marker_boundary_issues(source_text, translated_text)
    result['boundary_issues'] = boundary_issues

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_comparison(result, args.detailed)

    if args.ignore_boundary:
        boundary_issues = []
    return 1 if (result['issues'] or boundary_issues) else 0


if __name__ == '__main__':
    exit(main())
