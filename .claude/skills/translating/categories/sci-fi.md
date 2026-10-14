# Sci-Fi Genre Translation Guide

## Overview

Science fiction translation requires balancing scientific plausibility, invented terminology consistency, world-building coherence, and accessibility. Unlike literary fiction, sci-fi demands special attention to technical exposition, invented terms, and maintaining the "sense of wonder" across language boundaries.

---

## 1. Tone & Voice

### Core Characteristics

**Technical but Accessible**
- Present complex concepts clearly without oversimplification
- Explain through character perspective and context, not narration
- Use analogies and comparisons rather than pure technical exposition
- Balance scientific plausibility with narrative flow

**World-Building Exposition**
- Introduce terminology gradually through natural context
- Use characters' dialogue to explain concepts (character knows more → character knows less)
- Avoid info-dumps; let readers discover the world organically
- Trust readers to understand meaning from context

**Speculative Narration**
- Maintain narrative authority even when describing impossible technology
- Use matter-of-fact tone for fantastical elements
- Employ conditional language sparingly; treat invented tech as established
- Maintain temporal consistency (past tense for narrative grounding)

**Sense of Wonder**
- Preserve awe and discovery in translator's voice
- Keep scientific rigor without coldness
- Allow poetic quality in technical descriptions (especially in space/nature scenes)
- Maintain the author's optimism or skepticism about technology as intended

### Author Style References

**Isaac Asimov Style**: Clarity-first, direct explanations, embedded science naturally in dialogue. Emphasis on scientific accuracy above all. Translator must maintain his didactic yet engaging tone.

**Arthur C. Clarke Style**: Elegant technical exposition, poetic treatment of space, gradual revelation of concepts. Famous principle: "Any sufficiently advanced technology is indistinguishable from magic." Translator should capture his mix of wonder and rigor.

**Frank Herbert Style** (Dune): Rich terminology embedded in context clues, reliance on appendices for reference, multi-layered world-building. Translator must preserve the density of his invented world without over-explaining.

---

## 2. Terminology Handling Principles

### Core Rule: Consistency Over Perfection

Invented terms are acceptable only if applied consistently throughout the entire work. One inconsistent term can break reader immersion more than an unfamiliar term used uniformly.

### Classification of Terms

#### A. Made-Up Technology Terms
**Translation Approach**: Keep as-is (in original language)
- Examples: "phaser," "warp drive," "photonic torpedo"
- Vietnamese: Keep English when untranslatable concept
- If Vietnamese equivalent exists: Create glossary entry with both terms
- Mark in glossary with English origin

#### B. Scientific/Technical Concepts
**Translation Approach**: Translate if concept exists in target language
- Physics: năng lượng (energy), lực hấp dẫn (gravity)
- Biology: DNA, gen (gene), protein
- Electronics: máy tính (computer), điều khiển (control)
- Mix of Vietnamese + Latin/Greek terminology acceptable if author uses same in original

#### C. Alien/Future Terminology
**Translation Approach**: Keep invented words as-is, provide context
- Alien species names: Vulcan, Klingon (unchanged)
- Alien concepts: spore drive, mycelial network (contextual explanation only)
- Cultural terms: Arrakeen, melange (keep original, use glossary)
- Create pronunciation guide if relevant to plot

#### D. Proper Nouns (Places, Species, People)
**Translation Approach**: Preserve exactly as written
- Place names: Tatooine, Caladan, Arrakis
- Species: Human, Fremen, Bene Gesserit
- Person names: Paul Atreides, Chani
- Exception: Translate descriptive titles only (e.g., "the Emperor" → "vị Hoàng Đế")

### Terminology Management Strategy

**Create Term Master List** (Before translating)
```
| English | Vietnamese | Category | Notes | First Appearance |
|---------|------------|----------|-------|------------------|
| lightsaber | tia sáng Jedi | Tech | Keep English | Chunk 3 |
| Force | Lực (Lực Lớn) | Concept | Capitalized always | Chunk 1 |
| Padawan | Padawan | Culture | Apprentice title, no translation | Chunk 2 |
```

