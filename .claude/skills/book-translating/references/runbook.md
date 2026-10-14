# Runbook — Book-Translating Orchestrator

Operational spec. SKILL.md points here. Per-agent procedure, reads, writes, budgets
and return contracts live in `.claude/agents/translator.md` / `editor.md` — not here.
All scripts run as `BOOK_ID=<id> ./venv/bin/python scripts/<name>.py`.

---

## State Machine

```
pending ──spawn translator──► translated
translated ──coordinator validate + log terms──► translated (logged)
translated ──batch lift──► review ──single editor──► verdict
 ├─ pass       ──► qa_passed
 └─ needs-fix  ──► rework ──REWORK SendMessage to owning translator──► translated
translated ──► review ──RE-REVIEW SendMessage to SAME batch editor──► verdict
... loop until qa_passed ...
```

Every transition goes through ONE command (it enforces the graph below, refuses
`translated` on a missing/empty file, appends `{status, at}` to `status_history`):
`./venv/bin/python scripts/manifest_status.py --book <id> <status> <chunk...>`.
Never hand-edit `manifest.json` or improvise a helper script for it.

| Current | Action | Next | Who |
|---|---|---|---|
| `pending` | Spawn translator (ASSIGNMENT) | `translated` | this skill + translator |
| `translated` | Accept return, log terms (`extract_term_map.py` once per batch) | `translated` (logged) | this skill |
| `translated` (batch complete) | Lift batch | `review` | this skill |
| `review` | Spawn one editor (BATCH) | verdict | this skill + editor |
| `review` + `pass` | Apply verdict | `qa_passed` | this skill |
| `review` + `needs-fix` | Apply verdict | `rework` | this skill |
| `rework` | REWORK to owning translator | `translated` | this skill + translator |
| `translated` (after rework) | Lift back, `extract_term_map.py`, RE-REVIEW | `review` | this skill |
| any | Validation fail ×2 / missing precondition | halt + report | this skill |
| `qa_passed` | Human decision only: `--reopen rework`, findings file `review/human_<range>.r0.json`, fresh translator REWORK, one editor RE-REVIEW | `rework` | this skill |

---

## Ownership

| File | Writer |
|---|---|
| `books/<id>/chunks/manifest.json` | this skill only |
| `books/<id>/style/new_terms.txt` | this skill only, via `log_terms.py` |
| `books/<id>/style/term_map.json`, `_terms_compact.md` | this skill only, via `extract_term_map.py` |
| `books/<id>/style/_knowledge_snapshot.md`, `_editor_snapshot.md` | `compile_knowledge.py` (session start) |
| `books/<id>/style/corrections.md` | editor agent (append) |
| `books/<id>/translated/<CHUNK>.md` | owning translator; editor typo auto-fixes |
| `logs/book-translating.tsv`, `logs/book-translating.agents.tsv`, `logs/qa_issues.txt` | this skill |

The orchestrator never Reads snapshots, `_terms_compact.md`, `corrections.md`,
knowledge files or chunks; it only runs the scripts and checks existence.

---

## Session Start

1. Pre-condition gate (SKILL.md): `dna.md`, style guide, parsable `manifest.json`.
2. `compile_knowledge.py` once (deterministic, cheap; no `--strict`). Exit 1/3 → HALT +
   report stderr. Exit 0 with `WARN` lines → continue; keep them for the batch report.
3. `extract_term_map.py` once, so `_terms_compact.md` exists before the first batch.
   Non-zero → HALT.
4. One check: `test -s` on `_knowledge_snapshot.md`, `_editor_snapshot.md`,
   `_terms_compact.md`. Any missing → HALT. `corrections.md` optional.
5. First session of a book (no chunk past `pending`): `./venv/bin/python scripts/utils/validate_toc.py --book <id> books/<id>/chunks`.
   Errors → HALT; report them: the source needs `<!-- front id=... -->` blocks / heading
   fixes, which the human makes (source is guarded). Translators copy markers, never add them.

Never re-run `compile_knowledge.py` mid-session (agents self-read terms/corrections).

---

## Batch Rules

- **Max 5 chunks per batch** (CLAUDE.md §4); `--batch-size` >5 rejected.
- **EN size cap (editor context):** add chunks in order while the sum of EN source
  bytes (`wc -c` on `books/<id>/chunks/<CHUNK>.md`, one call for the candidates) stays
  ≤ ~95KB (≈200KB EN+VI pairs ≈ 90K tok). Stop before exceeding. Never split one batch
  across two editors.
