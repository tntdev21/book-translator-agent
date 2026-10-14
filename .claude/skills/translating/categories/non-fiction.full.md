# Non-Fiction (Popular Science & Ideas) Translation Patterns
## English → Vietnamese Guide

**Version**: 1.0
**Created**: 2026-09-29
**Research Date Range**: 2024-2026
**Domain Focus**: Popular science, AI/technology, physics/cosmology, philosophy & ethics, big-questions non-fiction

---

## Executive Summary

Non-fiction of the "big questions" kind — Tegmark, Christian, Harari, Kahneman,
Dawkins — is **argumentative narrative prose**. The
author is not writing a manual or a reference table; they are building a case across
several hundred pages, and the reader is being walked through it step by step. This
changes what the translator must protect.

What separates this category from its neighbours:

| Neighbour | Its centre of gravity | Why non-fiction differs |
|---|---|---|
| `technical.md` | Imperative instructions, code, procedures | Non-fiction has almost no imperatives. It *asserts*, *qualifies*, and *argues*. |
| `self-help.md` | Second-person advice, actionable steps | Non-fiction addresses the reader as a fellow thinker, not a student to be instructed. |
| `literary.md` | Character, voice, imagery | Non-fiction has a narrator and a voice, but no invented characters; the "plot" is the argument. |
| `sci-fi.md` | Invented worlds, coined technology | Non-fiction writes about the real world under uncertainty — the hard part is *calibrating* claims, not inventing them. |

Five core challenges, in order of how much damage getting them wrong does:

1. **Epistemic register.** The single biggest failure mode. "Life *may* emerge", "this
   *would* require", "*if* current trends continue" are claims of carefully bounded
   strength. Flatten them into plain assertion — "sự sống sẽ xuất hiện" — and the
   translator has made the author say something the author deliberately did not say.
   In a book whose entire subject is what we do and don't know about the future, this
   is a correctness bug, not a style preference.
2. **Speculation vs. reported fact.** Thought experiments and scenarios (a lab that
   secretly builds a superintelligence, a future society run by AI) are *hypotheticals*. If the
   Vietnamese reads like reportage, readers take fiction for prediction.
3. **Multi-domain terminology.** One book spans AI/ML, cosmology, philosophy of mind,
   ethics, and mathematics. Each has its own Vietnamese conventions, and they must not
   fight each other across chapters.
4. **The author's stance.** First-person popular science — "As a biologist, I feel
   fortunate to have spent most of the past twenty years…" — is a
   deliberate move to establish credibility and companionship. It is not filler.
5. **Consistency across a long argument.** A term introduced in Chapter 1 and used in
   Chapter 7 must be the same term. Readers build a mental glossary as they go; drift
   breaks it.

**Terminology load**: expect roughly 10–25% of the text to be domain vocabulary
requiring a deliberate choice (keep English, translate, or gloss). Lower than a
technical manual, higher than a novel — but the terms are more *abstract*, and there
is often no settled Vietnamese equivalent.

**Primary evidence for this file**: a published Vietnamese translation of a
big-questions popular-science book, read against its English original. All examples
are `[constructed]`: written to illustrate the patterns observed in that pair, not
quoted from it. See §10 for sources and their limits.

---

## 1. Tone & Voice Framework

### 1.1 The Author as Narrator of an Argument

In non-fiction the author is a *character in their own book*: a physicist, a
philosopher, a journalist who went and looked. The Vietnamese needs to preserve that
positioning. Three things carry it:

- **Framing verbs of stance** — "I argue", "I suspect", "it seems to me", "we shall
  see". These are not hedges to be trimmed; they locate the claim.
- **The inclusive "we"** — "we physicists", "our Universe", "we still don't know".
  Vietnamese `chúng ta` (inclusive: you and I together) vs `chúng tôi` (exclusive:
  me and my group) is a real choice here, and popular science almost always wants
  `chúng ta`. See §6.1.
- **Register of address** — non-fiction rarely says "bạn" the way self-help does.
  The reader is a companion in inquiry, addressed as `chúng ta` (we) far more often
  than as `bạn` (you).

**`[constructed]`** — first-person credibility, and the inclusive "our":

> EN: "As a biologist, I feel fortunate to have spent most of the past twenty years
> working out how our cells keep time — and it's been an amazing journey of
> discovery."
>
> VI: "Là một nhà sinh học, tôi cảm thấy may mắn khi có thể dành phần lớn hai mươi
> năm qua để tìm hiểu cách tế bào của chúng ta đo đếm thời gian; đó quả là một hành
> trình khám phá tuyệt vời."

Note what the rendering does: `Là một nhà sinh học` (bare appositive, no
"with vai trò là…"), `tôi cảm thấy may mắn` (not `tôi thấy mình may mắn`), and the
em-dash becomes a semicolon. The sentence keeps its relaxed, confident rhythm rather
than becoming formal.

### 1.2 Epistemic Register: The Hedging Ladder

**This is the centrepiece of the category.** English marks claim strength with
modals and adverbs — *may / might / could / would / can / should / must / probably /
possibly / arguably / presumably / surely*. Vietnamese does not have a modal system,
so the strength of a claim is distributed across several mechanisms at once:

1. a lexical hedge (`có thể`, `có lẽ`, `dường như`, …),
2. an optional sentence particle (`… mà`, `… vậy`, `… đấy`, `… thôi`),
3. the choice of verb/tense-aspect marker (`sẽ` / `đang` / `đã` / bare),
4. and, importantly, **whether the hedge appears at all**.

The ladder, weakest to strongest:

