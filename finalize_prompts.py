#!/usr/bin/env python3
"""
Finalize cb-prompts.json:

1. Sibling-inherit: for every entry whose prompt is "Same..." or <40 chars,
   find the longest substantive sibling in the same (batch_prefix, sport)
   subgroup and inherit its prompt. Mark the entry with inherited_from.
2. Report coverage: how many entries have a substantive prompt after the
   inherit pass, broken down by source.
3. Write cb-prompts.json with a metadata header including generation time and
   source counts.
"""
import json
import os
import re
import datetime

IDEAS_DIR = '/Users/justinbarad/Documents/Claude Code/ideas'
INPUT = os.path.join(IDEAS_DIR, 'cb-prompts.json')
OUTPUT = os.path.join(IDEAS_DIR, 'cb-prompts.json')


def is_short(p):
    if not p:
        return True
    if 'Same prompt' in p or 'Same as' in p:
        return True
    if p.strip().lower() == 'same':
        return True
    if len(p) < 40:
        return True
    return False


def batch_key(id, sport):
    prefix = id.replace('_', '-').split('-')[0]
    return (prefix, sport or '?')


def main():
    with open(INPUT) as f:
        merged = json.load(f)

    # If file already has a metadata header, unwrap it.
    if isinstance(merged, dict) and 'items' in merged and 'meta' in merged:
        merged = merged['items']

    # Group by (prefix, sport).
    from collections import defaultdict
    groups = defaultdict(list)
    for url, rec in merged.items():
        id = rec.get('id', '')
        sport = rec.get('sport') or ''
        groups[batch_key(id, sport)].append((url, rec))

    # Pick canonical per group: the longest substantive prompt.
    canonical = {}
    for key, items in groups.items():
        best = None
        best_len = 0
        for url, rec in items:
            p = rec.get('prompt') or ''
            if is_short(p):
                continue
            if len(p) > best_len:
                best = (url, rec)
                best_len = len(p)
        if best:
            canonical[key] = best

    # Inherit.
    inherited = 0
    for url, rec in merged.items():
        p = rec.get('prompt') or ''
        if not is_short(p):
            continue
        id = rec.get('id', '')
        sport = rec.get('sport') or ''
        key = batch_key(id, sport)
        if key in canonical:
            can_url, can_rec = canonical[key]
            if can_url == url:
                continue
            rec['prompt_inherited_from'] = can_rec.get('id')
            rec['prompt_original'] = p
            rec['prompt'] = can_rec.get('prompt')
            # If seed wasn't set, inherit that too (though different seeds per sibling).
            if not rec.get('seed') and can_rec.get('seed'):
                rec['seed_inherited'] = True
                rec['seed'] = can_rec.get('seed')
            if not rec.get('ref') and can_rec.get('ref'):
                rec['ref'] = can_rec.get('ref')
            inherited += 1

    # Count final state.
    substantive = 0
    short = 0
    by_source = defaultdict(int)
    for rec in merged.values():
        p = rec.get('prompt') or ''
        if is_short(p):
            short += 1
        else:
            substantive += 1
        by_source[rec.get('source', 'unknown')] += 1

    print(f'Total items: {len(merged)}')
    print(f'Substantive prompts: {substantive}')
    print(f'Short/unresolved: {short}')
    print(f'Inherited from sibling: {inherited}')
    print()
    print('Sources:')
    for src, n in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f'  {n:>4}  {src}')

    # List the remaining short ones for follow-up.
    remaining = []
    for url, rec in merged.items():
        p = rec.get('prompt') or ''
        if is_short(p):
            remaining.append({
                'id': rec.get('id'),
                'sport': rec.get('sport'),
                'prompt': p,
                'label': rec.get('label'),
            })
    if remaining:
        print(f'\nStill-short ({len(remaining)}):')
        for r in remaining[:30]:
            print(f'  {r["id"]:30}  "{r["prompt"][:60]}"')

    # Build metadata-wrapped output.
    meta = {
        'generated': datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z',
        'total': len(merged),
        'substantive_count': substantive,
        'short_count': short,
        'inherited_count': inherited,
        'sources': dict(by_source),
        'note': (
            'Source of truth for CB2 AI Creative Lab generation prompts. '
            'Results files (*_results.json) have full 500+ char prompts with '
            'seed+ref+arm metadata for the Apr 8 production batches (v1, rot, '
            'refab, dual, snow). cb-review.html covers the older batches with '
            'shorter but exact prompts (20-120 chars — that is the literal '
            'text sent to the API during that era). Sibling-inherit was used '
            'to copy canonical prompts to "Same as X" placeholder entries '
            'within the same (prefix, sport) subgroup.'
        ),
    }
    out = {
        'meta': meta,
        'items': merged,
    }
    with open(OUTPUT, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote {OUTPUT} ({os.path.getsize(OUTPUT) / 1024:.0f}KB)')


if __name__ == '__main__':
    main()
