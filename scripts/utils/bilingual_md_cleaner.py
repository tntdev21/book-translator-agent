#!/usr/bin/env python3
"""Turn one GitBook-style bilingual (English + Chinese) chapter into pipeline markdown.

Source shape (e.g. cool8jay/Theory-of-Fun-for-Game-Design): every English block is
followed by its Chinese translation, comic images are HTML ``<img>`` blocks with a
``>`` caption, footnotes are ``[text](#user-content-fn-N)[^N]`` with ``[^N]: ...``
definitions for both languages, numbered in one shared sequence.

Output follows the pipeline conventions (see pcg-in-games source):
- Chinese blocks, Chinese-only tables and ``<hr>`` separators are dropped;
- images -> ``<!-- figure id="comic-<stem>" -->`` (export injects the file);
- footnote refs -> ``<small>k</small>`` renumbered from 1 per chapter, each kept
  definition -> ``<aside class="footnote">k. text</aside>`` after the paragraph that
  first cites it (so the note travels with its paragraph into the same chunk);
- links -> their text, ``* `` lists -> ``- ``, trailing ``\\`` hard breaks removed;
- ``>`` caption / quote lines are kept as ``> text`` (one per block).
"""

import re

# Han + kana only: fullwidth punctuation alone (e.g. "Huckleberry Finn ～ Twain") is not Chinese.
CJK_RE = re.compile(r'[぀-ヿ㐀-䶿一-鿿]')
LIST_RE = re.compile(r'^(\s*)(?:[*•]|(\d+\.))\s+')
FN_DEF_LINE_RE = re.compile(r'^\[\^\d+\]:')
IMG_RE = re.compile(r'<img\s+src="images/([^"]+)"')
TABLE_RE = re.compile(r'(?:^>?\s*<table>.*?</table>\s*$)', re.S | re.M)
FN_REF_RE = re.compile(r'\[([^\]]*)\]\(#user-content-fn-\d+\)\[\^(\d+)\]')
BARE_FN_REF_RE = re.compile(r'\[\^(\d+)\](?!:)')
FN_DEF_RE = re.compile(r'^\[\^(\d+)\]:\s*(.*)$', re.S)
LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
TAG_RE = re.compile(r'</?(?:span|sup|sub|u|font)[^>]*>')


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def figure_id(filename: str) -> str:
    """``1.1.png`` -> ``comic-1-1``; ``about-the-author.png`` -> ``comic-about-the-author``."""
    stem = filename.rsplit('.', 1)[0]
    return 'comic-' + re.sub(r'[^A-Za-z0-9]+', '-', stem).strip('-')


def split_blocks(text: str) -> list[list[str]]:
    """Blank-line separated blocks; a bare ``>`` line also separates quote blocks."""
    blocks, cur = [], []
    for line in text.replace('\r\n', '\n').split('\n'):
        if not line.strip() or line.strip() == '>':
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line.rstrip())
    if cur:
        blocks.append(cur)
    return blocks


def clean_inline(text: str) -> str:
    """Strip inline HTML/markdown noise that the pipeline cannot render."""
    text = TAG_RE.sub('', text)
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = text.replace('～', '~').replace('\\$', '$').replace('\\*', '*').replace('`', '')
    text = re.sub(r'\\$', '', text)                       # trailing hard break
    return re.sub(r'[ \t]+', ' ', text).strip()


def _html_block(block: list[str]) -> tuple[list[str], list[str]]:
    """Image or styled ``<p>`` block -> (output lines, image filenames)."""
    joined = '\n'.join(block)
    images = IMG_RE.findall(joined)
    out = [f'<!-- figure id="{figure_id(name)}" -->' for name in images]
    body = re.sub(r'<(?:p|div|img)[^>]*>|</(?:p|div)>', '\n', joined)
    for part in re.split(r'<br\s*/?>|\n', body):
        part = clean_inline(part)
        if part and not has_cjk(part):
            out.append(part)
    return out, images


