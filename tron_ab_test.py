#!/usr/bin/env python3
"""
Tron Reference A/B Test — 2026-04-09

Tests the 20 Tron reference photos Jordan shot on 2026-04-09 (Drive folder
1DfR8YHW9L2BLb_w-JZhKEdj_Vfo1D4es, IMG_7184–IMG_7203) against the exact
same prompts + seeds used in the Hunter/Patriot rotation A/B
(rotated_ab_test.py). Pure A/B isolation — only variable is the reference
photo. Refs with high keeper rate become t01..tN in CLAUDE.md ref table.

Methodology note: Jordan shot multi-orientation variants this time (PLUS-up
AND PLUS-down of same scenes), so the sips -r 180 post-processing step from
rotated_ab_test.py is SKIPPED. Drive URLs are submitted directly to NB Pro
via the same lh3.googleusercontent.com pattern used for Ref C in production.

Anti-pattern avoidance: Justin rates the GENERATED images (via
tron-ab-review.html), not the raw reference photos. Pre-triage burns user
attention on decisions the model should make for us via keeper rate signal.

Cost: 20 refs × 2 sports × 2 scenes = 80 jobs @ $0.15 = $12.00
Expected wall time: ~5-10 minutes at 8 concurrent workers.
"""
import json
import os
import urllib.request
import urllib.error
import concurrent.futures
import time

FAL_KEY = "abd109db-5b32-4be9-8e80-55d543ef21b5:25db06d5650ad2d12f2f1d32dcca5099"
ENDPOINT = "https://fal.run/fal-ai/nano-banana-pro/edit"

# 20 Tron refs from Drive folder 1DfR8YHW9L2BLb_w-JZhKEdj_Vfo1D4es
# Downloaded to tron-refs/originals/ on 2026-04-09.
TRON_REFS = [
    {"id": "t01", "name": "IMG_7184", "file_id": "1iC67fOEGyuv6jJn-0uXFHnVmevXRtjGk"},
    {"id": "t02", "name": "IMG_7185", "file_id": "1jxVP6yb1RGSdQj551w9tc_GsZCF5fdy0"},
    {"id": "t03", "name": "IMG_7186", "file_id": "1EGepZNq9qZ8QipBmR3XQCIWsh7kFbR3a"},
    {"id": "t04", "name": "IMG_7187", "file_id": "15-9JyB3VQvnItMar27tvKvNrjJ1ysW-d"},
    {"id": "t05", "name": "IMG_7188", "file_id": "14wFf-JNdzJ44DnaEcHZtT-5MiFvD6tWE"},
    {"id": "t06", "name": "IMG_7189", "file_id": "1HpSg9A5Cr89zQclZ_UqlJsThBYwePXlb"},
    {"id": "t07", "name": "IMG_7190", "file_id": "1J7XBg4bVToxeNLlESKTVQaPkf1KMqzuv"},
    {"id": "t08", "name": "IMG_7191", "file_id": "1F29NpOOcZceKfmTCsc3kXvXjrMwtvZ_w"},
    {"id": "t09", "name": "IMG_7192", "file_id": "15juvsZ5uULR6ChLP5zAVhiN_mMxhrQWZ"},
    {"id": "t10", "name": "IMG_7193", "file_id": "1anfPl4uJ3dHpAkGfHWgkAE6pjkUBY83w"},
    {"id": "t11", "name": "IMG_7194", "file_id": "1FlOTSnp1w0hcwve3masxCN7ayW6epCQ0"},
    {"id": "t12", "name": "IMG_7195", "file_id": "1f4aZySxxytuXAN5lXIlgFT9p_bg645RJ"},
    {"id": "t13", "name": "IMG_7196", "file_id": "1LfFB3ec_BVYfmVKELIY1N-NE8nWJDLlb"},
    {"id": "t14", "name": "IMG_7197", "file_id": "1DnHwYQBBfL9zCbZsjILudozCYPJ6oz1_"},
    {"id": "t15", "name": "IMG_7198", "file_id": "141kPI_mPO7Ry7eJ1G5Uay-rEdjMKrBqu"},
    {"id": "t16", "name": "IMG_7199", "file_id": "1hyuDNmldEa6PjjvL2n6PkIYgVGmusNdD"},
    {"id": "t17", "name": "IMG_7200", "file_id": "1VTOu2axfFhFSCY69ha9D3wRjHp-u9sJI"},
    {"id": "t18", "name": "IMG_7201", "file_id": "15qQAInr--xwNn5ZG06HNMPZH4gzf3nSm"},
    {"id": "t19", "name": "IMG_7202", "file_id": "1dHAc8wIETg0TSmCLrpt5EiEZ6sFo67iW"},
    {"id": "t20", "name": "IMG_7203", "file_id": "1uCUnWwq4RpO6uDpb5EwkMrpxa6jE9ljW"},
]

