#!/usr/bin/env python3
"""
Reset a book's translation progress back to a clean "all pending" baseline.

Branch-independent: rebuilds state from the files on disk instead of checking
out a fixed commit, so it works on main, benchmark branches and worktrees.
Operates on the repo that contains this script (run it from the worktree you
want to reset).

What it resets:
  - chunks/manifest.json  -> every chunk `pending`, history = one pending entry
  - translated/           -> every file removed except .gitkeep
  - review/               -> editor verdict files removed (if the dir exists)
  - style/new_terms.txt   -> header only
  - style/corrections.md  -> header only
  - logs/book-translating.tsv         -> this book's rows removed
  - logs/book-translating.agents.tsv  -> deleted (no book column; per-run ledger)
  - style/term_map.json, style/_terms_compact.md, style/_knowledge_snapshot.md,
    style/_editor_snapshot.md -> regenerated

Never touches: source/, chunks/chunk_*.md, glossary.csv, style guide, dna.md,
samples/, output/.

Usage:
  ./venv/bin/python scripts/reset_book.py --book <id> --dry-run
  ./venv/bin/python scripts/reset_book.py --book <id> --yes
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.utils.book_config import load_book  # noqa: E402

NEW_TERMS_HEADER = "# New Terms Log\n\n"
CORRECTIONS_HEADER = (
    "# Editor Corrections\n\n"
    "Recurring editor findings for this book. Read before translating each later chunk.\n"
)
# Structural per-chunk keys kept as-is; everything else is progress and dropped.
STRUCTURAL_CHUNK_KEYS = ("id", "source", "pages", "word_count")
STATES = ["pending", "translated", "review", "rework", "qa_passed"]
LOGS_DIR = REPO_ROOT / "logs"
BATCH_TSV = LOGS_DIR / "book-translating.tsv"
AGENTS_TSV = LOGS_DIR / "book-translating.agents.tsv"
BATCH_TSV_BOOK_COL = 7  # 0-based index of book_id in the batch TSV


def reset_manifest(path: Path, dry_run: bool) -> str:
    """Rewrite manifest so every chunk is pending with a fresh history."""
    data = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    dropped, chunks = set(), []
    for chunk in data["chunks"]:
        dropped |= set(chunk) - set(STRUCTURAL_CHUNK_KEYS) - {
            "status", "translated", "translated_at", "status_history"}
        base = {k: chunk[k] for k in STRUCTURAL_CHUNK_KEYS if k in chunk}
        chunks.append({
            "id": base.get("id"),
            "source": base.get("source"),
            "translated": None,
            "pages": base.get("pages"),
            "word_count": base.get("word_count"),
            "status": "pending",
            "translated_at": None,
            "status_history": [{"status": "pending", "at": now}],
        })
    total = len(chunks)
    data.update({
        "status": "ready",
        "status_states": STATES,
        "chunks": chunks,
        "total_chunks": total,
        "statistics": {
            "chunks_pending": total, "chunks_translated": 0, "chunks_review": 0,
            "chunks_rework": 0, "chunks_done": 0, "chunks_qa_passed": 0,
            "progress_percent": 0,
        },
        "last_updated": now,
    })
    # Absolute paths leak the worktree they were written in; keep repo-relative.
    sg = data.get("style_guide")
    if sg and os.path.isabs(sg) and "/books/" in sg:
        data["style_guide"] = "books/" + sg.split("/books/", 1)[1]
    if not dry_run:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    note = f" (dropped keys: {', '.join(sorted(dropped))})" if dropped else ""
    return f"manifest: {total} chunks -> pending{note}"


def clear_translated(dir_: Path, dry_run: bool, label: str = "translated/") -> str:
    """Remove everything in `dir_` (translated/ or review/) except .gitkeep."""
    files = [p for p in dir_.iterdir() if p.name != ".gitkeep"] if dir_.exists() else []
    for p in files:
        if dry_run:
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    if not dry_run:
        dir_.mkdir(parents=True, exist_ok=True)
        (dir_ / ".gitkeep").touch()
    return f"{label}: removed {len(files)} file(s)"


def reset_text(path: Path, content: str, dry_run: bool) -> str:
    lines = len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0
    if not dry_run:
        path.write_text(content, encoding="utf-8")
    return f"{path.name}: {lines} line(s) -> header only"


def clean_logs(book_id: str, dry_run: bool) -> list[str]:
    """Drop this book's batch rows; delete the per-run agentId ledger."""
    out = []
    if BATCH_TSV.exists():
        rows = BATCH_TSV.read_text(encoding="utf-8").splitlines(keepends=True)
        keep = [r for r in rows if not (
            len(r.rstrip("\n").split("\t")) > BATCH_TSV_BOOK_COL
            and r.rstrip("\n").split("\t")[BATCH_TSV_BOOK_COL] == book_id)]
        if not dry_run:
            BATCH_TSV.write_text("".join(keep), encoding="utf-8")
        out.append(f"{BATCH_TSV.name}: removed {len(rows) - len(keep)} row(s)")
    if AGENTS_TSV.exists():
        if not dry_run:
            AGENTS_TSV.unlink()
        out.append(f"{AGENTS_TSV.name}: deleted")
    return out


class RegenerateError(RuntimeError):
    """Derived-file regeneration failed after the state reset succeeded."""


def regenerate(book_id: str, dry_run: bool) -> list[str]:
    """Rebuild derived files from the now-empty translation state."""
    if dry_run:
        return ["term_map.json + _terms_compact.md + _knowledge_snapshot.md + "
                "_editor_snapshot.md: would regenerate"]
    env = {**os.environ, "BOOK_ID": book_id}
    py = sys.executable
    for cmd in ([py, "scripts/extract_term_map.py", "--quiet"],
                [py, "scripts/compile_knowledge.py", "--book", book_id]):
        try:
            subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True,
                           stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise RegenerateError(
                "state reset OK, regenerate FAILED "
                f"(exit {exc.returncode}): rerun `compile_knowledge.py --book {book_id}`"
            ) from exc
    return ["term_map.json + _terms_compact.md + _knowledge_snapshot.md + "
            "_editor_snapshot.md: regenerated"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--book", help="Book id (default: $BOOK_ID or the only book)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    book = load_book(args.book)
    print(f"Repo: {REPO_ROOT}\nBook: {book.id}{'  [DRY RUN]' if args.dry_run else ''}")
    if not args.dry_run and not args.yes:
        if input("This deletes all translations for this book. Continue? [y/N] ").lower() != "y":
            print("Aborted.")
            return 1

    report = [
        reset_manifest(book.manifest_path, args.dry_run),
        clear_translated(book.translated_dir, args.dry_run),
        *([clear_translated(book.root / "review", args.dry_run, "review/")]
          if (book.root / "review").exists() else []),
        reset_text(book.new_terms_path, NEW_TERMS_HEADER, args.dry_run),
        reset_text(book.corrections_path, CORRECTIONS_HEADER, args.dry_run),
        *clean_logs(book.id, args.dry_run),
    ]
    for line in report:
        print(f"  - {line}")
    try:
        for line in regenerate(book.id, args.dry_run):
            print(f"  - {line}")
    except RegenerateError as exc:
        print(f"  - {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
