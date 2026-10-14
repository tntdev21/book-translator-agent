---
name: editing
description: Review a Vietnamese translation against its English source and report what is wrong (mistranslations, awkward phrasing, term drift) while auto-fixing only unambiguous typos. Use after translating chunks, before export. Reports to a human; does not rewrite the translation. Spawns the `editor` agent.
user-invocable: true
---

# Editing

Review procedure, auto-fix list, passes, corrections format and JSON return live in
the `editor` agent (`.claude/agents/editor.md`). This skill is the entry point.

## When to Use

- Chunks are translated and need review before export
- Terms may have drifted between chunks translated in different sessions
- A reviewer asks "is this translation actually right?"

Do not use it to translate or rewrite.

## The Governing Rule

> **Fix only what cannot change meaning. Report everything else.**

| Response | When | Who acts |
|---|---|---|
| **Auto-fix** | The fix cannot change meaning | Editor |
| **Report** | The fix might change meaning | Human decides, translator fixes |
| **Escalate** | The problem recurs across books | Human decides, Layer 2/1 |

The editor proposes; a human promotes. Never edit Layer 1/2 from review.

## Standalone Usage

Prerequisites, run before spawning:

```bash
./venv/bin/python scripts/compile_knowledge.py --book <id>   # only if _editor_snapshot.md is missing
./venv/bin/python scripts/extract_term_map.py                # always; refreshes _terms_compact.md
```

Spawn exactly ONE `editor` agent for the whole batch. Prompt:

```
Book: <id>
BATCH: <batch-id>
Chunks: chunk_A, chunk_B
Neighbours: <prev> (before, <N> lines), <next> (after)
```

`<N>` = line count of the previous neighbour's translated file. Either side may be
`none`. Re-review after rework, one prompt per batch:

```
Book: <id>
RE-REVIEW: <batch-id>
Chunks: chunk_A
Neighbours: <prev> (before, <N> lines), <next> (after)
```

followed by each translator's `addressed` / `regressions` JSON.

Manifest: coordinator moves records `translated → review`, then `qa_passed | rework`;
rework → owning translator → same editor via RE-REVIEW; never `qa_passed` without
re-review (CLAUDE.md §4).

The agent returns JSON: per-chunk `pass | needs-fix`, auto-fixes, decisions needed,
promotion candidates. Render it for the human as a short report (auto-fixed table,
needs-decision table, verdict per chunk). Lines in `notes` marked `kind: tooling`
go to `logs/qa_issues.txt`, not `corrections.md`.

## Writing to corrections.md

`books/<id>/style/corrections.md` is read by every later translator. The editor agent
appends entries per its def. If a human or coordinator appends by hand, first confirm the
rule is not already in the compiled snapshot or an existing entry.

## Checklist

- [ ] `extract_term_map.py` run before the editor started
- [ ] One editor for the whole batch
- [ ] Every finding cites location, source text, translated text
- [ ] New corrections checked against snapshot and existing entries
- [ ] Promotion candidates reported, not applied
- [ ] Verdict per chunk

> The editor's value is in what it refuses to change.
