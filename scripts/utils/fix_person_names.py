#!/usr/bin/env python3
"""
Fix person name capitalization in translated files.
"""

import sys as _sys
from pathlib import Path as _Path

if __package__ in (None, ""):
    # Direct execution: ``python scripts/utils/fix_person_names.py``. This file and its
    # siblings use package-relative imports, so make the repo importable as a
    # package first. Without this the relative imports below raise ImportError.
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    __package__ = "scripts.utils"

import re
from pathlib import Path
from typing import Optional, Set, Dict, List


def load_person_names(terms_file: Optional[Path] = None) -> Set[str]:
    """Load known person names from the book's new_terms.txt."""
    names = set()

    if terms_file is None:
        from .book_config import BookConfigError, load_book
        try:
            terms_file = load_book().new_terms_path
        except BookConfigError:
            return names

    if terms_file.exists():
        with open(terms_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line and not line.strip().startswith('#'):
                    parts = line.split('|')
                    if len(parts) >= 3:
                        english = parts[0].strip()
                        context = parts[2].strip().lower()
                        if 'name' in context or is_person_name_pattern(english):
                            names.add(english)

    return names


def is_person_name_pattern(text: str) -> bool:
    """Detect if text looks like a person name."""
    text = text.strip()
    if any(char in text for char in ['(', ')', '[', ']', '{', '}', '|', '/', '\\']):
        return False
    if text.isupper():
        return False
    words = text.split()
    if len(words) < 2:
        return False
    titles = ['Dr.', 'Professor', 'Mr.', 'Mrs.', 'Ms.', 'Captain']
    if words[0] in titles:
        words = words[1:]
    if not (2 <= len(words) <= 4):
        return False
    for word in words:
        if not word[0].isupper():
            return False
    return True


def normalize_person_name(name: str) -> str:
    """Normalize person name to proper capitalization."""
    lowercase_prefixes = {'van', 'von', 'de', 'di', 'da', 'del', 'della'}
    words = name.split()
    normalized = []
    for i, word in enumerate(words):
        if word in ['Dr.', 'Professor', 'Mr.', 'Mrs.', 'Ms.']:
            normalized.append(word)
        elif i > 0 and word.lower() in lowercase_prefixes:
            normalized.append(word.lower())
        else:
            normalized.append(word.capitalize())
    return ' '.join(normalized)


def fix_person_names_in_text(text: str, known_names: Set[str]) -> tuple[str, int]:
    """Fix person name capitalization in text."""
    fixes = 0
    result = text
    name_lookup = {name.lower(): normalize_person_name(name) for name in known_names}

    for name_lower, name_proper in name_lookup.items():
        words = name_lower.split()
        pattern_parts = [f'[{w[0].upper()}{w[0].lower()}]{w[1:]}' if len(w) > 1 else f'[{w.upper()}{w.lower()}]' for w in words]
        pattern = r'\b' + r'\s+'.join(pattern_parts) + r'\b'
        matches = re.findall(pattern, result, re.IGNORECASE)
        incorrect = [m for m in matches if m != name_proper]
        if incorrect:
            fixes += len(incorrect)
            result = re.sub(pattern, name_proper, result, flags=re.IGNORECASE)

    return result, fixes


def fix_person_names_file(filepath: Path, backup: bool = True,
                          terms_file: Optional[Path] = None) -> int:
    """Fix person names in a file."""
    if not filepath.exists():
        return 0

    known_names = load_person_names(terms_file)
    if not known_names:
        return 0

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content, fixes = fix_person_names_in_text(content, known_names)

    if fixes > 0:
        if backup:
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

    return fixes


if __name__ == '__main__':
    import sys
    from pathlib import Path

    from .book_config import bootstrap_argv

    argv, cfg = bootstrap_argv()
    if len(argv) < 2:
        print("Usage: python fix_person_names.py <file>")
        sys.exit(1)

    filepath = Path(argv[1])
    fixes = fix_person_names_file(filepath, terms_file=cfg.new_terms_path)

    if fixes > 0:
        print(f"✅ Fixed {fixes} person name issues in {filepath.name}")
    else:
        print(f"✅ No person name issues found in {filepath.name}")
