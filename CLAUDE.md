# CB2 AI Creative Lab

## 1. Project Overview

AI product photography pipeline for Chubby Buttons CB2 — a wearable Bluetooth remote with 5 tactile buttons, worn on the forearm. We generate lifestyle marketing photos and videos of the CB2 on people doing action sports (motorcycle, skiing, snowboard, MTB). Justin Barad is co-founder; Jordan handles product photography. After testing 21+ approaches across 385+ images, the winning pipeline uses GPT Image 1.5, Nano Banana Pro (Gemini 3 Pro), Nano Banana 2 (Gemini 3.1 Flash), or FLUX 2 Flex as the generation model, with Ref C reference photo and generate-and-filter strategy — Justin reviews everything by eye. GPT Image 1.5 masked inpainting (scored 99) solves above-elbow placement on GPT-generated scenes.

## 2. What Works (Production Pipeline)

### Step 1: Generate

**Primary model (NEW — April 7): GPT Image 1.5**
- **API:** `POST https://fal.run/fal-ai/gpt-image-1.5/edit`
- **API key:** stored in `~/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas/memory/project_architecture.md`
- **Reference photo:** J&Mike Dual (Ref C) — Drive ID `1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7`
- **URL:** `https://lh3.googleusercontent.com/d/1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7=w800`
- **Key settings:** `quality: "high"`, `input_fidelity: "high"` (preserves product details from reference)
- **Request format:**
  ```json
  {
    "image_urls": ["<ref_url>"],
    "prompt": "<prompt>",
    "size": "1024x1536",
    "quality": "high",
    "input_fidelity": "high"
  }
  ```
- **Cost:** ~$0.10-0.20/image at high quality
- **Why:** Justin said "quality of the images is amazing." Scored 89-90 on first motorcycle tests. Produces photographic-quality images that don't look "AI painting" or "cartoonish." The `input_fidelity: "high"` parameter preserves CB2 reference details better than any FLUX model.
- **Note:** No seed parameter — every generation is unique. No guidance_scale control.

**Secondary model: FLUX 2 Flex g7.0** (still valid, cheaper)
- **API:** `POST https://fal.run/fal-ai/flux-2-flex/edit`
- **Key setting:** `guidance_scale: 7.0` (scored 90-96, $0.05/MP)
- **Request format:**
  ```json
  {
    "image_urls": ["<ref_url>"],
    "prompt": "<prompt>",
    "seed": <number>,
    "num_images": 1,
    "output_format": "jpeg",
    "safety_tolerance": 5,
    "guidance_scale": 7.0,
    "num_inference_steps": 28
  }
  ```

**Nano Banana Pro (Gemini 3 Pro Image)** — scored 99, 98, 95, 91
- **API:** `POST https://fal.run/fal-ai/nano-banana-pro/edit`
- **Cost:** $0.15/image
- **Key features:** Reasoning-based model, supports up to 14 reference images
- **Request format:** Same as FLUX 2 Flex (`image_urls`, `prompt`, `seed`, `guidance_scale`, etc.)
- **Why:** Gorgeous scene compositions. CB2 fidelity rated "poor" by AI pixel analysis but Justin loved the results as usable marketing photos. His visual assessment is the only metric that matters.
- **Note:** AI analysis and human assessment diverge significantly on this model — trust Justin's eyes.

**Nano Banana 2 (Gemini 3.1 Flash Image)** — scored 100 on skiing
- **API:** `POST https://fal.run/fal-ai/nano-banana-2/edit`
- **Cost:** $0.08/image
- **Key features:** Cheaper/faster sibling of Nano Banana Pro. Dynamic action compositions.
- **Request format:** Same as FLUX 2 Flex
- **Why:** Scored 100 on skiing (tied for all-time best). Strong dynamic compositions at lowest cost of the top-tier models.

**GPT Image 1.5 Masked Inpainting** (two-step pipeline) — scored 99
- **Step 1:** Generate clean scene with GPT Image 1.5 (no CB2 in prompt)
- **Step 2:** Mask the lower forearm region, then call GPT Image 1.5 edit with `mask_image_url` parameter + Ref C + CB2 prompt
- **API:** Same `fal-ai/gpt-image-1.5/edit` but with additional `mask_image_url` parameter
- **Cost:** ~$0.30 (two GPT calls)
- **Why:** Solves above-elbow placement — the #1 open problem. By masking specifically the lower forearm, the CB2 is forced into the correct position. Scored 99 on motorcycle.
- **CRITICAL LIMITATION:** Only works on GPT-generated base images. Tested on Nano Banana 2 base images and got catastrophic mode collapse (GPT replaces entire image with Ref C). The base image must come from GPT Image 1.5 for the mask to work correctly.

**FLUX-to-GPT Enhancement Pipeline** (two-step)
- **Step 1:** Generate with FLUX 2 Flex (good CB2 accuracy, $0.05/MP)
- **Step 2:** Enhance with GPT Image 1.5 edit + `input_fidelity: "high"` (improves photorealism)
- **Cost:** ~$0.20 total
- **Results:** FLUX originals scored 94, 97. GPT-enhanced versions scored 91, 94, 88. CB2 survives enhancement.
- **Why:** Leverages FLUX's superior CB2 placement accuracy with GPT's superior photorealism. Enhancement sometimes slightly reduces CB2 detail but overall image quality improves.

**Other models tested (available via fal.ai, same API key):**
- **FLUX 2 Pro** (`fal-ai/flux-2-pro/edit`): $0.03/MP, good photorealism but CB2 flipped perpendicular in test
- **FLUX 2 Max** (`fal-ai/flux-2-max/edit`): $0.07/MP, best textures in FLUX family, CB2 placed above elbow in test

