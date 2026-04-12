#!/usr/bin/env python3
"""
CB2 Production Batch v2 — Multi-Sport × Multi-Ref × Multi-Model
Generates ~112 images across all sports, colorways, refs, and models.
Fires through the CF Worker proxy, polls for completion, saves results.
"""

import json, time, random, sys, subprocess

WORKER = "https://cb2-proxy.chubbybuttons.workers.dev"
PASSWORD = "cbcreative"

# === REFS ===
REFS = {
    "h3": {"colorway": "Hunter", "type": "jacket", "url": "https://jbarad424.github.io/ideas/rotated-refs/h3.jpg"},
    "h5": {"colorway": "Hunter", "type": "jacket", "url": "https://jbarad424.github.io/ideas/rotated-refs/h5.jpg"},
    "p4": {"colorway": "Patriot", "type": "jacket", "url": "https://jbarad424.github.io/ideas/rotated-refs/p4.jpg"},
    "p6": {"colorway": "Patriot", "type": "jacket", "url": "https://jbarad424.github.io/ideas/rotated-refs/p6.jpg"},
    "t01": {"colorway": "Tron", "type": "jacket", "url": "https://jbarad424.github.io/ideas/ref-library/tron-raw/t01.jpeg"},
    "t03": {"colorway": "Tron", "type": "jacket", "url": "https://jbarad424.github.io/ideas/ref-library/tron-raw/t03.jpeg"},
    "t18": {"colorway": "Tron", "type": "product", "url": "https://jbarad424.github.io/ideas/ref-library/tron-raw/t18.jpeg"},
}

# Product shots for dual-ref (image 2)
PRODUCT_SHOTS = {
    "Hunter": "https://jbarad424.github.io/ideas/rotated-refs/h6.jpg",
    "Patriot": "https://jbarad424.github.io/ideas/rotated-refs/h6.jpg",  # fallback to Hunter
    "Tron": "https://jbarad424.github.io/ideas/ref-library/tron-raw/t18.jpeg",
}

# === GEAR ===
GEAR = {
    "moto": "full-face helmet, leather riding jacket with armor, thick leather riding gloves",
    "ski": "ski helmet, goggles, ski gloves, ski jacket",
    "snow": "snowboard helmet, gloves, snowboard jacket",
    "mtb": "full-face DH helmet, gloves, long-sleeve jersey with armor",
    "sled": "full-face helmet, snowmobile gloves, snowmobile suit",
}

SUBJECTS = {
    "moto": "motorcycle rider",
    "ski": "skier",
    "snow": "snowboarder",
    "mtb": "mountain biker",
    "sled": "snowmobile rider",
}

# === CB2 BLOCK (LEFT arm default) ===
CB2_BLOCK = "the compact wearable remote from image 1 (108mm long, 39mm wide) with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, LED window closest to WRIST, PLUS button closest to wrist, MINUS button closest to elbow, five round tactile buttons in a vertical row reading from wrist to elbow: PLUS (+), FAST-FORWARD (two right triangles), PLAY/PAUSE (three bars with triangle), REWIND (two left triangles), MINUS (\u2212), device parallel to the forearm not perpendicular"

# === SCENES (2 per sport for variety) ===
SCENES = {
    "moto": [
        "Motorcycle rider cruising Pacific Coast Highway at golden hour, ocean cliffs in background, warm light on leather jacket",
        "Motorcycle rider on desert highway through red rock canyon, adventure bike, harsh midday sun",
    ],
    "ski": [
        "Skier carving through a powder bowl under bluebird sky, snow spray catching sunlight",
        "Skier descending a steep mountain slope through forest glade, dappled sunlight filtering through snow-covered trees",
    ],
    "snow": [
        "Snowboarder on a powder day in deep snow, regular stance, mountain backdrop, soft diffused light",
        "Snowboarder making a deep powder turn with spray, misty forest trail, ethereal morning light",
    ],
    "mtb": [
        "Mountain biker descending steep alpine singletrack, wildflowers on slope edges, dramatic valley below",
        "Mountain biker on Pacific Northwest rainforest trail, technical roots and rocks, canopy light",
    ],
    "sled": [
        "Snowmobile rider crossing a frozen alpine meadow, mountains reflected in ice, powder spray behind",
        "Snowmobile rider blasting through backcountry powder, snow-laden trees, bright winter sun",
    ],
}

CAMERAS = [
    "Shot on Sony A7R IV 85mm f/2.0, editorial photography, film grain",
    "Shot on Nikon Z9 70mm f/2.8, documentary photography, natural light",
    "Shot on Sony A7IV 85mm f/1.8, golden hour backlight, warm tones, film grain",
    "Shot on Leica Q3 28mm, harsh natural sun, deep shadows, documentary",
]

