# Vietnamese Language Conventions for Book Translation

Reference guide for translators working on Vietnamese book translations. This document covers punctuation, formatting, typography, writing style, and foreign element handling based on established Vietnamese translation standards.

---

## 1. Punctuation

### 1.1 Quotation Marks

**Vietnamese Style**
- Use double straight quotation marks: `" "` (not curved quotes)
- Use single straight quotation marks for quotes within quotes: `' '`
- NO spaces between quotation marks and text inside: `"text"` not `" text "`

**Rules**
- Punctuation inside quotation marks if part of the quoted content
- Punctuation outside if not part of the quotation
- For multi-line quotations, use quotes only at start and end (not at beginning of each line)

**Examples**
```
Hắn gọi tôi là "thằng khốn".
(He called me a "bastard".)

Cô ấy hỏi: "Bạn đi đâu?" tôi trả lời.
(She asked: "Where are you going?" I replied.)

Tôi nói "Xin chào" để chào hỏi.
(I said "hello" as a greeting.)
```

### 1.2 Dashes

**Project Convention**
- Do not emit em-dashes (`—`).
- Use spaced ASCII hyphens for retained prose parentheticals: ` - `.
- Start dialogue lines with leading `- `.
- Use an unspaced en-dash for numeric ranges: `9–10`, `10–20%`.
- Preserve lexical hyphens in compounds.

**Examples**
```
SOURCE: He said—it was clear—that she would arrive.
OUTPUT: He said - it was clear - that she would arrive.

WRONG: Pages 10 - 20
RIGHT: Pages 10–20

RIGHT (dialogue): - Tôi hiểu rồi.
RIGHT (compound): self-aware
```

### 1.3 Ellipsis

**Style**
- Use three dots: `...` (not `…` Unicode ellipsis in some contexts)
- Indicates hesitation, unfinished thought, or omitted content
- Called "dấu lửng" in Vietnamese

**Examples**
```
"I'm not sure if I should..." she said.
(Tôi không chắc liệu mình có nên... - cô ấy nói.)

The story continues with the day, the week, the month...
(Câu chuyện tiếp tục với ngày, tuần, tháng...)
```

### 1.4 Other Punctuation Spacing

**Rule**: Punctuation marks immediately follow the word without preceding space.

**Examples**
```
WRONG: She asked , "Where are you ?"
RIGHT: She asked, "Where are you?"

Period position: Periods and any other punctuation mark are followed by one space (not two).

Colon usage: Introduces explanation, list, or quotation with one space after.
```

### 1.5 Dialogue Punctuation

**Introduction**
- Use colon to introduce dialogue: `He said: "..."`
- Apply standard quotation mark rules

**Multi-line Dialogue**
- Each new speaker gets new paragraph
- Apply quotation mark rules to entire speech block (not each line)

---

## 2. Formatting Numbers, Dates, & Currency

### 2.1 Number Format

**Vietnamese Standard**: `999.999.999,99`
- Thousands separator: dot (`.`)
- Decimal separator: comma (`,`)
- Group size: 3 digits
- Always include `0` before decimal for numbers less than 1: `0,5` (not `,5`)

**Examples**
```
English: 1,000.50
Vietnamese: 1.000,50

English: 0.75
Vietnamese: 0,75

English: 1,234,567.89
Vietnamese: 1.234.567,89
```

### 2.2 Date Format

**Standard Format**: `DD/MM/YYYY` (day/month/year - little-endian)

**Numeric Dates**
- Use slashes or periods: `09/12/2024` or `09.12.2024`
- Day and month: always with leading zeros

**Written Dates**
- Format: `ngày [day] tháng [month] năm [year]`
- No special names for months/days - use numbers
- Days of week: Chủ nhật (Sunday), thứ hai (Monday) through thứ bảy (Saturday)

