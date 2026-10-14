# CLAUDE.md - Instructions for Claude Code

## Project Overview
This is a translation project. All instructions for Claude Code are contained in this file.

**IMPORTANT:** Before you plan or proceed any implementation, always read the `./README-FOR-AGENTS.md` file first to get context.

---

## ⚠️ IMPORTANT

1. **DO NOT read PDF directly** - Always use pdfplumber extract first
2. **ALWAYS load style guide** before translating: `books/<id>/style/translation_style_guide.md`
3. **Coordinator updates manifest.json** only after validated batch outputs are ready; translators never write the shared manifest during parallel work
4. **Coordinator logs accepted new terms** with `python3 scripts/log_terms.py`
   - NEVER manually append to `books/<id>/style/new_terms.txt`
   - Script automatically prevents duplicates and infinite loops
5. **SAMPLES ARE NOT SOURCE** - `books/<id>/samples/` holds published EN↔VI
   pairs used to derive voice rules (`dna.md`). Never chunk, translate, or
   export them.
6. **AUTOMATIC QUALITY CHECKS** - `python scripts/fix.py` runs automatically:
   - CJK corruption detection (prevents Chinese/Japanese chars)
   - Book-specific name extraction (auto-builds from source)
   - Sentence break fixing (uses extracted names)
   - All formatting fixes
7. **EDIT AFTER TRANSLATING** - `/editing <chunks>` reviews against the source.
   The editor auto-fixes unambiguous typos only; everything else is reported
   for a human to decide, then handed back to the translator.
8. **LOG EDITOR FINDINGS** - Recurring issues go to
   `books/<id>/style/corrections.md`, which every later `/translating` run reads.
   Never edit Layer 1/2 knowledge from the editor — propose, human promotes.
9. **TRANSLATED TEXT IS GUARDED** - A PreToolUse hook (`.claude/hooks/translated-guard.cjs`)
   blocks the main session from writing/removing `books/*/translated/**`, `chunks/*.md`,
   `source/**`. Fixes go to the owning translator (RETRY/REWORK); denials log to `logs/hook-denials.txt`.

## 🆕 FOR NEW BOOKS (Automated Setup)

When starting a new book translation:

1. **Scaffold the book**: create `books/<id>/` and write `books/<id>/book.yaml`
   (`id`, `title_en`, `title_vi`, `author`, `category`, `language_pair`,
   `epub_identifier`, `chunk_size`). No code changes needed —
   adding a book means adding one directory plus one YAML file.

2. **Extract and split**:
   ```bash
   python scripts/extract.py input/source.pdf books/<id>/source/full_text.md
   python scripts/split_chunks.py books/<id>/source/full_text.md books/<id>/chunks/
   ```
   `split_chunks.py` reads `category` from `book.yaml` to pick the Layer-2 template.

2b. **Mark front matter + check TOC in the source** (before any translation):
   wrap title page / copyright / epigraph / dedication in
   `<!-- front id="title-page|copyright|epigraph|dedication|cover" [class="..."] -->` … `<!-- /front -->`
   (language-neutral ids; translated TOC entries map to them via `scripts/utils/toc_language_config.json`).
   Leave `title-page` empty: export fills it from `book.yaml` (`title_vi`, `subtitle_vi`, `author`). Then:
   ```bash
   python scripts/utils/validate_toc.py --book <id> books/<id>/chunks   # must PASS
   ```
   Translators copy markers verbatim (`validate-translation.py` errors otherwise); they never add them.

3. **First run of `python scripts/fix.py`**:
   - Automatically extracts character names from the book's own source
   - Creates `books/<id>/style/book_names.json` database
   - Uses names to fix sentence breaks smartly

4. **Auto-updated for each book**:
   - Names database refreshes weekly automatically
   - No manual name list maintenance needed
   - Works for any book or author

5. **Prevention layers**:
   - CJK detection catches corruption early
   - Name extraction improves over time
   - All fixes run automatically before export

---

## 🔄 Automated Workflow

All critical scripts now include **automatic formatting fixes**:

| Step | Script | Auto-fixes Applied |
|------|--------|-------------------|
| 1️⃣ Extract | `extract.py` | ✅ Sentence breaks + Dash normalization + Backup |
| 2️⃣ Split | `split_chunks.py` | ✅ Verification (catches any missed issues) |
| 3️⃣ Translate | Manual (Claude) | - |
| 4️⃣ Fix | `fix.py` (optional) | ✅ All formatting issues + Check mode |
| 5️⃣ Export | `export.py` | ✅ Sentence breaks + Dash normalization |

**Result**: Clean, properly formatted text at every stage! 🎉

---

