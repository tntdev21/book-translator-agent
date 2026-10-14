---
name: book-translating
description: Orchestrate end-to-end EN→VI translation pipeline for one book — batch translation (≤5 parallel), editor review (single per batch), manifest state machine, term logging, and rework loop. Use when you want the full per-chunk pipeline driven automatically against a book's manifest.json. Does not translate or review chunks itself; it owns state and spawns the translator/editor subagents, whose agent definitions own the per-chunk procedure.
user-invocable: true
when_to_use: "Invoke when you want a book's pending chunks driven through pending → translated → review → qa_passed with the canonical batch + single-editor pattern."
category: translation
keywords: [orchestrator, translation, manifest, batch, review, rework, qa, en-vi, book, pipeline]
argument-hint: "[--book <id>] [--batch-size N] [--from <chunk-id>] [--dry-run] [--stop-on-review] [--max-batches N]"
---

# Book-Translating Orchestrator

Drives a book's pending chunks through the canonical pipeline. Owns state and
subagent lifecycle only; never translates, edits or reviews text.
Operational spec: [`references/runbook.md`](references/runbook.md). Message
templates: [`references/subagent-prompts.md`](references/subagent-prompts.md).

Not for: single chunk → `/translate` (`translating` skill); single review → `/editing`; Layer-3 setup → `/deriving-dna`.

## Owns vs Delegates

| Concern | Owner |
|---|---|
| Batch picking, manifest transitions, `new_terms.txt` (via `log_terms.py`), `term_map.json` + `_terms_compact.md` (via `extract_term_map.py`), ledger, `logs/qa_issues.txt` | **this skill** |
| Translation, `fix.py`, validation, candidate terms, return JSON | `translator` agent (`.claude/agents/translator.md`) |
| Paired review, typo auto-fix, `corrections.md`, verdict JSON | `editor` agent (`.claude/agents/editor.md`) |
| Role snapshots `_knowledge_snapshot.md` / `_editor_snapshot.md` | `scripts/compile_knowledge.py` |

**The orchestrator never Reads** `_knowledge_snapshot.md`, `_editor_snapshot.md`,
`_terms_compact.md`, `corrections.md`, `dna.md`, the style guide, glossary, or any
chunk. Subagents Read their own context (agent def Step 0). Prompts carry ids only.

## Flow

1. **Session start (once):** pre-condition gate (below), then
   `BOOK_ID=<id> ./venv/bin/python scripts/compile_knowledge.py` (no `--strict`) and
   `BOOK_ID=<id> ./venv/bin/python scripts/extract_term_map.py`. Bash output only.
2. **Pick batch** from `manifest.json`: next `pending` (or from `--from`), ≤ batch-size,
   EN source ≤ ~95KB total (runbook §Batch Rules). `--dry-run`: print it, stop.
3. **Spawn N translators in ONE message** (Agent tool, `subagent_type: translator`,
   `description: "translator"`, no `name`, prompt = prompts §ASSIGNMENT). Append a
   ledger line per agentId.
4. **Accept** each return (prompts §Acceptance + runbook Rule 1a exit-code gate); one
   RETRY on failure, never a fix by main. Mark `translated` via `manifest_status.py`
   (refuses a missing/empty file). Log accepted `candidate_terms` one at a time.
5. `extract_term_map.py` (refreshes `term_map.json` + `_terms_compact.md`).
6. Move batch to `review`; **spawn exactly one editor** (`subagent_type: editor`,
   `description: "editor"`, no `name`, prompt = prompts §BATCH).
7. **Verdicts:** `pass` → `qa_passed`; `needs-fix` → `rework` → `SendMessage` the
   owning translator (prompts §REWORK) → accept → `translated` → `review` →
   `extract_term_map.py` → `SendMessage` the **same batch editor** (prompts §RE-REVIEW).
   Append editor `kind: tooling:` note lines to `logs/qa_issues.txt`.
   Term-drift `needs_decision` → apply the editor's `recommended` by default and continue
   (runbook §Term Decisions); never pause for the user over a term or wording choice.
   `--stop-on-review`: pause after each verdict.
8. **Batch close** (all chunks `qa_passed`): TSV log line, one usage table
   (runbook §Batch-End Usage Report to Human), report `needs_decision`/promotion
   candidates/WARN lines. Loop to step 2 until done, stopped, or `--max-batches` reached.

## Pre-Condition Gate

Before step 1's scripts: `books/<id>/dna.md`, `books/<id>/style/translation_style_guide.md`
exist and `books/<id>/chunks/manifest.json` parses. Missing → halt:
"Run `/deriving-dna`, then re-run `/book-translating`." No spawns, no writes.

After step 1's scripts, one check: `_knowledge_snapshot.md`, `_editor_snapshot.md`,
`_terms_compact.md` all exist and are non-empty (`test -s`). Still missing → HALT +
report. `corrections.md` is optional (agents treat missing as empty).

`compile_knowledge.py` exit 1 or 3 → HALT, report stderr. Exit 0 with `WARN` lines →
continue; carry the WARN lines into the batch report. `extract_term_map.py` non-zero →
HALT (never spawn an editor on a stale term list).

## Execution Discipline

Runs in the main loop. Only writes are hook-guarded (`translated-guard`: main never
writes `translated/`, `chunks/*.md`, `source/`). Audited sessions stalled 4–8 min and
spawned nothing by looping on checks.

- **D1 Act, don't re-verify.** Every check runs once; never re-run a command or a
  variant whose output you have seen.
- **D2 "Now spawning" = the Agent call** in the same turn, never narration followed by Bash.
- **D3 Goal discipline.** Only the user's goal; no invented sub-goals. Ambiguous → one
  short question.
- **D4 Action discipline.** Only actions authorized here. No state transition before
  the translated file exists (`test -s`); no manifest write before the first spawn;
  never reconstruct prior batches from other sessions' logs (runbook Rule 0). Every
  transition = `scripts/manifest_status.py`. No ad-hoc scripts, analysis or benchmark
  reading during a run (separate session).
- **D5 Budget.** ≤15 Bash calls before the session's first spawn; over → stop, report,
  spawn or halt.

## CLI Args

| Flag | Default | Purpose |
|---|---|---|
| `--book <id>` | auto-detect | Book under `books/` (`--book`, `BOOK_ID`, or the only book) |
| `--batch-size N` | 5 (cap 5) | >5 rejected |
| `--from <chunk-id>` | first `pending` | Resume at this chunk (inclusive) |
| `--dry-run` | off | Print next batch; no spawns, no writes |
| `--stop-on-review` | off | Pause after each editor verdict |
| `--max-batches N` | 5 | Stop after N batch closes; main may auto-compact, see runbook §Compaction Recovery |

Valid forms only: `--book <id>`, `--from chunk_NNN` (zero-padded), `--batch-size N`.
Translate loose phrasing once ("3 chunk 27-29" → `--from chunk_027 --batch-size 3`).
Invalid: `--book` with no value or a placeholder, `--from 27`, positional ranges.
Omit `--book` to auto-detect.

## Reused Utilities

| Script | Use |
|---|---|
| `scripts/utils/book_config.py` | Book + path resolution |
| `scripts/compile_knowledge.py` | Role snapshots (session start) |
| `scripts/extract_term_map.py` | `term_map.json` + `_terms_compact.md` (session start, after term logging, before every editor message) |
| `scripts/log_terms.py` | Idempotent term append (coordinator only) |
| `scripts/manifest_status.py` | Every manifest transition (graph-checked) |
| `scripts/check_agent_context.py --subagents` | Usage report + first-batch cache check |

> The orchestrator owns state, not text. Translators and editors own text. Never both.
