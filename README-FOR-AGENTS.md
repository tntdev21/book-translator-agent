# Book Translation Pipeline (EN → VI)

> Source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE). Not open source: commercial use is not permitted.

Translate a whole book from English to Vietnamese with Claude Code. Python scripts extract,
chunk, fix and export. Claude Code subagents translate and review:

- one **translator** per chunk, up to 5 in parallel;
- one **editor** per batch, reviewing EN↔VI pairs;
- a coordinator session that owns the manifest state machine and the term log.

Output: PDF, EPUB and HTML.

Measured cost (Sonnet 5.5, prompt caching): about **$0.82 per ~3,000-word chunk**, about $28 for a 34-chunk book.

---

## Requirements

- Python 3 + venv (`./setup.sh`)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI, only for the translation and review step
- WeasyPrint system libraries for PDF export (macOS: `brew install pango`; `source activate.sh` sets `DYLD_FALLBACK_LIBRARY_PATH`)

```bash
./setup.sh              # creates venv, installs requirements.txt
source activate.sh      # activates venv (+ WeasyPrint lib path on macOS)
```

## Quick start

```bash
# 1. Scaffold the book: one directory + one YAML file (see below)
mkdir -p books/<id>/style

# 2. Extract source (.pdf / .docx / .epub / .txt) and split into chunks + manifest
python scripts/extract.py input/source.pdf books/<id>/source/full_text.md
python scripts/split_chunks.py books/<id>/source/full_text.md books/<id>/chunks/

# 3. Style files (required by the orchestrator):
#    books/<id>/dna.md                              - voice rules (/deriving-dna)
#    books/<id>/style/translation_style_guide.md
#    books/<id>/style/glossary.csv                  - optional seed terms

# 4. Translate + review, inside Claude Code at the repo root
/book-translating --book <id> --batch-size 5 --max-batches 5

# 5. Export
python scripts/export.py --book <id>             # PDF + EPUB + HTML -> books/<id>/output/
```

Re-run step 4 to continue: it resumes at the next `pending` chunk (or `--from chunk_NNN`).
`--dry-run` prints the next batch without spawning anything.

### `books/<id>/book.yaml`

```yaml
id: my-book
title_en: "Original Title"
title_vi: "Tên tiếng Việt"
author: "Author Name"
language_pair: en-vi
category: non-fiction        # picks the Layer-2 template in .claude/skills/translating/categories/
epub_identifier: my-book-vi
chunk_size: 3000
font: Literata                # optional: folder under fonts/ (export.py --font overrides)
rights:                      # compiled into the translator snapshot header
  holder_confirmed: true
  statement: "The operator holds the Vietnamese translation rights to this book."
```

Categories available: `non-fiction`, `literary`, `fantasy`, `romance`, `sci-fi`, `self-help`, `technical`, `thriller`.

### Deriving the voice (`/deriving-dna`)

Put a published EN↔VI pair of the same author or genre in `books/<id>/samples/<name>/` (`en.*` and `vi.*`). Extract both with `scripts/extract.py`, then run `/deriving-dna` in Claude Code. It writes `books/<id>/dna.md`. Samples are reference material only: they are never chunked, translated or exported.

---

## How it works

```
extract.py → split_chunks.py → manifest.json (all pending)
                  │
/book-translating (coordinator = your Claude Code session)
  ├─ compile_knowledge.py   → role snapshots (_knowledge_snapshot.md, _editor_snapshot.md)
  ├─ extract_term_map.py    → _terms_compact.md (glossary + accepted new terms + drift)
  ├─ translator × N (≤5)    → translated/chunk_NNN.md + JSON (validation, candidate terms)
  ├─ coordinator            → accept gate, log_terms.py, manifest_status.py
  ├─ editor × 1 per batch   → review/<batch>.r<N>.json: pass | needs-fix per chunk
  └─ needs-fix → REWORK to the owning translator → RE-REVIEW by the same editor
                  │
export.py (runs fix.py first) → PDF / EPUB / HTML
```

