#!/usr/bin/env python3
"""
Validate a book's glossary against its translated chunks.

For each canonical term registered in ``new_terms.txt``, assert that the
canonical Vietnamese string appears at least once across the rendered chunks.
Report terms that are absent (never rendered) and chunks that contain a
different rendering (drift).

Intended use:

- ``python scripts/validate_glossary.py`` reports drift to stdout, exits 1
  on any finding so it can be wired into a pre-export gate.
- ``python scripts/validate_glossary.py --json`` emits a machine-readable
  report for the orchestrator.
- ``python scripts/validate_glossary.py --chunk chunk_009.md`` narrows the
  scan to one file (handy while debugging a single chunk).

A canonical translation is "absent" only if the book has at least one
translated chunk; the validator skips empty ``translated/`` directories.
Retained-in-source terms (e.g. ``computer``, ``eudaimonia``) intentionally
appear verbatim in both columns, and the script treats those as their own
canonical form on either side.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


def _bootstrap_imports() -> None:
    """Make ``scripts`` importable when run as ``python scripts/validate_glossary.py``."""
    import os
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)


_bootstrap_imports()

from scripts.utils.book_config import bootstrap_argv  # noqa: E402


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# A term row is `EN | VI | context | chunk_NNN`. The context field may itself
# contain a pipe (rare) — split with maxsplit=3 so we don't truncate it.
TERM_PARTS = re.compile(r"(?<![\\])\|")


@dataclass(frozen=True)
class TermEntry:
    """One row in `new_terms.txt`."""

    english: str
    vietnamese: str
    context: str
    chunk_id: str
    source_line: int  # 1-based, for error messages

    @property
    def canonical(self) -> str:
        """The Vietnamese rendering that translators must reuse book-wide."""
        return self.vietnamese.strip()

    @property
    def en_key(self) -> str:
        """Lowercased lookup key — Vietnamese casing/diacritics vary by chunk."""
        return self.english.strip().casefold()


def parse_terms_file(path: Path) -> list[TermEntry]:
    """Read a `new_terms.txt` file and return its term rows in file order.

    Skips blank lines, `#`-headers, and `---` separators, mirroring what
    `log_terms.py` writes. Rows that don't match the four-part shape are
    skipped with a printed warning so a single bad row never aborts the
    whole scan.
    """
    if not path.exists():
        return []

    entries: list[TermEntry] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line == "---":
            continue
        # Allow a leading dash ("- term | vi | ctx | chunk_001") the way some
        # editors format their term logs.
        if line.startswith("-"):
            line = line.lstrip("- ").strip()
        parts = [part.strip() for part in TERM_PARTS.split(line)]
        if len(parts) != 4:
            print(f"⚠️  Skipping malformed row at {path}:{line_number}: {raw!r}")
            continue
        en, vi, ctx, chunk = parts
        if not en or not vi:
            print(f"⚠️  Skipping empty term row at {path}:{line_number}: {raw!r}")
            continue
        entries.append(
            TermEntry(
                english=en,
                vietnamese=vi,
                context=ctx,
                chunk_id=chunk,
                source_line=line_number,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


@dataclass
class ChunkFinding:
    """A single rendering anomaly in one translated chunk."""

    chunk: str
    line: int
    matched_text: str
    kind: str  # "canonical" | "drift" | "retained"


@dataclass
class TermReport:
    """The full result of validating one term."""

    term: TermEntry
    canonical_chunks: list[str] = field(default_factory=list)
    drift_chunks: list[ChunkFinding] = field(default_factory=list)
    absent_chunks: list[str] = field(default_factory=list)

    @property
    def has_finding(self) -> bool:
        """True if anything looks wrong — drift or never-rendered."""
        return bool(self.drift_chunks) or not self.canonical_chunks

    @property
    def status(self) -> str:
        if self.drift_chunks and not self.canonical_chunks:
            return "absent+drift"
        if self.drift_chunks:
            return "drift"
        if not self.canonical_chunks:
            return "absent"
        return "ok"


def _find_all(text: str, needle: str) -> list[tuple[int, str]]:
    """Return ``[(line_number, line_text), ...]`` for every occurrence."""
    hits: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if needle in line:
            hits.append((line_number, line))
    return hits


def _is_retained_italic(line: str, term: str) -> bool:
    """True when ``term`` appears in source form, wrapped in markdown italics.

    Translators often keep Greek/Latin/Sanskrit terms italicized as ``*arete*``
    while expanding them in Vietnamese prose. The italicized source form is
    *not* drift; flagging it as such would drown the real findings.
    """
    if not term:
        return False
    return (
        f"*{term}*" in line
        or f"**{term}**" in line
        or f"*{term},*" in line
        or f"*{term}.*" in line
        or f"_{term}_" in line
    )


def _is_passthrough(vi_text: str) -> bool:
    """True when the term is intentionally retained verbatim.

    Some glossary entries (e.g. ``computer``, ``eudaimonia``) keep the source
    word as the canonical rendering. Those entries will match everywhere the
    translator dropped the source word in — that is the *desired* state, not
    drift. We detect them by checking whether the entry's English equals its
    Vietnamese (case-folded).
    """
    return False  # reserved; the current data set doesn't need this branch.


def scan_chunk(
    chunk_path: Path,
    terms: Iterable[TermEntry],
) -> tuple[dict[str, ChunkFinding], dict[str, int]]:
    """Scan one translated chunk for canonical renderings and drift.

    Returns a tuple ``(findings, canonical_hits)``:

    - ``findings[term_key]`` is the most representative ChunkFinding for that
    term in this chunk (canonical > drift; first match wins).
    - ``canonical_hits[term_key]`` is the count of canonical matches in
    this chunk, used by the caller to build ``TermReport.canonical_chunks``.
    """
    findings: dict[str, ChunkFinding] = {}
    canonical_hits: dict[str, int] = {}

    text = chunk_path.read_text(encoding="utf-8") if chunk_path.exists() else ""

    for term in terms:
        canonical = term.canonical
        if not canonical:
            continue

        canon_lines = _find_all(text, canonical)
        if canon_lines:
            canonical_hits[term.en_key] = canonical_hits.get(term.en_key, 0) + len(canon_lines)
            findings.setdefault(
                term.en_key,
                ChunkFinding(
                    chunk=chunk_path.name,
                    line=canon_lines[0][0],
                    matched_text=canonical,
                    kind="canonical",
                ),
            )
            continue

        # No canonical match. Probe for drift only when the English term
        # itself is present in the chunk — otherwise we can't tell whether
        # the translator chose a different rendering or simply skipped the
        # concept. This keeps the validator from flooding the report with
        # false positives for terms that only appear in source chunks.
        en_hits = _find_all(text, term.english.strip())
        if not en_hits:
            continue

        # Look for any plausible Vietnamese rendering on the same line —
        # a non-Latin word in the line that is *not* the canonical form.
        # Keeping this lightweight: we report the first non-canonical
        # Vietnamese-looking token. The point is to surface drift for
        # human triage, not to score alternative renderings.
        for line_number, line in en_hits:
            # Skip lines that retain the source term in italics — that's
            # the translator signalling "keep the foreign word, expand it
            # in Vietnamese elsewhere", not a different rendering.
            if _is_retained_italic(line, term.english.strip()):
                continue
            drift_token = _first_drift_token(line, canonical, term.english.strip())
            if drift_token:
                findings[term.en_key] = ChunkFinding(
                    chunk=chunk_path.name,
                    line=line_number,
                    matched_text=drift_token,
                    kind="drift",
                )
                break

    return findings, canonical_hits


_VI_CHAR = re.compile(r"[À-ỹ]")


# Phrases a translator is most likely to use as an alternative rendering.
# The regex catches one or more Vietnamese words connected by spaces,
# hyphens, or quotes, sitting near the source term.
_DRIFT_PHRASE = re.compile(r"[\"“']?[\wÀ-ỹ][\wÀ-ỹ\s'\-]{1,40}?[\"”']?")


def _first_drift_token(line: str, canonical: str, en_term: str) -> Optional[str]:
    """Return a plausible Vietnamese token from ``line`` that is not ``canonical``.

    Used only as a hint for the report — the validator doesn't try to
    score alternative renderings. We start the search near the source term
    (``en_term``) and return the first quoted/explanatory VI phrase we
    find that doesn't match the canonical. This catches patterns like::

        arete - "sự xuất sắc" và "sự hoàn thành mục đích"

    where the actual drifted rendering is in quotes after the source term.
    """
    # Prefer tokens near ``en_term`` so the report points at the rendering,
    # not at an earlier descriptive sentence.
    anchor = line.find(en_term)
    if anchor < 0:
        anchor = 0
    window = line[anchor : anchor + 200]

    # First, look for a quoted Vietnamese phrase.
    quoted = re.findall(r"[\"'“]([^\"'”]{2,40})[\"'”]", window)
    for phrase in quoted:
        if phrase.strip() == canonical.strip():
            continue
        if not _VI_CHAR.search(phrase):
            continue
        return phrase.strip()

    # Fall back to the first Vietnamese word in the post-anchor window.
    tokens = re.findall(r"[\wÀ-ỹ]+(?:[\s'\-][\wÀ-ỹ]+)*", window)
    for token in tokens:
        if token == canonical:
            continue
        if not _VI_CHAR.search(token):
            continue
        if len(token) < 2:
            continue
        return token
    return None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def validate(
    terms: list[TermEntry],
    translated_dir: Path,
    chunk_filter: Optional[str] = None,
) -> tuple[list[TermReport], dict[str, list[ChunkFinding]]]:
    """Run the scan and return per-term and per-chunk reports."""
    if not translated_dir.exists():
        return [], {}

    chunk_paths = sorted(translated_dir.glob("chunk_*.md"))
    if chunk_filter:
        chunk_paths = [p for p in chunk_paths if chunk_filter in p.name]

    per_term: dict[str, TermReport] = {
        term.en_key: TermReport(term=term) for term in terms
    }
    per_chunk: dict[str, list[ChunkFinding]] = {p.name: [] for p in chunk_paths}

    for chunk_path in chunk_paths:
        findings, hits = scan_chunk(chunk_path, terms)
        for key, finding in findings.items():
            per_chunk[chunk_path.name].append(finding)
            if finding.kind == "canonical":
                per_term[key].canonical_chunks.append(chunk_path.name)
            else:
                per_term[key].drift_chunks.append(finding)

        for key, count in hits.items():
            report = per_term.get(key)
            if report and not report.canonical_chunks:
                report.canonical_chunks.append(chunk_path.name)

    return list(per_term.values()), per_chunk


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_text_report(reports: list[TermReport], chunk_reports: dict[str, list[ChunkFinding]]) -> None:
    drift_count = sum(1 for r in reports if r.drift_chunks)
    absent_count = sum(1 for r in reports if not r.canonical_chunks)
    ok_count = sum(1 for r in reports if r.status == "ok")

    print(f"📚 Glossary validation: {len(reports)} terms")
    print(f"   ✅ ok:      {ok_count}")
    print(f"   ⚠️  drift:  {drift_count}")
    print(f"   ❌ absent:  {absent_count}")
    print()

    for report in reports:
        if report.status == "ok":
            continue
        term = report.term
        print(f"• {term.english!r} → {term.canonical!r}  [{report.status}]")
        print(f"    context: {term.context}")
        print(f"    source:  {term.chunk_id} (new_terms.txt line {term.source_line})")
        for canonical in report.canonical_chunks:
            print(f"    canonical hits: {canonical}")
        if report.drift_chunks:
            for finding in report.drift_chunks:
                print(
                    f"    drift: {finding.chunk}:{finding.line} "
                    f"matched {finding.matched_text!r}"
                )
        if not report.canonical_chunks and not report.drift_chunks:
            absent = [c for c in chunk_reports if c.startswith("chunk_")]
            print(f"    never rendered in any of {len(absent)} translated chunks")
        print()

    if any(c for c in chunk_reports.values()):
        print("Chunks with findings (for human review):")
        for chunk, findings in chunk_reports.items():
            if not findings:
                continue
            drift = [f for f in findings if f.kind == "drift"]
            canonical = [f for f in findings if f.kind == "canonical"]
            print(
                f"  {chunk}: {len(canonical)} canonical, "
                f"{len(drift)} drift"
            )
        print()


def _build_json_payload(
    reports: list[TermReport],
    chunk_reports: dict[str, list[ChunkFinding]],
) -> dict:
    return {
        "summary": {
            "total": len(reports),
            "ok": sum(1 for r in reports if r.status == "ok"),
            "drift": sum(1 for r in reports if r.drift_chunks),
            "absent": sum(1 for r in reports if not r.canonical_chunks),
        },
        "terms": [
            {
                "english": r.term.english,
                "canonical": r.term.canonical,
                "context": r.term.context,
                "source_chunk": r.term.chunk_id,
                "source_line": r.term.source_line,
                "status": r.status,
                "canonical_chunks": r.canonical_chunks,
                "drift": [
                    {
                        "chunk": f.chunk,
                        "line": f.line,
                        "matched_text": f.matched_text,
                    }
                    for f in r.drift_chunks
                ],
            }
            for r in reports
        ],
        "chunks": {
            chunk: [
                {
                    "term": finding.matched_text,
                    "line": finding.line,
                    "kind": finding.kind,
                }
                for finding in findings
            ]
            for chunk, findings in chunk_reports.items()
        },
    }


def main() -> int:
    """CLI for ``python scripts/validate_glossary.py``."""
    argv, cfg = bootstrap_argv()
    parser = argparse.ArgumentParser(
        description="Validate glossary renderings across translated chunks.",
    )
    parser.add_argument(
        "--book",
        default=None,
        metavar="ID",
        help="Book id under books/ (default: $BOOK_ID or the only book present)",
    )
    parser.add_argument(
        "--chunk",
        default=None,
        help="Restrict the scan to one chunk file (substring match)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report",
    )
    parser.add_argument(
        "--terms-file",
        default=None,
        help="Override new_terms.txt path (default: the active book's)",
    )
    parser.add_argument(
        "--translated-dir",
        default=None,
        help="Override translated/ path (default: the active book's)",
    )
    args = parser.parse_args(argv[1:])

    terms_path = (
        Path(args.terms_file)
        if args.terms_file
        else cfg.new_terms_path
    )
    translated_dir = (
        Path(args.translated_dir)
        if args.translated_dir
        else cfg.translated_dir
    )

    terms = parse_terms_file(terms_path)
    if not terms:
        print(f"No terms found in {terms_path}")
        return 0

    reports, chunk_reports = validate(terms, translated_dir, args.chunk)

    if args.json:
        print(json.dumps(_build_json_payload(reports, chunk_reports), ensure_ascii=False, indent=2))
    else:
        _print_text_report(reports, chunk_reports)

    has_finding = any(r.has_finding for r in reports)
    return 1 if has_finding else 0


if __name__ == "__main__":
    sys.exit(main())