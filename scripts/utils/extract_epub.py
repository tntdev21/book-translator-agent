#!/usr/bin/env python3
"""
Extract text from EPUB to Markdown.

Handles two common EPUB shapes:

1. **Paged EPUBs** (Internet Archive scans, etc.) — one XHTML file per printed
   page (``page_0.html``, ``page_1.html``, ...). Page numbers are preserved as
   ``<!-- Page N -->`` markers, so the rest of the pipeline behaves exactly as
   it does for PDF sources.
2. **Flowable EPUBs** — a handful of chapter XHTML files with ``<h1>``/``<h2>``
   headings. Chapter headings are emitted as Markdown headings; there are no
   page markers (an EPUB has no fixed pagination).

Both shapes are OCR'd or reflowed text, so a light cleanup pass repairs the
characteristic artefacts (ligatures, curly quotes, and the ``I`` → ``1``
substitution) before the file is written.
"""

import html as html_lib
import os
import re
import sys
import zipfile
from pathlib import Path

# OCR/typography repairs applied to extracted text. Each is (pattern, repl).
# Kept deliberately small: only unambiguous fixes, since a wrong repair is
# harder to notice than a missing one.
_OCR_FIXES = [
    # Curly quotes / dashes -> ASCII, matching the rest of the pipeline.
    ("‘", "'"), ("’", "'"),
    ("“", '"'), ("”", '"'),
    ("…", "..."),
    # Ligatures that survive EPUB extraction.
    ("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"),
    ("ﬃ", "ffi"), ("ﬄ", "ffl"),
]

# "1" used where the pronoun "I" was meant. OCR renders the capital I as 1 in
# this scan, but only in positions where the pronoun occurs — sentence-initial
# ("1 live in Seattle") or after sentence punctuation ("3. 1 like imagining").
# The lookbehind is what keeps real numerals intact: "page 1 here", "1 000",
# and "1 Person" are all left alone, because none of them follow sentence
# punctuation. An over-broad pattern here silently corrupts numbers, which is
# harder to spot than leaving an OCR error in place.
_OCR_STANDALONE_ONE = re.compile(r'(?:(?<=^)|(?<=[.!?]\s)|(?<=[.!?]"\s))1(?=\s+[a-z])', re.M)

# Marker matched by the splitter (see split_chunks.PAGE_MARKER_RE).
_PAGE_MARKER = "<!-- Page {n} -->"


class _Markup:
    """Converts a single XHTML document to plain-text blocks."""

    BLOCK_RE = re.compile(r'<(p|h[1-6]|blockquote|li)\b[^>]*>(.*?)</\1>', re.S | re.I)

    @staticmethod
    def body(source: str) -> str:
        match = re.search(r'<body[^>]*>(.*?)</body>', source, re.S | re.I)
        return match.group(1) if match else source

    @classmethod
    def blocks(cls, source: str) -> list[tuple[str, str]]:
        """Return (kind, text) pairs, where kind is 'h1'..'h6' or 'p'."""
        out = []
        for tag, inner in cls.BLOCK_RE.findall(cls.body(source)):
            text = re.sub(r'<[^>]+>', '', inner)
            text = html_lib.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                out.append((tag.lower(), text))
        return out


def _repair(text: str) -> str:
    """Apply the OCR/typography fixes."""
    for bad, good in _OCR_FIXES:
        text = text.replace(bad, good)
    return _OCR_STANDALONE_ONE.sub("I", text)


def _page_number(filename: str) -> int | None:
    """Extract N from '.../page_N.html'. None if the file isn't page-shaped."""
    match = re.search(r'page_(\d+)\.x?html?$', filename, re.I)
    return int(match.group(1)) if match else None


def _read_documents(epub_path: str) -> list[tuple[str, str]]:
    """Return (filename, xhtml_source) for content documents, in spine order.

    Falls back to zip order when the spine can't be resolved, so a malformed
    EPUB still extracts rather than failing outright.
    """
    try:
        from ebooklib import epub
        book = epub.read_epub(epub_path)
        items = list(book.get_items())
        by_name = {i.get_name(): i for i in items}
        docs = []
        for spine_id, _ in book.spine:
            item = None
            for candidate in items:
                if getattr(candidate, "id", None) == spine_id:
                    item = candidate
                    break
            if item is None:
                continue
            try:
                docs.append((item.get_name(), item.get_content().decode("utf-8", "replace")))
            except Exception:
                continue
        if docs:
            # Skip the generated nav document; it duplicates the TOC.
            docs = [(n, s) for n, s in docs if not n.lower().endswith("nav.xhtml")]
            return docs
        _ = by_name
    except Exception:
        pass

    # Fallback: read XHTML straight out of the zip.
    with zipfile.ZipFile(epub_path) as zf:
        names = sorted(n for n in zf.namelist() if n.lower().endswith((".xhtml", ".html", ".htm")))
        return [(n, zf.read(n).decode("utf-8", "replace")) for n in names]


def extract_epub(input_path: str, output_path: str, max_pages: int | None = None) -> dict:
    """Extract an EPUB to Markdown at ``output_path``.

    Returns a small stats dict (pages, words, paged).
    """
    print(f"📄 Extracting from {input_path}...")
    documents = _read_documents(input_path)
    if not documents:
        raise ValueError(f"No XHTML content found in {input_path}")

    # A document set is "paged" when most files carry a page_N name.
    known = [p for p in (_page_number(name) for name, _ in documents) if p is not None]
    paged = len(known) >= max(3, len(documents) // 2)

    out: list[str] = []
    pages_seen = 0

    if paged:
        # Emit pages in printed order — zip order is not always page order.
        ordered = sorted(documents, key=lambda d: (_page_number(d[0]) or 0))
        for name, source in ordered:
            number = _page_number(name)
            if number is None:
                continue
            if max_pages and number > max_pages:
                continue
            out.append(_PAGE_MARKER.format(n=number))
            out.append("")
            for _kind, text in _Markup.blocks(source):
                out.append(_repair(text))
                out.append("")
            pages_seen += 1
    else:
        first_page = True
        for _name, source in documents:
            blocks = _Markup.blocks(source)
            if not blocks:
                continue
            out.append(_PAGE_MARKER.format(n=1 if first_page else 2))
            out.append("")
            first_page = False
            for kind, text in blocks:
                text = _repair(text)
                if kind in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    level = int(kind[1])
                    out.append(f"{'#' * level} {text}")
                else:
                    out.append(text)
                out.append("")
            pages_seen += 1

    content = "\n".join(out).rstrip() + "\n"
    words = len(content.split())

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Done! Saved to {output_path}")
    print(f"   Kind: {'paged' if paged else 'flowable'} EPUB")
    print(f"   Documents: {len(documents)}")
    print(f"   Units written: {pages_seen}")
    print(f"   Words: ~{words:,}")

    return {"pages": pages_seen, "words": words, "paged": paged}


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_epub.py <input.epub> [output.md] [max_pages]")
        print("Example: python extract_epub.py input/source.epub source/full_text.md")
        print("Example: python extract_epub.py input/sample.epub source/sample.md 30")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "source/full_text.md"
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)

    try:
        extract_epub(input_file, output_file, max_pages)
    except ImportError:
        print("❌ Missing ebooklib. Run: pip install ebooklib")
        sys.exit(1)


if __name__ == "__main__":
    main()
