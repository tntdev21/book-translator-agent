# Universal Translation Principles (Layer 1 — Rule Card)

**Precedence (low → high):** Layer 1 → Layer 2 → Layer 3 (book). Higher layer overrides lower on conflict.

## Core Principle
- **Accuracy AND naturalness** are the default goal. Sacrifice one only when the other is critical.
- Translate **concepts/meaning**, not word-for-word substitutions.
- **Preserve author voice** — register, stance, hedging, humour, self-awareness.
- **Preserve structure exactly**: blank-line-delimited source blocks, headings, lists, dialogue, page markers all keep their corresponding blocks. Do not merge or split paragraphs for style.
- **Blank-line block preservation is non-negotiable**: count of source blocks must equal count of translated blocks.

## Equivalence Modes
- **Formal equivalence** — source-oriented: keep structure, terminology exact. Use for technical/legal/academic.
- **Dynamic equivalence** — target-oriented: natural target expression, same effect. Use for literary/marketing.
- Default to **dynamic equivalence**; switch to formal only when source is technical, legal, or where foreignness is intentional. Target-oriented never means losing source meaning.

## Epistemic Register
- Preserve **every hedge** in the source. Modals (`may/might/could/would/should/must`), adverbs (`probably/possibly/arguably/presumably/surely`) all carry meaning.
- **Never flatten a hedge to bare assertion.** Match claim strength exactly: `có thể` ≠ `có khả năng` ≠ `nhiều khả năng` ≠ `chắc chắn`.
- Conditional obligations (`would have to`, `would need to`) → `sẽ phải` / `cần phải`. Conditional, not present-tense.

## Glossary Discipline
- **70% of translation quality issues are terminology-related.** High-impact terms first: branded, product, UI, domain jargon, frequently-mistranslated.
- **Glossary is a hard rule**: if a term is logged, use the logged rendering — even if you'd choose differently.
- **Report candidate new terms in your return JSON; never write `new_terms.txt` or the glossary** (the coordinator logs accepted terms).
- **First-mention gloss**: VN term + EN in parens (or vice versa), then VN only thereafter.
- Acronyms: Latin script after first mention; never spell out every time.
- **Consistency matrix per book**: list each acronym, full form, chunk where first defined.
- **Merge failures are worse than split failures**: two EN terms collapsed into one VI term silently changes meaning.

## Author Voice Preservation
- Preserve humour, irony, self-aware asides. These are **not filler**.
- Preserve the author's confidence level — do not over-soften with particles (`nhé`, `thôi`, `mà`).

## Cultural Adaptation Decision Tree
- TECHNICAL/LEGAL/ACADEMIC → formal equivalence
- INTENTIONALLY FOREIGN voice → preserve foreignness
- CULTURAL REFERENCES → importance check: stylistic → preserve+explain; practical → adapt; idiom/humor → adapt/transcreate
- PUBLIC-FACING/reader engagement → dynamic equivalence
- DEFAULT → balanced: accuracy + naturalness

## Pitfalls (each is a correctness bug)
- **False cognates**: research before assuming.
- **Over-literal translation**: think in concepts, not words.
- **Idiomatic expression failures**: literal destroys meaning.
- **Missing context**: same word means different things in different situations.
- **Tone & voice loss**: accuracy without personality.
- **Adding explanation the author didn't write**: misrepresents pacing, accumulates, bloat, indistinguishable from author prose.
- **Importing a distinction the author didn't make**: silently upgrading author's precision.

## Tone Rules
- **Register consistency**: formal throughout OR mixed deliberately. Never accidental mixing.
- Match register to source: conversational source → conversational translation; formal source → formal translation.
- Dialogue registers can differ from narrative registers — distinguish by character.

## Structure Preservation
- **Heading hierarchy** (`# → ## → ###`) preserved exactly. Do not promote/demote.
- **Numbered sub-headings** ("1.3 The Hedging Problem") keep their numbers.
- **Lists** only where source has lists. Do not convert flowing sentence → list.
- **List-item length**: if source items are full sentences, keep full sentences.
- **Inline enumerations**: pick `thứ nhất… thứ hai… thứ ba…` OR `đầu tiên… tiếp theo… cuối cùng…`, do not mix.
- **Recurring headings** must be worded identically each time so reader recognises callback.
- **Page-marker boundary** — each `<!-- Page N -->` is a corresponding block and keeps the exact blank-line relationship the source gives it: standalone in source (blank line before and after) → standalone; inline in source (between two prose lines) → inline. No blanket "blank line around every marker" rule: extraction often cuts a sentence at a page turn, so an inline marker is correct, not an error to normalize.
