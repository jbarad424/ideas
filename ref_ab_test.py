#!/usr/bin/env python3
"""
Reference Photo A/B Test — Apr 8 2026
Tests 12 candidate reference photos from Drive folder 180Tt__ + Ref C baseline
across motorcycle + MTB sports, 2 generations each = 52 images total.

Model: Nano Banana Pro (fal-ai/nano-banana-pro/edit) @ $0.15/image
Budget: ~$7.80
"""
import json
import time
import urllib.request
import urllib.error
import concurrent.futures
import os
import sys

FAL_KEY = "abd109db-5b32-4be9-8e80-55d543ef21b5:25db06d5650ad2d12f2f1d32dcca5099"
ENDPOINT = "https://fal.run/fal-ai/nano-banana-pro/edit"

def drive_url(file_id, w=1600):
    return f"https://lh3.googleusercontent.com/d/{file_id}=w{w}"

# 12 candidates + Ref C baseline
REFS = [
    # Patriot product close-ups
    {"id": "p1", "name": "IMG_0513_Patriot_Product_A", "file_id": "1ASyvicax7lM9gQm45YDUAQjGpPKu53HR", "colorway": "Patriot", "type": "product"},
    {"id": "p2", "name": "IMG_0517_Patriot_Product_B", "file_id": "1a7UDcAAH1i4KDjdHSwdpgQSICduohbNa", "colorway": "Patriot", "type": "product"},
    # Patriot on jacket
    {"id": "p3", "name": "IMG_0546_Patriot_Jacket_A", "file_id": "1BcqhrqdrEgK27Y5cfYA8qfzSkFcHR-L7", "colorway": "Patriot", "type": "jacket"},
    {"id": "p4", "name": "IMG_0550_Patriot_Jacket_B", "file_id": "1TnipKYiHCOBm1wBloxLhFDSzoddxOUXQ", "colorway": "Patriot", "type": "jacket"},
    {"id": "p5", "name": "IMG_0556_Patriot_Jacket_C", "file_id": "1jvilgmnPXDnfG9Mf5kXfPMcXLHV_6GjY", "colorway": "Patriot", "type": "jacket"},
    {"id": "p6", "name": "IMG_0560_Patriot_Jacket_D", "file_id": "13O__D25OOqcvZ4XGCwifgUZsac67bMDz", "colorway": "Patriot", "type": "jacket"},
    # Hunter product close-ups
    {"id": "h1", "name": "IMG_0525_Hunter_Product_A", "file_id": "1PL5wh4AifIvoPNPcaUEX04iLp-z5xIoR", "colorway": "Hunter", "type": "product"},
    {"id": "h2", "name": "IMG_0529_Hunter_Product_B", "file_id": "1fIbI_i90IURqMSPUIS4c-jZB4ANbXYAk", "colorway": "Hunter", "type": "product"},
    # Hunter on jacket
    {"id": "h3", "name": "IMG_0534_Hunter_Jacket_A", "file_id": "1KeaKD9RwJopY0c_dHTgUiiV-a-Wyh327", "colorway": "Hunter", "type": "jacket"},
    {"id": "h4", "name": "IMG_0541_Hunter_Jacket_B", "file_id": "18A5vhpJYrzCTVkJJF4K2-ctv55o3lzh9", "colorway": "Hunter", "type": "jacket"},
    {"id": "h5", "name": "IMG_0542_Hunter_Jacket_C", "file_id": "1gQT2_r9UFOVCu3fHk7SmSvzmryfmRYFr", "colorway": "Hunter", "type": "jacket"},
    {"id": "h6", "name": "IMG_0566_Hunter_Product_C", "file_id": "10yVW3qgOSMd2AGu-40Lo2LPBEt_vRdKA", "colorway": "Hunter", "type": "product"},
    # Baseline: current production reference
    {"id": "refc", "name": "RefC_JMike_Dual_BASELINE", "file_id": "1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7", "colorway": "Hunter (2 people)", "type": "baseline"},
]

# Two scene prompts per sport with different seeds for variance
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

def submit(ref, sport, scene_idx):
    scene = SCENES[sport][scene_idx]
    payload = {
        "image_urls": [drive_url(ref["file_id"])],
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
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
            url = data.get("images", [{}])[0].get("url", "")
            print(f"OK  {label}: {url}")
            return {"label": label, "ref": ref, "sport": sport, "scene_idx": scene_idx, "url": url, "seed": scene["seed"], "prompt": scene["prompt"]}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERR {label} HTTP {e.code}: {body[:200]}")
        return {"label": label, "ref": ref, "sport": sport, "scene_idx": scene_idx, "error": f"{e.code} {body[:200]}"}
    except Exception as e:
        print(f"ERR {label}: {e}")
        return {"label": label, "ref": ref, "sport": sport, "scene_idx": scene_idx, "error": str(e)}

def main():
    jobs = []
    for ref in REFS:
        for sport in ["moto", "mtb"]:
            for scene_idx in [0, 1]:
                jobs.append((ref, sport, scene_idx))
    print(f"Total jobs: {len(jobs)} (~${len(jobs)*0.15:.2f})")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(submit, *j) for j in jobs]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    with open("ref_ab_test_results.json", "w") as fp:
        json.dump(results, fp, indent=2)
    ok = sum(1 for r in results if "url" in r)
    print(f"\nDone: {ok}/{len(results)} succeeded")

if __name__ == "__main__":
    main()