# IDENTICAL scenes + seeds to rotated_ab_test.py — pure A/B isolation
# with the Hunter/Patriot baseline. Do not modify.
SCENES = {
    "moto": [
        {
            "seed": 9101,
            "prompt": ("Motorcycle rider cruising coastal highway at golden hour, wearing leather riding "
                       "jacket, thick leather riding gloves, and full-face helmet, the wearable remote from "
                       "image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the "
                       "jacket sleeve, positioned halfway between wrist and elbow, PLUS button closest to wrist, "
                       "LED window closest to wrist, five round tactile buttons, both arms relaxed on handlebars, "
                       "waist-up, Shot on Sony A7R IV 85mm f/2.0, warm natural light, film grain")
        },
        {
            "seed": 9102,
            "prompt": ("Adventure motorcycle rider on desert canyon road, wearing textile riding jacket, "
                       "leather riding gloves, and full-face helmet, the wearable remote from image 1 with its "
                       "velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, "
                       "positioned halfway between wrist and elbow, PLUS button closest to wrist, five round "
                       "tactile buttons, waist-up, Shot on Nikon Z9 70mm f/2.8, harsh desert sun, documentary photography")
        }
    ],
    "mtb": [
        {
            "seed": 9201,
            "prompt": ("Mountain biker descending a rocky forest trail, wearing full-face downhill helmet, "
                       "protective gloves, and jersey with armor, the wearable remote from image 1 with its "
                       "velcro strap wrapped fully around the LEFT lower forearm OVER the jersey sleeve, "
                       "positioned halfway between wrist and elbow, PLUS button closest to wrist, five round "
                       "tactile buttons, both hands on handlebars, waist-up, Shot on Sony A7R IV 85mm f/2.0, "
                       "dappled forest light, film grain")
        },
        {
            "seed": 9202,
            "prompt": ("Mountain biker on alpine ridge singletrack, wearing full-face downhill helmet, "
                       "protective gloves, and long-sleeve jersey, the wearable remote from image 1 with its "
                       "velcro strap wrapped fully around the LEFT lower forearm OVER the jersey sleeve, "
                       "positioned halfway between wrist and elbow, PLUS button closest to wrist, five round "
                       "tactile buttons, waist-up, Shot on Nikon Z9 70mm f/2.8, mountain landscape, documentary photography")
        }
    ]
}


def drive_url(file_id: str) -> str:
    """Public Drive CDN URL. Same pattern as Ref C in CLAUDE.md."""
    return f"https://lh3.googleusercontent.com/d/{file_id}=w1600"


def submit(ref: dict, sport: str, scene_idx: int) -> dict:
    scene = SCENES[sport][scene_idx]
    ref_url = drive_url(ref["file_id"])
    payload = {
        "image_urls": [ref_url],
        "prompt": scene["prompt"],
        "seed": scene["seed"],
        "num_images": 1,
        "output_format": "jpeg",
        "guidance_scale": 4.0,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    label = f"{ref['id']}_{sport}_s{scene_idx}"
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=420) as resp:
            data = json.loads(resp.read())
            url = data.get("images", [{}])[0].get("url", "")
            dt = time.time() - t0
            print(f"OK  {label} ({dt:.1f}s): {url}", flush=True)
            return {
                "label": label,
                "ref_id": ref["id"],
                "ref_name": ref["name"],
                "ref_url": ref_url,
                "sport": sport,
                "scene_idx": scene_idx,
                "seed": scene["seed"],
                "url": url,
                "prompt": scene["prompt"],
                "duration_s": round(dt, 1),
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERR {label} HTTP {e.code}: {body[:200]}", flush=True)
        return {"label": label, "ref_id": ref["id"], "ref_name": ref["name"],
                "sport": sport, "scene_idx": scene_idx, "error": f"{e.code} {body[:200]}"}
    except Exception as e:
        print(f"ERR {label}: {e}", flush=True)
        return {"label": label, "ref_id": ref["id"], "ref_name": ref["name"],
                "sport": sport, "scene_idx": scene_idx, "error": str(e)}


def main():
    jobs = [(ref, sport, idx) for ref in TRON_REFS for sport in ["moto", "mtb"] for idx in [0, 1]]
    print(f"=== Tron ref A/B: {len(jobs)} jobs (~${len(jobs) * 0.15:.2f}) ===", flush=True)
    print(f"20 refs × 2 sports × 2 scenes @ NB Pro, seeds 9101/9102/9201/9202", flush=True)

    t_start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(submit, *j) for j in jobs]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    results.sort(key=lambda r: (r["ref_id"], r["sport"], r.get("scene_idx", 0)))

    out_path = "tron_ab_results.json"
    with open(out_path, "w") as fp:
        json.dump({
            "meta": {
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "jobs": len(jobs),
                "cost_usd": round(len(jobs) * 0.15, 2),
                "wall_time_s": round(time.time() - t_start, 1),
                "model": "fal-ai/nano-banana-pro/edit",
                "refs": TRON_REFS,
                "scenes": SCENES,
            },
            "results": results,
        }, fp, indent=2)

    ok = sum(1 for r in results if "url" in r)
    err = len(results) - ok
    dt = time.time() - t_start
    print(f"\n=== Done: {ok}/{len(results)} succeeded, {err} errors in {dt:.1f}s ===", flush=True)
    print(f"Results saved to {out_path}", flush=True)
    if err:
        print("Failed jobs:", [r["label"] for r in results if "error" in r], flush=True)


if __name__ == "__main__":
    main()
