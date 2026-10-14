#!/usr/bin/env python3
"""Tests for .claude/hooks/translated-guard.cjs (PreToolUse role guard, P9 V3).

Runs the hook with crafted stdin exactly as Claude Code does and checks the
documented PreToolUse output: deny = exit 0 + hookSpecificOutput JSON.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".claude" / "hooks" / "translated-guard.cjs"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")

T = "books/x/translated/chunk_001.md"
S = "books/x/chunks/chunk_001.md"
V = ".claude/skills/translating/scripts"
CHAINED = (
    f"S={S}; T={T}; V={V}; ./venv/bin/python scripts/fix.py $T --source $S "
    "--preserve-page-marker-boundaries --no-backup; ./venv/bin/python $V/compare-structure.py "
    "--source $S --translated $T; ./venv/bin/python $V/validate-translation.py --source $S "
    "--translated $T --glossary books/x/style/glossary.csv"
)


def run(tmp_path, tool, tool_input, agent_type=None):
    payload = {
        "session_id": "s", "transcript_path": "/dev/null", "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse", "tool_name": tool,
        "tool_input": tool_input, "tool_use_id": "toolu_1",
    }
    if agent_type:
        payload["agent_id"] = "a1"
        payload["agent_type"] = agent_type
    env = {"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run([NODE, str(HOOK)], input=json.dumps(payload), text=True,
                          capture_output=True, env=env, timeout=10)
    assert proc.returncode == 0, proc.stderr
    if not proc.stdout.strip():
        return None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    return out


def denied(out):
    return out is not None and out["permissionDecision"] == "deny"


def bash(cmd):
    return {"command": cmd}


# --- main (no agent_type) -------------------------------------------------

@pytest.mark.parametrize("cmd", [
    "rm books/x/translated/*.bak",
    "rm -f books/x/translated/chunk_001.md.bak",
    "mv books/x/translated/chunk_001.md /tmp/a.md",
    "cp /tmp/a.md books/x/translated/chunk_001.md",
    "sed -i '' 's/a/b/' books/x/translated/chunk_001.md",
    "echo hi >> books/x/chunks/chunk_001.md",
    "cat <<'EOF' > books/x/translated/chunk_001.md\nx\nEOF",
    "printf x | tee books/x/source/full_text.md",
    f"T={T}; rm $T",
])
def test_main_bash_writes_denied(tmp_path, cmd):
    out = run(tmp_path, "Bash", bash(cmd))
    assert denied(out)
    assert "SendMessage RETRY" in out["permissionDecisionReason"]
    log = (tmp_path / "logs" / "hook-denials.txt").read_text()
    assert "\tmain\tBash\t" in log


@pytest.mark.parametrize("cmd", [
    f"test -s {T} && echo ok",
    f"wc -l < {T}",
    f"cat {T}",
    f"./venv/bin/python {V}/compare-structure.py --source {S} --translated {T} >/dev/null; echo $?",
    f"./venv/bin/python scripts/manifest_status.py --book x translated chunk_001",
    "BOOK_ID=x ./venv/bin/python scripts/extract_term_map.py",
    "cp books/x/translated/chunk_001.md /tmp/copy.md",
    "ls books/x/translated/ 2>&1 | head",
])
def test_main_bash_reads_allowed(tmp_path, cmd):
    assert run(tmp_path, "Bash", bash(cmd)) is None
    assert not (tmp_path / "logs" / "hook-denials.txt").exists()


@pytest.mark.parametrize("tool,path", [
    ("Edit", f"/repo/{T}"), ("Write", T), ("Write", S), ("Edit", "/repo/books/x/source/full_text.md"),
])
def test_main_edit_write_denied(tmp_path, tool, path):
    assert denied(run(tmp_path, tool, {"file_path": path}))


def test_main_multiedit_nested_paths_denied(tmp_path):
    assert denied(run(tmp_path, "MultiEdit", {"edits": [{"file_path": T}]}))


@pytest.mark.parametrize("path", [
    "books/x/chunks/manifest.json", "logs/book-translating.agents.tsv", "books/x/style/new_terms.txt",
])
def test_main_state_files_allowed(tmp_path, path):
    assert run(tmp_path, "Write", {"file_path": path}) is None


# --- translator -----------------------------------------------------------

@pytest.mark.parametrize("cmd", [
    f"./venv/bin/python scripts/fix.py --no-backup {T}",
    CHAINED,
    f"cat {T}",
    f"{CHAINED.split('; ./venv/bin/python scripts/fix.py')[0]}; ./venv/bin/python $V/compare-structure.py --source $S --translated $T",
])
def test_translator_validators_allowed(tmp_path, cmd):
    assert run(tmp_path, "Bash", bash(cmd), "translator") is None


@pytest.mark.parametrize("cmd", [
    f"sed -i '' 's/a/b/' {T}",
    f"perl -pi -e 's/a/b/' {T}",
    f"awk '{{print}}' {S} > {T}",
    f"python3 -c \"open('{T}','w').write('x')\"",
    f"./venv/bin/python - <<'EOF'\nopen('{T}','w').write('x')\nEOF",
    f"cat > {T} <<'EOF'\nx\nEOF",
    f"rm {T}.bak",
])
def test_translator_bash_writes_denied(tmp_path, cmd):
    out = run(tmp_path, "Bash", bash(cmd), "translator")
    assert denied(out)
    assert "Edit tool" in out["permissionDecisionReason"]


@pytest.mark.parametrize("tool", ["Edit", "Write"])
def test_translator_edit_write_allowed(tmp_path, tool):
    assert run(tmp_path, tool, {"file_path": T}, "translator") is None


# --- editor ---------------------------------------------------------------

def test_editor_write_translated_denied(tmp_path):
    assert denied(run(tmp_path, "Write", {"file_path": T}, "editor"))


@pytest.mark.parametrize("tool,path", [
    ("Edit", T),
    ("Write", "books/x/review/batch_001-005.r0.json"),
    ("Edit", "books/x/style/corrections.md"),
])
def test_editor_allowed(tmp_path, tool, path):
    assert run(tmp_path, tool, {"file_path": path}, "editor") is None


def test_editor_bash_write_denied_validator_allowed(tmp_path):
    assert denied(run(tmp_path, "Bash", bash(f"sed -i '' 's/a/b/' {T}"), "editor"))
    cmd = f"./venv/bin/python {V}/compare-structure.py --source {S} --translated {T}"
    assert run(tmp_path, "Bash", bash(cmd), "editor") is None


# --- other roles / robustness ---------------------------------------------

def test_other_agent_type_noop(tmp_path):
    assert run(tmp_path, "Bash", bash(f"rm {T}"), "general-purpose") is None


def test_unrelated_tool_noop(tmp_path):
    assert run(tmp_path, "Read", {"file_path": T}) is None


def test_malformed_stdin_fails_open(tmp_path):
    proc = subprocess.run([NODE, str(HOOK)], input="not json", text=True,
                          capture_output=True, timeout=10)
    assert proc.returncode == 0 and proc.stdout == ""


def test_main_inline_python_mentioning_paths_allowed(tmp_path):
    """Main's own heredocs (e.g. docs edits quoting paths) are not text writes."""
    cmd = f"./venv/bin/python - <<'X'\nprint('see {T} and {S}')\nX"
    assert run(tmp_path, "Bash", bash(cmd)) is None


