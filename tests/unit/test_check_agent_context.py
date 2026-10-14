#!/usr/bin/env python3
"""Tests for scripts/check_agent_context.py — subagent discovery and role parsing.

The subagent paths (`--subagents`) resolve session→subagent transcripts off disk
instead of relying on the Agent tool result, so these cover the two pieces that
can silently go wrong: figuring out *which* session, and reading role/type out of
the sibling `.meta.json`.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import check_agent_context as cac  # noqa: E402


# --- _resolve_current_session -------------------------------------------------


def test_resolve_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_ID", "from-env")
    assert cac._resolve_current_session("explicit-id") == "explicit-id"


def test_resolve_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_ID", "from-env")
    assert cac._resolve_current_session("") == "from-env"


def test_resolve_env_is_stripped(monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_ID", "  padded  ")
    assert cac._resolve_current_session("") == "padded"


def test_resolve_falls_back_to_newest_subagents_dir(tmp_path, monkeypatch):
    """No explicit id, no env var → newest <session>/subagents/ owner wins."""
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(cac, "_project_session_dir", lambda: project)

    older = project / "older-session" / "subagents"
    older.mkdir(parents=True)
    newer = project / "newer-session" / "subagents"
    newer.mkdir(parents=True)
    # Force the newest by mtime — creation order is not guaranteed to differ.
    import os
    import time

    time.sleep(0.01)
    os.utime(newer, None)

    assert cac._resolve_current_session("") == "newer-session"


def test_resolve_ignores_dirs_without_subagents(tmp_path, monkeypatch):
    """A main-session dir with no subagents/ must not be selected."""
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(cac, "_project_session_dir", lambda: project)

    (project / "no-subagents").mkdir()
    (project / "has-subagents" / "subagents").mkdir(parents=True)

    assert cac._resolve_current_session("") == "has-subagents"


def test_resolve_returns_empty_when_nothing_available(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(cac, "_project_session_dir", lambda: project)
    assert cac._resolve_current_session("") == ""


# --- _role_from_subagent ------------------------------------------------------


def _write_meta(jsonl: Path, meta: dict) -> None:
    jsonl.with_suffix(".meta.json").write_text(json.dumps(meta), encoding="utf-8")


def test_role_prefers_custom_agent_type(tmp_path):
    jsonl = tmp_path / "agent-atranslator-027-abc123.jsonl"
    jsonl.touch()
    _write_meta(jsonl, {"name": "translator-027", "customAgentType": "translator"})
    assert cac._role_from_subagent(jsonl) == ("translator-027", "translator")


def test_role_uses_builtin_agent_type_when_distinct(tmp_path):
    jsonl = tmp_path / "agent-aexplore-fix-tests-abc.jsonl"
    jsonl.touch()
    _write_meta(jsonl, {"name": "explore-fix-tests", "agentType": "Explore"})
    assert cac._role_from_subagent(jsonl) == ("explore-fix-tests", "Explore")


def test_role_drops_agent_type_that_only_echoes_the_name(tmp_path):
    """Built-in meta sets agentType == name; that is not a useful type."""
    jsonl = tmp_path / "agent-aexplore-fix-tests-abc.jsonl"
    jsonl.touch()
    _write_meta(jsonl, {"name": "explore-fix-tests", "agentType": "explore-fix-tests"})
    assert cac._role_from_subagent(jsonl) == ("explore-fix-tests", "")


def test_role_unnamed_spawn_is_agent_id_and_uses_agent_type(tmp_path):
    """Unnamed spawn: meta has only agentType/description; role == agentId."""
    jsonl = tmp_path / "agent-a1b2c3d4e5f60718.jsonl"
    jsonl.touch()
    _write_meta(jsonl, {"agentType": "translator", "description": "translator"})
    assert cac._role_from_subagent(jsonl) == ("a1b2c3d4e5f60718", "translator")


def test_role_falls_back_to_agent_id_without_meta(tmp_path):
    jsonl = tmp_path / "agent-a1b2c3d4e5f60718.jsonl"
    jsonl.touch()
    assert cac._role_from_subagent(jsonl) == ("a1b2c3d4e5f60718", "")


def test_role_survives_corrupt_meta(tmp_path):
    jsonl = tmp_path / "agent-a1b2c3d4e5f60718.jsonl"
    jsonl.touch()
    jsonl.with_suffix(".meta.json").write_text("{not json", encoding="utf-8")
    assert cac._role_from_subagent(jsonl) == ("a1b2c3d4e5f60718", "")


def test_role_named_spawn_keeps_full_name(tmp_path):
    """`editor-027-029` comes from meta name, untouched by filename handling."""
    jsonl = tmp_path / "agent-aeditor-027-029-f1b735e6e8d9af80.jsonl"
    jsonl.touch()
    _write_meta(jsonl, {"name": "editor-027-029", "customAgentType": "editor"})
    assert cac._role_from_subagent(jsonl) == ("editor-027-029", "editor")


# --- _parse_session: cache totals, dedupe, idle TTL ----------------------------


def _write_transcript(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _row(msg_id, inp, out, read, create):
    return {
        "message": {
            "id": msg_id,
            "usage": {
                "input_tokens": inp,
                "output_tokens": out,
                "cache_read_input_tokens": read,
                "cache_creation_input_tokens": create,
            },
        }
    }


def test_parse_session_sums_cache_totals(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 10, 100, 5), _row("b", 2, 20, 200, 0)])
    u = cac._parse_session(f)
    assert u.api_calls == 2
    assert u.total_cache_read_tokens == 300
    assert u.total_cache_create_tokens == 5


def test_parse_session_first_call_cache_fields(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 10, 900), _row("b", 1, 1, 950, 0)])
    u = cac._parse_session(f)
    assert u.first_cache_create_tokens == 900
    assert u.first_cache_read_tokens == 10
    d = cac.asdict(u)
    assert d["first_cache_create_tokens"] == 900 and d["first_cache_read_tokens"] == 10


def test_parse_session_first_call_uses_deduped_final_copy(tmp_path):
    """Streamed first message: the last copy's usage is the first call's usage."""
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 0, 0), _row("a", 1, 9, 0, 800), _row("b", 1, 1, 800, 0)])
    u = cac._parse_session(f)
    assert u.first_cache_create_tokens == 800


def test_parse_session_dedupes_streamed_message_id(tmp_path):
    """Same assistant message written twice → counted once, last copy wins."""
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 5, 100, 50), _row("a", 1, 30, 100, 50)])
    u = cac._parse_session(f)
    assert u.api_calls == 1
    assert u.total_output_tokens == 30
    assert u.total_cache_read_tokens == 100
    assert u.total_cache_create_tokens == 50


def test_parse_session_idle_over_ttl_recommends_fresh(tmp_path):
    import os
    import time

    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 1, 1)])
    old = time.time() - 56 * 60
    os.utime(f, (old, old))
    u = cac._parse_session(f)
    assert u.status == "ok"
    assert u.recommendation.startswith("SPAWN_FRESH — cache expired")


def test_idle_overrides_recommendation_but_keeps_full_status(tmp_path):
    import os
    import time

    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 200_000, 0)])
    old = time.time() - 90 * 60
    os.utime(f, (old, old))
    u = cac._parse_session(f)
    assert u.status == "full"
    assert u.recommendation.startswith("SPAWN_FRESH — cache expired")


def test_parse_session_keeps_file_order_for_idless_entries(tmp_path):
    f = tmp_path / "s.jsonl"
    rows = [_row(None, 1, 1, 10, 0), _row("a", 1, 1, 20, 0), _row(None, 1, 1, 30, 0)]
    _write_transcript(f, rows)
    u = cac._parse_session(f)
    assert u.api_calls == 3
    assert u.last_cache_read_tokens == 30


def test_subagent_table_total_row_has_cache_totals(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 100, 7), _row("b", 1, 1, 200, 9)])
    u = cac._parse_session(f)
    total = cac._format_subagent_table([u]).splitlines()[-1]
    assert "300" in total and "16" in total


def test_parse_session_recent_is_reusable(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 1, 1)])
    assert cac._parse_session(f).recommendation.startswith("REUSE_OK")


def test_subagent_table_has_cache_columns(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1, 1, 123, 456)])
    u = cac._parse_session(f)
    u.role, u.agent_type = "translator", "translator"
    out = cac._format_subagent_table([u])
    assert "CacheCreate" in out and "123" in out and "456" in out


def test_cost_usd_uses_sonnet_prices(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 1_000_000, 1_000_000, 1_000_000, 1_000_000)])
    u = cac._parse_session(f)
    # $2 in + $10 out + $0.20 read + $4 write per 1M tokens
    assert u.cost_usd == pytest.approx(16.2)


def test_subagent_table_main_row_counts_in_total(tmp_path):
    f = tmp_path / "s.jsonl"
    _write_transcript(f, [_row("a", 0, 100_000, 0, 0)])
    sub = cac._parse_session(f)
    main = cac._parse_session(f)
    out = cac._format_subagent_table([sub], main).splitlines()
    assert "Cost $" in out[0]
    assert any(line.startswith("main (session)") for line in out)
    assert out[-1].startswith("TOTAL") and out[-1].endswith("2.00")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
