#!/usr/bin/env python3
"""
Configuration constants for translation scripts.
Centralizes magic numbers and configuration values.
"""

# Sentence break fixing
MAX_SENTENCE_FIX_PASSES = 20  # Maximum iterations to prevent infinite loops
MIN_LINE_LENGTH_FOR_JOIN = 10  # Minimum characters in a line to consider joining

# DOCX extraction
DOCX_WORDS_PER_PAGE = 500  # Estimated words per page for DOCX pagination

# Chunking
DEFAULT_CHUNK_SIZE = 3000  # Target words per chunk (≈10-15 pages)

# Dash normalization
EM_DASH = '—'
REPLACEMENT_DASH = '-'

# Per-book paths live on BookConfig (see book_config.py) — they are derived
# from books/<id>/book.yaml, not from repo-root constants, so a repo-wide
# constant would only be wrong for every book but one.