| Strength | English marker | Vietnamese | Notes |
|---|---|---|---|
| Bare speculation | "could conceivably", "one might imagine" | `hoàn toàn có thể hình dung rằng`, `ta có thể tưởng tượng ra` | Signals a constructed possibility, not a claim. |
| Weak possibility | "might", "may", "could" | `có thể`, `có lẽ`, `biết đâu` | `có thể` is the workhorse. `biết đâu` adds "who knows" flavour — use sparingly. |
| Plausible | "plausibly", "likely" (weak) | `có khả năng`, `nhiều khả năng`, `dường như` | `có khả năng` = "there is a possibility"; `dường như` = "it appears that" (evidential, from observed signs). |
| Probable | "probably", "in all likelihood" | `nhiều khả năng`, `rất có thể`, `hầu như chắc chắn` | `nhiều khả năng` reads stronger than `có khả năng`. Do not collapse the two. |
| Presumption | "presumably", "presumably because" | `hẳn là`, `chắc hẳn`, `theo lẽ thường thì` | `hẳn là` carries an inference the author expects you to accept. |
| Near-certainty | "almost certainly", "surely" | `gần như chắc chắn`, `hẳn nhiên` | Reserve for genuine near-certainty. |
| Supposition (introducing a scenario) | "suppose that…", "imagine that…" | `giả sử rằng`, `giả sử`, `thử tưởng tượng rằng` | This is a *scenario opener*, not a probability claim. See §1.3. |
| Hypothetical framing | "by hypothesis", "on this hypothesis" | `theo giả thuyết`, `theo giả định` | Academic register; fine in a book with an academic author. |
| Obligation | "would have to", "would need to" | `sẽ phải`, `cần phải`, `ắt phải` | The `would`-future-of-obligation. Easy to miss: it is *conditional*, not present-tense. |
| Necessity | "must", "necessarily" | `phải`, `tất yếu` | Strongest rung. `tất yếu` is philosophical necessity — do not use for mere obligation. |
| Assertion | "is", "will be" | bare `là` / `sẽ là` | No hedge. Only when the author made no hedge. |

**Calibration cautions.**

- `có thể` is doing a lot of work and is the *default*. Do not upgrade it to
  `nhiều khả năng` for emphasis, and do not downgrade `nhiều khả năng` to `có thể`
  for smoothness. The difference is the author's confidence, not decoration.
- `dường như` is *evidential*: it means the speaker infers from evidence. Use it where
  English says "apparently", "it seems", "there appears to be". Do not use it for
  "might".
- English "can" is ambiguous between *possibility* ("it can happen") and *capability*
  ("it can process a billion tokens"). Vietnamese needs `có thể` for the first and
  `có khả năng`/`có thể làm được` for the second. Getting this wrong changes meaning.
- In a conditional, both the antecedent and the consequent usually carry a marker:
  "If X, then Y would be Z" → `Nếu X thì Y sẽ là Z`. Dropping the `sẽ` turns a
  hypothetical into a plain future prediction.

**`[constructed]`** — stacked hedges, and how to carry them:

> EN: "Perhaps we are the first minds in this galaxy to wonder where we came from.
> Perhaps others will arise millions of years after us — and perhaps whether they
> ever find a trace of us will depend on what we choose to leave behind on this
> small planet."
>
> VI: "Có lẽ chúng ta là những trí óc đầu tiên trong thiên hà này biết tự hỏi mình
> từ đâu đến. Có lẽ những trí óc khác sẽ xuất hiện sau ta hàng triệu năm – và có lẽ
> việc chúng có tìm thấy dấu vết của ta hay không sẽ phụ thuộc vào những gì ta chọn
> để lại trên hành tinh nhỏ bé này."

Three `Có lẽ` openings, each carrying `sẽ` inside. The rendering does *not* vary the hedge for variety's sake — the repeated `Có lẽ … sẽ …` is what makes
the passage read as sustained speculation rather than a series of predictions. Note
also that Vietnamese places `Có lẽ` clause-initially where English might put "maybe"
mid-clause.

**Hedge frequency in the parallel text** (counts over the full published Vietnamese
translation, ~770k characters — a useful sanity baseline):

| Vietnamese hedge | Occurrences | Approx. English source |
|---|---|---|
| `có thể` | 1177 | can / could / may / might / possibly |
| `có khả năng` | 120 | can (capability) / is capable of / there is a possibility |
| `có lẽ` | 61 | perhaps / maybe / I suspect |
| `dường như` | 53 | it seems / apparently / there appears to be |
| `giả sử` | 28 | suppose / imagine that |
| `hầu như` | 16 | almost / nearly / virtually |
| `nhiều khả năng` | 10 | probably / in all likelihood |
| `phần nào` | 9 | somewhat / to some extent |
| `theo tôi` | 8 | in my view / I think |
| `giả thuyết` | 7 | hypothesis / hypothetically |
| `rất có thể` | 1 | very likely / highly likely |

Two things to take from this. First, `có thể` dominates by an order of magnitude — it
is the default and the rest are deliberate escalations. Second, the strong forms
(`rất có thể`, `nhiều khả năng`) are *rare*: a translation that scatters them evenly
is mistaking emphasis for accuracy.

### 1.3 Speculation, Thought Experiment, and Scenario

The secret-lab story, the AI-run society of the future, the "if a superintelligence
escapes the box" sequences — these are not predictions and not reportage. They are
*scenarios*, devices for making an abstract argument concrete. Vietnamese has to
signal hypothetical status clearly, because the past-tense-and-definite-article
texture of the English narration can read as a historical account.

Techniques, in rough order of strength:

| Device | Vietnamese | Effect |
|---|---|---|
| Explicit scenario opener | `Giả sử rằng…`, `Hãy tưởng tượng rằng…`, `Thử hình dung…` | Marks everything that follows as hypothetical. |
| Conditional frame | `Nếu … thì … sẽ …` | Carries the hypothesis through the sentence. |
| Irrealis marker | `sẽ`, `ắt sẽ`, `hẳn sẽ` | Future-in-hypothesis. |
| Narrative present | bare verb, present time | Makes the scenario vivid without claiming it happened. |
| Explicit withdrawal | `Dĩ nhiên, đây chỉ là giả định…`, `Tất nhiên, kịch bản này…` | The author's "of course, this is just a thought experiment". |

**`[constructed]`** — a scenario opener that must not become reportage:

> EN: "Suppose that in 2040 a team trains a system that can write its own code."
>
> ❌ Flat: "Năm 2040, một nhóm đã huấn luyện một hệ thống có thể tự viết mã."
> — reads as history; `đã` plus a definite year turns the hypothesis into fact.
>
> ✅ Framed: "Giả sử rằng vào năm 2040, một nhóm nghiên cứu huấn luyện được một hệ
> thống có thể tự viết mã." — `Giả sử rằng` frames it; the bare verb avoids `đã`.