**Maintain Consistency**
- Use exact same translation every single instance (no variations)
- If using Vietnamese + English hybrid (e.g., "máy tính quantum"), stick with it throughout
- Mark glossary with page/section first appearance
- Review glossary weekly; never add "alternative translations"

**Handle Brand New Terms**
- If encountering untranslatable term: Research if established Vietnamese translation exists
- If not: Create descriptive Vietnamese term or keep English with explanation
- Log in `style/new_terms.txt` with context chunk
- Use script: `python scripts/log_terms.py "term | translation | context | chunk_XXX"`

---

## 3. World-Building Translation

### Place Names

**Rule**: Do not translate place names
- Keep: Arrakis, Caladan, Giedi Prime (Star Wars, Dune)
- Not: Tinh Cầu (bad - invented places should stay English)
- Reasoning: Place names are identity markers; translation breaks world consistency

**Exception**: Only translate if original author provides Vietnamese equivalent (rare)

### Species & Race Names

**Capitalization Rule** (applies to Vietnamese too)
- Capitalize all species names consistently
- Species named from homeland: Always capitalize (Fremen from Arrakis)
- Cultural group names: Capitalize (Bene Gesserit, Jedi)
- Biological classifications: lowercase unless proper noun (human, humanoid, amphibian)

**Vietnamese Format**
```
English: Vulcan (species from planet Vulcan)
Vietnamese: Người Vulcan hoặc Vulcan (keep consistent - choose one)

English: Fremen (cultural group)
Vietnamese: Người Fremen hoặc Fremen (keeps English, recognizable)

English: humans vs. Humans
Vietnamese: con người vs. Người (if referencing species group)
```

### Technology Names

**Brand Names & Proprietary Tech**: Keep as-is
- Keeps brand identity intact
- Examples: lightsaber, sonic screwdriver, TARDIS
- Translate descriptive function: "a device for cutting" but keep the tech name

**Functional Tech Categories**: Translate with context
```
English: "blaster" (weapon type)
Vietnamese: "súng năng lượng" (energy gun) or keep "blaster"

English: "hyperdrive" (engine type)
Vietnamese: "động cơ dịch chuyển siêu không gian" or "hyperdrive"

Strategy: Keep futuristic/invented names, translate functional categories where helpful
```

### Social Structure & Institutions

**Titles & Ranks**: Decide per-work
```
Case 1 - Keep English:
English: "Jedi Master, Padawan, Sith"
Vietnamese: "Jedi Master, Padawan, Sith" (established terms in Vietnamese sci-fi)

Case 2 - Mix:
English: "Bene Gesserit Reverend Mother"
Vietnamese: "Bene Gesserit" (keep, organization name) + "Reverend Mother" (or "Mẹ Kính Trọng")

Strategy: Maintain author's style; if they capitalize and mystify, preserve that in Vietnamese
```

**Cultural Concepts**: Translate with glossary support
```
English: "the Tao" (philosophical)
Vietnamese: "Đạo Tao" (has existing translation)

English: "the Force" (mystical)
Vietnamese: "Lực" hoặc "Lực Lớn" (provide both, pick one)

English: "spice" (resource, untranslatable metaphor)
Vietnamese: "gia vị" (functional) or "spice" (keep, makes more sense in context)
```

---

## 4. Common Sci-Fi Terminology

### Space & Astronomy

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| spaceship | tàu vũ trụ / con tàu |  |
| spacecraft | phương tiện không gian |  |
| warp drive | động cơ dịch chuyển / động cơ biến dạng | Keep English if author emphasizes tech name |
| FTL (faster-than-light) | nhảy cảnh sáng / vượt tốc độ ánh sáng | Explain once, use abbreviation after |
| hyperspace | không gian siêu | Keep structure for sci-fi flavor |
| black hole | hố đen |  |
| nebula | tinh vân |  |
| asteroid | tiểu hành tinh |  |
| orbit | quỹ đạo |  |
| light-year | năm ánh sáng |  |
| starship | tàu sao / tàu ngôi sao |  |
| bridge (of ship) | buồng điều khiển / cầu chỉ huy |  |
| cargo bay | khoang hàng |  |
| airlock | cảnh cửa kín khí |  |

