#!/usr/bin/env python3
"""Repair PDF-extraction artefacts in translated Markdown.

Two repairs, both conservative:

1. Spacing accents left beside their base letter by LaTeX/TeX PDFs
   (`Go¨del`, `Be´zier`, `Popovic´`, `Mart´ınez`, `Mart´ ınez`, `Holmga˚rd`)
   are recombined into one NFC character (Gödel, Bézier, Popović, Martínez,
   Holmgård). Only an ASCII letter directly followed by the accent (or an accent
   directly followed by a dotless `ı`) is touched, and only when Unicode has a
   precomposed result, so composed Vietnamese text is never altered. Fenced
   code blocks and inline `code` are skipped.
2. Book-specific literal replacements from `books/<id>/style/glyph_repairs.json`
   (`{"replacements": {"(cid:54)=": "≠", "Sch on ¨": "Schön"}}`). `(cid:N)` codes
   are font-specific, so they are never mapped globally. Literals apply
   everywhere because the artefact text is never legitimate.
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple

# Spacing accent -> combining mark.
_COMBINING = {
    "¨": "̈", "´": "́", "ˆ": "̂", "˜": "̃",
    "ˇ": "̌", "˘": "̆", "˙": "̇", "¸": "̧",
    "˚": "̊", "˝": "̋", "ˋ": "̀",
}
_ACCENTS = "".join(_COMBINING)
_DOTLESS_RE = re.compile(rf"([{_ACCENTS}])[ \t]?ı")
_LETTER_ACCENT_RE = re.compile(rf"([A-Za-z])([{_ACCENTS}])")
_CODE_SPAN_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _compose(base: str, accent: str) -> Optional[str]:
    composed = unicodedata.normalize("NFC", base + _COMBINING[accent])
    return composed if len(composed) == 1 else None


def _repair_dotless(match: "re.Match") -> str:
    return _compose("i", match[1]) or match[0]


def _repair_letter_accent(match: "re.Match") -> str:
    return _compose(match[1], match[2]) or match[0]


def _repair_prose(text: str) -> Tuple[str, int]:
    count = 0
    for pattern, fn in ((_DOTLESS_RE, _repair_dotless), (_LETTER_ACCENT_RE, _repair_letter_accent)):
        text, n = _count_sub(pattern, fn, text)
        count += n
    return text, count


def _count_sub(pattern, fn, text):
    changed = 0

    def wrapper(match):
        nonlocal changed
        out = fn(match)
        if out != match[0]:
            changed += 1
        return out

    return pattern.sub(wrapper, text), changed


def _repair_line(line: str) -> Tuple[str, int]:
    """Repair accents outside inline code spans."""
    pieces, last, total = [], 0, 0
    for span in _CODE_SPAN_RE.finditer(line):
        fixed, n = _repair_prose(line[last:span.start()])
        pieces += [fixed, span[0]]
        total += n
        last = span.end()
    fixed, n = _repair_prose(line[last:])
    return "".join(pieces) + fixed, total + n


def repair_text(text: str, replacements: Optional[Dict[str, str]] = None) -> Tuple[str, int]:
    """Return `(repaired_text, number_of_repairs)`."""
    total = 0
    for old in sorted(replacements or {}, key=len, reverse=True):
        n = text.count(old)
        if n:
            text = text.replace(old, replacements[old])
            total += n
    out, in_fence = [], False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
        elif in_fence:
            out.append(line)
        else:
            fixed, n = _repair_line(line)
            out.append(fixed)
            total += n
    return "\n".join(out), total


def load_replacements(path: Path) -> Dict[str, str]:
    """Load the per-book literal replacement map; missing file = empty."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    replacements = data.get("replacements", {})
    if not isinstance(replacements, dict) or not all(
            isinstance(k, str) and k and isinstance(v, str) for k, v in replacements.items()):
        raise ValueError(f"{path}: 'replacements' must map non-empty strings to strings")
    return replacements


def fix_diacritics_file(filepath: Path, replacements: Optional[Dict[str, str]] = None,
                        backup: bool = True, check_only: bool = False) -> int:
    """Repair one file in place (or only count with `check_only`)."""
    if not filepath.exists():
        return 0
    content = filepath.read_text(encoding="utf-8")
    fixed, count = repair_text(content, replacements)
    if count and not check_only:
        if backup:
            filepath.with_suffix(filepath.suffix + ".bak").write_text(content, encoding="utf-8")
        filepath.write_text(fixed, encoding="utf-8")
    return count


if __name__ == "__main__":
    from .book_config import bootstrap_argv

    argv, cfg = bootstrap_argv()
    check = "--check-only" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    if not paths:
        print("Usage: python fix_diacritics.py [--check-only] <file>... [--book ID]")
        _sys.exit(1)
    reps = load_replacements(cfg.style_dir / "glyph_repairs.json")
    for p in paths:
        n = fix_diacritics_file(Path(p), reps, backup=False, check_only=check)
        print(f"{Path(p).name}: {n} artefact(s) {'found' if check else 'fixed'}")