**Examples**
```
Numeric: 03/12/2014 (December 3rd, 2014)
Written: ngày 31 tháng 7 năm 2004 (July 31st, 2004)
Day: Thứ ba, ngày 15 tháng 3 năm 2024 (Tuesday, March 15th, 2024)
```

### 2.3 Time Format

**Standard**: 12-hour notation in most cases
- Leading zero in hours can be omitted
- Format: `HH:MM` or `H:MM`
- Can add AM/PM designation if needed

**Examples**
```
09:30 (09 or 9:30)
2:45 PM
```

### 2.4 Currency Format

**Vietnamese Dong (VND)**
- Symbol: `₫` or `đ`
- Position: AFTER the number
- Format: `1.000.000.000 đ`
- Group size: 3 (thousands separator: dot)

**Foreign Currency**
- DO NOT translate currency codes (USD, GBP, EUR, etc.)
- Keep currency codes in UPPERCASE
- Position: typically BEFORE amount in Vietnamese context

**Examples**
```
Vietnamese: 1.000.000 đ (1 million dong)
Foreign: 100 USD (not 100 đô la Mỹ)
Mixed: 1.000.000 đ = 42 USD
```

---

## 3. Typography

### 3.1 Capitalization Rules

**Proper Nouns - General Rule**
- Capitalize first letter of ALL syllables in proper nouns
- Vietnamese proper nouns are multi-syllabic, so apply to each syllable

**Personal Names**
- Capitalize all syllables: `Nguyễn Du`, `Trần Phú`, `Bác Hồ`
- Include given names and family names
- Foreign names: Keep original capitalization (direct transliteration style preferred in modern Vietnamese)

**Geographical Names**
- Capitalize all syllables: `Hà Nội`, `Hà Lan`, `Bắc Trung Bộ`
- Common nouns with geographical names: lowercase common noun, capitalize proper noun
  - `Cửa Lô beach` (not `Cửa Lô Beach`)
  - `Bến Thành market` (not `Bến Thành Market`)
  - `Vâm Côn river` (not `Vâm Côn River`)

**Direction + Topography Combinations**
- Capitalize all syllables when indicating regions: `Bắc Trung Bộ`, `Tây Nguyên`

**Titles & Book/Article Titles**
- Capitalize ONLY:
  - First letter of first word of title and subtitle
  - All syllables of proper nouns
- Lowercase all other words
  - Example: `Tìm hiểu về lịch sử Việt Nam` (Understanding Vietnamese History)
  - NOT: `Tìm Hiểu Về Lịch Sử Việt Nam`

**Journal, Newspaper, Organization Names**
- Capitalize all syllables: `Báo Nhân Dân`, `Tạp Chí Văn Học`

**Sentence Start**
- Capitalize first letter of sentence: normal English-like rule
- Example: `Hôm nay là ngày đẹp.` (Today is a beautiful day.)

**NO Accents on Capital Letters**
- Rule: Do not use diacritical marks on initial capital letters
- Example: `Ágain` becomes `Again` (though Vietnamese preserves diacritics always)

**Examples Summary**
```
CORRECT:
- Hà Nội (city)
- Nguyễn Ái Quốc (person)
- Cửa Lô beach (geography + common noun)
- Tìm hiểu về văn học Việt (title capitalization)
- Báo Nhân Dân (publication name)

WRONG:
- Ha Noi (lacks capitalization)
- nguyễn Ái Quốc (inconsistent capitalization)
- Cửa Lô Beach (common noun capitalized)
- Tìm Hiểu Về Văn Học Việt (over-capitalization)
```

### 3.2 Word Spacing

**Standard Rule**: Single space between words
- Single space after punctuation (not double spaces as in some English styles)
- No extra spaces around punctuation marks

### 3.3 Emphasis Techniques

**Bold, Italic, Underline**
- Use sparingly and consistently
- Bold: For important terms, section headers, book titles
- Italic: For foreign words, emphasized phrases, titles
- Underline: Minimal use (reserved for links, emphasized text in specific contexts)