**`[constructed]`** — a scenario built at length:

> EN: "Suppose your navigation assistant has no goals of its own but will do whatever
> you ask, and you ask it to get you to the airport as fast as possible…"
>
> VI: "Giả sử trợ lý dẫn đường của bạn không có mục tiêu nào của riêng nó, nhưng sẽ
> làm bất cứ điều gì bạn yêu cầu, và bạn bảo nó đưa bạn ra sân bay nhanh nhất có
> thể…"

The `Giả sử` opener plus `sẽ` inside the clause is the whole mechanism. The scenario
unfolds in present/future narration, never slipping into `đã`.

**The withdrawal move.** Non-fiction authors regularly step out of a scenario to say
"of course, this is only an illustration". Do not smooth these away — they are how
the author keeps faith with the reader, and they are often the only thing separating
speculation from advocacy.

### 1.4 First-Person Popular Science

The first-person authorial voice does real work: it establishes why this person is
worth listening to, and it makes a large subject feel navigable.

**`[constructed]`**:

> EN: "As a biologist, I feel fortunate to have spent most of the past twenty years
> working out how our cells keep time — and it's been an amazing journey of
> discovery."
>
> VI: "Là một nhà sinh học, tôi cảm thấy may mắn khi có thể dành phần lớn hai mươi
> năm qua để tìm hiểu cách tế bào của chúng ta đo đếm thời gian; đó quả là một hành
> trình khám phá tuyệt vời."

Notice:
- `Là một nhà sinh học` keeps the credentials-first opening. Vietnamese has no article,
  so this is a bare appositive and works well.
- `tôi cảm thấy may mắn` — first person kept explicit. A translation that wrote
  `thật may mắn khi…` (impersonal) would be smoother but would drop the stance.
- `quả là` restores the mild self-deprecating warmth of "it's been an amazing
  journey". Without it the sentence is flat.
- `hành trình khám phá` for "journey of discovery" is the established collocation;
  do not invent `cuộc du hành của sự khám phá`.

**Pronoun policy for the authorial voice.** In non-fiction the author is `tôi`
(not `chúng tôi`, unless genuinely speaking for a team). The reader, jointly with the
author, is `chúng ta`. `chúng tôi` appears when the author means "the research
community I belong to" — "we physicists still don't know".

**`[constructed]`** — the exclusive/inclusive split:

> EN: "We neuroscientists still can't say exactly how our memories are stored."
>
> The `we neuroscientists` is exclusive-of-reader → `chúng tôi, những nhà thần kinh
> học, vẫn chưa thể nói chính xác ký ức của chúng ta được lưu trữ ra sao`.
>
> But `our memories` in the same sentence is inclusive → `của chúng ta`. A single sentence can require both pronouns, and that is correct.

### 1.5 Tone Consistency Across a Long Argument

Non-fiction books modulate tone deliberately: a rigorous chapter, then a lighter one
built on a thought experiment, then a sombre closing chapter on risk. The Vietnamese
register must follow that modulation rather than locking to one formality level.

A workable default register for this category:

- **Neutral-to-formal, but not bureaucratic.** Full Vietnamese sentences, standard
  connectives (`Tuy nhiên`, `Bởi vậy`, `Mặt khác`, `Nói cách khác`), no colloquial
  contractions.
- **Avoid administrative Vietnamese.** `nhằm mục đích`, `vấn đề nêu trên`,
  `tiến hành thực hiện` are the register of government documents and will make a
  physicist sound like a civil servant.