### Prompt Structure
Every prompt follows this skeleton. The **middle is locked** (never change the CB2 block). The **bookends are creative choices** — scene/setting and style/mood/camera can be varied freely per batch. Validated across 289 images with editorial, documentary, Sony A7IV, harsh midday, golden hour, and others — style variation does not affect CB2 hit rate.

**Structure:** `[SCENE + SETTING] + [SUBJECT + ACTIVITY] + LOCKED CB2 BLOCK + waist-up + [STYLE/MOOD/CAMERA]`

**Locked CB2 block (Nano Banana Pro / GPT Image 1.5 with dual-ref + explicit symbols):**
- Left arm: `the compact wearable remote from image 1 (108mm long, 39mm wide) with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, LED window closest to WRIST, PLUS button closest to wrist, MINUS button closest to elbow, five round tactile buttons in a vertical row reading from wrist to elbow: PLUS (+), FAST-FORWARD (two right triangles), PLAY/PAUSE (three bars with triangle), REWIND (two left triangles), MINUS (−), button symbols matching the product in image 2`
- Right arm: `the compact wearable remote from image 1 (108mm long, 39mm wide) with its velcro strap wrapped fully around the RIGHT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, LED window closest to ELBOW, MINUS button closest to wrist, PLUS button closest to elbow, five round tactile buttons in a vertical row reading from wrist to elbow: MINUS (−), REWIND (two left triangles), PLAY/PAUSE (three bars with triangle), FAST-FORWARD (two right triangles), PLUS (+), button symbols matching the product in image 2`
- **Requires dual-ref:** image 1 = Ref C at w=1600, image 2 = cb2-ref-front.jpg (product close-up with clear symbols)

**Locked CB2 block (FLUX 2 Flex — simpler version):**
- Left arm: `wearing the wearable remote from image 1 on their LEFT forearm, PLUS button closest to wrist, LED window closest to wrist`
- Right arm: `wearing the wearable remote from image 1 on their RIGHT forearm, MINUS button closest to wrist, LED window closest to elbow`