**Vietnamese-Specific Markup**
- No special conventions differ from English typography
- Follow same rules for consistency

---

## 4. Writing Style

### 4.1 Sentence Structure

**Basic Order**: Subject + Verb + Object (SVO)
- Same as English, but different emphasis patterns

**Topic-Comment Structure** (Important!)
- Vietnamese prefers topic-prominent sentences
- Move topic to front, then comment on it
- Different from English emphasis

**Examples**
```
English: I already read this book.
Vietnamese: Sách này thì tôi đọc rồi.
Literal: "Book this (topic), I read already (comment)."

English: Your house is very nice.
Vietnamese: Nhà bạn thì đẹp lắm.
Literal: "Your house (topic), it's very nice (comment)."
```

**Adjective Placement**
- AFTER nouns (opposite of English)
- "tall man" = "đàn ông cao" (man tall)
- "beautiful house" = "ngôi nhà đẹp" (house beautiful)

**Adverb Placement** (When object present)
- Subject + Verb + Object + Adverbs
- "I finished reading the book quickly" = "Tôi đọc xong cuốn sách nhanh" (quickly at end)

**Tense Markers** (Not conjugation-based)
- Past: add particle `đã` before verb
- Present progressive: add particle `đang` before verb
- Future: add particle `sẽ` before verb
- Often omitted in context where tense is clear

### 4.2 Sentence Length & Complexity

**General Guidelines**
- Vietnamese can handle long, complex sentences like English
- Use subordinate clauses naturally
- Break very long sentences for clarity (readability > grammar)
- Typical academic/formal writing uses moderately long sentences

**Paragraph Structure**
- Standard paragraph length: 4-8 sentences
- Keep related ideas together
- Use topic sentences (especially important for formal writing)

### 4.3 Formal vs. Informal Register

**Formal (Academic/Professional)**
- Use complete sentences without contractions
- Avoid slang and colloquial expressions
- Use formal pronouns and kinship terms
- More complex sentence structures
- Technical terminology (translated appropriately)
- Add formal particles: `ạ`, `anh/chị` (respectful)

**Informal (Casual/Daily)**
- Simpler sentence structures
- Conversational tone acceptable
- Colloquialisms permitted in dialogue
- Casual pronouns: `tớ/cậu`, `mình`, `bạn`
- Informal particles: `nha`, `nhé`, `mà` (regional variations)

**Formality Markers in Vietnamese**
- `ạ` - very formal, used for social superiors
- `nha` (Southern) / `nhá` (Northern) - reduces formality, implies closeness
- Kinship terms: Used even for non-relatives in formal contexts
  - `anh` (older male/formal)
  - `chị` (older female/formal)
  - `em` (younger/familiar)

**Examples**
```
Formal: Xin chào, bạn khỏe không ạ?
(Hello, how are you? - very formal)

Informal: Chào cậu, cậu khỏe không nhé?
(Hey man, you doing okay? - casual/familiar)

Academic: Như chúng tôi đã đề cập trong phần trước, ...
(As we mentioned in the previous section, ...)

Conversational: Như tớ nói lúc trước, ...
(Like I said before, ...)
```

### 4.4 Translation Principles

**Avoid Literal/Word-for-Word Translation**
- Capture essence and meaning, not word-for-word transfer
- Maintain natural Vietnamese flow
- Adjust for topic-comment structure when needed
- Respect Vietnamese idioms and expressions

**Maintain Appropriate Tone**
- Conversational source → conversational translation (not heavy/formal)
- Formal source → formal translation (no slang/unprofessional words)
- Match register throughout document

---

## 5. Foreign Elements

### 5.1 Foreign Names

**Modern Convention**: Direct Phonetic Transliteration
- Keep original spelling and pronunciation
- Preserve original names (most common modern approach)
- Readers expect original names in contemporary Vietnamese