def test_main_heredoc_body_is_data(tmp_path):
    """Command-looking lines inside a heredoc body are not executed."""
    cmd = f"cat > /tmp/notes.txt <<'X'\nrm {T}\ncd books/x/translated && rm *.bak\nX\necho done"
    assert run(tmp_path, "Bash", bash(cmd)) is None


# --- review follow-ups (P9 fix) ---------------------------------------------

@pytest.mark.parametrize("cmd", [
    "echo x 1> books/x/translated/chunk_001.md",
    "echo x &> books/x/translated/chunk_001.md",
    "cd books/x/translated && rm *.bak",
    "find books/x/translated -name '*.bak' -delete",
    "dd if=/dev/zero of=books/x/translated/chunk_001.md count=1",
    "git checkout -- books/x/translated/chunk_001.md",
])
def test_main_bypasses_denied(tmp_path, cmd):
    assert denied(run(tmp_path, "Bash", bash(cmd)))


@pytest.mark.parametrize("cmd", [
    "cd books/x/translated && ls",
    "cd books/x/translated && wc -l chunk_001.md 2>&1",
    "git diff books/x/translated/chunk_001.md",
    "find books/x/translated -name '*.md'",
])
def test_main_read_variants_allowed(tmp_path, cmd):
    assert run(tmp_path, "Bash", bash(cmd)) is None


@pytest.mark.parametrize("role", ["translator", "editor"])
def test_agent_unlisted_python_script_denied(tmp_path, role):
    cmd = f"./venv/bin/python scripts/fix10.py {T}"
    assert denied(run(tmp_path, "Bash", bash(cmd), role))


def test_agent_validate_translation_allowed(tmp_path):
    cmd = f"./venv/bin/python {V}/validate-translation.py --source {S} --translated {T} --glossary g.csv"
    assert run(tmp_path, "Bash", bash(cmd), "translator") is None


def test_main_accept_gate_allowed(tmp_path):
    cmd = (f"./venv/bin/python {V}/compare-structure.py --source {S} --translated {T} "
           "--ignore-boundary >/dev/null; echo $?")
    assert run(tmp_path, "Bash", bash(cmd)) is None
