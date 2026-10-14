"""Font resolution shared by the PDF, EPUB and HTML exporters.

Fonts live one folder per family, with generic variant file names, so switching
font is just a name change:

    fonts/<Family>/Regular.ttf
    fonts/<Family>/Bold.ttf
    fonts/<Family>/Italic.ttf
    fonts/<Family>/BoldItalic.ttf

``Regular`` is required; a missing Bold/Italic variant is skipped and the
renderer synthesizes it. ``.otf`` is accepted in place of ``.ttf``.
The family is chosen by ``font:`` in ``book.yaml`` (default ``Literata``) and can
be overridden with ``export.py --font``.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Union

from .book_config import REPO_ROOT

FONTS_DIR = REPO_ROOT / "fonts"
DEFAULT_FONT = "Literata"
FALLBACK_STACK = "Georgia, serif"

# (variant file stem, font-weight, font-style)
VARIANTS = (
    ("Regular", "normal", "normal"),
    ("Bold", "bold", "normal"),
    ("Italic", "normal", "italic"),
    ("BoldItalic", "bold", "italic"),
)
EXTENSIONS = (".ttf", ".otf")
MEDIA_TYPES = {".ttf": "font/ttf", ".otf": "font/otf"}


@dataclass(frozen=True)
class FontFile:
    variant: str
    weight: str
    style: str
    path: Path

    @property
    def media_type(self) -> str:
        return MEDIA_TYPES[self.path.suffix.lower()]


@dataclass(frozen=True)
class FontFamily:
    name: str
    files: list = field(default_factory=list)

    @property
    def css_stack(self) -> str:
        """``font-family`` value: the family first, then the serif fallback."""
        return f"'{self.name}', {FALLBACK_STACK}"

    def font_face_css(self, url_for: Callable[[FontFile], str]) -> str:
        """One ``@font-face`` block per variant; ``url_for`` maps a file to its ``src`` URL."""
        return "\n".join(
            f"""@font-face {{
    font-family: '{self.name}';
    src: url('{url_for(f)}');
    font-weight: {f.weight};
    font-style: {f.style};
}}"""
            for f in self.files
        )


class FontNotFoundError(FileNotFoundError):
    pass


def available_fonts(fonts_dir: Union[str, Path, None] = None) -> list:
    root = Path(fonts_dir) if fonts_dir else FONTS_DIR
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and _find(p, "Regular"))


def _find(folder: Path, stem: str) -> Optional[Path]:
    for ext in EXTENSIONS:
        path = folder / f"{stem}{ext}"
        if path.is_file():
            return path
    return None


def resolve_font(name: Optional[str] = None, fonts_dir: Union[str, Path, None] = None) -> FontFamily:
    """Resolve ``fonts/<name>/`` into a :class:`FontFamily`.

    Raises :class:`FontNotFoundError` when the folder or its ``Regular`` file is
    missing, listing the families that are available.
    """
    name = name or DEFAULT_FONT
    root = Path(fonts_dir) if fonts_dir else FONTS_DIR
    folder = root / name

    files = []
    for variant, weight, style in VARIANTS:
        path = _find(folder, variant)
        if path:
            files.append(FontFile(variant, weight, style, path.resolve()))

    if not files or files[0].variant != "Regular":
        found = ", ".join(available_fonts(root)) or "none"
        raise FontNotFoundError(
            f"Font '{name}' not found: expected {folder}/Regular.ttf "
            f"(available: {found})"
        )
    return FontFamily(name, files)


# Inline small caps (`<span class="sc">LET AGREED</span>`) come from the source
# PDF's small-caps runs, already written in capitals. `all-small-caps` maps
# capitals to small-cap glyphs (OpenType `c2sc`), which Literata ships and
# Bookerly lacks, so `.sc` is always set in Literata whatever the body font.
SMALL_CAPS_FONT = "Literata"
SMALL_CAPS_VARIANTS = ("Regular", "Italic")  # small caps are never bold here


def small_caps(body: FontFamily, fonts_dir: Union[str, Path, None] = None):
    """Return ``(extra_family, css)`` for ``.sc`` spans.

    ``extra_family`` holds the Literata files the exporter must embed beside
    the body font, or ``None`` when the body already is Literata or Literata is
    not installed (the renderer then synthesizes small caps from the body font).
    """
    extra = None
    stack = body.css_stack
    if body.name != SMALL_CAPS_FONT:
        try:
            literata = resolve_font(SMALL_CAPS_FONT, fonts_dir)
        except FontNotFoundError:
            literata = None
        if literata:
            extra = FontFamily(literata.name, [f for f in literata.files if f.variant in SMALL_CAPS_VARIANTS])
            stack = f"'{SMALL_CAPS_FONT}', {body.css_stack}"
    css = f".sc {{ font-family: {stack}; font-variant-caps: all-small-caps; letter-spacing: 0.04em; }}"
    return extra, css
