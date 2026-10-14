---
name: translating
description: Translate book chunks EN→VI using the 3-layer knowledge system (universal, category, book-specific). Use for translating chunks of a book, reworking a chunk after editor findings, or understanding where translation rules live. Spawns `translator` agents.
user-invocable: true
---

# Translating

Per-chunk translation procedure lives in the `translator` agent
(`.claude/agents/translator.md`). This skill is the map: what knowledge exists,
where it is compiled, and how to spawn translators.

## When to Use

- Translating chunks of a book (EN→VI), one agent per chunk
- Reworking or retrying a chunk
- Finding which layer a translation rule belongs to

## 3-Layer Knowledge

| Layer | Source | Scope |
|---|---|---|
| L1 Universal | `references/*.md` | every translation |
| L2 Category | `categories/{category}.md` + `{category}--dna-*.md` | every book of the genre |
| L3 Book | `books/<id>/dna.md`, `style/*` | one book |

L1+L2+L3 are compiled into role-filtered files: `books/<id>/style/_knowledge_snapshot.md`
(translator) and `_editor_snapshot.md` (editor). Dynamic files, always current:
`_terms_compact.md` (binding terms) and `corrections.md` (editor findings).
Agents read these themselves; never paste knowledge into a prompt.

## Prerequisites

```bash
./venv/bin/python scripts/compile_knowledge.py --book <id>   # snapshots; re-run after style/dna/glossary changes
./venv/bin/python scripts/extract_term_map.py                # _terms_compact.md; re-run after term changes
```

Chunks must exist (`scripts/split_chunks.py`). `dna.md` and `style/translation_style_guide.md` are required; run `/deriving-dna` if missing.

## Standalone Usage

Spawn one `translator` agent per chunk (up to 5, all in ONE message). Prompt:

```
Book: <id>
ASSIGNMENT: chunk_XXX
```

Rework: line 2 `REWORK: chunk_XXX`, then the editor findings JSON.
Retry: line 2 `RETRY: chunk_XXX <reason>`.

The agent returns JSON (validation flags, candidate terms). It writes only its own
translated chunk; you (the coordinator) update `manifest.json` and log accepted terms
with `scripts/log_terms.py`, and advance the record to `translated`. Then run `/editing`. Full pipeline: `/book-translating`.

## Resources

| Path | Purpose |
|---|---|
| `references/base-principles.md` | L1 translation principles |
| `references/vietnamese-conventions.md` | L1 Vietnamese rules |
| `references/quality-checklist.md` | L1 QA checklist |
| `categories/*.md` | L2 genre templates (thriller, sci-fi, fantasy, romance, literary, technical, self-help, non-fiction) |

| Script | Purpose |
|---|---|
| `.claude/skills/translating/scripts/validate-translation.py` | quality validation |
| `.claude/skills/translating/scripts/compare-structure.py` | structure comparison vs source |
| `scripts/fix.py` (repo root) | formatting fixes; flags in the agent def |

> Translate meaning, tone, and intent, not words.
