#!/usr/bin/env python3
"""
Recover full generation prompts for every item in _rate_corpus.json.

Strategy:
1. FAST PATH: load all *_results.json files — these are the clean source of
   truth for the ~180 items from v1/refab/rot/dual/snow tests.
2. SLOW PATH: walk every Claude Code transcript (.jsonl), find bash tool calls
   that sent a "prompt": "..." JSON argument to fal.ai, and match them up to
   corpus URLs via the tool_result that came back (fal.media or catbox.moe URL
   in the response).
3. Write a single `recovered_prompts.json` artifact that maps:
      url -> {prompt, seed, ref, model, source}
   where `source` is either "results_file:<name>" or "transcript:<path>:line<N>"
4. Report coverage stats and list any URLs still missing.

Usage:
  python3 recover_prompts.py                  # run full recovery
  python3 recover_prompts.py --super <file>   # also score against a super URLs file
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

IDEAS_DIR = '/Users/justinbarad/Documents/Claude Code/ideas'
TRANSCRIPT_DIR = '/Users/justinbarad/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas'
OUTPUT = os.path.join(IDEAS_DIR, 'recovered_prompts.json')

RESULT_FILES = [
    'production_batch_v1_results.json',
    'ref_ab_test_results.json',
    'ref_ab_rotated_results.json',
    'dual_ref_test_results.json',
    'snow_goofy_test_results.json',
    'snow_mirror_test_results.json',
    'snow_arm_flip_results.json',
    'mirrored_img2_test_results.json',
]

URL_PAT = re.compile(r'https?://(?:files\.catbox\.moe|v3b?\.fal\.media|v\d?\.fal\.media|fal\.media)/[^\s"\'<>)\]]+')
PROMPT_PAT = re.compile(r'"prompt"\s*:\s*"((?:[^"\\]|\\.)*)"')
SEED_PAT = re.compile(r'"seed"\s*:\s*(\d+)')
IMGURLS_PAT = re.compile(r'"image_urls?"\s*:\s*\[([^\]]*)\]')


def load_corpus():
    with open(os.path.join(IDEAS_DIR, '_rate_corpus.json')) as f:
        return json.load(f)


def fast_path(corpus_urls):
    """Load clean result files. Returns url -> recovery dict."""
    recovered = {}
    for fname in RESULT_FILES:
        p = os.path.join(IDEAS_DIR, fname)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p))
        except Exception as e:
            print(f'  skip {fname}: {e}', file=sys.stderr)
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            url = item.get('url')
            if not url or url in recovered:
                continue
            recovered[url] = {
                'prompt': item.get('prompt'),
                'seed': item.get('seed'),
                'ref': item.get('ref') or item.get('ref_id') or item.get('pair'),
                'sport': item.get('sport'),
                'label': item.get('label'),
                'scene_id': item.get('scene_id') or item.get('scene_idx'),
                'arm': item.get('arm') or item.get('arm_prompt') or item.get('stance'),
                'source': f'results_file:{fname}',
            }
    return recovered


def scan_transcript(path, corpus_urls):
    """
    Walk a .jsonl transcript. For every tool_use (bash) call, extract the
    prompt (if any), then look at the paired tool_result for a fal.media/catbox
    URL. Emit (url, prompt, seed, source) triples.

    We also attempt a fallback: scan the command itself for a URL if the result
    wasn't parseable (some calls inline the URL for chained operations).
    """
    if not os.path.exists(path):
        return {}

    # Build a cheap tool_use_id -> (prompt, seed, image_urls, line) index,
    # then pair with tool_result blocks on the second pass.
    tool_inputs = {}  # tool_use_id -> dict
    results = {}       # url -> recovery dict

    # First pass: tool_use records.
    with open(path, errors='replace') as f:
        for line_no, raw in enumerate(f, 1):
            if 'prompt' not in raw and 'fal' not in raw and 'catbox' not in raw:
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
                ctype = c.get('type')
                if ctype == 'tool_use' and c.get('name') in ('Bash',):
                    tu_id = c.get('id') or ''
                    cmd = ((c.get('input') or {}).get('command') or '')
                    if not cmd:
                        continue
                    # Extract every prompt literal that appears in the command.
                    prompts = PROMPT_PAT.findall(cmd)
                    if not prompts:
                        continue
                    seeds = SEED_PAT.findall(cmd)
                    image_urls = []
                    m = IMGURLS_PAT.search(cmd)
                    if m:
                        image_urls = URL_PAT.findall(m.group(1))
                    # Unescape JSON backslashes in prompts.
                    prompts = [p.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\') for p in prompts]
                    tool_inputs[tu_id] = {
                        'prompts': prompts,
                        'seeds': seeds,
                        'image_urls': image_urls,
                        'cmd_head': cmd[:400],
                        'line': line_no,
                    }

    # Second pass: tool_result records.
    with open(path, errors='replace') as f:
        for line_no, raw in enumerate(f, 1):
            if 'fal.media' not in raw and 'catbox.moe' not in raw:
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
                if c.get('type') != 'tool_result':
                    continue
                tu_id = c.get('tool_use_id') or ''
                inputs = tool_inputs.get(tu_id)
                if not inputs:
                    continue
                # Find URLs in the result.
                result_content = c.get('content', [])
                text_blob = ''
                if isinstance(result_content, list):
                    for rc in result_content:
                        if isinstance(rc, dict):
                            text_blob += rc.get('text', '') or ''
                        elif isinstance(rc, str):
                            text_blob += rc
                elif isinstance(result_content, str):
                    text_blob = result_content
                urls = URL_PAT.findall(text_blob)
                # Also check toolUseResult shape.
                tur = rec.get('toolUseResult', {}) or {}
                if isinstance(tur, dict):
                    for k in ('stdout', 'output'):
                        v = tur.get(k)
                        if isinstance(v, str):
                            urls.extend(URL_PAT.findall(v))
                # Dedupe + keep only URLs we care about.
                urls = list(dict.fromkeys(urls))
                wanted = [u for u in urls if u in corpus_urls]
                if not wanted:
                    continue
                prompts = inputs['prompts']
                # Heuristic: if only one prompt in the cmd, every URL in this
                # result came from that prompt. If multiple, attempt to match
                # 1:1 in order.
                for i, url in enumerate(wanted):
                    if url in results:
                        continue
                    if len(prompts) == 1:
                        p = prompts[0]
                    elif i < len(prompts):
                        p = prompts[i]
                    else:
                        p = prompts[-1]
                    results[url] = {
                        'prompt': p,
                        'seed': inputs['seeds'][min(i, len(inputs['seeds']) - 1)] if inputs['seeds'] else None,
                        'ref': (inputs['image_urls'] or [None])[0],
                        'image_urls': inputs['image_urls'],
                        'source': f'transcript:{os.path.basename(path)}:line{inputs["line"]}',
                    }
    return results


def main():
    corpus = load_corpus()
    print(f'Corpus: {len(corpus)} items')

    corpus_urls = set(i['url'] for i in corpus)

    # Fast path first.
    fast = fast_path(corpus_urls)
    fast_hits = set(fast.keys()) & corpus_urls
    print(f'Fast path (results files): {len(fast_hits)} URLs recovered')

    still_missing = corpus_urls - fast_hits
    print(f'Still missing: {len(still_missing)} URLs — scanning transcripts...')

    # Slow path: walk all transcripts.
    transcripts = []
    for root, _, files in os.walk(TRANSCRIPT_DIR):
        for f in files:
            if f.endswith('.jsonl'):
                transcripts.append(os.path.join(root, f))
    # Sort by size descending so we hit the big ones first.
    transcripts.sort(key=lambda p: -os.path.getsize(p))
    print(f'Transcripts: {len(transcripts)} files, '
          f'{sum(os.path.getsize(p) for p in transcripts) / 1024 / 1024:.0f}MB total')

    recovered = dict(fast)
    for p in transcripts:
        before = len([u for u in recovered if u in corpus_urls])
        hits = scan_transcript(p, corpus_urls & set(corpus_urls - set(recovered.keys())))
        for url, rec in hits.items():
            if url not in recovered:
                recovered[url] = rec
        after = len([u for u in recovered if u in corpus_urls])
        gained = after - before
        size_mb = os.path.getsize(p) / 1024 / 1024
        print(f'  {os.path.basename(p)[:60]:60} {size_mb:6.1f}MB  +{gained} recovered')

    # Final report
    final_hits = set(recovered.keys()) & corpus_urls
    final_missing = corpus_urls - final_hits
    print()
    print(f'FINAL: {len(final_hits)}/{len(corpus_urls)} URLs recovered '
          f'({len(final_hits) * 100 / len(corpus_urls):.0f}%)')
    print(f'Still missing: {len(final_missing)}')

    # Break down the still-missing by id prefix.
    id_by_url = {i['url']: i['id'] for i in corpus}
    missing_prefixes = Counter()
    for u in final_missing:
        id = id_by_url.get(u, '')
        prefix = id.replace('_', '-').split('-')[0]
        missing_prefixes[prefix] += 1
    if missing_prefixes:
        print('\nStill-missing by batch prefix:')
        for p, n in missing_prefixes.most_common(20):
            print(f'  {n:>4}  {p}')

    # Write the artifact.
    out = {u: r for u, r in recovered.items() if u in corpus_urls}
    with open(OUTPUT, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote: {OUTPUT}')
    print(f'Size: {os.path.getsize(OUTPUT) / 1024:.0f}KB')

    # Optionally score a super URLs file.
    if '--super' in sys.argv:
        super_file = sys.argv[sys.argv.index('--super') + 1]
        with open(super_file) as f:
            super_urls = [l.strip() for l in f if l.strip()]
        super_hits = [u for u in super_urls if u in recovered]
        print(f'\nSUPER PILE: {len(super_hits)}/{len(super_urls)} super URLs have recovered prompts')
        missing_supers = [u for u in super_urls if u not in recovered]
        if missing_supers:
            print('Missing super URLs:')
            for u in missing_supers[:10]:
                print(f'  {u}')


if __name__ == '__main__':
    main()
