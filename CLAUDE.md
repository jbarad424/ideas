# CB2 AI Creative Lab

## 1. Project Overview

AI product photography pipeline for Chubby Buttons CB2 — a wearable Bluetooth remote with 5 tactile buttons, worn on the forearm. We generate lifestyle marketing photos and videos of the CB2 on people doing action sports (motorcycle, skiing, snowboard, MTB). Justin Barad is co-founder; Jordan handles product photography. After testing 18+ approaches across 340+ images, the winning pipeline uses GPT Image 1.5 (new as of April 7) or FLUX 2 Flex as the generation model, with Ref C reference photo and generate-and-filter strategy — Justin reviews everything by eye.

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

**Other models tested (available via fal.ai, same API key):**
- **FLUX 2 Pro** (`fal-ai/flux-2-pro/edit`): $0.03/MP, good photorealism but CB2 flipped perpendicular in test
- **FLUX 2 Max** (`fal-ai/flux-2-max/edit`): $0.07/MP, best textures in FLUX family, CB2 placed above elbow in test
- **Nano Banana Pro** (`fal-ai/nano-banana-pro/edit`): $0.15/image, reasoning-based, supports 14 refs, untested

### Prompt Structure
Every prompt follows this skeleton. The **middle is locked** (never change the CB2 block). The **bookends are creative choices** — scene/setting and style/mood/camera can be varied freely per batch. Validated across 289 images with editorial, documentary, Sony A7IV, harsh midday, golden hour, and others — style variation does not affect CB2 hit rate.

**Structure:** `[SCENE + SETTING] + [SUBJECT + ACTIVITY] + LOCKED CB2 BLOCK + waist-up + [STYLE/MOOD/CAMERA]`

**Locked CB2 block (GPT Image 1.5 — reinforced version):**
- Left arm: `the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-up button closest to wrist, five round tactile buttons`
- Right arm: `the wearable remote from image 1 with its velcro strap wrapped fully around the RIGHT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-down button closest to wrist, five round tactile buttons`

**Locked CB2 block (FLUX 2 Flex — simpler version):**
- Left arm: `wearing the wearable remote from image 1 on their LEFT forearm, volume-up button closest to wrist`
- Right arm: `wearing the wearable remote from image 1 on their RIGHT forearm, volume-down button closest to wrist`

