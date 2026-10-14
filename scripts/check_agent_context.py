#!/usr/bin/env python3
"""
Check context usage of Claude Code agent sessions by reading session JSONL logs.

Usage:
    # Check specific session by ID
    python scripts/check_agent_context.py <session-id>

    # Find most recent N subagent sessions (exclude current main session)
    python scripts/check_agent_context.py --recent [N]

    # Check all sessions modified in last N minutes
    python scripts/check_agent_context.py --active [N_MINUTES]

    # Per-subagent usage for one main session (for the batch-end usage report).
    # With no id, auto-resolves $CLAUDE_SESSION_ID, else the newest session
    # with a subagents/ directory.
    python scripts/check_agent_context.py --subagents
    python scripts/check_agent_context.py --subagents <session-id>

    # Get JSON output (for piping/automation)
    python scripts/check_agent_context.py --json <session-id>
    python scripts/check_agent_context.py --json --recent 5

Output fields per session:
    session_id, api_calls, last_context_tokens, max_context_tokens,
    utilization_pct, last_input_tokens, last_output_tokens,
    last_cache_read_tokens, total_cache_read_tokens, total_cache_create_tokens,
    first_cache_read_tokens, first_cache_create_tokens (first API call, after
    dedupe — the cache-warm check: siblings 2..N should show ~0 create),
    status (ok/warning/full; context fill only), recommendation
    (idle > 55 min overrides it with SPAWN_FRESH — cache expired)

Context window limit: 200,000 tokens (Claude Sonnet).
Warning threshold: 80% (160,000 tokens).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# Constants
CONTEXT_WINDOW_LIMIT = 200_000
WARNING_THRESHOLD = 0.80  # 80%
# Subagent prompt cache TTL is 1h; treat >55m idle as expired (safety margin).
CACHE_TTL_SAFE_SECONDS = 55 * 60
RECENT_MINUTES_DEFAULT = 30
RECENT_COUNT_DEFAULT = 5
# Sonnet 5.5 list prices, USD per 1M tokens. Cache writes are priced at the 1h TTL
# rate because every pipeline agent uses 1h caching (5m writes were measured at 0).
PRICE_PER_MTOK = {"input": 2.0, "output": 10.0, "cache_read": 0.20, "cache_create": 4.0}


def _cost_usd(input_tok: int, output_tok: int, cache_read: int, cache_create: int) -> float:
    """Token totals → USD at Sonnet prices."""
    p = PRICE_PER_MTOK
    return (
        input_tok * p["input"] + output_tok * p["output"]
        + cache_read * p["cache_read"] + cache_create * p["cache_create"]
    ) / 1_000_000

# Resolve project path pattern for Claude session directory
# /Users/bob/project → -Users-bob-project
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_SESSION_DIR = Path.home() / ".claude" / "projects"


def _project_session_dir() -> Path:
    """Find the session directory matching the current project."""
    project_path = str(REPO_ROOT).replace("/", "-")
    return PROJECT_SESSION_DIR / project_path


@dataclass
class SessionUsage:
    session_id: str
    api_calls: int
    last_context_tokens: int
    max_context_tokens: int
    utilization_pct: float
    last_input_tokens: int
    last_output_tokens: int
    last_cache_read_tokens: int
    last_cache_create_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cache_create_tokens: int
    first_cache_read_tokens: int
    first_cache_create_tokens: int
    file_size_kb: float
    modified_ago_seconds: float
    status: str
    recommendation: str
    # Subagent-only metadata (empty for main sessions). `role` is the spawn name
    # when one was given (e.g. "editor-027-029"); for unnamed spawns it is the
    # agentId (transcript stem minus "agent-"), resolved with the sibling .meta.json.
    role: str = ""
    parent_session: str = ""
    agent_type: str = ""
    # Sonnet-priced cost of the whole transcript (see PRICE_PER_MTOK).
    cost_usd: float = 0.0


def _parse_session(jsonl_path: Path) -> Optional[SessionUsage]:
    """Parse a session JSONL file and extract usage stats."""
    session_id = jsonl_path.stem
    # Keyed by assistant message id: streaming writes the same message several
    # times into the transcript, so only the last copy (final usage) counts.
    by_id: dict[str, dict] = {}
    entries_seen: list[str] = []

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = obj.get("message")
                if isinstance(msg, dict) and "usage" in msg:
                    u = msg["usage"]
                    input_tok = u.get("input_tokens", 0)
                    cache_read = u.get("cache_read_input_tokens", 0)
                    cache_create = u.get("cache_creation_input_tokens", 0)
                    output_tok = u.get("output_tokens", 0)

                    effective_input = input_tok + cache_read + cache_create
                    context_size = effective_input + output_tok

                    entry = {
                        "input_tokens": input_tok,
                        "cache_read": cache_read,
                        "cache_create": cache_create,
                        "output_tokens": output_tok,
                        "context_size": context_size,
                    }
                    # Entries lacking an id get a unique key so file order holds.
                    msg_id = msg.get("id") or f"_anon:{len(by_id)}:{len(entries_seen)}"
                    entries_seen.append(msg_id)
                    by_id.pop(msg_id, None)  # re-insert → keeps latest order
                    by_id[msg_id] = entry
    except (OSError, PermissionError):
        return None

    entries_with_usage = list(by_id.values())
    if not entries_with_usage:
        return None

    total_input = sum(e["input_tokens"] for e in entries_with_usage)
    total_output = sum(e["output_tokens"] for e in entries_with_usage)
    total_cache_read = sum(e["cache_read"] for e in entries_with_usage)
    total_cache_create = sum(e["cache_create"] for e in entries_with_usage)

    first = entries_with_usage[0]
    last = entries_with_usage[-1]
    max_ctx = max(e["context_size"] for e in entries_with_usage)
    last_ctx = last["context_size"]

    # If last entry has 0 context (session ended with summary/status message),
    # use max context as the effective "current" size — this is conservative.
    effective_ctx = last_ctx if last_ctx > 0 else max_ctx
    utilization = effective_ctx / CONTEXT_WINDOW_LIMIT

    mtime = jsonl_path.stat().st_mtime
    idle_seconds = time.time() - mtime

    # Status & recommendation
    if utilization >= 1.0:
        status = "full"
        recommendation = "SPAWN_FRESH — context exhausted"
    elif utilization >= WARNING_THRESHOLD:
        status = "warning"
        recommendation = "PLAN_REFRESH — approaching limit"
    else:
        status = "ok"
        chunks_remaining = int(
            (CONTEXT_WINDOW_LIMIT - effective_ctx) / 26_000
        )  # ~26K per chunk reuse
        recommendation = f"REUSE_OK — ~{chunks_remaining} more chunks possible"

    # Idle past the cache TTL overrides the recommendation only; `status` keeps
    # describing context fill so full/warning stay visible in reports.
    if idle_seconds > CACHE_TTL_SAFE_SECONDS:
        recommendation = (
            f"SPAWN_FRESH — cache expired (idle {int(idle_seconds // 60)}m > 1h TTL)"
        )

    file_size = jsonl_path.stat().st_size / 1024

    return SessionUsage(
        session_id=session_id,
        api_calls=len(entries_with_usage),
        last_context_tokens=effective_ctx,
        max_context_tokens=max_ctx,
        utilization_pct=round(utilization * 100, 1),
        last_input_tokens=last["input_tokens"],
        last_output_tokens=last["output_tokens"],
        last_cache_read_tokens=last["cache_read"],
        last_cache_create_tokens=last["cache_create"],
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_cache_read_tokens=total_cache_read,
        total_cache_create_tokens=total_cache_create,
        first_cache_read_tokens=first["cache_read"],
        first_cache_create_tokens=first["cache_create"],
        file_size_kb=round(file_size, 1),
        modified_ago_seconds=round(idle_seconds, 0),
        status=status,
        recommendation=recommendation,
        cost_usd=round(
            _cost_usd(total_input, total_output, total_cache_read, total_cache_create), 4
        ),
    )


def _find_session_file(session_id: str) -> Optional[Path]:
    """Locate a session JSONL file by ID prefix match."""
    session_dir = _project_session_dir()
    if not session_dir.exists():
        return None

    # Exact match first
    exact = session_dir / f"{session_id}.jsonl"
    if exact.exists():
        return exact

    # Prefix match
    matches = list(session_dir.glob(f"{session_id}*.jsonl"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous session ID '{session_id}':", file=sys.stderr)
        for m in matches:
            print(f"  {m.stem}", file=sys.stderr)
        return None

    return None


def _find_recent_sessions(
    count: int, exclude_session: Optional[str] = None, minutes: int = 0
) -> list[tuple[Path, float]]:
    """Find recently modified session files."""
    session_dir = _project_session_dir()
    if not session_dir.exists():
        return []

    cutoff = time.time() - (minutes * 60) if minutes > 0 else 0
    sessions = []

    for f in session_dir.glob("*.jsonl"):
        if exclude_session and f.stem.startswith(exclude_session):
            continue
        mtime = f.stat().st_mtime
        if mtime >= cutoff:
            sessions.append((f, mtime))

    sessions.sort(key=lambda x: x[1], reverse=True)
    return sessions[:count]


def _subagents_dir(session_id: str) -> Optional[Path]:
    """Locate the <session>/subagents/ directory for a main session id.

    The harness writes every spawned subagent's transcript to
    `<project>/<main-session-id>/subagents/agent-a<name>-<hash>.jsonl`.
    This is the only place their usage data lives — the Agent tool result
    does not carry it. Accepts a full id or an unambiguous prefix.
    """
    session_dir = _project_session_dir()
    if not session_dir.exists():
        return None
    exact = session_dir / session_id / "subagents"
    if exact.is_dir():
        return exact
    matches = [d / "subagents" for d in session_dir.glob(f"{session_id}*") if d.is_dir()]
    matches = [m for m in matches if m.is_dir()]
    if len(matches) == 1:
        return matches[0]
    return None


def _resolve_current_session(explicit: str) -> str:
    """Resolve the session id for `--subagents` when no value was given.

    Order: the explicit value → `$CLAUDE_SESSION_ID` → the most recently
    modified `<project>/<id>/subagents/` directory owner. The last fallback
    matters because Claude Code does not reliably export `CLAUDE_SESSION_ID`
    into Bash tool subprocesses; the newest subagents dir is almost always the
    live session. Returns "" when nothing can be resolved.
    """
    if explicit:
        return explicit
    env = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if env:
        return env
    session_dir = _project_session_dir()
    if not session_dir.exists():
        return ""
    candidates = [
        d / "subagents"
        for d in session_dir.iterdir()
        if d.is_dir() and (d / "subagents").is_dir()
    ]
    if not candidates:
        return ""
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return newest.parent.name


def _role_from_subagent(path: Path) -> tuple[str, str]:
    """Return (role, agent_type) for a subagent transcript file.

    Transcript file is `agent-<agentId>.jsonl`. Named spawns carry `name` in the
    sibling `.meta.json` (role = name). Unnamed spawns (translators) have a meta
    with only `agentType`/`description`, so role = the agentId itself
    (`stem.removeprefix("agent-")`) — match it to the Agent tool result's agentId.
    agent_type preference: `customAgentType` → `agentType` (when it differs
    from the role) → "".
    """
    role = ""
    agent_type = ""
    meta = path.with_suffix(".meta.json")
    if meta.exists():
        try:
            with open(meta, "r", encoding="utf-8") as f:
                data = json.load(f)
            role = str(data.get("name", "") or "")
            agent_type = str(data.get("customAgentType", "") or "")
            if not agent_type:
                builtin = str(data.get("agentType", "") or "")
                agent_type = builtin if builtin and builtin != role else ""
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    if not role:
        role = path.stem.removeprefix("agent-")
    return role, agent_type


def _parse_subagents(session_id: str) -> list[SessionUsage]:
    """Parse every subagent transcript belonging to a main session."""
    sub_dir = _subagents_dir(session_id)
    if not sub_dir:
        return []
    usages = []
    for f in sorted(sub_dir.glob("*.jsonl")):
        u = _parse_session(f)
        if not u:
            continue
        u.role, u.agent_type = _role_from_subagent(f)
        u.parent_session = session_id
        usages.append(u)
    usages.sort(key=lambda u: u.modified_ago_seconds)
    return usages


def _format_table(usages: list[SessionUsage]) -> str:
    """Format usage data as a readable table."""
    if not usages:
        return "No sessions with usage data found."

    lines = []
    lines.append(
        f"{'Session':<12} {'Calls':>6} {'Context':>10} {'Util%':>6} "
        f"{'Max':>10} {'Status':<8} Recommendation"
    )
    lines.append("-" * 90)

    for u in usages:
        ctx = f"{u.last_context_tokens:,}"
        mx = f"{u.max_context_tokens:,}"
        status_icon = {"ok": "✅", "warning": "⚠️", "full": "🔴"}.get(
            u.status, "?"
        )
        lines.append(
            f"{u.session_id[:12]:<12} {u.api_calls:>6} {ctx:>10} "
            f"{u.utilization_pct:>5.1f}% {mx:>10} "
            f"{status_icon} {u.status:<6} {u.recommendation}"
        )

    # Summary
    if len(usages) > 1:
        total_input = sum(u.total_input_tokens for u in usages)
        total_output = sum(u.total_output_tokens for u in usages)
        lines.append("-" * 90)
        lines.append(
            f"{'TOTAL':<12} {sum(u.api_calls for u in usages):>6} "
            f"{'':>10} {'':>6} {'':>10} "
            f"   input={total_input:,} output={total_output:,}"
        )

    return "\n".join(lines)


def _format_subagent_table(
    usages: list[SessionUsage], main_usage: Optional[SessionUsage] = None
) -> str:
    """Format subagent usage as a batch-facing table.

    Columns match the runbook's Batch-End Usage Report so the orchestrator can
    paste the output directly. `Util%` is computed from `max_context_tokens`
    (peak context reached), not `last_context_tokens` — the decision the report
    feeds ("did this agent approach the window?") is about the peak, and a
    subagent that ended on a small summary turn would otherwise look light.
    `Cost $` is Sonnet-priced (PRICE_PER_MTOK). When `main_usage` is given, a
    `main` row (the orchestrator session to date) is added and counted in TOTAL.
    """
    if not usages:
        return "No subagent usage data found for this session."

    lines = []
    lines.append(
        f"{'Agent':<28} {'Type':<14} {'Calls':>6} {'Input':>10} "
        f"{'Output':>9} {'CacheRead':>11} {'CacheCreate':>12} "
        f"{'Ctx(max)':>10} {'Util%':>6} {'Cost $':>8}"
    )
    lines.append("-" * 123)

    rows = list(usages) + ([main_usage] if main_usage else [])
    total_calls = total_in = total_out = total_cr = total_cc = 0
    total_cost = 0.0
    for u in rows:
        is_main = u is main_usage
        role = "main (session)" if is_main else u.role
        agent_type = "orchestrator" if is_main else u.agent_type
        peak_util = u.max_context_tokens / CONTEXT_WINDOW_LIMIT * 100
        if is_main:
            lines.append("-" * 123)
        lines.append(
            f"{role[:27]:<28} {agent_type[:13]:<14} {u.api_calls:>6} "
            f"{u.total_input_tokens:>10,} {u.total_output_tokens:>9,} "
            f"{u.total_cache_read_tokens:>11,} "
            f"{u.total_cache_create_tokens:>12,} {u.max_context_tokens:>10,} "
            f"{peak_util:>5.1f}% {u.cost_usd:>8.2f}"
        )
        total_calls += u.api_calls
        total_in += u.total_input_tokens
        total_out += u.total_output_tokens
        total_cr += u.total_cache_read_tokens
        total_cc += u.total_cache_create_tokens
        total_cost += u.cost_usd

    lines.append("-" * 123)
    lines.append(
        f"{'TOTAL':<28} {'':<14} {total_calls:>6} {total_in:>10,} "
        f"{total_out:>9,} {total_cr:>11,} {total_cc:>12,} "
        f"{'':>10} {'':>6} {total_cost:>8.2f}"
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check Claude Code agent context usage from session logs"
    )
    parser.add_argument(
        "session_id", nargs="?", help="Session ID (or prefix) to check"
    )
    parser.add_argument(
        "--recent",
        nargs="?",
        const=RECENT_COUNT_DEFAULT,
        type=int,
        help=f"Find N most recent subagent sessions (default {RECENT_COUNT_DEFAULT})",
    )
    parser.add_argument(
        "--active",
        nargs="?",
        const=RECENT_MINUTES_DEFAULT,
        type=int,
        help=f"Sessions modified in last N minutes (default {RECENT_MINUTES_DEFAULT})",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    parser.add_argument(
        "--include-current",
        action="store_true",
        help="Include current main session in --recent/--active results",
    )
    parser.add_argument(
        "--subagents",
        nargs="?",
        const="",
        metavar="SESSION_ID",
        help=(
            "List per-subagent usage for a main session (reads "
            "<session>/subagents/*.jsonl). Accepts a full id or prefix; with no "
            "value, resolves $CLAUDE_SESSION_ID, else the most recently "
            "modified session that has a subagents/ directory."
        ),
    )
    parser.add_argument(
        "--all", action="store_true", help="Show all sessions"
    )

    args = parser.parse_args()

    # Mode 0: per-subagent usage for a main session
    if args.subagents is not None:
        target = _resolve_current_session(args.subagents)
        if not target:
            print(
                "--subagents: no session id given and none could be resolved "
                "(no $CLAUDE_SESSION_ID, no <session>/subagents/ directory). "
                "Pass a session id explicitly.",
                file=sys.stderr,
            )
            sys.exit(1)
        main_path = _find_session_file(target)
        resolved = main_path.stem if main_path else target
        usages = _parse_subagents(resolved)
        if not usages:
            expected = _subagents_dir(resolved)
            where = str(expected) if expected else "a <session>/subagents/ directory"
            print(
                f"No subagent transcripts found for session '{target}'. "
                f"Expected {where}",
                file=sys.stderr,
            )
            sys.exit(1)
        main_usage = _parse_session(main_path) if main_path else None
        if args.json:
            print(json.dumps([asdict(u) for u in usages], indent=2))
        else:
            print(_format_subagent_table(usages, main_usage))
        return

    # Mode 1: specific session
    if args.session_id:
        path = _find_session_file(args.session_id)
        if not path:
            print(f"Session not found: {args.session_id}", file=sys.stderr)
            sys.exit(1)
        usage = _parse_session(path)
        if not usage:
            print("No usage data in session", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(asdict(usage), indent=2))
        else:
            print(_format_table([usage]))
        return

    # Mode 2: --all
    if args.all:
        session_dir = _project_session_dir()
        files = list(session_dir.glob("*.jsonl"))
        usages = []
        for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
            u = _parse_session(f)
            if u:
                usages.append(u)
        if args.json:
            print(json.dumps([asdict(u) for u in usages[:50]], indent=2))
        else:
            print(_format_table(usages[:50]))
        return

    # Mode 3: --recent or --active
    minutes = args.active if args.active else 0
    count = args.recent if args.recent else RECENT_COUNT_DEFAULT

    exclude = None if args.include_current else os.environ.get("CLAUDE_SESSION_ID")
    sessions = _find_recent_sessions(count, exclude_session=exclude, minutes=minutes)

    if not sessions:
        print("No recent sessions found.", file=sys.stderr)
        sys.exit(0)

    usages = []
    for path, _ in sessions:
        u = _parse_session(path)
        if u:
            usages.append(u)

    if args.json:
        print(json.dumps([asdict(u) for u in usages], indent=2))
    else:
        print(_format_table(usages))


if __name__ == "__main__":
    main()