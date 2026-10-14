# System Architecture

**Project:** Book Translation Pipeline
**Last Updated:** 2026-10-10
**Architecture:** Local Python CLI with isolated book workspaces, single-turn self-read subagents.

## 1. Model

Shared scripts and knowledge live at the repository root. Every book owns its working data under `books/<id>/`; scripts resolve one `BookConfig` and use its paths rather than hard-coded global book directories.

```text
--book <id> → BOOK_ID → one detected books/*/book.yaml → ambiguity error
```

`book.yaml` declares identity, language pair, category, chunk size, optional derivation metadata, and overridable paths. Shared formatting rules at `style/formatting_rules.md` apply unless a book-local style override exists.

## 2. Pipeline

```text
PDF / DOCX / EPUB / TXT
        │
        ▼
extract.py → books/<id>/source/full_text.md (+ .bak)
        │           ↓ auto-fixes: sentence breaks, dash normalization, name capitalization
        ▼
split_chunks.py → chunks/chunk_NNN.md + manifest.json + page_marker_boundaries.json
        │
        ▼
compile_knowledge.py → _knowledge_snapshot.md (translator ~32KB) + _editor_snapshot.md (editor ~35KB)
        │        (static, role-filtered L1+L2+L3; dynamic: _terms_compact.md via extract_term_map.py, corrections.md)
        │
        ├─ [parallel: translators per chunk]
        ▼
/translating → translated/chunk_NNN.md
        │              ▲
        │              └─ Layer 1 (universal) → Layer 2 (category) → Layer 3 (dna + guide + formatting); corrections.md read dynamically
        ├─ [single batch editor]
        ▼
/editing → typo auto-fixes + revision findings → corrections.md + manifest state update
        │
        ├─ [log_terms.py + extract_term_map.py: manage glossary]
        ├─ [check_agent_context.py: track token usage per agent]
        ▼
fix.py → quality checks (name extraction, CJK, sentence breaks, dashes, format)
        │
        ├─ [centered anchored front-matter blocks with TOC links]
        ├─ [footnote marker preservation/export]
        ▼
export.py → output/{PDF, EPUB, HTML} + TOC validation
```

**Extraction:** Structured PDF via pdfplumber, python-docx, ebooklib, or direct TXT. Auto-fixes sentence breaks, dashes, name capitalization; creates `.bak`.

**Chunking:** Packs paragraph blocks; preserves page markers (hard sentence-fix boundaries) with metadata in `page_marker_boundaries.json`. Never emits marker-only translation units. Refuses regeneration if translations or non-pending states exist.

**Translation:** Parallel translator agents per chunk; each self-reads `_knowledge_snapshot.md`, `_terms_compact.md` and `corrections.md` in Step 0. Each translator gets token-usage tracked via `check_agent_context.py`.

**Editing:** Single batch editor reviews all chunks, auto-fixes typos only, reports findings. Recurring issues logged to `corrections.md` for later runs.

**Export:** Validates TOC (must be in `chunk_001.md`), applies centered anchored front-matter with links, outputs PDF/EPUB/HTML with proper formatting.

## 3. Translation Knowledge

| Layer | Location | Purpose |
|---|---|---|
| Universal | translating skill | Shared language and formatting principles |
| Category | `.claude/skills/translating/categories/` | Genre/category conventions |
| Book | `books/<id>/style/`, `dna.md` | Book terminology, voice evidence, names, and recurring corrections |

`books/<id>/samples/<name>/en.md` and `vi.md` are published parallel references used to derive `dna.md`. Samples are never source text: they must not be chunked, translated, or exported.

`log_terms.py` prevents duplicate entries at write time. There is no independent duplicate-deduplication pass and no Gemini translation path.

## 4. State and Quality

**Manifest state machine (5-state):** `pending → translated → review → [rework → translated → review] → qa_passed`.

- **Coordinator:** Sole writer of `manifest.json` and accepted term logs. After either change, runs `extract_term_map.py` (refreshes `_terms_compact.md`; `term_map.json` stays for scripts/humans) at session start and after each batch, before editor review.
- **Translators:** Parallel spawns per chunk; each tracked separately by `check_agent_context.py` for token usage reporting.
- **Editor:** Single per batch. Auto-fixes unambiguous typos only; reports mistranslations, awkward phrasing, drift. Reworked chunks return (SendMessage) to the owning translator, then to the same batch editor.
- **Quality pipeline (`fix.py`):** Name extraction, CJK detection, sentence boundaries (respects `page_marker_boundaries.json`), dash normalization, name capitalization, format checks.
- **Corrections feedback:** Recurring editor findings logged to `style/corrections.md`; all later `/translating` runs read and apply them. Shared knowledge changes stay human-gated.
- **Export validation:** TOC validator ensures `MỤC LỤC` or `TABLE OF CONTENTS` header exists in `chunk_001.md`, chapter headings match `CHƯƠNG n` form, and TOC↔content cross-check passes.