### Physics & Energy

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| energy | năng lượng |  |
| radiation | tia xạ / bức xạ |  |
| plasma | plasma / chất tính nhân |  |
| matter | vật chất |  |
| antimatter | chất phản vật chất |  |
| laser | tia laser / tia sáng |  |
| photon | photon / hạt sáng |  |
| gravitational field | trường hấp dẫn |  |
| temporal | theo thời gian / liên quan thời gian | Use "thời gian" for clarity |
| quantum | lượng tử |  |
| singularity | điểm kỳ dị |  |

### Technology & Robotics

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| robot | robot / công nhân cơ khí |  |
| android | android / người máy | "người máy" if looks human |
| AI / artificial intelligence | trí tuệ nhân tạo / AI |  |
| cyborg | nhân tạo mạnh / người cyborg | Blend of human + machine |
| hologram | hình chiếu / bộ ba chiều |  |
| terminal | thiết bị đầu cuối / máy tính |  |
| interface | giao diện / bệ mặt |  |
| download | tải xuống |  |
| upload | tải lên |  |
| server | máy chủ |  |
| network | mạng |  |
| virus | virus / chương trình phá hoại |  |
| encryption | mã hóa |  |

### Weapons & Defense

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| blaster | súng công suất cao / súng năng lượng |  |
| phaser | bộ phát tia / bộ điều chỉnh | Often keep English in space opera |
| photonic torpedo | ngư lôi ánh sáng |  |
| shield | khiên / lá chắn năng lượng |  |
| force field | trường lực |  |
| disruptor | máy phá hủy / bộ phát nhân |  |

### Time Travel & Temporal

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| time travel | du hành thời gian |  |
| paradox | nghịch lý |  |
| timeline | dòng thời gian / khoảng thời gian |  |
| alternate timeline | khoảng thời gian khác biệt |  |
| temporal | theo thời gian |  |
| causality | nhân quả |  |

### Aliens & Species

| English | Vietnamese | Context/Notes |
|---------|------------|---------------|
| humanoid | người hình / nhân hình | Keep English if significant |
| extraterrestrial | người ngoài hành tinh / sinh vật ngoài Trái Đất |  |
| alien | sinh vật ngoài / sinh vật lạ | Use "sinh vật ngoài" for sci-fi |
| telepathy | truyền tâm / đọc tâm |  |
| species | loài / chủng loài |  |

---

## 5. Technical Exposition Techniques

### The Info-Dump Problem

**What is it**: Lengthy technical explanations inserted into narrative to explain world mechanics.

**Translation Challenge**: Must maintain accessibility without losing technical precision.

### Handling Strategies

#### A. Context-First Method
Instead of explaining, show the concept in use:

```
WRONG (too much explanation):
"Tàu sử dụng động cơ dịch chuyển, một thiết bị tận dụng lý thuyết hạt nhân..."

RIGHT (context-based):
"Paul nhìn vào màn hình dữ liệu. Dòng số chạy nhanh. 'Bao lâu cho hyperdrive kích hoạt?'
'Ba phút, sư phụ.'"
```

The reader understands "hyperdrive" exists and what it does without explanation.

#### B. Character-as-Explainer
Use natural knowledge difference between characters:

```
The expert character explains to the novice (or vice versa):
- Engineer explains malfunction to captain
- Rookie asks veteran about procedure
- AI explains to human characters

This makes explanation feel like dialogue, not exposition.
```

#### C. Glossary + Contextual Clues
Introduce term with minimal context, full definition in glossary:

```
Text: "Phương pháp mycelial dịch chuyển đã thay đổi mọi thứ."
Glossary: "Mycelial Network Drive: A hypothetical faster-than-light
propulsion system using quantum spore technology..."

Reader gets meaning from context, can consult glossary if curious.
```

#### D. Analogical Translation
Use reader's existing knowledge:

```
Complex: "Năng lượng được điều chỉnh qua bộ điều chế lượng tử"
Simple: "Năng lượng được điều chỉnh giống như việc xoay âm lượng trên radio"
```

### Dialogue Exposition Rules

