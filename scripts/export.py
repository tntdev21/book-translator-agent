#!/usr/bin/env python3
"""
Unified export script - exports to PDF, EPUB, and HTML.
Combines: export_pdf, export_epub, export_html

Usage:
    python scripts/export.py                     # Export all formats (all chunks)
    python scripts/export.py -f pdf              # Export only PDF
    python scripts/export.py -f epub             # Export only EPUB
    python scripts/export.py -f html             # Export only HTML
    python scripts/export.py --test              # Export chunk 1 only (test mode)
    python scripts/export.py --chunks 1-5        # Export chunks 1-5
    python scripts/export.py --chunks 1,3,5      # Export specific chunks
    python scripts/export.py -o output/ -t "Title" -a "Author"

The book to export is picked with --book <id>, $BOOK_ID, or automatically when
exactly one book exists under books/. Title/author default to the book's
book.yaml.
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from utils.book_config import add_book_argument, get_config_from_args
from utils.chunk_loader import load_chunks
from utils.fonts import FontNotFoundError, resolve_font


def main():
    parser = argparse.ArgumentParser(
        description='Export translated book to various formats'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['pdf', 'epub', 'html', 'all'],
        default='all',
        help='Output format (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        '-o',
        default=None,
        help="Output directory (default: the book's output/ directory)"
    )
    parser.add_argument(
        '--title',
        '-t',
        help="Book title (default: the book's title_vi from book.yaml)"
    )
    parser.add_argument(
        '--author',
        '-a',
        help="Book author (default: the book's author from book.yaml)"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Export chunk 1 only (test mode)'
    )
    parser.add_argument(
        '--chunks',
        type=str,
        help='Export specific chunks (e.g., "1-5" or "1,3,5")'
    )
    parser.add_argument(
        '--force',
        '-y',
        action='store_true',
        help='Continue export even if TOC validation fails (required in non-interactive sessions)'
    )
    parser.add_argument(
        '--proof',
        action='store_true',
        help='Proof mode: Letter size (612×792pt) with 1-inch margins and 11pt font (PDF only)'
    )
    parser.add_argument(
        '--font',
        type=str,
        help='Font folder under fonts/ (default: book.yaml "font", else Literata)'
    )
    add_book_argument(parser)

    args = parser.parse_args()
    cfg = get_config_from_args(args)
    font = args.font or cfg.font or None
    try:
        family = resolve_font(font)  # fail before the slow merge/convert steps
    except FontNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print(f"Font: {family.name}")

    # Load chunks based on mode (test/specific/full)
    # Proof mode is special: it reads the English extracted source
    # (source/full_text.md) directly for structural verification against the
    # original PDF, bypassing the translated/ directory entirely.
    if args.proof:
        source_file = cfg.source_file
        if not source_file.exists():
            print(f"❌ Error: source file not found: {source_file}")
            print("💡 Tip: run `python scripts/extract.py` first to produce the English source.")
            return 1
        files = [source_file]
        output_suffix = "_proof"
        export_mode = "Proof (English source)"
    else:
        try:
            files, output_suffix, export_mode = load_chunks(
                test=args.test,
                chunks=args.chunks,
                translated_dir=cfg.translated_dir
            )
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Error: {e}")
            if isinstance(e, FileNotFoundError) and "No translated files" in str(e):
                print("💡 Tip: Translate some chunks first!")
            return 1

    output_dir = Path(args.output_dir) if args.output_dir else cfg.output_dir
    title = args.title or cfg.title_vi
    if args.proof:
        title = args.title or cfg.title_en
    author = args.author or cfg.author

    print("=" * 60)
    print("📚 Book Export Tool")
    print("=" * 60)
    print(f"Book: {cfg.id} ({title})")
    print(f"Mode: {export_mode}")
    print(f"Found {len(files)} source file(s)" if args.proof else f"Found {len(files)} translated chunk(s)")
    print(f"Output directory: {output_dir}")
    print(f"Format: {args.format}")
    if args.proof:
        print("Proof: ON (English source → Letter-size PDF for structural verification)")
    print()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear output directory before generating new files
    # This prevents stale debug HTML and old PDFs from accumulating
    cleared_count = 0
    for old_file in output_dir.iterdir():
        if old_file.is_file() and old_file.name != ".DS_Store":
            old_file.unlink()
            cleared_count += 1
    if cleared_count > 0:
        print(f"🗑️  Cleared {cleared_count} old file(s) from output/")

    # Generate timestamp suffix for this run
    timestamp = datetime.now().strftime('%Y-%m-%dT%H%M%S')
    print(f"  ⏱️  Timestamp: {timestamp}")

    # Collect existing exports to clean up later (before writing new ones)
    existing_exports = set(output_dir.glob(f'document{output_suffix}_*'))
    print()

    success_count = 0
    formats_to_export = []
    exported_files = []  # Track files created during this run

    if args.format == 'all':
        formats_to_export = ['pdf', 'epub', 'html']
    else:
        formats_to_export = [args.format]

    # Pre-export: Validate TOC format
    print(f"\n{'=' * 60}")
    print("🔍 Pre-processing: Validating TOC...")
    print("=" * 60)
    try:
        from utils.validate_toc import TOCValidator

        validator = TOCValidator(cfg.translated_dir)
        validation_passed = validator.validate_all()

        if not validation_passed:
            print("\n⚠️  TOC validation failed. Please fix errors before exporting.")
            print("See docs/toc-standards.md for format requirements.")
            if not args.force:
                if not sys.stdin.isatty():
                    print("❌ Export cancelled (non-interactive session).")
                    print("💡 Re-run with --force/-y to export despite validation errors.")
                    return 1
                user_input = input("\nContinue with export anyway? (y/N): ")
                if user_input.lower() != 'y':
                    print("❌ Export cancelled.")
                    return
            print("⚠️  Continuing with export despite validation errors...\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not validate TOC: {e}")
        print("Continuing with export anyway...")

    # Pre-export: Run full fix (sentence breaks + dashes + formatting)
    print(f"\n{'=' * 60}")
    print("🔧 Pre-processing: Running fixes...")
    print("=" * 60)
    try:
        from utils.fix_sentence_breaks import fix_sentence_breaks
        from utils.normalize_dashes import normalize_dashes_file

        total_fixes = 0

        # Step 1: Fix sentence breaks
        print("📝 Fixing sentence breaks...")
        for file in files:
            fixes = fix_sentence_breaks(file, backup=False)
            if fixes > 0:
                print(f"  ✓ {file.name}: {fixes} breaks")
                total_fixes += fixes

        # Step 2: Normalize dashes
        print("➖ Normalizing dashes...")
        for file in files:
            changes = normalize_dashes_file(str(file))
            if changes > 0:
                total_fixes += changes

        if total_fixes > 0:
            print(f"✅ Applied {total_fixes} fixes")
        else:
            print("✅ No fixes needed")
    except Exception as e:
        print(f"⚠️  Warning: Could not run fixes: {e}")
        print("Continuing with export anyway...")

    # Export to each format
    for idx, fmt in enumerate(formats_to_export, 1):
        progress = f"[{idx}/{len(formats_to_export)}]"
        print(f"\n{'=' * 60}")
        print(f"📄 {progress} Exporting to {fmt.upper()}...")
        print("=" * 60)

        try:
            # Read and merge all translated files
            print(f"Reading {len(files)} translated files...")
            merged_content = '\n\n'.join([f.read_text(encoding='utf-8') for f in files])
            from utils.markdown_converter import fill_title_page
            merged_content = fill_title_page(merged_content, cfg.title_vi or cfg.title_en, cfg.author, cfg.subtitle_vi)
            print(f"✓ Merged {len(merged_content):,} characters")

            if fmt == 'pdf':
                from utils.export_pdf import create_pdf
                from utils.markdown_converter import make_toc_links_clickable, markdown_to_html_with_dialogue

                print("Processing TOC links...")
                md_with_toc_links = make_toc_links_clickable(merged_content)
                print("✓ TOC links processed")

                print("Converting markdown to HTML...")
                html_content = markdown_to_html_with_dialogue(md_with_toc_links, include_cover=True, cover_path=cfg.cover_path)
                print(f"✓ Generated {len(html_content):,} characters of HTML")

                # Save HTML debug file
                debug_html_file = output_dir / f'document{output_suffix}_{timestamp}_debug.html'
                debug_html_file.write_text(html_content, encoding='utf-8')
                debug_size = debug_html_file.stat().st_size / (1024 * 1024)
                print(f"✓ Debug HTML saved: {debug_html_file.name} ({debug_size:.2f} MB)")

                print("Generating PDF with WeasyPrint...")
                proof_suffix = "_proof" if args.proof else ""
                output_file = output_dir / f'document{output_suffix}_{timestamp}{proof_suffix}.pdf'
                if args.proof:
                    pdf_created = create_pdf(md_with_toc_links, str(output_file), title, proof_mode=True, cover_path=cfg.cover_path, font=font)
                else:
                    pdf_created = create_pdf(md_with_toc_links, str(output_file), title=title, cover_path=cfg.cover_path, font=font)
                if pdf_created:
                    file_size = output_file.stat().st_size / (1024 * 1024)
                    print(f"✅ PDF exported: {output_file} ({file_size:.2f} MB)")
                    exported_files.append(output_file)
                    exported_files.append(debug_html_file)
                    success_count += 1
                else:
                    print(f"❌ PDF export failed")

            elif fmt == 'epub':
                from utils.markdown_converter import make_toc_links_clickable, markdown_to_html_with_dialogue
                from utils.export_epub import create_epub
                from ebooklib import epub as epub_lib

                print("Processing TOC links...")
                md_with_toc_links = make_toc_links_clickable(merged_content)
                print("✓ TOC links processed")

                print("Converting markdown to HTML...")
                html_content = markdown_to_html_with_dialogue(md_with_toc_links, include_cover=False, cover_path=cfg.cover_path)
                print(f"✓ Generated {len(html_content):,} characters of HTML")

                # Save HTML debug file
                debug_html_file = output_dir / f'document{output_suffix}_{timestamp}_epub_debug.html'
                debug_html_file.write_text(html_content, encoding='utf-8')
                debug_size = debug_html_file.stat().st_size / (1024 * 1024)
                print(f"✓ Debug HTML saved: {debug_html_file.name} ({debug_size:.2f} MB)")

                print("Creating EPUB structure with chapters...")
                book = create_epub(
                    html_content,
                    title=title,
                    author=author,
                    identifier=cfg.epub_identifier or f"{cfg.id}-vi",
                    cover_path=cfg.cover_path,
                    font=font,
                )
                chapter_count = len(book.toc) if book.toc else 0
                print(f"✓ Created {chapter_count} chapters")

                print("Writing EPUB file...")
                output_file = output_dir / f'document{output_suffix}_{timestamp}.epub'
                epub_lib.write_epub(str(output_file), book, {})
                file_size = output_file.stat().st_size / (1024 * 1024)
                print(f"✅ EPUB exported: {output_file} ({file_size:.2f} MB)")
                exported_files.append(output_file)
                exported_files.append(debug_html_file)
                success_count += 1

            elif fmt == 'html':
                from utils.markdown_converter import make_toc_links_clickable, markdown_to_html_with_dialogue
                from utils.export_html import create_html

                print("Processing TOC links...")
                md_with_toc_links = make_toc_links_clickable(merged_content)
                print("✓ TOC links processed")

                print("Converting markdown to HTML...")
                html_content = markdown_to_html_with_dialogue(md_with_toc_links, include_cover=True, cover_path=cfg.cover_path)
                print(f"✓ Generated {len(html_content):,} characters of HTML")

                print("Creating HTML document...")
                full_html = create_html(
                    html_content,
                    title=title,
                    cover_path=cfg.cover_path,
                    font=font,
                )

                print("Writing HTML file...")
                output_file = output_dir / f'document{output_suffix}_{timestamp}.html'
                output_file.write_text(full_html, encoding='utf-8')
                file_size = output_file.stat().st_size / (1024 * 1024)
                print(f"✅ HTML exported: {output_file} ({file_size:.2f} MB)")
                exported_files.append(output_file)
                success_count += 1

        except Exception as e:
            print(f"❌ Error exporting {fmt.upper()}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 EXPORT SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully exported: {success_count}/{len(formats_to_export)} formats")

    if success_count > 0:
        print(f"\n📁 Output directory: {output_dir}")
        print("\nGenerated files:")
        for f in exported_files:
            if f.exists() and f.is_file():
                size = f.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024*1024 else f"{size/1024/1024:.2f} MB"
                print(f"  • {f.name} ({size_str})")

    return 0 if success_count == len(formats_to_export) else 1


if __name__ == '__main__':
    sys.exit(main())
