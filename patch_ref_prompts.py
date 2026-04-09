#!/usr/bin/env python3
"""
patch_ref_prompts.py — fill in the 5 short REF TEST items in cb-prompts.json.

The `ref-A*`, `ref-B*`, `ref-C*`, `ref-D*` batch (FLUX 2 Pro) tested 4 different
reference photos with the SAME prompt to isolate the reference-photo variable.
cb-review.html labels A1/B1/C1/D1 as "Motorcycle coastal + exact layout spec"
and marks all siblings as "Same".

The actual prompt was recovered from the transcript for the `t2nesw.jpg`
(Hunter Arm Outside) call in 8b38428e-*.jsonl. Same prompt applies to all
REF TEST A/B/C/D entries per the cb-review.html labels.
"""
import json
import os
from datetime import datetime, timezone

PROMPTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cb-prompts.json")

# Canonical prompt recovered from transcript (seed 42 call with t2nesw.jpg ref)
REF_TEST_PROMPT = (
    "Motorcycle rider cruising on a coastal highway, wearing a leather jacket, "
    "the product from image 1 is strapped flush against the riders lower forearm "
    "over the jacket sleeve. The plus/volume-up button is closest to the wrist, "
    "minus closest to the elbow, play/pause in the center. LED indicator and CB "
    "logo face outward. Ocean and cliffs, warm spring sunlight, editorial "
    "motorcycle photography"
)

# Reference photo per sub-batch (from cb-review.html labels and ref_ab_test.py REFS list)
REF_PHOTOS = {
    "A": {"name": "Hunter Arm Outside", "role": "third-person arm photo", "catbox": "https://files.catbox.moe/t2nesw.jpg"},
    "B": {"name": "Motorcycle Close Up", "role": "real moto forearm photo", "catbox": None},
    "C": {"name": "J&Mike Dual", "role": "two-person dual CB2 photo", "catbox": None},
    "D": {"name": "Original Product Front", "role": "standing product control", "catbox": None},
}


def main():
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        doc = json.load(f)
    items = doc["items"]

    # Find all ref-A*/B*/C*/D* items and patch prompt + source
    patched = 0
    for url, entry in items.items():
        eid = entry.get("id", "")
        # Matches ref-A1, ref-A2, ..., ref-D5
        if not (eid.startswith("ref-") and len(eid) == 6 and eid[4] in "ABCD" and eid[5].isdigit()):
            continue
        current_prompt = entry.get("prompt", "") or ""
        # Only patch if current is short/stub
        if len(current_prompt.strip()) >= 40 and not current_prompt.lower().startswith("motorcycle coastal"):
            continue
        letter = eid[4]
        ref_meta = REF_PHOTOS[letter]
        # Preserve the pre-existing prompt for audit
        entry["prompt_original"] = current_prompt
        entry["prompt"] = REF_TEST_PROMPT
        entry["source"] = "transcript_manual:ref_test_canonical"
        entry["ref"] = {
            "name": ref_meta["name"],
            "role": ref_meta["role"],
            "catbox_url": ref_meta["catbox"],
        }
        entry["model"] = "flux2-pro @image"
        entry["sport"] = "moto"  # all REF TEST batches are motorcycle coastal
        entry["experiment"] = "REF TEST — FLUX 2 Pro reference photo A/B/C/D comparison"
        patched += 1

    # Update meta
    meta = doc.get("meta", {})
    substantive = sum(1 for e in items.values() if e.get("prompt") and len(e["prompt"].strip()) >= 40)
    meta["substantive_count"] = substantive
    meta["short_count"] = len(items) - substantive
    meta["patched_ref_canonical"] = patched
    meta["last_patched"] = datetime.now(timezone.utc).isoformat()
    doc["meta"] = meta

    with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"Patched {patched} REF TEST items with canonical prompt.")
    print(f"Substantive now: {substantive}/{len(items)} ({100*substantive/len(items):.0f}%)")


if __name__ == "__main__":
    main()
