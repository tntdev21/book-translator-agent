---
name: deriving-dna
user-invocable: true
description: Derive translation DNA from a parallel EN↔VI sample — an author-voice profile for one book, plus evidence-backed genre rules for the shared category template. Use when a book has a sample/ directory with a published translation pair and needs its Layer-3 style guide, or when the Layer-2 category template needs evidence from a real published pair.
---

# Deriving DNA

Turn a published EN↔VI translation pair into translation rules that later
chunks and later books can be held to.

---

## When to Use

Use this skill when:

- A book has `books/<id>/samples/<name>/` containing a published translation
  pair (`en.md` + `vi.md`) and needs its Layer-3 style guide
- A Layer-2 category template needs evidence backing instead of assertion
- A reviewer asks "why is this the rule?" and the honest answer is currently
  "it seemed right"

Do **not** use it to translate. Samples are raw material for rules, never
translation input.

---

## What "DNA" Means Here

Three outputs, three purposes. Conflating their evidence, scope, and operating
roles is the main mistake this skill exists to prevent.

| | Author DNA | Genre DNA | Translation style guide |
|---|---|---|---|
| **Question** | How does *this author* sound? | How does *this genre* read in Vietnamese? | How should translators apply the available book evidence? |
| **Destination** | `books/<id>/dna.md` | `.claude/skills/translating/categories/<category>--dna-<sample>.md` | `books/<id>/style/translation_style_guide.md` |
| **Scope** | One book, one author | Every book in the category | One book, translator-facing |
| **Lifetime** | Until superseded by a better sample | Accumulates across samples | Updated whenever book DNA is re-derived |
| **Layer** | Layer 3 evidence | Layer 2 evidence | Layer 3 operating guide |

Author DNA goes in **one** file per book (`dna.md`), merging what every sample
shows. Genre DNA goes in a **separate** file per sample, never merged into the
category template directly — provenance has to survive. The style guide is a
concise application layer: it points back to the evidence and must never turn a
provisional observation into a confirmed authorial rule.

### Why samples usually come from a different author

The strongest sample is a translation of *the same author's earlier book*: same
voice, same vocabulary, same publisher conventions. When that exists, author DNA
is high-confidence.

When it does not — as with Brian Christian, who has no Vietnamese translation —
a **comparable** book stands in. It supplies reliable genre DNA and only a
*provisional* author voice. Say which case you are in, explicitly, in both
outputs. A provisional voice passed off as measured is worse than no voice.

---

## Inputs

```
books/<id>/samples/
└── <sample-name>/
    ├── en.pdf | en.epub | en.txt     # publisher original (keep it)
    ├── vi.pdf | vi.epub | vi.txt     # publisher original (keep it)
    ├── en.md                          # extracted
    └── vi.md                          # extracted
```

Extract with the normal pipeline:

```bash
python scripts/extract.py books/<id>/samples/<name>/en.epub books/<id>/samples/<name>/en.md
python scripts/extract.py books/<id>/samples/<name>/vi.epub books/<id>/samples/<name>/vi.md
```

---

## Workflow

### Step 1: Determine the comparison unit

**Compare at chapter level, not page level.** A publisher's Vietnamese edition
breaks chapters differently from the English original — different chapter
count, different boundaries, sometimes a merged or split chapter. Aligning by
page number produces confident nonsense.

```bash
# Find the chapter boundaries in each
grep -n "^#\{1,2\} \|^Chương \|^CHƯƠNG \|^Phần " books/<id>/samples/<name>/en.md
grep -n "^#\{1,2\} \|^Chương \|^CHƯƠNG \|^Phần " books/<id>/samples/<name>/vi.md
```

If chapter markers are absent in the Vietnamese edition, use the table of
contents, then locate each chapter's opening sentence in `vi.md`. Record the
mapping — it is the scaffold every later step hangs on.

### Step 2: Read pairs, not files

Read one chapter's EN and its VI counterpart **together**. Reading all of `en.md`
then all of `vi.md` produces impressions you cannot cite.

For each chapter, collect observations under four heads:

