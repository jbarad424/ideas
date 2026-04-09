#!/usr/bin/env python3
"""
Second-pass transcript miner for prompts that were passed through shell
function calls (which my first miner missed because the "prompt" JSON
literal contained $PROMPT instead of the text).

Pattern we match:
  generate "BATCH-ID" SEED "FULL PROMPT TEXT"
  generate "BATCH-ID" "FULL PROMPT TEXT"
  gen "BATCH-ID" SEED "FULL PROMPT TEXT"

Usage:
  python3 mine_shell_funcs.py

Produces mined_shell_prompts.json mapping id -> {prompt, seed, source, cmd_line}.
This is then merged into cb-prompts.json by finalize_prompts.py (round 2).
"""
import json
import os
import re

TRANSCRIPT_DIR = '/Users/justinbarad/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas'
OUTPUT = '/Users/justinbarad/Documents/Claude Code/ideas/mined_shell_prompts.json'

# Match: word(generate|gen) "ID" [SEED|$VAR|$((expr))] "PROMPT"
# Allow for bash arithmetic in ID too.
CALL_PAT = re.compile(
    r'\b(?:generate|gen)\s+'
    r'"([^"\n]+)"\s+'           # id
    r'([^\s"\n]+)\s+'            # seed (number, $var, or $((...)))
    r'"([^"\n]{20,})"'           # prompt (at least 20 chars)
)
# Also handle the 2-arg variant: generate "ID" "PROMPT" (no seed)
CALL_PAT_NOSEED = re.compile(
    r'\b(?:generate|gen)\s+'
    r'"([^"\n]+)"\s+'           # id
    r'"([^"\n]{20,})"'           # prompt
)
# Handle bash for loops to unroll IDs that use $((base+i))
FOR_LOOP_PAT = re.compile(r'for\s+(\w+)\s+in\s+([^;\n]+);\s*do(.*?)done', re.DOTALL)
VAR_ID_PAT = re.compile(r'\$\(\(\s*(\d+)\s*\+\s*(\w+)\s*\)\)')


def unroll_ids(id_template, seed_template, loop_var, loop_values):
    """Given id='flex7-moto-$((2000+i))' and seed='$((2000+i))' and
    loop_values=['0','1','2','3','4'], return list of (id, seed)."""
    out = []
    for v in loop_values:
        try:
            v_int = int(v)
        except ValueError:
            continue
        def sub(m):
            base = int(m.group(1))
            var = m.group(2)
            if var != loop_var:
                return m.group(0)
            return str(base + v_int)
        id_r = VAR_ID_PAT.sub(sub, id_template)
        seed_r = VAR_ID_PAT.sub(sub, seed_template)
        # Handle raw $i substitution.
        id_r = id_r.replace(f'${loop_var}', str(v_int))
        seed_r = seed_r.replace(f'${loop_var}', str(v_int))
        out.append((id_r, seed_r))
    return out