- **Gaps are allowed:** a batch is the next N `pending` chunks in order, even when
  `qa_passed` chunks sit between them (e.g. 001, 003, 008). Never shrink a batch to keep
  it contiguous; each extra editor costs a full Step-0 context. Batch id = first-last.
- **One fresh translator per chunk**, all in ONE message (prompts §Spawn rules); never
  reused across chunks (measured: reuse costs more, ~2 chunks fill context).
- **One editor per batch**, sequential within the batch, spawned fresh per batch.
- **Contiguous:** a batch stops at the first non-`pending` chunk.
- **Batch id:** `batch_<first>-<last>` (3-digit chunk numbers, e.g. `batch_027-029`).
- **Neighbours** for BATCH/RE-REVIEW: prompts §BATCH.
- **First-batch cache check (once):** `check_agent_context.py --subagents --json`;
  report only if translators #2..N show `first_cache_read_tokens` ≈ 0. Request #2
  (Step 0 Reads) is never sibling-shared; its per-agent write is expected.

---

## Tool-Call Budget & Cost Accounting

**Rule 0 — batch from the manifest only.** Take the next `pending` chunks (or
`--from`) from `manifest.json`. Never reconstruct earlier batches from other sessions'
JSONL logs, `logs/*.tsv`, `term_map.json` timestamps, task outputs or worktrees.
`check_agent_context.py` and the usage report cover only agents this session spawned.
Inconsistent pre-existing state (a batch stuck in `translated`/`review`/`rework`) →
proceed with `pending` chunks or halt + report in one message; never investigate.

**Rule 1 — scripts only, no ad-hoc probes.** The orchestrator never hand-checks a
translated file (`python -c`, heredoc, re-Read). Validation is the agents' job via
`fix.py`, `compare-structure.py`, `validate-translation.py` (agent defs).
A chunk that fails validation after its translator returns → `SendMessage` RETRY to
the owning translator. The orchestrator never edits, fixes, moves or deletes anything
in `translated/`, `chunks/*.md` or `source/` (no fix scripts, no `rm *.bak`); the
`translated-guard` PreToolUse hook denies it and logs to `logs/hook-denials.txt`.
No ad-hoc scripts (scratchpad or repo) during a run: usage analysis, benchmark
reading and `assert_usage.py` belong in a separate session.

**Rule 1a — independent accept gate.** On every translator return (ASSIGNMENT, RETRY,
REWORK) whose flags pass prompts §Acceptance, run before `manifest_status.py translated`:
`./venv/bin/python .claude/skills/translating/scripts/compare-structure.py --source books/<id>/chunks/<CHUNK>.md --translated books/<id>/translated/<CHUNK>.md --ignore-boundary >/dev/null; echo $?`
Non-zero → RETRY to the owner (counts as the one RETRY). Use only the exit code;
never read the output. `--ignore-boundary` keeps the accepted residual page-marker
mismatch (prompts §Acceptance) from failing the gate.

**Rule 2 — budgets** (soft, defined in agent defs): translator ≤40 Bash per message,
editor ≤60 per batch. An agent reporting a breach in `notes` → log it in the batch
report; repeat breaches across batches → surface to the user.

**Rule 3 — usage in manifest.** After each batch, write per-chunk `usage` from
`check_agent_context.py --subagents --json` totals, matched by row `role` == ledger
`agentId`:

```json
"usage": {"input_tokens": N, "output_tokens": N, "cache_read_input_tokens": N,
          "cache_creation_input_tokens": N, "bash_calls": N}
```

Totals are cumulative per agent (a translator that also did REWORK counts both).
Write an agent's totals once, on its chunk; editor totals go on the batch report only.
Unavailable fields → omit; never guess. `usage` is never part of the status contract.

---

## Batch-End Usage Report to Human

**Trigger:** once per batch, when every chunk of the batch is `qa_passed` (a batch
with chunks still in `rework` has not triggered it). Not per chunk or per agent.

**Command:** `./venv/bin/python scripts/check_agent_context.py --subagents` (add
`--json` for fields). It reads `<session>/subagents/*.jsonl` for the current session.
Never `--active`/`--recent` (miss subagents) or a hand-built `$CLAUDE_SESSION_ID`.

Rows: `role` = ledger `agentId` → chunk / batch id.

**Output:** one markdown table in chat:

| Agent | Chunk | API calls | Input tok | Output tok | Cache read | Cache create | Context tok | Util% | Cost $ |
|---|---|---|---|---|---|---|---|---|---|

