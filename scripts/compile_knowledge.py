#!/usr/bin/env python3
"""
Compile the 3-layer translation knowledge into one deterministic markdown snapshot.

Layers (low → high precedence):
  1. Universal (.claude/skills/translating/references/) — base principles, conventions, QA
  2. Category  (.claude/skills/translating/categories/)  — {category}.md + sorted {category}--dna-*.md
  3. Book      (books/<id>/)                            — dna.md, style guide, formatting

Two role snapshots are written (translator, editor): static knowledge only,
human-only sections stripped, Layer 1 filtered per role. Dynamic files
(glossary, new_terms, corrections) are NOT included; subagents read the
compact term map and corrections.md directly (higher precedence).
Output is byte-identical across runs (no timestamp in the body).

Exit codes: 0 ok/warn-only; 1 missing required source; 2 duplicate lint under
--strict; 3 size guard (>50KB).

Excluded: `style/book_names.json` (phrase/terminology data used by fix.py,
not by the translator — saves ~4.5K tokens/agent).

Usage:
    python scripts/compile_knowledge.py                       # auto-detect book, default path, condensed mode
    python scripts/compile_knowledge.py --book <id>           # explicit book
    python scripts/compile_knowledge.py --role translator     # write one role only
    python scripts/compile_knowledge.py --role editor --output PATH   # custom output (needs --role)
    python scripts/compile_knowledge.py --role editor --stdout        # emit to stdout (needs --role)
    python scripts/compile_knowledge.py --strict              # duplicate lint -> exit 2
    python scripts/compile_knowledge.py --full                # opt out of condensed mode (use full Layer 1/2 files)
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

# Allow direct execution: ``python scripts/compile_knowledge.py`` must work
# even though scripts/utils/book_config.py uses package-relative imports.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.utils.book_config import (  # noqa: E402
    BookConfig,
    SHARED_FORMATTING_RULES,
    add_book_argument,
    get_config_from_args,
    resolve_book_id,
)

# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

SKILL_ROOT = _REPO_ROOT / ".claude" / "skills" / "translating"
LAYER1_DIR = SKILL_ROOT / "references"
LAYER2_DIR = SKILL_ROOT / "categories"

# Required Layer 1 files — the universal foundation that every book reads.
LAYER1_FILES = ("base-principles.md", "vietnamese-conventions.md", "quality-checklist.md")

ROLES = ("translator", "editor")
OUTPUT_NAMES = {"translator": "_knowledge_snapshot.md", "editor": "_editor_snapshot.md"}

# Layer 1 sections kept per role: "*" = whole file, else level-2 heading prefixes
# (case-insensitive). A listed section that is not found warns, never crashes.
ROLE_L1: Dict[str, Dict[str, Union[str, List[str]]]] = {
    "translator": {
        "base-principles.md": "*",
        "vietnamese-conventions.md": "*",
        "quality-checklist.md": ["Severity Levels", "During Translation"],
    },
    "editor": {
        "base-principles.md": "*",
        "vietnamese-conventions.md": "*",
        "quality-checklist.md": "*",
    },
}

# Heading prefixes (case-insensitive) of sections stripped from every file.
ROLE_STRIP: Dict[str, List[str]] = {
    "all": ["Promotion candidates", "Samples Used", "Snapshot Metadata"],
    "translator": ["Open Questions"],
    "editor": ["Translation Workflow & Per-Chunk Checklist"],
}

WARN_BYTES = 45 * 1024
FAIL_BYTES = 50 * 1024
CORRECTIONS_WARN_BYTES = 40 * 1024
TERMS_COMPACT_WARN_BYTES = 30 * 1024


# ---------------------------------------------------------------------------
# Per-file inclusion
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    """Read a UTF-8 text file and strip a single trailing newline (we re-add one).

    We do *not* rewrite content — the snapshot must be byte-identical to the
    source files modulo line endings, which we normalize to LF and join with
    a single blank line between files.
    """
    text = path.read_text(encoding="utf-8")
    # Normalize CRLF/CR → LF so the snapshot is OS-independent.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Drop exactly one trailing newline; we add our own separator below.
    if text.endswith("\n"):
        text = text[:-1]
    return text


def _include_required(rel_path: str, root: Path) -> str:
    """Read a file the snapshot cannot proceed without. Exits with a helpful error."""
    path = root / rel_path
    if not path.exists():
        print(
            f"❌ Required file missing: {path}\n"
            f"   The 3-layer knowledge snapshot cannot be compiled without this file.\n"
            f"   Restore the file or run the upstream generator that produces it.",
            file=sys.stderr,
        )
        sys.exit(1)
    return _read(path)


# ---------------------------------------------------------------------------
# Fence-aware markdown section handling
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_CODE_SPAN_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")


def _strip_comments_outside_code(text: str) -> str:
    """Remove HTML comments except those inside inline code spans."""
    out: List[str] = []
    pos = 0
    for m in _CODE_SPAN_RE.finditer(text):
        out.append(_COMMENT_RE.sub("", text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_COMMENT_RE.sub("", text[pos:]))
    return "".join(out)


def _scan_headings(lines: List[str]) -> List[Tuple[int, int, str]]:
    """Return [(line_idx, level, title)] for headings outside ``` / ~~~ fences."""
    out: List[Tuple[int, int, str]] = []
    fence: Optional[str] = None
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(1)
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        h = _HEADING_RE.match(line)
        if h:
            out.append((i, len(h.group(1)), h.group(2)))
    return out


def _section_end(headings: List[Tuple[int, int, str]], k: int, n_lines: int) -> int:
    """Exclusive end line of the section at headings[k]: next heading of same-or-higher level."""
    level = headings[k][1]
    for j in range(k + 1, len(headings)):
        if headings[j][1] <= level:
            return headings[j][0]
    return n_lines


def _matches(title: str, prefixes: Sequence[str]) -> bool:
    t = title.casefold()
    return any(t.startswith(p.casefold()) for p in prefixes)


def strip_html_comments(text: str) -> str:
    """Remove HTML comments outside code fences."""
    lines = text.split("\n")
    out: List[str] = []
    buf: List[str] = []
    fence: Optional[str] = None

    def flush() -> None:
        if buf:
            out.extend(_strip_comments_outside_code("\n".join(buf)).split("\n"))
            buf.clear()

    for line in lines:
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(1)
            if fence is None:
                flush()
                fence = marker
            elif fence == marker:
                fence = None
                out.append(line)
                continue
        if fence is not None:
            out.append(line)
        else:
            buf.append(line)
    flush()
    return "\n".join(out)


def strip_sections(text: str, prefixes: Sequence[str]) -> str:
    """Drop every section whose heading starts with one of ``prefixes`` (case-insensitive)."""
    if not prefixes:
        return text
    lines = text.split("\n")
    headings = _scan_headings(lines)
    drop = [False] * len(lines)
    for k, (idx, _lvl, title) in enumerate(headings):
        if _matches(title, prefixes):
            for i in range(idx, _section_end(headings, k, len(lines))):
                drop[i] = True
    kept = [ln for ln, d in zip(lines, drop) if not d]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip("\n")


def clean_text(text: str, role: str) -> str:
    """Apply comment + role-specific section stripping."""
    text = strip_html_comments(text)
    text = strip_sections(text, ROLE_STRIP["all"] + ROLE_STRIP.get(role, []))
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def filter_l1(text: str, wanted: Union[str, List[str]], label: str) -> str:
    """Keep the title block plus only the level-2 sections named in ``wanted``."""
    if wanted == "*":
        return text
    lines = text.split("\n")
    headings = _scan_headings(lines)
    l2 = [(k, h) for k, h in enumerate(headings) if h[1] == 2]
    first_l2 = l2[0][1][0] if l2 else len(lines)
    keep = lines[:first_l2]
    found = set()
    for k, (idx, _lvl, title) in l2:
        for w in wanted:
            if title.casefold().startswith(w.casefold()):
                found.add(w)
                keep.extend(lines[idx:_section_end(headings, k, len(lines))])
                break
    for w in wanted:
        if w not in found:
            print(f"WARN L1 section '{w}' not found in {label}; skipped", file=sys.stderr)
    return "\n".join(keep).strip("\n")


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

Source = Tuple[str, str]  # (source label, cleaned text) — used by the dup lint


def _section(title: str, files_in_order: List[Tuple[str, str]]) -> str:
    """Join file bodies under a layer header. ``files_in_order`` is [(subhead, body)]."""
    chunks = [f"## {title}", ""]
    for subhead, body in files_in_order:
        chunks.append(f"### {subhead}")
        chunks.append("")
        chunks.append(body)
        chunks.append("")
    while chunks and chunks[-1] == "":
        chunks.pop()
    return "\n".join(chunks)


def _format_layer1(role: str, sources: List[Source], condensed: bool) -> str:
    files: List[Tuple[str, str]] = []
    for rel in sorted(LAYER1_FILES):
        path = LAYER1_DIR / rel
        if not condensed:
            full = LAYER1_DIR / rel.replace(".md", ".full.md")
            if full.exists():
                path = full
        if not path.exists():
            _include_required(path.name, path.parent)  # exits 1 with message
        text = clean_text(_read(path), role)
        text = filter_l1(text, ROLE_L1[role].get(rel, "*"), path.name)
        sources.append((f"L1/{path.name}", text))
        files.append((path.name, text))
    suffix = " (condensed)" if condensed else " (full)"
    return _section(f"Layer 1 — Universal References{suffix}", files)


def _format_layer2(cfg: BookConfig, role: str, sources: List[Source], condensed: bool) -> str:
    category = cfg.category
    template = LAYER2_DIR / f"{category}.md"
    if not condensed and (LAYER2_DIR / f"{category}.full.md").exists():
        template = LAYER2_DIR / f"{category}.full.md"
    if not template.exists():
        print(
            f"❌ Required file missing: {template}\n"
            f"   Category '{category}' is declared in book.yaml but has no template\n"
            f"   under {LAYER2_DIR}/. Add {category}.md or change `category:` in book.yaml.",
            file=sys.stderr,
        )
        sys.exit(1)
    paths = [template] + [
        p for p in sorted(LAYER2_DIR.glob(f"{category}--dna-*.md")) if not p.name.endswith(".full.md")
    ]
    files: List[Tuple[str, str]] = []
    for path in paths:
        text = clean_text(_read(path), role)
        sources.append((f"L2/{path.name}", text))
        files.append((path.name, text))
    suffix = " (condensed)" if condensed else " (full)"
    return _section(f"Layer 2 — Category: {category}{suffix}", files)


def _format_layer3(cfg: BookConfig, role: str, sources: List[Source]) -> str:
    """Layer 3 static book knowledge: dna, style guide, formatting rules."""
    files: List[Tuple[str, str]] = []
    for label, path, why in (
        ("dna.md", cfg.dna_path, "The book DNA captures the author's voice and is mandatory.\n"
         "   Derive it with the deriving-dna skill, or scaffold it from book.yaml."),
        ("translation_style_guide.md", cfg.style_guide_path,
         "The translation style guide defines voice/register/glossary rules\n"
         "   that translators must follow. Create it before compiling knowledge."),
    ):
        if not path.exists():
            print(f"❌ Required file missing: {path}\n   {why}", file=sys.stderr)
            sys.exit(1)
        text = clean_text(_read(path), role)
        sources.append((f"L3/{label}", text))
        files.append((label, text))

    local_fmt = cfg.style_dir / "formatting_rules.md"
    if local_fmt.exists():
        fmt, label = local_fmt, "formatting_rules.md"
    elif SHARED_FORMATTING_RULES.exists():
        fmt, label = SHARED_FORMATTING_RULES, "formatting_rules.md (shared)"
    else:
        fmt, label = None, ""
    if fmt is not None:
        text = clean_text(_read(fmt), role)
        sources.append((f"L3/{label}", text))
        files.append((label, text))
    return _section("Layer 3 — Book-Specific Knowledge", files)


# ---------------------------------------------------------------------------
# Duplicate lint
# ---------------------------------------------------------------------------

_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
_MIN_BULLET_KEY = 15


def _norm(s: str) -> str:
    s = re.sub(r"[`*_]", "", s)
    return re.sub(r"[\W_]+", "", s.casefold())


