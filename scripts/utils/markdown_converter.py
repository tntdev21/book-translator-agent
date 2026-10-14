#!/usr/bin/env python3
"""
Shared markdown to HTML conversion functions.

This module provides markdown processing functions used by all export formats:
- PDF export (export_pdf.py)
- EPUB export (export_epub.py)
- HTML export (export_html.py)
"""

import os
import re
import json
from html import escape
from pathlib import Path

# Shared mapping of special Vietnamese section titles to their anchor IDs
# These sections are converted to headings in markdown_to_html_with_dialogue()
SPECIAL_SECTIONS = {
    'Lời cống hiến': 'loi-cong-hien',
    'Đề từ': 'de-tu',
    'Lời nói đầu của tác giả': 'loi-noi-dau-cua-tac-gia',
    'Lời mở đầu': 'loi-mo-dau',
    'LỜI MỞ ĐẦU': 'loi-mo-dau',  # Uppercase variant
}


# Front-matter block (cover, title page, copyright, epigraph, dedication):
#   <!-- front id="anchor" -->  ...lines...  <!-- /front -->
# Lines inside render as centered paragraphs; the id is a TOC link target.
FRONT_OPEN_RE = re.compile(r'^<!--\s*front\s+id="([a-z0-9-]+)"(?:\s+class="([a-z0-9 -]+)")?\s*-->$')
# Quote attribution on its own line: <small>–NAME</small> [optional trailing text]
ATTRIBUTION_RE = re.compile(r'^<small>[-–—]\s*[^<]*</small>')
FRONT_CLOSE_RE = re.compile(r'^<!--\s*/front\s*-->$')


def load_toc_language_config():
    """Load TOC language configuration from JSON file."""
    config_path = Path(__file__).parent / 'toc_language_config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Flatten all TOC headers into a single list
            all_headers = []
            for lang_headers in config['toc_headers'].values():
                all_headers.extend(lang_headers)
            front_ids = config.get('front_sections', {}).get('ids', {})
            return {
                'toc_headers': all_headers,
                'chapter_patterns': config.get('chapter_patterns', {}).get('patterns', []),
                # normalized alias -> front block id, e.g. "ban-quyen" -> "copyright"
                'front_aliases': {text_to_anchor(alias): front_id
                                  for front_id, aliases in front_ids.items() for alias in aliases},
            }
    except Exception as e:
        # Fallback to basic headers if config file not found
        return {
            'toc_headers': ["mục lục", "table of contents", "contents"],
            'chapter_patterns': [r'^(Chapter|Chương|Chapitre)\s+\d+'],
            'front_aliases': {},
        }


def text_to_anchor(text: str) -> str:
    """Convert any text to a URL-safe anchor ID.

    Examples:
        "Lời cống hiến" -> "loi-cong-hien"
        "Chapter 1" -> "chapter-1"
        "Author's Note" -> "authors-note"
        "Đề từ" -> "de-tu"

    Args:
        text: The text to convert to an anchor

    Returns:
        URL-safe anchor ID
    """
    import unicodedata

    # Vietnamese character mapping (đ/Đ must be handled before normalize)
    vietnamese_map = {
        'đ': 'd', 'Đ': 'd',
    }
    for viet, latin in vietnamese_map.items():
        text = text.replace(viet, latin)

    # Remove accents/diacritics
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def scan_existing_headings(lines: list[str]) -> set[str]:
    """
    Pre-scan content to find all actual headings/sections.

    This is used to determine which TOC entries should be converted to links.

    Args:
        lines: List of content lines

    Returns:
        Set of anchor IDs for existing headings
    """
    existing_headings = set()

    for line in lines:
        stripped = line.strip()

        # Front-matter blocks: <!-- front id="anchor" -->
        front_match = FRONT_OPEN_RE.match(stripped)
        if front_match:
            existing_headings.add(front_match.group(1))
            continue

        # Check for special sections (shared with markdown_to_html_with_dialogue)
        if stripped in SPECIAL_SECTIONS:
            existing_headings.add(SPECIAL_SECTIONS[stripped])
            continue

        # Match markdown headings
        if stripped.startswith('#'):
            heading_text = re.sub(r'^#+\s*', '', stripped).strip()
            existing_headings.add(text_to_anchor(heading_text))
        # Match uppercase headings (chapter titles)
        elif stripped and (stripped.isupper() or stripped.startswith('CHƯƠNG')):
            # Extract chapter number from "CHƯƠNG 1" format
            chapter_match = re.match(r'^(Chương|Chapter|CHƯƠNG)\s+(\d+)', stripped, re.IGNORECASE)
            if chapter_match:
                chapter_num = chapter_match.group(2)
                existing_headings.add(f"chuong-{chapter_num}")
            else:
                existing_headings.add(text_to_anchor(stripped))

    return existing_headings