**Natural dialogue for technical concepts**:
1. Never have two experts explain to each other
2. Use curiosity/confusion as motivation
3. Interrupt explanations naturally
4. Use technical terms + show effects
5. Vary sentence length (short for action, longer for explanation)

**Bad Example**:
```
"As you know, the quantum entanglement device works by..."
"Yes, yes, I know that already..."
```

**Good Example**:
```
"The hyperdrive is still offline?"
"Another five minutes. The power coupling burned out."
"Can we reroute?"
"Not from here. Someone needs to access the engine room."
```

---

## 6. Dialogue Conventions

### Technical Dialogue Requirements

**Character Voice Consistency**
- AI or logical character: Short, precise sentences with passive voice
- Casual soldier: Contractions, slang, active voice
- Alien character: Slight word order variation, unusual emphasis patterns
- Vietnamese: Adjust particles và/thôi/cơ mà to match character type

**Mixing Technical Terms in Dialogue**
- Use jargon, but define once on first use
- After definition, use term consistently without re-explanation
- Allow characters to assume listener knowledge (builds world authenticity)

**Example dialogue translation**:
```
Original (English):
"The main reactor is fluctuating. I need to regulate the EMP shielding."
"How long?"
"Ten minutes, maybe less."

Vietnamese (maintain tone):
"Lò phản ứng chính bị dao động. Tôi phải điều chỉnh khiên EMP."
"Mất bao lâu?"
"Mười phút, có thể ít hơn."

NOT: "Lò phản ứng chính bị dao động vì sự mất cân bằng điện từ đang..."
(Too much explanation in dialogue)
```

### Avoiding Common Mistakes

| Problem | Wrong | Right |
|---------|-------|-------|
| Explaining obvious | "The door, which slides electronically..." | "The door slid open." |
| Over-translating terms | "bộ điều chỉnh tần số radio" (3 words) | "radio regulator" or keep English |
| Breaking character voice | Villain uses technical jargon, then slang | Maintain speech patterns |
| Lost sense of wonder | "Tàu vũ trụ là phương tiện di chuyển" | "Tàu tia sáng bắn qua bầu trời" |

---

## 7. Consistency Maintenance Tools

### Create & Use a Terminology Database

**Format** (can be Google Sheets or CSV):
```
| Term | Vietnamese | Category | Author Style | First Use | Frequency | Notes |
|------|------------|----------|--------------|-----------|-----------|-------|
| lightsaber | tia sáng Jedi | Tech | formal | Ch 1 | 47x | Iconic term, ALWAYS capitalize |
| the Force | Lực | Concept | mystical | Intro | 150x | "Lực lớn" vs "Lực" - use former |
| Jedi | Jedi | Culture | formal | Ch 1 | 200x | NEVER translate |
```

**Update Rules**:
- Add new terms immediately upon discovery
- Never remove terms (archive old versions)
- Flag terms requiring glossary entry
- Cross-check every 5 chunks

### Glossary Structure

Place glossary at end of book:

```
GLOSSARY OF TERMS

Force, the (Lực Lớn) - The mystical energy field binding all living things
in the Star Wars universe. Central to Jedi philosophy and training. First
mentioned Chapter 1.

Jedi (Jedi) - An ancient order of warrior-philosophers who serve as keepers
of peace and justice in the galaxy. Members train from childhood as Padawans
under Jedi Masters. First mentioned Chapter 1.

Padawan (Padawan) - An apprentice Jedi in training under a Jedi Master. The
title indicates the learner's rank and obligation. First mentioned Chapter 3.
```

### Weekly QA Checklist

Before chunk approval:
- [ ] All proper nouns spelled identically to first appearance
- [ ] All invented terms use same Vietnamese equivalent throughout
- [ ] Glossary updated with new terms
- [ ] No terms appear with variations (e.g., "lightsaber" and "light saber")
- [ ] Species names capitalized consistently
- [ ] Author's technical tone preserved
- [ ] Sense of wonder maintained in descriptive passages

---

## 8. Language-Specific Vietnamese Considerations

### Sentence Structure in Technical Exposition

**English allows complex embedded clauses:**
"The device, which controls the temporal field using quantum mechanics, must be activated carefully."