Chunk states: `pending → translated → review → rework → qa_passed`.
`scripts/manifest_status.py` is the only writer.

**Knowledge layers.** Rules are delta-only and compiled into one snapshot per role. Precedence, low to high:

1. universal rules (`.claude/skills/translating/references/`)
2. category card (`categories/<category>.md`)
3. `books/<id>/dna.md`
4. style guide and terms
5. formatting rules
6. `corrections.md`

Agents read the snapshot themselves at start-up. The agent definitions contain procedure only.

**Editor contract.** The editor auto-fixes only unambiguous typos. Mistranslations, term drift and style issues go back to the translator who owns the chunk. Recurring patterns are appended to `books/<id>/style/corrections.md`, which every later translator reads.

**Cost visibility.** After each batch the coordinator prints a usage table from `scripts/check_agent_context.py --subagents`: tokens, cache read/write and Cost $ per agent, plus a main-session row, a TOTAL and $/chunk. The cache design decisions behind these numbers are in [`docs/system-architecture.md`](docs/system-architecture.md) §5a.

---

## Layout

| Path | Purpose |
|---|---|
| `scripts/` | extract, split, fix, export, compile_knowledge, extract_term_map, log_terms, manifest_status, check_agent_context, reset_book |
| `scripts/utils/` | single-purpose helpers behind the unified scripts |
| `books/<id>/` | one book: `book.yaml`, `dna.md`, `source/`, `chunks/` (+ `manifest.json`), `translated/`, `review/`, `style/`, `output/` |
| `style/` | shared formatting rules and glossary (book-local files override) |
| `fonts/<Family>/` | fonts embedded in PDF/EPUB/HTML: `Regular.ttf`, `Bold.ttf`, `Italic.ttf`, `BoldItalic.ttf`. Default Literata (SIL OFL) |
| `.claude/agents/translator.md`, `editor.md` | subagent definitions (procedure + JSON contract) |
| `.claude/skills/book-translating/` | orchestrator skill + runbook |
| `.claude/skills/translating/`, `editing/`, `deriving-dna/` | per-chunk skills, Layer-1/2 knowledge, validation scripts |
| `.claude/hooks/translated-guard.cjs` | blocks the coordinator from editing `translated/`, `chunks/*.md`, `source/`; fixes must go through the owning agent |
| `CLAUDE.md` | instructions Claude Code loads in this repo; full command reference |
| `tests/` | pytest suite |

## Without Coding Harness

Every script runs standalone:

```bash
python scripts/fix.py books/<id>/translated/chunk_001.md   # CJK check, sentence breaks, dashes, names
python scripts/fix.py --check-only
python scripts/export.py --book <id> -f pdf                 # or -f epub / -f html
```

You can translate `books/<id>/chunks/chunk_NNN.md` by hand or with any other tool, save it as `books/<id>/translated/chunk_NNN.md`, then run `fix.py` and `export.py`.

---

## Contributing

This repository ships the **product only**: the pipeline scripts and the translation runtime (two agents, four skills, one hook). The development harness used to build it is not included: planning and review agents, dev workflows, plans and journals. Use your own coding agent or work by hand.

- Run the tests: `./venv/bin/python -m pytest tests/unit -q`
- Keep agent definitions procedure-only. Language, genre and book rules belong in the knowledge layers or in `books/<id>/style/`.
- Changes to `scripts/` need a test in `tests/unit/`.
- After editing style or knowledge files, re-run `scripts/compile_knowledge.py --book <id>`. It fails above 50KB per snapshot.

## Copyright

Translate only books you have the rights to translate. Do not commit copyrighted source text, chunks or translations to a public fork.

## License

**Source-available, not open source.** Licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE):
free for personal, research, educational and other noncommercial use. Commercial use
(selling translations made with it, paid services, bundling in a commercial product)
requires a separate license from the author.

Fonts under `fonts/Literata/` are SIL OFL 1.1 (`fonts/Literata/OFL.txt`).
