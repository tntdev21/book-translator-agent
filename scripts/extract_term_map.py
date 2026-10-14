#!/usr/bin/env python3
"""
Extract a compact term→rendering→chunk_id map from translated chunks.

Purpose
-------
The editor agent's "Pass 2: Across Chunks" previously required loading all
translated chunks into context (~97K tokens for a 35-chunk book), which is
prohibitive. This script produces a single small JSON (`term_map.json`) that
captures which Vietnamese rendering of each tracked term appears in which
chunk. The editor can then read only the term map (a few KB) plus the two
adjacent chunks it is currently reviewing, instead of all 35 chunks.

Output schema
-------------
{
  "schema_version": 1,
  "book_id": "my-book",
  "generated_at": "2026-10-01T12:00:00Z",
  "totals": {"terms": 30, "renderings": 47, "chunks_scanned": 35},
  "terms": [
    {
      "source": "site-specificity",
      "renderings": [
        {"vi": "tính đặc thù theo địa điểm",
         "chunks": ["chunk_009", "chunk_011"],
         "count": 5}
      ],
      "drift": false
    },
    ...
  ],
  "drift_candidates": [
    {
      "source": "site-specificity",
      "renderings": ["tính đặc thù theo địa điểm", "tính đặc thù theo từng đêm diễn"],
      "chunks_by_rendering": {
        "tính đặc thù theo địa điểm": ["chunk_009"],
        "tính đặc thù theo từng đêm diễn": ["chunk_011"]
      }
    },
    ...
  ]
}

Pure stdlib. No external dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.book_config import load_book  # noqa: E402

CHUNK_PATTERN = re.compile(r"chunk_(\d{3})\.md$")
HEADING_LINE = re.compile(r"^\s*#+\s")            # skip headings
PAGE_MARKER = re.compile(r"^\s*<\s*!\s*-")        # skip page markers
TOC_LINE = re.compile(r"Mục lục\s+Bìa")          # skip TOC bleed


def is_renderable_line(line: str) -> bool:
    """Return False for headings / page markers / TOC bleed lines."""
    if not line.strip():
        return False
    if HEADING_LINE.match(line):
        return False
    if PAGE_MARKER.match(line):
        return False
    if TOC_LINE.search(line):
        return False
    return True


def load_new_terms_rows(new_terms_path: Path) -> List[Tuple[str, str, str]]:
    """
    Parse new_terms.txt. Each entry is `source | translation | context | chunk_id`.
    Returns [(source_term, vietnam_translation, context), ...].
    Skips malformed lines silently.
    """
    entries: List[Tuple[str, str, str]] = []
    if not new_terms_path.exists():
        return entries
    with open(new_terms_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2:
                continue
            source = parts[0]
            target = parts[1]
            context = parts[2] if len(parts) > 2 else ""
            if source and target:
                entries.append((source, target, context))
    return entries


def load_terms_from_new_terms(new_terms_path: Path) -> List[Tuple[str, str]]:
    """Return [(source_term, vietnam_translation), ...] from new_terms.txt."""
    return [(s, t) for s, t, _ in load_new_terms_rows(new_terms_path)]


def load_glossary_rows(glossary_path: Path) -> List[Tuple[str, str, str]]:
    """
    Parse glossary.csv. Columns: source_term,target_term,context,chunk_id.
    Returns [(source_term, vietnam_translation, context), ...].
    Skips header and malformed rows.
    """
    entries: List[Tuple[str, str, str]] = []
    if not glossary_path.exists():
        return entries
    with open(glossary_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            source = row[0].strip()
            target = row[1].strip()
            # Skip header
            if source == "source_term" and target == "target_term":
                continue
            context = row[2].strip() if len(row) > 2 else ""
            if source and target:
                entries.append((source, target, context))
    return entries


def load_terms_from_glossary(glossary_path: Path) -> List[Tuple[str, str]]:
    """Return [(source_term, vietnam_translation), ...] from glossary.csv."""
    return [(s, t) for s, t, _ in load_glossary_rows(glossary_path)]


def discover_chunks(translated_dir: Path) -> List[Path]:
    """Return sorted list of chunk_NNN.md files."""
    return sorted(translated_dir.glob("chunk_*.md"))


def scan_chunk_for_renderings(
    chunk_path: Path,
    renderings: Iterable[str],
) -> Dict[str, int]:
    """
    Count occurrences of each rendering inside a chunk's renderable lines.
    Returns {rendering: count}.
    """
    counts: Dict[str, int] = {}
    with open(chunk_path, "r", encoding="utf-8") as f:
        text = f.read()
    for line in text.splitlines():
        if not is_renderable_line(line):
            continue
        for r in renderings:
            if r in line:
                counts[r] = counts.get(r, 0) + 1
    return counts


def build_term_map(
    translated_dir: Path,
    term_pairs: List[Tuple[str, str]],
) -> Tuple[dict, List[Path]]:
    """
    Build the term_map dict from chunk scans.

    Returns (term_map, scanned_chunk_paths).
    """
    chunks = discover_chunks(translated_dir)
    # Group target translations by source term
    by_source: Dict[str, List[str]] = {}
    for source, target in term_pairs:
        by_source.setdefault(source, [])
        if target not in by_source[source]:
            by_source[source].append(target)

    terms_out: List[dict] = []
    drift_candidates: List[dict] = []
    renderings_total = 0

    # Stable order: sort by source term
    for source in sorted(by_source.keys()):
        renderings = by_source[source]
        renderings_records: List[dict] = []
        # Scan each chunk
        chunk_hits: Dict[str, Dict[str, int]] = {}  # rendering -> {chunk_id: count}
        for chunk_path in chunks:
            m = CHUNK_PATTERN.search(chunk_path.name)
            if not m:
                continue
            chunk_id = f"chunk_{m.group(1)}"
            counts = scan_chunk_for_renderings(chunk_path, renderings)
            for r, c in counts.items():
                if c > 0:
                    chunk_hits.setdefault(r, {})[chunk_id] = c

        # Emit records sorted by rendering
        for r in sorted(renderings):
            hits = chunk_hits.get(r, {})
            if not hits:
                # Skip renderings not actually present in any chunk
                continue
            renderings_records.append(
                {
                    "vi": r,
                    "chunks": sorted(hits.keys()),
                    "count": sum(hits.values()),
                }
            )
            renderings_total += 1

        # Only include term in output if at least one rendering has hits
        if not renderings_records:
            continue

        has_drift = len(renderings_records) > 1
        term_record = {
            "source": source,
            "renderings": renderings_records,
            "drift": has_drift,
        }
        terms_out.append(term_record)
        if has_drift:
            drift_candidates.append(
                {
                    "source": source,
                    "renderings": [rec["vi"] for rec in renderings_records],
                    "chunks_by_rendering": {
                        rec["vi"]: rec["chunks"] for rec in renderings_records
                    },
                }
            )

    # Cross-term pattern groups: detect families of terms whose VI
    # renderings share a long common prefix/suffix, e.g.
    #   site-specificity    -> "tính đặc thù theo địa điểm"
    #   night-specificity  -> "tính đặc thù theo từng đêm diễn"
    # These are different source terms so they don't show up as
    # same-source drift, but the bounded editor should notice that the
    # "tính đặc thù theo ..." prefix is reused inconsistently.
    pattern_groups = build_pattern_groups(terms_out)

    return (
        {
            "schema_version": 1,
            "book_id": translated_dir.parent.name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "totals": {
                "terms": len(terms_out),
                "renderings": renderings_total,
                "chunks_scanned": len(chunks),
                "pattern_groups": len(pattern_groups),
            },
            "terms": terms_out,
            "drift_candidates": drift_candidates,
            "pattern_groups": pattern_groups,
        },
        chunks,
    )


def _normalize_for_pattern(text: str) -> str:
    """Lowercase + collapse whitespace for fuzzy prefix matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def build_pattern_groups(terms_out: List[dict]) -> List[dict]:
    """
    Group terms whose primary rendering shares a long Vietnamese prefix.

    A "primary rendering" is the rendering with the highest count (ties
    broken by lexicographic order). Two renderings belong to the same
    group when their normalized form shares a leading run of >= 6
    Vietnamese tokens and the suffix after the common prefix is
    non-trivial in both (>= 4 chars). This catches the
    site-specificity / night-specificity case where the shared prefix
    is "tính đặc thù theo" but the suffix differs.
    """
    MIN_PREFIX_TOKENS = 4   # e.g. "tính đặc thù theo" = 4 tokens
    MIN_SUFFIX_CHARS = 4

    # primary rendering -> [(source, vi, chunks)]
    primary_index: Dict[str, List[Tuple[str, str, List[str]]]] = {}
    for t in terms_out:
        renderings = t["renderings"]
        if not renderings:
            continue
        primary = max(renderings, key=lambda r: (r["count"], -len(r["vi"])))
        norm = _normalize_for_pattern(primary["vi"])
        primary_index.setdefault(norm, []).append(
            (t["source"], primary["vi"], primary["chunks"])
        )

    # Group by common-prefix tokens
    by_prefix: Dict[str, List[Tuple[str, str, List[str]]]] = {}
    for norm, items in primary_index.items():
        tokens = norm.split(" ")
        if len(tokens) < MIN_PREFIX_TOKENS + 1:
            continue
        prefix = " ".join(tokens[:MIN_PREFIX_TOKENS])
        by_prefix.setdefault(prefix, []).extend(items)

    groups: List[dict] = []
    for prefix, items in by_prefix.items():
        # Need >= 2 distinct sources sharing this prefix
        distinct_sources = {src for src, _, _ in items}
        if len(distinct_sources) < 2:
            continue
        # Confirm suffixes are non-trivial
        members: List[dict] = []
        for src, vi, chunks in items:
            norm = _normalize_for_pattern(vi)
            suffix = norm[len(prefix):].strip()
            if len(suffix) < MIN_SUFFIX_CHARS:
                continue
            members.append({"source": src, "vi": vi, "chunks": chunks, "suffix": suffix})
        if len(members) < 2:
            continue
        # Flag as drift only if suffixes differ across members
        suffixes = {m["suffix"] for m in members}
        groups.append(
            {
                "prefix": prefix,
                "members": members,
                "drift": len(suffixes) > 1,
            }
        )

    groups.sort(key=lambda g: (-len(g["members"]), g["prefix"]))
    return groups


