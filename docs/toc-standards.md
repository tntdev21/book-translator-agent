# TOC Standards

**Last Updated:** 2026-10-08

Format requirements for the Table of Contents (Mục lục) in translated chunks.

Enforced automatically by `scripts/utils/validate_toc.py` (class `TOCValidator`).
`scripts/export.py` runs this validation before export and refuses to continue
on failure unless `--force`/`-y` is passed.

## 1. TOC header

The TOC must open with one of these exact headers, on its own line:

- `MỤC LỤC`
- `TABLE OF CONTENTS`
- `CONTENTS`

The header is searched only in `chunk_001.md`. A missing header is a hard error.

## 2. Chapter entries

Each chapter entry in the TOC must match:

```
^CHƯƠNG (\d+)$
```

- Uppercase `CHƯƠNG` is required. `Chương 1` is an error — the validator reports
  *"Use 'CHƯƠNG' not 'Chương'"*.
- The entry must be the chapter label alone. Do not merge the chapter title onto
  the same line (e.g. `CHƯƠNG 1 Mở đầu` is flagged as merged text).
- Chapter numbers must be digits only, no roman numerals, no zero padding
  (`CHƯƠNG 1`, not `CHƯƠNG 01`).

## 3. Chapter headings in content

Chapter headings in the body must use the same `^CHƯƠNG (\d+)$` form, so the
validator can cross-check TOC entries against content.

Two failure modes are detected in every chunk:

| Pattern | Error |
|---|---|
| `^CHƯƠNG \d+ [A-Z...]` (title merged onto heading line) | Merged text |
| `^Chương \d+$` (lowercase) | Use 'CHƯƠNG' not 'Chương' |

## 4. Numbering

Chapter numbers must be sequential. Gaps produce a warning, not an error:

```
⚠️  Gap: 5-7
```

## 5. TOC ↔ content cross-check

Every `CHƯƠNG n` in the TOC must exist as a heading in some chunk, and vice
versa. Mismatches are hard errors:

- `❌ CHƯƠNG n in TOC but not in content`
- `❌ CHƯƠNG n in <file> but not in TOC`

### 5b. Link check (every TOC format)

The validator runs the export's own linker over the merged book
(`validate_toc.check_toc_links`):

- `❌ TOC entry has no target` — no `# ` heading and no front block matches. Hard error.
- `⚠️ TOC wording differs from heading` — `N. …` entry linked by chapter number but
  worded differently from `# N. …`. Warning; Book Close sends it back to the TOC chunk
  (headings are canonical).

Linking rules: `N. …` entries link to the first top-level `# N. …` heading (wording may
differ); other entries match top-level `# ` headings only, never `## ` subheadings (e.g.
the per-chapter groups of a Notes chapter). Duplicate ids get `-2`, `-3` suffixes.

### 5c. Front-matter blocks

```markdown
<!-- front id="copyright" class="copyright" -->
...
<!-- /front -->
```

Ids are language-neutral: `cover`, `title-page`, `copyright`, `epigraph`, `dedication`
(plus free ids such as `epigraphs` for pages with no TOC entry). A TOC entry links to them
through the aliases in `scripts/utils/toc_language_config.json` → `front_sections`
("Bản quyền", "*Copyright*" → `copyright`). Markers are added to the **source** chunk once
per book and copied verbatim by translators. An empty `title-page` block is filled at
export from `book.yaml` (`title_vi`, `subtitle_vi`, `author`).

## 6. File layout requirements

- `chunk_001.md` must exist in the translated directory — the TOC is read from it.
- Chunk files are named `chunk_NNN.md` (no language suffix).

## 7. Running the validator

```bash
python scripts/utils/validate_toc.py <translated_dir>
```

Check the source before translating (front blocks, headings):

```bash
python scripts/utils/validate_toc.py --book <book-id> books/<book-id>/chunks
```

Or run the standalone CLI:

```bash
python scripts/utils/validate_toc.py books/<book-id>/translated
```

## 8. Legacy translations

For books translated before structured extraction was implemented (pre-verification
gate), TOC validation may fail due to missing or malformed chapter headings. In these
cases, `--force`/`-y` can be used to bypass validation and proceed with export:

```bash
python scripts/export.py -y  # Bypass TOC validation
```

However, this is not recommended for new translations. Always verify structure through
the proof export gate before splitting and translating.