- **Keep the author's occasional informal register.** When the author writes "This is
  a big deal", the Vietnamese should be `Đây là chuyện lớn` or `Điều này có ý nghĩa
  lớn`, not `Đây là một vấn đề có tầm quan trọng đáng kể`.
- **Chapter-level tracking.** Before translating a chapter, note its register in the
  manifest's chunk notes so the next chunk can pick up where it left off.

---

## 2. Terminology Management Strategy

### 2.1 The Multi-Domain Terminology Problem

A single big-questions book typically ranges across four or five domains, each with
its own Vietnamese conventions:

| Domain | Example vocabulary | Typical handling |
|---|---|---|
| AI / ML | artificial general intelligence, deep learning, reinforcement learning, superintelligence, alignment | Mixed — acronyms kept, some terms translated, some kept English with a gloss |
| Physics / cosmology | Big Bang, dark energy, entropy, quantum, multiverse, 13.8 billion years | Mostly translated; established Vietnamese forms exist |
| Philosophy of mind | consciousness, qualia, intentionality, substrate, functionalism | Mixed — `ý thức` is settled, `qualia` usually kept |
| Ethics | utilitarianism, deontology, moral patient, trolley problem | Mostly translated; some kept as proper names of positions |
| Mathematics | exponent, logarithm, algorithm, computational complexity | Mostly translated |

The risk is not per-term correctness — it is *cross-domain inconsistency*: the same
English word meaning two things in two chapters, translated two different ways with
no signal to the reader that the meaning shifted (see §7.2).

### 2.2 When to Keep English (Untranslated)

Keep the English term when any of these hold:

1. **It is an acronym or a proper name of a field artifact.** `AI`, `AGI`, `ML`,
   `GPU`, `GPT`, `Transformer` (when naming the architecture). Vietnamese technical
   writing keeps these in Latin script.
2. **It names a specific hypothesis, effect, or thought experiment.** `the trolley
   problem`, `the Fermi paradox`, `the Turing test`, `the alignment problem`, and
   an author's own coined taxonomy. These are proper nouns of ideas.
3. **There is no settled Vietnamese equivalent and a translation would invent a
   false precision.** `qualia`, `alignment`, `robustness` in the AI sense. Usually
   keep English on first use with a Vietnamese gloss, then keep English.
4. **The author themselves is using it as a term of art and flags it.** If the
   English text says "what researchers call X", mirror that.
5. **It is a product, company, or institution name.** `OpenAI`, `DeepMind`, `Google
   DeepMind`, `AlphaGo`. Always Latin script.

**Observed in published translations** — names the author gives to a scenario's
actors (an AI, a fictional team) stay untranslated throughout, because they are
names, not common nouns. `AI` stays in Latin script.

### 2.3 When to Translate

Translate when:

1. **The Vietnamese equivalent is established and unambiguous.** `trí tuệ nhân tạo`
   for AI (though the acronym stays), `vũ trụ` for universe, `ý thức` for
   consciousness, `thuật toán` for algorithm, `học máy` for machine learning.
2. **The term is descriptive rather than a proper name.** "reinforcement learning"
   → `học tăng cường`; "natural language processing" → `xử lý ngôn ngữ tự nhiên`.
3. **Leaving it English would make the sentence unreadable for the intended
   audience.** A general Vietnamese reader of a popular-science book will not parse
   an English clause embedded mid-sentence.
4. **The author uses the term in passing, not as a defined term of art.** An English
   word that appears once and is never revisited should usually just be translated.

### 2.4 First-Mention Glossing

The standard pattern: on first mention, give the Vietnamese term followed by the
English in parentheses (or vice versa, depending on which is more likely to be
recognised); thereafter use only the Vietnamese term.

**`[constructed]`**:

> "trí tuệ tổng quát nhân tạo (artificial general intelligence, AGI)" on first
> mention → thereafter `AGI` or `trí tuệ tổng quát nhân tạo`.

Two rules that matter:

- **Gloss once, in the place the author first uses it** — not in the chapter where
  you happen to translate it, if that differs. If the author defines a term in
  Chapter 3 but you first meet it in Chapter 2, gloss in Chapter 2 and note it.
- **Record the gloss in the book glossary** (`books/<id>/style/new_terms.txt` via
  `scripts/log_terms.py`) so later chunks are consistent.

### 2.5 Metaphor-Terms and Extended Metaphors

Non-fiction authors coin or borrow metaphors and then lean on them for chapters.
A coined label such as `Mind 2.0` is itself a metaphor-term: a stage-based naming of
eras. An AI named `Prometheus` carries a metaphor (stolen fire). These must be
translated **once, consistently, and with the metaphor intact** — or kept in English
if the metaphor does not survive.

Rules:

- **Decide the rendering at first use and log it.** Never re-decide mid-book.
- **Keep the metaphor audible.** If `Mind 2.0` becomes `Trí óc 2.0`, the "2.0" must
  keep reading as a version number, not as a quantity. Published Vietnamese often
  keeps such a coined title in English.
- **Do not translate a metaphor literally into nonsense.** "the genie is out of the
  bottle" needs the Vietnamese image (`thần đèn đã ra khỏi chai`) or an idiomatic
  equivalent (`nước đã đổ không hốt lại được`), not a literal `vị thần ở ngoài chai`.
- **Track metaphor drift.** If the author extends a metaphor across chapters ("the
  genie… the lamp… the wishes"), the Vietnamese must extend the same Vietnamese
  image, not switch to a different one partway.

### 2.6 Acronym Rules

- **First mention**: full Vietnamese or English form with the acronym in parentheses.
  e.g. `trí tuệ nhân tạo (AI)`.
- **Thereafter**: the acronym alone, in Latin script. Do not spell it out every time.
- **Vietnamese-origin acronyms**: if the Vietnamese phrase yields its own acronym
  (rare in this genre), be consistent within the book.
- **Do not translate the letters of an acronym.** `AI` is never `TTNT` unless the
  whole book has established that convention — and even then, the first mention must
  show both.
- **Plural/possessive**: English `AI's` becomes `của AI`; do not write `AI's` in
  Vietnamese text.
- **Consistency matrix** — keep one table per book listing each acronym, its full
  form, and the chunk where it was first defined.

---

## 3. Structure Conventions for Argumentative Prose

### 3.1 Claim → Evidence → Qualification

The characteristic non-fiction paragraph moves: *here is my claim; here is the
evidence or reasoning; here is the caveat that bounds it.* Vietnamese should preserve
all three movements. The failure mode is dropping the qualification because the
sentence already felt complete.

**`[constructed]`**:

> EN: "Superintelligence would likely be the most consequential event in human
> history — though 'likely' is doing a great deal of work in that sentence."
>
> ✅ "Siêu trí tuệ nhiều khả năng sẽ là sự kiện hệ trọng nhất trong lịch sử loài
> người — dù chữ 'nhiều khả năng' ở đây đang phải gánh một trọng trách rất lớn."
>
> ❌ "Siêu trí tuệ sẽ là sự kiện hệ trọng nhất trong lịch sử loài người." — the
> author's own self-aware caveat is gone, and now the book asserts the opposite of
> what it argued.

### 3.2 Definition-in-Passing vs Formal Definition

Two different moves:

- **Definition-in-passing**: the author names a term and moves on, expecting context
  to carry it. Translate the term, do not add a gloss unless the reader cannot
  proceed. Adding glosses the author didn't write is over-translation.
- **Formal definition**: the author explicitly defines ("By X I mean…", "X is defined
  as…", "Let us call this X"). These must be marked as definitions in Vietnamese:
  `Ở đây tôi muốn nói đến…`, `X được định nghĩa là…`, `Ta gọi đây là X`. A formal
  definition that reads as casual mention loses the reader's anchor.

### 3.3 Thought Experiments

Structure: setup → the experiment → the intuition the author wants → the caveat about
what the experiment does and doesn't show.

- **Signal the setup** with `Giả sử rằng…` / `Hãy tưởng tượng…` (see §1.3).
- **Keep the experiment's internal consistency.** If the setup says "there are exactly
  sixteen valleys", do not paraphrase to "many valleys" — the number is load-bearing
  for the argument.
- **Preserve the author's meta-commentary** about the experiment ("this is obviously
  unrealistic; that's the point"). It is doing argumentative work.
- **Do not add a caveat the author didn't write**, and do not remove one they did.

### 3.4 Quotation and Reported Speech

Non-fiction quotes other thinkers constantly: "Dennett argues", "as Chalmers puts
it", "in Kahneman's account".

- **Names stay in Latin script** and keep their original spelling.
- **The framing verb carries the stance.** `lập luận` (argues), `cho rằng` (holds
  that), `nhận xét` (remarks), `chỉ ra` (points out), `thừa nhận` (concedes),
  `phản đối` (objects). Choosing `cho rằng` where the author wrote "insists"
  softens the disagreement; choosing `khẳng định` where the author wrote "suggests"
  hardens it. These are semantic, not stylistic.
- **Direct quotation** keeps quotation marks and is translated faithfully. Vietnamese
  uses `"…"` for direct speech; nested quotes take `'…'`.
- **Indirect quotation** (`rằng` clauses) is the default and usually reads better in
  Vietnamese than a literal direct quote.
- **Do not silently improve a quote.** If the original is awkward, the Vietnamese
  awkwardness should be proportionate.

### 3.5 Section Headings and the Rhetorical Question

Non-fiction chapter and section headings are often arguments in miniature, or
questions the chapter will answer.

- **Headings**: keep them short, keep their tone. A punchy English heading should be
  a punchy Vietnamese heading, not an expanded descriptive one. If the heading is
  itself a term that recurs in the text, the heading's rendering must be the same
  rendering used in the body.
- **Rhetorical questions**: keep them as questions. Vietnamese question intonation is
  carried by `?` plus, often, a final particle (`không?`, `chứ?`, `sao?`, `à?`).
  A rhetorical question that becomes a statement loses the author's move of posing
  the problem to the reader. Do not add a particle that changes the tone — `à?` is
  conversational and can undercut a grave passage.
- **Recurring headings** (e.g. a chapter that revisits "the three scenarios") must be
  worded identically each time so the reader recognises the callback.

### 3.6 Lists Embedded in Prose

Non-fiction uses inline enumerations ("three obstacles: first… second… third…") and
occasionally real lists.

- **Inline enumerations**: keep the enumeration markers consistent. Vietnamese has
  `thứ nhất… thứ hai… thứ ba…` and `đầu tiên… tiếp theo… cuối cùng…`. Do not mix
  systems within a single enumeration.
- **Real Markdown lists**: only when the source has them. Do not convert a flowing
  sentence into a bulleted list for readability — that is an editorial change. (This
  matters mechanically: see §5.5 on how the pipeline's sentence-break fixer treats
  list lines.)
- **List-item length**: if the author's list items are full sentences, keep them as
  full sentences; do not compress to fragments.

---

## 4. Domain-Specific Handling

### 4.1 AI / Machine Learning

The fastest-moving vocabulary in the genre. Two failure modes: over-translating
(producing Vietnamese terms nobody in the field uses) and under-translating (leaving
so much English the page becomes unreadable).

| EN | VI | Rule |
|---|---|---|
| artificial intelligence | trí tuệ nhân tạo, `AI` | Translate in full form; keep the acronym. |
| artificial general intelligence | trí tuệ tổng quát nhân tạo, `AGI` | Gloss on first use; thereafter `AGI`. |
| machine learning | học máy | Settled. |
| deep learning | học sâu | Settled. |
| reinforcement learning | học tăng cường | Settled. |
| neural network | mạng nơ-ron | Settled; note the hyphenated `nơ-ron`. |
| large language model | mô hình ngôn ngữ lớn | Translate; `LLM` if the author uses the acronym. |
| superintelligence | siêu trí tuệ | Settled. |
| alignment (AI) | sự căn chỉnh / bài toán căn chỉnh | No settled form. Gloss: `căn chỉnh (alignment)`. |
| intelligence explosion | bùng nổ trí tuệ | Translate. |
| singularity | điểm kỳ dị | Settled in VI popular science. |
| the Turing test | phép thử Turing | Translate; keep the proper name. |
| computation / compute | tính toán / năng lực tính toán | Distinguish the noun from the capacity. |
| hardware / software | phần cứng / phần mềm | Settled. |
| upload (a mind) | tải lên (tâm trí) | Verb is settled; the mind-upload sense needs care. |
| substrate | nền tảng / cơ chất | Philosophy sense usually `cơ chất`; AI sense `nền tảng`. |

**Acronyms in this domain** (`AI`, `AGI`, `ML`, `RL`, `GPU`, `TPU`, `LLM`) stay in
Latin script after first mention — Vietnamese AI writing does this universally.

**Careful with `intelligence`**: it is `trí tuệ` in this domain, but `thông minh` when
it means "cleverness" in ordinary speech. `artificial intelligence` is never
`trí thông minh nhân tạo` in modern usage.

### 4.2 Physics / Cosmology

Mostly well-settled Vietnamese terminology, because Vietnamese physics education has
a long continuous tradition.

| EN | VI | Notes |
|---|---|---|
| Big Bang | Vụ Nổ Lớn | Capitalised as a proper event. |
| universe | vũ trụ | |
| entropy | entropy | Kept; some texts use `entrôpi`. Follow the book, not your preference. |
| dark matter / dark energy | vật chất tối / năng lượng tối | Settled. |
| quantum | lượng tử | |
| multiverse | đa vũ trụ | Settled in popular science. |
| light-year | năm ánh sáng | |
| 13.8 billion years | 13,8 tỷ năm | **Decimal comma**, not point — Vietnamese convention. |
| thermodynamics (second law) | nhiệt động lực học (định luật thứ hai) | |
| causality | nhân quả / quan hệ nhân quả | |

**Numbers**: Vietnamese uses `.` for thousands and `,` for decimals — the reverse of
English. `13.8` → `13,8`. `1,000,000` → `1.000.000`. Get this right or the physics
becomes nonsense. See §5.3.

**Units**: `km`, `kg`, `s`, `W`, `°C` are kept as symbols. Spelled-out units
(`kilometre`) translate (`kilômét`).

### 4.3 Philosophy of Mind / Consciousness

The hardest domain, because Vietnamese philosophical vocabulary is thinner here and
English terms carry decades of technical debate.

| EN | VI | Notes |
|---|---|---|
| consciousness | ý thức | Settled and used for both the faculty and the state. |
| conscious experience | trải nghiệm ý thức | |
| qualia | qualia / cảm giác chủ quan | Usually kept English; gloss on first use. |
| sentience | khả năng cảm nhận | Distinguish from consciousness (see below). |
| subjective experience | trải nghiệm chủ quan | |
| intentionality | tính ý hướng | Technical; gloss. |
| functionalism | chủ nghĩa chức năng | Also `thuyết chức năng`. |
| the hard problem | bài toán khó | `vấn đề khó` also seen; be consistent. |
| zombie (philosophical) | thây ma triết học / zombie triết học | Needs a gloss — the ordinary reader will misread it as horror. |
| mind-body problem | vấn đề tâm-trí | |
| theory of mind | lý thuyết về tâm trí | Not the AI sense (which is `lý thuyết tâm trí` in the cognitive-science sense too — context decides). |
| emergence | tính nổi lên / sự xuất hiện | `tính nổi lên` for the technical sense. |

**`consciousness` vs `sentience`**: non-fiction authors often use these
interchangeably; a careful author does not. `sentience` is the capacity to feel,
`consciousness` the capacity to be aware. If the author distinguishes them, the
Vietnamese must too — `khả năng cảm nhận` vs `ý thức`. If the author uses them
loosely, do not import a distinction the author didn't make (see §8.4).

**`qualia`**: keep English. Attempting a Vietnamese coinage produces something no
reader will recognise.

### 4.4 Ethics / Decision Theory

| EN | VI | Notes |
|---|---|---|
| utilitarian / utilitarianism | theo chủ nghĩa vị lợi / chủ nghĩa vị lợi | Settled. |
| deontology | nghĩa vụ luận / đạo đức học nghĩa vụ | Gloss on first use. |
| consequentialism | chủ nghĩa hệ quả | |
| moral patient / moral agent | đối tượng có tư cách đạo đức / chủ thể đạo đức | Technical; gloss. |
| trolley problem | bài toán xe đẩy | Settled in VI popular writing. |
| the veil of ignorance | bức màn vô minh | Settled (Rawls). |
| Pareto improvement | cải thiện Pareto | Keep the proper name. |
| zero-sum / positive-sum | tổng bằng không / tổng dương | |
| existential risk | rủi ro tồn vong | Now standard in VI AI-safety writing. |
| precautionary principle | nguyên tắc phòng ngừa | |

### 4.5 Mathematics and Formal Intuition

Authors use maths as an intuition pump, not a derivation. Keep the intuition, keep
the notation.

- **Notation stays Latin**: variables are `x`, `y`, `n`; functions are `f(x)`. Do not
  italicise differently from the source, and do not translate `n` to `n` (it is the
  same). Greek letters keep their names in Vietnamese transliteration when spoken
  (`alpha` → `alpha` in a formula, `anpha` when spelled out in prose).
- **`exponential`** as a popular-science intensifier ("exponential growth") →
  `tăng trưởng theo cấp số nhân`. But "exponentially more" used rhetorically
  ("exponentially harder") is often better as `khó hơn gấp bội` — check whether the
  author means the function or the feeling.
- **Order-of-magnitude claims** ("a factor of a million") → `gấp một triệu lần`, not
  a literal `một nhân tố của một triệu`.
- **Probabilities**: `10%` stays `10%`. "one in a million" → `một trên một triệu`.
- **Formulas in Markdown**: leave them in code/LaTeX spans untouched, and translate
  only the surrounding prose.

---

## 5. Formatting Conventions

### 5.1 Chapters and Headings

Same rules as the rest of the pipeline (see `style/formatting_rules.md`): `# CHƯƠNG N`
for chapter headings, kept consistent for the TOC validator.