**Key prompt improvements discovered April 7:**
- **"OVER the jacket sleeve"** — fixes bare skin / sleeve-ripped-off problem (major issue in earlier batches)
- **"halfway between wrist and elbow"** — reinforces below-elbow placement (Justin's #1 complaint was above-elbow)
- **"velcro strap wrapped fully around"** — fixes missing strap (Justin flagged in desert v1: "strap missing on upper part")
- **"five round tactile buttons"** — prevents GPT Image 1.5 from generating 7-8 buttons (happened in night scene)
- **Specific camera/lens** ("Shot on Sony A7R IV 85mm f/2.0") — more photographic than generic quality boosters
- **Add imperfections** ("film grain, slight lens vignetting, chromatic aberration") — reduces AI-polished look

**Example prompts (GPT Image 1.5):**
- `Motorcycle rider cruising coastal highway at golden hour, wearing leather riding jacket and full-face helmet, the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-up button closest to wrist, five round tactile buttons, both arms relaxed on handlebars, waist-up, Shot on Sony A7R IV 85mm f/2.0, warm natural light, film grain`
- `Desert highway through red rock canyon, motorcycle rider on adventure bike, wearing textile riding jacket and full-face helmet, the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, volume-up button closest to wrist, five round tactile buttons, waist-up, Shot on Nikon Z9 70mm f/2.8, harsh desert sun, documentary photography`

**What NOT to put in prompts:**
- Colorway names or button colors (let the reference photo handle it)
- "Bright button icons" or "clearly visible symbols" (causes glowing)
- Complex multi-detail instructions (earbuds + helmet + jacket — use two-pass instead)
- "Product photography" (triggers sterile white-background aesthetic)
- CB2 description before the scene (scene-first produces better results)
- Generic quality boosters ("4K," "hyperrealistic," "ultra HD") — triggers over-polished CGI look
- The word "photorealistic" — ironically triggers AI's idea of photorealistic, which is over-smoothed

### Arm Orientation Rule
- LEFT arm: volume-up (+) closest to WRIST
- RIGHT arm: volume-down (−) closest to WRIST
- Rule: wearer reads buttons left-to-right looking at their own arm

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
- Also available via fal.ai: Kling 3.0 Pro, Veo 3.1
- Workflow: stills first → Justin picks winners → animate only approved images

### Key Stats (April 7, 2026 — end of session)
- 340+ total images generated, 290+ reviewed
- 20 new images generated this session (6 Flex moto, 2 two-pass, 4 model comparison, 8 GPT Image 1.5)
- Best GPT Image 1.5 scores: 90 (coastal), 89 (desert) — with 4 more awaiting review
- Top all-time: 100 (snowboard), 98 (motorcycle, MTB, skiing)
- Orientation correct 65-70% with Ref C + arm rules (FLUX), ~50% with GPT Image 1.5 (small sample)
- 13 test videos across 6 models
- **GPT Image 1.5 is the new photorealism champion** — Justin: "quality of the images is amazing"

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
- **GPT Image 1.5** is the new photorealism champion (scored 89-90 on motorcycle, Justin: "quality is amazing")
- **FLUX 2 Flex g7.0** remains valid as cheaper alternative (scored 90-96, $0.05/MP vs ~$0.10-0.20 GPT)
- **Ref C (J&Mike Dual)** is the production reference photo (works with both GPT Image 1.5 and FLUX)
- **Reinforced prompt** with "OVER jacket sleeve," "halfway between wrist and elbow," "velcro strap wrapped fully around" — fixes bare skin, above-elbow, and missing strap problems
- **Scene-first prompts** with specific camera/lens language produce the most photographic results
- **Two-pass** works for adding helmets and earbuds to winning images (confirmed again this session)
- **Gen-4 Turbo** (97) and **Gen-4.5** (94) are the production video models
- **Generate-and-filter with human review** is the only reliable quality gate
- **T-shirt bleed largely solved by prompting** — including "leather riding jacket" in prompt gets proper gear without needing jacket-specific reference photos

### Open Problems
- **Above-elbow placement:** Still happens ~30-50% of the time even with "halfway between wrist and elbow" reinforcement. Justin's #1 complaint.
- **Symbol clarity:** GPT Image 1.5 sometimes renders warped/unclear button symbols (Justin: "symbols are a little wart")
- **Button count accuracy:** GPT Image 1.5 night scene generated 7-8 buttons instead of 5. Adding "five round tactile buttons" helps but not always.
- **Colorway control:** No reliable way to specify Hunter/Tron/Patriot from prompt alone. Fix requires colorway-specific reference photos.
- **Hunter symbol fidelity:** All existing Hunter reference photos have old/faded symbol outlines and missing LED plastic.
- **Patriot coverage:** Zero third-person Patriot photos exist anywhere.

### Latest Test Batch (April 7 — 4 images awaiting review)
GPT Image 1.5 Round 2 with reinforced strap prompts (the most promising batch yet):
- **gpt-coastal-v2-8501**: PCH golden hour, leather jacket, CB2 with strap visible, 5 buttons, lower forearm
- **gpt-coastal-v3-8502**: Cliffside sunset, distressed leather, ocean below, CB2 with strap wrapping around arm
- **gpt-desert-v2-8503**: Red rock mesas, dusty textile jacket, strap clearly visible, green buttons at mid-forearm — potentially best GPT 1.5 image yet
- **gpt-forest-8504**: Pine forest morning mist, dark jacket, CB2 green buttons on lower forearm, editorial vibe

### April 7 Session Results (This Session)

**Model Comparison (4-way head-to-head, same prompt + Ref C):**
| Model | Endpoint | Cost | Justin's Verdict |
|-------|----------|------|-----------------|
| FLUX 2 Flex g7.0 | `fal-ai/flux-2-flex/edit` | $0.05/MP | "Looks like a painting in a bad way, no CB visible" |
| FLUX 2 Pro | `fal-ai/flux-2-pro/edit` | $0.03/MP | "Looks inspiring but CB2 flipped perpendicular" |
| FLUX 2 Max | `fal-ai/flux-2-max/edit` | $0.07/MP | "Would be really cool if CB was below elbow" |
| **GPT Image 1.5** | `fal-ai/gpt-image-1.5/edit` | ~$0.10-0.20 | **"Quality of images is amazing. Remote preserved."** |

**GPT Image 1.5 Deep Dive (8 images, 2 rounds):**
- Round 1 (basic reinforcement): Coastal 90, Desert 89, Alpine fail (above elbow), Night 0 (wrong product)
- Round 2 (strap + button count reinforcement): 4 images awaiting review — look very strong

**FLUX 2 Flex Motorcycle Batch (6 images):**
- Desert 8104 strongest ("Strong. Right spot."), others had above-elbow or sleeve issues
- Key learning: including "leather jacket" and "helmet" in prompt gets proper motorcycle gear ~83% of the time

**Two-Pass Tests (2 images):**
- Sunrise + helmet: CB2 survived, helmet added naturally, but above elbow
- Alpine + earbuds: CB2 survived, earbuds not visible under helmet

### Next Session Priorities
1. **Justin reviews 4 GPT Image 1.5 Round 2 images** — desert v2 and coastal v2/v3 look very promising
2. **Generate more GPT Image 1.5 images** if round 2 scores well — scale up the winning prompts across more scenes
3. **Test GPT Image 1.5 on other sports** (skiing, snowboard, MTB) — only tested motorcycle so far
4. **Jordan shoots 7 reference photos** — 3 Hunter + 3 Patriot + 1 Tron winter. See jordan-shot-list.html
5. **Build CREATE tab** — sport/colorway/vibe dropdowns → auto-generate → review page
6. **Scale video production** — animate approved stills only with Gen-4 Turbo
7. **Cancel Recraft subscription** ($25/mo, never used)
8. **Fix feedback sync** — SYNC_URL points to wrong webhook (plan exists in luminous-bubbling-candy.md)
9. **Test Nano Banana Pro** (`fal-ai/nano-banana-pro/edit`) — reasoning-based, supports 14 refs, $0.15/image, untested

### Key Resources
| Resource | Location |
|----------|----------|
| Review page | https://jbarad424.github.io/ideas/cb-review.html |
| Jordan's shot list | https://jbarad424.github.io/ideas/jordan-shot-list.html |
| Feedback JSON | https://jbarad424.github.io/ideas/cb-feedback.json |
| Notion status | https://www.notion.so/33af45bfc038813f8b09f0d6efdffc49 |
| Google Drive | CB2 AI Generated Photos (4 quality-tier subfolders) |
| Memory files | ~/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas/memory/ |
| Make.com sync webhook | https://hook.us1.make.com/p3bt4ga6npqjs3608t9aou45qq1m5amh |

### Sports Priority
| Sport | Status | Notes |
|-------|--------|-------|
| Motorcycle coastal | **Best sport** (90 GPT, 98 Flex) | GPT Image 1.5 producing magazine-quality shots. Helmet/jacket via prompting works. |
| Skiing | Production-ready (96) | Needs GPT Image 1.5 testing. Needs gloves in ref photo. |
| Snowboard | Production-ready (96-100) | Strong with Flex g7.0. Needs GPT Image 1.5 testing. |
| MTB | Cracked (94-98) | Recently jumped from avg 34 to 94+. Needs GPT Image 1.5 testing. |
| Hiking | Deprioritized | "People have headphones, don't need CB2 for hiking" — Justin |
| Running | Deprioritized | Not core use case (no gloves needed) |
| Fishing/ATV | Dropped | Not enough demand |
