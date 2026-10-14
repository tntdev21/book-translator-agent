#!/usr/bin/env python3
"""Retired legacy ASCII dash-spacing utility.

Use ``python scripts/fix.py`` for supported formatting normalization. This module
is retained solely so historical invocations fail safely: running it exits 1
without touching any file. ``fix_dash_spacing()`` stays importable for tests.
"""

import re
import sys
from pathlib import Path

_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")


def fix_dash_spacing(text):
    """Apply legacy dash spacing rules without changing HTML comments.

    Deprecated: this utility's broad ASCII-hyphen policy is not suitable for
    general translation formatting. It is retained only for compatibility.
    """
    comments = []

    def protect_comment(match):
        comments.append(match.group(0))
        return f"\0PAGE_COMMENT_{len(comments) - 1}\0"

    protected = _HTML_COMMENT_RE.sub(protect_comment, text)
    protected = re.sub(r"(\S)-(\s)", r"\1 - \2", protected)
    protected = re.sub(r"(\s)-(\S)", r"\1 - \2", protected)
    protected = re.sub(r"(\S)-(\S)", r"\1 - \2", protected)

    for index, comment in enumerate(comments):
        protected = protected.replace(f"\0PAGE_COMMENT_{index}\0", comment)
    return protected


def process_file(file_path):
    """Process a single markdown file."""
    content = Path(file_path).read_text(encoding="utf-8")
    fixed = fix_dash_spacing(content)
    if fixed == content:
        return False

    Path(file_path).write_text(fixed, encoding="utf-8")
    return True


def main():
    """Refuse to run: the legacy rules corrupt HTML attrs (class="front-title").

    Kept so historical invocations fail safely instead of rewriting chunks.
    """
    print(
        "fix_dash_spacing.py is retired and no longer modifies files "
        "(it turned class=\"front-title\" into class=\"front - title\").\n"
        "Use: python scripts/fix.py",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
