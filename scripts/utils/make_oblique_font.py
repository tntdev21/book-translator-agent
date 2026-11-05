#!/usr/bin/env python3
"""Build a slanted (oblique) font from a Regular TrueType file.

Some italics (e.g. Literata Italic: 2° slant, cursive letterforms) read as a different
typeface rather than slanted text. WeasyPrint never synthesises a slant, so a real
oblique file is generated: the Regular outlines skewed by ``--angle`` degrees.

Usage:
    python scripts/utils/make_oblique_font.py fonts/Literata/Regular.ttf fonts/Literata/Oblique.ttf
"""

import argparse
import math
from pathlib import Path

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def make_oblique(src: Path, dst: Path, angle: float = 10.0) -> None:
    font = TTFont(src)
    glyph_set = font.getGlyphSet()
    skew = math.tan(math.radians(angle))
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(TransformPen(pen, (1, 0, skew, 1, 0, 0)))  # composites decomposed
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)
        glyf[name] = glyph
        advance, _ = font["hmtx"][name]
        font["hmtx"][name] = (advance, getattr(glyph, "xMin", 0))  # lsb must equal the new xMin
    for table in ("hdmx", "LTSH", "VDMX"):  # device metrics no longer match the outlines
        if table in font:
            del font[table]
    font["post"].italicAngle = -angle
    font["hhea"].caretSlopeRise, font["hhea"].caretSlopeRun = 1000, round(1000 * skew)
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection | 0x201) & ~0x40  # ITALIC|OBLIQUE, not REGULAR
    font["head"].macStyle |= 0x2
    family = font["name"].getDebugName(1) or src.parent.name
    for rec in font["name"].names:
        if rec.nameID in (2, 17):
            rec.string = "Oblique"
        elif rec.nameID in (4, 6):
            rec.string = f"{family} Oblique" if rec.nameID == 4 else f"{family.replace(' ', '')}-Oblique"
    font.save(dst)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--angle", type=float, default=10.0)
    args = ap.parse_args()
    make_oblique(args.src, args.dst, args.angle)
    print(f"✓ {args.dst} ({args.angle}°)")


if __name__ == "__main__":
    main()
