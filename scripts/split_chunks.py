#!/usr/bin/env python3
"""Split markdown into translation-sized chunks while preserving page markers."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from utils.book_config import bootstrap_argv, load_book

PAGE_MARKER_RE = re.compile(r"<!-- Page (\d+) -->")

# Manifest status state machine (Phase 06):
#   pending   -> translated -> review -> rework -> qa_passed
# Backward-compat alias: legacy "done" maps to "translated" and is rewritten
# on the next manifest write.
VALID_CHUNK_STATUSES = {"pending", "translated", "review", "rework", "qa_passed"}
LEGACY_STATUS_ALIASES = {"done": "translated", "in_progress": "translated"}

# A manifest can only be safely regenerated when no chunk has progressed past
# ``pending``. Any non-pending status (including legacy "done") blocks regen.
SAFE_REGEN_STATUSES = {"pending"}


def detect_category(content):
    """Detect a category from content when the caller did not supply one."""
    content_lower = content.lower()
    categories = {
        "thriller": ["thriller", "suspense", "murder", "detective", "crime", "mystery", "assassin"],
        "sci-fi": ["science fiction", "sci-fi", "spaceship", "robot", "android", "galaxy", "alien"],
        "fantasy": ["fantasy", "magic", "wizard", "dragon", "kingdom", "sword", "sorcerer"],
        "romance": ["romance", "love story", "passion", "heart", "kiss"],
        "literary": ["literary", "classic", "novel"],
        "technical": ["technical", "manual", "guide", "documentation", "api", "programming"],
        "self-help": ["self-help", "motivation", "success", "habit", "mindset", "productivity"],
        "non-fiction": [
            "artificial intelligence", "machine learning", "neural network", "algorithm",
            "consciousness", "philosophy", "ethics", "physics", "universe", "evolution",
            "economics", "research", "scientist", "hypothesis", "theory of", "cognitive",
        ],
    }
    scores = {category: sum(keyword in content_lower for keyword in keywords)
              for category, keywords in categories.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "literary"


def _write_chunk(output_dir, chunk_id, blocks, start_page, end_page):
    """Write one chunk and return its manifest record."""
    chunk_file = f"chunk_{chunk_id:03d}.md"
    Path(output_dir, chunk_file).write_text("\n\n".join(blocks).rstrip() + "\n", encoding="utf-8")
    word_count = sum(len(block.split()) for block in blocks)
    print(f"  ✓ {chunk_file} ({word_count:,} words, pages {start_page}-{end_page})")
    now = datetime.now().isoformat()
    return {
        "id": f"{chunk_id:03d}",
        "source": chunk_file,
        "translated": None,
        "pages": f"{start_page}-{end_page}",
        "word_count": word_count,
        "status": "pending",
        "translated_at": None,
        "status_history": [
            {"status": "pending", "at": now},
        ],
    }


def _paragraph_units(content):
    """Return ``(text, start_page, end_page)`` units at paragraph boundaries.

    Markers stay in the emitted text, but consecutive empty pages are carried into
    the next prose block. This prevents marker-only translation chunks while
    retaining every source marker for QA.
    """
    current_page = 1
    pending_markers = []
    pending_start_page = None
    units = []

    for part in re.split(r"\n\s*\n", content):
        # Remove only separator newlines. Leading indentation can be meaningful
        # Markdown (nested lists, blockquotes, or code) and must survive chunking.
        block = part.strip("\n")
        if not block.strip():
            continue

        marker = PAGE_MARKER_RE.fullmatch(block.strip())
        if marker:
            current_page = int(marker.group(1))
            pending_markers.append(block)
            pending_start_page = current_page if pending_start_page is None else pending_start_page
            continue

        text = "\n\n".join([*pending_markers, block])
        units.append((text, pending_start_page or current_page, current_page))
        pending_markers = []
        pending_start_page = None

    # A source ending in markers should not create a translation-only marker chunk.
    if pending_markers and units:
        text, start_page, _end_page = units[-1]
        units[-1] = ("\n\n".join([text, *pending_markers]), start_page, current_page)

    return units


def _split_units(content):
    """Use paragraph units for both marked and flowable sources."""
    return _paragraph_units(content)


def _ensure_safe_regeneration(output_dir, cfg):
    """Refuse to replace chunks once translation work has begun."""
    existing_chunks = list(output_dir.glob("chunk_*.md"))
    if not existing_chunks:
        return

    translated = list(cfg.translated_dir.glob("chunk_*.md")) if cfg.translated_dir.exists() else []
    manifest_path = output_dir / "manifest.json"
    statuses = []
    if manifest_path.exists():
        try:
            statuses = [chunk.get("status") for chunk in json.loads(manifest_path.read_text(encoding="utf-8")).get("chunks", [])]
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Cannot safely replace chunks: invalid manifest {manifest_path}") from error

    # Normalize legacy status aliases so the regen guard sees current values.
    normalized = [LEGACY_STATUS_ALIASES.get(s, s) for s in statuses]
    if translated or any(status not in SAFE_REGEN_STATUSES for status in normalized):
        raise RuntimeError(
            "Cannot replace chunks after translation progress exists. Reconcile translations and manifest first."
        )

    for chunk_path in existing_chunks:
        chunk_path.unlink()


def split_into_chunks(input_path, output_dir, chunk_size=3000, category=None, cfg=None):
    """Split Markdown into chunks near ``chunk_size`` without losing blocks."""
    if cfg is None:
        cfg = load_book()

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    content = input_path.read_text(encoding="utf-8")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _ensure_safe_regeneration(output_dir, cfg)
    units = _split_units(content)

    chunks = []
    blocks = []
    current_words = 0
    start_page = end_page = 1
    chunk_id = 1

    for text, unit_start_page, unit_end_page in units:
        words = len(text.split())
        if blocks and current_words + words > chunk_size:
            chunks.append(_write_chunk(output_dir, chunk_id, blocks, start_page, end_page))
            chunk_id += 1
            blocks = []
            current_words = 0

        if not blocks:
            start_page = unit_start_page
        blocks.append(text)
        current_words += words
        end_page = unit_end_page

    if blocks:
        chunks.append(_write_chunk(output_dir, chunk_id, blocks, start_page, end_page))

    if category is None:
        category = detect_category(content)
        print(f"\n📚 Auto-detected category: {category}")

    manifest = {
        "schema_version": 2,
        "project": "Translation Project",
        "book_id": cfg.id,
        "source_file": str(input_path),
        "source_language": cfg.source_language,
        "target_language": cfg.target_language,
        "category": category,
        "category_template": f".claude/skills/translating/categories/{category}.md",
        "style_guide": str(cfg.style_guide_path),
        "total_chunks": len(chunks),
        "total_words": sum(chunk["word_count"] for chunk in chunks),
        "status": "ready",
        "status_states": [
            "pending",
            "translated",
            "review",
            "rework",
            "qa_passed",
        ],
        "chunks": chunks,
        "statistics": {
            "chunks_pending": len(chunks),
            "chunks_translated": 0,
            "chunks_review": 0,
            "chunks_rework": 0,
            "chunks_done": 0,
            "chunks_qa_passed": 0,
            "progress_percent": 0,
        },
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Created {len(chunks)} chunks ({manifest['total_words']:,} total words)")
    print(f"📋 Manifest saved to {manifest_path}")


def main():
    argv, cfg = bootstrap_argv()
    if len(argv) < 2:
        print("Usage: python3 split_chunks.py <input.md> [output_dir] [chunk_size] [category] [--book <id>]")
        print(f"Example: python3 split_chunks.py {cfg.source_file} {cfg.chunks_dir} 3000 non-fiction")
        sys.exit(1)

    input_file = argv[1]
    output_dir = argv[2] if len(argv) > 2 else str(cfg.chunks_dir)
    chunk_size = int(argv[3]) if len(argv) > 3 else cfg.chunk_size
    category = argv[4] if len(argv) > 4 else None

    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)

    # Extraction normally applies these fixes. Keep split as the second quality
    # gate for sources supplied directly, with page markers protected as hard
    # boundaries by ``fix_sentence_breaks``.
    from utils.fix_sentence_breaks import fix_sentence_breaks
    from utils.normalize_dashes import normalize_dashes_file

    print("🔍 Pre-processing: Verifying source file...")
    fixes = fix_sentence_breaks(Path(input_file), backup=False)
    dashes = normalize_dashes_file(input_file)
    if fixes + dashes:
        print(f"  ⚠️  Found and fixed {fixes + dashes} source issues")
    else:
        print("  ✅ Source file is clean")

    print(f"\n📂 Splitting {input_file} into chunks (~{chunk_size} words each)...\n")
    split_into_chunks(input_file, output_dir, chunk_size, category, cfg=cfg)


if __name__ == "__main__":
    main()