**When to Transliterate**
- Historical/classical figures: May use Vietnamese equivalents
- Only if approved Vietnamese translations exist
- Example: Confucius = Khổng Tử (established historical equivalent)

**Writing Rules for Transliterated Names**
- Capitalize first letter of each component (multi-word names)
- Examples: `Vladimir Ilich Lenin`, `Frederick Engels`, `Kim Il Sung`
- Keep accents and special characters from original language if possible

**Sino-Vietnamese Names** (Older convention, less common now)
- Transliterated into Sino-Vietnamese phonetics
- Example: Portugal = 葡萄牙 → `Bồ Đào Nha` (fully Vietnamese)
- Only use if specifically required

**Non-Vietnamese Names (Except Chinese)**
- Use English spellings
- UNLESS established Vietnamese translations exist
- Registered/trademarked names: NEVER change them
  - Example: `Coca-Cola`, `Microsoft`, `Toyota` (always in original)

**Examples**
```
KEEP ORIGINAL: Peter, Susan, Vladimir, Sarah
USE ENGLISH SPELLING: Most foreign names

TRANSLITERATED (rare): Khổng Tử (Confucius - historical)
                       Mạc Tư Đông (Mao Zedong - alternative acceptable)

NEVER CHANGE: Coca-Cola, Microsoft, Apple, Google, FIFA
```

### 5.2 Loanwords & Borrowed Terms

**Current Vietnamese Loanword Usage** (~5% of foreign names)
- Modern Vietnamese: Minimal transliteration (only ~5% of foreign names)
- Past Vietnamese: Heavy transliteration (historic ~95%)
- Trend: Toward original English spelling

**Categories of Loanwords**

1. **Integrated Loanwords** (fully adopted)
   - From French (historical colonial influence)
   - From English (modern influence)
   - Often have Vietnamese pronunciation rules applied

   Examples:
   - `Cà phê` (café - from French "café")
   - `Tivi` (TV - from English)
   - `Ra-đi-ô` (radio - from English)
   - `Xe máy` (motorcycle - partially borrowed)
   - `Máy tính` (computer - literally "computing machine")

2. **Non-Integrated Loanwords** (recent borrowings)
   - Often kept in original form with Vietnamese spelling adaptation
   - Product names, technology terms, modern concepts
   - Examples: Email → `email`, Software → `phần mềm` (literal translation), Computer → `máy tính` (literal)

3. **Sino-Vietnamese Words** (ancient layer)
   - Estimated 30-70% of Vietnamese vocabulary
   - Fully integrated, not considered "foreign" anymore
   - Especially prominent in academic/formal writing

**Translation Decisions**

| Situation | Action | Example |
|-----------|--------|---------|
| Loanword with established Vietnamese term | Translate | "Computer" → `máy tính` |
| Modern product/brand name | Keep original | "iPhone" → `iPhone` |
| Foreign word emphasized in source | Keep original, may italicize | "email" → `email` (or italicized) |
| Common non-integrated loanword | Check context; usually keep original | "Software" → `phần mềm` (if translated) or `software` (if kept) |
| Non-integrated, no Vietnamese term | Keep original | "Data" → `dữ liệu` (translated) or `data` (kept) |

**Translator's Guide**
- Always check client instructions first
- When in doubt: translate established terms, keep new/technical terms
- Consistency: Apply same decision throughout document
- Specialized terminology: May remain untranslated in academic works

### 5.3 Acronyms

**Widely-Used Vietnamese Acronyms**
- HLV = Huấn luyện viên (Coach)
- BTC = Ban tổ chức (Organizers)
- THPT = Trung học Phổ thông (High School)
- UNESCO, FIFA, USA (universal acronyms - keep as-is)

**Translation Rules**
- If Vietnamese acronym exists and is widely used: use it
- If no Vietnamese equivalent: keep source acronym (in English/original)
- Acronyms common in Vietnamese: keep unchanged
- First mention: optionally provide full term in footnote or parentheses

