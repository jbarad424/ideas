# CB2 AI Creative Lab

## 1. Project Overview

AI product photography pipeline for Chubby Buttons CB2 — a wearable Bluetooth remote with 5 tactile buttons, worn on the forearm. We generate lifestyle marketing photos and videos of the CB2 on people doing action sports (motorcycle, skiing, snowboard, MTB). Justin Barad is co-founder; Jordan handles product photography. After testing 15+ approaches across 300+ images, the winning pipeline is reference-photo editing on FLUX 2 Flex with a generate-and-filter strategy — Justin reviews everything by eye.

## 2. What Works (Production Pipeline)

### Step 1: Generate
- **API:** `POST https://fal.run/fal-ai/flux-2-flex/edit`
- **API key:** stored in `~/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas/memory/project_architecture.md`
- **Reference photo:** J&Mike Dual (Ref C) — Drive ID `1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7`
- **URL:** `https://lh3.googleusercontent.com/d/1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7=w800`
- **Key setting:** `guidance_scale: 7.0` (scored 96-100, 33% cheaper than Pro)
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

### Prompt Templates
- Motorcycle: `Person on motorcycle on coastal mountain road, wearing the wearable remote from image 1 on their LEFT forearm, volume-up button closest to wrist, waist-up, golden hour, adventure photography`
- Skiing: `Skier on snowy mountain slope, bright ski jacket, wearing the wearable remote from image 1 on their LEFT forearm over jacket sleeve, volume-up button closest to wrist, waist-up, bright winter day`
- Snowboard: `Snowboarder on powder slope, colorful winter gear, wearing the wearable remote from image 1 on their RIGHT forearm over jacket sleeve, volume-down button closest to wrist, waist-up, mountain backdrop`
- MTB: `Mountain biker on dusty forest trail, wearing the wearable remote from image 1 on their LEFT forearm, volume-up button closest to wrist, waist-up, action sports photography`

NOTE: These templates are locked for now (used as controlled variables during testing). A style/mood variation test is pending before opening up the creative bookends (lighting, camera style, mood descriptors). Do not vary them without running that test first.

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

### Key Stats (April 7, 2026)
- 300+ images generated, 270+ reviewed
- 41 scored 90+, best: 100 (snowboard), 98 (motorcycle, MTB, skiing)
- Orientation correct 65-70% with Ref C + arm rules
- 13 test videos across 6 models
- FLUX 2 Flex g7.0 validated as production model (90-96 scores, $0.02/MP)

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
- **FLUX 2 Flex g7.0** is the production model (scored 90-96 across 20 images, 33% cheaper than Pro)
- **Ref C (J&Mike Dual)** is the production reference photo (65-70% correct orientation)
- **Scene-first simple prompts** produce the best results
- **Two-pass** works for adding helmets and earbuds to winning images
- **Gen-4 Turbo** (97) and **Gen-4.5** (94) are the production video models
- **Generate-and-filter with human review** is the only reliable quality gate

### Open Problems
- **T-shirt bleed:** J&Mike wearing T-shirts → generated people often lack sport-appropriate gear. Fix requires sport-specific reference photos with correct clothing.
- **Colorway control:** No reliable way to specify Hunter/Tron/Patriot from prompt alone. Multi-ref (J&Mike + colorway close-up) partially transfers color but doesn't improve orientation. Fix requires colorway-specific third-person reference photos.
- **Hunter symbol fidelity:** All existing Hunter reference photos have old/faded symbol outlines and missing LED plastic. Generated Hunter images inherit these flaws.
- **Patriot coverage:** Zero third-person Patriot photos exist anywhere.
- **Style variation untested:** Prompt templates use "golden hour" and "adventure photography" as controlled variables. Not yet validated whether other styles (blue hour, editorial, documentary) maintain the same CB2 hit rate.

### Next Session Priorities
1. **Jordan shoots 7 reference photos** — 3 Hunter (moto jacket, ski jacket, hiking gear) + 3 Patriot (same) + 1 Tron winter. Updated units with fresh symbols. Both arms. See jordan-shot-list.html.
2. **Build CREATE tab** — sport/colorway/vibe dropdowns → Make.com webhook → auto-generate → images appear in review page
3. **Run style/mood variation test** — 3 different lighting/camera combos × 5 seeds to validate whether creative bookends affect CB2 hit rate before opening up prompt templates
4. **Scale video production** — animate approved stills only with Gen-4 Turbo
5. **Cancel Recraft subscription** ($25/mo, never used)

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
| Motorcycle coastal | Production-ready (98) | Best sport, needs helmet via two-pass |
| Skiing | Production-ready (96) | Needs gloves in ref photo |
| Snowboard | Production-ready (96-100) | Strong with Flex g7.0 |
| MTB | Cracked (94-98) | Recently jumped from avg 34 to 94+ |
| Hiking | Deprioritized | "People have headphones, don't need CB2 for hiking" — Justin |
| Running | Deprioritized | Not core use case (no gloves needed) |
| Fishing/ATV | Dropped | Not enough demand |