# === BATCH MATRIX ===
BATCH = [
    # moto — all refs + GPT for Hunter/Tron
    ("moto", "h3", "fal-ai/nano-banana-pro/edit"),
    ("moto", "h5", "fal-ai/nano-banana-pro/edit"),
    ("moto", "p4", "fal-ai/nano-banana-pro/edit"),
    ("moto", "p6", "fal-ai/nano-banana-pro/edit"),
    ("moto", "t01", "fal-ai/nano-banana-pro/edit"),
    ("moto", "t03", "fal-ai/nano-banana-pro/edit"),
    ("moto", "h3", "fal-ai/gpt-image-1.5/edit"),
    ("moto", "t18", "fal-ai/gpt-image-1.5/edit"),
    # ski — NB2 default + NB Pro for select refs
    ("ski", "h3", "fal-ai/nano-banana-2/edit"),
    ("ski", "p4", "fal-ai/nano-banana-2/edit"),
    ("ski", "t01", "fal-ai/nano-banana-2/edit"),
    ("ski", "t03", "fal-ai/nano-banana-2/edit"),
    ("ski", "h5", "fal-ai/nano-banana-pro/edit"),
    ("ski", "t18", "fal-ai/nano-banana-pro/edit"),
    # snow — NB Pro + NB2 for Hunter
    ("snow", "h3", "fal-ai/nano-banana-pro/edit"),
    ("snow", "p6", "fal-ai/nano-banana-pro/edit"),
    ("snow", "t01", "fal-ai/nano-banana-pro/edit"),
    ("snow", "t03", "fal-ai/nano-banana-pro/edit"),
    ("snow", "h3", "fal-ai/nano-banana-2/edit"),
    # mtb — NB Pro + GPT for Hunter
    ("mtb", "h3", "fal-ai/nano-banana-pro/edit"),
    ("mtb", "h5", "fal-ai/nano-banana-pro/edit"),
    ("mtb", "p4", "fal-ai/nano-banana-pro/edit"),
    ("mtb", "t01", "fal-ai/nano-banana-pro/edit"),
    ("mtb", "t03", "fal-ai/nano-banana-pro/edit"),
    ("mtb", "h3", "fal-ai/gpt-image-1.5/edit"),
    # sled — NB Pro across colorways
    ("sled", "h3", "fal-ai/nano-banana-pro/edit"),
    ("sled", "t01", "fal-ai/nano-banana-pro/edit"),
    ("sled", "p4", "fal-ai/nano-banana-pro/edit"),
]

MODEL_LABELS = {
    "fal-ai/gpt-image-1.5/edit": "GPT Image 1.5",
    "fal-ai/nano-banana-pro/edit": "Nano Banana Pro",
    "fal-ai/nano-banana-2/edit": "Nano Banana 2",
    "fal-ai/flux-2-flex/edit": "FLUX 2 Flex",
}


