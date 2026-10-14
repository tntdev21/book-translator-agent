#!/usr/bin/env python3
"""
Integration tests: HTML to PDF/EPUB conversion workflow.
Tests the interaction between HTML generation and export to PDF/EPUB formats.
"""

import pytest
from pathlib import Path

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not installed")
def test_html_to_pdf(tmp_path: Path) -> None:
    """Test HTML to PDF conversion using WeasyPrint."""
    from weasyprint import HTML
    
    html_content = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Test</title></head>
<body>
<h1>Chapter 1</h1>
<p>Test paragraph.</p>
</body>
</html>"""
    
    html_file = tmp_path / "test.html"
    html_file.write_text(html_content, encoding='utf-8')
    
    pdf_file = tmp_path / "test.pdf"
    HTML(filename=str(html_file)).write_pdf(str(pdf_file))
    
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0
    pdf_bytes = pdf_file.read_bytes()
    assert pdf_bytes.startswith(b'%PDF')


@pytest.mark.skipif(not EBOOKLIB_AVAILABLE, reason="ebooklib not installed")
def test_html_to_epub(tmp_path: Path) -> None:
    """Test HTML to EPUB conversion using ebooklib."""
    from ebooklib import epub
    
    book = epub.EpubBook()
    book.set_identifier('test123')
    book.set_title('Test Book')
    book.set_language('en')
    book.add_author('Test Author')
    
    chapter1 = epub.EpubHtml(title='Chapter 1', file_name='chap_01.xhtml', lang='en')
    chapter1.content = '<h1>Chapter 1</h1><p>Content here.</p>'
    
    book.add_item(chapter1)
    book.toc = (epub.Link('chap_01.xhtml', 'Chapter 1', 'chap1'),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', chapter1]
    
    epub_file = tmp_path / "test.epub"
    epub.write_epub(str(epub_file), book)
    
    assert epub_file.exists()
    assert epub_file.stat().st_size > 0
    epub_bytes = epub_file.read_bytes()
    assert epub_bytes.startswith(b'PK')


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="WeasyPrint not installed")
def test_pdf_metadata(tmp_path: Path) -> None:
    """Test PDF metadata embedding."""
    from weasyprint import HTML
    
    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="author" content="Test Author">
<title>Test Document Title</title>
</head>
<body><h1>Test Content</h1></body>
</html>"""
    
    html_file = tmp_path / "test.html"
    html_file.write_text(html_content, encoding='utf-8')
    
    pdf_file = tmp_path / "test.pdf"
    HTML(filename=str(html_file)).write_pdf(str(pdf_file))
    
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0
    pdf_bytes = pdf_file.read_bytes()
    assert b'%PDF' in pdf_bytes


@pytest.mark.skipif(not EBOOKLIB_AVAILABLE, reason="ebooklib not installed")
def test_epub_toc_structure(tmp_path: Path) -> None:
    """Test EPUB TOC structure validation."""
    from ebooklib import epub
    
    book = epub.EpubBook()
    book.set_identifier('toc_test')
    book.set_title('TOC Structure Test')
    book.set_language('vi')
    
    intro = epub.EpubHtml(title='Intro', file_name='intro.xhtml', lang='vi')
    intro.content = '<h1>Intro</h1><p>Content.</p>'
    
    ch1 = epub.EpubHtml(title='Chapter 1', file_name='ch1.xhtml', lang='vi')
    ch1.content = '<h1>Chapter 1</h1><p>Content.</p>'
    
    book.add_item(intro)
    book.add_item(ch1)
    
    book.toc = (
        epub.Link('intro.xhtml', 'Intro', 'intro'),
        epub.Link('ch1.xhtml', 'Chapter 1', 'ch1')
    )
    
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', intro, ch1]
    
    epub_file = tmp_path / "toc_test.epub"
    epub.write_epub(str(epub_file), book)
    
    assert epub_file.exists()
    assert epub_file.stat().st_size > 0
    
    read_book = epub.read_epub(str(epub_file))
    assert read_book.get_metadata('DC', 'title')[0][0] == 'TOC Structure Test'
    assert len(read_book.toc) > 0
