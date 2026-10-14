#!/usr/bin/env python3
"""Detect `<!-- Page N -->` boundaries in markdown and compare them source↔VI.

A page marker has exactly one of two *boundaries*:

- ``standalone`` — the marker is its own blank-line-delimited block
- ``inline``     — the marker sits inside a block, between two prose lines

The boundary must match between source and translation. Extraction frequently
cuts a sentence mid-paragraph at a page turn, so either form is valid — but the
translation must not change it. Used by ``scripts/fix.py
(--preserve-page-marker-boundaries)`` and ``compare-structure.py``.
"""

import re
from pathlib import Path
from typing import Dict, List

PAGE_MARKER_RE = re.compile(r'<!-- Page (\d+) -->')
STANDALONE_RE = re.compile(r'^<!-- Page (\d+) -->$')


def split_blocks(text: str) -> List[str]:
    """Blank-line-delimited blocks, stripped, empty ones dropped."""
    return [b.strip() for b in text.split('\n\n') if b.strip()]


def marker_boundaries(text: str) -> Dict[str, str]:
    """Map page number → 'standalone' | 'inline'.

    A page number repeated in both forms is reported as 'inline' (the more
    constrained form, and the one that needs fixing when it drifts).
    """
    boundaries: Dict[str, str] = {}
    for block in split_blocks(text):
        match = STANDALONE_RE.match(block)
        if match:
            page = match.group(1)
            if boundaries.get(page) != 'inline':
                boundaries[page] = 'standalone'
            continue
        if '<!-- Page' not in block:
            continue
        for line in block.split('\n'):
            line_match = re.match(r'^\s*<!-- Page (\d+) -->\s*$', line)
            if line_match:
                boundaries[line_match.group(1)] = 'inline'
    return boundaries


def compare_boundaries(source_text: str, translated_text: str) -> List[Dict[str, str]]:
    """Markers whose boundary differs between source and translation."""
    source = marker_boundaries(source_text)
    translated = marker_boundaries(translated_text)
    issues = []
    for page in sorted(set(source) | set(translated), key=int):
        src = source.get(page)
        tgt = translated.get(page)
        if src != tgt:
            issues.append({
                'page': page,
                'source': src or 'missing',
                'translated': tgt or 'missing',
            })
    return issues


def find_standalone_drift(source_path: Path, translated_path: Path) -> List[str]:
    """Pages that are standalone in source but inline in the translation.

    Those are exactly the markers ``fix.py`` must not collapse when
    ``--preserve-page-marker-boundaries`` is on.
    """
    issues = compare_boundaries(
        source_path.read_text(encoding='utf-8'),
        translated_path.read_text(encoding='utf-8'),
    )
    return [i['page'] for i in issues if i['source'] == 'standalone']