CONTEXT_MAX = 60


def build_terms_compact(
    glossary_rows: List[Tuple[str, str, str]],
    new_term_rows: List[Tuple[str, str, str]],
    term_map: Optional[dict] = None,
) -> str:
    """
    Compact editor-facing term list: `term → VI`, glossary wins on conflict.

    Context (<=60 chars) is appended only when VI == term (casefold), so
    deliberately retained English terms are not mistaken for log errors (D24).
    Second section `## Drift` lists terms with >1 rendering across chunks.
    """
    merged: Dict[str, Tuple[str, str, str]] = {}
    for rows in (new_term_rows, glossary_rows):  # glossary last -> wins
        for source, vi, context in rows:
            merged[source.casefold()] = (source, vi, context)

    lines: List[str] = []
    for _, (source, vi, context) in sorted(merged.items()):
        line = f"{source} → {vi}"
        if vi.casefold() == source.casefold() and context:
            ctx = context if len(context) <= CONTEXT_MAX else context[:CONTEXT_MAX].rstrip()
            line += f" ({ctx})"
        lines.append(line)

    out = [
        "# Terms (glossary + new_terms) — generated, do not edit",
        f"{len(lines)} terms",
        "",
        *lines,
        "",
        "## Drift",
    ]
    drift_lines: List[str] = []
    for t in (term_map or {}).get("terms", []):
        if not t.get("drift"):
            continue
        parts = [f"{r['vi']} ({', '.join(r['chunks'])})" for r in t["renderings"]]
        drift_lines.append(f"{t['source']} → " + "; ".join(parts))
    out.extend(drift_lines if drift_lines else ["(none)"])
    return "\n".join(out) + "\n"


