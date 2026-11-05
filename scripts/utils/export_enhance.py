"""Export-time content enhancements applied to merged markdown (never to translated/*.md).

- ``apply_chapter_headings``: "# 2. Title" -> "# Chương 2: Title" (templates from book.yaml
  ``headings``), including the manual TOC list under "# Mục lục".
- ``inject_figures``: place ``![Hình X.Y](src)`` before the paragraph that starts with
  "Hình X.Y" when ``images/fig-X-Y.png`` exists (dropping duplicated "(a) ..." label lines
  above it); replace ``<!-- figure id="X" -->`` lines (tables, equations) by ``images/X.png``.

Both are no-ops without configuration / images, so other books are unaffected.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .markdown_converter import load_toc_language_config
from .reflow_captions import reflow_split_captions

CHAPTER_RE = re.compile(r'^(\d+)\.\s+(\S.*)$')
APPENDIX_RE = re.compile(r'^([A-Z])\.\s+(\S.*)$')
# Caption = "Hình X.Y:" (colon required); body references like "Hình 7.9 cho thấy..." must not match.
CAPTION_RE = re.compile(r'^\**\s*Hình\s+(\d+|[A-Z])\.(\d+)\s*:')
MARKER_RE = re.compile(r'^<!--\s*figure\s+id="([A-Za-z0-9_-]+)"\s*-->$')
SUBLABEL_LINE_RE = re.compile(r'^\([a-z]\)(\s|$)')
MARKER_SCALE = 1.4   # source text is 10pt, the export body 14.4pt


def _map_title(text: str, headings: dict) -> str:
    chapter_fmt = headings.get('chapter_format')
    appendix_fmt = headings.get('appendix_format')
    m = CHAPTER_RE.match(text)
    if m and chapter_fmt:
        return chapter_fmt.format(n=m.group(1), title=m.group(2))
    m = APPENDIX_RE.match(text)
    if m and appendix_fmt:
        return appendix_fmt.format(n=m.group(1), title=m.group(2))
    return text


def apply_chapter_headings(content: str, headings: dict | None) -> str:
    """Rewrite numbered "# " headings and the TOC list that mirrors them."""
    if not headings or not (headings.get('chapter_format') or headings.get('appendix_format')):
        return content
    toc_headers = {h.lower() for h in load_toc_language_config()['toc_headers']}
    out, in_toc = [], False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('# '):
            body = stripped[2:].strip()
            if body.lower() in toc_headers:
                in_toc = True
                out.append(line)
                continue
            in_toc = False
            out.append('# ' + _map_title(body, headings))
        elif in_toc and stripped and not stripped.startswith('<'):
            out.append(_map_title(stripped, headings))
        else:
            out.append(line)
    return '\n'.join(out)


def figure_id(file_name: str) -> str:
    return Path(file_name).stem.removeprefix('fig-').replace('-', '.')


def _drop_subfigure_labels(out: list[str]) -> None:
    """Remove "(a) ..." label lines directly above a caption whose image is injected.

    Walks back over blank lines and HTML comments (page markers); stops at the first
    other line that is not a label, so body text is never dropped.
    """
    i = len(out) - 1
    drop = []
    while i >= 0:
        s = out[i].strip()
        if not s or s.startswith('<!--'):
            i -= 1
        elif SUBLABEL_LINE_RE.match(s):
            drop.append(i)
            i -= 1
        else:
            break
    for i in drop:  # indices are descending
        del out[i]


def _marker_width_pt(images_dir: Path, name: str) -> str:
    """Display width suffix for a marker image: source width scaled to body-text size."""
    try:
        for entry in json.loads((images_dir / 'figures.json').read_text(encoding='utf-8')):
            if entry.get('file') == name:
                bbox = entry['bbox']
                return f'{{width={(bbox[2] - bbox[0]) * MARKER_SCALE:.0f}pt}}'
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        pass
    return ''


def inject_figures(content: str, images_dir: Path | None, src_mode: str = 'relative',
                   warn=print) -> tuple[str, list[str]]:
    """Insert figure images.

    - Caption lines "Hình X.Y" get ``images/fig-X-Y.png`` placed before them (and the
      subfigure label lines above them dropped, since the image already carries them).
    - ``<!-- figure id="X" -->`` lines are replaced by ``images/X.png`` (no caption);
      a missing image warns and drops the line.

    ``src_mode``: ``'relative'`` -> ``images/<file>`` (EPUB/HTML, files copied alongside),
    ``'file'`` -> absolute ``file://`` URI (PDF). Returns ``(content, used_files)``.
    Captions without an image keep their text and trigger ``warn``.
    """
    images_dir = Path(images_dir) if images_dir is not None else None
    have_dir = images_dir is not None and images_dir.is_dir()

    def src_for(name: str) -> str:
        return f'file://{(images_dir / name).resolve()}' if src_mode == 'file' else f'images/{name}'

    # Data check only: a caption splitting a paragraph is repaired in the chunks
    # (reflow_captions.py), never patched here.
    split = reflow_split_captions(content)[1]
    if split:
        warn(f'⚠️  Caption splits a paragraph ({", ".join(split)}); '
             'run scripts/utils/reflow_captions.py --book <id> --apply')

    out, used = [], []
    for line in content.split('\n'):
        marker = MARKER_RE.match(line.strip())
        if marker:
            name = f'{marker.group(1)}.png'
            if have_dir and (images_dir / name).exists():
                if out and out[-1].strip():
                    out.append('')
                out.extend([f'![]({src_for(name)}){_marker_width_pt(images_dir, name)}', ''])
                if name not in used:
                    used.append(name)
            else:
                warn(f'⚠️  No image for figure marker "{marker.group(1)}" ({name}); line dropped')
            continue
        m = CAPTION_RE.match(line.strip()) if have_dir else None
        if m:
            fig = f'{m.group(1)}.{m.group(2)}'
            name = f'fig-{m.group(1)}-{m.group(2)}.png'
            if (images_dir / name).exists() and name not in used:
                _drop_subfigure_labels(out)
                if out and out[-1].strip():
                    out.append('')
                out.extend([f'![Hình {fig}]({src_for(name)})', ''])
                used.append(name)
            elif not (images_dir / name).exists():
                warn(f'⚠️  No image for Hình {fig} ({name}); keeping caption only')
        out.append(line)
    return '\n'.join(out), used
