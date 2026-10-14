#!/usr/bin/env python3
"""
Move manifest chunks through the 5-state machine (the only sanctioned writer).

Transition graph:
  pending -> translated -> review -> qa_passed | rework;  rework -> translated
  qa_passed -> rework only with --reopen (a human decision reopens a passed chunk)

Refuses `translated` unless books/<id>/translated/<chunk>.md is non-empty.
Each transition sets `status`, appends `{status, at}` (UTC ISO) to
`status_history`, and refreshes top-level `statistics` + `last_updated`.
All-or-nothing: one illegal chunk in the list writes nothing.

Usage:
  ./venv/bin/python scripts/manifest_status.py --book <id> <status> <chunk_id...>
  ./venv/bin/python scripts/manifest_status.py --book <id> --reopen rework <chunk_id...>
  (chunk ids: chunk_007 or 007)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.utils.book_config import BookConfigError, load_book  # noqa: E402

STATES = ["pending", "translated", "review", "rework", "qa_passed"]
TRANSITIONS = {
    "pending": {"translated"},
    "translated": {"review"},
    "review": {"qa_passed", "rework"},
    "rework": {"translated"},
    "qa_passed": set(),
}


def norm_id(chunk: str) -> str:
    """`chunk_007`, `chunk_007.md` or `7` -> `007`."""
    cid = chunk.removesuffix(".md").removeprefix("chunk_")
    if not cid.isdigit():
        raise ValueError(f"bad chunk id: {chunk}")
    return cid.zfill(3)


def statistics(chunks: list[dict]) -> dict:
    counts = {s: sum(1 for c in chunks if c.get("status") == s) for s in STATES}
    total = len(chunks) or 1
    return {
        "chunks_pending": counts["pending"], "chunks_translated": counts["translated"],
        "chunks_review": counts["review"], "chunks_rework": counts["rework"],
        "chunks_done": counts["qa_passed"], "chunks_qa_passed": counts["qa_passed"],
        "progress_percent": round(100 * counts["qa_passed"] / total),
    }


def apply(manifest: dict, status: str, ids: list[str], translated_dir: Path,
          reopen: bool = False) -> list[str]:
    """Validate every requested transition, then apply all. Raises ValueError."""
    by_id = {c["id"]: c for c in manifest["chunks"]}
    errors, todo = [], []
    for cid in ids:
        chunk = by_id.get(cid)
        if chunk is None:
            errors.append(f"chunk_{cid}: not in manifest")
            continue
        cur = chunk.get("status", "pending")
        allowed = TRANSITIONS.get(cur, set()) | ({"rework"} if reopen and cur == "qa_passed" else set())
        if status not in allowed:
            errors.append(f"chunk_{cid}: illegal {cur} -> {status}")
            continue
        if status == "translated":
            f = translated_dir / f"chunk_{cid}.md"
            if not f.is_file() or f.stat().st_size == 0:
                errors.append(f"chunk_{cid}: {f} missing or empty")
                continue
        todo.append((chunk, cur))
    if errors:
        raise ValueError("; ".join(errors))
    now = datetime.now(timezone.utc).isoformat()
    for chunk, _ in todo:
        chunk["status"] = status
        chunk.setdefault("status_history", []).append({"status": status, "at": now})
    manifest["statistics"] = statistics(manifest["chunks"])
    manifest["last_updated"] = now
    return [f"chunk_{c['id']}: {cur} -> {status}" for c, cur in todo]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--book", default=None)
    ap.add_argument("--reopen", action="store_true",
                    help="allow qa_passed -> rework (human-decided reopen only)")
    ap.add_argument("status", choices=STATES[1:])
    ap.add_argument("chunks", nargs="+")
    args = ap.parse_args(argv)
    try:
        book = load_book(args.book)
    except BookConfigError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    try:
        ids = list(dict.fromkeys(norm_id(c) for c in args.chunks))
        path = book.manifest_path
        manifest = json.loads(path.read_text(encoding="utf-8"))
        lines = apply(manifest, args.status, ids, book.translated_dir, args.reopen)
    except ValueError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    # Atomic replace: a crash mid-write never leaves a truncated manifest.
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