## 5. Special Features

**Footnote handling:** Export pipeline (PDF/EPUB/HTML) preserves footnote markers in final output.

**Front-matter formatting:** Export generates centered, anchored front-matter blocks with Table of Contents links, improving readability in PDF/EPUB.

**Proof export gate:** `python scripts/export.py --proof -y` generates a preview PDF for structure verification *before* translation starts, ensuring source layout matches expectations.

## 5a. Prompt-cache & cost design decisions

Final state after plans 261009-1634 (self-read) and 261012-0904 (P9). Rationale + numbers: `docs/journals/261012-prompt-cache-design-decisions.md`.

**Self-read model:** translator/editor agent defs hold procedure + JSON contract only. Coordinator spawns with a ~1K assignment prompt (no `name`, all of a batch in one message); Step 0 = ONE parallel Read of the role snapshot (`_knowledge_snapshot.md` ~32KB / `_editor_snapshot.md` ~35KB, compiled once per session; guard WARN >45KB, FAIL >50KB), `_terms_compact.md`, `corrections.md`, chunk(s). Main never inlines knowledge.

| Decision | Why (measured) |
|---|---|
| Spawn without `name`, byte-identical first turn | `name` wraps the prompt per agent → only tools+system hit. Shared prefix ≈ system+tools (~5–8K); Step-0 tool results (~22.9K/translator) are per-agent writes by design |
| Fresh translator per chunk, never reused | E1: 9 req/chunk, peak ~58K. Reuse saves ~11K write (≈$0.04) but re-reads ~58K × 9 req (≈$0.10) → +$0.06 on 2nd chunk, ~175K peak on 3rd (compaction). Consistency comes from refreshed terms/corrections files, not agent memory |
| REWORK → owning translator, RE-REVIEW → same batch editor (SendMessage) | D-P0 probe: resume reads full history from cache; file edits/gitStatus don't break it. Dead agents → fresh spawn |
| One fresh editor per batch, EN cap ~95KB | Editor is the context-scarce agent (peaks 150–161K) |
| Windowed RE-REVIEW; `lines:"sweep"` / span >40 / >6 ranges → `grep -nE` old forms | Session D editor compacted at 165.9K from whole-file re-Reads; E1: 0 compactions |
| No direct editor↔translator messaging | Relay saves ≤$0.04/chunk, but would load the editor and bypass main's accept gates/manifest ownership |
| `--max-batches` default 5, main autocompaction accepted | Main +≈33K/5-chunk batch, compacts ~167K; one compaction ≈$0.30, recovered in ~1 batch; subagents unaffected. Recovery = runbook §Compaction Recovery (manifest, ledger, latest `review/*.r<N>.json`, `logs/batch-notes.txt`) |

**Cost (Sonnet 5.5: in $2, out $10, cache read $0.20, 1h write $4 /MTok; all writes 1h TTL):** `check_agent_context.py --subagents` prints a Cost $ column + `main (session)` + TOTAL; the batch-end report copies it and adds $/chunk.

| Session | Config | $/chunk |
|---|---|---|
| C (03ccd996) | 3 batches × 3 | $1.02 |
| D (3dabfa1e) | 3 batches × 5 | $0.89 |
| E1 (f5404739) | 3 batches × 5, P9.2 | **$0.815** (translator $0.43, editor $0.22, main $0.16) |

Whole book (34 chunks) ≈ $27.7.

## 6. Boundaries

- No web app, service API, database, queue, or cloud deployment.
- Translation/editing workflows run natively in Claude Code agent context; no external API keys required.
- Generated exports stay in `books/<id>/output/`; always fix translated source, not output artifacts.

## 7. Related Skills

- `.claude/skills/book-translating/` — Full orchestration: spawn translators, manage manifest, run editor, track token usage.
- `.claude/skills/translating/` — Base translation logic with universal + category layers.

## Document Information

- **Related:** [Codebase Summary](codebase-summary.md), [Runbook](runbook.md), [PDR](project-overview-pdr.md), [Changelog](project-changelog.md)
