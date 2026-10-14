# Translation Quality Assurance Checklist

**Version:** 1.0
**Last Updated:** 2025-12-04
**Purpose:** Comprehensive QA validation for book translation projects

---

## Table of Contents

1. [Pre-Translation Checks](#pre-translation-checks)
2. [During Translation Checks](#during-translation-checks)
3. [Post-Translation Checks](#post-translation-checks)
4. [Automated Checks](#automated-checks-scripts-can-verify)
5. [Manual Review Checks](#manual-review-checks)
6. [Severity Levels & Error Categories](#severity-levels--error-categories)
7. [QA Sign-Off Template](#qa-sign-off-template)

---

## Pre-Translation Checks

**Purpose:** Establish baseline & prevent QA issues from source

### Source Document Validation
- [ ] **CRITICAL** - Source file extracted without corruption (compare byte count with original)
- [ ] **CRITICAL** - All pages/chapters present in extraction (check page range matches source)
- [ ] **IMPORTANT** - Sentence breaks verified (mid-sentence breaks identified & logged)
- [ ] **IMPORTANT** - Formatting preserved in source extraction (heading hierarchy, indentation)
- [ ] **IMPORTANT** - Special characters handled correctly (quotes, dashes, Unicode)
- [ ] **NICE** - Backup of original source created & versioned

### Style Guide & Glossary Preparation
- [ ] **CRITICAL** - Translation style guide exists & loaded
- [ ] **CRITICAL** - Glossary/term base compiled with source → target mappings
- [ ] **CRITICAL** - Proper nouns list prepared (character names, place names, brand names)
- [ ] **IMPORTANT** - Formatting rules documented (dates, numbers, dashes, units)
- [ ] **IMPORTANT** - Tone & voice guidelines defined (formal/informal register)
- [ ] **IMPORTANT** - Terminology decision log initialized (for new/ambiguous terms)
- [ ] **NICE** - Reference materials gathered (genre-specific terminology, cultural context)

### Project Structure Setup
- [ ] **CRITICAL** - Chunk division plan created (consistent chunk sizes)
- [ ] **CRITICAL** - Manifest/tracking file initialized with metadata
- [ ] **IMPORTANT** - Target locale specified (Vietnamese variant, date format, etc.)
- [ ] **IMPORTANT** - QA issue log created & accessible
- [ ] **NICE** - Reference translation samples identified (if available)

---

## During Translation Checks

**Purpose:** Catch issues early, maintain quality throughout

### Per-Chunk Translation Validation
- [ ] **CRITICAL** - Blank-line-delimited source block count matches exactly; headings, lists, dialogue blocks, and page markers retain corresponding blocks
- [ ] **CRITICAL** - Each `<!-- Page N -->` boundary matches the source exactly (standalone ↔ standalone, inline ↔ inline); do not add blank lines around markers that are inline in the source
- [ ] **CRITICAL** - No content omitted (compare key phrases/proper nouns presence)
- [ ] **CRITICAL** - No content added (translation only, no explanatory additions)
- [ ] **IMPORTANT** - All proper nouns translated consistently (check against proper noun list)
- [ ] **IMPORTANT** - Glossary terms used correctly (check against term base)
- [ ] **IMPORTANT** - Heading hierarchy preserved (# → ##, structure intact)
- [ ] **IMPORTANT** - Numbering & lists preserved exactly (1, 2, 3... not a, b, c)
- [ ] **NICE** - Comments/notes added for ambiguous translations (for later review)

### Consistency Checks (Running)
- [ ] **CRITICAL** - Character names consistent (John Smith always "John Smith", never "Smith" alone without context)
- [ ] **CRITICAL** - Place names consistent (New York always same, no variations)
- [ ] **IMPORTANT** - Recurring phrases handled identically (e.g., "once upon a time" always same translation)
- [ ] **IMPORTANT** - Terminology applied consistently within chunk
- [ ] **IMPORTANT** - Tone/voice consistent throughout chunk (formal voice if established)

### Formatting During Translation
- [ ] **CRITICAL** - Dash policy applied: prose ` - `, dialogue `- `, numeric ranges `10–20`, compounds unchanged
- [ ] **IMPORTANT** - Punctuation spacing maintained (French thin space rules if applicable)
- [ ] **IMPORTANT** - Dialogue formatting preserved (quotes, line breaks, indentation)
- [ ] **IMPORTANT** - Footnote/endnote references preserved & numbered correctly
- [ ] **IMPORTANT** - Special formatting markers maintained (bold, italics, code blocks if present)

---

## Post-Translation Checks

**Purpose:** Final validation before export/delivery

### Structural Validation
- [ ] **CRITICAL** - Total paragraph count matches source (full document)
  - Source paragraphs: _______
  - Translated paragraphs: _______
  - Variance: _______ (document if >1%)
- [ ] **CRITICAL** - All chapters/sections present
- [ ] **CRITICAL** - Heading hierarchy correct (no orphaned headings, proper nesting)
- [ ] **IMPORTANT** - Table of Contents structure valid (if auto-generated)
- [ ] **IMPORTANT** - Footnotes/endnotes complete & correctly numbered
- [ ] **IMPORTANT** - Page breaks/chapter breaks in expected locations

### Content Completeness
- [ ] **CRITICAL** - No untranslated segments (find & mark with [TODO] for review)
- [ ] **CRITICAL** - No source text remaining in translation (except quoted phrases, if intentional)
- [ ] **CRITICAL** - All proper nouns present (cross-check against source)
- [ ] **IMPORTANT** - No placeholder text left ("fill this in", "check this", etc.)
- [ ] **IMPORTANT** - All numbers/statistics preserved (spot-check sample)
- [ ] **NICE** - All dialogue translated (search for quotation marks)

### Terminology & Consistency (Global)
- [ ] **CRITICAL** - All glossary terms used consistently (run terminology check across full document)
- [ ] **CRITICAL** - Character names consistent throughout (create name index, verify all instances)
- [ ] **CRITICAL** - Place names consistent throughout
- [ ] **IMPORTANT** - Technical terms standardized (if applicable to genre)
- [ ] **IMPORTANT** - Recurring phrases handled identically across all chunks
- [ ] **IMPORTANT** - Brand names not mistranslated (kept in original if required)

### Style & Tone Validation
- [ ] **CRITICAL** - Voice consistent throughout (formal maintained, or informal if applicable)
- [ ] **IMPORTANT** - Tone matches original (serious passages sound serious, humorous remain humorous)
- [ ] **IMPORTANT** - Register appropriate (formal for academic, casual for dialogue)
- [ ] **IMPORTANT** - Cultural references adapted appropriately (not just literal translation)
- [ ] **IMPORTANT** - Pacing/rhythm matches original (not unnecessarily long/short sentences)
- [ ] **NICE** - Idiomatic expressions translated naturally (not word-for-word)

### Formatting Consistency (Global)
- [ ] **CRITICAL** - Dash normalization: all dashes consistent throughout
- [ ] **CRITICAL** - Punctuation spacing: French rules (thin space) applied consistently if target is French-adjacent
- [ ] **IMPORTANT** - Capitalization rules applied consistently (Vietnamese rules: lowercase after dash, proper nouns capitalized)
- [ ] **IMPORTANT** - Number formatting consistent (1,000 vs. 1.000 vs. 1 000)
- [ ] **IMPORTANT** - Quote styles consistent (curly vs. straight quotes)
- [ ] **IMPORTANT** - Spacing: no double spaces, consistent indentation
- [ ] **NICE** - Ellipsis: consistent style (... vs. …)

### Readability Assessment
- [ ] **IMPORTANT** - Sentence length varies (no monotonous sentences)
- [ ] **IMPORTANT** - No run-on sentences (reading aloud test: should be readable in one breath)
- [ ] **IMPORTANT** - Paragraph lengths varied & logical
- [ ] **IMPORTANT** - Transitions between ideas flow naturally
- [ ] **IMPORTANT** - No awkward phrasing that disrupts reading
- [ ] **NICE** - Flow matches original (not too literal, sounds natural in target language)

### Native Speaker Review
- [ ] **CRITICAL** - Reviewed by native Vietnamese speaker (if available)
- [ ] **CRITICAL** - Naturalness confirmed (doesn't sound like machine translation)
- [ ] **IMPORTANT** - Colloquialisms & idioms appropriate for target audience
- [ ] **IMPORTANT** - No literal translations that sound unnatural in Vietnamese
- [ ] **IMPORTANT** - Grammar correctness verified
- [ ] **NICE** - Feedback documented for future reference

---

## Automated Checks (Scripts can verify)

**Purpose:** Catch mechanical errors via automation

### Formatting Validation
- [ ] **fix.py --check-only** runs without critical errors
- [ ] Sentence breaks verified (no mid-sentence line breaks)
- [ ] Dash normalization applied (em-dash → standard dash)
- [ ] Person name capitalization correct (First Last format)
- [ ] Special characters valid (no encoding issues)

### File Integrity Checks
- [ ] File syntax valid (no corruption)
- [ ] Character encoding consistent (UTF-8)
- [ ] Line ending consistent (LF, not mixed CRLF)
- [ ] File size reasonable (not drastically different from source)

### TOC/Structural Validation
- [ ] **validate_toc.py** passes without errors
- [ ] All heading levels (# through ####) present & ordered
- [ ] No orphaned subheadings (e.g., ### without ##)
- [ ] Heading text is not empty

### Terminology Checks (if using CAT tools)
- [ ] Term base check runs (flagged terms verified as intentional)
- [ ] No forbidden terms present (if forbidden term list exists)
- [ ] Terminology consistency score acceptable (>95% reuse if available)

### Statistical Validation
- [ ] Word count ratio source:target reasonable (typically 0.8–1.2 ratio depending on language pair)
- [ ] Paragraph count matches (±1 acceptable with justification)
- [ ] Character count similar order of magnitude (not 50% longer/shorter without reason)

---

## Manual Review Checks

**Purpose:** Catch nuance errors automation can't detect

### Comprehension Test
- [ ] Can someone unfamiliar with source understand the meaning clearly?
- [ ] Translation conveys intended message without ambiguity
- [ ] Context is clear (pronouns refer to correct antecedents)
- [ ] Technical concepts explained sufficiently (if applicable)

### Accuracy Verification (Sample)
- [ ] **Random sampling**: Pick 5 paragraphs at different document positions
  - Para #: _______ → Source ↔ Target match? YES / NO / PARTIAL
  - Para #: _______ → Source ↔ Target match? YES / NO / PARTIAL
  - Para #: _______ → Source ↔ Target match? YES / NO / PARTIAL
  - Para #: _______ → Source ↔ Target match? YES / NO / PARTIAL
  - Para #: _______ → Source ↔ Target match? YES / NO / PARTIAL
- [ ] Sample accuracy ≥95% (if <95%, escalate for full review)

### Terminology Spot Check
- [ ] Pick 10 glossary terms at random
- [ ] Verify each term translated consistently across document
- [ ] Correct translation used (not alternative translation)
- [ ] Term not mistranslated as homonym or similar word

### Dialogue & Character Voice
- [ ] Each character's voice consistent throughout (distinct personality in dialogue)
- [ ] Dialogue natural (doesn't sound stilted or overly formal)
- [ ] Dialogue punctuation correct (punctuation before closing quote or after?)
- [ ] Line breaks & formatting match original

### Cultural & Contextual Appropriateness
- [ ] Cultural references handled appropriately (adapted vs. kept literal)
- [ ] Humor translated (not just explained)
- [ ] Offensive content intentionality preserved if present
- [ ] Historical context accurate (names, dates, events)

### Problem Areas Review
- [ ] Complex sentences re-read for clarity
- [ ] Passive voice evaluated (is it necessary or awkward?)
- [ ] Metaphors translated effectively (conveying meaning, not literal)
- [ ] Puns or wordplay adapted to target language if possible
- [ ] Difficult passages compared directly with source

---

## Severity Levels & Error Categories

### Severity Classification

| Level | Impact | Examples | Action |
|-------|--------|----------|--------|
| **CRITICAL** | Translation unusable, meaning lost | Untranslated segments, missing chapters, wrong character names | STOP – Fix before release |
| **IMPORTANT** | Reduces quality, confuses reader | Inconsistent terminology, tone breaks, formatting errors | FIX – Document in errata if not fixed |
| **NICE** | Polish/refinement issues | Grammar could be more natural, could vary sentence length | OPTIONAL – Fix if time permits |

### Error Categories

**Accuracy Errors**
- Mistranslation (wrong meaning)
- Omission (content missing)
- Addition (content not in source)
- Incorrect terminology

**Fluency Errors**
- Grammar mistakes
- Unnatural phrasing
- Inconsistent tone
- Awkward sentence structure

**Consistency Errors**
- Same term translated multiple ways
- Character names spelled inconsistently
- Formatting inconsistency
- Tone breaks

**Formatting Errors**
- Broken dashes/punctuation
- Incorrect spacing
- Heading level errors
- Missing special characters

---

## QA Sign-Off Template

**Use this template to document final QA approval for each chunk or final document:**

```markdown
## QA Sign-Off: [Chunk_XXX or FINAL_DOCUMENT]

**QA Reviewer:** _________________
**Review Date:** _________________
**Translation Date:** _________________

### Checklist Status
- Pre-translation checks: ☐ PASS / ☐ FAIL
- Automated checks: ☐ PASS / ☐ FAIL
- Manual review checks: ☐ PASS / ☐ FAIL

### Critical Issues Found
1. _________________________________
2. _________________________________
3. _________________________________

**Status:** ☐ APPROVED / ☐ APPROVED WITH MINOR NOTES / ☐ REQUIRES REWORK

### Approval Notes
_________________________________________________________________

**Sign-Off:** ______________________ (Reviewer Signature/Name)
```

---

## Implementation Guide

### For Single Chunk Translation
1. Complete "During Translation Checks" while translating
2. After translation, run `python scripts/fix.py translated/chunk_XXX_vi.md`
3. Run automated checks section
4. Perform manual review checks on 10% of content (sample 5 paragraphs)
5. Sign off in manifest with "qa_passed" status

### For Full Document QA
1. Ensure all chunks individually signed off
2. Run `python scripts/fix.py` on all translated files
3. Run `python scripts/utils/validate_toc.py translated/`
4. Perform global consistency checks (terminology, character names, tone)
5. Sample-test 25 paragraphs across full document (5 per chapter if possible)
6. Create final QA sign-off document
7. Ready for export

### For Export Pre-Check
1. Complete all post-translation checks above
2. Run `python scripts/export.py --check-only` (if available) or proceed directly
3. Verify export output matches expected format
4. Spot-check exported file (random 5 pages in PDF, check chapter breaks)

---

## Quick Reference: Most Important Items

**If you only have 30 minutes for QA:**

1. ✓ Paragraph count matches source (CRITICAL)
2. ✓ No untranslated segments (CRITICAL)
3. ✓ Character names consistent (CRITICAL)
4. ✓ Glossary terms used consistently (CRITICAL)
5. ✓ Dashes normalized (CRITICAL)
6. ✓ Read 5 random paragraphs for naturalness (IMPORTANT)
7. ✓ Tone consistent (IMPORTANT)

---

## References & Resources

Based on best practices from:
- ISO 17100:2015 translation standard requirements
- Industry-recognized QA frameworks (LISA QA, MQM, TAUS DQF)
- Leading translation tools: Trados Studio, memoQ, Smartcat, Phrase
- Translation QA expertise sources: Transifex, Lokalise, Tomedes, POEditor

**Key Industry Standards Referenced:**
- Two or three professional linguists review per ISO 17100
- Error typology aligned with MQM (Multidimensional Quality Metrics)
- Quality scoring by category: Accuracy, Fluency, Terminology, Style, Grammar

---

## Notes

- **Customize severity levels** based on your project requirements (some projects may escalate IMPORTANT to CRITICAL)
- **Add project-specific checks** in blank areas for domain-specific terminology or format requirements
- **Review this checklist** after each major translation milestone and update based on common issues found
- **Archive QA sign-offs** with final deliverable for audit trail