## Commands Reference

### 1. Extract Source File to Markdown

**Unified script (auto-detects PDF/DOCX):**
```bash
python scripts/extract.py input/source.pdf books/<id>/source/full_text.md
python scripts/extract.py input/source.docx books/<id>/source/full_text.md
# Or only first 30 pages:
python scripts/extract.py input/source.pdf books/<id>/source/sample.md 30
```

**✅ AUTOMATIC FIXES INCLUDED**:
- Sentence break fixing (mid-sentence, compound words, pronouns)
- Dash normalization (prose ` - `, dialogue `- `, numeric ranges retain `–`)
- Person name capitalization (Alice Chen, not Alice chen)
- Creates backup (.bak) automatically

**Individual scripts (located in scripts/utils/, use extract.py instead):**
- `utils/extract_pdf.py` - PDF extraction only
- `utils/extract_docx.py` - DOCX extraction only

### 1b. Compile Knowledge Snapshot (NEW)

Compiles the 3-layer knowledge (Universal → Category → Book-Specific) into two static,
role-filtered snapshots. Run once per book after style files are populated; re-run when
style/dna/formatting changes (glossary/new terms → `extract_term_map.py`).

```bash
python scripts/compile_knowledge.py --book <id>
# Output: books/<id>/style/_knowledge_snapshot.md  (translator, ~32KB)
#         books/<id>/style/_editor_snapshot.md     (editor, ~35KB)
# Size guard: WARN >45KB, FAIL >50KB (exit 3)
# --full: swaps L1+L2 to uncleaned *.full.md (debug only; exceeds the 50KB guard → exit 3)
# --strict: duplicate-rule lint fails with exit 2
```

Dynamic files (rerun/append during the pipeline, not part of the snapshots):
`books/<id>/style/_terms_compact.md` (glossary + new terms + Drift section, generated by
`python scripts/extract_term_map.py`) and `books/<id>/style/corrections.md`. Agent
definitions hold procedure only; each agent self-reads its snapshot + these two files in
Step 0 (single turn). The coordinator never reads or inlines knowledge.

### 2. Split into Chunks
```bash
python scripts/split_chunks.py books/<id>/source/full_text.md books/<id>/chunks/
```

**✅ AUTOMATIC VERIFICATION**: Checks source file for any remaining issues before splitting

### 3. Translate a Chunk
```
# Python: invoke the venv interpreter by direct path (see "PYTHON ENVIRONMENT" below).
# Shell state does not persist between Bash calls: either call ./venv/bin/python directly,
# or chain in ONE command: `source venv/bin/activate && python scripts/export.py ...`.
# PDF export (WeasyPrint) on macOS also needs: DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

The translator agent self-reads, in ONE parallel Read in Step 0:
books/<id>/style/_knowledge_snapshot.md (compiled 3-layer knowledge),
books/<id>/style/_terms_compact.md, books/<id>/style/corrections.md and the chunk.
Nothing is pasted into the prompt. Missing snapshot or terms file = `context_missing`
(recompile / rerun extract_term_map.py); missing corrections.md = empty.

Translate file books/<id>/chunks/chunk_XXX.md:
- Follow 100% style guide
- Follow formatting rules (dashes, chapters, dialogue)
- Keep paragraph structure intact
- Translate naturally, not mechanically

Save as: books/<id>/translated/chunk_XXX.md

After translation:
1. ✨ **AUTOMATIC FIX** (no manual commands needed!):
   python scripts/fix.py

   **What it does automatically**:
   - Step 0: Auto-extracts book names from the book's own source → books/<id>/style/book_names.json
   - Step 1: Detects & fixes CJK corruption (Chinese/Japanese chars)
   - Step 2: Fixes sentence breaks using extracted names
   - Step 3: Normalizes dashes (em-dash → regular dash)
   - Step 4: Fixes person name capitalization
   - Step 5: Checks remaining formatting issues

   **Advanced options** (usually not needed):
   python scripts/fix.py --check-only              # Check only, no fixes
   python scripts/fix.py --skip-cjk                # Skip CJK detection
   python scripts/fix.py --skip-name-extraction    # Skip name extraction

2. Report validation results and proposed new terms to the **batch coordinator**.
   In a multi-chunk batch, translators must not write the shared manifest or
   `new_terms.txt`; the coordinator serializes those updates after all outputs validate.

3. The coordinator updates `chunks/manifest.json` through the 5-state machine:
   `pending → translated → review → rework → qa_passed`.

4. The coordinator logs accepted new terms one at a time:
   python scripts/log_terms.py "term | translation | context | chunk_XXX"

   ⚠️ IMPORTANT: Use the script for EVERY term addition
   ⚠️ NEVER manually append to books/<id>/style/new_terms.txt
   ⚠️ The script prevents duplicates and infinite loops

**Individual fix scripts (located in scripts/utils/, use fix.py instead):**
- `utils/fix_sentence_breaks.py` - Fix sentence breaks only
- `utils/normalize_dashes.py` - Normalize dashes only
- `utils/fix_person_names.py` - Fix person name capitalization only
- `utils/fix_formatting.py` - Check formatting only
```