Non-fiction-specific:

- **Sub-headings** are frequent and carry structure. Preserve the hierarchy (`##` vs
  `###`) exactly — do not promote or demote.
- **Numbered sub-headings** ("1.3 The Hedging Problem") keep their numbers.
- **A heading that is a sentence** ("Why This Matters") keeps the sentence form.

### 5.2 Figures, Captions, Tables

- **Figure captions** translate in full, including the figure number: `Hình 3.2`.
- **Table headers** translate; table *content* follows §2 and §4 per cell. Keep the
  column alignment intact mechanically.
- **Cross-references** ("see Figure 3.2") → `xem Hình 3.2`. Do not translate the
  number.
- **If a figure is an image**, do not attempt to translate text inside it. Add a
  translator's note only if the author's argument depends on reading it.

### 5.3 Numbers, Dates, Units

| Item | English | Vietnamese |
|---|---|---|
| Decimal | `13.8` | `13,8` |
| Thousands | `1,000` | `1.000` |
| Large | `1.5 million` | `1,5 triệu` |
| Date | `March 4, 2011` | `4 tháng 3 năm 2011` |
| Decade | `the 2010s` | `thập niên 2010` |
| Century | `the 21st century` | `thế kỷ 21` |
| Range | `10–20%` | `10–20%` (keep the en-dash as a range) |
| Approx. | `~100` | `~100` or `khoảng 100` |