def lint_duplicates(sources: List[Source]) -> List[str]:
    """Exact normalized matches of ##/### headings and bullets across different files."""
    seen: Dict[Tuple[str, str], Tuple[str, str]] = {}
    out: List[str] = []
    reported = set()
    for label, text in sources:
        lines = text.split("\n")
        fence: Optional[str] = None
        heading = ""
        for line in lines:
            m = _FENCE_RE.match(line)
            if m:
                fence = None if fence == m.group(1) else (fence or m.group(1))
                continue
            if fence:
                continue
            h = _HEADING_RE.match(line)
            items: List[Tuple[str, str, str]] = []
            if h:
                heading = h.group(2)
                if len(h.group(1)) in (2, 3):
                    items.append(("h", _norm(heading), heading))
            else:
                b = _BULLET_RE.match(line)
                if b:
                    key = _norm(b.group(1))
                    if len(key) >= _MIN_BULLET_KEY:
                        items.append(("b", key, b.group(1)))
            for kind, key, shown in items:
                if not key:
                    continue
                prev = seen.get((kind, key))
                if prev is None:
                    seen[(kind, key)] = (label, heading if kind == "b" else shown)
                elif prev[0] != label and (kind, key, prev[0], label) not in reported:
                    reported.add((kind, key, prev[0], label))
                    where_b = heading if kind == "b" else shown
                    snippet = f" [{shown[:50]}]" if kind == "b" else ""
                    out.append(f"WARN dup: {prev[0]}:{prev[1]} == {label}:{where_b}{snippet}")
    return out