### 4. Batch Translate and Edit (up to five chunks)

Use one translator per chunk; each translator owns only its source/translated-file pair
and reports validation results plus candidate terms. The coordinator alone
updates the shared manifest and term log after the batch outputs validate. The coordinator
runs `python scripts/extract_term_map.py` once at session start and again after each batch's
term logging (before assigning the editor) to refresh `_terms_compact.md`.

After every batch translation is marked `translated`, move the complete batch to `review`
and assign **exactly one editor** to review every chunk. Do not parallelize editor review
within a batch. The editor performs paired EN↔VI review, a bounded cross-chunk term/seam
pass, and gives a `pass` or `needs-fix` verdict per chunk.

- `pass`: coordinator moves `review → qa_passed`.
- `needs-fix`: coordinator moves only that chunk to `rework`, returns it to its owning
  translator, then sends the repaired chunk back through `translated → review` to the
  **same batch editor**. Do not shortcut to `qa_passed`.

```text
translator × N → coordinator validates/logs/marks translated
               → one editor reviews the entire batch
               → qa_passed | rework → owning translator → same editor re-review
```

### 4b. Orchestrate a Book (full pipeline)

For a book-level pipeline that drives pending chunks through
`pending → translated → review → qa_passed` with the canonical batch + single-
editor pattern, spawns subagents per a runbook, and owns `manifest.json` and
`new_terms.txt`:

At batch close (all chunks qa_passed), the orchestrator prints one consolidated markdown token-usage table for the batch to the chat — see `.claude/skills/book-translating/references/runbook.md` §Batch-End Usage Report to Human.
```
/book-translating --book <id> [--from <chunk-id>] [--batch-size N] [--dry-run] [--stop-on-review]
```

See `.claude/skills/book-translating/SKILL.md` for details. The leaf-skills
`/translating`, `/editing`, `/deriving-dna` remain the source of truth for
per-chunk work — this orchestrator only owns state and subagent lifecycle.

### 5. QA Check
```
Check books/<id>/translated/chunk_XXX.md:
1. Check formatting: python scripts/fix.py --check-only
2. Validate TOC: python scripts/utils/validate_toc.py translated/
3. Compare paragraph count with original
4. Verify glossary terms are translated correctly
5. Re-read to check if natural
6. Log issues to logs/qa_issues.txt
```

### 6. Merge & Export

**⚠️ AUTOMATIC TOC VALIDATION:**
Export script automatically validates TOC format before export.
See `docs/toc-standards.md` for format requirements.

**Unified export script:**
```bash
# Export all formats (PDF + EPUB + HTML)
python scripts/export.py

# Export only PDF
python scripts/export.py -f pdf

# Export only EPUB
python scripts/export.py -f epub

# Custom output directory and metadata
python scripts/export.py -o custom_output/ -t "Book Title" -a "Author Name"
```

**✅ AUTOMATIC FIXES INCLUDED**:
- Pre-export sentence break fixing
- Pre-export dash normalization
- Pre-export person name capitalization
- No backups created (keeps translated/ clean)

**💡 OPTIONAL - Manual fix before export:**
```bash
# If you want to check/fix manually before export:
python scripts/fix.py

# Or check-only mode:
python scripts/fix.py --check-only
```

**Individual export scripts (located in scripts/utils/, use export.py instead):**
- `utils/export_pdf.py` - PDF export only
- `utils/export_epub.py` - EPUB export only
- `utils/export_html.py` - HTML export only

---

## File Locations

Each book lives in its own directory. `<id>` resolves from `--book <id>`, the
`BOOK_ID` env var, or auto-detection when exactly one book exists
(`scripts/utils/book_config.py`).