**Watch the em-dash vs. range-dash distinction**: the pipeline normalises em-dashes
(§5.4) but a numeric range must keep its dash. A `10–20` that becomes `10 - 20` reads
as a subtraction.

### 5.4 Dashes

The pipeline normalises prose em-dashes to a spaced ASCII hyphen ` - ` (see
`scripts/utils/normalize_dashes.py`), matching the project's house style. Two
non-fiction-specific cautions:

- **Parenthetical em-dash** — an author's aside set off by dashes — may instead
  become a comma or semicolon when Vietnamese reads better. If retained as a dash,
  use ` - `, never an em-dash. `…— though 'likely' is doing a great deal of work —`
  → `…, dù 'nhiều khả năng' đang phải gánh…`.
- **Range dashes** must survive as unspaced en-dashes (see §5.3).

### 5.5 Lists and the Sentence-Break Fixer

Mechanically important. `scripts/utils/fix_sentence_breaks.py` joins lines that look
like a sentence split across a line break. It treats a lone `- ` line as dialogue
(keeps processing it) but a `- ` line whose neighbour is also a `- ` line as a
markdown list (leaves it alone).

Consequence for non-fiction: **if you introduce list items into the prose that the
source did not have, you create ambiguous `- ` lines.** Don't. If the source has a
list, keep it as a list with consistent markers.

### 5.6 Footnotes and Endnotes

- **Footnote markers** keep their position relative to the Vietnamese sentence —
  which may move, because Vietnamese word order differs. Put the marker after the
  phrase it annotates, not after the English word that happened to precede it.
- **Footnote text** translates in full, in the same register as the body.
- **Bibliographic citations** (author, title, year, publisher) are **not** translated
  beyond the frame words. A cited title stays in its original language:
  `Nick Bostrom, *Superintelligence* (2014)` stays as-is.