def is_toc_end(stripped: str, blank_line_count: int, in_toc: bool) -> bool:
    """
    Determine if we've reached the end of the TOC section.

    Args:
        stripped: Current line (stripped)
        blank_line_count: Number of consecutive blank lines
        in_toc: Whether we're currently in TOC section

    Returns:
        True if TOC has ended
    """
    if not in_toc:
        return False

    # Allow page markers within TOC - they don't end the TOC
    if '<!-- Page' in stripped or '<!- - - Page' in stripped:
        return False

    # A front-matter block (e.g. an epigraph page after the TOC) is not a TOC entry
    if FRONT_OPEN_RE.match(stripped):
        return True

    # End if we see 3+ consecutive blank lines (section break)
    if blank_line_count >= 3:
        return True

    # End if we hit a markdown heading (actual content start)
    if stripped.startswith('#'):
        return True

    # End if we detect actual chapter content (uppercase heading that's not a TOC entry)
    # This is detected when we find uppercase text that is very long (likely a chapter title, not TOC)
    if stripped and stripped.isupper() and len(stripped) > 50:
        return True

    # End TOC if we detect actual body text (paragraph starting with capital letter)
    # This happens after the TOC listing when real content begins
    # Exclude known TOC patterns: "Chương X", section titles like "Lời kết"
    if stripped and not stripped.startswith('Chương ') and not stripped.startswith('Chapter '):
        # Check if this looks like body text (longer than a title, or starts with specific phrases)
        if (len(stripped) > 30 and stripped[0].isupper()) or \
           stripped.startswith('Dành tặng cho') or \
           stripped.startswith('Ngày khoa học'):
            return True

    return False


def convert_toc_entry_to_link(stripped: str, existing_headings: set[str],
                              chapter_numbers: dict[str, str] | None = None) -> str | None:
    """
    Convert a TOC entry to a markdown link if it has a corresponding heading.

    Args:
        stripped: TOC entry text (stripped)
        existing_headings: Set of existing heading anchors
        chapter_numbers: Optional chapter number -> anchor map; an "N. ..." entry
            links to chapter N even when its wording differs from the heading

    Returns:
        Markdown link string if conversion successful, None if should skip/keep as-is
    """
    # Skip blank lines and very short lines (likely page numbers or artifacts)
    if not stripped or len(stripped) < 2:
        return None

    # Skip lines that are just numbers (page numbers in TOC)
    if stripped.isdigit():
        return None

    # Skip lines with roman numerals only (page numbers)
    if re.match(r'^[ivxlcdm]+$', stripped, re.IGNORECASE):
        return None

    # Match "Chương X" or "Chapter X" patterns
    chapter_match = re.match(r'^(Chương|Chapter|Chapitre|Capítulo|Capitolo)\s+(\d+)', stripped, re.IGNORECASE)
    if chapter_match:
        chapter_num = chapter_match.group(2)
        anchor = f"chuong-{chapter_num}"
        # Only create link if this chapter exists in the content
        if anchor in existing_headings:
            return f'[{stripped}](#{anchor})'
        return None  # Keep as plain text if chapter doesn't exist

    number_match = re.match(r'^(\d+)\.\s', stripped)
    if chapter_numbers and number_match and number_match.group(1) in chapter_numbers:
        return f'[{stripped}](#{chapter_numbers[number_match.group(1)]})'

    # For any other text (pre-chapter sections like Dedication, Prologue, etc.)
    # Auto-generate anchor from the text itself
    anchor = text_to_anchor(stripped)
    # Only create link if this section exists in the content
    if anchor in existing_headings:
        return f'[{stripped}](#{anchor})'

    # If entry starts with a number (e.g., "12. Epilogue..."), try matching
    # without the number prefix - headings may not include it
    number_prefix_match = re.match(r'^\d+\.\s+(.*)', stripped)
    if number_prefix_match:
        text_without_number = number_prefix_match.group(1)
        anchor_without_number = text_to_anchor(text_without_number)
        if anchor_without_number in existing_headings:
            return f'[{stripped}](#{anchor_without_number})'

    return None  # Keep as plain text if section doesn't exist


