# Translation Quality Checklist (Layer 1 — Rule Card)

## Severity Levels
- **CRITICAL** — translation unusable, meaning lost. STOP and fix.
  - Untranslated segments, missing chapters, wrong character names, source blocks merged/split.
- **IMPORTANT** — reduces quality, confuses reader. Fix before release.
  - Inconsistent terminology, tone breaks, formatting errors, lost hedges.
- **NICE** — polish. Optional.

## During Translation (per chunk)
### Content
- [ ] CRITICAL — Source block count matches exactly; headings/lists/dialogue/page markers each retain corresponding blocks.
- [ ] CRITICAL — Each `<!-- Page N -->` boundary matches the source exactly (standalone ↔ standalone, inline ↔ inline).
- [ ] CRITICAL — No content omitted (cross-check proper nouns, key phrases).
- [ ] CRITICAL — No content added (translation only, no explanatory additions).
- [ ] Heading hierarchy preserved (`#` → `##` → `###`); numbering & lists preserved exactly.
- [ ] Every hedge preserved with matching strength; conditionals stay conditional.

### Consistency
- [ ] CRITICAL — Character and place names consistent (`John Smith` always, never `Smith` alone without context).
- [ ] CRITICAL — No two distinct EN terms collapsed into one VI term; no new term rendered two ways.
- [ ] Glossary terms used correctly; acronyms glossed at first mention only. Recurring phrases handled identically.
- [ ] Tone/voice consistent throughout chunk.

### Formatting
- [ ] CRITICAL — Dash policy: prose ` - `, dialogue `- `, numeric ranges `10–20`, compounds unchanged; no em-dashes (`—`).
- [ ] Quotation marks straight double `" "`; single space after punctuation.
- [ ] Footnote/endnote references and special markers (bold, italics, code blocks) preserved.

## Post-Translation (final validation)
### Structural & Completeness
- [ ] CRITICAL — Block count matches source; all chapters/sections present, no orphan headings.
- [ ] CRITICAL — No untranslated segments or leftover source text (except intentional quoted phrases); all proper nouns present.
- [ ] No placeholder text; all numbers preserved. TOC valid; breaks where expected.

### Terminology, Style & Formatting (global)
- [ ] CRITICAL — Glossary terms, names consistent across document; no term rendered two ways across chunks. Brands kept original.
- [ ] CRITICAL — Voice consistent. Tone matches original (serious stays serious, humour stays humorous).
- [ ] Register fits content; cultural references adapted, not literal; pacing and idioms natural.
- [ ] Numbers `1.000,99`, dates DD/MM/YYYY, quotes and dashes consistent; no double spaces.

### Readability
- [ ] Sentence length varies; no run-on sentences (one-breath test). Transitions flow naturally.
- [ ] No unnatural literal VI; grammar correct; native-speaker naturalness.

## Automated Checks (script-verifiable)
- [ ] `fix.py` / `--check-only` clean: sentence breaks, dashes, person-name capitalization, CJK corruption.
- [ ] UTF-8, LF line endings. `validate_toc.py` passes; heading levels ordered, no empty headings.
- [ ] Word count ratio source:target 0.8–1.2. Block count equals source.

## Manual Review Checks (nuance automation can't catch)
- [ ] Comprehension: unfamiliar reader follows; pronoun antecedents clear.
- [ ] **Random sampling**: 5 paragraphs at different positions. Accuracy ≥95%; below → escalate.
- [ ] **Terminology spot check**: 10 random glossary terms verified consistent (>95% reuse).
- [ ] Character voice distinct; dialogue natural, punctuation correct.
- [ ] Cultural references, humour, puns adapted, not explained. Metaphors work; passive voice evaluated; history accurate.

## Error Categories
- **Accuracy**: mistranslation, omission, addition, wrong terminology.
- **Fluency**: grammar mistakes, unnatural phrasing, awkward structure.
- **Consistency**: same term multiple ways, name spelling drift, tone breaks.
- **Formatting**: broken dashes/punctuation, incorrect spacing, heading errors.
