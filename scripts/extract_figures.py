#!/usr/bin/env python3
"""Crop every figure out of a book's source PDFs.

Figures are not part of the extracted text (images, vector drawings and the
Times/Helvetica text inside them are all skipped by extraction), so each
"Fig. X.Y: ..." caption is located in the chapter PDFs and the region above it
is rendered to ``books/<id>/images/fig-X-Y.png``. A manifest is written to
``images/figures.json``.

Region rule: everything between the nearest body-text line above the caption
(or the top margin) and the caption: image bboxes, vector curves/rects/lines
and skipped-font words (figure-internal labels). Body text that sits inside a
drawing is treated as part of the figure.

Usage:
    python scripts/extract_figures.py --book <id> [--pdf-dir DIR] [--dpi 200]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.book_config import REPO_ROOT, add_book_argument, get_config_from_args  # noqa: E402

CAPTION_NUM_RE = re.compile(r"^(\d+|[A-Z])\.(\d+):?$")
HEADER_ZONE = 90.0   # pt from top: running headers / page numbers (body starts below)
FOOTER_ZONE = 40.0   # pt from bottom
MARGIN = 5.0         # pt added around the crop
SIDE_MARGIN = 0.0    # applied in addition to MARGIN when clamping to the page
MIN_SIDE = 12.0      # a region smaller than this (pt) is not a figure


@dataclass
class Caption:
    fig_id: str   # "4.1"
    page: int     # 0-based
    top: float
    x0: float


def font_base(name: str) -> str:
    return (name or "").split("+")[-1]


def is_skipped(word: dict, skip_fonts: list[str]) -> bool:
    return any(font_base(word.get("fontname", "")).startswith(p) for p in skip_fonts)


def find_captions(words: list[dict], page_index: int, page_width: float) -> list[Caption]:
    """Caption = line-initial "Fig." followed by "N.M:" (a body reference has no colon).

    Words before it in other fonts are tolerated: one page overlays a hidden
    caption of another edition on the real one.
    """
    caps = []
    if not words:
        return caps
    lines: dict[int, list[dict]] = {}
    for w in words:
        lines.setdefault(round(w["top"] / 3), []).append(w)
    for key in sorted(lines):
        line = sorted(lines[key], key=lambda w: w["x0"])
        for i, w in enumerate(line[:-1]):
            if w["text"] != "Fig." or any(
                    font_base(p["fontname"]) == font_base(w["fontname"]) for p in line[:i]):
                continue
            nxt = line[i + 1]["text"]
            if nxt.endswith(":") and CAPTION_NUM_RE.match(nxt):
                caps.append(Caption(nxt.rstrip(":"), page_index, w["top"], w["x0"]))
    return caps


def _bbox(o: dict) -> tuple[float, float, float, float]:
    return (o["x0"], o["top"], o["x1"], o["bottom"])


def _intersects(a, b, pad: float = 1.0) -> bool:
    return not (a[2] < b[0] - pad or b[2] < a[0] - pad or a[3] < b[1] - pad or b[3] < a[1] - pad)


LABEL_REACH = 45.0   # pt: "(a)" line must lie this close above the caption
SUB_SIZE = 8.0       # pt: smaller glyphs are sub/superscripts, not listing lines
MONO_GAP = 30.0      # pt: max gap between listing lines / listing and caption


def mono_block_top(words: list[dict], cap_top: float) -> float | None:
    """Top of a monospace listing (grammar boxes) ending right above the caption."""
    lines: dict[int, list[dict]] = {}
    for w in words:
        if w["bottom"] <= cap_top + 1 and w.get("size", 10) >= SUB_SIZE:
            lines.setdefault(round(w["top"] / 3), []).append(w)
    top, edge = None, cap_top
    for key in sorted(lines, reverse=True):
        ws = lines[key]
        mono = sum(font_base(w["fontname"]).startswith("NimbusMon") for w in ws)
        if mono * 2 < len(ws):
            if len(ws) <= 2:
                continue  # sub/superscript fragments between listing lines
            if top is None:
                continue
            break
        line_top = min(w["top"] for w in ws)
        line_bottom = max(w["bottom"] for w in ws)
        if edge - line_bottom > MONO_GAP:
            break
        top, edge = line_top, line_top
    return top


SUBLABEL_RE = re.compile(r"^\([a-z]\)$")
LABEL_LINE_MAX_WORDS = 20   # a "(a) ..." line longer than this is a list item, not a label
LABEL_GAP = 60.0            # pt: a label line must sit this close below a drawing


def sublabel_line_tops(words: list[dict]) -> dict[int, float]:
    """Line key -> top for lines whose first word is a subfigure label "(a)"."""
    first: dict[int, dict] = {}
    for w in words:
        key = round(w["top"] / 3)
        if key not in first or w["x0"] < first[key]["x0"]:
            first[key] = w
    return {k: w["top"] for k, w in first.items() if SUBLABEL_RE.match(w["text"])}


def label_line_words(words: list[dict], gboxes: list[tuple]) -> list[dict]:
    """Words of short "(a) ..." label lines that sit right below a drawing.

    Multi-row figures ((a)-(f) in a grid) carry body-font labels between the
    rows; without this they would be mistaken for body text and cut the figure.
    """
    lines: dict[int, list[dict]] = {}
    for w in words:
        lines.setdefault(round(w["top"] / 3), []).append(w)
    out = []
    for line in lines.values():
        line = sorted(line, key=lambda w: w["x0"])
        if not SUBLABEL_RE.match(line[0]["text"]) or len(line) > LABEL_LINE_MAX_WORDS:
            continue
        top = min(w["top"] for w in line)
        if any(0 <= top - g[3] <= LABEL_GAP and g[0] < line[-1]["x1"] and g[2] > line[0]["x0"]
               for g in gboxes):
            out.extend(line)
    return out


def detect_region(page, caption: Caption, skip_fonts: list[str], prev_cap_bottom: float | None):
    """Return (x0, top, x1, bottom) of the figure above ``caption``, or None."""
    width, height = float(page.width), float(page.height)
    cap_top = caption.top
    lower = HEADER_ZONE
    if prev_cap_bottom is not None:
        lower = max(lower, prev_cap_bottom)
    upper = min(cap_top, height - FOOTER_ZONE)

    words = page.extract_words(x_tolerance=1.5, extra_attrs=["fontname", "size"])
    graphics = [o for kind in (page.images, page.curves, page.rects, page.lines) for o in kind]
    graphics = [
        o for o in graphics
        if o["bottom"] <= upper + 2 and o["top"] >= lower - 2
        # ignore page-wide hairlines/frames (rules), which are layout not figure
        and not (o["x1"] - o["x0"] >= 0.95 * width and o["bottom"] - o["top"] < 2)
    ]
    gboxes = [_bbox(o) for o in graphics]

    # Subfigure captions "(a) ..." (body font, may wrap) sit between drawing and
    # caption: everything from the first such line down to the caption is figure.
    near = [t for t in sublabel_line_tops(words).values() if 0 < cap_top - t <= LABEL_REACH]
    label_start = min(near) if near else None
    mono_start = mono_block_top(words, cap_top)
    fig_boxes = gboxes + [_bbox(w) for w in words if is_skipped(w, skip_fonts)]
    labels = {id(w) for w in label_line_words(words, fig_boxes)}
    fig_words, body_words = [], []
    for w in words:
        if w["bottom"] > upper + 2 or w["top"] < lower - 2:
            continue
        if (is_skipped(w, skip_fonts) or id(w) in labels
                or (label_start is not None and w["top"] >= label_start - 1)
                or (mono_start is not None and w["top"] >= mono_start - 1)):
            fig_words.append(w)
        else:
            body_words.append(w)

    # Floor = nearest body line above the caption that is not drawn inside a graphic.
    floor = lower
    for w in sorted(body_words, key=lambda w: w["bottom"], reverse=True):
        wb = _bbox(w)
        if any(_intersects(wb, g, 0.0) for g in gboxes):
            continue
        if w["bottom"] > upper - 1:
            continue
        floor = max(floor, w["bottom"])
        break

    boxes = [g for g in gboxes if g[1] >= floor - 2]
    boxes += [_bbox(w) for w in fig_words if w["top"] >= floor - 2]
    # body words inside the figure's vertical extent (labels set in the text font)
    if boxes:
        for w in body_words:
            wb = _bbox(w)
            if w["top"] >= floor - 2 and any(_intersects(wb, b, 0.0) for b in boxes):
                boxes.append(wb)
    if not boxes:
        return None
    x0 = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    if x1 - x0 < MIN_SIDE or bottom - top < MIN_SIDE:
        return None
    return (
        max(0.0, x0 - MARGIN), max(0.0, floor + 1.0, top - MARGIN),
        min(width, x1 + MARGIN), min(cap_top - 1.0, bottom + MARGIN),
    )


def render_crop(page, bbox, out_path: Path, dpi: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.crop(bbox).to_image(resolution=dpi).save(str(out_path))


def extract_figures(pdfs: list[Path], images_dir: Path, skip_fonts: list[str], dpi: int = 200):
    """Return (figures, missing). Each figure: dict(id, pdf, page(1-based), bbox)."""
    import pdfplumber

    figures, missing = [], []
    for pdf_path in pdfs:
        with pdfplumber.open(pdf_path) as pdf:
            for pi, page in enumerate(pdf.pages):
                words = page.extract_words(x_tolerance=1.5, extra_attrs=["fontname", "size"])
                caps = find_captions(words, pi, float(page.width))
                caps.sort(key=lambda c: c.top)
                prev_bottom = None
                for cap in caps:
                    bbox = detect_region(page, cap, skip_fonts, prev_bottom)
                    # next region on this page may not reach above this caption's line
                    prev_bottom = cap.top + 12.0
                    if bbox is None:
                        missing.append({"id": cap.fig_id, "pdf": pdf_path.name, "page": pi + 1})
                        continue
                    name = f"fig-{cap.fig_id.replace('.', '-')}.png"
                    render_crop(page, bbox, images_dir / name, dpi)
                    figures.append({
                        "id": cap.fig_id, "file": name, "pdf": pdf_path.name,
                        "page": pi + 1, "bbox": [round(v, 1) for v in bbox],
                    })
    return figures, missing


def extract_extras(spec_path: Path, pdf_dir: Path, images_dir: Path, dpi: int) -> list[dict]:
    """Crop hand-measured regions (table bodies, display equations) from ``spec_path``.

    JSON list of ``{"id", "pdf", "page" (1-based), "bbox" [x0, top, x1, bottom] in pt}``;
    each is rendered to ``images/<id>.png``. Captions are not part of the crop (they
    are translated in the text).
    """
    import pdfplumber

    if not spec_path.exists():
        return []
    out = []
    for spec in json.loads(spec_path.read_text(encoding="utf-8")):
        with pdfplumber.open(pdf_dir / spec["pdf"]) as pdf:
            page = pdf.pages[spec["page"] - 1]
            render_crop(page, tuple(spec["bbox"]), images_dir / f"{spec['id']}.png", dpi)
        out.append({"id": spec["id"], "file": f"{spec['id']}.png", "pdf": spec["pdf"],
                    "page": spec["page"], "bbox": spec["bbox"]})
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Crop figures out of a book's source PDFs")
    add_book_argument(parser)
    parser.add_argument("--pdf-dir", default=None, help="Directory holding the chapter PDFs")
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args(argv)

    cfg = get_config_from_args(args)
    ext = cfg.extraction or {}
    inputs = ext.get("inputs") or []
    if not inputs:
        print("book.yaml has no extraction.inputs; nothing to crop.")
        return 1
    candidates = [Path(args.pdf_dir)] if args.pdf_dir else [
        p for p in REPO_ROOT.iterdir() if p.is_dir() and (p / inputs[0]).exists()
    ]
    if not candidates:
        print(f"Could not find the PDF directory holding {inputs[0]}; pass --pdf-dir.")
        return 1
    pdf_dir = candidates[0]
    pdfs = [pdf_dir / n for n in inputs if (pdf_dir / n).exists()]
    skip_fonts = ext.get("skip_fonts") or []
    images_dir = cfg.root / "images"

    figures, missing = extract_figures(pdfs, images_dir, skip_fonts, args.dpi)
    figures.sort(key=lambda f: [int(p) if p.isdigit() else p for p in f["id"].split(".")])
    extras = extract_extras(images_dir / "extra_crops.json", pdf_dir, images_dir, args.dpi)
    figures += extras
    (images_dir / "figures.json").write_text(
        json.dumps(figures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Captions found: {len(figures) - len(extras) + len(missing)}")
    print(f"Figures cropped: {len(figures) - len(extras)} (+{len(extras)} table/equation crops) -> {images_dir}")
    if missing:
        print(f"No region detected for {len(missing)} caption(s):")
        for m in missing:
            print(f"  Fig. {m['id']} ({m['pdf']} p.{m['page']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