**Key prompt improvements discovered April 7:**
- **"OVER the jacket sleeve"** — fixes bare skin / sleeve-ripped-off problem (major issue in earlier batches)
- **"halfway between wrist and elbow"** — reinforces below-elbow placement (Justin's #1 complaint was above-elbow)
- **"velcro strap wrapped fully around"** — fixes missing strap (Justin flagged in desert v1: "strap missing on upper part")
- **"five round tactile buttons"** — prevents GPT Image 1.5 from generating 7-8 buttons (happened in night scene)
- **Specific camera/lens** ("Shot on Sony A7R IV 85mm f/2.0") — more photographic than generic quality boosters
- **Add imperfections** ("film grain, slight lens vignetting, chromatic aberration") — reduces AI-polished look

**Example prompts (GPT Image 1.5):**
- `Motorcycle rider cruising coastal highway at golden hour, wearing leather riding jacket, thick leather riding gloves, and full-face helmet, the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-up button closest to wrist, five round tactile buttons, both arms relaxed on handlebars, waist-up, Shot on Sony A7R IV 85mm f/2.0, warm natural light, film grain`
- `Desert highway through red rock canyon, motorcycle rider on adventure bike, wearing textile riding jacket, leather riding gloves, and full-face helmet, the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-up button closest to wrist, five round tactile buttons, waist-up, Shot on Nikon Z9 70mm f/2.8, harsh desert sun, documentary photography`

**MANDATORY per-sport gear (always include in prompts):**
- **Motorcycle:** leather riding gloves, full-face helmet, leather/textile riding jacket with armor
- **Skiing:** ski gloves, helmet, goggles, ski jacket
- **Snowboard:** gloves, helmet, snowboard jacket
- **MTB:** full-face DH helmet, gloves, jersey/armor
- **Snowmobile:** snowmobile gloves, full-face helmet, snowmobile suit

**What NOT to put in prompts:**
- Colorway names or button colors (let the reference photo handle it)
- "Bright button icons" or "clearly visible symbols" (causes glowing)
- "Wireless earbuds" or "AirPods" — they float on the face or look comically Photoshopped. If wearing a helmet, earbuds are invisible anyway (implied by use case). Drop from all prompts.
- "Product photography" (triggers sterile white-background aesthetic)
- CB2 description before the scene (scene-first produces better results)
- Generic quality boosters ("4K," "hyperrealistic," "ultra HD") — triggers over-polished CGI look
- The word "photorealistic" — ironically triggers AI's idea of photorealistic, which is over-smoothed

### Arm Orientation Rule (CONFIRMED April 7 — verified by Justin with engineering drawing, product photo, and 3 rounds of testing)
- **LEFT arm (wrist→elbow):** PLUS (+), FAST-FORWARD (▷▷), PLAY/PAUSE (≡▷), REWIND (◁◁), MINUS (−). LED window at WRIST (same end as PLUS).
- **RIGHT arm (wrist→elbow):** MINUS (−), REWIND (◁◁), PLAY/PAUSE (≡▷), FAST-FORWARD (▷▷), PLUS (+). LED window at ELBOW (same end as PLUS).
- **Key rule:** LED window is ALWAYS on the PLUS end of the device. PLUS is closest to wrist on LEFT arm, closest to elbow on RIGHT arm.
- **Device dimensions:** 108mm × 39mm (≈ 4.25" × 1.5"). NOT 3 inches.
- **WARNING:** A previous session incorrectly reversed this to "MINUS closest to wrist on LEFT arm" — that is WRONG. Justin confirmed in V3 feedback: "minus symbol is by the wrist, which should not be" (on left arm).

### Reference Photo Rotation Rule (CONFIRMED April 8 — 26–2 A/B verdict with pure isolation)
**Reference photo orientation is the primary failure mode for upside-down CB2 renders.** In the first ref A/B test (12 candidate refs × 48 gens, Nano Banana Pro, single-ref), Justin flagged 73% of outputs as rotated-180°. Rotating each reference 180° (`sips -r 180`) and re-running with identical prompts and seeds produced a 26–2 win rate for the rotated side (31/48 pairs rated, `exportedAt: 2026-04-08T18:47Z`). Scoring semantics: rot=5 means rotation nailed it; rot=1 means still broken; orig=5 means it didn't need rotation; both=5 means the model swapped arms (still correct, just mirrored).

**Production reference library (locked 2026-04-08):**

| ID | File | Colorway | Type | Rotated URL (permanent) |
|----|------|----------|------|--------------------------|
| h3 | IMG_0534_Hunter_Jacket_A | Hunter | jacket | `https://jbarad424.github.io/ideas/rotated-refs/h3.jpg` |
| h5 | IMG_0542_Hunter_Jacket_C | Hunter | jacket | `https://jbarad424.github.io/ideas/rotated-refs/h5.jpg` |
| h6 | IMG_0566_Hunter_Product_C | Hunter | product | `https://jbarad424.github.io/ideas/rotated-refs/h6.jpg` |
| p4 | IMG_0550_Patriot_Jacket_B | Patriot | jacket | `https://jbarad424.github.io/ideas/rotated-refs/p4.jpg` |
| p5 | IMG_0556_Patriot_Jacket_C | Patriot | jacket | `https://jbarad424.github.io/ideas/rotated-refs/p5.jpg` |
| p6 | IMG_0560_Patriot_Jacket_D | Patriot | jacket | `https://jbarad424.github.io/ideas/rotated-refs/p6.jpg` |
| **Tron — added 2026-04-09 (Justin shot these himself, A/B results in `ratings/tron_ab_ratings_2026-04-09.json`)** | | | | |
| t18 | IMG_7201_Tron_Product_A | Tron | product | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t18.jpeg` |
| t01 | IMG_7184_Tron_Glove | Tron | jacket | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t01.jpeg` |
| t03 | IMG_7186_Tron_Sleeve_A | Tron | jacket | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t03.jpeg` |
| t11 | IMG_7194_Tron_Sleeve_B | Tron | jacket | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t11.jpeg` |
| t05 | IMG_7188_Tron_Sleeve_C (Tier 2) | Tron | jacket | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t05.jpeg` |
| t09 | IMG_7192_Tron_Sleeve_D (Tier 2) | Tron | jacket | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t09.jpeg` |
| t17 | IMG_7200_Tron_Product_B (Tier 2) | Tron | product | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t17.jpeg` |

**Tron A/B results (2026-04-09):** Justin shot 20 Tron refs (IMG_7184–7203), and `tron_ab_test.py` fired 20 refs × 2 sports × 2 scenes = 80 NB Pro gens (same prompts + seeds as the 2026-04-08 Hunter/Patriot rotation A/B for direct comparison). 77/80 rated. **Unlike the Hunter/Patriot shoot, Justin captured multi-orientation variants physically, so no `sips -r 180` post-processing was needed.** Full pattern analysis + Hunter/Patriot reshoot recommendations in `ratings/CLAUDE-md-proposed-update.md`. TL;DR: **t18 is the only pure-pure gold (4×5, 0 flags)** — standalone product on wood table, vertical canonical orientation (PLUS at top). t01/t03/t11 are Tier-1 with cosmetic rot180 flags only. t10 and t16 are kill-listed.

**Killed references (never use — rotation + arm lock didn't fix them):**
- h1 (IMG_0525), h4 (IMG_0541), p1 (IMG_0513) — 3 rot=1 fails each in the rotation A/B
- **p5 (IMG_0556)** — killed 2026-04-08 after production batch V1. Only 1 clean success out of 8 gens (mtb_s1=5). 3 perpendicular flags + 3 wrongArm flags. Worst performer in the batch.
- **t10 (IMG_7193)** — killed 2026-04-09 after Tron A/B. Produced a score-1 on mtb_s1 (weird two-rider composition) + score-3 on mtb_s0. Avg 3.5, worst Tron performer.
- **t16 (IMG_7199)** — killed 2026-04-09 after Tron A/B. Upside-down vertical standalone (MINUS at top, opposite of t18 canonical orientation). Score-1 on mtb_s1 + one unrated. Avg 3.67.

**Mixed (use only in specific scenes that worked):** h2, p2, p3.

**Ref C (J&Mike Dual) is still a valid baseline** — it had 0 flags in the original A/B and was excluded from the rotation test because rotating it would break something already working. Continue using it when you want the "two-people shot works" dynamic.

### Per-Scene Arm Decision Table (proposed 2026-04-08, locks in naturally visible arm per camera setup)
**The arm swap problem:** When both orig+rotated scored 5, the model placed the device on opposite arms. Rotating a reference flips the device top-to-bottom, and the model re-assigns it to whichever arm makes the new orientation "natural" — so without an explicit arm lock, the model has an escape hatch. Every prompt must lock LEFT or RIGHT explicitly per scene.

| Scene | Seed | Target arm | How to get it |
|-------|------|------------|---------------|
| moto_s0 coastal golden hour | 9101 | LEFT | default framing |
| moto_s1 desert canyon | 9102 | LEFT | default framing |
| mtb_s0 forest descend | 9201 | LEFT | default framing |
| mtb_s1 alpine ridge | 9202 | LEFT | default framing |
| ski carve | — | RIGHT | default framing |
| **snowboard LEFT** | 9401/9402 | LEFT | h3 ref + **regular stance** |
| **snowboard RIGHT** | 9401/9402 | RIGHT | h3 ref + **goofy stance** (right foot forward) |
| snowmobile | — | LEFT | default framing |

**CRITICAL — prompt arm-lock does NOT work (confirmed 2026-04-08).** The `LEFT lower forearm` / `RIGHT lower forearm` text in the CB2 block is cosmetic. The reference image geometry, the rider's body orientation, and the scene pose prior dominate. Three tests proved this:
1. Prompt LEFT vs RIGHT on same refs → 5/6 stayed LEFT regardless
2. Mirrored refs (device on opposite arm in ref) → 6/6 still rendered LEFT
3. Goofy stance on h3 → FLIPPED both scenes from L to R (h5 and p4 stance-immune)

**The real levers are:**
- **Reference choice** — most refs are "arm-committed" by virtue of the pose/angle in the source photo. h3 responds to stance swaps; h5 and p4 don't.
- **Body orientation in scene** — for snowboard, regular stance = LEFT output, goofy stance = RIGHT output (on h3 only so far).
- **Fallback: GPT masked inpainting** — generate clean scene → mask specific forearm → inpaint CB2. Only works on GPT Image 1.5 base images. Known-good from V1 (scored 99 on moto).

**Rule:** Keep the LEFT/RIGHT text in the prompt for documentation, but don't trust it. If you need a specific arm on snow, use h3 + the matching stance. For other sports, stick with defaults until re-tested. Retire h5 and p5 from snow permanently.

### Step 2 (optional): Two-Pass Gear Addition
- Run a winning image through FLUX edit again to add helmet or earbuds
- Works for: helmets, earbuds, small accessories (CB2 survives)
- Does NOT work for: full wardrobe swaps or ski gloves (destroys CB2)
- Kontext Pro also works for helmets (scored 95)

### Step 3: Review
- **Review page:** `https://jbarad424.github.io/ideas/cb-review.html`
- 7 tabs: TO REVIEW, REVIEWED, PROGRESS, GALLERY, VIDEOS, CREATE (under construction), AI SCORING
- Feedback syncs to `cb-feedback.json` on GitHub via Make.com webhook
- Cross-device sync merges (doesn't overwrite) via fetch-before-push

### Step 4 (for winners): Video
- Take approved stills → animate with Runway Gen-4 Turbo (scored 97) or Gen-4.5 (scored 94)
- Runway API key stored in memory files
- Also available via fal.ai: **Seedance 2.0** (added 2026-04-09, currently #1 on Artificial Analysis Elo at 1269 — beats Veo 3, Sora 2, Gen-4.5), Kling 3.0 Pro, Veo 3.1, Sora 2 Pro
- **Seedance 2.0** — `fal-ai/bytedance/seedance-2.0/image-to-video` ($0.3024/sec at 720p std, $0.2419/sec at 720p fast). Multimodal (up to 9 ref images), 4–15s clips, native audio. fal page mentions a gating form — first call may return 403; if so, file the access request and retry. Wired into Video Lab as "Seedance 2.0" + "Seedance Fast" buttons. UNTESTED on CB2 stills as of 2026-04-09 — Justin to smoke test.
- Workflow: stills first → Justin picks winners → animate only approved images

### Key Stats (April 7, 2026 — end of third session)
- 410+ total images generated, 290+ reviewed, 25 new images awaiting review
- ~90 new images generated April 7 total (across three sessions): 6 Flex moto, 2 two-pass, 4 model comparison, 8 GPT Image 1.5, 19 pipeline tests, 7 micro-inpainting, 20 NB Pro action batch (ski/sled/moto/MTB × 5), 5 motorcycle-with-gloves, ~19 other
- New all-time highs: **100** (NB2 skiing, V4 moto desert), **99** (GPT masked inpaint motorcycle, NB Pro coastal)
- Top all-time: 100 (snowboard, NB2 skiing, V4 moto desert), 99 (GPT masked inpaint, NB Pro coastal), 98 (motorcycle, MTB, skiing)
- 5 parallel research agents completed: product placement models, compositing, Jordan shot list, micro-inpainting, FLUX-to-photorealism
- 5 parallel pipeline tests completed: GPT masked inpaint, Nano Banana Pro, Nano Banana 2, FLUX-to-GPT enhancement, Fibo Edit
- Orientation correct 65-70% with Ref C + arm rules (FLUX), ~50% with GPT Image 1.5 (small sample)
- 14 test videos across 6 models (Kling 3.0 Pro V4 desert added)
- **4 production-quality models validated:** GPT Image 1.5, FLUX 2 Flex, Nano Banana Pro, Nano Banana 2
- **Above-elbow placement solved** via GPT masked inpainting (on GPT-generated scenes only)
- **Review page UX major upgrade:** Gallery filter toggles, voice-dictated score parser rewrite, Video Lab with real fal.ai submissions + Job History persistence

## 3. What's Been Tried and Failed

Every entry here was properly tested with real API calls and real images. Do NOT re-attempt these unless a fundamentally new capability has been released that specifically addresses the stated failure reason. State that reason explicitly before re-testing.

| # | Approach | Tests Run | Best Result | Why It Failed | Date Killed |
|---|----------|-----------|-------------|---------------|-------------|
| 1 | **LoRA fine-tuning** (FLUX 1 Dev + FLUX 2 Dev) | 9 training runs, 10 inference tests per model | 17/100 | CB2 has 5 specific buttons, LED window, logo, strap — too many precise details for a LoRA to memorize. V4 also trained on a corrupted ZIP (HTML error page). Even with proper training data (45 lifestyle + product photos), both FLUX 1 and FLUX 2 produced garbled remotes. | Apr 6 |
| 2 | **Inpainting Pipeline B** (crude rectangular mask → FLUX Fill Pro) | 2 tests | 0/100 | Destroyed the entire scene. Rectangular masks are too imprecise for a small forearm device. | Apr 4 |
| 3 | **Inpainting Pipeline C** (SAM 3 precise mask → Fill Pro, text-only) | 4 tests | 5/100 | Text description alone cannot generate a recognizable CB2. The model has no concept of what the product looks like without a reference image. | Apr 4 |
| 4 | **Inpainting Pipeline E** (SAM 3 mask → Fill Pro + reference_image_url) | 12 tests (6 parameter combos × 2 scenes) | 0/100 | reference_image_url is a GLOBAL control that warps the entire image, not just the masked region. This is an API architecture limitation, not fixable by parameter tuning. | Apr 5 |
| 5 | **ControlNet + IP-Adapter Pipeline G** (fal.ai flux-general) | 4 live API calls | Grid artifacts | Three fatal problems: (1) IP-Adapter overrides ControlNet — confirmed with live test. (2) flux-general runs FLUX.1 Dev, a generation behind FLUX 2 — worse quality at 2.5x cost. (3) Canny ControlNet can't solve orientation without already having the correct output image (circular dependency). | Apr 6 |
| 6 | **Kontext scene-swap Pipeline F** | Multiple tests | 80/100 ceiling | Every result looks like the same modeling photo with a new backdrop. Can't rotate symbols. Can't create compositional variety. Good for one-off fixes, not production. | Apr 5 |
| 7 | **SAM rotation post-processing Pipeline H** | 3 tests on winning images | 35/100 | Detection works (SAM 3 finds the CB2 correctly) but the rotation + compositing looks unnatural — device appears embedded in skin/jacket. Lighting direction inverts. Feathered edges visible. | Apr 6 |
| 8 | **AI auto-scoring v1** (structured checklist, no reference) | 30 images | 63% accuracy | Sees "something on arm" and says YES even for garbled blobs. 8 false positives (garbage scored 85-100). Can't distinguish the CB2 from any dark rectangle. | Apr 7 |
| 9 | **AI auto-scoring v2** (reference comparison — show AI the real CB2) | 30 images | 57% accuracy (worse) | More conservative but 7 false negatives — filtered out images scoring 86, 92, and 99. Would have killed production winners. Not reliable enough as a filter. | Apr 7 |
| 10 | **Colorway-specific prompting** ("Hunter green with yellow icons") | 20 images across 6 sports | 10-22 avg | Model illuminates/glows the buttons in the requested color instead of rendering them naturally. Colorway must come from the reference photo, not the prompt. | Apr 6 |
| 11 | **CB2-first prompt order** (product description before scene) | 6 images, A/B vs scene-first | Broke skiing scene | Putting CB2 details first causes FLUX 2 to over-anchor on the object at the expense of scene coherence. Scene-first produces better composition AND better CB2 rendering. | Apr 7 |
| 12 | **Tahoe single-person reference photos** | 6 images across 3 sports | Copies original | Too constraining — model reproduces the reference person verbatim instead of creating diverse compositions. "Looks like the original photo" across all tests. | Apr 7 |
| 13 | **Full wardrobe swap via two-pass** (change T-shirt to motorcycle jacket) | 3 tests | CB2 destroyed | Model treats the CB2 as part of the "clothing" and removes it along with the T-shirt. Only small, targeted additions (helmet, earbuds) survive two-pass. | Apr 7 |
| 14 | **AI Vision co-rater** (early Claude Sonnet scoring) | ~20 images | Gave 5/5 to floating products | Holistic scoring by LLMs is fundamentally unreliable for product-specific detail assessment. | Apr 3 |
| 15 | **Outpainting from real CB2 photo** (FLUX Pro Fill) | 14 tests across 3 crop strategies | 0/100 (V2/V3), scene-confused (V1) | V1 (wide Mike Moto crop): CB2 perfect but motorcycle context leaked into every sport scene. V2 (tight arm crop): too little context, total hallucinations. V3 (Ref C arm crop): two-person fragments fused into nightmares. Outpainting is designed for background extension, not constructing full-body action athletes from arm fragments. | Apr 7 |
| 16 | **Stock photo + multi-ref CB2 overlay** (Path C) | 2 tests | 40/100 | Base rider scored 90 but the combination step (adding CB2 via multi-ref edit) produced oversized CB2 (4x too big) and cartoonish quality. Multi-ref edit treats both images as creative inspiration, not as "overlay product onto person." | Apr 7 |
| 17 | **Virtual try-on APIs** (6 models: IDM-VTON, CAT-VTON, FASHN, Leffa, Kling Kolors, FLUX 2 VTON) | 7 tests across 6 models | 0/100 | Every VTON model segments the person into body regions and looks for CLOTHING to replace. They all treated the CB2 reference photo as a T-shirt and replaced the rider's shirt. IDM-VTON's auto-mask confirmed: it masked the entire torso. VTON has no concept of "accessory on forearm." Accessory-specific APIs (Pixazo, SellerPic) exist but are enterprise/apply-only and designed for watches, not action sports. | Apr 7 |
| 18 | **Kontext LoRA Inpaint** (fal-ai/flux-kontext-lora/inpaint) | 20+ tests across 4 sports, 3 mask sizes, 3 strength values | 0/100 on clean bases | Initial 96-97 scores were a confounded test — the base image was generated by FLUX 2 Flex with Ref C at g=2.0, so the CB2 was already present from reference bleed-through. Kontext inpaint took credit for FLUX 2 Flex's work. When tested on truly clean base images (no Ref C influence), every test scored 0. The approach cannot place a CB2 from a reference onto a masked forearm region. Varying prompt style, mask size (small/big), mask format (PNG/JPEG), strength (0.85-1.0), guidance_scale, reference photo (Ref C vs standing product), and image orientation (landscape/portrait) made no difference. | Apr 7 |
| 19 | **Micro-inpainting for symbol sharpening** (GPT Image 1.5 small masks on CB2 area) | 7 tests: 3 mask strategies (rectangle, five circles, oval) on 99-scored moto + 100-scored skiing | Made things WORSE | Every micro-inpaint reduced quality: button count dropped from 5 to 4, strap removed, symbols garbled. GPT regenerates the entire device during inpainting and loses details that were already correct. On non-GPT base images, small masks cause catastrophic mode collapse (GPT replaces entire image with Ref C). Micro-inpainting is fundamentally wrong for refinement — GPT cannot selectively sharpen, it regenerates. | Apr 7 |
| 20 | **Fibo Edit** (fal-ai/fibo/edit) | 1 test | 0/100 | Text-only object insertion — no reference image support. Same fundamental failure as Pipeline C (#3): text description alone cannot generate a recognizable CB2. The model has no concept of what the product looks like without a reference image. Dead on arrival. | Apr 7 |
| 21 | **Compositing CB2 from FLUX onto GPT scene** (extract CB2 region from FLUX image, paste onto GPT scene) | Conceptual analysis | Dead on arrival | Same geometric mismatch problem as Pipeline H (#7): the CB2 from a FLUX-generated image has different arm angle, lighting direction, perspective, and scale than the GPT-generated scene. Compositing requires matched geometry, which would require generating both images with identical poses — a circular dependency. | Apr 7 |

## 4. Operating Rules (Always Follow)

**How to work with Justin:**
1. Never suggest breaks, bedtime, or comment on session length. Justin decides when he's done.
2. Justin's visual assessment of CB2 images is more reliable than any AI analysis. Always defer to his scores.
3. Never fabricate scores, data, or claim something works without verifying it yourself first.
4. Direct, no-BS communication. Say what's true, not what sounds good.

**How to make decisions:**
5. Before committing to ANY path, proactively list what else hasn't been tested. Don't wait for Justin to ask "is this the only way?" — surface the alternatives yourself and explain why you're recommending one over the others.
6. Before declaring an approach dead, distinguish "the concept is wrong" from "my implementation was wrong." State what a proper test would look like.
7. Don't flip-flop on recommendations. State what would prove you wrong BEFORE testing, not after.
8. Always research what's currently best-in-class before spending credits. The AI landscape changes fast — don't assume last session's tool is still the right one.
9. Run parallel agents to test alternatives simultaneously. Justin has credits to burn and prefers data over speculation. Test first, recommend second.

**How to build:**
10. Simple tools + chat feedback > complex infrastructure. Don't over-build.
11. Foundation first — rock solid every iteration, no shortcuts.
12. Never claim a fix is deployed without checking for side effects (the git deletion bug happened because of this).
13. Before every git commit, check `git diff --cached` for accidental deletions. Run the safe-commit check.

**Session handoff protection:**
14. At the end of every session, update this CLAUDE.md with: what was tested, what the results were, what's dead, and what's next. This file IS the handoff — a new session on any machine reads it automatically.
15. Before suggesting any approach, check the "What's Been Tried and Failed" section above. If it's listed there, do NOT re-suggest it unless you have a specific, concrete reason why the previous failure doesn't apply (new model released, different implementation, etc.). State that reason explicitly.
16. When updating this file, never remove entries from the failed section. Only add to it. The failed section is append-only — it's the project's scar tissue and it prevents us from repeating mistakes.

## 5. Current Status and Next Steps

### What's Validated and Production-Ready
- **GPT Image 1.5** is the photorealism champion (scored 89-90 on motorcycle, 99 with masked inpainting, Justin: "quality is amazing")
- **Nano Banana Pro (Gemini 3 Pro)** scored 99, 98, 95, 91 — reasoning-based, gorgeous scenes ($0.15/image)
- **Nano Banana 2 (Gemini 3.1 Flash)** scored 100 on skiing — cheapest top-tier model ($0.08/image)
- **FLUX 2 Flex g7.0** remains valid as cheapest option (scored 90-96, $0.05/MP)
- **GPT Masked Inpainting** solves above-elbow placement (scored 99) — generate clean scene, mask lower forearm, inpaint CB2. Only works on GPT-generated base images.
- **FLUX-to-GPT Enhancement** leverages FLUX CB2 accuracy + GPT photorealism (FLUX 94/97 originals survived enhancement)
- **Ref C (J&Mike Dual)** is the production reference photo (works with GPT Image 1.5, FLUX, Nano Banana Pro/2)
- **Reinforced prompt** with "OVER jacket sleeve," "halfway between wrist and elbow," "velcro strap wrapped fully around" — fixes bare skin, above-elbow, and missing strap problems
- **Scene-first prompts** with specific camera/lens language produce the most photographic results
- **Two-pass** works for adding helmets and earbuds to winning images (confirmed again this session)
- **Gen-4 Turbo** (97) and **Gen-4.5** (94) are the production video models
- **Generate-and-filter with human review** is the only reliable quality gate
- **T-shirt bleed largely solved by prompting** — including "leather riding jacket" in prompt gets proper gear without needing jacket-specific reference photos

### Open Problems
- **Above-elbow placement:** Still happens ~30-50% with single-pass generation. **Partially solved** via GPT masked inpainting (forces lower forearm), but that adds cost ($0.30 vs $0.10-0.20) and only works on GPT-generated base images.
- **Symbol clarity:** GPT Image 1.5 sometimes renders warped/unclear button symbols (Justin: "symbols are a little wart"). Micro-inpainting to fix this **confirmed dead** — makes things worse every time (see failed #19).
- **Button count accuracy:** GPT Image 1.5 night scene generated 7-8 buttons instead of 5. Adding "five round tactile buttons" helps but not always.
- **Colorway control:** No reliable way to specify Hunter/Tron/Patriot from prompt alone. Fix requires colorway-specific reference photos.
- **Hunter symbol fidelity:** All existing Hunter reference photos have old/faded symbol outlines and missing LED plastic.
- **Patriot coverage:** Zero third-person Patriot photos exist anywhere.
- **GPT masked inpainting model dependency:** Only works on GPT-generated base images. NB2 and other model bases cause catastrophic mode collapse.

### April 7 Session Results (Combined — Two Sessions)

**Early Session — Model Comparison and GPT Image 1.5 Discovery:**

**Model Comparison (4-way head-to-head, same prompt + Ref C):**
| Model | Endpoint | Cost | Justin's Verdict |
|-------|----------|------|-----------------|
| FLUX 2 Flex g7.0 | `fal-ai/flux-2-flex/edit` | $0.05/MP | "Looks like a painting in a bad way, no CB visible" |
| FLUX 2 Pro | `fal-ai/flux-2-pro/edit` | $0.03/MP | "Looks inspiring but CB2 flipped perpendicular" |
| FLUX 2 Max | `fal-ai/flux-2-max/edit` | $0.07/MP | "Would be really cool if CB was below elbow" |
| **GPT Image 1.5** | `fal-ai/gpt-image-1.5/edit` | ~$0.10-0.20 | **"Quality of images is amazing. Remote preserved."** |

**GPT Image 1.5 Deep Dive (8 images, 2 rounds):**
- Round 1 (basic reinforcement): Coastal 90, Desert 89, Alpine fail (above elbow), Night 0 (wrong product)
- Round 2 (strap + button count reinforcement): 4 images generated

**FLUX 2 Flex Motorcycle Batch (6 images):**
- Desert 8104 strongest ("Strong. Right spot."), others had above-elbow or sleeve issues
- Key learning: including "leather jacket" and "helmet" in prompt gets proper motorcycle gear ~83% of the time

**Two-Pass Tests (2 images):**
- Sunrise + helmet: CB2 survived, helmet added naturally, but above elbow
- Alpine + earbuds: CB2 survived, earbuds not visible under helmet

**Continued Session — New Pipelines Validated:**

**GPT Image 1.5 Masked Inpainting (scored 99):**
- Generate clean motorcycle scene with GPT Image 1.5 (no CB2) → mask lower forearm → inpaint CB2 with Ref C + input_fidelity:high
- Solves above-elbow placement by forcing CB2 into masked lower forearm region
- CRITICAL: Only works on GPT-generated base images. Failed catastrophically on NB2 bases (mode collapse).

**Nano Banana Pro / Gemini 3 Pro Image (scored 99, 98, 95, 91):**
- Reasoning-based model, gorgeous compositions
- CB2 fidelity rated "poor" by AI analysis but Justin scored results 91-99
- Key insight: Justin's "usable marketing photo" standard differs from pixel-level AI analysis. His eyes are the only metric.

**Nano Banana 2 / Gemini 3.1 Flash Image (scored 100 on skiing):**
- Cheaper/faster sibling of NB Pro ($0.08/image)
- Dynamic action compositions, new all-time high on skiing

**FLUX-to-GPT Enhancement Pipeline:**
- FLUX originals scored 94, 97. GPT-enhanced versions scored 91, 94, 88
- CB2 survives enhancement with input_fidelity:high
- Trade-off: photorealism improves but CB2 detail can slightly degrade

**What Failed This Continued Session:**
- **Micro-inpainting for symbol sharpening** — 7 tests, 3 mask strategies, all made things worse (see failed #19)
- **Fibo Edit** — text-only, no reference support, same as Pipeline C failure (see failed #20)
- **Compositing CB2 from FLUX onto GPT scene** — geometric mismatch, dead on arrival (see failed #21)

### Third Session — Review Page UX Overhaul + New Batches

**Gallery Filter UX Fix:**
- Filters changed from confusing ✓/✗ icons to clear "Accepted"/"Rejected" text labels
- Toggle behavior: clicking same filter resets to 'all', no separate All button needed
- Added hint text: "Tap a filter to toggle it on/off"

**galScore() Voice Parser Rewrite:**
- Complete rewrite to handle Justin's voice-dictated reviews (Siri transcription)
- Priority-ranked candidate system with 8+ regex patterns: "give this 90", "like a 98", "100 percent", "close to 100", "this is like 100", "get this to 96", etc.
- Fixed critical bug: "100 percent", "this is like 100" were parsing as 50 (keyword default). Now correctly parse as 100.
- Word-number mapping: "hundred percent" → 100, "five out of 100" → 5
- "Final score: X" manual override as highest priority

**Video Lab — Real API Submissions from Browser:**
- Video Lab now makes real fetch() calls to fal.ai queue API directly from the browser (CORS allowed from jbarad424.github.io)
- Supports Kling 3.0 Pro, Veo 3.1 Lite, Sora 2 Pro; Runway still requires Claude Code
- Added directorial cues textarea for custom prompts
- Fixed image display glitch on tab switch (src='' then setTimeout to set URL)
- Active job state persists in localStorage (`cb2_videolab_job`) — survives page reloads
- **Job History panel** — persistent log of all submissions in localStorage (`cb2_video_jobs`, up to 20)
  - Every submission logged with requestId, statusUrl, platform, label, timestamp
  - Status auto-updates on COMPLETED/FAILED via polling
  - "Refresh All" button batch-checks all pending jobs
  - "Watch" link appears for completed videos
  - Nothing gets lost even if polling breaks or page reloads

**fal.ai Queue API Key Learnings:**
- Submit: POST to `queue.fal.run/{endpoint}` — returns `request_id`, `status_url`, `response_url`
- Status check: GET (not POST!) to `status_url` — POST re-queues the job
- Result: GET to `response_url` — returns video URL in `res.video.url` or `res.output.video.url`
- Status URLs use a SHORTER base path than submit URL (e.g., `/fal-ai/kling-video/requests/{id}/status` not `/fal-ai/kling-video/v3/pro/image-to-video/requests/{id}/status`). Always use the URLs returned by the API.
- Jobs complete and charge even if the UI loses track. Job History solves this visibility problem.

**New Images Generated (25 total, awaiting Justin's review):**
- 20 NB Pro dual-ref action batch: ski (7001-7005), snowmobile (7001-7005), motorcycle (7001-7005), MTB (7001-7005)
- 5 motorcycle-with-gloves (8001-8005) — leather riding gloves added to prompt

**Kling 3.0 Pro Video:**
- Animated V4 Moto Desert (100-scored image) — completed, added to ALL_VIDEOS as vid-kling3-v4desert

**Prompt Template Updates:**
- All motorcycle prompts now include "thick leather riding gloves"
- "Wireless earbuds" / "AirPods" removed from all prompts permanently (float on face, look Photoshopped)
- MANDATORY per-sport gear list added to CLAUDE.md

### April 10 Session Summary (35+ commits)

**Gallery overhaul:**
- Videos merged into gallery as Photos/Videos toggle (separate content types, no mixing)
- 37 super-liked images fixed and properly tracked
- Video thumbnails display inline — no more blank video cards
- Filter bar reorganized into clean rows for mobile: Show/Sport/Model
- Sort by date added
- Debounced gallery rendering for performance

**CREATE tab — full production workflow:**
- Model-aware Sonnet prompt refiner (optimizes per model: GPT Image 1.5, NB Pro, NB2, FLUX)
- Sport-aware vibe system (scene descriptions match sport environment)
- Gender dropdown for male/female subject selection
- Reference photo auto-pick based on past performance data
- Model badge on generated cards
- Bigger text for readability
- Colorway swap button: same pose, different colorway (Hunter/Patriot/Tron)

**Video Lab — permanent tab with full controls:**
- Duration slider, aspect ratio presets (9:16/16:9/1:1), end-frame controls
- Seedance 2.0 integration with polling fix deployed
- Keep/Archive workflow for reviewing completed videos
- "Create again" button for re-generating with different settings
- Auto-archive to catbox for permanent video URLs
- Confirmation modals before every generation (cost transparency)
- Refiner translates button-press descriptions to environmental camera effects

**Discover tab (new):**
- CB2-free "sketch" photo generation (~$0.05 each) — athletes in action without product
- Inspiration upload with Claude Vision analysis (upload any photo, get recreation suggestions)

**Archive and infrastructure:**
- Safety guard on archival operations
- .nojekyll deployed for GitHub Pages compatibility
- Corpus hydration for permanent URLs
- Video auto-archive pipeline
- Tab persistence (remembers last active tab)
- Batch persistence for CREATE operations
- Deployed Worker source code saved to repo

**Business case PDF generated** — full market analysis for cofounder presentation (separate document)

### Next Session Priorities (updated 2026-04-10 EOD)
1. **Verify fal.ai pricing** against actual billing dashboard — confirm $0.08-$0.30/image cost assumptions.
2. **Test Seedance 2.0 end-to-end** — polling fix deployed but untested with real CB2 stills.
3. **Try cluster-test.html** — visual clustering experiment groups similar photos by AI vision analysis.
4. **Video Lab cross-device sync** — jobs are currently per-browser localStorage, need shared state.
5. **Hunter/Patriot product reshoot** when products arrive — t18-clone (vertical standalone on wood table, PLUS at top, warm light).

### Key Resources
| Resource | Location |
|----------|----------|
| Review page | https://jbarad424.github.io/ideas/cb-review.html |
| Tron ref A/B review | https://jbarad424.github.io/ideas/tron-ab-review.html |
| Jordan's shot list | https://jbarad424.github.io/ideas/jordan-shot-list.html |
| Feedback JSON | https://jbarad424.github.io/ideas/cb-feedback.json |
| Notion status | https://www.notion.so/33af45bfc038813f8b09f0d6efdffc49 |
| Google Drive | CB2 AI Generated Photos (4 quality-tier subfolders) |
| Memory files | ~/.claude/projects/-Users-justinbarad-code-cb2-ideas/memory/ |
| Make.com sync webhook | https://hook.us1.make.com/p3bt4ga6npqjs3608t9aou45qq1m5amh |
| Plan v2 (CREATE tab) | `PLAN-CREATE-TAB-V2.md` in repo root |

### Colorway Status (updated 2026-04-09)
| Colorway | Status | Production refs | Notes |
|----------|--------|-----------------|-------|
| **Hunter** | Production-ready | h3, h5, h6 | Reshoot t18-clone pending (product shipment to Justin next week) |
| **Patriot** | Production-ready | p4, p6 (p5 killed) | Reshoot t18-clone pending (product shipment to Justin next week) |
| **Tron** | **Production-ready as of 2026-04-09** | t18 (pure gold), t01, t03, t11 (Tier 1), t05, t09, t17 (Tier 2) | Justin shot 20 refs 2026-04-09, A/B locked winners. t18 is the only pure-pure. t10, t16 kill-listed. |

### Sports Priority
| Sport | Status | Notes |
|-------|--------|-------|
| Motorcycle coastal | **Best sport** (100 V4 desert, 99 GPT masked inpaint, 90 GPT, 98 Flex) | 5 new gloves-added images awaiting review. All prompts now include leather riding gloves. |
| Skiing | **All-time high** (100 NB2, 96 Flex) | 5 new NB Pro dual-ref images awaiting review. Needs gloves in ref photo. |
| Snowboard | Production-ready (96-100) | Strong with Flex g7.0. Needs NB Pro/NB2 testing. |
| MTB | Cracked (94-98) | 5 new NB Pro dual-ref images awaiting review. Recently jumped from avg 34 to 94+. |
| Snowmobile | New — testing | 5 new NB Pro dual-ref images awaiting first review. Added snowmobile detection to galDetectSport(). |
| Hiking | Deprioritized | "People have headphones, don't need CB2 for hiking" — Justin |
| Running | Deprioritized | Not core use case (no gloves needed) |
| Fishing/ATV | Dropped | Not enough demand |
