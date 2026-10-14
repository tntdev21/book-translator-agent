#!/usr/bin/env python3
"""
Universal extractor - auto-detects PDF, DOCX, EPUB, or TXT and extracts to Markdown.
Automatically fixes sentence breaks after extraction.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.book_config import bootstrap_argv  # noqa: E402


def main():
    argv, cfg = bootstrap_argv()
    if len(argv) < 2:
        print("Usage: python extract.py <input_file> [output.md] [max_pages] [--book <id>]")
        print("Supports: .pdf, .docx, .epub, .txt")
        print("")
        print("Examples:")
        print("  python extract.py input/source.pdf")
        print("  python extract.py input/source.docx source/full_text.md")
        print("  python extract.py input/sample.pdf source/sample.md 30")
        sys.exit(1)
    
    input_file = argv[1]

    if not os.path.exists(input_file):
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)

    # Detect file type
    ext = os.path.splitext(input_file)[1].lower()

    if ext == '.pdf':
        print("📄 Detected: PDF")
        from utils.extract_pdf import extract_pdf
        from utils.fix_sentence_breaks import fix_sentence_breaks
        from utils.normalize_dashes import normalize_dashes_file
        output_file = argv[2] if len(argv) > 2 else str(cfg.source_file)
        max_pages = int(argv[3]) if len(argv) > 3 else None

        # Extract PDF
        extract_pdf(input_file, output_file, max_pages)

        # Post-process: Fix formatting issues
        print("\n🔧 Post-processing: Running fixes...")
        print("  📝 Fixing sentence breaks...")
        fixes = fix_sentence_breaks(output_file, backup=True)
        if fixes > 0:
            print(f"    ✓ Fixed {fixes} breaks")

        print("  ➖ Normalizing dashes...")
        dash_changes = normalize_dashes_file(output_file)
        if dash_changes > 0:
            print(f"    ✓ Normalized {dash_changes} dashes")

        total = fixes + dash_changes
        if total > 0:
            print(f"✅ Applied {total} fixes total")
        else:
            print("✅ No fixes needed")

    elif ext == '.docx':
        print("📄 Detected: DOCX")
        from utils.extract_docx import extract_docx, extract_docx_by_pages
        from utils.fix_sentence_breaks import fix_sentence_breaks
        from utils.normalize_dashes import normalize_dashes_file
        output_file = argv[2] if len(argv) > 2 else str(cfg.source_file)
        max_pages = int(argv[3]) if len(argv) > 3 else None

        # Extract DOCX
        if max_pages:
            extract_docx_by_pages(input_file, output_file, max_pages)
        else:
            extract_docx(input_file, output_file)

        # Post-process: Fix formatting issues
        print("\n🔧 Post-processing: Running fixes...")
        print("  📝 Fixing sentence breaks...")
        fixes = fix_sentence_breaks(output_file, backup=True)
        if fixes > 0:
            print(f"    ✓ Fixed {fixes} breaks")

        print("  ➖ Normalizing dashes...")
        dash_changes = normalize_dashes_file(output_file)
        if dash_changes > 0:
            print(f"    ✓ Normalized {dash_changes} dashes")

        total = fixes + dash_changes
        if total > 0:
            print(f"✅ Applied {total} fixes total")
        else:
            print("✅ No fixes needed")
    
    elif ext == '.epub':
        print("📄 Detected: EPUB")
        from utils.extract_epub import extract_epub
        from utils.fix_sentence_breaks import fix_sentence_breaks
        from utils.normalize_dashes import normalize_dashes_file
        output_file = argv[2] if len(argv) > 2 else str(cfg.source_file)
        max_pages = int(argv[3]) if len(argv) > 3 else None

        extract_epub(input_file, output_file, max_pages)

        # Post-process: same formatting pass as the other extractors.
        print("\n🔧 Post-processing: Running fixes...")
        print("  📝 Fixing sentence breaks...")
        fixes = fix_sentence_breaks(output_file, backup=True)
        if fixes > 0:
            print(f"    ✓ Fixed {fixes} breaks")

        print("  ➖ Normalizing dashes...")
        dash_changes = normalize_dashes_file(output_file)
        if dash_changes > 0:
            print(f"    ✓ Normalized {dash_changes} dashes")

        total = fixes + dash_changes
        if total > 0:
            print(f"✅ Applied {total} fixes total")
        else:
            print("✅ No fixes needed")

    elif ext == '.doc':
        print("❌ .doc format not directly supported.")
        print("💡 Tip: Convert to .docx first using LibreOffice:")
        print(f"   libreoffice --headless --convert-to docx {input_file}")
        sys.exit(1)
    
    elif ext == '.txt':
        print("📄 Detected: TXT (plain text)")
        output_file = argv[2] if len(argv) > 2 else str(cfg.source_file)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Copied to {output_file}")
    
    else:
        print(f"❌ Unsupported format: {ext}")
        print("Supported: .pdf, .docx, .epub, .txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