---

## 6. Reader Engagement

### 6.1 Inclusive vs. Exclusive "We" — a Real Decision

Vietnamese forces a choice English does not make explicit.

| Form | Meaning | Use when |
|---|---|---|
| `chúng ta` | inclusive: you (reader) and I (author), together | Default for popular science. "we humans", "our future", "we still don't know". |
| `chúng tôi` | exclusive: I and my group, not you | Only when the author means a specific in-group: "we physicists", "we at MIT", and even then often better as `các nhà vật lý` / `nhóm chúng tôi`. |
| `loài người` / `nhân loại` | humanity | When "we" means the species and inclusive `chúng ta` would sound too cosy for a grave passage. |

**Default to `chúng ta`.** Big-questions non-fiction is written to put the reader
inside the argument. `chúng tôi` pushes the reader outside it, and does so silently.

**Observed in published translations** — `chúng ta` is used for the species-level
"we" throughout, and reserves `chúng tôi` for the author's own research group.

### 6.2 Address and Stance

- **Do not introduce `bạn`.** Unlike self-help, non-fiction rarely addresses the
  reader in the second person; when it does ("you might think…"), it is a rhetorical
  move, and `bạn` in Vietnamese can read as condescending in a serious argument.
  Consider `ta` (neutral, inclusive-ish) or restructure to a `chúng ta` sentence.
  Use `bạn` only where the author is genuinely buttonholing the reader.
- **Keep the author's confidence level.** A book that argues forcefully should read
  forcefully in Vietnamese. Over-softening with particles (`nhé`, `thôi`, `mà`) makes
  a serious argument sound casual. Reserve particles for the places where the author
  is genuinely being casual.
- **Preserve humour and irony.** Popular-science authors are often funny, and a
  translator who flattens the jokes has changed the book. If the author makes a dry
  aside, the Vietnamese aside should be dry — do not add an explanatory gloss that
  kills it.

### 6.3 Callbacks and Recurring Motifs

Big-questions books plant a term or image early and pay it off late.

- **Log the term the first time you render it** and reuse that rendering verbatim.
- **If the callback depends on the wording** ("as I called it in Chapter 1"), the
  Chapter-1 wording must match exactly.
- **If the callback depends on a metaphor**, the Vietnamese metaphor must be the same
  metaphor (see §2.5).

---

## 7. Glossary Consistency Across a Long Book

### 7.1 Why This Matters More Here

A novel can survive some terminology drift; the reader tracks characters, not terms.
A non-fiction book is *built* out of its terms. A reader who meets
`bài toán căn chỉnh` in Chapter 2 and `vấn đề alignment` in Chapter 7 has lost
the thread of the argument, not merely been mildly annoyed.

### 7.2 One English Term, Several Vietnamese — and Vice Versa

Two directions of failure:

- **Splitting**: one English term rendered two ways across chunks. Fix: a per-book
  term table, consulted before translating each chunk, appended to after.
- **Merging**: two English terms collapsed into one Vietnamese term, hiding a
  distinction the author is making. The classic case in this genre: `consciousness`
  and `sentience` both → `ý thức`. Also `mind` / `brain` both → `trí óc`, and
  `intelligence` / `intellect`.

The merge failure is *worse* than the split failure because it is invisible: the
Vietnamese reads perfectly and says something the author didn't.

### 7.3 Cross-Chunk Workflow

1. **Before translating a chunk**, load the book's `new_terms.txt` and glossary.
2. **On encountering a term**, check the table first. If present, use the recorded
   rendering even if you would have chosen differently.
3. **On coining a new rendering**, log it immediately with
   `python scripts/log_terms.py "term | translation | context | chunk_XXX"`.
   Never append to `style/new_terms.txt` by hand.
4. **On finding the table wrong**, update the entry — and note the reason. Do not
   silently diverge; a chunk translated with an unlogged correction is worse than
   one translated wrong, because the next chunk has no way to know.

### 7.4 Proper Names of Ideas

Hypotheses, effects, thought experiments, and named arguments are proper nouns.
They keep their attribution: `the Fermi paradox` → `nghịch lý Fermi`, not
`nghịch lý về sự im lặng của vũ trụ`. The name is the retrieval key; a reader who
reads further or looks it up needs the name.

---

## 8. Common Pitfalls

### 8.1 Flattening the Hedge

**The single most damaging error in this category.** Covered in §1.2; restated here
because it recurs.

> ❌ EN: "This might be the last century in which humans are the smartest things on
> Earth."
> ❌ VI: "Đây là thế kỷ cuối cùng mà con người là sinh vật thông minh nhất Trái Đất."
> ✅ VI: "Đây có thể là thế kỷ cuối cùng mà con người còn là sinh vật thông minh
> nhất trên Trái Đất."

The Vietnamese version with `có thể` and `còn` says what the English says. The other
says something the author pointedly avoided.

### 8.2 Turning a Scenario into a Prediction

Thought experiments and scenarios read as reportage if not signalled. Every scenario
opener needs its `Giả sử rằng…` / `Hãy tưởng tượng…` / `Trong kịch bản này…`. A
chapter that opens "Trong tương lai, AI sẽ…" without the conditional frame tells the
reader this is going to happen.

### 8.3 Adding Explanation the Author Didn't Write

The temptation of the subject-matter-aware translator: the text mentions something
briefly and you know a clarifying clause would help. Resist. Translator additions
(a) misrepresent the author's pacing, (b) accumulate and bloat the book, and
(c) are indistinguishable from the author's own prose to the reader, who will
attribute them to the author. This is the non-fiction form of the §2.3
"definition-in-passing" trap.

### 8.4 Importing a Distinction the Author Didn't Make

The mirror of §8.3 and often subtler. A translator who knows that philosophers
distinguish `sentience` from `consciousness` may render them with two Vietnamese
terms even where the author uses them loosely — silently upgrading the author's
precision. Check the author's usage before adding rigour.

### 8.5 Terminology Drift Across Chunks

Covered in §7. The practical guard is the log-before-you-move-on rule: never finish
a chunk with an unlogged new term.