- Agent = `agent_type`; Chunk = ledger chunk (editor: batch id).
- Input/Output = `total_input_tokens`/`total_output_tokens`; Cache read/create =
  `total_cache_read_tokens`/`total_cache_create_tokens` (create is the costly part:
  1h-TTL write); Context = `max_context_tokens`; Util% = `utilization_pct`.
- Cost $ = the script's Sonnet-priced column; copy it, never compute. Keep its `main
  (session)` row (session to date). **TOTAL** row = the script's; add `$/chunk` = TOTAL
  $ ÷ chunks qa_passed this session. Missing field → `—`, never guessed. Call out any `status: warning`/`full` agent below the table.
- Below the table: compile WARN lines, budget breaches, `needs_decision` for chunks
  outside the verdict set, `promotion_candidates`, tooling notes filed.

**Fail-open:** script fails → print `usage report unavailable: <reason>` and continue.
No rows → state `unmapped sessions: N`; never silently drop an agent. This report is
additional to the manifest `usage` block and the TSV line.

---

## Editor Rules

- Exactly **one editor per batch**; never parallel within a batch.
- **Same editor re-reviews every rework** of the batch via `SendMessage` RE-REVIEW
  (prompts §RE-REVIEW). Reworks accepted while it is busy are merged into ONE
  RE-REVIEW. Never re-assign a different editor mid-batch (term/voice coherence). An
  idle-expired cache just costs a rewrite; accept it.
- Run `extract_term_map.py` before every editor message (BATCH, each RE-REVIEW, a
  replacement editor's batch). The editor never runs it. For RE-REVIEW, run
  `shasum books/<id>/style/_terms_compact.md` before and after it and send
  `Terms: changed|unchanged` (prompts §RE-REVIEW).
- The editor writes each verdict to `books/<id>/review/<batch-id>.r<N>.json` (next free N)
  and returns it as `verdict_path`; REWORK messages carry only that path, copied verbatim
  (prompts §REWORK).
- **RE-REVIEW return:** `chunks` holds exactly the re-reviewed chunks; apply only keys
  present. Findings in other chunks arrive as `needs_decision` tagged with that chunk →
  batch report only, never auto-reopened.
- Verdicts are per chunk.
- **Tooling notes (D25):** after every editor return, append each `notes` line starting
  `kind: tooling:` to `logs/qa_issues.txt` as `<YYYY-MM-DD> <id> <chunk> <text>`. Never
  to `corrections.md`.
- **Death:** an editor that dies (any terminal error, e.g. `API Error: 400 ... not
  accessible`) is never resumed. Spawn a fresh editor with the BATCH message re-issuing
  every chunk still in `review`; its budget starts at 0.

---

## Rework Rules

- `needs-fix` chunk → `rework` → `SendMessage` REWORK to its **owning translator**
  (owner = `agentId` of the LATEST ledger line with that chunk and `kind=translator`).
- Accept per prompts §Acceptance (REWORK). Then `translated → review`,
  `extract_term_map.py`, RE-REVIEW to the same batch editor.
- Owner dead → spawn a fresh translator with the REWORK message as its prompt; append
  a ledger line (it becomes the owner).
- Failed acceptance → one RETRY (`RETRY: <CHUNK> <reason>`, REWORK JSON expected).
  Second failure → halt + escalate.
- Not allowed: one shared rework agent per batch.

---

## Term Logging

1. After each translator return is accepted, walk its `candidate_terms`.
2. Accept only from returns with all three `validation` flags true.
3. Log one at a time: `log_terms.py "term | translation | context | <CHUNK>"`
   (idempotent; duplicates skipped).
4. Reject proper nouns, single everyday words, idioms and one-off puns. Never hand-edit
   `new_terms.txt`.
5. Then run `extract_term_map.py` once for the batch (writes `term_map.json` and
   `_terms_compact.md` incl. `## Drift`). Never before terms are logged.
6. The chunk holding the TOC (`# Contents`): also log every chapter title from its TOC,
   `"<EN title> | <VI title> | chapter title | <CHUNK>"`, so later translators render
   the `# N. …` headings with the same words (translator self-check covers headings).

---

## Term Decisions (never a pause)

