#!/usr/bin/env python3
"""
Export book to HTML format for preview.
Usage:
    python3 scripts/export_html.py                   # Export full book
    python3 scripts/export_html.py --test            # Export chunk 1 only (test)
    python3 scripts/export_html.py --chunks 1-5      # Export chunks 1-5
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/export_html.py``. This file and its
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
import base64
from pathlib import Path

# Import shared markdown conversion functions
from .markdown_converter import (
    make_toc_links_clickable,
    markdown_to_html_with_dialogue
)
from .book_config import REPO_ROOT, add_book_argument, get_config_from_args
from .chunk_loader import load_chunks
from .fonts import resolve_font, small_caps

def get_font_face_css(family):
    """@font-face CSS with the family's files embedded as base64 data URIs."""
    def data_uri(f):
        data = base64.b64encode(f.path.read_bytes()).decode("ascii")
        return f"data:{f.media_type};base64,{data}"
    return family.font_face_css(data_uri)

def create_html(html_content, title="untitled", cover_path=None, font=None, fonts_dir=None):
    """Create standalone HTML file."""

    # Check for cover
    cover_html = ""
    cover = Path(cover_path) if cover_path else Path('cover.jpg')
    if cover.exists():
        cover_html = f'''
    <div class="cover-page">
        <img src="file://{cover.resolve()}" alt="Cover" class="cover-image"/>
    </div>
'''

    # Get embedded font CSS
    family = resolve_font(font, fonts_dir)
    font_face_css = get_font_face_css(family)
    sc_family, sc_css = small_caps(family, fonts_dir)
    if sc_family:
        font_face_css += "\n" + get_font_face_css(sc_family)
    font_face_css += "\n" + sc_css

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{font_face_css}

        body {{
            font-family: {family.css_stack};
            font-size: 11pt;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2em;
            background-color: #f5f5f5;
        }}

        .content {{
            background-color: white;
            padding: 3em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Cover page */
        .cover-page {{
            text-align: center;
            margin-bottom: 3em;
            page-break-after: always;
        }}

        .cover-image {{
            max-width: 100%;
            height: auto;
        }}

        /* Copyright */
        .copyright-page {{
            page-break-before: always;
            page-break-after: always;
            text-align: center;
            margin: 3em 0;
        }}

        .copyright-year {{
            font-size: 1.2em;
            margin-bottom: 1em;
        }}

        .copyright-text {{
            font-size: 0.9em;
            text-align: center;
        }}

        /* TOC */
        .toc-title {{
            text-align: center;
            font-size: 1.8em;
            margin: 2em 0 1em 0;
            font-weight: bold;
        }}

        .toc-entry {{
            text-align: left;
            margin: 0.5em 0;
        }}

        .toc-link {{
            text-decoration: none;
            color: #333;
        }}

        .toc-link:hover {{
            color: #0066cc;
            text-decoration: underline;
        }}

        /* Headings */
        .chapter-heading {{
            page-break-before: always;
            margin: 3em 0 2em 0;
        }}

        .chapter-heading h1 {{
            text-align: center;
            font-size: 1.6em;
            font-weight: bold;
            margin: 0;
        }}

        h1 {{
            text-align: center;
            font-size: 1.6em;
            font-weight: bold;
            margin: 2em 0 1em 0;
        }}

        h2.section-subtitle {{
            text-align: center;
            font-size: 1.3em;
            margin: 1em 0;
        }}

        /* Paragraphs */
        p {{
            text-align: justify;
            text-indent: 1.5em;
            margin-bottom: 0.8em;
            line-height: 1.6;
        }}

        .preserve-break {{
            text-indent: 0;
            margin-bottom: 0.3em;
            text-align: left;
        }}

        /* Special sections */
        /* Front matter (title page, copyright, epigraph, dedication) */
        .front-matter {{
            text-align: center;
            page-break-before: always;
            page-break-after: always;
            margin: 3em 0;
        }}
        .front-matter:empty + .front-matter {{ page-break-before: auto; }}
        .front-matter:empty {{ page-break-before: auto; page-break-after: auto; margin: 0; }}
        .front-matter p {{
            text-align: center;
            text-indent: 0;
            margin: 0.4em 0;
        }}
        .front-matter .front-title {{
            font-size: 1.6em;
            font-weight: bold;
            margin: 2em 0 0.6em;
        }}
        .front-matter.copyright p {{ font-size: 0.75em; margin: 0.2em 0; }}
        .front-matter .copyright-page {{
            page-break-before: auto;
            page-break-after: auto;
            margin: 0;
        }}

        /* Quote attribution: right-aligned, like the source */
        .quote-attribution {{
            text-align: right;
            text-indent: 0;
            margin: 0.4em 0 1.2em;
        }}
        .front-matter.epigraphs {{
            text-align: left;
            page-break-after: auto;
            margin: 0;
            padding: 0 1.5em;
        }}
        .front-matter.epigraphs p {{
            text-align: left;
            margin: 0;
        }}
        .front-matter.epigraphs .quote-attribution {{
            text-align: right;
            margin: 0.4em 0 1.2em;
        }}
        .toc-entry small {{
            font-size: 0.75em;
        }}

        .quote-attribution small {{ font-size: 0.6em; }}
        .front-matter .front-sub {{ font-size: 1.1em; font-style: italic; margin-bottom: 2em; }}
        .dedication {{
            text-align: center;
            font-style: italic;
            text-indent: 0;
            margin: 2em 3em;
        }}

        .epigraph {{
            text-align: center;
            font-style: italic;
            text-indent: 0;
            margin: 1.5em 3em;
        }}

        .epigraph-attribution {{
            text-align: center;
            text-indent: 0;
        }}

        /* Dialogue */
        .dialogue {{
            margin: 1em 0;
        }}

        .dialogue-line {{
            text-indent: 0 !important;
            margin-bottom: 0.3em;
        }}

        /* Page markers */
        .page-marker {{
            color: #999;
            font-size: 0.85em;
            font-style: italic;
            text-align: center;
            text-indent: 0;
            margin: 1.5em 0;
        }}
    </style>
</head>
<body>
    <div class="content">
{cover_html}
{html_content}
    </div>
</body>
</html>
"""
    return html_template

def main():
    """Export book to HTML."""
    parser = argparse.ArgumentParser(description='Export book to HTML format')
    parser.add_argument('--test', action='store_true', help='Export chunk 1 only (test mode)')
    parser.add_argument('--chunks', type=str, help='Export specific chunks (e.g., "1-5" or "1,3,5")')
    add_book_argument(parser)
    args = parser.parse_args()

    cfg = get_config_from_args(args)

    print("=" * 60)
    if args.test:
        print("📄 HTML Export - Test Mode (Chunk 1)")
    elif args.chunks:
        print(f"📄 HTML Export - Chunks {args.chunks}")
    else:
        print("📄 Full Book HTML Export")
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
    output_path = str(cfg.output_dir / f"{safe_title}{output_suffix}.html")

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
    print(f"\n📝 Processing content...")
    md_with_links = make_toc_links_clickable(merged_content)
    html_content = markdown_to_html_with_dialogue(md_with_links, include_cover=False)

    print(f"✓ Generated {len(html_content):,} characters of HTML")

    # Create HTML
    print(f"\n📄 Generating HTML...")
    html_output = create_html(html_content, title=title, cover_path=cfg.cover_path, font=cfg.font)

    # Write file
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"\n✅ HTML exported → {output_path}")
    print(f"📊 File size: {file_size:.2f} MB")
    print("\n" + "=" * 60)
    print("✅ Export complete!")
    print("=" * 60)
    print(f"\n💡 Features:")
    print("   • Title: untitled")
    print("   • Responsive web layout")
    print("   • TOC with clickable links")
    print("   • Cover included")
    print(f"   • Total chunks: {len(chunk_files)}")
    print("\n🌐 Open in browser to preview!")

if __name__ == "__main__":
    # Allow direct execution (``python scripts/utils/<name>.py``) despite the
    # package-relative imports above, which otherwise raise ImportError.
    import sys as _sys
    from pathlib import Path as _Path
    _r = _Path(__file__).resolve().parents[2]
    if str(_r) not in _sys.path:
        _sys.path.insert(0, str(_r))
    from scripts.utils.export_html import main as _main
    _main()
