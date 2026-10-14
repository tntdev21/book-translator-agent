#!/usr/bin/env node
/**
 * translated-guard.cjs - PreToolUse role guard for book text files (P9 V3)
 *
 * Roles come from stdin `agent_type` (present only inside a subagent; absent = main).
 *   main       : deny Edit/Write/MultiEdit and Bash redirects/tee/sed -i/rm/mv/cp on
 *                books/<id>/{translated/**, chunks/*.md, source/**}
 *   translator : deny Bash writes there (sed -i, perl -i, redirects, heredoc/python -c,
 *                python scripts other than fix.py / compare-structure.py / validate-translation.py);
 *                Edit/Write allowed (owner check is the agent def's job)
 *   editor     : deny Write on translated/** and Bash writes there; Edit allowed
 *   other      : no-op
 *
 * Bash detection is heuristic and biased to false negatives: reads (cat, wc,
 * test -s) and the validators (fix.py, compare-structure.py) always pass.
 * Deny = exit 0 + hookSpecificOutput.permissionDecision "deny"; one line per
 * denial is appended to logs/hook-denials.txt. Any internal error fails open.
 */

const fs = require('fs');
const path = require('path');

const PROTECTED = /books\/[^\/\s'"]+\/(?:translated\/|chunks\/[^\/\s'"]*\.md\b|source\/)/;
const TRANSLATED = /books\/[^\/\s'"]+\/translated\//;
const REASONS = {
  main: 'orchestrator never edits text; SendMessage RETRY to owning translator',
  translator: 'use the Edit tool (or Write for a full rewrite)',
  editor: 'editor auto-fixes typos with the Edit tool only; report everything else',
};
const ROLES = new Set(Object.keys(REASONS));
const AGENT_SCRIPTS = new Set(['fix.py', 'compare-structure.py', 'validate-translation.py']);

/** Inline simple `VAR=value` assignments so `T=books/..; sed -i .. $T` is seen. */
function expandVars(cmd) {
  const vars = {};
  const re = /(?:^|[\s;&|(])([A-Za-z_]\w*)=(?:"([^"]*)"|'([^']*)'|([^\s;&|]+))/g;
  let m;
  while ((m = re.exec(cmd))) vars[m[1]] = m[2] ?? m[3] ?? m[4];
  return cmd.replace(/\$\{?([A-Za-z_]\w*)\}?/g, (all, name) => (name in vars ? vars[name] : all));
}

function tokens(seg) {
  return seg.replace(/["']/g, ' ').trim().split(/\s+/).filter(Boolean);
}

/** First real command word, skipping env assignments and wrappers. */
function commandWord(toks) {
  let i = 0;
  while (i < toks.length && (/^[A-Za-z_]\w*=/.test(toks[i]) || ['sudo', 'command', 'env', 'nohup', 'time'].includes(toks[i]))) i++;
  return [path.basename(toks[i] || ''), toks.slice(i + 1)];
}

/** Returns the offending segment if the Bash command writes to a path matching pathRe. */
function bashWrite(command, pathRe, agent = true) {
  const cmd = expandVars(command);
  // A bare `books/<id>/translated` or `source` dir (no trailing slash) counts too.
  const has = (s) => pathRe.test(s.replace(/\/(translated|source)(?![\w\/])/g, "/$1/"));
  if (!has(cmd)) return null;
  // Inline python/heredoc code that mentions a protected path (agents only:
  // main's own heredocs, e.g. docs edits that quote paths, must not trip it).
  if (agent && /(?:^|[\s;&|(\/])python3?\b[^\n;&|]*(?:\s-c\s|\s-\s|<<)/.test(cmd)) return cmd;
  let inDir = false; // a prior `cd <protected dir>` makes relative targets protected
  // Heredoc bodies are data, not commands; the opener line (with any redirect) stays.
  const body = cmd.replace(/<<-?\s*['"]?(\w+)['"]?([^\n]*)\n[\s\S]*?\n\s*\1[ \t]*(?=\n|$)/g, '<<$1$2');
  for (const seg of body.split(/&&|\|\||[;|\n]/)) {
    const toks = tokens(seg);
    const [word, args] = commandWord(toks);
    if (word === 'cd') { inDir = args.some((a) => has(a)); continue; }
    if (!inDir && !has(seg)) continue;
    // Redirect into a protected path, incl. 1> and &> (not fd dups like 2>&1).
    const redir = /(?:^|[^<>&\d])(?:&|\d+)?>>?(?!&)\s*['"]?([^\s'";&|>]+)/g;
    let r;
    while ((r = redir.exec(seg))) if (has(r[1]) || (inDir && !r[1].startsWith('/'))) return seg;
    const hit = inDir || args.some((a) => has(a));
    if (['rm', 'rmdir', 'mv', 'truncate', 'tee', 'unlink', 'shred'].includes(word) && hit) return seg;
    if (['cp', 'ln', 'install', 'rsync'].includes(word) && args.length && (inDir || has(args[args.length - 1]))) return seg;
    if (['sed', 'gsed'].includes(word) && hit && args.some((a) => /^-[a-zA-Z]*i|^--in-place/.test(a))) return seg;
    if (word === 'perl' && hit && args.some((a) => /^-[a-zA-Z]*i/.test(a))) return seg;
    if (['awk', 'gawk'].includes(word) && hit && args.some((a) => a === 'inplace')) return seg;
    if (word === 'find' && hit && args.some((a) => a === '-delete' || a === 'rm' || a === '-execdir')) return seg;
    if (word === 'dd' && args.some((a) => a.startsWith('of=') && (inDir || has(a)))) return seg;
    if (word === 'git' && hit && args.some((a) => ['checkout', 'restore', 'rm', 'mv', 'clean'].includes(a))) return seg;
    // Agents may run only the sanctioned validators on their text (no fix10.py-style scripts).
    if (agent && /^python[\d.]*$/.test(word) && hit) {
      const script = path.basename(args.find((a) => !a.startsWith('-')) || '');
      if (!AGENT_SCRIPTS.has(script)) return seg;
    }
  }
  return null;
}

function editPaths(input) {
  const out = [];
  if (input && typeof input.file_path === 'string') out.push(input.file_path);
  if (input && Array.isArray(input.edits)) {
    for (const e of input.edits) if (e && typeof e.file_path === 'string') out.push(e.file_path);
  }
  return out;
}

/** Pure decision: returns {reason, target} to deny, or null to allow. */
function decide(payload) {
  const role = payload.agent_type || 'main';
  if (!ROLES.has(role)) return null;
  const tool = payload.tool_name;
  const input = payload.tool_input || {};
  if (tool === 'Bash') {
    const re = role === 'main' ? PROTECTED : TRANSLATED;
    const seg = bashWrite(String(input.command || ''), re, role !== 'main');
    return seg ? { role, reason: REASONS[role], target: seg.trim() } : null;
  }
  if (!['Edit', 'Write', 'MultiEdit'].includes(tool)) return null;
  const p = editPaths(input).map((f) => f.replace(/\\/g, '/'));
  if (role === 'main') {
    const t = p.find((f) => PROTECTED.test(f));
    return t ? { role, reason: REASONS.main, target: t } : null;
  }
  if (role === 'editor' && tool === 'Write') {
    const t = p.find((f) => TRANSLATED.test(f));
    return t ? { role, reason: REASONS.editor, target: t } : null;
  }
  return null;
}

function logDenial(payload, d) {
  try {
    const root = process.env.CLAUDE_PROJECT_DIR || payload.cwd || process.cwd();
    const dir = path.join(root, 'logs');
    fs.mkdirSync(dir, { recursive: true });
    const excerpt = d.target.replace(/\s+/g, ' ').slice(0, 160);
    fs.appendFileSync(path.join(dir, 'hook-denials.txt'),
      `${new Date().toISOString()}\t${d.role}\t${payload.tool_name}\t${excerpt}\n`);
  } catch (_) { /* logging never blocks the decision */ }
}

function main() {
  let raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch (_) { process.exit(0); }
  let payload;
  try { payload = JSON.parse(raw); } catch (_) { process.exit(0); }
  const d = decide(payload);
  if (!d) process.exit(0);
  logDenial(payload, d);
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: `translated-guard (${d.role}): ${d.reason}`,
    },
  }));
  process.exit(0);
}

if (require.main === module) {
  try { main(); } catch (_) { process.exit(0); }
}

module.exports = { decide, bashWrite };
