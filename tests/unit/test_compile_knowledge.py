"""Unit tests for scripts/compile_knowledge.py (role snapshots, strip, lint, size guard)."""

from __future__ import annotations

import pytest

from scripts import compile_knowledge as ck
from scripts.utils.book_config import BookConfig

CHECKLIST = """# Checklist

## Severity Levels
- sev-rule-marker

## During Translation (per chunk)
### Content
- during-rule-marker

## Manual Review Checks
- manual-review-marker
"""

DNA = """# DNA

## Voice
- keep the voice lively

## Samples Used
- sample-list-marker

<!-- hidden-comment-marker -->

## Open Questions
- open-question-marker

## Promotion candidates (human)
- promo-marker

## Structure
- keep blocks
"""

GUIDE = """# Guide

## Tone
- guide-tone

```
# 1. fenced pseudo heading
- fenced line
```

## Open Questions & Upgrade Path
- guide-open-marker

## Translation Workflow & Per-Chunk Checklist
- workflow-marker

### Layout Convention
- layout-marker

## Last
- last-marker
"""


@pytest.fixture
def env(tmp_path, monkeypatch):
    l1 = tmp_path / "l1"
    l2 = tmp_path / "l2"
    l1.mkdir()
    l2.mkdir()
    (l1 / "base-principles.md").write_text("# Base\n\n## Pitfalls\n- base-marker\n", encoding="utf-8")
    (l1 / "vietnamese-conventions.md").write_text("# Conv\n\n## Dashes\n- conv-marker\n", encoding="utf-8")
    (l1 / "quality-checklist.md").write_text(CHECKLIST, encoding="utf-8")
    (l2 / "testcat.md").write_text("# Card\n\n## Tone\n- card-marker\n", encoding="utf-8")
    monkeypatch.setattr(ck, "LAYER1_DIR", l1)
    monkeypatch.setattr(ck, "LAYER2_DIR", l2)

    root = tmp_path / "book"
    style = root / "style"
    style.mkdir(parents=True)
    (root / "dna.md").write_text(DNA, encoding="utf-8")
    (style / "translation_style_guide.md").write_text(GUIDE, encoding="utf-8")
    (style / "formatting_rules.md").write_text("# Fmt\n\n## Dashes\n- fmt-marker\n", encoding="utf-8")
    (style / "glossary.csv").write_text("term,vi\nglossary-marker,x\n", encoding="utf-8")
    (style / "new_terms.txt").write_text("newterm-marker | y\n", encoding="utf-8")
    (style / "corrections.md").write_text("# c\n- corrections-marker\n", encoding="utf-8")
    cfg = BookConfig(id="tb", root=root, category="testcat")
    monkeypatch.setattr(ck, "get_config_from_args", lambda args: cfg)
    return cfg


def test_strip_sections_and_comments(env):
    out = ck.compile_snapshot(env, "translator")
    assert "sample-list-marker" not in out
    assert "promo-marker" not in out
    assert "hidden-comment-marker" not in out
    assert "keep the voice lively" in out and "keep blocks" in out  # siblings kept


def test_fenced_heading_not_a_heading():
    text = "## A\n```\n# 1. fake\n## Samples Used\n```\n- keep\n## Samples Used\n- drop\n## B\n- b"
    out = ck.strip_sections(text, ["Samples Used"])
    assert "# 1. fake" in out and "- keep" in out and "- b" in out
    assert "- drop" not in out
    # the fenced '## Samples Used' survives, the real one is gone
    assert out.count("Samples Used") == 1


def test_role_split_open_questions_and_workflow(env):
    tr = ck.compile_snapshot(env, "translator")
    ed = ck.compile_snapshot(env, "editor")
    assert "open-question-marker" not in tr and "guide-open-marker" not in tr
    assert "open-question-marker" in ed and "guide-open-marker" in ed
    assert "workflow-marker" in tr and "layout-marker" in tr  # subsection goes with parent
    assert "workflow-marker" not in ed and "layout-marker" not in ed
    assert "last-marker" in ed and "last-marker" in tr
    assert "# 1. fenced pseudo heading" in tr


def test_dynamic_files_excluded(env):
    for role in ck.ROLES:
        out = ck.compile_snapshot(env, role)
        for marker in ("glossary-marker", "newterm-marker", "corrections-marker"):
            assert marker not in out