Editor `needs_decision` entries of kind `term-drift` carry `recommended`. The editor's
recommendation is the default; apply it and continue, then record it for the human:
- term not logged → `log_terms.py "term | <recommended> | context | <CHUNK>"`;
- logged with another rendering → `log_terms.py --replace-translation "<term>" "<recommended>"`;
- a logged entry misapplied to ordinary usage (generic word, idiom) → `log_terms.py --remove-term "<term>"`.
Then `extract_term_map.py`, and the REWORK/RE-REVIEW proceeds as usual. Append one line
per decision to `logs/term_decisions.txt`: `<YYYY-MM-DD> <id> <CHUNK> <term> -> <rendering> (editor default)`.
List them under the batch usage table. The human may override later with the same
script calls; a change then goes through a normal REWORK.
A drift entry with no `recommended` → pick the form already used most often in
`qa_passed` chunks, and record it the same way.

---

## Book Close (all chunks `qa_passed`)

Run `./venv/bin/python scripts/utils/validate_toc.py --book <id>` before the final report.
- `TOC entry has no target` / `TOC wording differs from heading` → human-findings REWORK
  (`review/human_<CHUNK>.r0.json`) of the **TOC chunk**: headings are canonical, the TOC
  is aligned to them. A missing front block traces to the source → report, human fixes.
- Same editor re-reviews; re-run the check; clean → final report.

---

## Halt Rules

Stop when: every chunk is `qa_passed` and Book Close is clean; the user stops; or an unrecoverable error —
pre-condition failure, `compile_knowledge.py` exit 1/3, missing role snapshot or
`_terms_compact.md`, `context_missing` from an agent, malformed manifest, two
validation failures on the same chunk, `log_terms.py`/`extract_term_map.py` failing
twice in a row.

On halt report: final state per chunk, follow-ups and why, promotion candidates.

---

## Failure Recovery

Dead agents are never resumed; recovery is always a fresh spawn.

| Failure | Action |
|---|---|
| Translator validation fail (1st) | RETRY to same agent; dead → fresh spawn with ASSIGNMENT |
| Translator validation fail (2nd, same chunk) | Halt + escalate; chunk stays/returns `pending` per user |
| Rework acceptance fail (1st) | RETRY to owner; dead → fresh spawn with REWORK |
| Rework acceptance fail (2nd) | Halt + escalate |
| `context_missing` from any agent | HALT, report missing path (rerun session start) |
| Editor reports missing source/VI | Halt + escalate; never invent content |
| `log_terms.py` rejects a term | Skip, note in batch report |
| Translator declines (`error: declined`) | One fresh spawn, same ASSIGNMENT; 2nd decline → stays `pending`, report, continue batch |
| `extract_term_map.py` fails | Halt; never message the editor with a stale term list |
| Agent crash mid-batch | One fresh respawn (translator: same message; editor: BATCH with chunks in `review`); 2nd crash → halt |

Never retry twice.

---

## Manifest Schema (read/write contract)

This skill writes only:

- `chunks[i].status` ∈ `{pending, translated, review, rework, qa_passed}`
- `chunks[i].status_history` — append `{status, at}`
- `chunks[i].usage` — optional, additive (Rule 3)
- top-level `statistics`, `last_updated` — recomputed by `manifest_status.py`

All other fields (`book_id`, `total_chunks`, `category`, `category_template`,
`style_guide`, `total_words`, `chunks[i].id/source/translated/pages/word_count`) are
read-only; if wrong, escalate.

---

## Logging

**Batch TSV** — one TAB-separated line per batch, append-only, `logs/book-translating.tsv`:

```
batch_id  started_at  finished_at  chunks  pass  needs_fix  errors  book_id  bash_calls_total
```

**agentId ledger** — `logs/book-translating.agents.tsv`, append-only, 3 columns:

```
agentId<TAB>chunk_or_batch<TAB>kind
```

Append right after every spawn, incl. retry/death respawns (translator → chunk id,
editor → batch id). It is the only agent→chunk map; never keep it in memory only. Agent → chunks = all lines for that
agentId; owner of a chunk = latest `translator` line for it. SendMessage follow-ups
add no line.

---

## Compaction Recovery

Runs up to `--max-batches` (default 5) may auto-compact main (~167K); accepted.
- **Batch notes:** at each batch close append one line to `logs/batch-notes.txt`:
  `<batch-id> <YYYY-MM-DD> pass=N rounds=rN open: <needs_decision/WARN/term decisions, or none>`.
- **After a compaction** (or any doubt): rebuild state from disk only - `manifest.json`
  statuses, the ledger (owners, batch editor), the batch's latest `review/<batch-id>.r<N>.json`,
  `logs/batch-notes.txt`. Never trust recalled agentIds or verdicts; never re-spawn a
  live owner or editor found in the ledger.

---

## Verification Reminders

- ≤5 translators alive at once; 1 editor per batch; discipline D1–D5 (SKILL.md) first.
