#!/usr/bin/env python3
"""
Shared chunk loading utilities for export scripts.
Handles test mode, chunk ranges, and full book mode.
"""

from pathlib import Path
from typing import Optional, Tuple, List

from .book_config import BookConfig, load_book


def load_chunks(
    test: bool = False,
    chunks: str = None,
    translated_dir: Optional[Path] = None,
    book: Optional[BookConfig] = None
) -> Tuple[List[Path], str, str]:
    """
    Load chunk files based on mode (test, specific chunks, or full book).

    Args:
        test: If True, load only chunk_001.md
        chunks: Chunk specification ("1-5" or "1,3,5")
        translated_dir: Explicit translated directory. Overrides ``book``.
        book: Book to load from. Defaults to the resolved active book.

    Returns:
        Tuple of (chunk_files, output_suffix, export_mode)

    Raises:
        FileNotFoundError: If translated directory or required chunks don't exist
        ValueError: If chunk specification is invalid
    """
    if translated_dir is None:
        translated_dir = (book or load_book()).translated_dir

    if not translated_dir.exists():
        raise FileNotFoundError(f"Translated directory not found: {translated_dir}")

    files = []
    output_suffix = ""
    export_mode = ""

    if test:
        # Test mode - only chunk 1
        chunk_file = translated_dir / 'chunk_001.md'
        if not chunk_file.exists():
            raise FileNotFoundError(f"chunk_001.md not found in {translated_dir}")
        files = [chunk_file]
        export_mode = "Test (Chunk 1)"
        output_suffix = "_test"

    elif chunks:
        # Specific chunks mode
        try:
            if '-' in chunks:
                # Range: 1-5
                parts = chunks.split('-')
                if len(parts) != 2:
                    raise ValueError(f"Invalid range format '{chunks}'. Expected: '1-5'")
                start, end = int(parts[0]), int(parts[1])
                if start < 1 or end < 1 or start > end:
                    raise ValueError(f"Invalid range {start}-{end}. Must be positive with start <= end")

                for i in range(start, end + 1):
                    chunk_file = translated_dir / f'chunk_{i:03d}.md'
                    if not chunk_file.exists():
                        raise FileNotFoundError(f"{chunk_file.name} not found in {translated_dir}")
                    files.append(chunk_file)
            else:
                # List: 1,3,5
                for num in chunks.split(','):
                    chunk_num = int(num.strip())
                    if chunk_num < 1:
                        raise ValueError(f"Chunk number must be positive, got: {chunk_num}")
                    chunk_file = translated_dir / f'chunk_{chunk_num:03d}.md'
                    if not chunk_file.exists():
                        raise FileNotFoundError(f"{chunk_file.name} not found in {translated_dir}")
                    files.append(chunk_file)
        except ValueError as e:
            raise ValueError(f"Invalid chunk specification '{chunks}'. Must be numbers (e.g., '1-5' or '1,3,5'): {e}")

        export_mode = f"Chunks {chunks}"
        output_suffix = f"_chunks_{chunks.replace('-', '_').replace(',', '_')}"

    else:
        # Full book mode
        files = sorted(translated_dir.glob('chunk_*.md'))
        if not files:
            raise FileNotFoundError(f"No translated files found in {translated_dir}")
        export_mode = "Full Book"
        output_suffix = ""

    return files, output_suffix, export_mode