def test_l1_role_filter(env):
    tr = ck.compile_snapshot(env, "translator")
    ed = ck.compile_snapshot(env, "editor")
    assert "sev-rule-marker" in tr and "during-rule-marker" in tr
    assert "manual-review-marker" not in tr
    assert "manual-review-marker" in ed and "sev-rule-marker" in ed
    assert "base-marker" in tr and "base-marker" in ed
    assert "conv-marker" in tr


def test_l1_missing_section_warns_not_crashes(env, capsys):
    (ck.LAYER1_DIR / "quality-checklist.md").write_text("# C\n\n## Other\n- x\n", encoding="utf-8")
    out = ck.compile_snapshot(env, "translator")
    assert "Severity Levels" not in out
    assert "WARN L1 section 'Severity Levels' not found" in capsys.readouterr().err


def test_deterministic(env):
    assert ck.compile_snapshot(env, "translator") == ck.compile_snapshot(env, "translator")
    assert ck.compile_snapshot(env, "editor") == ck.compile_snapshot(env, "editor")


def test_main_writes_both_roles(env, capsys):
    assert ck.main([]) == 0
    assert (env.style_dir / "_knowledge_snapshot.md").exists()
    assert (env.style_dir / "_editor_snapshot.md").exists()


def test_stdout_requires_role(env):
    with pytest.raises(SystemExit) as e:
        ck.main(["--stdout"])
    assert e.value.code == 2


def _pad_dna(env, nbytes):
    base = (env.root / "dna.md").read_text(encoding="utf-8")
    # unique lines (avoid dup lint), strip-safe
    pad = "\n".join(f"- padding line number {i:06d} " + "x" * 30 for i in range(nbytes // 60))
    (env.root / "dna.md").write_text(base + "\n## Pad\n" + pad + "\n", encoding="utf-8")


def test_size_guard_fail(env, capsys):
    _pad_dna(env, 51 * 1024)
    assert ck.main(["--role", "translator"]) == 3
    assert (env.style_dir / "_knowledge_snapshot.md").exists()  # still written


def test_size_guard_warn_only(env, capsys):
    _pad_dna(env, 46 * 1024)
    assert ck.main(["--role", "translator"]) == 0
    assert "> 45KB" in capsys.readouterr().err


def test_size_guard_silent(env, capsys):
    _pad_dna(env, 40 * 1024)
    assert ck.main(["--role", "translator"]) == 0
    err = capsys.readouterr().err
    assert "KB" not in err and "snapshot" not in err


def test_dup_lint_warn_and_strict(env, capsys):
    dup = "- an identical rule bullet that appears twice\n"
    (ck.LAYER2_DIR / "testcat.md").write_text("# Card\n\n## Tone\n" + dup, encoding="utf-8")
    (env.root / "dna.md").write_text(DNA + "\n## Dup\n" + dup, encoding="utf-8")
    assert ck.main(["--role", "translator"]) == 0
    err = capsys.readouterr().err
    assert "WARN dup: L2/testcat.md:Tone == L3/dna.md:Dup" in err
    assert ck.main(["--role", "translator", "--strict"]) == 2


def test_no_dup_no_strict_exit(env):
    assert ck.main(["--strict"]) == 2  # fixture shares '## Dashes'/'## Tone' headings
    (env.style_dir / "formatting_rules.md").write_text("# F\n\n## Fmt only\n- fmt-marker\n", encoding="utf-8")
    (ck.LAYER2_DIR / "testcat.md").write_text("# Card\n\n## Card only\n- card-marker\n", encoding="utf-8")
    (env.style_dir / "translation_style_guide.md").write_text(GUIDE.replace("## Tone", "## Guide tone"), encoding="utf-8")
    assert ck.main(["--strict"]) == 0


@pytest.mark.parametrize("which", ["dna", "guide"])
def test_missing_required_exit_1(env, which):
    (env.dna_path if which == "dna" else env.style_guide_path).unlink()
    with pytest.raises(SystemExit) as e:
        ck.main([])
    assert e.value.code == 1


def test_inline_code_comment_survives():
    text = "- marker `<!-- Page N -->` kept\n\n<!-- note -->\n- after <!-- inline --> x"
    out = ck.strip_html_comments(text)
    assert "`<!-- Page N -->`" in out
    assert "note" not in out and "inline" not in out
    assert "- after  x" in out


def test_stdout_size_guard(env, capsys):
    _pad_dna(env, 51 * 1024)
    assert ck.main(["--role", "translator", "--stdout"]) == 3