| Head | What to note |
|---|---|
| **Register** | Formality, first-person stance, hedging vocabulary and *how often* |
| **Terminology** | Which English terms stay English, which get translated, how first mention is glossed |
| **Structure** | Sentence splitting, paragraph joins, how em-dashes and lists are handled |
| **Voice** | Rhythm, repetition tolerated or avoided, directness |

### Step 3: Demand evidence for every rule

This is the constraint the whole skill rests on.

> Every rule you write must be backed by a real EN↔VI sentence pair you can
> quote. No pair, no rule.

A rule that feels true but has no pair is a guess wearing a rule's clothes.
Write it down as an **open question** instead.

Good:

```markdown
### Hedging: `có thể` for `may` / `might` / `can`

EN (p. 34): "It may take centuries."
VI (Ch. 1): "Quá trình đó có thể mất hàng thế kỷ."

EN (p. 51): "Such a system might not remain aligned."
VI (Ch. 2): "Một hệ thống như vậy có thể sẽ không còn duy trì được sự căn chỉnh."
```

Bad — no pair, untestable:

```markdown
### Hedging

Vietnamese scientific writing uses `có thể` to soften claims, which reads more
naturally than a bare assertion.
```

**Also count, don't estimate.** If you claim a term appears "often", count it:

```bash
grep -o "có thể" books/<id>/samples/<name>/vi.md | wc -l
```

A measured number ("`có thể` occurs 412 times in 168k words, ≈2.5 per 1,000")
is falsifiable. "Often" is not.

### Step 4: Write the three outputs

#### Evidence authority and guide guardrails

- The current `samples/<name>/en.md` and `vi.md` pair is the authority for every
  quoted EN↔VI example and every count.
- `books/<id>/book.yaml`, the current book/category DNA, the base category
  template, and formatting rules are the authority for project context and
  precedence.
- Historical plans and reports may inspire the *organization* of the guide only.
  They are never evidence for pairs, counts, terminology, source paths, or rules.
- Label every guide decision as **[project house rule]**, **[category convention]**,
  **[parallel evidence]**, or **[open/provisional]**. A stand-in author's evidence
  remains provisional and must name that limitation.
- Do not invent citations or frequency claims. Pairless observations belong in
  Open Questions. One sample cannot establish a category rule without human review.

#### Mandatory dedup before writing (genre DNA and `dna.md`)

Do this after drafting candidates and BEFORE writing either file. Parent layers
already reach the translator; restating them only adds size and drift risk.

1. Load the parent layers: the L1 cards (`references/*.md`), the category card
   `categories/<category>.md`, and (for `dna.md`) any existing
   `categories/<category>--dna-*.md`.
2. Classify every candidate rule against them:

   | Class | Meaning | Write? |
   |---|---|---|
   | `new` | no parent states it | yes |
   | `refines <parent>` | narrows or adds evidence to a parent rule | yes, heading suffix `(refines <parent>)` |
   | `override <parent>` | contradicts a parent rule, with pair evidence | yes, heading suffix `(override <parent>)` |
   | `duplicate` | a parent already states it | no |

3. Write only `new`, `refines`, `override`. List the dropped duplicates (rule and
   parent that covers it) in the final report.
4. Promotion: when a human promotes a rule into the category card, delete it from the
   genre DNA file and leave a provenance line in the card.

Keep these section names exact; the knowledge compiler strips them by heading prefix
(`Open Questions` from the translator snapshot only): `Samples Used`, `Open Questions`, `Promotion candidates`.

**Author DNA → `books/<id>/dna.md`**

```markdown
# Author DNA: <Author>

Derived from <N> sample(s). See `samples/` for the pairs.

**Confidence:** measured | provisional
<!-- "provisional" when the sample is a stand-in author, not this author -->

## Samples Used

| Sample | Pair | Confidence | Why |
|---|---|---|---|
| <sample-id> | <Author> EN↔VI | provisional | stand-in author; genre match |

## Voice

<rules, each with an EN↔VI pair>

## Terminology

<rules, each with a pair and a count where it matters>

## Structure

<rules, each with a pair>

## Open Questions

<observations with no supporting pair — explicitly marked as unresolved>
```

