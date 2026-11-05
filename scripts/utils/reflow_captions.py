#!/usr/bin/env python3
"""Repair paragraphs split by a top-of-page figure/table caption (and mid-sentence blank lines).

Older technical extractions emitted a figure that sat at the top of a PDF page between the
two halves of a sentence that crossed the page break:

    ... (hoặc các điểm ảnh cùng màu,       <- paragraph, sentence unfinished
    <!-- Page 37 -->
    Hình 3.2: (a) Một hầm ngục ...         <- caption (optionally "(a) ... (b) ..." labels above it)
    trong trường hợp ảnh) có thể ...       <- continuation, starts lowercase

Rewritten to the layout the fixed extractor (pdf_technical_layout) now produces:

    ... (hoặc các điểm ảnh cùng màu,
    <!-- Page 37 -->
    trong trường hợp ảnh) có thể ...

    Hình 3.2: (a) Một hầm ngục ...

Works on EN source (Fig./Table) and VI translations (Hình/Bảng). Text is only moved, never edited.

Usage:
    python scripts/utils/reflow_captions.py --book <id>            # report only
    python scripts/utils/reflow_captions.py --book <id> --apply    # rewrite files
    python scripts/utils/reflow_captions.py --apply FILE...        # specific files
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

CAPTION_RE = re.compile(r'^\**\s*(Fig\.|Figure|Table|Hình|Bảng)\s+(\d+|[A-Z])\.\d+\s*:')
TABLE_CAPTION_RE = re.compile(r'^\**\s*(Table|Bảng)\s')
PANEL_LABEL_RE = re.compile(r'^\([a-z]\)\s')
FIGURE_MARKER_RE = re.compile(r'^<!--\s*figure\s+id=')
TABLE_BODY_RE = re.compile(r'^(\d+\.\s|\|)')   # numbered/pipe table rows right after a table caption
PAGE_RE = re.compile(r'^<!--\s*Page\s+\d+\s*-->$')
BOUNDARY = '<!-- chunk-boundary -->'               # joins chunk files so splits across chunks are seen
SENTENCE_END_RE = re.compile(r'[.!?:;…"”)\]]\**$')


def _is_figure_line(s: str) -> bool:
    return bool(CAPTION_RE.match(s) or PANEL_LABEL_RE.match(s) or FIGURE_MARKER_RE.match(s))


def _starts_lower(s: str) -> bool:
    """Starts with a lowercase Latin letter (incl. Vietnamese "đ", "ư"; not Greek/symbols)."""
    return bool(s) and s[0].islower() and unicodedata.name(s[0], '').startswith('LATIN')


LEAD_PUNCT_RE = re.compile(r'^(?:\[\d+(?:,\s*\d+)*\]\s*|[(\[`"“\'])+')   # "[13] ", "(", "`"


def _continues(s: str) -> bool:
    """Continuation of an unfinished sentence: lowercase after any leading citation/bracket/
    backtick ("[13] is", "(blocks", "`minimize` statement"); never a code fence."""
    return not s.startswith('```') and _starts_lower(LEAD_PUNCT_RE.sub('', s))


def _is_marker(s: str) -> bool:
    return bool(PAGE_RE.match(s)) or s == BOUNDARY


def caption_id(line: str) -> str | None:
    m = CAPTION_RE.match(line.strip())
    return f'{"T" if m.group(1) in ("Table", "Bảng") else "F"}{m.group(2)}.{m.group(0).split(".")[-1].rstrip(": ")}' \
        if m else None


def reflow_split_captions(text: str, force: set[str] | None = None) -> tuple[str, list[str]]:
    """Return ``(text, repaired caption ids)``; see module docstring.

    ``force``: caption ids (from the aligned source chunk) to repair even when the
    translated continuation does not start lowercase. Repeats until stable: a paragraph
    split twice (figures on consecutive pages) exposes its second split after the first repair.
    """
    repairs = []
    for _ in range(50):  # each pass rejoins one more fragment
        # A forced id applies once; later passes only follow the unfinished-sentence signal.
        text, ids = _reflow_once(text, force and force - set(repairs))
        if not ids:
            break
        repairs.extend(i for i in ids if i not in repairs)
    return text, repairs


def _reflow_once(text: str, force: set[str] | None) -> tuple[str, list[str]]:
    lines = text.split('\n')
    out, i, repairs = [], 0, []
    while i < len(lines):
        s = lines[i].strip()
        if not (CAPTION_RE.match(s) or (_is_figure_line(s) and _figure_block_has_caption(lines, i))):
            out.append(lines[i])
            i += 1
            continue
        # Figure block: caption/label/figure-marker lines (+ table rows), blanks and page markers between.
        j, block, carried, in_table = i, [], [], False
        while j < len(lines):
            t = lines[j].strip()
            if t and (_is_figure_line(t) or (in_table and TABLE_BODY_RE.match(t))):
                block.append(lines[j])
                if CAPTION_RE.match(t):
                    in_table = bool(TABLE_CAPTION_RE.match(t))
            elif t and _is_marker(t):
                carried.append(t)
            elif t:
                break
            j += 1
        # Paragraph before the block: last text line of out, skipping blanks and markers.
        p = len(out) - 1
        while p >= 0 and (not out[p].strip() or _is_marker(out[p].strip())):
            p -= 1
        before = out[p].rstrip() if p >= 0 else ''
        after = lines[j].strip() if j < len(lines) else ''
        prose_before = before and not before.lstrip().startswith(('#', '<', '`', '-', '|')) \
            and not before.endswith(('```', '>')) and not _is_figure_line(before.strip())
        ids = [cid for cid in map(caption_id, block) if cid]
        forced = bool(force and set(ids) & force)
        split = forced or (not SENTENCE_END_RE.search(before) and _continues(after))
        if not (prose_before and after and not after.startswith(('#', '<!--')) and split):
            out.extend(lines[i:j])
            i = j
            continue
        markers = [ln.strip() for ln in out[p + 1:] if ln.strip()] + carried
        del out[p + 1:]
        # Page markers stay inside the rejoined paragraph; chunk boundaries move after the
        # figure so both paragraph halves land in the same chunk.
        out.extend([m for m in markers if m != BOUNDARY] + [lines[j], ''])
        prev_body = False
        for ln in block:
            body = bool(TABLE_BODY_RE.match(ln.strip())) and not CAPTION_RE.match(ln.strip())
            if out[-1] != '' and not (body and prev_body):
                out.append('')
            out.append(ln)
            prev_body = body
        out.append('')
        if BOUNDARY in markers:
            out.extend([BOUNDARY, ''])
        repairs.extend(ids)
        i = j + 1
        # Drop blank lines that followed the continuation; one separator already emitted.
        while i < len(lines) and not lines[i].strip():
            i += 1
    return '\n'.join(out), repairs


def join_fragments(text: str) -> tuple[str, int]:
    """Join paragraph lines split by a blank line mid-sentence ("one works as an" / "attractor
    and ..."), left by older extractions of indented list-item bodies. Returns (text, joins)."""
    lines, out, joins, fence = text.split('\n'), [], 0, False
    for ln in lines:
        s = ln.strip()
        if s.startswith('```') or (fence and s.endswith('```')):
            fence = not fence if s.count('```') == 1 else fence
        prev = out[-2].rstrip() if len(out) >= 2 else ''
        # prev >= 40 chars: a wrapped prose line, not a short pseudocode/equation line.
        if (not fence and out and out[-1] == '' and _starts_lower(s) and len(prev) >= 40
                and not prev.lstrip().startswith(('#', '<', '`', '-', '|')) and not prev.endswith(('```', '>'))
                and not _is_figure_line(prev.strip()) and not SENTENCE_END_RE.search(prev)):
            out.pop()
            out[-1] = prev + ('' if prev.endswith('-') else ' ') + s
            joins += 1
            continue
        out.append(ln)
    return '\n'.join(out), joins


def reflow_files(texts: list[str], force: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Reflow consecutive chunk files as one stream; returns per-file texts + repaired ids."""
    joined = f'\n\n{BOUNDARY}\n\n'.join(t.strip('\n') for t in texts)
    new, ids = reflow_split_captions(joined, force)
    new, joins = join_fragments(new)
    ids = ids + [f'J{k}' for k in range(joins)]
    parts = re.split(r'\n*' + re.escape(BOUNDARY) + r'\n*', new)
    assert len(parts) == len(texts), 'chunk boundary lost during reflow'
    return [old if part.strip('\n') == old.strip('\n') else part.strip('\n') + '\n'
            for old, part in zip(texts, parts)], ids


def _figure_block_has_caption(lines: list[str], i: int) -> bool:
    """A label/marker line only starts a figure block if a caption follows within the block."""
    for ln in lines[i:i + 8]:
        s = ln.strip()
        if CAPTION_RE.match(s):
            return True
        if s and not (_is_figure_line(s) or PAGE_RE.match(s)):
            return False
    return False


def _book_files(book_id: str) -> tuple[list[Path], list[Path], list[Path]]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from utils.book_config import load_book
    cfg = load_book(book_id)
    full_text = [cfg.source_file] if cfg.source_file.exists() else []
    return (full_text, sorted(cfg.chunks_dir.glob('chunk_*.md')),
            sorted(cfg.translated_dir.glob('chunk_*.md')))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='*', type=Path)
    ap.add_argument('--book')
    ap.add_argument('--apply', action='store_true', help='rewrite files (default: report only)')
    args = ap.parse_args()
    # Groups reflowed as one stream: full text, source chunks, translated chunks (forced by
    # the captions repaired in the source chunks, since translations may reorder words).
    groups = [[f] for f in args.files] if args.files else list(_book_files(args.book))
    total, src_ids = 0, None
    for files in groups:
        if not files:
            continue
        texts = [f.read_text(encoding='utf-8') for f in files]
        force = src_ids if files[0].parent.name == 'translated' else None
        new, ids = reflow_files(texts, force)
        if files[0].parent.name == 'chunks':
            src_ids = set(ids)
        total += len(ids)
        changed = [f for f, old, n in zip(files, texts, new) if old != n]
        caps = [i for i in ids if not i.startswith('J')]
        if ids:
            print(f'{"fixed" if args.apply else "split"}: {files[0].parent} ({", ".join(caps)}; '
                  f'{len(ids) - len(caps)} mid-sentence blank-line join(s))')
            print('   files: ' + ', '.join(f.name for f in changed))
        if args.apply:
            for f, old, n in zip(files, texts, new):
                if old != n:
                    f.write_text(n, encoding='utf-8')
    print(f'{total} split paragraph(s) {"repaired" if args.apply else "found"}')
    return 1 if total and not args.apply else 0


if __name__ == '__main__':
    sys.exit(main())
