#!/usr/bin/env python3
"""
Export book to EPUB format.

⚠️  This is an individual utility script. For normal usage, use:
    python scripts/export.py -f epub

Advanced usage (direct):
    python scripts/utils/export_epub.py                   # Export full book
    python scripts/utils/export_epub.py --test            # Export chunk 1 only (test)
    python scripts/utils/export_epub.py --chunks 1-5      # Export chunks 1-5
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/export_epub.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import os
import re
import sys
import argparse
from pathlib import Path

# Import shared markdown conversion functions
from .markdown_converter import make_toc_links_clickable, markdown_to_html_with_dialogue
from .book_config import BookConfig, REPO_ROOT, add_book_argument, get_config_from_args
from .chunk_loader import load_chunks
from .fonts import DEFAULT_FONT, resolve_font, small_caps
from ebooklib import epub

def epub_font_path(f):
    """Path of a font file inside the EPUB: fonts/<Family>/<Variant>.<ext>."""
    return f"fonts/{f.path.parent.name}/{f.variant}{f.path.suffix.lower()}"


def get_css(family=None, fonts_dir=None):
    """Get CSS matching PDF export. ``family`` defaults to the resolved default font."""
    family = family or resolve_font()
    sc_family, sc_css = small_caps(family, fonts_dir)
    # style.css lives in style/, so font URLs climb one level to the EPUB root.
    font_faces = family.font_face_css(lambda f: f"../{epub_font_path(f)}")
    if sc_family:
        font_faces += "\n" + sc_family.font_face_css(lambda f: f"../{epub_font_path(f)}")
    return font_faces + "\n" + sc_css + "\n\n" + _BASE_CSS.replace("__FONT_STACK__", family.css_stack)


# Full-bleed cover page: no margins, image scaled to fill the screen. ebooklib
# drops inline <style> from the cover page, so this ships as its own file.
COVER_CSS = """@page { margin: 0; }
html, body { margin: 0; padding: 0; height: 100%; }
img { display: block; width: 100%; height: 100%; object-fit: contain; }
"""

_BASE_CSS = '''
body {
    font-family: __FONT_STACK__;
    line-height: 1.8;
    text-align: justify;
    margin: 1em;
}

/* Copyright */
.copyright-page {
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    margin: 3em 0;
}

.copyright-year {
    font-size: 1.2em;
    margin-bottom: 1em;
}

.copyright-text {
    font-size: 1em;
    text-align: center;
}

/* TOC */
.toc-title {
    text-align: center;
    font-size: 1.6em;
    margin: 2em 0 1em 0;
    font-weight: bold;
}

.toc-entry {
    text-align: left;
    margin: 0.5em 0;
}

.toc-link {
    text-decoration: none;
    color: #000;
}

/* Headings */
.chapter-heading {
    page-break-before: always;
    margin: 3em 0 2em 0;
}

.chapter-heading h1 {
    text-align: center;
    font-size: 1.5em;
    font-weight: bold;
    margin: 0;
}

h1 {
    text-align: center;
    font-size: 1.5em;
    font-weight: bold;
    margin: 2em 0 1em 0;
}

h2.section-subtitle,
.section-heading h2 {
    text-align: center;
    font-size: 1.2em;
    margin: 1em 0;
}

/* Paragraphs */
p {
    text-align: justify;
    text-indent: 1.5em;
    margin-bottom: 0.8em;
    line-height: 1.8;
}

.preserve-break {
    text-indent: 0;
    margin-bottom: 0.3em;
    text-align: left;
}

/* Special sections */
/* Front matter (title page, copyright, epigraph, dedication) */
.front-matter {
    text-align: center;
    page-break-before: always;
    page-break-after: always;
    margin: 3em 0;
}
.front-matter:empty + .front-matter { page-break-before: auto; }
.front-matter:empty { page-break-before: auto; page-break-after: auto; margin: 0; }
.front-matter p {
    text-align: center;
    text-indent: 0;
    margin: 0.4em 0;
}
.front-matter .front-title {
    font-size: 1.6em;
    font-weight: bold;
    margin: 2em 0 0.6em;
}
.front-matter.copyright p { font-size: 0.75em; margin: 0.2em 0; }
.front-matter .copyright-page {
    page-break-before: auto;
    page-break-after: auto;
    margin: 0;
}

/* Quote attribution: right-aligned, like the source */
.quote-attribution {
    text-align: right;
    text-indent: 0;
    margin: 0.4em 0 1.2em;
}
.front-matter.epigraphs {
    text-align: left;
    page-break-after: auto;
    margin: 0;
    padding: 0 1.5em;
}
.front-matter.epigraphs p {
    text-align: left;
    margin: 0;
}
.front-matter.epigraphs .quote-attribution {
    text-align: right;
    margin: 0.4em 0 1.2em;
}
.toc-entry small {
    font-size: 0.75em;
}

.quote-attribution small { font-size: 0.6em; }
.front-matter .front-sub { font-size: 1.1em; font-style: italic; margin-bottom: 2em; }
.dedication {
    text-align: center;
    font-style: italic;
    text-indent: 0;
    margin: 2em 3em;
}

.epigraph {
    text-align: center;
    font-style: italic;
    text-indent: 0;
    margin: 1.5em 3em;
}

.epigraph-attribution {
    text-align: center;
    text-indent: 0;
}

/* Dialogue */
.dialogue {
    margin: 1em 0;
}

.dialogue-line {
    text-indent: 0 !important;
    margin-bottom: 0.3em;
}

/* Page markers */
.page-marker {
    color: #999;
    font-size: 0.85em;
    font-style: italic;
    text-align: center;
    text-indent: 0;
    margin: 1.5em 0;
}
'''

def extract_anchor_map(chapters_data):
    """Extract mapping of anchor IDs to chapter indices (first occurrence wins, as in HTML)."""
    import re
    anchor_map = {}

    for i, chapter_data in enumerate(chapters_data):
        # Find all id attributes in this chapter
        id_pattern = r'id="([^"]+)"'
        for match in re.finditer(id_pattern, chapter_data['content']):
            anchor_id = match.group(1)
            anchor_map.setdefault(anchor_id, i)

    return anchor_map

def fix_toc_links(chapters_data, anchor_map):
    """Fix TOC links to point to correct chapter files."""
    import re

    for i, chapter_data in enumerate(chapters_data):
        content = chapter_data['content']

        # Find all internal anchor links
        link_pattern = r'<a\s+href="#([^"]+)"([^>]*)>(.*?)</a>'

        def replace_link(match):
            anchor_id = match.group(1)
            other_attrs = match.group(2)
            link_text = match.group(3)

            # Find which chapter contains this anchor
            if anchor_id in anchor_map:
                target_chapter_idx = anchor_map[anchor_id]
                # If anchor is in a different chapter, add chapter file reference
                if target_chapter_idx != i:
                    chapter_file = f'chapter_{target_chapter_idx + 1:03d}.xhtml'
                    return f'<a href="{chapter_file}#{anchor_id}"{other_attrs}>{link_text}</a>'

            # Keep original link if anchor is in same chapter or not found
            return match.group(0)

        chapter_data['content'] = re.sub(link_pattern, replace_link, content)

    return chapters_data

def build_detailed_toc(chapters_data, anchor_map):
    """Build detailed TOC entries for all major sections."""
    import re

    toc_entries = []

    for i, chapter_data in enumerate(chapters_data):
        chapter_file = f'chapter_{i+1:03d}.xhtml'
        chapter_title = chapter_data['title']

        # Add main chapter entry
        toc_entries.append({
            'title': chapter_title,
            'file': chapter_file,
            'id': f'chapter_{i+1}'
        })

        # Find all anchors with headings in this chapter
        # Look for patterns like: <div id="anchor"><h1>Title</h1>
        anchor_heading_pattern = r'<div\s+id="([^"]+)"[^>]*>\s*<h1[^>]*>([^<]+)</h1>'

        for match in re.finditer(anchor_heading_pattern, chapter_data['content']):
            anchor_id = match.group(1)
            heading_text = match.group(2).strip()

            # Add as sub-entry only if it's different from chapter title
            if heading_text != chapter_title:
                toc_entries.append({
                    'title': heading_text,
                    'file': f'{chapter_file}#{anchor_id}',
                    'id': anchor_id
                })

    return toc_entries

def split_content_by_chapters(html_content):
    """Split HTML content into chapters based on h1 headings."""
    import re

    # Find all chapter headings and their positions
    # Look for either standalone h1 or h1 inside chapter-heading div
    chapter_pattern = r'(?:<div[^>]*class="chapter-heading"[^>]*>[\s\n]*)?<h1[^>]*>(.*?)</h1>'
    chapters = []

    matches = list(re.finditer(chapter_pattern, html_content, re.DOTALL))

    if not matches:
        # No chapters found, return single chapter
        return [{"title": "Content", "content": html_content}]

    for i, match in enumerate(matches):
        chapter_title = re.sub(r'<[^>]+>', '', match.group(1)).strip()  # Remove HTML tags
        start_pos = match.start()

        # Find end position (start of next chapter or end of content)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(html_content)

        chapter_content = html_content[start_pos:end_pos]

        chapters.append({
            "title": chapter_title,
            "content": chapter_content
        })

    # Add content before first chapter if any
    if matches[0].start() > 0:
        intro_content = html_content[:matches[0].start()]
        if intro_content.strip():
            chapters.insert(0, {
                "title": "Introduction",
                "content": intro_content
            })

    return chapters

def create_epub(html_content, title="", author="", identifier="", language="vi",
                cover_path=None, font=None, fonts_dir=None):
    """Create EPUB book from processed HTML content.

    Args:
        title: Book title (required for a well-formed EPUB).
        author: Book author; omitted from metadata when empty.
        identifier: EPUB identifier; falls back to a title-derived slug.
        language: BCP-47 language tag of the content.
        cover_path: Path to the cover image, if any.
        font: Font family folder under ``fonts_dir`` (default: fonts.DEFAULT_FONT).
        fonts_dir: Root holding one folder per font family (default: repo fonts/).
    """
    book = epub.EpubBook()

    # Set metadata
    if not identifier:
        identifier = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'untitled'
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(language)
    if author:
        book.add_author(author)

    # Add cover as book cover (not content)
    cover = Path(cover_path) if cover_path else None
    if cover and cover.exists():
        with open(cover, 'rb') as f:
            book.set_cover(cover.name, f.read())
        book.add_item(epub.EpubItem(uid="cover_style", file_name="style/cover.css",
                                    media_type="text/css", content=COVER_CSS))
        cover_page = book.get_item_with_id('cover')
        cover_page.add_link(href='style/cover.css', rel='stylesheet', type='text/css')
        cover_page.is_linear = True  # shown as the first page

    # Add CSS + embedded font files
    family = resolve_font(font, fonts_dir)
    style = get_css(family, fonts_dir)
    default_css = epub.EpubItem(uid="style", file_name="style/style.css", media_type="text/css", content=style)
    book.add_item(default_css)

    sc_family, _ = small_caps(family, fonts_dir)
    for f in family.files + (sc_family.files if sc_family else []):
        book.add_item(epub.EpubItem(
            uid=f"font_{f.path.parent.name.lower()}_{f.variant.lower()}",
            file_name=epub_font_path(f),
            media_type=f.media_type,
            content=f.path.read_bytes(),
        ))

    # Split content into chapters
    chapters_data = split_content_by_chapters(html_content)

    # Extract anchor mapping
    anchor_map = extract_anchor_map(chapters_data)

    # Fix TOC links to be cross-chapter
    chapters_data = fix_toc_links(chapters_data, anchor_map)

    # Build detailed TOC
    detailed_toc = build_detailed_toc(chapters_data, anchor_map)

    # Create EPUB chapters
    epub_chapters = []
    toc_entries = []

    for i, chapter_data in enumerate(chapters_data):
        # Create chapter file
        file_name = f'chapter_{i+1:03d}.xhtml'
        chapter = epub.EpubHtml(
            title=chapter_data['title'],
            file_name=file_name,
            lang='vi'
        )
        chapter.content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="vi">
<head>
    <title>{chapter_data['title']}</title>
</head>
<body>
{chapter_data['content']}
</body>
</html>'''

        # Link CSS to chapter
        chapter.add_link(href='style/style.css', rel='stylesheet', type='text/css')

        book.add_item(chapter)
        epub_chapters.append(chapter)

    # Build TOC from detailed entries
    for entry in detailed_toc:
        toc_entries.append(epub.Link(entry['file'], entry['title'], entry['id']))

    # Build TOC
    book.toc = tuple(toc_entries)

    # Add NCX and Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define reading order (spine)
    book.spine = (['cover'] if book.get_item_with_id('cover') else []) + epub_chapters

    return book

def main():
    """Export book to EPUB."""
    parser = argparse.ArgumentParser(description='Export book to EPUB format')
    parser.add_argument('--test', action='store_true', help='Export chunk 1 only (test mode)')
    parser.add_argument('--chunks', type=str, help='Export specific chunks (e.g., "1-5" or "1,3,5")')
    add_book_argument(parser)
    args = parser.parse_args()

    cfg = get_config_from_args(args)

    print("=" * 60)
    if args.test:
        print("📚 EPUB Export - Test Mode (Chunk 1)")
    elif args.chunks:
        print(f"📚 EPUB Export - Chunks {args.chunks}")
    else:
        print("📚 Full Book EPUB Export")
    print(f"Title: {cfg.display_title}")
    print("=" * 60)

    # Determine which chunks to load
    translated_dir = cfg.translated_dir

    try:
        chunk_files, output_suffix, export_mode = load_chunks(
            test=args.test, chunks=args.chunks, translated_dir=translated_dir
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return

    if args.test:
        title = f"{cfg.display_title} - Test (Chunk 1)"
    elif args.chunks:
        title = f"{cfg.display_title} - Chunks {args.chunks}"
    else:
        title = cfg.display_title

    safe_title = re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(cfg.output_dir / f"{safe_title}{output_suffix}.epub")

    print(f"\n✓ Found {len(chunk_files)} chunks")

    # Read and merge chunks
    chunks = []
    for chunk_file in chunk_files:
        if not chunk_file.exists():
            print(f"❌ Missing {chunk_file}")
            return
        with open(chunk_file, 'r', encoding='utf-8') as f:
            content = f.read()
            chunks.append(content)
        print(f"  ✓ Loaded {chunk_file.name}")

    # Merge content
    merged_content = '\n\n'.join(chunks)
    print(f"\n✓ Merged {len(chunks)} chunks")

    # Check cover
    if cfg.cover_path.exists():
        print(f"✓ Found {cfg.cover_path.name}")

    # Process using PDF export logic
    print(f"\n📝 Processing content (same as PDF export)...")
    md_with_links = make_toc_links_clickable(merged_content)
    html_content = markdown_to_html_with_dialogue(md_with_links, include_cover=False)

    print(f"✓ Generated {len(html_content):,} characters of HTML")

    # Create EPUB
    print(f"\n📄 Generating EPUB with TOC...")
    book = create_epub(
        html_content,
        title=title,
        author=cfg.author,
        identifier=cfg.epub_identifier or f"{cfg.id}-vi",
        cover_path=cfg.cover_path,
        font=cfg.font,
    )

    # Count chapters in TOC
    chapter_count = len(book.toc) if book.toc else 0
    print(f"✓ Generated {chapter_count} chapters with TOC links")

    # Write file
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    epub.write_epub(output_path, book, {})

    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"\n✅ EPUB exported → {output_path}")
    print(f"📊 File size: {file_size:.2f} MB")
    print("\n" + "=" * 60)
    print("✅ Export complete!")
    print("=" * 60)
    print(f"\n💡 Features:")
    print(f"   • Title: {title}")
    print(f"   • Font: {cfg.font or DEFAULT_FONT} (embedded)")
    print("   • All formatting from PDF export")
    print("   • Cover included")
    print(f"   • TOC with {chapter_count} clickable chapter links")
    print(f"   • Total chunks: {len(chunk_files)}")
    print("\n📖 EPUB ready!")

if __name__ == "__main__":
    # Allow direct execution (``python scripts/utils/<name>.py``) despite the
    # package-relative imports above, which otherwise raise ImportError.
    import sys as _sys
    from pathlib import Path as _Path
    _r = _Path(__file__).resolve().parents[2]
    if str(_r) not in _sys.path:
        _sys.path.insert(0, str(_r))
    from scripts.utils.export_epub import main as _main
    _main()