**Genre DNA → `.claude/skills/translating/categories/<category>--dna-<sample>.md`**

Same evidence discipline, but each rule also carries a **provenance line**:

```markdown
# Genre DNA: <category> — derived from <sample title>

**Source pair:** <Author>, *<Title>* (<year> EN) ↔ <publisher> (<year> VI)
**Derived:** 2026-09-29
**Scope:** rules that look like genre conventions, not this translator's habits

## <Rule>

EN: "<sentence>"
VI: "<sentence>"
**Count:** <n> occurrences in <m> words
**Generalises?** likely | uncertain — <why>
```

The `Generalises?` line matters. One translator's habit looks identical to a
genre convention until a second sample disagrees. Marking it keeps the
distinction alive.

**Translation style guide → `books/<id>/style/translation_style_guide.md`**

Create or update this required Layer-3 guide after writing `dna.md`. It is an
operational synthesis, not a third evidence store and not a replacement for
`dna.md`. Create `style/` when needed, but never overwrite `glossary.csv`,
`new_terms.txt`, or `corrections.md`.

Use this concise structure:

```markdown
# Translation Style Guide — <title>

## Scope, Evidence Status & Authority
## Tone & Voice
## Sentence Structure & Source Fidelity
## Terminology & Proper Nouns
## Formatting & Locale
## Examples / Decision Patterns
## Critical Don’ts
## Open Questions & Upgrade Path
## Translation Workflow & Per-Chunk Checklist
```

The guide must state the precedence: universal → base category → sorted category
DNA → book DNA → style guide/glossary → formatting rules → corrections. It must
name `dna.md` and category DNA as evidence sources, keep stand-in status visible,
and defer canonical structural punctuation to the formatting rules. Include only
rules traceable to the current DNA artifacts; cite at least one real pair for each
parallel-evidence rule and retain counts when frequency matters. Keep unresolved
or pairless observations under Open Questions. Do not copy facts, examples, counts,
terminology, or formatting from historical reports, and do not create a speculative
glossary.

### Step 5: Surface to Layer 2 — with a human decision

Do **not** edit `.claude/skills/translating/categories/<category>.md` yourself.
Write the genre DNA file, then report which rules look strong enough to promote
and why. A human decides.

The same logic as the term glossary: `non-fiction.md` is loaded by every
non-fiction book, so anything added to it silently becomes law everywhere.

---

## What This Skill Must Not Do

| Anti-pattern | Why it fails |
|---|---|
| Read `en.md` then `vi.md` | Impressions with no citable pair |
| Align by page number | Editions paginate differently — confident nonsense |
| Write a rule without a pair | Unfalsifiable; indistinguishable from a guess |
| Say "often" instead of counting | Not checkable, not comparable across samples |
| Edit the category template directly | One sample's habit becomes law for every book |
| Present stand-in DNA as measured | Downstream agents cannot tell which rules to trust |
| Restate a parent-layer rule | Duplicates bloat the compiled snapshot and can drift from the parent |

---

## Output Checklist

- [ ] Sample pairs extracted and the originals kept alongside
- [ ] Chapter mapping between editions recorded
- [ ] Every rule carries a real EN↔VI pair
- [ ] Frequency claims are counted, not estimated
- [ ] `dna.md` states confidence (measured vs provisional)
- [ ] Genre DNA written to its own file, not merged into the category template
- [ ] `Generalises?` marked on each genre rule
- [ ] Required `style/translation_style_guide.md` created or updated after `dna.md`
- [ ] Guide cites its current DNA evidence, labels authority/provisional status, and defers structural punctuation to formatting rules
- [ ] Dedup run against parent layers; every rule classed new/refines/override; dropped duplicates listed in the report
- [ ] Pairless observations listed as open questions, not rules
- [ ] Promotion candidates reported for human review

---

## Remember

> A rule without a citation is a guess.
> One sample is one data point — say so.
> The value of this skill is what it refuses to claim.
