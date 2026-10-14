"""Load canonical and live translation terminology."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import NamedTuple


class Term(NamedTuple):
    source: str
    target: str
    context: str = ""


def _key(source: str) -> str:
    return source.strip().casefold()


def load_glossary(path: Path | None) -> dict[str, Term]:
    """Load canonical CSV or a legacy pipe-separated glossary."""
    if path is None or not path.exists():
        return {}

    content = path.read_text(encoding="utf-8-sig")
    reader = csv.reader(StringIO(content))
    header = next(reader, None)
    if header and {column.strip().casefold() for column in header} >= {
        "source_term",
        "target_term",
    }:
        rows = reader
        column_indexes = {
            column.strip().casefold(): index for index, column in enumerate(header)
        }
    else:
        rows = csv.reader(StringIO(content), delimiter="|")
        next(rows, None)
        column_indexes = {"source_term": 0, "target_term": 1, "context": 2}

    terms: dict[str, Term] = {}
    for row in rows:
        source_index = column_indexes["source_term"]
        target_index = column_indexes["target_term"]
        if len(row) <= max(source_index, target_index):
            continue
        source = row[source_index].strip()
        target = row[target_index].strip()
        context_index = column_indexes.get("context")
        context = (
            row[context_index].strip()
            if context_index is not None and len(row) > context_index
            else ""
        )
        if source and target:
            terms[_key(source)] = Term(source, target, context)
    return terms


def load_new_terms(path: Path | None) -> dict[str, Term]:
    """Load valid four-column entries from the Markdown new-terms log."""
    if path is None or not path.exists():
        return {}

    terms: dict[str, Term] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "|" not in line:
            continue
        row = [part.strip() for part in line.lstrip("- ").split("|")]
        if len(row) < 4:
            continue
        source, target = row[:2]
        context = row[2] if len(row) > 2 else ""
        if source and target:
            terms[_key(source)] = Term(source, target, context)
    return terms


def load_terminology(
    glossary_path: Path | None, new_terms_path: Path | None = None
) -> dict[str, Term]:
    """Load canonical glossary terms overlaid by live new-term decisions."""
    terms = load_glossary(glossary_path)
    terms.update(load_new_terms(new_terms_path))
    return terms