**Vietnamese prefers simpler structure:**
"Thiết bị này điều khiển trường thời gian bằng cơ học lượng tử. Phải kích hoạt cẩn thận."

**Strategy**: Break long sentences; use more periods; maintain clarity.

### Particle Usage in Character Voice

| Particle | Character Type | Example |
|----------|---|---------|
| cơ mà | Casual/soldier | "Tàu hyperdrive hỏng cơ mà" (damn) |
| à | Scientific/formal | "Tàu hyperdrive hỏng à?" (questioningly) |
| thôi | Dismissive | "Để tôi làm thôi" (just let me) |
| đấy | Emphasis | "Đó là công việc khó đấy" (really difficult) |

**Match Vietnamese particles to character voice, maintaining tone shifts**.

### Neologism Acceptance in Vietnamese

Vietnamese readers accept:
- English tech terms (phổ biến)
- Latin/Greek compounds (khoa học)
- Vietnamese + English hybrids (bình thường)

Keep consistency; don't vary between "tàu vũ trụ" and "spaceship" in same context.

---

## 9. Genre-Specific Challenges & Solutions

| Challenge | Why It Happens | Solution |
|-----------|---|----------|
| Over-explaining tech | Translator fears reader confusion | Trust context; use glossary |
| Inconsistent terms | Rushing; assuming synonyms are OK | Master list; never "vary" terms |
| Losing technical tone | Trying to make it "more natural" | Preserve author's rigor |
| Breaking immersion | Unnecessary cultural adaptation | Keep place names/concepts as-is |
| Flat dialogue | Translating speech too literally | Adapt particles/structure for voice |
| Weak sense of wonder | Over-functional translation | Use poetic language in space scenes |

---

## 10. Reference Works & Further Study

### Essential Authors to Reference

**For Technical Precision**:
- Isaac Asimov (*Foundation* series)
- Arthur C. Clarke (*2001: A Space Odyssey*)
- Greg Egan (*Permutation City* - hardest hard sci-fi)

**For World-Building Density**:
- Frank Herbert (*Dune*)
- Iain M. Banks (*Culture* series)
- Ursula K. Le Guin (*Hainish Cycle*)

**For Dialogue Naturalism**:
- Lois McMaster Bujold (*Vorkosigan Saga*)
- John Scalzi (*Old Man's War*)
- N.K. Jemisin (*Broken Earth* trilogy)

### Research Resources

- [Science Fiction Encyclopedia](https://sf-encyclopedia.com/) - Comprehensive SF terminology
- [Technovelgy.com](http://www.technovelgy.com/) - 3,300+ SF inventions
- TV Tropes: Sci-Fi and Naming tropes
- Author interviews on writing style and terminology choices

---

## Quick Reference: Translation Decision Tree

```
ENCOUNTERED AN UNKNOWN TERM?

Is it a made-up technology?
  └─ YES → Keep in English, add to glossary → Go to Master List
  └─ NO → Next

Is it a scientific concept?
  └─ YES → Translate if Vietnamese exists → Check glossary
  └─ NO → Next

Is it a proper noun (place/species/person)?
  └─ YES → Keep EXACTLY as written → Verify spelling
  └─ NO → Next

Is it cultural/social terminology?
  └─ YES → Translate if possible, glossary if complex
  └─ NO → Consider context

Already appears in text?
  └─ YES → Use EXACT same translation
  └─ NO → Add to Master List → Log with chunk number

Unsure about consistency?
  └─ Search entire project → Update all instances
```

---

## Checklist Before Final Export

- [ ] All terminology appears in Master Glossary
- [ ] No invented term appears with variations
- [ ] All proper nouns match first appearance spelling
- [ ] Species names capitalized consistently
- [ ] Technical tone matches author's original style
- [ ] Dialogue sounds natural in Vietnamese but preserves technical accuracy
- [ ] Info-dumps have been contextualized where possible
- [ ] Sense of wonder preserved in space/discovery scenes
- [ ] New terms logged with `python scripts/log_terms.py`
- [ ] Glossary formatted and sorted alphabetically
- [ ] Cross-references checked for continuity
