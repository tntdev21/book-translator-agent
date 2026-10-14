# Formatting Rules for Translations

This document defines the formatting standards for Vietnamese translations to ensure consistency across all chunks.

## Version
Last updated: 2025-01-28

---

## 1. Punctuation

### Dashes
- **Prose rule**: Use spaced ASCII hyphen ` - ` instead of em-dash `—` for parenthetical interruptions.
- **Dialogue rule**: A dialogue line starts with leading `- `, not ` - `.
- **Range rule**: Keep an unspaced en-dash in numeric ranges: `10–20`, `10–20%`.
- **Compound rule**: Preserve lexical hyphens: `self-aware`.
- **Rationale**: Simpler, consistent across devices, and unambiguous by context.
- **Examples**:
  - ✅ Prose: `Anh nhìn cô - đôi mắt đầy lo lắng`
  - ✅ Dialogue: `- Tôi hiểu rồi.`
  - ✅ Range: `10–20%`
  - ❌ Wrong: `Anh nhìn cô — đôi mắt đầy lo lắng` (em-dash)
  - ❌ Wrong: `xung quanh-hay là` (unspaced prose interruption)
  - ❌ Wrong: `10 - 20%` (looks like subtraction)

### Quotation Marks
- Use standard double quotes `"` for dialogue and quotations
- DON'T use Vietnamese guillemets `« »`

### Ellipsis
- Use three periods `...` for trailing off
- Use `…` (single character) sparingly, prefer `...`

---

## 2. Chapter Headings

### Format
- **Rule**: `CHƯƠNG X` (Vietnamese first, then number)
- **Examples**:
  - ✅ Correct: `CHƯƠNG 1`, `CHƯƠNG 23`, `CHƯƠNG 130`
  - ❌ Wrong: `1\nCHƯƠNG`, `Chapter 1`, `Chương 1`

### Placement
- Chapter headings should be on a single line
- Blank line before and after chapter heading
- No decorative characters or formatting

---

## 3. Dialogue Formatting

### Line Breaks
- **Rule**: Each dialogue line starts with `- ` and is on its own line
- **Important**: Do NOT merge multiple dialogue lines into one paragraph
- **Example**:

✅ Correct:
```
- Anh đi đâu? - Cô hỏi.
- Tôi phải đi. - Anh đáp.
- Ở lại với em. - Cô nói.
```

❌ Wrong:
```
- Anh đi đâu? - Cô hỏi. - Tôi phải đi. - Anh đáp. - Ở lại với em. - Cô nói.
```

### Mixed Dialogue and Narrative
- When dialogue is embedded in narrative, keep it on the same line:
  ```
  Anh vươn tay ra. - Đừng lo. - Anh nói.
  ```

### Isolated Single-Line Dialogue (CRITICAL)
**Rule**: Single dialogue lines MUST NOT appear isolated without context

⚠️ **Problem**: Isolated dialogue can be misinterpreted as headings by markdown converter

❌ **Wrong** - Isolated dialogue (will become heading):
```markdown
Đôi mắt của cậu ta mở to một chút.
- Ồ...
Faukman cảm thấy một chút lo lắng.
```

✅ **Solution 1** - Add speaker attribution:
```markdown
Đôi mắt của cậu ta mở to một chút.

- Ồ... - Anh kỹ thuật viên nói.

Faukman cảm thấy một chút lo lắng.
```

✅ **Solution 2** - Group with adjacent dialogue:
```markdown
Đôi mắt của cậu ta mở to một chút.
- Ồ...
- Có vấn đề gì vậy?
```

✅ **Solution 3** - Use blank lines for proper paragraph detection:
```markdown
Đôi mắt của cậu ta mở to một chút.

- Ồ...

Faukman cảm thấy một chút lo lắng.
```

**Validation**: Run `python scripts/utils/validate_dialogue.py translated/` to detect isolated dialogue

---

## 4. Paragraph Structure

### Indentation
- No manual indentation in markdown (handled by CSS/export)
- Blank line between paragraphs

### Line Length
- No hard line wrapping
- Each paragraph is a single long line in markdown
- Line breaks only for actual paragraph breaks or dialogue

### Preserve Line Breaks
**IMPORTANT**: Some content requires preserved line breaks in the .md file:

✅ **Preserve breaks for**:
- Book title lists (e.g. an author's other works, listed one per line)
- Author information
- Short lines without sentence-ending punctuation
- Lists of items (chapters, names, etc.)
- Short credits or attributions

**Example** (front matter):
```markdown
Các tác phẩm khác của cùng tác giả
Tên sách thứ nhất
Tên sách thứ hai
Tên sách thứ ba
```
Each line should remain separate (not merged into one paragraph)

❌ **Don't preserve breaks for**:
- Long paragraphs that continue across lines
- Regular narrative text
- Sentences that end with period/question mark/exclamation

**Technical implementation**:
- Lines < 80 characters without `.!?…` at end → preserve as separate
- Lines that end with sentence punctuation → can merge continuation
- Export scripts use `.preserve-break` CSS class for short lines

---

## 5. Special Elements

### Page Markers
- Keep as HTML comments: `<!-- Page X -->`
- Preserve for reference during QA
- Will be styled appropriately in final export

### Front-Matter Blocks
- `<!-- front id="..." [class="..."] -->` … `<!-- /front -->` wrap title page, copyright,
  epigraph, dedication. They live in the **source** chunk; copy both lines verbatim, translate
  only the text between. They are TOC link targets: a dropped marker = broken TOC
  (`validate-translation.py` errors).

### Small Caps (`<span class="sc">`)
- Inline small caps from the source (speaker labels `JUDGE`, signs `LET AGREED`, `B.C.`)
  are `<span class="sc">TEXT</span>` inside the sentence. Copy the span verbatim, text in
  English, never translate or move it out of its paragraph (`validate-translation.py` errors).
- `<small>` is NOT small caps: it means a footnote marker `<small>N</small>` or a whole
  display block (attribution, caption). Never wrap inline words in `<small>`.

### Emphasis
- **Bold**: Use `**text**` sparingly for emphasis
- _Italic_: Use `*text*` for thoughts, titles, foreign words
- Do not overuse formatting

---

## 6. Whitespace

### Blank Lines
- Maximum 2 consecutive blank lines
- 1 blank line between paragraphs
- 2 blank lines before major sections

### Trailing Spaces
- Remove trailing spaces at end of lines
- No tabs, use spaces only

---

## 7. Special Characters

### Vietnamese Characters
- Use proper Vietnamese diacritics: `à á ả ã ạ â ă ê ô ơ ư đ`
- Always use correct tone marks

### Numbers
- Arabic numerals for numbers: `1, 2, 3, 100, 1000`
- Spell out numbers in dialogue if natural
- Use `,` for thousands separator: `1,000` not `1.000`

### Units
- Metric system: `km, m, cm, kg`

---

## 8. Typography

### Capitalization
- Chapter headings: ALL CAPS
- Proper nouns: Capitalize (Prague, Alice Chen, Marcus)
- Vietnamese words: Follow Vietnamese capitalization rules

### Abbreviations
- Keep English abbreviations as-is: `OBE, CIA, FBI`
- Add Vietnamese translation in parentheses on first use if helpful

---

## 9. Consistency Rules

### Names
- Keep character names consistent throughout
- Use glossary for standardized translations

### Terminology
- Follow `style/glossary.csv` for technical terms
- Log new terms in `style/new_terms.txt`

### Formatting
- Run `scripts/check_formatting.py` before finalizing
- Run `scripts/normalize_dashes.py` to standardize punctuation

---

## 10. Export Formatting

### Font Usage
Fonts live one folder per family under `fonts/`, with generic file names:

```
fonts/<Family>/Regular.ttf      # required
fonts/<Family>/Bold.ttf
fonts/<Family>/Italic.ttf
fonts/<Family>/BoldItalic.ttf   # .otf also accepted
```

- **Default**: Literata (SIL OFL 1.1, full Vietnamese coverage); licence in `fonts/Literata/OFL.txt`
- **Choose a family**: `font: <Family>` in `book.yaml`, or `export.py --font <Family>`
- A missing Bold/Italic file is skipped (the renderer synthesizes it); a missing `Regular` stops the export
- Available: `Literata` (add your own under `fonts/<Family>/`)
- Ship only fonts whose licence allows redistribution (OFL or similar)

**Implementation** (`scripts/utils/fonts.py`):
- PDF: `@font-face` with `file://` URLs, embedded by WeasyPrint
- EPUB: files embedded at `fonts/<Family>/<Variant>.ttf`
- HTML: files embedded as base64 data URIs
- Fallback stack: `'<Family>', Georgia, serif`

### Dialogue in HTML/PDF
- Each dialogue line (`- ...`) becomes its own paragraph
- No indentation on dialogue lines
- Slight spacing between dialogue exchanges

### Preserved Line Breaks
- Short lines (< 80 chars) without sentence-ending punctuation
- Use `.preserve-break` CSS class
- No indentation, minimal spacing

### Chapter Links
- TOC must link to chapters using anchors
- Format: `[CHƯƠNG 1](#chuong-1)`

### Page Breaks
**CRITICAL**: Major sections must start on a new page

- **Rule**: Add `page-break-before: always` to major content sections (chapters and special sections)
- **Applies to**:
  - Copyright page (page-break-before AND page-break-after)
  - Publisher info page (if present - page-break-before AND page-break-after)
  - Lời cống hiến (Dedication)
  - Đề từ (Epigraph)
  - Lời nói đầu của tác giả (Author's Note)
  - LỜI MỞ ĐẦU (Prologue)
  - CHƯƠNG 1, CHƯƠNG 2, etc. (Chapters)

- **Does NOT apply to**:
  - MỤC LỤC (Table of Contents) - follows naturally from copyright page
  - Title pages, book lists - follow natural flow

- **CSS Implementation**:
  ```css
  .copyright-page {
      page-break-before: always;
      page-break-after: always;
  }

  .chapter-heading {
      page-break-before: always;
  }

  .cover-page {
      page-break-after: always;
  }
  ```

- **Rationale**: Proper book formatting, major content sections start fresh page while maintaining natural flow
- **Examples**:
  - ✅ Correct: Cover page first, then copyright on separate page
  - ✅ Correct: Copyright page separate (page breaks before & after)
  - ✅ Correct: TOC follows naturally after copyright (no extra blank page)
  - ✅ Correct: Each CHƯƠNG on new page
  - ✅ Correct: Lời cống hiến on new page
  - ❌ Wrong: Blank page between copyright and TOC
  - ❌ Wrong: Copyright mixed with TOC

### Cover Page
- **File**: `cover.jpg` in project root
- **Format**: JPEG image
- **Placement**: First page of PDF
- **Styling**: Full page, centered, no margins

### Copyright Page
- **Detection**: Lines starting with "Bản quyền ©" or year (e.g., "2025")
- **Page breaks**: Before and after (separate page - respect .md file structure)
- **Year styling**:
  - Font size: 11pt
  - Alignment: Centered
  - Margin bottom: 1em
- **Copyright text styling**:
  - Font size: 9pt
  - Alignment: Centered
  - Line height: 1.5
  - Text indent: 0

### Publisher Page (if present)
- **Detection**: Lines starting with "Penguin Random House"
- **Font size**: 8pt
- **Alignment**: Justified
- **Line height**: 1.5
- **Page breaks**: Before and after (separate page)

---

## Scripts for Enforcement

Use the unified formatter for supported formatting fixes; it preserves structural HTML
comments such as `<!-- Page X -->` while normalizing prose punctuation.

1. **Fix formatting issues**:
   ```bash
   python3 scripts/fix.py
   ```

2. **Check without writing**:
   ```bash
   python3 scripts/fix.py --check-only
   ```

3. **Fix chapter headings**:
   ```bash
   python3 scripts/utils/fix_chapter_format.py
   ```

4. **Test HTML export**:
   ```bash
   python3 scripts/utils/export_html_test.py
   ```

5. **Test PDF export**:
   ```bash
   python3 scripts/export_pdf_test.py
   ```

7. **Test EPUB export (recommended for Kindle)**:
   ```bash
   python3 scripts/export_epub_test.py
   ```

---

## Changelog

### 2025-01-28 (Update 4c)
- **CRITICAL**: Copyright page now respects .md file structure
- Copyright page detection: year + "Bản quyền ©" gets separate page
- Updated copyright styling: centered, 9pt text, 11pt year
- Separated copyright page (.copyright-page) from publisher page (.publisher-page)
- **FIXED**: Removed page break before TOC (was causing blank page)
- TOC now follows naturally after copyright page

### 2026-10-12
- Fonts: default Literata (SIL OFL); one folder per family `fonts/<Family>/{Regular,Bold,Italic,BoldItalic}.ttf`, chosen via `book.yaml` `font:` or `--font`

### 2025-01-28 (Update 4b)
- Fixed copyright font size (7pt → 8pt for better readability)
- Fixed broken URL: https://eu - contact.penguin.ie → https://eu-contact.penguin.ie
- Added missing headers on pages 12, 13, 14:
  - Page 12: "Lời cống hiến" header above dedication
  - Page 13: "Đề từ" header above epigraph
  - Page 14: "Lời nói đầu của tác giả" header above "SỰ THẬT"
- Added section-subtitle style for subsection headers

### 2025-01-28 (Update 4a)
- Added cover page support (cover.jpg)
- Added copyright page detection and page breaks
- Copyright info (starting with "Penguin Random House") gets separate page
- Updated export scripts to include cover image
- Added CSS for `.copyright-page` and `.cover-page`

### 2025-01-28 (Update 3)
- **CRITICAL**: Added dash spacing rule (must have spaces on both sides)
- Added page break rule for major sections (TOC, chapters, special sections)
- Added a legacy dash-spacing utility (deprecated; use `scripts/fix.py`)
- Updated export scripts with `page-break-before: always` for `.toc-title`
- Fixed 65 files with dash spacing issues

### 2025-01-28 (Update 2)
- Added line break preservation rule for short lines
- Specified `.preserve-break` CSS class for lists/short content
- Updated export formatting section

### 2025-01-28 (Update 1)
- Initial version
- Added dash normalization rule (— → -)
- Defined chapter heading format (CHƯƠNG X)
- Specified dialogue line break preservation
- Added maximum blank line rule (2 consecutive)

---

## Notes

- This document should be reviewed before translating each chunk
- Update this file when new formatting patterns are discovered
- All scripts should enforce these rules automatically
- When in doubt, check completed chunks for examples