def scan_chapter_headings(lines: list[str]) -> tuple[set[str], dict[str, str]]:
    """Top-level (``# ``) heading anchors, plus chapter number -> anchor.

    A TOC lists chapters, so it should link to ``# `` headings, not to a
    same-named ``## `` subheading elsewhere (e.g. the per-chapter groups inside
    a Notes chapter). Numbered chapters ("# 3. Title") are also indexed by
    number so a TOC entry still links when its wording drifts from the heading.
    Front-matter blocks and special sections count as top level.
    """
    top_level: set[str] = set()
    by_number: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        front_match = FRONT_OPEN_RE.match(stripped)
        if front_match:
            top_level.add(front_match.group(1))
        elif stripped in SPECIAL_SECTIONS:
            top_level.add(SPECIAL_SECTIONS[stripped])
        elif stripped.startswith('# '):
            heading_text = stripped[2:].strip()
            anchor = SPECIAL_SECTIONS.get(heading_text) or text_to_anchor(heading_text)
            top_level.add(anchor)
            num_match = re.match(r'^(\d+)\.\s', heading_text)
            if num_match:
                by_number.setdefault(num_match.group(1), anchor)
    return top_level, by_number


def make_toc_links_clickable(content: str, report: list | None = None) -> str:
    """
    Convert TOC entries to clickable links.

    This function detects TOC sections and converts all entries
    (chapters and pre-chapter sections) to clickable links.

    Process:
    1. Scan content to find all existing headings
    2. Detect TOC section automatically
    3. Convert TOC entries to links with auto-generated anchors
    4. Detect TOC end using blank lines or first actual chapter
    5. Only create links for entries that have corresponding headings in content

    Args:
        content: Markdown content
        report: Optional list; receives one ``(entry_text, anchor or None)`` per
            TOC entry, for validation (see ``validate_toc.check_toc_links``)

    Returns:
        Content with clickable TOC links
    """
    lines = content.split('\n')
    result = []
    in_toc = False
    blank_line_count = 0

    # Load language configuration
    lang_config = load_toc_language_config()
    toc_headers = [h.lower() for h in lang_config['toc_headers']]
    front_aliases = lang_config.get('front_aliases', {})

    # Pre-scan headings. Prefer top-level (# ) anchors so an entry never links
    # to a same-named subheading; fall back to all headings when a book has none.
    top_level, chapter_numbers = scan_chapter_headings(lines)
    existing_headings = top_level or scan_existing_headings(lines)

    for line in lines:
        stripped = line.strip()

        # Detect TOC start — strip markdown heading prefix (# / ##) so
        # "Contents", "# Contents", "# Mục lục" all match.
        heading_match = re.match(r'^#+\s+(.*)', stripped)
        heading_body = (heading_match.group(1) if heading_match else stripped)
        if heading_body.lower() in toc_headers:
            in_toc = True
            result.append(line)
            blank_line_count = 0
            continue

        # Check if TOC has ended
        if is_toc_end(stripped, blank_line_count, in_toc):
            in_toc = False

        # Count consecutive blank lines to detect TOC end
        if not stripped:
            blank_line_count += 1
        else:
            blank_line_count = 0

        # Convert TOC entries to links when inside TOC
        if in_toc and stripped:
            # Strip <small> tags for matching, but preserve them in output
            entry_text = stripped
            has_small_tags = stripped.startswith('<small>') and stripped.endswith('</small>')
            if has_small_tags:
                entry_text = stripped[7:-8]  # Remove <small> and </small>

            # Front-matter entries ("Bản quyền", "*Copyright*") link to the
            # language-neutral block id the source carries (<!-- front id="copyright" -->)
            front_id = front_aliases.get(text_to_anchor(entry_text))
            if front_id in existing_headings:
                linked = f'[{entry_text}](#{front_id})'
            else:
                linked = convert_toc_entry_to_link(entry_text, existing_headings, chapter_numbers)
            if report is not None:
                anchor_match = re.search(r'\]\(#([^)]+)\)$', linked or '')
                report.append((entry_text, anchor_match.group(1) if anchor_match else None))
            if linked:
                # If it had <small> tags, wrap the link back in them
                if has_small_tags:
                    # Extract the link from the markdown format [text](#anchor)
                    link_match = re.match(r'\[(.*?)\]\((#.*?)\)', linked)
                    if link_match:
                        result.append(f'<small>[{link_match.group(1)}]({link_match.group(2)})</small>')
                    else:
                        result.append(line)
                else:
                    result.append(linked)
            else:
                result.append(line)
            continue

        result.append(line)

    return '\n'.join(result)


