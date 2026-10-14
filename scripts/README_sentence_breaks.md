# Sentence Break Detection & Fix Tools

## Problem

During translation, sentences sometimes get broken across multiple lines improperly:

```markdown
❌ WRONG:
Chuyến đi cay đắng qua
Công viên Folimanka đã khiến anh lạnh cóng, và
giờ anh cởi đôi giày da dính
tuyết và xoa bàn chân đóng băng.

✅ CORRECT:
Chuyến đi cay đắng qua Công viên Folimanka đã khiến anh lạnh cóng, và giờ anh cởi đôi giày da dính tuyết và xoa bàn chân đóng băng.
```

## Tools

### 1. Check Formatting (Detection)

**Script:** `utils/fix_formatting.py`

Detects 3 types of issues:
1. Word breaks (words split across lines)
2. Excessive blank lines (>2 consecutive)
3. **Sentence breaks** (sentences split across lines)

**Usage:**
```bash
# Check all translated files (using unified script - recommended)
python3 scripts/fix.py --check-only

# Or use individual script directly
python3 scripts/utils/fix_formatting.py
```

**Output:**
```
Found issues in 2 files:

chunk_037.md:
------------------------------------------------------------
  Line 5: Sentence break - "iên Folimanka đã khiến anh lạnh cóng, và" → "giờ anh cởi đôi giày da dính"
  Line 11: Sentence break - " phụ nữ trên Cầu Charles tiếp tục ám ảnh" → "anh. Mọi thứ về cuộc"

SUMMARY:
  Total files with issues: 2
  Total issues: 15
  Word breaks: 0
  Excessive blank lines: 0
  Sentence breaks: 15
```

### 2. Fix Sentence Breaks (Auto-fix)

**Script:** `utils/fix_sentence_breaks.py` (or use unified `fix.py`)

Automatically joins improperly broken sentences.

**Features:**
- ✅ Multi-pass algorithm (handles sentences broken across many lines)
- ✅ Preserves proper paragraph breaks
- ✅ Creates backup files (.bak)
- ✅ Skips markdown elements (#, -, *, >)
- ✅ Smart detection using Vietnamese punctuation rules

**Usage:**

```bash
# Recommended: Use unified fix script
python3 scripts/fix.py translated/chunk_037.md
python3 scripts/fix.py --check-only

# Or use individual script directly
python3 scripts/utils/fix_sentence_breaks.py translated/chunk_037.md
python3 scripts/utils/fix_sentence_breaks.py --no-backup
python3 scripts/utils/fix_sentence_breaks.py --check-only
```

**Output:**
```
Processing 1 files...

📋 Backup created: translated/chunk_037.md.bak
✓ chunk_037.md: Fixed 9 sentence breaks

============================================================
Fixed 9 sentence breaks in 1 files
Backup files created with .bak extension
```

## How It Works

### Detection Logic

A line has an improper break if:
1. Line doesn't end with proper punctuation (`.`, `!`, `?`, `...`, `—`, `"`, `»`, `)`, `]`, `…`)
2. AND line is substantial (> 10 characters)
3. AND next line starts with lowercase or Vietnamese lowercase letter
4. AND next line is not empty/comment/markdown

### Vietnamese Lowercase Letters

The script recognizes Vietnamese diacritics:
- `àáảãạ` `ăằắẳẵặ` `âầấẩẫậ`
- `èéẻẽẹ` `êềếểễệ`
- `ìíỉĩị`
- `òóỏõọ` `ôồốổỗộ` `ơờớởỡợ`
- `ùúủũụ` `ưừứửữự`
- `ỳýỷỹỵ`
- `đ`

### Multi-Pass Algorithm

The fix script uses multiple passes because sentences can be broken across many lines:

**Pass 1:**
```
Line 1: "text qua"           →  "text qua công viên"
Line 2: "công viên và"       →  "công viên và giờ anh"
Line 3: "giờ anh cởi"        →  (unchanged)
```

**Pass 2:**
```
Line 1: "text qua công viên và" → "text qua công viên và giờ anh cởi"
Line 2: "giờ anh cởi"          →  (unchanged)
```

Continues until no more fixes needed (max 20 passes).

## Integration

**Translation Workflow:**

**Recommended workflow (using unified script):**
```bash
# 1. Translate chunk → translated/chunk_XXX.md
# 2. Fix all formatting issues in one step
python3 scripts/fix.py translated/chunk_XXX.md
# 3. Update manifest
```

**Alternative workflow (using individual scripts):**
1. Translate chunk → `translated/chunk_XXX.md`
2. Fix sentence breaks → `python3 scripts/utils/fix_sentence_breaks.py translated/chunk_XXX.md`
3. Normalize dashes → `python3 scripts/utils/normalize_dashes.py`
4. Check formatting → `python3 scripts/utils/fix_formatting.py`
5. Update manifest

## Limitations

**Edge Case:** Lines ending with certain Vietnamese words followed by capitalized proper nouns:

```markdown
Chuyến đi cay đắng qua
Công viên Folimanka đã khiến...
```

Here "qua" (through) doesn't end with punctuation, but "Công viên Folimanka" (Folimanka Park) is a proper noun that must be capitalized. The script may not join these automatically since it sees a capital letter starting the next line.

**Solution:** Manual review or context-aware improvements in future versions.

## Examples

### Before Fix:
```markdown
Người phụ nữ trên Cầu Charles tiếp tục ám ảnh
anh. Mọi thứ về cuộc
gặp gỡ ngắn ngủi đều có vẻ siêu thực... cách cô ta
di chuyển ma mị, ánh mắt
trống rỗng, mùi chết chóc, và cách cô ta dường
như không nghe thấy anh... như thể cô ta sống
trong một thực tại song song.
```

### After Fix:
```markdown
Người phụ nữ trên Cầu Charles tiếp tục ám ảnh anh. Mọi thứ về cuộc gặp gỡ ngắn ngủi đều có vẻ siêu thực... cách cô ta di chuyển ma mị, ánh mắt trống rỗng, mùi chết chóc, và cách cô ta dường như không nghe thấy anh... như thể cô ta sống trong một thực tại song song.
```

## Testing

```bash
# Create test file
cat > test.md << 'EOF'
Câu này bị
ngắt ra làm
nhiều dòng.

Đây là câu mới. Và đây cũng vậy.
EOF

# Check issues (unified script)
python3 scripts/fix.py test.md --check-only

# Fix it (unified script)
python3 scripts/fix.py test.md

# Or use individual script
python3 scripts/utils/fix_sentence_breaks.py test.md
```

## History

- **2025-11-28**: Created to fix sentence break issues in chapter 37 (line 7833 of source)
