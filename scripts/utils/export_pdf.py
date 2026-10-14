#!/usr/bin/env python3
"""
Export book to PDF format.

⚠️  This is an individual utility script. For normal usage, use:
    python scripts/export.py -f pdf

Advanced usage (direct):
    python scripts/utils/export_pdf.py                    # Export full book
    python scripts/utils/export_pdf.py --test             # Export chunk 1 only (test)
    python scripts/utils/export_pdf.py --chunks 1-5       # Export chunks 1-5
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/export_pdf.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import os
import re
import argparse
from pathlib import Path

# Import shared markdown conversion functions
from .markdown_converter import (
    load_toc_language_config,
    make_toc_links_clickable,
    markdown_to_html_with_dialogue
)
from .book_config import REPO_ROOT, add_book_argument, get_config_from_args
from .chunk_loader import load_chunks
from .fonts import DEFAULT_FONT, resolve_font, small_caps

def create_pdf(md_content, output_path, title="un-titled", proof_mode=False, cover_path=None,
               font=None, fonts_dir=None):
    """Create PDF with WeasyPrint.

    Args:
        md_content: Markdown content to render
        output_path: Path for output PDF file
        title: Book title for metadata
        proof_mode: If True, use Letter size (612x792pt) with 1-inch margins
                   and 11pt font for structural verification against source PDF.
                   If False (default), use Letter with the source PDF's body metrics
                   (14.4pt text, ~57pt side / 66pt top margins).
        font: Font family folder under ``fonts_dir`` (default: fonts.DEFAULT_FONT).
        fonts_dir: Root holding one folder per font family (default: repo fonts/).
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        print("❌ WeasyPrint not installed!")
        print("Install with: pip install weasyprint --break-system-packages")
        return False

    # Convert markdown to HTML
    # Note: Caller should call make_toc_links_clickable() before passing content here
    # to avoid double-processing
    html_content = markdown_to_html_with_dialogue(md_content, include_cover=True, cover_path=cover_path)

    family = resolve_font(font, fonts_dir)
    font_faces = family.font_face_css(lambda f: f.path.as_uri())
    sc_family, sc_css = small_caps(family, fonts_dir)
    if sc_family:
        font_faces += "\n" + sc_family.font_face_css(lambda f: f.path.as_uri())
    font_faces += "\n" + sc_css + "\n"

    # Page size and margin differ between proof and default modes
    if proof_mode:
        # Proof mode: Letter size matching source PDF for structural verification
        page_css = """
        @page {
            size: 612pt 792pt;  /* Letter size, matches source PDF */
            margin: 72pt;       /* 1 inch margins */
            @bottom-center {
                content: counter(page);
                font-family: __FONT_STACK__;
                font-size: 10pt;
            }
        }

        @page :first {
            @bottom-center { content: none; }   /* no number on the cover */
        }

        body {
            font-family: __FONT_STACK__;
            font-size: 11pt;
            line-height: 1.5;
        }
        """
    else:
        # Default mode: same page size and body metrics as the source PDF
        page_css = """
        @page {
            size: 612pt 792pt;      /* Letter, matches source PDF */
            margin: 66pt 57pt;      /* source text block */
            @bottom-center {
                content: counter(page);
                font-family: __FONT_STACK__;
                font-size: 10pt;
            }
        }

        @page :first {
            @bottom-center { content: none; }   /* no number on the cover */
        }

        body {
            font-family: __FONT_STACK__;
            font-size: 14.4pt;      /* source body size */
            line-height: 1.4;
        }
        """

    page_css = page_css.replace("__FONT_STACK__", family.css_stack)
    css = font_faces + page_css + f"""

    /* Cover page: full bleed, its own page with no margins */
    @page cover {{
        margin: 0;
        @bottom-center {{ content: none; }}
    }}
    .cover-page {{
        page: cover;
        page-break-after: always;
        padding: 0;
        margin: -8px;   /* cancel the UA body margin (8px) so the image bleeds */
        width: 612pt;
        height: 792pt;
    }}
    """ + """

    .cover-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    /* Copyright page */
    .copyright-page {
        page-break-before: always;
        page-break-after: always;
        text-align: center;
        margin: 3em 0;
    }

    .copyright-year {
        font-size: 11pt;
        font-weight: normal;
        text-align: center;
        text-indent: 0;
        margin-bottom: 1em;
    }

    .copyright-text {
        font-size: 9pt;
        text-align: center;
        text-indent: 0;
        margin-bottom: 0.8em;
        line-height: 1.5;
    }

    /* Publisher page */
    .publisher-page {
        page-break-before: always;
        page-break-after: always;
        margin: 2em 0;
    }

    .publisher-text {
        font-size: 8pt;
        text-align: justify;
        text-indent: 0;
        margin-bottom: 0.8em;
        line-height: 1.5;
    }

    /* TOC styling */
    .toc-title {
        text-align: center;
        font-size: 1em;
        margin: 1.5em 0 1em 0;
        letter-spacing: 0.1em;
        page-break-after: avoid;
    }

    .toc-entry {
        text-align: left;
        text-indent: 0;
        margin: 0.3em 0;
        font-size: 14.4pt;
        display: block;
    }

    .toc-link {
        text-decoration: none;
        color: #0066cc;
        display: block;
        cursor: pointer;
        transition: color 0.2s;
    }

    .toc-link:hover {
        color: #003366;
        text-decoration: underline;
    }

    /* Chapter headings */
    .chapter-heading {
        page-break-before: always;
        margin-top: 2em;
        margin-bottom: 1em;
    }

    .chapter-heading h1 {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        margin: 0;
        page-break-after: avoid;
    }

    h1 {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        margin: 1.5em 0 0.8em 0;
        page-break-after: avoid;
    }

    /* All headings render at body size (bold/centred only) */
    h2, h3, h4, h5, h6 {
        font-size: 1em;
    }

    h2.section-subtitle {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        margin: 1em 0 0.8em 0;
        page-break-after: avoid;
    }

    .section-heading h2 {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        margin: 1em 0 0.8em 0;
        page-break-after: avoid;
    }

    p {
        text-align: justify;
        text-indent: 1em;
        margin-bottom: 0.5em;
        orphans: 2;
        widows: 2;
    }

    /* Preserve line breaks for short lines */
    .preserve-break {
        text-indent: 0;
        margin-bottom: 0.2em;
        text-align: left;
    }

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
    /* Dedication styling */
    .dedication {
        text-align: center;
        font-style: italic;
        text-indent: 0;
        margin: 1.5em 2em;
        font-size: 9pt;
    }

    /* Epigraph styling */
    .epigraph {
        text-align: center;
        font-style: italic;
        text-indent: 0;
        margin: 1em 2em;
        font-size: 9pt;
    }

    .epigraph-attribution {
        text-align: center;
        text-indent: 0;
        margin-top: 0.3em;
        font-size: 9pt;
    }

    /* Dialogue formatting */
    .dialogue {
        margin: 0.8em 0;
    }

    .dialogue-line {
        text-indent: 0 !important;
        margin-bottom: 0.2em;
        line-height: 1.5;
    }

    /* Page markers */
    .page-marker {
        color: #999;
        font-size: 7pt;
        font-style: italic;
        text-align: center;
        text-indent: 0;
        margin: 1em 0 0.3em 0;
    }

    /* Footnote reference (in text) and back-link (in note) */
    .footnote-ref,
    .footnote-back {
        color: #0066cc;
        text-decoration: none;
    }
    .footnote-back {
        font-weight: bold;
    }
    .footnote-back:hover {
        text-decoration: underline;
    }
    """

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
{html_content}
</body>
</html>
"""

    # Generate PDF
    font_config = FontConfiguration()
    HTML(string=html_template).write_pdf(
        output_path,
        stylesheets=[CSS(string=css, font_config=font_config)],
        font_config=font_config
    )

    return True

def main():
    """Export book to PDF."""
    parser = argparse.ArgumentParser(description='Export book to PDF format')
    parser.add_argument('--test', action='store_true', help='Export chunk 1 only (test mode)')
    parser.add_argument('--chunks', type=str, help='Export specific chunks (e.g., "1-5" or "1,3,5")')
    parser.add_argument('--proof', action='store_true',
                       help='Proof mode: Letter size (612×792pt) with 1-inch margins and 11pt font for structural verification')
    add_book_argument(parser)
    args = parser.parse_args()

    cfg = get_config_from_args(args)

    print("=" * 60)
    if args.test:
        print("📖 PDF Export - Test Mode (Chunk 1)")
    elif args.chunks:
        print(f"📖 PDF Export - Chunks {args.chunks}")
    else:
        print("📚 Full Book PDF Export")
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
    proof_suffix = "_proof" if args.proof else ""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(cfg.output_dir / f"{safe_title}{output_suffix}{proof_suffix}.pdf")

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

    # Process TOC links
    print(f"\n📝 Processing TOC links...")
    md_with_toc = make_toc_links_clickable(merged_content)
    print(f"✓ TOC links processed")

    # Create PDF
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    print(f"\n📄 Generating PDF{'(proof mode)' if args.proof else ''}...")
    if create_pdf(md_with_toc, output_path, title=title, proof_mode=args.proof, font=cfg.font):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"\n✅ PDF exported → {output_path}")
        print(f"📊 File size: {file_size:.2f} MB")
        print("\n" + "=" * 60)
        print("✅ Export complete!")
        print("=" * 60)
        print(f"\n💡 Settings:")
        if args.proof:
            print("   • Page size: 612pt × 792pt (US Letter, proof mode)")
            print("   • Margins: 72pt (1 inch, all sides)")
            print(f"   • Font: {cfg.font or DEFAULT_FONT}, 11pt")
            print("   • Line height: 1.5")
            print("   • Cover: Fitted within margins")
            print(f"   • Total chunks: {len(chunk_files)}")
            print("\n📋 Proof copy for structural verification!")
        else:
            print("   • Page size: 612pt × 792pt (US Letter, same as source)")
            print("   • Margins: 66pt top/bottom, 57pt sides")
            print(f"   • Font: {cfg.font or DEFAULT_FONT}, 14.4pt")
            print("   • Line height: 1.4")
            print("   • Cover: Fitted within margins")
            print(f"   • Total chunks: {len(chunk_files)}")
            print("\n📖 PDF ready!")
    else:
        print("\n❌ PDF export failed")

if __name__ == "__main__":
    main()
