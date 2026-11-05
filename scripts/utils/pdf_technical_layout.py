#!/usr/bin/env python3
"""Opt-in Markdown layout for LaTeX/Springer-style technical textbooks.

Enabled with `extraction: {layout: technical}` in book.yaml (see
`extract_pdf.py`). It turns the baseline-grouped lines of `extract_pdf` into:

- `# N. Title` chapter headings (`Chapter N` + title lines, `Appendix A`, or a
  bare title such as `Preface`); `##`/`###` section headings from bold
  Medium-weight faces larger than body text, level from the numbering
  (`1.1` -> `##`, `1.6.1` -> `###`); bold-italic headings without numbering
  (interview questions) become bold paragraphs;
- running headers/footers and figure panel labels (`(a) (b)`) dropped;
- `•` / `N.` items as `- item` / `N. item` lists (also the numbered
  References), hanging-indent lines joined into their item;
- monospace lines as fenced code blocks (indentation from x position);
  inline monospace as `code`, bold run-ins as `**Abstract**`;
- `Fig.`/`Table`/`Algorithm N.M:` captions kept as their own paragraphs;
- page-bottom footnotes (tiny leading number) as `<aside class="footnote">`;
- hyphenated line breaks removed (`pro-` + `cedural` -> `procedural`).

Dehyphenation heuristic: join only when the next line starts lowercase. Keep
the hyphen when the word before it already has one (`state-of-` `the-art`),
the next line starts upper-case/digit, or the compound (`search-based`) occurs
elsewhere in the same PDF written unbroken. A paragraph that continues across
a page break is merged the same way.

Not handled: display equations stay as plain centred lines; tables become
numbered/plain lines; text inside figures is dropped via `skip_fonts`; a code
block split by a page break becomes two adjacent fences.
"""

from collections import Counter
import re

_BULLET_RE = re.compile(r"^[•·▪‣]\s*")
_ORDERED_RE = re.compile(r"^(\d{1,3})\.\s+(?=[A-Z(“\"*<`\[])")
_CAPTION_RE = re.compile(r"^(Fig\.|Table|Algorithm)\s+[0-9A-Z]+\.\d+[:.]")
_LABEL_RE = re.compile(r"^(Chapter|Appendix|Part)\s+([A-Z]|\d+)$")
_NUMBERING_RE = re.compile(r"^((?:[A-Z]|\d+)(?:\.\d+)+)\s")
_PANEL_RE = re.compile(r"^(\(\w\)\s*)+$")
_NOTE_RE = re.compile(r"^(\d{1,2})\s+(?=\S)")
_SENTENCE_END_RE = re.compile(r"[.?!:)”\"’*]\s*$")
_TRAILING_NOTES_RE = re.compile(r"(?:\n\n<aside class=\"footnote\">[^\n]*</aside>)+\Z")
_COMPOUND_RE = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)+")
_FRAGMENT_RE = re.compile(r"(\S*[A-Za-z])-$")

_HEADER_ZONE = .115  # fraction of page height holding running headers
_FOOTER_ZONE = .83   # fraction of page height below which page numbers sit
_PARA_GAP = 1.3      # baseline gap (in body pitches) that ends a paragraph/list item
_CHAPTER_RATIO = 1.35
_HEADING_RATIO = 1.15


def _bold(font):
    return "medi" in font or "bold" in font


def hyphen_move(first, second, compounds):
    """Return `(head, tail, sep)` so that `head + sep + tail` joins two lines.

    Dehyphenation moves the broken word's first half into `tail`, so a page
    marker can be inserted between `head` and `tail` without splitting a word.
    """
    match = _FRAGMENT_RE.search(first)
    if not match or first.endswith("--") or not second[:1].isalnum():
        return first, second, " "
    fragment = match.group(1)
    head = first[:match.start()]
    if "-" in fragment or not second[0].islower():
        return head, fragment + "-" + second, ""  # real hyphen: keep it
    word = re.sub(r"^\W+", "", fragment) + "-" + re.match(r"[a-z]+", second).group(0)
    if word.lower() in compounds:
        return head, fragment + "-" + second, ""
    return head, fragment + second, ""