def resolve_paths(
    translated_dir: Optional[Path],
    new_terms_path: Optional[Path],
    glossary_path: Optional[Path],
    output_path: Optional[Path],
) -> Tuple[Path, Path, Path, Path]:
    """Resolve paths from explicit args or active book config."""
    if translated_dir and new_terms_path and glossary_path and output_path:
        return translated_dir, new_terms_path, glossary_path, output_path
    book = load_book()
    return (
        translated_dir or book.translated_dir,
        new_terms_path or book.new_terms_path,
        glossary_path or (book.style_dir / "glossary.csv"),
        output_path or (book.style_dir / "term_map.json"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract term→rendering→chunk_id map from translated chunks."
    )
    parser.add_argument(
        "--translated-dir",
        type=Path,
        help="Directory containing chunk_NNN.md files. Defaults to active book.",
    )
    parser.add_argument(
        "--new-terms",
        type=Path,
        help="Path to new_terms.txt. Defaults to active book.",
    )
    parser.add_argument(
        "--glossary",
        type=Path,
        help="Path to glossary.csv. Defaults to active book style/glossary.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path. Defaults to active book style/term_map.json.",
    )
    parser.add_argument(
        "--no-compact",
        action="store_true",
        help="Skip writing _terms_compact.md.",
    )
    parser.add_argument(
        "--compact-output",
        type=Path,
        help="Compact terms path. Defaults to <output dir>/_terms_compact.md.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-step progress output.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write indented JSON instead of compact.",
    )
    args = parser.parse_args()

    translated_dir, new_terms_path, glossary_path, output_path = resolve_paths(
        args.translated_dir, args.new_terms, args.glossary, args.output
    )

    if not translated_dir.exists():
        print(f"Error: translated dir not found: {translated_dir}", file=sys.stderr)
        return 1

    new_rows = load_new_terms_rows(new_terms_path)
    glossary_rows = load_glossary_rows(glossary_path)
    term_pairs: List[Tuple[str, str]] = [(s, t) for s, t, _ in new_rows]
    term_pairs.extend((s, t) for s, t, _ in glossary_rows)

    if not term_pairs:
        print("Warning: no terms loaded from new_terms.txt or glossary.csv.",
              file=sys.stderr)

    term_map, chunks = build_term_map(translated_dir, term_pairs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Default to compact JSON: the editor reads this file into its own
    # context, and indent doubles the byte count. Editors don't need
    # whitespace to consume structured JSON. --pretty is for human
    # inspection.
    separators = (",", ": ") if args.pretty else (",", ":")
    indent = 2 if args.pretty else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(term_map, f, ensure_ascii=False, separators=separators, indent=indent)

    compact_path: Optional[Path] = None
    if not args.no_compact:
        compact_path = args.compact_output or (output_path.parent / "_terms_compact.md")
        compact_path.parent.mkdir(parents=True, exist_ok=True)
        compact_path.write_text(
            build_terms_compact(glossary_rows, new_rows, term_map), encoding="utf-8"
        )

    size_bytes = output_path.stat().st_size
    if not args.quiet:
        print(f"Translated dir: {translated_dir}")
        print(f"New terms file: {new_terms_path}")
        print(f"Glossary file:  {glossary_path}")
        print(f"Output:         {output_path}")
        print(f"Chunks scanned: {len(chunks)}")
        print(f"Terms mapped:   {term_map['totals']['terms']}")
        print(f"Renderings:     {term_map['totals']['renderings']}")
        print(f"Drift candidates:{len(term_map['drift_candidates'])}")
        print(f"Output size:    {size_bytes} bytes ({size_bytes/1024:.1f} KB)")
        if compact_path:
            print(f"Compact terms:  {compact_path} ({compact_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())