# ---------------------------------------------------------------------------
# Snapshot assembly
# ---------------------------------------------------------------------------

def build_snapshot(cfg: BookConfig, role: str = "translator",
                   condensed: bool = True) -> Tuple[str, List[Source]]:
    """Return (snapshot text, cleaned sources) for ``role``."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}; expected one of {ROLES}")
    sources: List[Source] = []
    layer1 = _format_layer1(role, sources, condensed)
    layer2 = _format_layer2(cfg, role, sources, condensed)
    layer3 = _format_layer3(cfg, role, sources)
    header = (
        f"# Knowledge Snapshot — book `{cfg.id}` ({cfg.category}) — role: {role}\n"
        f"Sources: {', '.join(label for label, _ in sources)}\n"
        f"Static L1+L2+L3 knowledge for role {role}. "
        f"Precedence low->high: L1 < L2 card < genre DNA < dna.md < style guide/terms "
        f"< formatting < corrections. Dynamic: _terms_compact.md, corrections.md."
    )
    # book.yaml `rights.statement`: the operator's rights declaration for this book.
    if cfg.rights.get("statement"):
        header += f"\nRights: {cfg.rights['statement'].strip()}"
    return "\n\n".join([header, layer1, layer2, layer3]) + "\n", sources


def compile_snapshot(cfg: BookConfig, role: str = "translator", condensed: bool = True) -> str:
    """Return the snapshot text for ``cfg`` and ``role``."""
    return build_snapshot(cfg, role, condensed)[0]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile role-specific translation knowledge snapshots (translator + editor).",
    )
    parser.add_argument("--role", choices=ROLES, default=None,
                        help="Write one role only (default: both)")
    parser.add_argument("--output", default=None, metavar="PATH",
                        help="Output path (requires --role)")
    parser.add_argument("--stdout", action="store_true",
                        help="Write to stdout instead of file (requires --role)")
    parser.add_argument("--full", action="store_true",
                        help="Use *.full.md Layer 1/2 files when present")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 2 if duplicate lint finds anything")
    add_book_argument(parser)
    args = parser.parse_args(argv)
    if (args.output or args.stdout) and not args.role:
        parser.error("--output/--stdout require --role")
    return args


def _info_checks(cfg: BookConfig) -> None:
    """Read-only size warnings for dynamic files (informational)."""
    if cfg.corrections_path.exists() and cfg.corrections_path.stat().st_size > CORRECTIONS_WARN_BYTES:
        print(f"WARN corrections.md is {cfg.corrections_path.stat().st_size} bytes (>40KB); "
              f"consider promoting entries", file=sys.stderr)
    terms = cfg.style_dir / "_terms_compact.md"
    if terms.exists() and terms.stat().st_size > TERMS_COMPACT_WARN_BYTES:
        print(f"WARN _terms_compact.md is {terms.stat().st_size} bytes (>30KB)", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    cfg = get_config_from_args(args)
    condensed = not args.full
    roles = [args.role] if args.role else list(ROLES)

    exit_code = 0
    lint_hits = 0
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for role in roles:
        snapshot, sources = build_snapshot(cfg, role, condensed)
        for warning in lint_duplicates(sources):
            lint_hits += 1
            print(f"{warning} (role {role})", file=sys.stderr)

        nbytes = len(snapshot.encode("utf-8"))
        if args.stdout:
            sys.stdout.write(snapshot)
            if nbytes > FAIL_BYTES:
                print(f"FAIL {role} snapshot {nbytes} bytes > 50KB limit", file=sys.stderr)
                exit_code = 3
            elif nbytes > WARN_BYTES:
                print(f"WARN {role} snapshot {nbytes} bytes > 45KB", file=sys.stderr)
            continue

        output = Path(args.output) if args.output else cfg.style_dir / OUTPUT_NAMES[role]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(snapshot, encoding="utf-8", newline="\n")
        mode = "condensed" if condensed else "full"
        print(f"✅ {role} snapshot for '{cfg.id}' ({mode}) → {output} "
              f"({nbytes} bytes, {snapshot.count(chr(10))} lines) @ {ts}")
        if nbytes > FAIL_BYTES:
            print(f"FAIL {role} snapshot {nbytes} bytes > 50KB limit", file=sys.stderr)
            exit_code = 3
        elif nbytes > WARN_BYTES:
            print(f"WARN {role} snapshot {nbytes} bytes > 45KB", file=sys.stderr)

    _info_checks(cfg)
    if exit_code:
        return exit_code
    if args.strict and lint_hits:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