| Purpose | Path |
|---------|------|
| Book config | `books/<id>/book.yaml` |
| Source PDF (input) | `input/source.pdf` |
| Source (extracted) | `books/<id>/source/full_text.md` |
| Style Guide | `books/<id>/style/translation_style_guide.md` |
| Formatting Rules | `books/<id>/style/formatting_rules.md` (falls back to shared `style/formatting_rules.md`) |
| Glossary | `books/<id>/style/glossary.csv` |
| New Terms | `books/<id>/style/new_terms.txt` |
| Name Database | `books/<id>/style/book_names.json` |
| Chunks | `books/<id>/chunks/chunk_XXX.md` |
| Manifest | `books/<id>/chunks/manifest.json` |
| Translated | `books/<id>/translated/chunk_XXX.md` |
| Final Output | `books/<id>/output/` |
| Cover | `books/<id>/cover.jpg` (optional) |
| Custom Font | `fonts/*.ttf` (shared) |
| Logs | `logs/*.txt` (shared) |

---

## Style Guide Format

Style guide must have these sections:

1. **Tone & Voice** - Formal/informal, academic/casual
2. **Sentence Structure** - How to handle long sentences, passive voice
3. **Glossary Table** - Terminology table EN → VI
4. **Proper Nouns** - Rules for translating proper names
5. **Formatting** - Numbers, dates, units
6. **Examples** - Specific examples

---

## Manifest Status Values

5-state machine (`schema_version=2`; each transition is logged in `status_history`):

- `pending` - Not yet translated
- `translated` - Translation completed (raw output from translator)
- `review` - Under editor review
- `rework` - Editor flagged issues; translator fixing
- `qa_passed` - Review completed and approved

---

## Global-Local Override Rule

When conflicts arise between shared root rules and book-specific rules, the
book-local rules always win:

- `books/<id>/style/formatting_rules.md` overrides shared `style/formatting_rules.md`
- `books/<id>/style/glossary.csv` and `books/<id>/style/new_terms.txt` override any
  shared terminology
- `books/<id>/style/corrections.md` corrections apply only to this book and are
  read by every later `/translating` run for that book

Shared rules remain the default; book-local rules layer on top to refine them for
its specific content.

---

## Output Specifications

### PDF (Letter, matches source)
- Size: 612pt × 792pt
- Margin: 66pt top/bottom, 57pt sides
- Font: from `fonts/` folder
- Font size: 14.4pt
- Line height: 1.4

### EPUB
- Font embedded from `fonts/`
- Chapters split by `# ` headings
- Auto-generated TOC

---

## Quick Commands

```bash
# ====================================
# SETUP (first time only)
# ====================================
./setup.sh
# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ====================================
# PYTHON ENVIRONMENT (canonical)
# ====================================
# Interactive terminal (human):
source activate.sh          # or: source venv/bin/activate
# Subagents/scripts (shell state does NOT persist between Bash calls) —
# invoke the interpreter directly:
./venv/bin/python scripts/fix.py
./venv/bin/python -m pytest tests/unit/ -q

# ====================================
# FULL TRANSLATION PIPELINE (AUTOMATED)
# ====================================
# <id> resolves from: --book <id>  |  BOOK_ID env  |  auto-detect (single book)
# 1. Extract + Auto-fix source
python scripts/extract.py input/source.pdf books/<id>/source/full_text.md

# 2. Split + Auto-verify
python scripts/split_chunks.py books/<id>/source/full_text.md books/<id>/chunks/

# 3. [Translate each chunk with Claude - see "Translate a Chunk" section]

# 4. (OPTIONAL) Manual fix check
python scripts/fix.py --check-only

# 5. Export + Auto-fix → Final output
python scripts/export.py

# ✅ All formatting issues handled automatically!

# ====================================
# UNIFIED SCRIPTS (recommended)
# ====================================
# Extract (auto-detect PDF/DOCX)
python scripts/extract.py input/source.pdf books/<id>/source/full_text.md

# Fix all formatting issues
python scripts/fix.py                           # Fix all files
python scripts/fix.py books/<id>/translated/chunk_XXX.md  # Fix specific file
python scripts/fix.py --check-only              # Check only, don't fix
python scripts/fix.py --skip-dashes             # Skip dash normalization

# Export to multiple formats
python scripts/export.py                        # Export all formats
python scripts/export.py -f pdf                 # Export only PDF
python scripts/export.py -f epub                # Export only EPUB
python scripts/export.py -o output/ -t "Title"  # Custom options

# ====================================
# TERM LOGGING (with duplicate prevention)
# ====================================
# Add new term
python scripts/log_terms.py "term | translation | context | chunk_id"

# Check for duplicates
python scripts/log_terms.py --check

# ====================================
# INDIVIDUAL SCRIPTS (in scripts/utils/, use unified versions instead)
# ====================================
# Extract: utils/extract_pdf.py, utils/extract_docx.py
# Fix: utils/fix_sentence_breaks.py, utils/normalize_dashes.py, utils/fix_formatting.py
# Export: utils/export_pdf.py, utils/export_epub.py, utils/export_html.py
```
