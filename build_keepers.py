#!/usr/bin/env python3
"""
build_keepers.py — filter cb-prompts.json down to Justin's super+yes keepers.

Reads:
  _keepers_super.txt  (one URL per line — 37 supers from cb-rate.html)
  _keepers_yes.txt    (one URL per line — all yes picks, super is a subset)
  cb-prompts.json     (full corpus with recovered prompts)

Writes:
  cb-keepers.json     (filtered subset, labeled super/yes)

Reports coverage gaps so we can chase any missing prompts.
"""
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SUPER_TXT = os.path.join(ROOT, "_keepers_super.txt")
YES_TXT = os.path.join(ROOT, "_keepers_yes.txt")
PROMPTS = os.path.join(ROOT, "cb-prompts.json")
OUT = os.path.join(ROOT, "cb-keepers.json")


def load_urls(path):
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def is_substantive(p):
    if not p:
        return False
    p = p.strip()
    if len(p) < 40:
        return False
    if p.lower().startswith("same as"):
        return False
    return True


def main():
    super_urls = load_urls(SUPER_TXT)
    yes_urls = load_urls(YES_TXT)

    # Dedup preserving order
    seen = set()
    super_unique = []
    for u in super_urls:
        if u not in seen:
            seen.add(u)
            super_unique.append(u)

    seen_y = set()
    yes_unique = []
    for u in yes_urls:
        if u not in seen_y:
            seen_y.add(u)
            yes_unique.append(u)

    super_set = set(super_unique)

    # Load the full prompts corpus
    with open(PROMPTS, "r", encoding="utf-8") as f:
        prompts_doc = json.load(f)
    items_by_url = prompts_doc.get("items", {})

    # Verify: super ⊆ yes?
    super_not_in_yes = [u for u in super_unique if u not in seen_y]
    if super_not_in_yes:
        print(f"WARN: {len(super_not_in_yes)} super URLs not in yes list (expected subset):")
        for u in super_not_in_yes[:5]:
            print(f"  {u}")

    # Build keepers — one entry per yes URL, labeled with super/yes
    keepers = {}
    missing_in_corpus = {"super": [], "yes": []}
    short_prompts = {"super": [], "yes": []}

    for u in yes_unique:
        label = "super" if u in super_set else "yes"
        entry = items_by_url.get(u)
        if entry is None:
            missing_in_corpus[label].append(u)
            # Still include with a stub so we know it exists
            keepers[u] = {
                "url": u,
                "label": label,
                "prompt": "",
                "_status": "not_in_corpus",
            }
            continue

        # Clone the entry and add label
        keeper = dict(entry)
        keeper["url"] = u
        keeper["label"] = label
        keepers[u] = keeper

        if not is_substantive(keeper.get("prompt", "")):
            short_prompts[label].append(u)

    # Also add any super URLs missing from yes list (shouldn't happen but safety)
    for u in super_not_in_yes:
        entry = items_by_url.get(u)
        keeper = dict(entry) if entry else {"url": u, "prompt": "", "_status": "not_in_corpus"}
        keeper["url"] = u
        keeper["label"] = "super"
        keepers[u] = keeper
        if entry is None:
            missing_in_corpus["super"].append(u)
        elif not is_substantive(keeper.get("prompt", "")):
            short_prompts["super"].append(u)

    # Stats
    super_count = sum(1 for k in keepers.values() if k["label"] == "super")
    yes_count = sum(1 for k in keepers.values() if k["label"] == "yes")
    super_substantive = super_count - len(short_prompts["super"]) - len(missing_in_corpus["super"])
    yes_substantive = yes_count - len(short_prompts["yes"]) - len(missing_in_corpus["yes"])

    out = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "source": "cb-prompts.json filtered by cb-rate.html super/yes piles",
            "total": len(keepers),
            "super_count": super_count,
            "yes_count": yes_count,
            "super_substantive": super_substantive,
            "super_short": len(short_prompts["super"]),
            "super_missing": len(missing_in_corpus["super"]),
            "yes_substantive": yes_substantive,
            "yes_short": len(short_prompts["yes"]),
            "yes_missing": len(missing_in_corpus["yes"]),
            "note": "label='super' is a gold star (swipe up); label='yes' is a like (swipe right). Super pile is a subset of yes pile in cb-rate.html.",
        },
        "items": keepers,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # Report
    print(f"Input: {len(super_unique)} super urls, {len(yes_unique)} yes urls")
    print(f"Output: {len(keepers)} keepers ({super_count} super + {yes_count} yes)")
    print()
    print(f"SUPER PILE coverage:")
    print(f"  substantive: {super_substantive}/{super_count} ({100*super_substantive/max(super_count,1):.0f}%)")
    print(f"  short:       {len(short_prompts['super'])}")
    print(f"  missing:     {len(missing_in_corpus['super'])}")
    print()
    print(f"YES PILE coverage:")
    print(f"  substantive: {yes_substantive}/{yes_count} ({100*yes_substantive/max(yes_count,1):.0f}%)")
    print(f"  short:       {len(short_prompts['yes'])}")
    print(f"  missing:     {len(missing_in_corpus['yes'])}")

    if short_prompts["super"]:
        print()
        print("SUPER with short/missing prompts (gaps to chase):")
        for u in short_prompts["super"]:
            entry = items_by_url.get(u, {})
            print(f"  {entry.get('id','?')}  ({entry.get('source','?')})  {u}")
    if missing_in_corpus["super"]:
        print()
        print("SUPER not in corpus at all:")
        for u in missing_in_corpus["super"]:
            print(f"  {u}")

    if short_prompts["yes"]:
        print()
        print(f"YES with short prompts: {len(short_prompts['yes'])} items")
        for u in short_prompts["yes"][:15]:
            entry = items_by_url.get(u, {})
            print(f"  {entry.get('id','?')}  ({entry.get('source','?')})  {u}")
        if len(short_prompts["yes"]) > 15:
            print(f"  ... and {len(short_prompts['yes']) - 15} more")
    if missing_in_corpus["yes"]:
        print()
        print(f"YES not in corpus: {len(missing_in_corpus['yes'])} items")
        for u in missing_in_corpus["yes"][:10]:
            print(f"  {u}")
        if len(missing_in_corpus["yes"]) > 10:
            print(f"  ... and {len(missing_in_corpus['yes']) - 10} more")

    print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