def proxy_call(target, body):
    """Call the CF Worker proxy via curl (avoids Python urlopen 403 issues)."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST", WORKER,
            "-H", "Content-Type: application/json",
            "-H", f"X-Team-Password: {PASSWORD}",
            "-H", f"X-Proxy-Target: {target}",
            "-d", json.dumps(body),
        ], capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout) if result.stdout.strip() else {"error": "empty response"}
    except Exception as e:
        return {"error": str(e)}


def build_prompt(sport, scene_idx, camera_idx):
    """Assemble a full production prompt."""
    scene = SCENES[sport][scene_idx % len(SCENES[sport])]
    subject = SUBJECTS[sport]
    gear = GEAR[sport]
    camera = CAMERAS[camera_idx % len(CAMERAS)]
    return f"{scene}. {subject} wearing {gear}, {CB2_BLOCK}, waist-up, {camera}"


def build_payload(endpoint, ref_url, product_url, prompt, seed):
    """Build a fal.ai payload."""
    if "gpt-image" in endpoint:
        return {
            "image_urls": [ref_url, product_url],
            "prompt": prompt,
            "size": "1024x1536",
            "quality": "high",
            "input_fidelity": "high",
        }
    body = {
        "image_urls": [ref_url, product_url],
        "prompt": prompt,
        "seed": seed,
        "num_images": 1,
        "output_format": "jpeg",
        "safety_tolerance": 5,
    }
    if "flux-2-flex" in endpoint:
        body["guidance_scale"] = 7.0
        body["num_inference_steps"] = 28
    return body


def submit_job(endpoint, payload):
    """Submit via fal-submit and return request_id + status URLs."""
    result = proxy_call("fal-submit", {"endpoint": endpoint, "input": payload})
    if not result.get("request_id"):
        return None, None, None, result
    rid = result["request_id"]
    base = endpoint.replace("/" + endpoint.split("/")[-1], "")
    status_url = f"https://queue.fal.run/{base}/requests/{rid}/status"
    result_url = f"https://queue.fal.run/{base}/requests/{rid}"
    return rid, status_url, result_url, None


def poll_job(status_url, result_url, timeout=300):
    """Poll until COMPLETED, FAILED, or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(8)
        s = proxy_call("fal-get", {"url": status_url})
        status = s.get("status", "UNKNOWN")
        t = s.get("metrics", {}).get("inference_time", 0)
        if status == "COMPLETED":
            if t and t < 5:  # Instant = content policy rejection
                res = proxy_call("fal-get", {"url": result_url})
                if res.get("detail"):
                    return "REJECTED", None
            res = proxy_call("fal-get", {"url": result_url})
            vid_url = res.get("video", {}).get("url")
            img_url = None
            # For image models, result is in different places
            if isinstance(res, dict):
                if res.get("images"):
                    img_url = res["images"][0].get("url")
                elif res.get("output"):
                    if isinstance(res["output"], list):
                        img_url = res["output"][0].get("url") if res["output"] else None
                    elif isinstance(res["output"], dict):
                        img_url = res["output"].get("url")
                elif res.get("image"):
                    img_url = res["image"].get("url")
                elif res.get("url"):
                    img_url = res["url"]
            return "COMPLETED", img_url
        elif status in ("FAILED", "ERROR"):
            return "FAILED", None
    return "TIMEOUT", None


def main():
    results = []
    total = len(BATCH) * 2  # 2 seeds per combo
    print(f"=== CB2 Production Batch v2 ===")
    print(f"Total jobs: {total}")
    print(f"Estimated cost: ~${sum(0.15 if 'gpt' in e or 'pro' in e else 0.08 for _, _, e in BATCH) * 2:.2f}")
    print()

    idx = 0
    for sport, ref_id, endpoint in BATCH:
        ref = REFS[ref_id]
        ref_url = ref["url"]
        product_url = PRODUCT_SHOTS[ref["colorway"]]

        for seed_i in range(2):
            idx += 1
            seed = random.randint(10000, 99999)
            scene_idx = seed_i  # alternate scenes
            camera_idx = idx  # cycle cameras
            prompt = build_prompt(sport, scene_idx, camera_idx)

            job_id = f"batch2-{sport}-{ref_id}-{endpoint.split('/')[-2]}-s{seed}"
            model_label = MODEL_LABELS.get(endpoint, endpoint)

            print(f"[{idx}/{total}] {sport} | {ref_id} ({ref['colorway']}) | {model_label} | seed {seed}")

            payload = build_payload(endpoint, ref_url, product_url, prompt, seed)
            rid, status_url, result_url, err = submit_job(endpoint, payload)

            if err:
                print(f"  SUBMIT ERROR: {json.dumps(err)[:100]}")
                results.append({
                    "id": job_id, "sport": sport, "ref": ref_id, "colorway": ref["colorway"],
                    "model": model_label, "endpoint": endpoint, "seed": seed,
                    "prompt": prompt, "status": "SUBMIT_ERROR", "url": None,
                    "error": json.dumps(err)[:200],
                })
                continue

            print(f"  Submitted: {rid[:18]}... polling...")

            status, img_url = poll_job(status_url, result_url)
            print(f"  Result: {status} {'-> ' + img_url[:60] if img_url else ''}")

            results.append({
                "id": job_id, "sport": sport, "ref": ref_id, "colorway": ref["colorway"],
                "model": model_label, "endpoint": endpoint, "seed": seed,
                "prompt": prompt, "status": status, "url": img_url,
                "request_id": rid,
            })

            # Save incrementally
            with open("batch_v2_results.json", "w") as f:
                json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "results": results}, f, indent=2)

    # Final summary
    completed = sum(1 for r in results if r["status"] == "COMPLETED" and r["url"])
    failed = sum(1 for r in results if r["status"] in ("FAILED", "SUBMIT_ERROR", "REJECTED"))
    timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
    print(f"\n=== DONE ===")
    print(f"Completed: {completed}/{total}")
    print(f"Failed: {failed}, Timeout: {timeout}")
    print(f"Results saved to batch_v2_results.json")


if __name__ == "__main__":
    main()
