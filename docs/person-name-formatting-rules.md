# Person Name Formatting Rules

## Standard Format

All person names, place name, city name in English MUST follow proper capitalization:
- **First letter of each part capitalized**
- **Remaining letters lowercase** (unless acronym or special case)

## Examples

### ✅ Correct
- Alice Chen
- Alice
- Marcus Webb
- Marcus
- Webb
- Elena Marsh
- Elena
- Marsh
- Jonas Faukman
- John Doe
- Mary Jane Watson

### ❌ Incorrect
- Alice chen (lowercase last name)
- alice Chen (lowercase first name)
- ALICE CHEN (all caps)
- alice chen (all lowercase)
- alice (all lowercase)
- chen (all lowercase)
- Marcus webb (lowercase last name)

## Special Cases

### Prefixes and Particles
- **van, von, de, di, da, del, della, etc.** - Usually lowercase when in middle
  - Examples: Ludwig van Beethoven, Leonardo da Vinci, Vincent van Gogh
  - But capitalized when starting: Van Gogh (without first name)

### Hyphenated Names
- **Each part capitalized**
  - Examples: Mary-Jane Watson, Jean-Claude Van Damme

### Titles
- **Capitalize titles when part of name**
  - Dr. Alice Chen
  - Professor Marcus Webb
  - Captain John Smith

### Abbreviations
- **Keep original capitalization**
  - J.K. Rowling
  - H.G. Wells

## Detection Patterns

Person names can be detected by:
1. Capitalized words (2+ parts typically)
2. Common first/last name patterns
3. Context clues (Dr., Professor, titles)
4. Glossary/term list entries marked as names

## Implementation

The fix script should:
1. Build a list of known person names from glossary/terms
2. Detect person name patterns in text
3. Fix capitalization to match standard format
4. Preserve special cases (prefixes, hyphens, titles)