TITLE_PAGE_EMPTY_RE = re.compile(
    r'^(<!--\s*front\s+id="title-page"[^>]*-->)\s*\n\s*(<!--\s*/front\s*-->)', re.MULTILINE)


def fill_title_page(md_content: str, title: str, author: str = "", subtitle: str = "") -> str:
    """Fill an empty ``<!-- front id="title-page" -->`` block from book metadata.

    Source title pages are usually images, so the block stays empty in the chunks
    and is generated at export from ``book.yaml`` (title_vi, subtitle_vi, author).
    A block that already has content is left alone.
    """
    lines = [f'<p class="front-title">{escape(title)}</p>'] if title else []
    if subtitle:
        lines.append(f'<p class="front-sub">{escape(subtitle)}</p>')
    if author:
        lines.append(f'<p class="front-author">{escape(author)}</p>')
    if not lines:
        return md_content
    body = '\n'.join(lines)
    return TITLE_PAGE_EMPTY_RE.sub(lambda m: f'{m.group(1)}\n{body}\n{m.group(2)}', md_content, count=1)


def markdown_to_html_with_dialogue(md_content, include_cover=False, cover_path=None):
    """Convert markdown to HTML preserving dialogue line breaks.

    ``cover_path`` is the cover image to embed when ``include_cover`` is set.
    Without it the cover is looked up at ./cover.jpg for backwards
    compatibility with the pre-multi-book layout.
    """
    # Markers are internal references. Remove only their own line: blank lines
    # encode paragraph boundaries, while no blank line encodes a continuation
    # across a printed-page break.
    md_content = re.sub(r'^[ \t]*<!--\s*Page\s*\d+\s*-->[ \t]*\n?', '', md_content, flags=re.MULTILINE)
    # Then strip any remaining inline markers from legacy sources.
    md_content = re.sub(r'<!--\s*Page\s*\d+\s*-->', '', md_content)

    lines = md_content.split('\n')
    html_parts = []
    i = 0

    # Add cover page if requested
    if include_cover:
        cover = Path(cover_path) if cover_path else Path('cover.jpg')
        if cover.exists():
            html_parts.append(f'<div class="cover-page">')
            html_parts.append(f'<img src="file://{cover.resolve()}" alt="Cover" class="cover-image"/>')
            html_parts.append('</div>')

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle clickable TOC links (HTML format)
        if stripped.startswith('<a href="#'):
            html_parts.append(f'<p class="toc-entry">{stripped}</p>')
            i += 1
            continue

        # Handle clickable TOC links (Markdown format: [text](#anchor))
        md_link_match = re.match(r'^\[(.*?)\]\((#.*?)\)$', stripped)
        if md_link_match:
            link_text = md_link_match.group(1)
            link_anchor = md_link_match.group(2)
            html_link = f'<a href="{link_anchor}" class="toc-link">{link_text}</a>'
            html_parts.append(f'<p class="toc-entry">{html_link}</p>')
            i += 1
            continue

        # Handle TOC links wrapped in <small> tags: <small>[text](#anchor)</small>
        small_link_match = re.match(r'^<small>\[(.*?)\]\((#.*?)\)</small>$', stripped)
        if small_link_match:
            link_text = small_link_match.group(1)
            link_anchor = small_link_match.group(2)
            html_link = f'<a href="{link_anchor}" class="toc-link">{link_text}</a>'
            html_parts.append(f'<p class="toc-entry"><small>{html_link}</small></p>')
            i += 1
            continue

        # Structured footnotes are reflowable citations, not display lines.
        if stripped.startswith('<aside class="footnote">') and stripped.endswith('</aside>'):
            note = stripped.removeprefix('<aside class="footnote">').removesuffix('</aside>')
            # Extract leading footnote number for anchor target (e.g., "5. text..." -> "5")
            fn_match = re.match(r'^(\d+)\.', note)
            if fn_match:
                num = fn_match.group(1)
                note_content = note[fn_match.end():]
                # Wrap number as back-link to the reference in body text
                note_id_attr = f' id="fn-{num}"'
                note_html = f'<aside class="footnote"{note_id_attr}><p><a href="#fn-ref-{num}" class="footnote-back">{num}</a>.{note_content}</p></aside>'
            else:
                note_id_attr = ''
                note_html = f'<aside class="footnote"{note_id_attr}><p>{note}</p></aside>'
            html_parts.append(note_html)
            i += 1
            continue

        # Front-matter block: centered, anchored, own page
        front_match = FRONT_OPEN_RE.match(stripped)
        if front_match:
            extra = f' {front_match.group(2)}' if front_match.group(2) else ''
            html_parts.append(f'<div id="{front_match.group(1)}" class="front-matter{extra}">')
            open_idx = len(html_parts) - 1
            i += 1
            while i < len(lines) and not FRONT_CLOSE_RE.match(lines[i].strip()):
                inner = lines[i].strip()
                if inner:
                    if ATTRIBUTION_RE.match(inner):
                        html_parts.append(f'<p class="quote-attribution">{inner}</p>')
                    else:
                        html_parts.append(inner if inner.startswith('<p') else f'<p>{inner}</p>')
                i += 1
            html_parts.append('</div>')
            if len(html_parts) - open_idx == 2:
                # Empty anchor-only block: keep it truly empty so CSS :empty applies
                html_parts[open_idx:] = [html_parts[open_idx] + '</div>']
            i += 1
            continue

        # Quote attribution (right-aligned); text glued after it is its own paragraph
        attr_match = ATTRIBUTION_RE.match(stripped)
        if attr_match:
            html_parts.append(f'<p class="quote-attribution">{attr_match.group(0)}</p>')
            rest = stripped[attr_match.end():].strip()
            if rest:
                lines[i] = rest
            else:
                i += 1
            continue

        # Page markers (both <!-- --> and <!- - - ->)
        if (stripped.startswith('<!--') and stripped.endswith('-->')) or \
           (stripped.startswith('<!-') and stripped.endswith('->')):
            # Remove comment markers and extract page text
            if stripped.startswith('<!--'):
                page_text = stripped[4:-3].strip()
            else:
                page_text = stripped[3:-2].strip()
            # Skip rendering page markers entirely (they're for reference only)
            i += 1
            continue

        # Copyright page - starts with "Bản quyền ©" or year
        if stripped.startswith('Bản quyền ©') or (stripped.isdigit() and len(stripped) == 4):
            # Check if this is a year followed by copyright
            if stripped.isdigit():
                html_parts.append('<div class="copyright-page">')
                html_parts.append(f'<p class="copyright-year">{stripped}</p>')
                i += 1
                # Next line should be "Bản quyền ©..."
                if i < len(lines) and lines[i].strip().startswith('Bản quyền ©'):
                    html_parts.append(f'<p class="copyright-text">{lines[i].strip()}</p>')
                    i += 1
                html_parts.append('</div>')
            else:
                # Direct copyright text
                html_parts.append('<div class="copyright-page">')
                html_parts.append(f'<p class="copyright-text">{stripped}</p>')
                i += 1
                html_parts.append('</div>')
            continue

        # Publisher info - starts with "Penguin Random House"
        if stripped.startswith('Penguin Random House'):
            html_parts.append('<div class="publisher-page">')
            # Collect all publisher-related paragraphs
            while i < len(lines):
                curr_line = lines[i].strip()
                if not curr_line or curr_line.startswith('<!--'):
                    break
                if curr_line.startswith('Penguin') or curr_line.startswith('Xuất bản') or \
                   curr_line.startswith('Doubleday') or curr_line.startswith('Đại diện') or \
                   'bản quyền' in curr_line.lower():
                    html_parts.append(f'<p class="publisher-text">{curr_line}</p>')
                    i += 1
                else:
                    break
            html_parts.append('</div>')
            continue

        # TOC title
        if stripped == 'Mục lục':
            html_parts.append('<h1 class="toc-title">MỤC LỤC</h1>')
            i += 1
            continue

        # Markdown section headings emitted by the structured PDF extractor.
        if stripped.startswith('## '):
            heading_text = stripped[3:].strip()
            anchor_id = text_to_anchor(heading_text)
            html_parts.append(f'<div id="{anchor_id}" class="section-heading">')
            html_parts.append(f'<h2>{heading_text}</h2>')
            html_parts.append('</div>')
            i += 1
            continue

        # Markdown headings (# Heading) - check if they match special sections
        if stripped.startswith('# '):
            heading_text = stripped[2:].strip()

            # Check if this is a special section
            if heading_text in SPECIAL_SECTIONS:
                anchor_id = SPECIAL_SECTIONS[heading_text]
                html_parts.append(f'<div id="{anchor_id}" class="chapter-heading">')
                html_parts.append(f'<h1>{heading_text}</h1>')
                html_parts.append('</div>')
                i += 1
                continue

            # Otherwise generate anchor from text
            anchor_id = text_to_anchor(heading_text)
            html_parts.append(f'<div id="{anchor_id}" class="chapter-heading">')
            html_parts.append(f'<h1>{heading_text}</h1>')
            html_parts.append('</div>')
            i += 1
            continue

        # Special section headings (Dedication, Epigraph, Author's Note, etc.)
        # Use shared SPECIAL_SECTIONS mapping (for plain text without # prefix)
        if stripped in SPECIAL_SECTIONS:
            anchor_id = SPECIAL_SECTIONS[stripped]
            html_parts.append(f'<div id="{anchor_id}" class="chapter-heading">')
            html_parts.append(f'<h1>{stripped}</h1>')
            html_parts.append('</div>')
            i += 1
            continue

        # Dedication content - starts with "Dành tặng cho"
        if stripped.startswith('Dành tặng cho'):
            # Process the dedication text as regular paragraph
            para_lines = [line.strip()]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if (not next_line or next_line.startswith('<!--')):
                    break
                para_lines.append(next_line)
                i += 1
            para_text = ' '.join(para_lines)
            html_parts.append(f'<p class="dedication">{para_text}</p>')
            continue

        # Epigraph content - quote starting with "Ngày khoa học"
        if stripped.startswith('Ngày khoa học'):
            # Process the quote
            html_parts.append(f'<p class="epigraph">{stripped}</p>')
            i += 1
            # Next line might be the attribution (-)
            if i < len(lines) and lines[i].strip() == '-':
                html_parts.append(f'<p class="epigraph-attribution">—</p>')
                i += 1
            continue

        # Author's Note section subtitle - "SỰ THẬT"
        if stripped == 'SỰ THẬT':
            html_parts.append(f'<h2 class="section-subtitle">{stripped}</h2>')
            i += 1
            continue

        # Special sections - format like chapters with anchors
        special_sections = {
            'LỜI MỞ ĐẦU': 'loi-mo-au'
        }

        if stripped in special_sections:
            anchor = special_sections[stripped]
            html_parts.append(f'<div id="{anchor}" class="chapter-heading">')
            html_parts.append(f'<h1>{stripped}</h1>')
            html_parts.append('</div>')
            i += 1
            continue

        # General section headings (UPPERCASE, not chapters)
        # Only match known section types, not story content in uppercase
        # This catches: PROLOGUE, DEDICATION, EPILOGUE, etc. in any language
        if stripped and stripped.isupper() and len(stripped) > 3:
            # Not a chapter, but a section heading
            if not re.match(r'^(CHƯƠNG|CHAPTER|CHAPITRE)\s+\d+', stripped, re.IGNORECASE):
                # Only treat as heading if it matches known section patterns
                # Exclude: questions (?), numbered lists (1), 2)), special chars (#, &, /)
                # Exclude: story content like typed messages, labels, codes
                if '?' in stripped or '#' in stripped or '&' in stripped or '/' in stripped:
                    # This is story content, not a heading
                    pass
                elif re.match(r'^\d+\)', stripped):
                    # This is a numbered item, not a heading
                    pass
                elif len(stripped.split()) <= 4 and all(c.isalpha() or c.isspace() for c in stripped):
                    # Short uppercase text with only letters (likely section heading)
                    # Generate anchor from the text
                    import unicodedata
                    anchor_text = unicodedata.normalize('NFKD', stripped)
                    anchor_text = anchor_text.encode('ascii', 'ignore').decode('ascii')
                    anchor_text = re.sub(r'[^\w\s-]', '', anchor_text.lower())
                    anchor = re.sub(r'[-\s]+', '-', anchor_text).strip('-')

                    html_parts.append(f'<div id="{anchor}" class="chapter-heading">')
                    html_parts.append(f'<h1>{stripped}</h1>')
                    html_parts.append('</div>')
                    i += 1
                    continue

        # Chapter headings with anchors
        chapter_match = re.match(r'^(CHƯƠNG (\d+))$', stripped)
        if chapter_match:
            chapter_title = chapter_match.group(1)
            chapter_num = chapter_match.group(2)
            anchor = f"chuong-{chapter_num}"
            html_parts.append(f'<div id="{anchor}" class="chapter-heading">')
            html_parts.append(f'<h1>{chapter_title}</h1>')
            html_parts.append('</div>')
            i += 1
            continue

        # Dialogue detection
        if stripped.startswith('- '):
            dialogue_lines = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                dialogue_lines.append(lines[i].strip())
                i += 1

            html_parts.append('<div class="dialogue">')
            for d_line in dialogue_lines:
                html_parts.append(f'  <p class="dialogue-line">{d_line}</p>')
            html_parts.append('</div>')
            continue

        # Empty lines
        if not stripped:
            i += 1
            continue

        # Regular paragraphs
        if stripped:
            # Check if this is a short line (book titles, lists, etc.)
            is_short_line = (
                len(stripped) < 80
                and not stripped.endswith(('.', '!', '?', '…'))
                and (i + 1 == len(lines) or not lines[i + 1].strip())
            )

            if is_short_line:
                # Preserve line break
                html_parts.append(f'<p class="preserve-break">{stripped}</p>')
                i += 1
            else:
                # Regular paragraph - merge lines
                para_lines = [line.strip()]
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if (not next_line or
                        next_line.startswith('#') or
                        next_line.startswith('- ') or
                        next_line.startswith('<!--') or
                        next_line.startswith('<a href=') or
                        next_line.startswith('CHƯƠNG') or
                        next_line == 'LỜI MỞ ĐẦU' or
                        next_line == 'SỰ THẬT' or
                        next_line.startswith('Dành tặng cho') or
                        next_line.startswith('Ngày khoa học') or
                        next_line == '---'):
                        break
                    para_lines.append(next_line)
                    i += 1

                para_text = ' '.join(para_lines)
                html_parts.append(f'<p>{para_text}</p>')
        else:
            i += 1

    # Phase 2: Convert <small>N</small> footnote references to clickable links
    # Only matches small tags containing 1-3 digits (footnote numbers)
    # Safe: won't affect <small>Notes</small>, ISBNs, or <small>[text](#anchor)</small>
    # Footnote numbers restart every chapter, so ids/hrefs are scoped per chapter
    # (fn-<chapter>-<n>); otherwise every link jumps to the first chapter's note.
    result = '\n'.join(html_parts)
    # Inline emphasis: *text* -> <em>text</em> (titles, foreign words)
    result = re.sub(r'(?<![\w*])\*(?=\S)([^*\n<>]+?)(?<=\S)\*(?![\w*])', r'<em>\1</em>', result)
    segments = result.split('class="chapter-heading">')
    for chapter_no, segment in enumerate(segments):
        segment = re.sub(
            r'<small>(\d{1,3})</small>',
            rf'<a id="fn-ref-{chapter_no}-\1" href="#fn-{chapter_no}-\1" class="footnote-ref"><sup>\1</sup></a>',
            segment
        )
        segment = re.sub(r'id="fn-(\d+)"', rf'id="fn-{chapter_no}-\1"', segment)
        segment = re.sub(r'href="#fn-ref-(\d+)"', rf'href="#fn-ref-{chapter_no}-\1"', segment)
        segments[chapter_no] = segment
    result = 'class="chapter-heading">'.join(segments)
    return dedupe_ids(result)


def dedupe_ids(html: str) -> str:
    """Suffix repeated ``id="x"`` as ``x-2``, ``x-3``... (first keeps the bare id).

    Duplicate ids are invalid HTML; links resolve to the first, but the EPUB
    anchor map keeps the last, sending TOC links into e.g. the Notes chapter.
    """
    seen: dict[str, int] = {}

    def renumber(match):
        anchor = match.group(1)
        seen[anchor] = seen.get(anchor, 0) + 1
        return match.group(0) if seen[anchor] == 1 else f'id="{anchor}-{seen[anchor]}"'

    return re.sub(r'\bid="([^"]+)"', renumber, html)