**Examples**
```
HLV Nguyễn Văn A (Coach A) - Vietnamese readers know this
The FIFA World Cup (not create Vietnamese acronym)
Công ty giáo dục B (Education Company B) - create acronym only if needed
```

---

## 6. Dialogue & Narrative

### 6.1 Character Speech

**Direct Speech**
- Use quotation marks as specified in Section 1.1
- Introduce with colon or comma
- New paragraph for each speaker

**Indirect Speech**
- No quotation marks needed
- Can modify pronouns/tense as needed
- More flexible with exact wording

**Examples**
```
DIRECT: "Tôi yêu bạn," cô ấy nói.
        ("I love you," she said.)

INDIRECT: Cô ấy nói rằng cô yêu bạn.
          (She said that she loves him/her.)

NEW SPEAKER: "Tôi cũng vậy," anh trả lời.
             "I feel the same," he replied.
```

### 6.2 Dialogue Tags

**Acceptable Verbs**
- `nói` (said)
- `hỏi` (asked)
- `trả lời` (replied)
- `gọi` (called)
- `yêu cầu` (requested/demanded)
- `lẩm bẩm` (muttered)
- `thì thầm` (whispered)

**Placement**
- Can come after direct speech with comma
- Usually follows the entire statement: `"Text," verb.`
- Can come before speech with colon: `Anh nói: "..."`

---

## 7. Special Considerations

### 7.1 Tone & Voice Consistency

**Book Translation Checklist**
- Formal throughout vs. mixed formality: decide early
- Character voices: distinguish by register
- Narrative vs. dialogue register: maintain separation
- Keep emotional intensity consistent

### 7.2 Text Direction

**Left-to-Right**: Vietnamese uses standard left-to-right script (Latin alphabet with diacritics)
- No special RTL considerations
- Punctuation positioning: standard (immediately after word)

### 7.3 Terms of Address

**Important Rule**: Do not use English translation of Vietnamese terms of address
- In quoted/translated text: use original Vietnamese term
- Can italicize for clarity: `*ạ*`, `*chị*`
- Explain in footnotes if needed for non-Vietnamese readers
- Preserves cultural authenticity

**Common Terms**
- `ạ` - formal suffix
- `anh` - older male
- `chị` - older female
- `em` - younger/familiar
- `bạn` - friend/peer
- `ông` - grandfather/formal male
- `bà` - grandmother/formal female

### 7.4 Measurement Units

**Vietnamese Practice**
- NOT all measurement terms translated
- Some translated, some localized, some kept untranslated

**Common Conversions**
- `second` = `giây` (translated)
- `meter` = `mét` (localized/adapted spelling)
- `kilogram` = `ki-lô-gam` or `kg` (adapted/abbreviated)
- Keep Celsius without conversion (Vietnam uses metric system)

**When Translating Scientific/Technical**
- Metric system is standard (Vietnam uses metric)
- If source uses imperial: may convert with note OR keep original with conversion
- Check document type and audience

### 7.5 Quotations & Citations

**Block Quotations**
- Indented block: standard formatting
- Use quotation marks for start/end of entire block (not each line)
- Source attribution: follow Chicago Manual of Style recommendations
- Add Vietnamese translation of source if necessary

**In-Text Citations**
- Maintain original citation format
- Translate source titles to Vietnamese if well-known
- Preserve exact publication details

---

## 8. Common Pitfalls & Solutions

