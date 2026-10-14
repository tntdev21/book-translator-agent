# Term Logging Script - Usage Guide

## Problem Solved
Previously, `style/new_terms.txt` grew to **139GB** (3.4 billion lines) due to infinite append loops.

## Solution
Created `log_terms.py` - a safe term logging script with duplicate prevention.

## Usage

### Add a single term
```bash
python scripts/log_terms.py "term | translation | context | chunk_id"
```

**Example:**
```bash
python scripts/log_terms.py "GABA | GABA | Brain chemistry | chunk_064"
```

### Check for duplicates
```bash
python scripts/log_terms.py --check
```

## Features
- ✅ **Duplicate detection** - Prevents adding the same term twice
- ✅ **Case-insensitive matching** - "GABA" and "gaba" are treated as duplicates
- ✅ **Auto-formatting** - Adds "- " prefix if missing
- ✅ **Safe file handling** - Creates file if it doesn't exist
- ✅ **Progress feedback** - Shows what was added or skipped

## Output Examples

**When adding a new term:**
```
✅ Added: - GABA | GABA | Brain chemistry | chunk_064
```

**When term already exists:**
```
ℹ️  Term already exists: GABA
```

**When checking for duplicates:**
```
⚠️  Found 2 duplicate terms:
  - crucifix bastion (lines 32, 171)
  - úzsi (lines 33, 174)
```

## Integration

This script is referenced in `CLAUDE.md` instructions:

```
Log thuật ngữ mới:
  python3 scripts/log_terms.py "term | translation | context | chunk_XXX"
  (Script tự động ngăn duplicate)
```

## Prevention

The script prevents:
1. Infinite loops causing file bloat
2. Duplicate entries
3. Manual merge conflicts
4. Data corruption

## History

- **2025-11-28**: Created to fix 139GB file issue caused by GABA term loop