def _english_items(block: list[str]) -> list[tuple[str, bool]]:
    """English content of one block as (paragraph or list item, is_quote) pairs.

    EN and CN often share a block (list items end in ``\\`` with the CN line right
    under them), so filtering is per line: CN lines are dropped; a numbered line with
    a pure-CN tail (``1. Linguistic 语言``) keeps its English head. Each list line starts a
    new item (``* ``/``• `` -> ``- ``, ``N.`` kept, indented = nested); other lines join.
    """
    quote = block[0].lstrip().startswith('>')
    items: list[str] = []
    joinable = False
    for line in block:
        line = re.sub(r'^\s*>\s?', '', line) if quote else line
        if line.lstrip().startswith('{%'):
            continue
        lm = LIST_RE.match(line)
        if has_cjk(line):
            head, tail = CJK_RE.split(line, maxsplit=1)[0], CJK_RE.search(line).start()
            numbered = lm and re.match(r'\s*\d+\.', line)
            if not (numbered and LIST_RE.sub('', head).strip()
                    and not re.search(r'[A-Za-z]', line[tail:])):
                continue
            line = head
        if lm:
            bullet = lm.group(2) or '-'                     # keep "N." numbering
            items.append(('  ' if lm.group(1) else '') + f'{bullet} ' + line[lm.end():].strip())
            joinable = True
        elif items and (joinable or not quote):
            items[-1] += ' ' + line.strip()
        else:
            items.append(line.strip())
            joinable = not quote
    return [(it, quote) for it in items]


def clean_chapter(text: str, heading: str | None) -> tuple[list[str], list[str]]:
    """Return (markdown blocks, image filenames) for one source file.

    ``heading`` replaces the file's own ``# `` line (or is added when it has none).
    """
    text = TABLE_RE.sub('', text)                         # Chinese-only HTML tables
    defs, body = {}, []
    for block in split_blocks(text):
        if FN_DEF_LINE_RE.match(block[0]):
            for note in re.split(r'\n(?=\[\^\d+\]:)', '\n'.join(block)):
                m = FN_DEF_RE.match(note)
                defs[m.group(1)] = m.group(2)
        else:
            body.append(block)

    out = [f'# {heading}'] if heading else []
    images: list[str] = []
    renum: dict[str, int] = {}

    def ref(m: re.Match) -> str:
        num = m.group(2) if m.re is FN_REF_RE else m.group(1)
        label = m.group(1) if m.re is FN_REF_RE else ''
        renum.setdefault(num, len(renum) + 1)
        return f'{label}<small>{renum[num]}</small>'

    for block in body:
        first = block[0].lstrip()
        if first.startswith('#'):
            continue                                       # replaced by ``heading``
        if first.startswith(('<p', '<div')):
            lines, imgs = _html_block(block)
            out.extend(lines)
            images.extend(imgs)
            continue
        if first.startswith(('<hr', '{%')):
            continue
        for item, quote in _english_items(block):
            before = len(renum)
            para = clean_inline(BARE_FN_REF_RE.sub(ref, FN_REF_RE.sub(ref, item)))
            # keep the marker outside emphasis so ``*Title<small>3</small>*`` stays italic
            para = re.sub(r'(<small>\d+</small>)(\*+)', r'\2\1', para)
            if not para.strip():
                continue
            out.append(f'> {para.strip()}' if quote else para)
            for num, k in list(renum.items())[before:]:
                note = clean_inline(' '.join(defs.get(num, '').split('\n')))
                out.append(f'<aside class="footnote">{k}. {note}</aside>')
    return out, images


def missing_notes(blocks: list[str]) -> list[str]:
    """Footnote numbers whose ``<aside>`` came out empty (definition not found)."""
    return [m.group(1) for b in blocks
            for m in [re.match(r'<aside class="footnote">(\d+)\.\s*</aside>$', b)] if m]