def join_lines(texts, compounds):
    """Join wrapped lines, removing line-break hyphens and italic splits."""
    out = texts[0]
    for text in texts[1:]:
        head, tail, sep = hyphen_move(out, text, compounds)
        out = head + sep + tail
    return re.sub(r"(?<=\S)\* \*(?=\S)", " ", out)


def find_compounds(lines):
    """Hyphenated words that occur unbroken somewhere in the document."""
    return {token.lower() for line in lines for token in _COMPOUND_RE.findall(line["text"])}


def _code_row(line, left):
    char_width = line["size"] * .6
    row = ""
    for word in sorted(line.get("words") or [], key=lambda item: item["x0"]):
        column = round((word["x0"] - left) / char_width)
        row = row.ljust(column) + word["text"] if column > len(row) else (row + " " + word["text"] if row else word["text"])
    return row or line["text"]


class Context:
    """Per-document state shared by every page."""

    def __init__(self, lines):
        regular = [line for line in lines if "regu" in line["font"] and "ital" not in line["font"]
                   and "mon" not in line["font"]]
        pool = regular or lines
        weights = Counter(line["size"] for line in pool for _ in line["text"])
        self.body = weights.most_common(1)[0][0] if weights else 10.0
        starts = Counter(round(line["x0"]) for line in pool if abs(line["size"] - self.body) < .2)
        self.margin = starts.most_common(1)[0][0] if starts else 0
        self.compounds = find_compounds(lines)
        self.refs = False
        self.last_kind = ""
        self.last_text = ""


def _is_noise(line, height, body):
    small = line["size"] < body * .9
    if small and (line["bottom"] < height * _HEADER_ZONE or line["top"] > height * _FOOTER_ZONE):
        return True
    return bool(_PANEL_RE.match(line["text"]))


def _render_heading(parts, chapter, italic, ctx):
    text = " ".join(parts)
    if chapter:
        ctx.refs = False
        label = _LABEL_RE.match(parts[0])
        if label and len(parts) > 1:
            return f"# {label.group(2)}. {' '.join(parts[1:])}"
        return f"# {text}"
    numbered = _NUMBERING_RE.match(text + " ")
    if italic and not numbered:
        return f"**{text}**"
    ctx.refs = text.strip().lower() == "references"
    level = numbered.group(1).count(".") + 1 if numbered else 2
    return f"{'#' * min(level, 6)} {text}"