### 8.6 Angular Vietnamese from Over-literal Syntax

English non-fiction loves long left-branching sentences with stacked subordinate
clauses. Carried into Vietnamese word-for-word these produce unreadable prose.
Vietnamese prefers shorter clauses, often reordered. Splitting one English sentence
into two or three Vietnamese sentences is usually correct, not a loss of fidelity —
the *argument* must survive, not the sentence boundary.

**Observed in published translations** — translators routinely split long English
sentences at the point where Vietnamese would naturally break, and converts em-dash
asides into semicolons.

### 8.7 Losing the Author's Self-Awareness

Popular-science authors constantly flag their own moves: "this is speculative",
"that's an obviously silly example", "I'm oversimplifying". These asides are the
author being honest with the reader and are *not* filler. Cutting them to tighten the
prose changes the book's epistemic stance.

### 8.8 Register Collapse

Mixing academic and colloquial registers within a paragraph. Vietnamese non-fiction
has a continuum from formal (`do đó`, `hơn nữa`, `tuy nhiên`) to colloquial
(`thế nên`, `với lại`, `nhưng mà`). Pick the register the author is in and hold it for
the paragraph. Do not mix `do đó` and `thế nên` in consecutive sentences.

---

## 9. QA Checklist

Run per chunk before marking it done.

**Epistemic**
- [ ] Every English modal (may / might / could / would / can / should / must) has a
      Vietnamese counterpart of the right strength (see §1.2 ladder).
- [ ] No bare assertions where the author hedged.
- [ ] Scenario openers are signalled (`giả sử`, `hãy tưởng tượng`).
- [ ] Conditional obligations (`would have to`) render as `sẽ phải`, not `phải`.

**Terminology**
- [ ] Every new term is logged via `scripts/log_terms.py`.
- [ ] No term rendered two ways within the chunk.
- [ ] No two distinct English terms collapsed into one Vietnamese term.
- [ ] Acronyms glossed on first mention, Latin script thereafter.
- [ ] `intelligence` → `trí tuệ` (not `thông minh`) in the AI sense.

**Structure**
- [ ] Chapter/sub-heading hierarchy preserved.
- [ ] Heading renderings match any earlier occurrence of the same heading.
- [ ] Lists are only where the source had lists.
- [ ] Defined terms marked as definitions; passing mentions are not.

**Formatting**
- [ ] Numbers use Vietnamese decimal/separator convention.
- [ ] Figure/table numbers and cross-references preserved.
- [ ] Range dashes survived the em-dash normalisation.
- [ ] Footnote markers sit after the phrase they annotate.

**Voice**
- [ ] Inclusive `chúng ta` used for species-level "we" unless the author meant a group.
- [ ] No `bạn` introduced where the source did not address the reader.
- [ ] The author's humour, irony, and self-aware asides survived.

**Mechanical**
- [ ] `python scripts/fix.py` run; no CJK corruption, no formatting issues.
- [ ] `python scripts/fix.py --check-only` clean.
- [ ] `chunks/manifest.json` updated to `done`.

---

## 10. Sources and Their Limits

**Primary parallel text**: a published Vietnamese translation (2020) of an English
big-questions popular-science book (2017), read side-by-side with the original. No
text is quoted from it: the examples are `[constructed]` to show the observed
patterns.

**What the parallel text supports well:**

- Hedging vocabulary and its frequency (`có thể`, `có khả năng`, `nhiều khả năng`,
  `dường như`, `giả sử`, …) — these are measured counts over the full Vietnamese text,
  not impressions.
- First-person popular-science register.
- Inclusive-`chúng ta` convention.
- Sentence-splitting and em-dash-to-semicolon behaviour.

**What the parallel text does *not* support:**

- **Neologism policy for AI terms.** The 2017 Vietnamese translation predates the
  current AI vocabulary. Terms like `alignment`, `AGI`, `LLM`, and `superintelligence`
  are either absent or handled inconsistently. The recommendations in §4.1 for those
  terms are reasoned from current Vietnamese technical usage, **not** extracted from
  the parallel text. Treat them as provisional.
- **Measurement of terminology density.** The "10–25%" figure in the Executive Summary
  is an estimate, not a measured quantity.
- **A second book.** All parallel evidence is from one author, one translator, one
  publishing house. Some of what is described here may be that translator's style
  rather than a genre convention. A second parallel pair is the natural next data
  point.

**Secondary sources**: general Vietnamese style conventions (number/decimal
separator, date format, `chúng ta` vs `chúng tôi`), Vietnamese technical terminology
in AI and physics as used in current Vietnamese-language writing, and the project's
own `style/formatting_rules.md`.

**Provenance markers used in this file:**

- **Observed in published translations** — a pattern seen in the parallel text pair,
  stated without quotation.
- `[constructed]` — written to illustrate a pattern; not a real published rendering.

---

## 11. Open Questions

1. **No settled Vietnamese form for `alignment`.** Current candidates: `căn chỉnh`,
   `sự căn chỉnh`, or keeping English. The right answer may depend on how prominent
   the term is in the specific book — a book about AI safety needs a settled
   rendering; a book that mentions it once does not.
2. **`qualia`.** Keeping English is safe but leaves a hole for a reader without
   English. A Vietnamese coinage (`cảm giác chủ quan`) is understandable but has no
   currency in Vietnamese philosophy writing. Currently resolved in favour of keeping
   English with a gloss; revisit if a Vietnamese philosophical literature emerges.
3. **`chúng ta` vs `loài người` for grave passages.** `chúng ta` is correct and
   inclusive, but in a passage about human extinction it can read as too
   companionable. No settled convention; §6.1 gives a default, not a rule.
4. **One-book evidence base.** Every observed pattern comes from a single
   translator. Whether these are genre conventions or house style is unresolved. A
   second parallel text would settle several recommendations in §6 and §8.
5. **AI terminology churn.** The §4.1 table will age faster than the rest of this
   file. It needs re-checking against current Vietnamese technical usage before each
   new AI-subject book, not annually.
6. **Number convention in quoted material.** When the source quotes a figure
   published with English separators, should the Vietnamese preserve the original
   (`13.8`) or convert (`13,8`)? Currently §5.3 says convert. There is an argument for
   preserving in direct quotations.
