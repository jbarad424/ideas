#!/usr/bin/env python3
"""Merge mined_shell_prompts.json into cb-prompts.json, overwriting any
short/placeholder prompts with the shell-mined full versions.

Shell-mined entries are preferred over cb-review.html summaries because they
are the literal arguments passed to the fal.ai API (exact prompts).
"""
import json
import os
import datetime

IDEAS_DIR = '/Users/justinbarad/Documents/Claude Code/ideas'

def is_short(p):
    if not p: return True
    if 'Same prompt' in p or 'Same as' in p: return True
    if p.strip().lower() == 'same': return True
    if len(p) < 40: return True
    return False

def main():
    with open(os.path.join(IDEAS_DIR, 'cb-prompts.json')) as f:
        data = json.load(f)
    meta = data.get('meta', {})
    items = data.get('items', data)  # allow both wrapped and unwrapped
    corpus = json.load(open(os.path.join(IDEAS_DIR, '_rate_corpus.json')))
    id_to_url = {i['id']: i['url'] for i in corpus}
    shell = json.load(open(os.path.join(IDEAS_DIR, 'mined_shell_prompts.json')))

    overwrote = 0
    added_seed = 0
    for id, rec in shell.items():
        url = id_to_url.get(id)
        if not url or url not in items:
            continue
        existing = items[url]
        existing_prompt = existing.get('prompt') or ''
        shell_prompt = rec.get('prompt') or ''
        # Overwrite if existing is short and shell is longer
        if is_short(existing_prompt) and len(shell_prompt) > len(existing_prompt):
            existing['prompt_original'] = existing_prompt
            existing['prompt'] = shell_prompt
            existing['source'] = rec.get('source')
            overwrote += 1
            # Also backfill seed if we have it
            if not existing.get('seed') and rec.get('seed'):
                existing['seed'] = rec['seed']
                added_seed += 1
        # Also backfill seed on substantive entries if missing
        elif not existing.get('seed') and rec.get('seed'):
            existing['seed'] = rec['seed']
            added_seed += 1

    # Recount
    substantive = sum(1 for r in items.values() if not is_short(r.get('prompt', '')))
    short = len(items) - substantive

    print(f'Overwrote {overwrote} short prompts with shell-mined full prompts')
    print(f'Added seed to {added_seed} entries')
    print(f'Substantive now: {substantive}/{len(items)} '
          f'({substantive*100/len(items):.0f}%)')
    print(f'Short remaining: {short}')

    # List remaining shorts
    remaining = []
    for url, rec in items.items():
        if is_short(rec.get('prompt', '')):
            remaining.append(rec.get('id', ''))
    if remaining:
        from collections import Counter
        pref = Counter(r.replace('_','-').split('-')[0] for r in remaining)
        print('\nRemaining short by prefix:')
        for p, n in pref.most_common():
            print(f'  {n:>4}  {p}')

    # Update metadata
    meta.update({
        'generated': datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z',
        'total': len(items),
        'substantive_count': substantive,
        'short_count': short,
        'shell_mined_overwrites': overwrote,
        'shell_mined_seed_backfills': added_seed,
    })
    out = {'meta': meta, 'items': items}
    with open(os.path.join(IDEAS_DIR, 'cb-prompts.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote cb-prompts.json ({os.path.getsize(os.path.join(IDEAS_DIR, "cb-prompts.json")) / 1024:.0f}KB)')

if __name__ == '__main__':
    main()
