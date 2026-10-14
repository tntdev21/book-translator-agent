# Subagent Message Templates

Assignment messages only. Procedure, Step 0 reads, forbidden reads/writes, budgets,
RE-REVIEW scope and return JSON live in `.claude/agents/translator.md` and
`.claude/agents/editor.md`; this file refers to return fields by name only.
Never paste knowledge, chunk text or skill files into a message.

Placeholders: `<id>` book id, `<CHUNK>` e.g. `chunk_027`, `<batch-id>` e.g.
`batch_027-029`. Line 1 is always `Book: <id>`. Edit nothing else.

## Spawn rules

- Agent tool, no `name` (a name wraps the prompt per agent and breaks sibling cache).
- Translator: `subagent_type: translator`, `description: "translator"` (fixed literal).
- Editor: `subagent_type: editor`, `description: "editor"` (fixed literal).
- All N translators of a batch in ONE message, same template, only `<CHUNK>` differs.
- Record each `agentId` in the ledger immediately (runbook §Logging).
- Follow-ups (REWORK, RETRY, RE-REVIEW) go by `SendMessage` to the recorded `agentId`.
  A dead agent is never resumed: spawn a fresh one with the same message as its prompt.

## ASSIGNMENT (translator spawn prompt)

```
Book: <id>
ASSIGNMENT: <CHUNK>
```

## RETRY (SendMessage, same translator)

```
Book: <id>
RETRY: <CHUNK> <reason: failed validation fields / missing addressed entries / unjustified regressions>
```

## BATCH (editor spawn prompt)

```
Book: <id>
BATCH: <batch-id>
Chunks: <CHUNK_A>, <CHUNK_B>, <CHUNK_C>
Neighbours: <prev> (before, <N> lines), <next> (after)
```

`<prev>` = chunk before the first listed chunk, `<next>` = chunk after the last.
`<N>` = `wc -l < books/<id>/translated/<prev>.md` (one Bash call). Either side `none`
when that chunk has no translated file (or does not exist).

## REWORK (SendMessage, owning translator)

```
Book: <id>
REWORK: <CHUNK>
Findings: books/<id>/review/<batch-id>.r<N>.json
```

`Findings:` = `verdict_path` of the editor return that set `needs-fix`, copied verbatim
(never computed). Never copy or paraphrase findings into the message (≤200 chars).
The translator's REWORK return must give `lines` on every `addressed` entry.

## RE-REVIEW (SendMessage, same batch editor)

```
Book: <id>
RE-REVIEW: <batch-id>
Chunks: <CHUNK_X>[, <CHUNK_Y>]
Neighbours: <prev> (before, <N> lines), <next> (after)
Terms: changed|unchanged
<CHUNK_X>: {"addressed": [...], "regressions": [...]}
```

`Chunks:` = every accepted rework currently queued (merge into one message).
Neighbours computed as in BATCH, around the named chunks. One JSON line per chunk,
copied verbatim from that translator's REWORK return (`addressed[].lines` included).
`Terms:` = `shasum _terms_compact.md` before vs after this round's `extract_term_map.py`.

## Acceptance — translator return

Accept only if `validation.paragraphs_match`, `validation.fix_py_clean` and
`validation.glossary_ok` are all true (a residual page-marker boundary mismatch is
reported in `notes` with flags left true — accept it, surface the note).
REWORK return additionally: every editor finding has an `addressed` entry, and
`regressions` is empty or each entry is justified.
`error: context_missing` → HALT batch, report the `missing` path.
`error: declined` (or no file and a refusal in `notes`) → one fresh spawn with the same
ASSIGNMENT (never RETRY the declining agent). Second decline → chunk stays `pending`,
note it in the batch report, continue the batch without it (not a halt).
Fail → one RETRY to the same agent (dead → fresh spawn with the original ASSIGNMENT/REWORK
message unchanged). Second failure on the same chunk → halt + escalate.
A REWORK that rejects a `needs_decision` finding → lift the chunk back to `review` anyway;
the RE-REVIEW line carries the translator's reason and the editor's verdict is final.
Never pause for the user over term or wording choices (runbook §Term Decisions).

## Term acceptance

Only from accepted returns with all validation flags true. For each `candidate_terms`
entry that is not a proper noun:
`BOOK_ID=<id> ./venv/bin/python scripts/log_terms.py "term | translation | context | <CHUNK>"`
(one call per term; the script skips terms already in new_terms.txt or glossary.csv).
Reject (do not log): single everyday words, idioms, and one-off puns/wordplay - the
validator flags every later occurrence of a logged term, so a generic word poisons
`glossary_ok` in later chunks.

## Verdict handling — editor return

- `chunks` key `pass` → `qa_passed`; `needs-fix` → `rework` → REWORK.
  Verdicts are independent per chunk.
- Apply only keys present in `chunks`; absent keys keep state; a key not in `review`
  is logged and ignored.
- `needs_decision` for chunks outside `chunks` (seams, passed chunks) → batch report
  only; never auto-reopen.
- `promotion_candidates` → batch report; a human promotes.
- `notes` lines starting `kind: tooling:` → append to `logs/qa_issues.txt` as
  `<YYYY-MM-DD> <id> <chunk> <text>`.
- `error: context_missing` → HALT, report.
