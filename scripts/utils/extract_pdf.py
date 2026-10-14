#!/usr/bin/env python3
"""Extract structured Markdown from text-based PDFs."""

from collections import Counter
import hashlib
import os
import re
import sys

import pdfplumber


_CID_REPAIRS_BY_SOURCE = {
    "32f0117b598fa18ab343f099129214e624239301f3c6970ff3ade8c14a659ea2": {
        "999": "fi", "1001": "fl", "1003": "ffi", "1006": "ffl", "1009": "ff",
    },
}
_CID_RE = re.compile(r"\(cid:(\d+)\)")


def _source_fingerprint(input_path):
    digest = hashlib.sha256()
    with open(input_path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repair_text(text, cid_repairs, unknown_cids):
    def repair(match):
        code = match[1]
        if code not in cid_repairs:
            unknown_cids.add(code)
        return cid_repairs.get(code, match[0])

    text = _CID_RE.sub(repair, text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


_MARKER_RE = re.compile(r"^(\d{1,3}|[*†‡]+)$")


def _attach_superscripts(words):
    """Fold superscript note markers into the word they follow.

    A superscript sits slightly higher than its host, so grouping by `top`
    would split it onto its own line and shove it away from its position in
    the sentence. Markers are glued to the preceding larger word as
    `<small>N</small>`, which the converters later turn into clickable links.
    """
    merged = []
    for word in sorted(words, key=lambda item: (item["x0"], item["top"])):
        host = next((
            prev for prev in reversed(merged)
            if _MARKER_RE.match(word["text"])
            and prev["size"] >= word["size"] * 1.25
            and -1 <= word["x0"] - prev["x1"] <= prev["size"] * .3
            and word["top"] < prev["bottom"] and word["bottom"] > prev["top"]
        ), None)
        if host is None:
            merged.append(dict(word))
        else:
            host["text"] += f"<small>{word['text']}</small>"
            host["x1"] = word["x1"]
    return merged


_GLUE_GAP = .1  # font-change gaps below this fraction of size are intra-word
_EDGE_RE = re.compile(r"^([“‘\"'(\[—–-]*)(.*?)((?:[.,;:!?”’\"')\]—–-]|<small>[^<]*</small>)*)$", re.S)


def _is_italic(word):
    """Body italics only: bold-italic is the section-heading face, left as-is."""
    font = word["fontname"].lower()
    return "italic" in font and "bold" not in font


def _glued(prev, word):
    """pdfplumber splits a word wherever the font changes (italic `human` +
    roman `.`); such fragments touch, while a real space is >=.12em here."""
    changed = prev["fontname"] != word["fontname"] or prev["size"] != word["size"]
    return changed and abs(word["x0"] - prev["x1"]) < prev["size"] * _GLUE_GAP


def _wrap_small_caps(line):
    """Collapse each run of `sc` words into one `<span class="sc">` word.

    The span keeps the run's font/size/geometry so `_glued` still decides the
    spacing against its neighbours (`way—<span…>LET AGREED</span>,`).
    """
    out = []
    for word in line:
        if word.get("sc") and out and out[-1].get("sc"):
            prev = out[-1]
            prev["words"].append(word["text"])
            prev["x1"] = word["x1"]
        else:
            out.append(dict(word, words=[word["text"]]) if word.get("sc") else word)
    for word in out:
        if word.get("sc"):
            word["text"] = f'<span class="sc">{" ".join(word.pop("words"))}</span>'
    return out


def _line_text(line):
    """Join a line's words, wrapping runs of body-italic words in `*...*`.

    Opening/closing punctuation and trailing note markers stay outside the
    asterisks (`*human*.`); a run with no letters or digits, or one that
    already contains a literal `*`, is left bare.
    """
    line = _wrap_small_caps(line)
    pieces, run = [], []

    def close_run():
        if not run:
            return
        text = "".join(run)
        prefix, body, suffix = _EDGE_RE.match(text).groups()
        # Literal asterisks in the source (`*sigh*`) already read as emphasis.
        if any(char.isalnum() for char in body) and "*" not in text:
            text = f"{prefix}*{body}*{suffix}"
        pieces.append(text)
        run.clear()

    for index, word in enumerate(line):
        separator = "" if index == 0 or _glued(line[index - 1], word) else " "
        # Markdown emphasis cannot wrap a raw `<span>`, so small caps stay roman.
        if _is_italic(word) and not word.get("sc"):
            if run:
                run.append(separator)
            else:
                pieces.append(separator)
            run.append(word["text"])
            if "<small>" in word["text"]:
                close_run()  # emphasis must not span a note marker
        else:
            close_run()
            pieces.append(separator + word["text"])
    close_run()
    return "".join(pieces)


def _join_lines(texts):
    """Join wrapped lines, reuniting an italic run split by the line break."""
    return re.sub(r"(?<=\S)\* \*(?=\S)", " ", " ".join(texts))


_SMALL_CAPS_RATIO = .9  # a run below 90% of its host line's size is small caps


def _bottom(word):
    return word.get("bottom", word["top"] + word["size"])


def _fold_inline_small_caps(groups):
    """Fold small-caps runs back into the body line they sit in.

    Small caps share the host line's baseline but are set smaller, so their
    `top` differs and grouping by `top` splits them onto a line of their own,
    which then reads as a standalone `<small>` block and tears the sentence
    (`my way—LET AGREED, one says` -> `my way - , one says` + block). A group
    whose glyphs are all smaller than a neighbouring group and whose vertical
    centre falls inside that group's span belongs to it; its words are tagged
    `sc` so `_line_text` wraps them in `<span class="sc">`. Mutates `groups`.
    """
    for top in sorted(groups):
        small = groups.get(top)
        if not small:
            continue
        size = max(word["size"] for word in small)
        bottom = max(_bottom(word) for word in small)
        centre = (min(word["top"] for word in small) + bottom) / 2
        host = next((
            other for other_top, other in groups.items()
            if other_top != top and other
            # Prose hosts only: a bare dash or `13:1` beside a small-caps
            # attribution (`–DAVID FOSTER WALLACE`) stays a display line.
            and any(re.search(r"[^\W\d_]{2}", word["text"]) for word in other)
            and size < min(word["size"] for word in other) * _SMALL_CAPS_RATIO
            and min(word["top"] for word in other) <= centre <= max(_bottom(word) for word in other)
            # Shared baseline: a separate small line just above/below a body
            # line (caption, display text) sits a full line away.
            and abs(bottom - max(_bottom(word) for word in other)) <= max(word["size"] for word in other) * .25
        ), None)
        if host is not None:
            host.extend(dict(word, sc=True) for word in small)
            groups[top] = []
    for top in [top for top, group in groups.items() if not group]:
        del groups[top]


def _line_groups(words, cid_repairs, unknown_cids):
    """Group extracted words into logical, reading-order lines."""
    words = _attach_superscripts(words)
    groups = {}
    for word in words:
        groups.setdefault(round(word["top"], 1), []).append(word)
    _fold_inline_small_caps(groups)
    lines = []
    for top in sorted(groups):
        line = sorted(groups[top], key=lambda word: word["x0"])
        # Small caps are inline decoration: a short turn (`WILLIAMSON: It isn't
        # me`) must still size as body text, not as a `<small>` display line.
        sized = [word for word in line if not word.get("sc")] or line
        weights = Counter((round(word["size"], 1), word["fontname"]) for word in sized for _ in word["text"])
        (size, font), _ = weights.most_common(1)[0]
        lines.append({
            # CIDs are repaired per word first so `(cid:N)` never reads as
            # punctuation at the edge of an italic run.
            "text": _repair_text(_line_text([
                dict(word, text=_repair_text(word["text"], cid_repairs, unknown_cids)) for word in line
            ]), cid_repairs, unknown_cids),
            "x0": line[0]["x0"], "x1": max(word["x1"] for word in line),
            "top": top,
            "bottom": max(word.get("bottom", word["top"] + word["size"]) for word in line),
            "size": size, "font": font.lower(),
        })
    return lines


def _body_size(lines):
    weights = Counter(line["size"] for line in lines for _ in line["text"])
    return weights.most_common(1)[0][0] if weights else 0


def _margin_x0(lines, body_size):
    starts = [round(line["x0"], 1) for line in lines if abs(line["size"] - body_size) < body_size * .02]
    return Counter(starts).most_common(1)[0][0] if starts else 0


def _indent_threshold(lines, body_size, margin_x0):
    offsets = sorted({line["x0"] - margin_x0 for line in lines if line["x0"] - margin_x0 > body_size * .2})
    return offsets[0] / 2 if offsets else float("inf")


def _classify_line(line, body_size, margin_x0, indent_threshold, page_width):
    # Tolerance scales with the line's own size so that a 16.6pt heading's
    # centre is judged against its own glyph width, not the body size. A
    # heading that spans half the page can easily sit 30-50pt off the true
    # geometric centre; 60% of the line's size covers this without letting
    # an indented paragraph line qualify.
    size_delta = body_size * .14
    line_center = (line["x0"] + line["x1"]) / 2
    centered = abs(line_center - page_width / 2) <= max(body_size, line["size"] * .6)

    # Chapter heading: meaningfully larger than body AND bold font. The bold
    # requirement prevents stray large italic display lines (epigraphs,
    # dedications) from being promoted to H1.
    if line["size"] > body_size + size_delta and "bold" in line["font"]:
        return "chapter"
    # Section heading: bold-italic AND centred (same size as body in this
    # book, which is why font style does the heavy lifting).
    if "bold" in line["font"] and "italic" in line["font"] and centered:
        return "section"
    if line["size"] < body_size - size_delta:
        return "small"
    if line["x0"] > margin_x0 + indent_threshold:
        return "paragraph"
    return "continuation"


def _has_multiple_columns(words, page_width, body_size):
    """Reject persistent left/right text clusters before reading order interleaves."""
    rows = {}
    for word in words:
        if abs(word["size"] - body_size) <= body_size * .1:
            rows.setdefault(round(word["top"], 1), []).append(word)
    left_rows = []
    right_rows = []
    split_rows = 0
    center = page_width / 2
    for top, row in rows.items():
        row = sorted(row, key=lambda word: word["x0"])
        if any(
            left["x1"] < center - body_size
            and right["x0"] > center + body_size
            and right["x0"] - left["x1"] > body_size * 2
            for left, right in zip(row, row[1:])
        ):
            split_rows += 1
        x0 = row[0]["x0"]
        x1 = max(word["x1"] for word in row)
        if x1 < center - body_size:
            left_rows.append(top)
        elif x0 > center + body_size:
            right_rows.append(top)
    staggered_pairs = sum(
        any(abs(left - right) <= body_size * .25 for right in right_rows)
        for left in left_rows
    )
    return split_rows >= 3 or staggered_pairs >= 3


def _is_small_line(line, body_size):
    return line["size"] < body_size * .9


def _is_citation_start(line, margin_x0, body_size):
    """Recognize a potential citation marker; never sufficient on its own."""
    return (
        _is_small_line(line, body_size)
        and abs(line["x0"] - margin_x0) <= body_size * .25
        and bool(re.match(r"^\d+[.)]?\s+\S", line["text"]))
    )


def _small_line_clusters(lines, body_size):
    """Group vertically adjacent small lines without merging display text blindly."""
    clusters = []
    index = 0
    while index < len(lines):
        if not _is_small_line(lines[index], body_size):
            index += 1
            continue
        start = index
        previous = lines[index]
        index += 1
        while index < len(lines) and _is_small_line(lines[index], body_size):
            gap = lines[index].get("top", float("inf")) - previous.get("top", float("-inf"))
            if not 0 < gap <= previous["size"] * 2.1:
                break
            previous = lines[index]
            index += 1
        clusters.append((start, index - 1))
    return clusters


def _is_citation_region(lines, cluster_start, cluster_end, body_size, dense_page):
    """A citation region is bottom-anchored, or a page dominated by note text."""
    region_bottom = max(line["bottom"] for line in lines)
    bottom_anchored = lines[cluster_end]["bottom"] >= region_bottom - body_size * 1.5
    return bottom_anchored or dense_page


def _is_dense_note_page(lines, body_size):
    """Measure how much of the page is note text, not body prose."""
    if not lines:
        return False
    small = sum(1 for line in lines if _is_small_line(line, body_size))
    return small / len(lines) >= .5


def _citation_ranges(lines, body_size, margin_x0, dense_page=None):
    """Return citation ranges only from geometry-supported small-text clusters."""
    if dense_page is None:
        dense_page = _is_dense_note_page(lines, body_size)
    ranges = []
    for cluster_start, cluster_end in _small_line_clusters(lines, body_size):
        starts = [
            index for index in range(cluster_start, cluster_end + 1)
            if _is_citation_start(lines[index], margin_x0, body_size)
        ]
        if not starts:
            continue
        if not _is_citation_region(lines, cluster_start, cluster_end, body_size, dense_page):
            continue

        note_ranges = []
        for position, start in enumerate(starts):
            end = starts[position + 1] - 1 if position + 1 < len(starts) else cluster_end
            continuation_indent = None
            valid_end = start
            for index in range(start + 1, end + 1):
                offset = lines[index]["x0"] - margin_x0
                if not lines[start]["size"] * .5 <= offset <= lines[start]["size"] * 1.5:
                    break
                if continuation_indent is not None and abs(offset - continuation_indent) > lines[start]["size"] * .25:
                    break
                continuation_indent = offset
                valid_end = index
            note_ranges.append((start, valid_end))

        # A hanging-indent continuation proves the note on its own. A single-line
        # note needs a genuinely dense marker run, so one numeric glyph or a lone
        # display line never inherits a neighbour's proof.
        if len(starts) >= 3:
            ranges.extend(note_ranges)
        else:
            ranges.extend(item for item in note_ranges if item[1] > item[0])
    return ranges


_TURN_END_RE = re.compile(r"[.?!…:][\"”’*)\]]*$")


def _wraps_speaker_turn(paragraph, turn_x0, line, body_size):
    """A transcript turn (`JUDGE: …`) is hanging-indented by about an em, so
    its wrapped lines read as new paragraphs. Keep them in the turn while its
    last line has not ended a sentence; a normal paragraph indent (< an em
    right of the label) still starts new narrative."""
    return bool(
        paragraph
        and paragraph[0].startswith('<span class="sc">')
        and line["x0"] >= turn_x0 + body_size * .9
        and not _TURN_END_RE.search(paragraph[-1])
    )


def _page_blocks(lines, body_size, margin_x0, indent_threshold, page_width):
    blocks, paragraph, heading = [], [], []
    paragraph_x0 = 0  # x0 of the line that opened `paragraph`
    citation_ranges = _citation_ranges(lines, body_size, margin_x0)
    citation_by_start = {start: end for start, end in citation_ranges}
    citation_lines = {
        line_index
        for start, end in citation_ranges
        for line_index in range(start, end + 1)
    }
    first_role = next((
        _classify_line(line, body_size, margin_x0, indent_threshold, page_width)
        for line in lines if line["text"] and _classify_line(line, body_size, margin_x0, indent_threshold, page_width) != "small"
    ), None)

    def flush_paragraph():
        if paragraph:
            blocks.append(_join_lines(paragraph))
            paragraph.clear()

    def flush_heading():
        if heading:
            level, text = heading[0]
            blocks.append(f"{'#' * level} {' '.join(item[1] for item in heading)}")
            heading.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if index in citation_by_start:
            flush_heading()
            flush_paragraph()
            end = citation_by_start[index]
            blocks.append(
                f"<aside class=\"footnote\">{_join_lines(lines[note_index]['text'] for note_index in range(index, end + 1))}</aside>"
            )
            index = end + 1
            continue
        if index in citation_lines:
            index += 1
            continue

        role = _classify_line(line, body_size, margin_x0, indent_threshold, page_width)
        if role in {"chapter", "section"}:
            flush_paragraph()
            level = 1 if role == "chapter" else 2
            if heading and heading[0][0] != level:
                flush_heading()
            heading.append((level, line["text"]))
        else:
            flush_heading()
            if role == "small":
                flush_paragraph()
                blocks.append(f"<small>{line['text']}</small>")
            else:
                if role == "paragraph" and not _wraps_speaker_turn(paragraph, paragraph_x0, line, body_size):
                    flush_paragraph()
                # Turns wrap at a hanging indent, so a margin-aligned line after
                # one is the narrative resuming, never part of the turn.
                if role == "continuation" and paragraph and paragraph[0].startswith('<span class="sc">'):
                    flush_paragraph()
                # Numbered list items (e.g., "0. Prologue", "12. Epilogue")
                # must start a new line rather than merging with the previous
                # continuation. Without this the TOC's chapter entries — which
                # share the body font/size and so are classified as
                # "continuation" — collapse into a single flattened paragraph.
                if role == "continuation" and re.match(r"^\d+\.\s+\S", line["text"]):
                    flush_paragraph()
                if not paragraph:
                    paragraph_x0 = line["x0"]
                paragraph.append(line["text"])
        index += 1
    flush_heading()
    flush_paragraph()
    return blocks, first_role == "continuation"


def extract_pdf(input_path, output_path, max_pages=None):
    """Extract a PDF to Markdown while preserving detected structure."""
    unknown_cids = set()
    cid_repairs = _CID_REPAIRS_BY_SOURCE.get(_source_fingerprint(input_path), {})
    with pdfplumber.open(input_path) as pdf:
        total = len(pdf.pages) if not max_pages else min(max_pages, len(pdf.pages))
        print(f"Extracting {total} pages from {input_path}...")
        pages = pdf.pages[:total]
        raw_pages = [page.extract_words(extra_attrs=["fontname", "size"]) for page in pages]
        page_lines = [_line_groups(words, cid_repairs, unknown_cids) for words in raw_pages]
        all_lines = [line for lines in page_lines for line in lines]
        body_size = _body_size(all_lines)
        margin_x0 = _margin_x0(all_lines, body_size)
        indent_threshold = _indent_threshold(all_lines, body_size, margin_x0)
        content = ""
        previous_trailing_citation = None
        for index, (page, words, lines) in enumerate(zip(pages, raw_pages, page_lines), start=1):
            if _has_multiple_columns(words, page.width, body_size):
                raise ValueError(f"Page {index} has a multi-column layout; extraction stopped to avoid interleaving columns.")
            blocks, continues_previous_page = _page_blocks(lines, body_size, margin_x0, indent_threshold, page.width)
            citation_ranges = _citation_ranges(lines, body_size, margin_x0)
            trailing_citation = next((item for item in citation_ranges if item[1] == len(lines) - 1), None)
            marker = f"<!-- Page {index} -->"

            if (
                content
                and previous_trailing_citation is not None
                and lines
                and _is_small_line(lines[0], body_size)
                and abs(lines[0]["x0"] - margin_x0 - body_size * .75) <= body_size * .25
                and content.endswith("</aside>")
            ):
                continuation_end = 0
                while (
                    continuation_end < len(lines)
                    and _is_small_line(lines[continuation_end], body_size)
                    and abs(lines[continuation_end]["x0"] - margin_x0 - body_size * .75) <= body_size * .25
                ):
                    continuation_end += 1
                continuation = _join_lines(line["text"] for line in lines[:continuation_end])
                content = content.removesuffix("</aside>") + f" {marker} {continuation}</aside>"
                blocks = blocks[continuation_end:]
            else:
                separator = "\n" if content and continues_previous_page else "\n\n"
                content += f"{separator}{marker}"
            page_text = "\n\n".join(blocks)
            if page_text:
                content += "\n" + (page_text if continues_previous_page else f"\n{page_text}")
            previous_trailing_citation = trailing_citation
            if index % 50 == 0:
                print(f"  Processed {index}/{total}")
    content = content.lstrip("\n") + "\n"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Done. Saved to {output_path}")
    print(f"Total characters: {len(content):,}")
    if unknown_cids:
        print(f"Warning: preserved unrecognized CID glyphs: {', '.join(sorted(unknown_cids, key=int))}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf.py <input.pdf> [output.md] [max_pages]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "source/full_text.md"
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    extract_pdf(input_file, output_file, max_pages)


if __name__ == "__main__":
    main()