def extract_from_command(cmd, source_tag):
    """Return list of {id, seed, prompt, source} dicts extracted from a single
    bash command. Handles both direct calls and calls inside for loops."""
    out = []
    # First find all for loops and process their bodies.
    matched_ranges = []
    for m in FOR_LOOP_PAT.finditer(cmd):
        loop_var = m.group(1)
        values_str = m.group(2).strip()
        # Parse values: space-separated or $(seq ...)
        if values_str.startswith('$(seq') or values_str.startswith('`seq'):
            seq_m = re.search(r'seq\s+(\d+)(?:\s+(\d+))?(?:\s+(\d+))?', values_str)
            if seq_m:
                a, b, c = seq_m.groups()
                a = int(a)
                if c:
                    values = list(range(int(a), int(c) + 1, int(b)))
                elif b:
                    values = list(range(int(a), int(b) + 1))
                else:
                    values = [a]
                values = [str(v) for v in values]
            else:
                values = []
        else:
            values = values_str.split()
        body = m.group(3)
        matched_ranges.append((m.start(), m.end()))
        for call_m in CALL_PAT.finditer(body):
            id_t, seed_t, prompt = call_m.groups()
            for id, seed in unroll_ids(id_t, seed_t, loop_var, values):
                out.append({
                    'id': id,
                    'seed': seed,
                    'prompt': prompt,
                    'source': f'transcript_shell:{source_tag}',
                })
        for call_m in CALL_PAT_NOSEED.finditer(body):
            id_t, prompt = call_m.groups()
            # Skip if already matched by 3-arg pattern
            if CALL_PAT.search(body[call_m.start():call_m.end() + 10]):
                continue
            for id, _ in unroll_ids(id_t, '', loop_var, values):
                out.append({
                    'id': id,
                    'seed': None,
                    'prompt': prompt,
                    'source': f'transcript_shell:{source_tag}',
                })

    # Now scan the parts of the command that weren't in any for loop.
    def in_match(pos):
        return any(s <= pos < e for s, e in matched_ranges)

    for call_m in CALL_PAT.finditer(cmd):
        if in_match(call_m.start()):
            continue
        id, seed, prompt = call_m.groups()
        if '$' in id:
            continue  # unresolvable without a loop context
        out.append({
            'id': id,
            'seed': seed if seed.isdigit() else None,
            'prompt': prompt,
            'source': f'transcript_shell:{source_tag}',
        })
    for call_m in CALL_PAT_NOSEED.finditer(cmd):
        if in_match(call_m.start()):
            continue
        id, prompt = call_m.groups()
        if '$' in id:
            continue
        # Skip if the 3-arg pattern already matched here
        if CALL_PAT.match(cmd, call_m.start()):
            continue
        out.append({
            'id': id,
            'seed': None,
            'prompt': prompt,
            'source': f'transcript_shell:{source_tag}',
        })
    return out


def main():
    recovered = {}
    total_cmds = 0
    matched_cmds = 0
    for fname in sorted(os.listdir(TRANSCRIPT_DIR)):
        if not fname.endswith('.jsonl'):
            continue
        p = os.path.join(TRANSCRIPT_DIR, fname)
        if os.path.isdir(p) or os.path.getsize(p) < 10000:
            continue
        with open(p, errors='replace') as f:
            for line_no, raw in enumerate(f, 1):
                if '"tool_use"' not in raw:
                    continue
                if 'generate ' not in raw and 'gen "' not in raw:
                    continue
                try:
                    rec = json.loads(raw)
                except Exception:
                    continue
                msg = rec.get('message', {}) or {}
                content = msg.get('content', [])
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') != 'tool_use' or c.get('name') != 'Bash':
                        continue
                    cmd = ((c.get('input') or {}).get('command') or '')
                    if not cmd:
                        continue
                    total_cmds += 1
                    tag = f'{fname}:line{line_no}'
                    hits = extract_from_command(cmd, tag)
                    if not hits:
                        continue
                    matched_cmds += 1
                    for h in hits:
                        if h['id'] not in recovered:
                            recovered[h['id']] = h
    print(f'Scanned bash commands: {total_cmds}')
    print(f'Commands with shell-func hits: {matched_cmds}')
    print(f'Unique IDs recovered: {len(recovered)}')

    # How many of these IDs appear in the corpus?
    corpus = json.load(open('/Users/justinbarad/Documents/Claude Code/ideas/_rate_corpus.json'))
    corpus_ids = {i['id'] for i in corpus}
    matched_ids = set(recovered.keys()) & corpus_ids
    print(f'IDs matching corpus: {len(matched_ids)}')

    # Sample
    sample_keys = sorted(matched_ids)[:10]
    for k in sample_keys:
        r = recovered[k]
        print(f'\n  {k}')
        print(f'    seed: {r.get("seed")}')
        print(f'    prompt ({len(r["prompt"])} chars): {r["prompt"][:200]}')

    with open(OUTPUT, 'w') as f:
        json.dump(recovered, f, indent=2)
    print(f'\nWrote {OUTPUT}')


if __name__ == '__main__':
    main()
