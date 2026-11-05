#!/usr/bin/env python3
"""Import a GitBook bilingual (EN + Chinese) markdown book as a pipeline source.

Replaces ``extract.py`` for books that already exist as per-chapter markdown with an
interleaved Chinese translation (no PDF). Reads ``SUMMARY.md`` for chapter order and
titles, keeps English only, and writes:

- ``books/<id>/source/full_text.md``  (front blocks, Contents list, chapters)
- ``books/<id>/images/comic-*.png``    (downscaled, palette-quantized)
- ``books/<id>/cover.jpg``             (from ``images/cover.png``)

Usage:
    ./venv/bin/python scripts/import_bilingual_md.py --book theory-of-fun \\
        --src temp/Theory-of-Fun-for-Game-Design [--max-width 900]
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from utils.bilingual_md_cleaner import (  # noqa: E402
    clean_chapter, figure_id, has_cjk, missing_notes)

SUMMARY_RE = re.compile(r'^\*\s+\[(.+?)\]\(([^)]+\.md)\)')
SKIP_FILES = {'README.md', 'cover.md'}                 # repo readme; cover -> cover.jpg
FRONT_FILES = {'dedication.md': 'dedication'}          # rendered as <!-- front --> blocks
CHAPTER_RE = re.compile(r'^Chapter\s+(\d+)\s+(.+)$')


def english_title(entry: str) -> str:
    """``Chapter 1 Why Write This Book? 第一章 ...`` -> ``1. Why Write This Book?``."""
    title = re.split(r'[㐀-鿿]', entry, maxsplit=1)[0].strip()
    m = CHAPTER_RE.match(title)
    return f'{m.group(1)}. {m.group(2)}' if m else title


def read_summary(src: Path) -> list[tuple[str, str]]:
    """Ordered (filename, English title) pairs from SUMMARY.md."""
    entries = []
    for line in (src / 'SUMMARY.md').read_text(encoding='utf-8').splitlines():
        m = SUMMARY_RE.match(line.strip())
        if m and m.group(2) not in SKIP_FILES:
            entries.append((m.group(2), english_title(m.group(1))))
    return entries


def save_image(src: Path, dest: Path, max_width: int) -> None:
    """Downscale to ``max_width`` and store as a 256-colour PNG (comics are flat art)."""
    with Image.open(src) as im:
        im = im.convert('RGB')
        if im.width > max_width:
            im = im.resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS)
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(dest, optimize=True)


def build(src: Path, book_dir: Path, max_width: int) -> int:
    entries = read_summary(src)
    blocks = ['<!-- front id="title-page" -->', '<!-- /front -->', '# Contents']
    blocks += [title for name, title in entries if name not in FRONT_FILES]
    images, problems = [], []
    for name, title in entries:
        text = (src / name).read_text(encoding='utf-8')
        front = FRONT_FILES.get(name)
        body, imgs = clean_chapter(text, None if front else title)
        if front:  # text only: a figure inside a front block would render as text
            body = [f'<!-- front id="{front}" -->'] + [
                b for b in body if not b.startswith('<!--')] + ['<!-- /front -->']
        else:
            images += imgs
        blocks += body
        problems += [f'{name}: footnote {n} has no definition' for n in missing_notes(body)]

    text = '\n\n'.join(blocks) + '\n'
    problems += [f'CJK left: {ln[:60]}' for ln in text.splitlines() if has_cjk(ln)]
    problems += [f'missing image: {n}' for n in images if not (src / 'images' / n).exists()]

    (book_dir / 'source').mkdir(parents=True, exist_ok=True)
    (book_dir / 'source' / 'full_text.md').write_text(text, encoding='utf-8')

    out_img = book_dir / 'images'
    out_img.mkdir(exist_ok=True)
    for name in dict.fromkeys(images):
        if (src / 'images' / name).exists():
            save_image(src / 'images' / name, out_img / f'{figure_id(name)}.png', max_width)
    cover = src / 'images' / 'cover.png'
    if cover.exists():
        with Image.open(cover) as im:
            im.convert('RGB').save(book_dir / 'cover.jpg', quality=90)

    size = sum(f.stat().st_size for f in out_img.glob('*.png')) / 1e6
    print(f'✅ {len(entries)} files, {len(text.split())} words -> {book_dir}/source/full_text.md')
    print(f'🖼  {len(set(images))} images, {size:.1f} MB (max width {max_width}px)')
    for p in problems:
        print(f'⚠️  {p}')
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--book', required=True, help='book id under books/')
    ap.add_argument('--src', required=True, type=Path, help='GitBook folder with SUMMARY.md')
    ap.add_argument('--max-width', type=int, default=900, help='image width cap in px')
    args = ap.parse_args()
    book_dir = Path(__file__).resolve().parent.parent / 'books' / args.book
    if not (args.src / 'SUMMARY.md').exists():
        print(f'❌ {args.src}/SUMMARY.md not found', file=sys.stderr)
        return 2
    return build(args.src, book_dir, args.max_width)


if __name__ == '__main__':
    sys.exit(main())
