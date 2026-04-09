#!/usr/bin/env python3
"""
Walk every Claude Code transcript and extract every (url, prompt, seed, ref)
tuple produced by a bash tool call that hit fal.ai.

Writes mined_prompts.json mapping url -> {prompt, seed, image_urls, cmd_excerpt, source}.

This is the slow-path fallback for any URL not covered by results files or
cb-review.html.
"""
import json
import os
import re
import sys
from collections import Counter

TRANSCRIPT_DIR = '/Users/justinbarad/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas'
OUTPUT = '/Users/justinbarad/Documents/Claude Code/ideas/mined_prompts.json'

URL_PAT = re.compile(r'https?://(?:files\.catbox\.moe|v\d?b?\.fal\.media|fal\.media)/[^\s"\'<>)\],}]+')
# Match every "prompt": "..." occurrence in a bash command or its stdout
PROMPT_PAT = re.compile(r'"prompt"\s*:\s*"((?:[^"\\]|\\.)*)"')
SEED_PAT = re.compile(r'"seed"\s*:\s*(\d+)')
IMGURLS_PAT = re.compile(r'"image_urls?"\s*:\s*\[([^\]]*)\]')
REF_URL_PAT = re.compile(r'https?://[^\s"\'<>)\],}]+\.(?:jpg|jpeg|png|webp)')


def unescape(s):
    return s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\').replace("\\'", "'")


def extract_from_cmd(cmd):
    """Return list of prompts and list of seeds and ref urls from a bash cmd."""
    prompts = [unescape(p) for p in PROMPT_PAT.findall(cmd)]
    seeds = SEED_PAT.findall(cmd)
    image_urls = []
    m = IMGURLS_PAT.search(cmd)
    if m:
        image_urls = REF_URL_PAT.findall(m.group(1))
    return prompts, seeds, image_urls


def extract_urls_from_result(result):
    """Extract fal.media / catbox URLs from a tool_result content blob."""
    text = ''
    if isinstance(result, str):
        text = result
    elif isinstance(result, list):
        for rc in result:
            if isinstance(rc, dict):
                text += rc.get('text', '') or ''
            elif isinstance(rc, str):
                text += rc
    return URL_PAT.findall(text)


def scan_transcript(path):
    """Walk a transcript, return url -> prompt info dict."""
    # Two-pass: first collect tool_use inputs keyed by id, then pair with results.
    tool_inputs = {}  # tu_id -> {prompts, seeds, image_urls, cmd_excerpt, line}

    with open(path, errors='replace') as f:
        for line_no, raw in enumerate(f, 1):
            if '"tool_use"' not in raw:
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
                if c.get('type') != 'tool_use':
                    continue
                if c.get('name') != 'Bash':
                    continue
                tu_id = c.get('id')
                if not tu_id:
                    continue
                cmd = ((c.get('input') or {}).get('command') or '')
                if not cmd or '"prompt"' not in cmd:
                    continue
                prompts, seeds, image_urls = extract_from_cmd(cmd)
                if not prompts:
                    continue
                tool_inputs[tu_id] = {
                    'prompts': prompts,
                    'seeds': seeds,
                    'image_urls': image_urls,
                    'cmd_excerpt': cmd[:300],
                    'line': line_no,
                }

    recovered = {}
    with open(path, errors='replace') as f:
        for line_no, raw in enumerate(f, 1):
            if 'tool_use_id' not in raw:
                continue
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
                tu_id = c.get('tool_use_id')
                if not tu_id or tu_id not in tool_inputs:
                    continue
                urls = extract_urls_from_result(c.get('content', ''))
                # Also check toolUseResult outer field.
                tur = rec.get('toolUseResult', {}) or {}
                if isinstance(tur, dict):
                    for k in ('stdout', 'output', 'content'):
                        v = tur.get(k)
                        if isinstance(v, str):
                            urls.extend(URL_PAT.findall(v))
                # Dedupe, keep order.
                urls = list(dict.fromkeys(urls))
                if not urls:
                    continue
                inputs = tool_inputs[tu_id]
                prompts = inputs['prompts']
                seeds = inputs['seeds']
                for i, url in enumerate(urls):
                    if url in recovered:
                        continue
                    # If there are multiple prompts in the cmd, match 1:1 in order.
                    if len(prompts) == 1:
                        p = prompts[0]
                    elif i < len(prompts):
                        p = prompts[i]
                    else:
                        p = prompts[-1]
                    seed = None
                    if seeds:
                        if i < len(seeds):
                            seed = seeds[i]
                        else:
                            seed = seeds[-1]
                    recovered[url] = {
                        'prompt': p,
                        'seed': seed,
                        'image_urls': inputs['image_urls'],
                        'cmd_excerpt': inputs['cmd_excerpt'],
                        'source': f'transcript:{os.path.basename(path)}:line{inputs["line"]}',
                    }
    return recovered


def main():
    paths = []
    for root, _, files in os.walk(TRANSCRIPT_DIR):
        for f in files:
            if f.endswith('.jsonl'):
                paths.append(os.path.join(root, f))
    paths.sort(key=lambda p: -os.path.getsize(p))

    print(f'Transcripts: {len(paths)}, '
          f'{sum(os.path.getsize(p) for p in paths) / 1024 / 1024:.0f}MB total')
    all_recovered = {}
    for p in paths:
        size_mb = os.path.getsize(p) / 1024 / 1024
        if size_mb < 0.05:
            continue
        before = len(all_recovered)
        hits = scan_transcript(p)
        for url, rec in hits.items():
            if url not in all_recovered:
                all_recovered[url] = rec
        gained = len(all_recovered) - before
        print(f'  {os.path.basename(p)[:50]:50} {size_mb:6.1f}MB  '
              f'+{gained:4d} gained  (total {len(all_recovered)})')

    print(f'\nTotal mined URLs: {len(all_recovered)}')

    # Join against corpus to see how much of the corpus is now covered.
    corpus = json.load(open('/Users/justinbarad/Documents/Claude Code/ideas/_rate_corpus.json'))
    corpus_urls = {i['url'] for i in corpus}
    covered = [u for u in corpus_urls if u in all_recovered]
    print(f'Corpus hits: {len(covered)}/{len(corpus_urls)} '
          f'({len(covered) * 100 / len(corpus_urls):.0f}%)')

    with open(OUTPUT, 'w') as f:
        json.dump(all_recovered, f, indent=2)
    print(f'Wrote {OUTPUT} ({os.path.getsize(OUTPUT) / 1024:.0f}KB)')


if __name__ == '__main__':
    main()