| Problem | Wrong | Right | Notes |
|---------|-------|-------|-------|
| Em-dash usage | "He said—clearly" | "He said - clearly" | Project prose parenthetical rule |
| Number separators | "1000,50" | "1.000,50" | Dot for thousands, comma for decimal |
| Quote marks | 'He said: what?' | "He said: what?" | Double quotes, straight (not curved) |
| Capitalization | "the beautiful house" → "cái nhà đẹp" | "nhà đẹp" | Adjectives follow nouns; lowercase common nouns |
| Date format | "3/12/2024" means March 12 | "3/12/2024" means December 3 | Vietnamese: DD/MM/YYYY |
| Foreign names | "Phạm Nam" for John | "John" | Keep original unless historical equivalent |
| Title caps | "Tìm Hiểu Về Lịch Sử" | "Tìm hiểu về lịch sử" | Only first word and proper nouns capitalized |
| Particle positioning | Subject + Adverb + Verb + Object | Subject + Verb + Object + Adverb | Adverbs come after objects when present |
| Register mixing | Formal narrative with casual dialogue | Match narrative/dialogue to source | Keep formality consistent |

---

## 9. Quick Reference Checklist

**Before Finalizing Translation**

- [ ] All quotation marks are straight double quotes: `" "`
- [ ] No em-dashes (—): prose uses ` - `, dialogue `- `, numeric ranges `–`
- [ ] Numbers formatted as: `999.999,99` (dot for thousands, comma for decimal)
- [ ] Dates formatted as: `DD/MM/YYYY` (e.g., `03/12/2024`)
- [ ] Proper nouns: all syllables capitalized (e.g., `Hà Nội`, `Nguyễn Du`)
- [ ] Book/article titles: only first word and proper nouns capitalized
- [ ] Adjectives follow nouns: "nhà đẹp" not "đẹp nhà"
- [ ] Register/formality consistent throughout document
- [ ] Foreign names kept in original (unless historical Vietnamese equivalent)
- [ ] Loanwords: client instructions followed; consistent usage
- [ ] Dialogue tags positioned correctly
- [ ] Topic-comment structure used naturally where appropriate
- [ ] No literal/word-for-word translations where unnatural
- [ ] Terms of address in original Vietnamese (not translated)
- [ ] Tone and voice matching source material

---

## 10. Sources & References

This guide synthesizes information from:

- [Vietnamese punctuation - Wikipedia](https://en.wikipedia.org/wiki/Vietnamese_punctuation)
- [Language Guidelines – Vietnamese - Unbabel](https://help.unbabel.com/hc/en-us/articles/360022945614-Language-Guidelines-Vietnamese)
- [Style guide - Gengo](https://gengo.com/vi/translators/resources/style-guide/)
- [Journal of Vietnamese Studies Style and Usage Guidelines](https://online.ucpress.edu/DocumentLibrary/JVS/JVS_Style_and_Usage_Guidelines_1_1_09.pdf)
- [Vietnamese Timed Text Style Guide – Netflix](https://partnerhelp.netflixstudios.com/hc/en-us/articles/220447048-Vietnamese-Timed-Text-Style-Guide)
- [Formatting standards & code snippets for Vietnam - Freeformatter.com](https://www.freeformatter.com/vietnam-standards-code-snippets.html)
- [Date and time notation in Vietnam - Wikipedia](https://en.wikipedia.org/wiki/Date_and_time_notation_in_Vietnam)
- [Sino-Vietnamese vocabulary - Wikipedia](https://en.wikipedia.org/wiki/Sino-Vietnamese_vocabulary)
- [Code Mixing and Loan Words in The Vietnamese Vocabulary - ERIC](https://files.eric.ed.gov/fulltext/EJ1474680.pdf)
- [Vietnamese grammar - Wikipedia](https://en.wikipedia.org/wiki/Vietnamese_grammar)
- [Vietnamese basic grammar: sentence structure – YourVietnamese](https://yourvietnamese.com/learn-vietnamese/sentence-structure/)

---

## Revision History

- **2025-12-04**: Initial comprehensive guide created with research from official Vietnamese style guides, academic sources, and translation best practices.

---

**Last Updated**: 2025-12-04
**For**: Vietnamese Book Translation Projects
**Status**: Ready for Reference Use
