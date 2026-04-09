#!/usr/bin/env python3
"""
Build cb-prompts.json — the durable source of truth for every CB2 corpus item.

Priority order (highest = best):
1. Per-batch results files (*_results.json)
   - Have full prompt, exact seed, ref metadata (id+url+colorway+type), arm,
     scene_id, label, sport.
   - Cover ~180 items from production_v1, ref_ab, ref_ab_rotated, dual,
     snow tests.
2. cb-review.html ALL_IMAGES array
   - Has full prompt (variable length — median 71 chars, max 605), id, url,
     model, label.
   - Missing seed/ref metadata but prompt is the thing that matters most.
   - Covers ~566 items.
3. Claude Code transcripts (fallback, TODO)
   - For anything not covered above, mine the .jsonl files for bash tool calls
     that sent a prompt to fal.ai.

Output schema (keyed by url):
{
  "https://...": {
    "id": "h3_moto_s0",
    "url": "https://...",
    "prompt": "Full prompt text...",
    "seed": 9101,
    "ref": {"id": "h3", "name": "...", "colorway": "Hunter", "type": "jacket",
            "url": "https://jbarad424.github.io/ideas/rotated-refs/h3.jpg"},
    "arm": "LEFT",
    "sport": "moto",
    "model": "Nano Banana Pro",
    "label": "Production V1 - h3 moto s0",
    "scene_id": "s0",
    "source": "results_file:production_batch_v1_results.json"
  },
  ...
}
"""

import json
import os
import re
import sys
from collections import Counter

IDEAS_DIR = '/Users/justinbarad/Documents/Claude Code/ideas'
OUTPUT = os.path.join(IDEAS_DIR, 'cb-prompts.json')

RESULT_FILES = [
    'production_batch_v1_results.json',
    'ref_ab_rotated_results.json',   # higher prio than plain ref_ab because rotated is the winner
    'ref_ab_test_results.json',
    'dual_ref_test_results.json',
    'snow_goofy_test_results.json',
    'snow_mirror_test_results.json',
    'snow_arm_flip_results.json',
    'mirrored_img2_test_results.json',
]


def load_corpus():
    with open(os.path.join(IDEAS_DIR, '_rate_corpus.json')) as f:
        return json.load(f)


def harvest_results_files(corpus_urls):
    recovered = {}
    for fname in RESULT_FILES:
        p = os.path.join(IDEAS_DIR, fname)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            url = item.get('url')
            if not url or url in recovered:
                continue
            if url not in corpus_urls:
                continue
            recovered[url] = {
                'url': url,
                'prompt': item.get('prompt'),
                'seed': item.get('seed'),
                'ref': item.get('ref') or item.get('ref_id') or item.get('pair'),
                'arm': item.get('arm') or item.get('arm_prompt') or item.get('stance'),
                'sport': item.get('sport'),
                'label': item.get('label'),
                'scene_id': item.get('scene_id') or item.get('scene_idx'),
                'source': f'results_file:{fname}',
            }
    return recovered


def harvest_cb_review(corpus_urls):
    p = os.path.join(IDEAS_DIR, 'cb-review.html')
    with open(p) as f:
        html = f.read()

    # Match one object at a time. Quotes are single-quotes throughout the file,
    # and prompts may contain escaped single quotes.
    pat = re.compile(
        r"\{\s*id:\s*'([^']+)'\s*,\s*"
        r"url:\s*'([^']+)'\s*,\s*"
        r"model:\s*'([^']*)'\s*,\s*"
        r"prompt:\s*'((?:[^'\\]|\\.)*)'[^}]*?"
        r"(?:label:\s*'([^']*)'[^}]*?)?"
        r"\}",
        re.DOTALL,
    )
    recovered = {}
    for m in pat.finditer(html):
        id, url, model, prompt, label = m.groups()
        if url not in corpus_urls:
            continue
        if url in recovered:
            continue
        prompt = prompt.replace("\\'", "'").replace('\\n', '\n').replace('\\\\', '\\')
        recovered[url] = {
            'url': url,
            'id_from_review': id,
            'prompt': prompt,
            'model': model,
            'label': label,
            'source': 'cb-review.html',
        }
    return recovered


def main():
    corpus = load_corpus()
    corpus_urls = {i['url'] for i in corpus}
    url_to_corpus = {i['url']: i for i in corpus}
    print(f'Corpus: {len(corpus)} items')

    # Tier 1: results files (best, full metadata).
    tier1 = harvest_results_files(corpus_urls)
    print(f'Tier 1 (results files): {len(tier1)} items')

    # Tier 2: cb-review.html (prompt only, 82% coverage).
    tier2 = harvest_cb_review(corpus_urls)
    print(f'Tier 2 (cb-review.html): {len(tier2)} items')

    # Merge: tier1 wins, tier2 fills gaps.
    merged = {}
    for url, rec in tier1.items():
        base = url_to_corpus[url]
        rec.setdefault('id', base['id'])
        rec.setdefault('model', base.get('model'))
        merged[url] = rec
    for url, rec in tier2.items():
        if url in merged:
            # If merged has no prompt (shouldn't happen), backfill.
            if not merged[url].get('prompt'):
                merged[url]['prompt'] = rec['prompt']
            continue
        base = url_to_corpus[url]
        rec['id'] = base['id']
        rec['sport'] = base.get('sport')
        rec['model'] = rec.get('model') or base.get('model')
        merged[url] = rec

    # Still missing?
    missing = corpus_urls - set(merged.keys())
    print(f'Merged: {len(merged)}/{len(corpus_urls)} '
          f'({len(merged) * 100 / len(corpus_urls):.0f}%) — '
          f'missing {len(missing)}')

    # How many merged entries have a "substantive" prompt (>40 chars and not a placeholder)?
    substantive = 0
    placeholder = 0
    short = 0
    no_prompt = 0
    for r in merged.values():
        p = r.get('prompt') or ''
        if not p:
            no_prompt += 1
        elif 'Same prompt' in p or 'Same as' in p:
            placeholder += 1
        elif len(p) < 40:
            short += 1
        else:
            substantive += 1
    print(f'  substantive: {substantive}')
    print(f'  placeholder: {placeholder}')
    print(f'  short (<40 chars): {short}')
    print(f'  no prompt: {no_prompt}')

    # Break down missing by batch prefix.
    miss_pref = Counter()
    for u in missing:
        id = url_to_corpus[u]['id']
        miss_pref[id.replace('_', '-').split('-')[0]] += 1
    if miss_pref:
        print('\nMissing by batch prefix:')
        for p, n in miss_pref.most_common(15):
            print(f'  {n:>4}  {p}')

    # Write the artifact.
    # Sort by corpus order for stable diffs.
    corpus_order = {i['url']: idx for idx, i in enumerate(corpus)}
    ordered = {u: merged[u] for u in sorted(merged.keys(), key=lambda x: corpus_order[x])}
    with open(OUTPUT, 'w') as f:
        json.dump(ordered, f, indent=2)
    print(f'\nWrote {OUTPUT} ({os.path.getsize(OUTPUT) / 1024:.0f}KB)')

    # Also write a list of still-missing URLs for the transcript miner.
    miss_file = os.path.join(IDEAS_DIR, '_prompts_missing.json')
    with open(miss_file, 'w') as f:
        json.dump(
            sorted([
                {'id': url_to_corpus[u]['id'], 'url': u, 'model': url_to_corpus[u].get('model')}
                for u in missing
            ], key=lambda x: x['id']),
            f, indent=2,
        )
    print(f'Wrote {miss_file} ({len(missing)} missing)')


if __name__ == '__main__':
    main()