def page_blocks(lines, height, ctx):
    """Return `(blocks, continues_previous_page)` for one page of lines."""
    body, margin = ctx.body, ctx.margin
    pitch = body * 1.2
    blocks, notes = [], []
    state = {"cur": None, "continues": False}
    prev = None
    last_end = False  # previous text line ended a sentence

    def flush():
        cur = state["cur"]
        state["cur"] = None
        if not cur:
            return
        kind, parts = cur["kind"], cur.get("parts")
        if kind == "note":
            text = join_lines(parts, ctx.compounds)
            text = _NOTE_RE.sub(lambda m: f"{m.group(1)}. ", text, count=1)
            notes.append(f'<aside class="footnote">{text}</aside>')
            return
        if kind == "head":
            text = _render_heading(parts, cur["chapter"], cur["italic"], ctx)
        elif kind == "list":
            items = [("- " if bullet else "") + join_lines(p, ctx.compounds)
                     for p, bullet in zip(parts, cur["bullets"]) if p]
            text = "\n".join(items)
        elif kind == "code":
            left = min(row["x0"] for row in cur["rows"] if row)
            text = "```\n" + "\n".join(_code_row(row, left) if row else ""
                                       for row in cur["rows"]) + "\n```"
        else:
            text = join_lines(parts, ctx.compounds)
        blocks.append(text)
        ctx.last_kind, ctx.last_text = kind, text

    kept = [line for line in lines if line["text"] and not _is_noise(line, height, body)]
    for line in kept:
        text, font, size = line["text"], line["font"], line["size"]
        gap = line["base"] - prev["base"] if prev else 999
        prev = line
        cur = state["cur"]
        mono = "mon" in font
        if _bold(font) and not mono and size >= body * _HEADING_RATIO:
            chapter = size >= body * _CHAPTER_RATIO
            joins = cur and cur["kind"] == "head" and cur["chapter"] == chapter and (
                chapter or (cur["size"] == round(size, 1) and gap <= pitch * _PARA_GAP))
            if not joins:
                flush()
                state["cur"] = {"kind": "head", "parts": [], "chapter": chapter,
                                "italic": "ital" in font, "size": round(size, 1)}
            state["cur"]["parts"].append(text)
            continue
        if mono and not ctx.refs:
            if cur and cur["kind"] == "code" and gap <= size * 2.6:
                if gap > size * 1.6:
                    cur["rows"].append("")
            else:
                flush()
                state["cur"] = cur = {"kind": "code", "rows": []}
            cur["rows"].append(line)
            continue
        if not ctx.refs and size < body * .9:
            if _NOTE_RE.match(text) and line["first_size"] < size * .85:
                flush()
                state["cur"] = {"kind": "note", "parts": [text]}
                continue
            if cur and cur["kind"] == "note" and gap <= size * 1.75:
                cur["parts"].append(text)
                continue
        bullet = _BULLET_RE.match(text)
        ordered = None if bullet else _ORDERED_RE.match(text)
        if ordered and (line["x0"] > margin + 8 or not (
                (cur and cur["kind"] == "list") or ctx.refs or gap > pitch * _PARA_GAP or last_end)):
            ordered = None
        if bullet or ordered:
            if not (cur and cur["kind"] == "list"):
                flush()
                state["cur"] = cur = {"kind": "list", "parts": []}
            cur["parts"].append([text[bullet.end():] if bullet else text])
            cur.setdefault("bullets", []).append(bool(bullet))
            last_end = False
            continue
        if cur and cur["kind"] == "list":
            empty_item = not any(cur["parts"][-1])
            if gap <= pitch * _PARA_GAP and (line["x0"] > margin + 3 or empty_item):
                cur["parts"][-1].append(text)
                continue
        if _CAPTION_RE.match(text):
            flush()
            state["cur"] = {"kind": "caption", "parts": [text]}
            continue
        if cur and cur["kind"] == "caption" and gap <= pitch * _PARA_GAP and line["x0"] <= margin + 3:
            cur["parts"].append(text)
            continue
        lead_bold = _bold(line["first_font"]) and "ital" not in line["first_font"] \
            and "mon" not in line["first_font"] and abs(line["first_size"] - body) < 1
        new_para = (not cur or cur["kind"] != "para" or line["x0"] > margin + 6
                    or gap > pitch * _PARA_GAP or lead_bold)
        if new_para:
            if not blocks and not cur and not notes and line["x0"] <= margin + 3 and not lead_bold:
                state["continues"] = True
            flush()
            state["cur"] = {"kind": "para", "parts": []}
        state["cur"]["parts"].append(text)
        last_end = bool(_SENTENCE_END_RE.search(text))
    flush()
    blocks.extend(notes)
    continues = state["continues"] and ctx.last_kind == "para" and bool(blocks) and (
        not _SENTENCE_END_RE.search(ctx.last_text) or blocks[0][:1].islower())
    return blocks, continues


def render_pages(page_lines, heights, first_page):
    """Render every page's lines to Markdown with `<!-- Page N -->` markers."""
    ctx = Context([line for lines in page_lines for line in lines])
    content = ""
    for number, (lines, height) in enumerate(zip(page_lines, heights), start=first_page):
        blocks, continues = page_blocks(lines, height, ctx)
        if continues and content:
            notes = _TRAILING_NOTES_RE.search(content)
            base = content[:notes.start()] if notes else content
            head, tail, sep = hyphen_move(base.rstrip(), blocks[0], ctx.compounds)
            if sep == "" and tail != blocks[0]:
                content = head + (notes.group(0) if notes else "")
                blocks[0] = tail
        separator = "\n" if content and continues else "\n\n"
        content += f"{separator}<!-- Page {number} -->"
        page_text = "\n\n".join(blocks)
        if page_text:
            content += "\n" + (page_text if continues else f"\n{page_text}")
    return content
