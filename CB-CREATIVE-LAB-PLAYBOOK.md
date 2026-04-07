# CB Creative Lab: The Complete AI Product Photography Playbook

**A step-by-step consulting guide for building an AI-powered marketing image pipeline for physical consumer products**

**Author:** Justin Barad, Chubby Buttons
**Version:** 2.0 — April 2026 (REVISED: Reference-First Architecture)
**Case study product:** Chubby Buttons 2 (CB2) — a wearable Bluetooth remote with 5 tactile buttons, worn on the forearm

---

> **CRITICAL UPDATE (v2.0):** This playbook was originally built around LoRA-first architecture. After testing, we discovered that diffusion models have a fundamental inability to count (exact accuracy < 23% per academic research). The revised architecture is **reference-first editing with LoRA as fallback.** The original LoRA sections remain valuable as the fallback layer. See Section 13 for the full revised architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Platform Selection Journey](#2-platform-selection-journey)
3. [Training Data Strategy](#3-training-data-strategy)
4. [Caption Writing Strategy](#4-caption-writing-strategy)
5. [Training Configuration](#5-training-configuration)
6. [Pipeline Architecture](#6-pipeline-architecture)
7. [Rating & Feedback System](#7-rating--feedback-system)
8. [Cost Breakdown](#8-cost-breakdown)
9. Common Mistakes
10. Scaling as a Service
11. Tool Stack
12. What's Still Unsolved
13. [**REVISED: Reference-First Architecture (v2.0)**](#13-revised-reference-first-architecture)
9. [Common Mistakes & How to Avoid Them](#9-common-mistakes--how-to-avoid-them)
10. [Scaling This as a Service](#10-scaling-this-as-a-service)
11. [Tool Stack Summary](#11-tool-stack-summary)
12. [What's Still Unsolved](#12-whats-still-unsolved)

---

## 1. Project Overview

### What We're Building

An AI image generation pipeline that produces photorealistic marketing photos of a specific physical product — the Chubby Buttons 2 (CB2) wearable Bluetooth remote — placed in action sports contexts like skiing, snowboarding, mountain biking, and motorcycling.

CB2 is a small device (roughly credit-card sized, slightly thicker) with a very specific set of visual features that make accuracy critical:

- Exactly 5 large raised tactile silicone buttons arranged in a specific layout
- Green/teal icon accents on each button (play/pause, skip forward, skip back, volume up, volume down)
- "CB2" logo on the front face
- Matte black silicone body (primary colorway), with olive/green and patriot variants
- Elastic armband with "chubby buttons" text on the strap
- USB-C port and Bluetooth pairing button on the edge
- Magnetic mount plate on the back

Every single one of these details matters. If the AI generates a remote with 4 buttons, or 6 buttons, or the wrong icon layout, or no logo — the image is unusable. This is the fundamental challenge of AI product photography: the bar for accuracy is not "looks cool" but "would you put this on your website without anyone noticing it's AI-generated."

### Why This Matters

Traditional product photography for action sports requires:

- Hiring professional photographers ($500-2,000/day)
- Booking athletes/models ($200-1,000/day)
- Travel to locations (mountains, trails, beaches)
- Equipment rental
- Post-production editing
- Weather dependencies and scheduling logistics
- A single shoot produces 20-50 usable images, many of which are similar

A working AI pipeline eliminates all of that. Once the model is trained:

- Generate unlimited variations on demand
- Test any sport, any location, any lighting condition, any colorway
- Iterate in minutes instead of months
- Cost per image drops to pennies

### The End Goal

Images accurate enough to post on the Chubby Buttons website, Instagram, Amazon listing, and paid ads without any viewer being able to tell they were AI-generated. The bar is not "cool AI art." The bar is "indistinguishable from a professional product photoshoot."

We are not there yet. This document captures every step of the journey, including the wrong turns, so you can get there faster with your own product.

---

## 2. Platform Selection Journey

### Phase 1: Image-to-Image (FLUX Kontext) — FAILED

Our first approach was the intuitive one: take an existing product photo, feed it into an image-to-image model, and ask it to place the product in a new scene.

We tried FLUX Kontext Pro on Replicate. The results were instructive in their failure:

**For product-on-white shots (flat-lays):** The model could reproduce something vaguely remote-shaped, but it would copy the reference image almost verbatim — same angle, same lighting, boring. It was a fancy copy machine, not a creative tool. The output looked like a slightly degraded version of the input photo.

**For action shots (product on a person in a scene):** This is where the approach completely fell apart. When you ask the model to place a small product on someone's arm while they're skiing down a mountain, the product either vanishes entirely, becomes an unrecognizable blob, or mutates into something with the wrong number of buttons. The model has no concept of what a CB2 "is" — it's just trying to blend pixels, and a 2-inch device on a forearm is simply too small a target for the model to preserve.

**The fundamental insight:** Image-to-image has a ceiling for small, detailed products. It works well for large, simple objects (a sneaker, a bottle, a backpack) where the object dominates the frame. For a small wearable with very specific details (5 buttons, specific icons, a logo), the model cannot maintain fidelity when the product becomes a small part of a larger scene. This is not a prompting problem — it is an architectural limitation of image-to-image approaches.

### The Pivot: LoRA Fine-Tuning

Jordan (co-founder and product lead) suggested we look into fine-tuning. Specifically, training a LoRA (Low-Rank Adaptation) model — a lightweight fine-tune that teaches a base model what our specific product looks like, so it can generate it from scratch in any context.

This was the right call. With a LoRA, the model doesn't need to "preserve" a reference image. It has learned the product's geometry, colors, button layout, and proportions as part of its internal representation. When you prompt it to generate a snowboarder wearing a CB2, it constructs the product from learned knowledge rather than trying to paste pixels from a reference.

### Why FLUX Over Stable Diffusion

We chose FLUX.1-dev as the base model for LoRA training. The reasons:

1. **Photorealism:** FLUX produces noticeably more photorealistic output than Stable Diffusion XL. For product marketing, "photorealistic" is the only acceptable quality level.
2. **Prompt adherence:** FLUX follows detailed prompts more faithfully, which matters when you're specifying exact product details.
3. **Resolution and detail:** Better fine detail preservation at inference time.
4. **Ecosystem:** The FLUX LoRA training pipeline on Replicate is well-tested and documented via the ostris/flux-dev-lora-trainer.

Stable Diffusion remains a valid choice if you need maximum community support or are working with very constrained budgets, but for product photography, FLUX's realism advantage is decisive.

### Replicate as the Training Platform

We use Replicate (replicate.com) for both training and inference. The reasons:

- **API-first:** Everything is accessible via API, which lets us build automation around it.
- **H100 GPUs:** Training runs on NVIDIA H100 GPUs, the fastest available. A full training run completes in 30-45 minutes.
- **Pay-as-you-go:** No monthly commitment for GPU time. You pay per second of compute.
- **Reasonable cost:** A full LoRA training run costs approximately $4-5. This is remarkably cheap compared to alternatives.
- **Private models:** Trained models can be kept private, which matters for competitive reasons.
- **Replicate username:** jbarad424, model name: cb2-lora (private).

### Higgsfield.ai Evaluation

Jordan also suggested we evaluate Higgsfield.ai, which takes a different approach: single-reference-photo compositing. You give it one product photo and a scene description, and it composites the product into a generated scene.

**How it differs from LoRA:** Higgsfield does not "learn" your product through fine-tuning. It takes one reference photo and attempts to blend it into a new scene at inference time. Think of it as sophisticated cut-and-paste with AI-powered blending, rather than the model understanding what your product actually is.

**Our assessment:**
- Works well for larger, simpler products (bottles, sneakers, bags) where the compositing target is large enough to preserve detail.
- Struggles with CB2's fine details — the 5 specific buttons, the small icons, the logo text. When compositing a small wearable, the fine details get smeared or lost.
- The motorcycle product placement demo looked surprisingly close to the actual product — worth testing for specific use cases.

**Decision:** Use Higgsfield as a downstream tool, not a replacement. LoRA gives us product accuracy. Higgsfield could be used to take an accurate LoRA-generated product shot and composite it into a more complex video scene or advertisement. They solve different problems.

**Higgsfield pricing:** $9-125/month plans, 15-70 credits per generation. API exists but product placement features may be UI-only at time of evaluation.

---

## 3. Training Data Strategy

**This is the most critical section of this entire document.** If you get the training data wrong, nothing else matters. Your LoRA will learn the wrong thing, and no amount of prompt engineering or parameter tuning will fix it.

### The Story of Getting It Wrong Three Times

#### v1: 13 images, auto-captioned

Our first training set was 13 images scraped from the Chubby Buttons website and marketing materials. They were mostly wide-angle action shots — snowboarders on mountains, skiers in powder, lifestyle shots where the product was a tiny detail on someone's arm.

**What the model learned:** "Outdoor vibes." Snow. Mountains. People wearing winter gear. The model had no idea what a CB2 remote actually looked like because the product was approximately 50 pixels wide in most training images.

**Result:** Generated images showed vaguely remote-shaped blobs with the wrong number of buttons (3, 4, 6, 7 — never consistently 5), wrong proportions, no recognizable logo, and no consistent color scheme. The model had learned "winter sports advertising aesthetic" not "the Chubby Buttons 2 product."

**Score from Justin:** 5 out of 100. "Vaguely remote-shaped."

#### v2: 28 images, manually captioned

We added 15 more images and wrote manual captions for all 28. The captions specified button count, logo, and colors. We thought this would fix the problem.

**What improved:** The model started generating something that looked more like a remote control. Button count became more consistent (though still wrong about half the time). The shape was closer to correct.

**What didn't improve:** The model still couldn't get all 5 buttons right in most generations. The detail-level accuracy was still too low because the majority of training images were still wide-angle shots where the product was small.

**Result:** Better, but still not website-quality. Maybe 10-15 out of 100.

#### v3a: 37 images including website product shots

We added 9 product shots directly from the chubbybuttons.io website — clean, close-up product photos on white backgrounds. This brought the total to 37 images with manual captions.

**What improved dramatically:** In close-up product shots, the model now consistently generated 5 buttons. The shape, proportions, and color scheme were recognizably CB2. This proved the hypothesis — the model CAN learn these details, but only if you show them to it at a scale where it can actually see them.

**What still failed:** Action shots. When the product was small in a wider scene, accuracy dropped right back to garbage. The model could render an accurate product when it was the entire frame, but not when it was a forearm accessory in a skiing scene. Still scored only 5-6 usable images out of 100 generated.

#### v3b: Same data, higher training parameters

We re-trained on the same 37 images but increased the LoRA rank from 16 to 32 and the step count to 2,500. The theory was that a higher-rank LoRA could capture more fine-grained detail.

**Result:** Marginal improvement. The best close-up shots were slightly sharper and more accurate. But the fundamental problem remained — the training data was still biased toward wide-angle shots, and no amount of parameter tuning can fix a data problem.

**Scores:** 5-6 usable images out of 100 generated. Roughly the same as v3a.

#### v4: 38 NEW close-up photos — the breakthrough approach

After three iterations of incremental improvement, we finally embraced the painful truth: the training data needed to be fundamentally restructured, not incrementally improved.

Justin photographed 38 brand-new images in a studio lightbox setup. The critical change: **35 of 38 images (92%) show all 5 buttons clearly visible.** The ratio flipped from 80% wide-angle / 20% close-up to 92% close-up / 8% contextual.

**Photo breakdown by category:**

| Category | Count | Notes |
|---|---|---|
| On-arm (ski glove) | 11 | Horizontal orientation, studio lightbox, all 5 buttons visible |
| Product close-up | 8 | 5 waterproof demos, 3 magnetic mount lifestyle shots |
| Multi-device | 6 | Colorway comparisons (olive/green + black side by side) |
| Product standing | 4 | Vertical orientation, logo and strap visible |
| Lifestyle/mounted | 4 | Kitchen, bathroom, living room, game room contexts |
| Product with accessory | 2 | Shown next to headphones, ski goggles |
| Back view | 2 | Magnetic plate, USB-C port, strap slots visible |
| Side view | 1 | Olive/green colorway, side profile |

**Colorway distribution:** 34 black, 3 olive/green (1 solo, 2 in multi-device shots). This was intentional — the black colorway is the primary product, so the model should know it best.

**Key details captured across the set:**
- USB-C charging port
- Bluetooth pairing button
- Magnetic mount system
- Elastic strap with "chubby buttons" branded text
- Green/teal icon accents on every button
- CB2 logo on front face
- Product from every angle (front, back, sides, top, bottom)

**Training status:** v4 training set was built (38 images + 38 manual captions = 76 files, 5.3MB zipped) and is ready for Replicate upload. This is the training run we expect to produce the first website-quality results.

### The Rules for Training Data (What We Learned the Hard Way)

1. **At least 70% of your images should be close-ups where the product fills most of the frame.** Not 20%. Not 50%. At least 70%. The model needs to see your product's details at a scale where individual features (buttons, logos, ports, textures) are clearly visible. Wide-angle action shots are almost useless for teaching the model what your product looks like.

2. **Photograph every angle.** Front, back, left side, right side, top, bottom, three-quarter views. The model needs to learn the product's 3D geometry, not just one flat face.

3. **Photograph every colorway.** If you have 3 SKUs, photograph all 3. Weight the training set toward your primary colorway (we used roughly 90% black, 10% olive/green).

4. **Include on-body/worn shots.** For wearables, show the product on an arm, wrist, or wherever it's worn. The model needs to learn what the product looks like in context, not just floating in space. But make sure the product is still large and clear in these shots.

5. **Show product with accessories.** If your product is used alongside other items (headphones, goggles, gloves), include a few shots showing the product next to or with those accessories.

6. **Capture detail shots.** Ports, buttons, logos, textures, closures, clasps — anything that makes your product unique. Photograph these at macro/close-up distance.

7. **Vary lighting conditions.** Include shots in studio lighting, natural light, warm light, cool light. This teaches the model how the product's materials respond to different lighting.

8. **Include waterproof/durability demos if relevant.** We included shots of the CB2 in water splashes. These are unusual angles and conditions that add variety to the training set.

9. **Minimum 20 images, ideal 30-50.** Below 20 and the model won't have enough examples to generalize. Above 50 and you start getting diminishing returns (and longer training times). The sweet spot for most products is 30-40 images.

10. **Use full-resolution originals.** Don't pre-resize your photos. The Replicate trainer handles resizing internally and trains at multiple resolutions (512, 768, 1024). Give it the best quality source material.

---

## 4. Caption Writing Strategy

Captions are the text descriptions paired with each training image. They tell the model what it's looking at in each photo, and they determine how the model connects the trigger word to visual features. Bad captions produce a bad model, even with great images.

### The Rules

**Rule 1: Every caption starts with the trigger word.**

The trigger word is a unique, non-real-word identifier that the model associates with your product. We use `CB2REMOTE`. Not "remote control" (too generic, would conflict with the model's existing concept of remote controls). Not "chubby buttons" (could conflict with other meanings). A made-up compound word that exists nowhere in the base model's training data.

Good: `CB2REMOTE wearable Bluetooth device on a skier's forearm...`
Bad: `A wearable remote control device on a skier's forearm...`

**Rule 2: Every caption must describe the exact product details.**

Do not write vague captions. Every caption should include the specific details that make your product unique. For CB2, every caption includes:

- "5 large raised tactile buttons"
- The specific button icons (play/pause, skip forward, skip back, volume up, volume down)
- "CB2 logo on front"
- The colorway ("black matte silicone body" or "olive green body")
- "elastic armband" or "wearable strap"

The model learns the association between these text descriptions and the visual features in the photos. If you write "a device on an arm," the model learns nothing specific. If you write "CB2REMOTE, a compact black matte silicone wearable Bluetooth remote with 5 large raised tactile silicone buttons with green/teal icons (play/pause, skip forward, skip back, volume up, volume down), CB2 logo on front face, elastic armband," the model learns exactly what those features look like.

**Rule 3: Include scene context.**

Describe what's happening in the photo beyond just the product. What surface is it on? What orientation? What's in the background? Is it on someone's arm? This helps the model generate appropriate scenes at inference time.

Example: `CB2REMOTE, a compact black matte silicone wearable Bluetooth remote with 5 large raised tactile silicone buttons with green/teal icons, CB2 logo on front face, strapped over a ski glove on the left forearm, horizontal orientation, studio lightbox lighting, white background`

**Rule 4: 30-60 words per caption.**

Too short (under 15 words) and the model gets no useful information. Too long (over 80 words) and the model may struggle to learn associations. The sweet spot is 30-60 words of dense, specific description.

**Rule 5: Do NOT use autocaption.**

The Replicate trainer has an autocaption option that uses a vision model to automatically describe your images. Do not use this. The vision model does not know your product. It will describe a CB2 as "a black rectangular electronic device" or "a remote control with buttons." It will not know there are exactly 5 buttons, will not know the icon names, will not know the brand name, will not know the colorway names.

Autocaption produces generic descriptions. Generic descriptions produce a generic model. Write every caption by hand. It takes 30-60 minutes for a 40-image training set. That time investment is trivially small compared to the hours you'll waste training on bad captions and generating unusable images.

**Rule 6: Set caption dropout to 0.05 (5%).**

Caption dropout means that 5% of the time during training, the model trains on an image without its caption. This forces the model to learn visual features independently of the text, which improves generalization. The model learns "what this thing looks like" in addition to "what this thing looks like when described as X." A dropout of 0.05 is the standard recommendation and we haven't found a reason to change it.

### Example Captions from Our v4 Training Set

```
CB2REMOTE, a compact black matte silicone wearable Bluetooth remote with 5 large raised
tactile silicone buttons with green/teal icons (play/pause, skip forward, skip back,
volume up, volume down), CB2 logo on front face, strapped horizontally over a black
ski glove on the forearm, studio lightbox lighting, white background
```

```
CB2REMOTE, back view of the compact black matte silicone wearable Bluetooth remote
showing the magnetic mounting plate, USB-C charging port, Bluetooth pairing button,
and strap attachment slots, placed on a white surface, studio lighting
```

```
CB2REMOTE, olive green matte silicone wearable Bluetooth remote standing upright on
a white surface next to a black CB2REMOTE, both showing 5 large raised tactile buttons
with teal icons, side by side colorway comparison, studio lighting
```

---

## 5. Training Configuration

### Platform and Model

- **Platform:** Replicate (replicate.com)
- **Trainer:** ostris/flux-dev-lora-trainer (community-maintained, well-tested)
- **Base model:** FLUX.1-dev (Black Forest Labs)
- **Account:** jbarad424 on Replicate
- **Trained model:** jbarad424/cb2-lora (private)

### Parameters

| Parameter | Value | Why |
|---|---|---|
| **Trigger word** | `CB2REMOTE` | Unique, non-real-word. The model has no pre-existing concept of this term, so it learns to associate it purely with your training data. |
| **LoRA rank** | 32 | Higher rank = more capacity to learn fine details. Rank 16 was noticeably worse at button accuracy. Rank 32 captures the difference between 4 and 5 buttons. Rank 64 would add training time with diminishing returns for this dataset size. |
| **Steps** | 2500 | For 30-40 images, 2500 steps provides enough passes through the data for the model to learn without overfitting. Fewer steps (1000) produced undertrained results. More steps (4000+) risk overfitting — the model starts memorizing training images instead of generalizing. |
| **Learning rate** | 0.0003 | Standard for FLUX LoRA training. We did not experiment with this. |
| **Batch size** | 1 | Standard for single-GPU LoRA training. Larger batch sizes require more VRAM. |
| **Resolution** | 512, 768, 1024 | Multi-resolution training. The model learns your product at multiple scales, which helps it render the product accurately whether it's the main subject or part of a larger scene. |
| **Autocaption** | false | Critical when providing custom captions. If set to true, the trainer will overwrite your captions with generic auto-generated ones. |
| **Caption dropout** | 0.05 | 5% of training steps use the image without its caption, improving visual generalization. |

### Cost and Time

- **Cost per training run:** ~$4-5 on H100 GPU via Replicate
- **Training time:** ~30-45 minutes
- **Total training investment across 4 runs (v1, v2, v3a/b):** ~$16
- **Estimated v4 training cost:** ~$4-5

### How to Upload Training Data to Replicate

1. Prepare a ZIP file containing paired images and captions. For each image `photo_01.jpg`, there should be a corresponding `photo_01.txt` file with the caption.
2. Go to replicate.com, navigate to your model page (or create a new model).
3. Start a new training run using the ostris/flux-dev-lora-trainer.
4. Upload the ZIP file as the input data.
5. Set the trigger word, rank, steps, learning rate, and other parameters as specified above.
6. Start training. You'll receive a notification when it completes.
7. The trained LoRA weights are automatically saved to your Replicate model.

### How to Generate Images with the Trained Model

Once training is complete, you can generate images via the Replicate API or web interface:

```
POST https://api.replicate.com/v1/predictions
Headers:
  Authorization: Bearer r8_YOUR_TOKEN
  Content-Type: application/json
  Prefer: wait=60

Body:
{
  "version": "YOUR_MODEL_VERSION_HASH",
  "input": {
    "prompt": "CB2REMOTE, a compact black wearable Bluetooth remote with 5 tactile buttons, strapped over a ski jacket forearm, snowboarder carving through fresh powder, mountain peaks in background, golden hour lighting, action sports photography",
    "num_outputs": 1,
    "guidance_scale": 3.5,
    "num_inference_steps": 28
  }
}
```

The `Prefer: wait=60` header is important — it tells Replicate to hold the HTTP connection open for up to 60 seconds and return the result synchronously instead of requiring you to poll for completion. This simplifies pipeline architecture significantly.

---

## 6. Pipeline Architecture

### Overview

The complete pipeline has these stages:

```
Prompt → Replicate API (generate image) → Google Drive (store image)
    → Claude Vision API (AI scoring) → Data Store (metadata)
    → Web App (human rating) → Feedback Analysis → Improved Prompts
    → Back to Prompt (the loop closes)
```

### Components

#### Web App (Asset Tagger v2)

A static HTML/CSS/JS single-page application hosted on GitHub Pages (free). The app provides:

- **Name selection:** Team members (Justin, Jordan, Michael, Slava) each log in with their name. Ratings are tracked per-person.
- **Swipe mode:** Tinder-style card interface. See an AI-generated image, view the AI's assessment scores, then Agree or Disagree.
- **Grid mode:** Gallery view of all generated images with filtering.
- **Create mode:** (Planned) Interface to describe a scene and generate new assets directly.
- **Training gate:** A boolean flag (`MODEL_TRAINING_IN_PROGRESS`) that blocks the Create mode when a new model is being trained. Shows a banner explaining what's happening and what lessons were learned from previous iterations.

The app loads image data from a JSON file (`cb-ai-lab.json`) hosted on the same GitHub Pages site. Ratings are stored locally in localStorage and synced to the backend via Make.com webhooks.

**Live URLs:**
- App v2: `https://jbarad424.github.io/ideas/asset-tagger-v2.html`
- Evolution dashboard: `https://jbarad424.github.io/ideas/cb-evolution.html`
- JSON data: `https://jbarad424.github.io/ideas/cb-ai-lab.json`

#### Make.com Webhooks for Orchestration

Make.com (formerly Integromat) serves as the orchestration layer. It connects the generation, storage, scoring, and feedback systems via webhook-triggered scenarios.

**Active scenarios:**

| Scenario | ID | Function |
|---|---|---|
| LoRA Generate v2 (Smart Polling) | 4655593 | Receives generation requests, calls Replicate API, stores result in Google Drive |
| Rate Image | 4653738 | Receives rating data from the web app, stores in data store |
| Sync JSON | 4654266 | Syncs data store to the GitHub-hosted JSON file |
| Vision Co-Rater | 4654454 | Sends generated images to Claude Vision API for automated scoring |

**Legacy scenarios (still active but not primary):**

| Scenario | Function | Status |
|---|---|---|
| FLUX Generate | Original image-to-image pipeline | Superseded by LoRA |
| Recraft Generate | Alternative generation engine | Failed in batch test |
| Runway Video | Video generation | Failed in batch test |

#### Replicate API for Generation

The LoRA generation scenario calls the Replicate predictions API with the trained model version. The critical implementation detail is the `Prefer: wait=60` header.

**Without this header:** You submit a prediction, get back a prediction ID, and then must poll `GET /v1/predictions/{id}` every few seconds until status changes from "processing" to "succeeded." This polling is where bugs hide.

**With this header:** The initial POST request blocks for up to 60 seconds. If the image generates within 60 seconds (most do, typically 15-30 seconds), the response contains the completed prediction with the output URL. No polling needed. If it takes longer than 60 seconds, you get back a "processing" status and fall back to polling.

#### Google Drive for Image Storage

Generated images are uploaded to a Google Drive folder using Make.com's Google Drive module. Each image gets a unique file name and a Drive file ID that's stored in the data store. The web app loads images directly from Google Drive using thumbnail URLs: `https://drive.google.com/thumbnail?id={fileId}&sz=w800`.

**Google Drive connection:** Connection ID 4724749 (justin@chubbybuttons.io).

#### Claude Vision API for Automated Scoring

Every generated image is sent to Claude's vision API (Anthropic) for automated quality assessment. Claude evaluates each image on three dimensions:

1. **Product Accuracy (1-5):** Does the product look like an actual CB2? Correct button count, proportions, colors, logo?
2. **Scene Quality (1-5):** Is the scene realistic, well-lit, properly composed? Any AI artifacts?
3. **Brand Alignment (1-5):** Does the image feel like a Chubby Buttons marketing photo? Right energy, right audience, right vibe?

Claude also generates a brief text assessment explaining its scores.

The AI scores serve as a first-pass filter and calibration tool. They do not replace human judgment — they accelerate it. A human reviewer can quickly scan 50 images by checking AI scores first and spending more time on borderline cases.

### The Polling Bug (and How We Fixed It)

This is worth documenting because it's the kind of bug that will bite anyone building async pipelines on Make.com.

**The original implementation (broken):**

1. POST to Replicate API to start generation
2. Sleep 60 seconds (Make.com sleep module)
3. GET the prediction status
4. Sleep 15 seconds
5. GET the prediction status again
6. Download the output URL

**What went wrong:** If the Replicate prediction took longer than 75 seconds (total sleep time), both GET requests returned `"status": "processing"` and there was no output URL yet. But the scenario continued to the download step anyway and attempted to download from a null/missing URL — producing garbage data or errors that were silently swallowed.

**The fix (deployed in scenario 4655593):**

1. POST to Replicate API with `Prefer: wait=60` header (blocks up to 60s, often returns the completed result immediately)
2. **Router module** checks the response:
   - If `status === "succeeded"` AND `output` array exists → proceed to download
   - If `status === "processing"` → poll attempt 1 (wait 20s, check status)
   - If still processing → poll attempt 2 (wait 20s, check status)
   - If still processing after ~100 seconds total → return error with prediction ID (human can check manually later)
3. Only download when status is definitively "succeeded"

**Key lesson:** Never download or process a result without explicitly checking that the upstream operation completed successfully. Sleep-then-assume-done is a recipe for garbage data.

### The Feedback Flywheel

The most valuable part of the pipeline is not any single component — it's the feedback loop that connects them:

1. **Generate** images with the current model and prompts
2. **AI scores** each image automatically (product accuracy, scene quality, brand alignment)
3. **Human rates** each image (Agree/Disagree with AI scores, plus feedback tags and notes)
4. **Analyze** the ratings: What types of images score well? What consistently fails? What specific issues recur?
5. **Improve prompts** based on analysis — add positive inversions for common failure modes, emphasize details that the model gets wrong
6. **If the model itself is the bottleneck** (wrong button count, wrong proportions), go back to step 0: improve training data and retrain
7. **Generate again** with improved prompts and/or improved model

This loop is what turns a mediocre AI pipeline into a progressively improving one. Each generation batch should be measurably better than the last. If it's not, you're not learning from the feedback.

---

## 7. Rating & Feedback System

### AI Vision Co-Rater

Every generated image is automatically sent to the Claude Vision API through the Vision Co-Rater Make.com scenario (ID 4654454). Claude evaluates the image and returns:

- **Product Accuracy (1-5):** 1 = product missing or unrecognizable, 5 = could pass for a real product photo
- **Scene Quality (1-5):** 1 = obvious AI artifacts, uncanny valley, 5 = photorealistic scene
- **Brand Alignment (1-5):** 1 = wrong aesthetic entirely, 5 = looks like a professional Chubby Buttons marketing image
- **Notes:** 2-3 sentences explaining the scores

The AI scores are displayed alongside each image in the rating app. The human reviewer sees the AI's assessment before making their own judgment.

### Human Rating Flow (Agree/Disagree)

The v2 app uses an Agree/Disagree model instead of traditional star ratings:

1. **Human sees the image** along with the AI's three scores and notes.
2. **Agree:** The human clicks Agree if the AI's assessment is roughly correct. The AI's scores are accepted as the final rating.
3. **Disagree:** The human clicks Disagree if the AI is wrong — either too generous or too harsh. A popup appears with:
   - **Negative feedback tags** (select all that apply):
     - Product issues: "Doesn't look like CB2," "Product floating/detached," "Product missing entirely," "Band looks wrong," "Wrong colorway shown," "Weird hands/fingers"
     - Scene issues: "AI artifacts visible," "Unrealistic/uncanny," "Boring/generic setting," "Bad lighting," "Wrong vibe for brand," "Scene too busy/cluttered"
   - **Free-text notes** for additional context

### Why Agree/Disagree Instead of Star Ratings

Traditional 1-5 star ratings are slow and inconsistent. Different people mean different things by "3 stars." The Agree/Disagree model is:

- **Faster:** Binary decision vs. picking a number on a scale
- **More informative when negative:** Disagreements come with specific tags explaining what's wrong
- **Calibrating:** Over time, the pattern of agreements and disagreements reveals whether the AI rater is systematically biased (e.g., always rates product accuracy too high)

### Positive Inversions for FLUX Prompts

FLUX does not support negative prompts (unlike Stable Diffusion). You cannot say "no floating product, no wrong button count." Instead, you must describe what you DO want more emphatically. We call these "positive inversions."

When a user tags a disagreement with a specific issue, the system stores a corresponding positive inversion that gets injected into future prompts:

| Disagreement Tag | Positive Inversion Added to Prompt |
|---|---|
| "Doesn't look like CB2" | "maintaining the exact same product proportions, button count, button layout, color, logo placement, and surface texture" |
| "Product floating/detached" | "product resting naturally and grounded with realistic shadow and physical contact" |
| "Product missing entirely" | "CB2REMOTE device clearly visible and prominently featured on the forearm" |
| "Band looks wrong" | "CB2 armband snugly strapped over jacket sleeve with realistic fabric interaction and visible velcro closure" |
| "AI artifacts visible" | "clean sharp details throughout with photorealistic rendering" |
| "Boring/generic setting" | "dramatic visually striking environment with depth and atmosphere" |
| "Bad lighting" | "professional cinematic lighting with natural light interaction on product surface" |

This creates a self-improving prompt system: the more images humans rate, the more specific and accurate the prompts become for future generations.

---

## 8. Cost Breakdown

### Direct Costs

| Item | Cost |
|---|---|
| Replicate LoRA training (4 runs: v1, v2, v3a, v3b) | ~$16 |
| Replicate test image generations (~20 images) | ~$1.50 |
| fal.ai testing (1 queue) | ~$0.02 |
| Pre-LoRA image-to-image generation (sessions 1-2) | ~$2 |
| **Total invested through v3b** | **~$20** |
| Estimated v4 training cost | ~$4-5 |
| **Projected total through v4** | **~$25** |

### Ongoing Costs

| Item | Cost | Notes |
|---|---|---|
| Make.com | $34/month | Includes all webhook scenarios, Google Drive integration, data stores |
| Replicate generation | ~$0.01-0.05/image | Pay-as-you-go, depends on resolution and inference steps |
| Claude Vision API (scoring) | ~$0.01-0.02/image | Per-image analysis call |
| GitHub Pages hosting | Free | Static HTML app hosting |
| Google Drive storage | Free | Images stored in existing Drive account |

### Comparison to Traditional Photography

| Traditional Photoshoot | Cost |
|---|---|
| Photographer (1 day) | $500-2,000 |
| Model/athlete (1 day) | $200-1,000 |
| Location/travel | $500-3,000 |
| Equipment rental | $200-500 |
| Post-production | $500-1,500 |
| **Total per shoot** | **$2,000-8,000** |
| **Usable images per shoot** | **20-50** |
| **Cost per usable image** | **$40-400** |

### ROI Math

If the AI pipeline produces even 5 website-quality images, it has paid for itself compared to a single professional photoshoot. At $25 total investment and $0.05 per generated image, you could generate 500 images for the cost of a single day's photography equipment rental.

The real ROI is in iteration speed. A photoshoot takes weeks to plan and execute. The AI pipeline generates new concepts in minutes. Even if only 5% of generated images are usable today, that percentage improves with every iteration of the feedback loop.

---

## 9. Common Mistakes & How to Avoid Them

### Mistake 1: Training on wide-angle action shots

**What happens:** The product is tiny in the frame. The model learns "outdoor sports aesthetic" instead of learning what your product actually looks like. You get beautifully generated ski scenes with an unrecognizable blob where the product should be.

**How to avoid it:** At least 70% of training images should be close-ups where the product fills most of the frame. Show the model every angle, every detail, every colorway up close before asking it to render the product at a distance.

### Mistake 2: Using autocaption

**What happens:** The autocaption model describes your product generically: "a black rectangular device with buttons." It doesn't know your product has exactly 5 buttons, specific icon names, a specific logo, specific colorway names. The trained model learns a generic "electronic device," not your specific product.

**How to avoid it:** Write every caption by hand. It takes 30-60 minutes for 40 images. Include every unique detail of your product in every caption. Start every caption with your trigger word.

### Mistake 3: Blind polling with sleep timers

**What happens:** You submit a generation request, sleep for 60 seconds, then try to download the result. If the generation took 90 seconds, you download nothing or garbage. If it took 10 seconds, you wasted 50 seconds waiting.

**How to avoid it:** Use the `Prefer: wait=60` header on Replicate API calls. Always check `status === "succeeded"` before downloading. Implement graceful fallback polling with explicit status checks at each step.

### Mistake 4: Celebrating "vaguely remote-shaped" output

**What happens:** After days of work, you generate an image that looks kinda-sorta like your product, and you feel accomplished. You share it with the team. Everyone says "that's cool!" You move on to generating more images at this quality level.

**How to avoid it:** The bar is not "vaguely correct." The bar is "would you put this on your product website without any disclaimer?" The customer browsing your website does not know or care that you used AI. They will judge the image by the same standard as a photograph. If the button count is wrong, the logo is missing, or the proportions are off, the image is unusable. Be honest about quality. Score ruthlessly.

### Mistake 5: Grading on a curve

**What happens:** Because AI image generation is hard, you start accepting lower quality. "Well, for AI, this is pretty good!" You compare to other AI-generated images instead of comparing to real product photography.

**How to avoid it:** Your competition is not other AI images. Your competition is a professional photographer with a $5,000 camera, a professional model, and a day at the ski resort. Grade against that. Justin's scoring rubric: "Would I put this on our website?" If no, the image scored zero, regardless of how impressive the AI's effort was.

### Mistake 6: Not checking prediction status before downloading

**What happens:** Your pipeline downloads whatever URL the API returns, regardless of whether the prediction actually completed. You end up with corrupted images, empty files, or error messages saved as image files in your Drive.

**How to avoid it:** Always have an explicit conditional check: Is `status === "succeeded"`? Does the `output` array exist and have at least one URL? Only then proceed to download.

### Mistake 7: Not tracking what you learn from each iteration

**What happens:** You train v1, generate images, say "those aren't great," train v2 with vaguely more data, generate again, say "still not great." You make the same mistakes across iterations because you never documented what specific aspect of the model was failing and what you tried to fix it.

**How to avoid it:** After every training run and every batch of generated images, write down: What specifically was wrong? What did we change? What was the hypothesis for why the change would help? What was the actual result? Justin's directive: "Every iteration must learn something — never waste tokens/credits without moving forward."

---

## 10. Scaling This as a Service

### What a Client Engagement Looks Like

This pipeline is productizable. Here is what a paid consulting engagement looks like, from first meeting to ongoing generation:

#### Phase 1: Onboarding (Week 1)

1. **Discovery call:** Understand the product, its unique visual features, target audience, and what kind of marketing images they need.
2. **Photo brief:** Send the client a detailed shot list based on the training data rules in Section 3. They need to photograph their product from every angle, every colorway, with accessories, in context, showing every detail. Minimum 30 images, ideal 40-50.
3. **Client shoots photos:** They can use a phone camera in a lightbox setup. Professional photography is nice but not required. What matters is that every product detail is clearly visible and well-lit.

#### Phase 2: Model Training (Week 2)

4. **Receive photos from client.** Review for completeness — are all angles covered? Are details visible? Are multiple colorways represented?
5. **Write captions.** You (the consultant) write every caption by hand, emphasizing the product's unique features. This requires you to understand the product deeply — study it, learn the feature names, understand the brand language.
6. **Train LoRA on Replicate.** ~$5, ~45 minutes. Use the configuration parameters from Section 5.
7. **Generate test images.** Run 20-30 test generations across different scenes and prompts.
8. **Score test images.** Be honest. If the product details are wrong, the training data needs improvement.
9. **Iterate if needed.** If the model isn't getting key details right, go back to step 4 and ask the client for more/better photos of the specific features that are failing. This may add a week.

#### Phase 3: Pipeline Setup (Week 2-3)

10. **Deploy rating app.** Clone the asset-tagger-v2 template, customize for the client's brand colors and team members.
11. **Set up Make.com scenarios.** Clone the generation, rating, sync, and vision scoring scenarios. Connect to the client's Google Drive.
12. **Configure positive inversions.** Set up the feedback tag system with product-specific disagreement options and positive inversions.
13. **Test end-to-end.** Generate an image, verify it appears in the app, rate it, verify the rating syncs.

#### Phase 4: Production (Ongoing)

14. **Generate marketing assets on demand.** Client requests specific scenes ("show the product on a cyclist," "try a beach volleyball setting"). You write prompts and generate batches.
15. **Client rates images.** Team members swipe through the rating app, providing feedback.
16. **Analyze feedback.** What's working? What's failing? Adjust prompts or retrain the model if needed.
17. **Deliver approved images.** Export high-rated images for the client's marketing team to use.

### Pricing Model Suggestions

| Service | Suggested Price | Justification |
|---|---|---|
| Initial setup (phases 1-3) | $1,000-2,500 | Includes photo brief, caption writing, LoRA training (1-2 iterations), pipeline setup, rating app deployment |
| Per-generation batch (20-50 images) | $100-250 | Prompt writing, generation, AI scoring, delivery |
| Monthly retainer (ongoing generation + iteration) | $500-1,500/month | Includes regular generation batches, feedback analysis, prompt optimization, periodic model retraining |
| Model retraining (when product changes) | $200-500 | New photos, new captions, new LoRA training |

### What Makes This Defensible

This is not just "I'll generate some AI images for you." The defensible value is in:

1. **The feedback loop.** Systematic Agree/Disagree rating with specific failure tags, positive inversions, and progressive prompt improvement. Most people using AI image generation throw prompts at a wall and hope. This is an engineered system that gets measurably better over time.

2. **The training data expertise.** Knowing that 70%+ of training images must be close-ups is knowledge that took 4 failed iterations and $20 to learn. A client trying this on their own would make the same mistakes.

3. **The pipeline.** Generation, storage, AI scoring, human rating, feedback analysis — this infrastructure takes days to build and debug (see: the polling bug). It's reusable across clients once built.

4. **The iteration process.** Knowing when to blame the prompts vs. when to blame the model vs. when to blame the training data. Knowing that autocaption is a trap. Knowing that rank 32 matters for fine detail. These are hard-won lessons that save clients weeks of dead ends.

---

## 11. Tool Stack Summary

| Tool | Purpose | Cost | Notes |
|---|---|---|---|
| **Replicate** | LoRA training + inference | Pay-as-you-go (~$5/training, ~$0.05/image) | H100 GPUs, API-first, private models |
| **Make.com** | Webhook orchestration | $34/month | Connects generation, storage, scoring, and feedback. Adequate but architecturally weak for async operations (sleep modules waste operations, no native "wait for callback"). |
| **GitHub Pages** | Static app hosting | Free | Hosts the rating web app and JSON data files |
| **Google Drive** | Image storage | Free (existing account) | Stores all generated images, accessible via thumbnail URLs |
| **Claude Vision API** | AI scoring | ~$0.01-0.02/image | Anthropic API, evaluates product accuracy, scene quality, brand alignment |
| **Higgsfield.ai** | (Optional) Scene compositing and video | $9-125/month | Downstream tool for compositing accurate product renders into video scenes. Not a LoRA replacement. |

### Future Considerations

**Cloudflare Workers + Workflows ($5/month):** If Make.com's async limitations become a bigger problem, Cloudflare Workers with durable execution Workflows would be a more reliable pipeline backbone. Workers can natively wait for webhook callbacks without wasting compute on sleep modules. Not urgent now that the polling fix is deployed, but the right long-term architecture for a more robust service.

**Replicate webhook callbacks:** Instead of polling or long-polling, Replicate can send a webhook when a prediction completes. This would eliminate all polling logic entirely. We haven't implemented this because the `Prefer: wait` header solved the immediate problem, but webhooks are the theoretically optimal approach.

---

## 12. What's Still Unsolved

### Getting from "recognizable product" to "photorealistic product in action scene"

The v3 models proved we can generate a recognizable CB2 in close-up product shots. The v4 training data should significantly improve this. But the final challenge remains: can the model render a photorealistic CB2 at a natural size on someone's forearm while they're skiing down a mountain, with correct button count, correct proportions, and correct colors — all at a size where the product is maybe 100-200 pixels of a larger image? This is the gap between "cool demo" and "usable marketing asset."

### Maintaining product accuracy at small sizes in wide shots

When the product is the full frame, accuracy is high. When the product is a small element of a wide action shot, accuracy degrades. This may be a fundamental limitation of the current generation of image models. Possible mitigations: generate the product as a close-up insert within a wider scene composition (two-pass generation), or use Higgsfield-style compositing to place an accurate product render into a separately generated scene.

### Video generation with accurate product

Runway and similar video models cannot maintain product-level accuracy across frames. A LoRA-trained still image model produces one frame of accuracy. Maintaining that across 60-120 frames of video, with motion, camera movement, and lighting changes, is a much harder problem. This is where Higgsfield's video capabilities may become valuable — using an accurate still render as input and animating the scene around it.

### The "last mile" of product detail accuracy

Even the best LoRA results occasionally get small details wrong — a button icon is slightly different, the logo text is slightly blurred, the strap texture doesn't quite match reality. For hero images on the product page, this may not be acceptable. For social media content, lifestyle blogs, or ad creative at scale, it may be "good enough." The question of where the quality threshold falls depends on the use case, and the answer will change as models improve.

### The honest assessment (as of April 2026)

We are not yet at the point where AI-generated images can replace a product photoshoot for hero website images. We are at the point where AI-generated images can supplement a photoshoot — generating concepts, testing scenes, producing social media content that doesn't need to withstand pixel-level scrutiny. The gap is closing with each model generation and each training iteration.

The v4 model, trained on 38 close-up product photos with meticulous manual captions, represents our strongest hypothesis yet. If it doesn't produce website-quality images, the next step is likely a different base model (FLUX 2, whenever it ships), higher-rank LoRA training, or a hybrid approach combining LoRA rendering with compositing tools.

What we know for certain: the approach works. The question is whether current-generation models can close the last-mile quality gap, or whether we need to wait for the next generation. Either way, the pipeline — the training data strategy, the feedback loop, the scoring system, the positive inversions — all of that transfers directly to better models when they arrive.

---

## Appendix A: File Locations & Resources

| Resource | Location |
|---|---|
| Rating app (v2) | `https://jbarad424.github.io/ideas/asset-tagger-v2.html` |
| Evolution dashboard | `https://jbarad424.github.io/ideas/cb-evolution.html` |
| Pitch deck page | `https://jbarad424.github.io/ideas/cb-creative-lab-deck.html` |
| JSON data (live) | `https://jbarad424.github.io/ideas/cb-ai-lab.json` |
| Legacy data (archived) | `https://jbarad424.github.io/ideas/cb-ai-lab-legacy.json` |
| GitHub repo (app code) | `jbarad424/ideas` |
| GitHub repo (training data, private) | `jbarad424/cb-creative-studio` |
| Replicate model (private) | `replicate.com/jbarad424/cb2-lora` |
| v4 training photos (Google Drive) | `https://drive.google.com/drive/folders/1nZvgFmI_kXqURDBZx_WSMFvSc9lfLW-k` |

## Appendix B: Session Log

| Session | Date | Key Outcomes |
|---|---|---|
| Session 1-2 | Pre-April 2026 | Image-to-image testing (FLUX Kontext). Proved the approach has a ceiling for small products. Spent ~$2 on generation. |
| Session 3 | April 2026 | Pivoted to LoRA fine-tuning. Trained v1 (13 images), v2 (28 images), v3a (37 images), v3b (37 images, higher rank). Proved close-up training data is critical. Total training cost ~$16. |
| Session 4 | April 3, 2026 | Received 38 close-up product photos from Justin. Built v4 training set (38 images + 38 captions). Fixed Make.com polling bug. Evaluated Higgsfield.ai. Researched Cloudflare Workers as Make.com alternative. v4 training set ready for upload. |

---

*This document is maintained as a living reference. Last updated April 3, 2026.*

---

## 13. REVISED: Reference-First Architecture (v2.0)

**Added April 3, 2026 — based on hands-on testing failures + independent deep research validation**

### Why We Pivoted

After training 6 LoRA versions (v1 through v4b) on 88+ product photos with manual captions, we achieved:
- Correct texture, color, accents, form factor, strap, icon symbols
- WRONG button count on every single test image (4, 6, 8, or 10 buttons instead of 5)

Academic research confirms: diffusion models have exact counting accuracy below 23% regardless of dataset size or training duration. This is architectural, not fixable with more training data.

**The insight:** Don't GENERATE the product. PRESERVE it. Use a real product photo as the structural anchor, then change the scene around it.

### The Correct Architecture

```
CLIENT INTAKE
  → 10-20 product photos (all angles, all colorways)
  → Brief (target scenes, brand guidelines, output specs)
  → "Must preserve" checklist (logo, button count, proportions, materials)

ASSET PREP
  → Background removal + segmentation
  → Canonical crops (front, side, back, on-body)
  → Detail crops (logo, buttons, ports, texture)
  → Edge maps (Canny) for structural conditioning
  → OCR pass for text that must survive

GENERATION ROUTER (picks best path per scene)
  ├── Path A: Reference-First Editing
  │   FLUX.2 Multi-Reference (up to 8 input images)
  │   or FLUX.1 Kontext (single reference + edit prompt)
  │   Cost: $0.03-0.08/image
  │   Best for: scenes where product is prominent
  │
  ├── Path B: Structure-Locked Generation
  │   ControlNet Canny + LoRA
  │   Edge map from real photo locks exact geometry
  │   LoRA provides trained style/texture
  │   Cost: ~$0.04/image
  │   Best for: exact structural fidelity (button count, proportions)
  │
  └── Path C: LoRA-Only (FALLBACK)
      Only when reference conditioning isn't enough
      Requires post-generation quality check for counting errors
      Cost: ~$0.01-0.05/image
      Best for: creative exploration, not final assets

SCORING PIPELINE
  → Product similarity check vs reference photos
  → Logo/text OCR correctness
  → Material/color preservation
  → Scene compliance
  → "Would a marketer ship this?" test
  → Human approval on top 2-4 candidates

VIDEO EXPANSION (only after stills work)
  → Higgsfield for product-to-ad
  → Runway for reference-based video
```

### Platform Comparison for Reference-First Editing

| Platform | Model | What It Does | Cost | API |
|----------|-------|-------------|------|-----|
| **fal.ai** | `flux-lora-canny` | Canny edges + custom LoRA | $0.035/MP | Yes |
| **fal.ai** | `flux-general/image-to-image` | Kontext-style reference editing | Check | Yes |
| **BFL direct** | FLUX.2 Pro | Multi-reference editing (up to 8 images) | $0.045/edit | Yes |
| **BFL direct** | FLUX.1 Kontext Pro | Single reference + edit | $0.04/image | Yes |
| **Replicate** | `xlabs-ai/flux-controlnet` | Canny ControlNet + optional LoRA | Per-second | Yes |
| **Photoroom** | Product editing API | Backgrounds, shadows, relighting | $0.10/call | Yes |

### What This Changes for Consulting Clients

**Old pitch:** "We train a custom AI model on your product photos and generate marketing images."
**Problem:** The model produces beautiful counterfeits — right vibe, wrong details.

**New pitch:** "We build a reference-conditioned generation pipeline that uses your ACTUAL product photos as structural anchors, ensuring perfect product fidelity in every generated scene. AI handles the scene, lighting, and composition — your real product stays pixel-accurate."
**Why it's better:** The product is never hallucinated. It's preserved from the source material.

### Cost Comparison: Old vs New Approach

| | LoRA-First (old) | Reference-First (new) |
|--|---|---|
| Setup cost | ~$5 per LoRA training | $0 (no training needed for Tier 1) |
| Per-image cost | $0.01-0.05 | $0.03-0.08 |
| Product accuracy | 5-6/100 (wrong counts) | Expected: much higher (structure locked) |
| Time to first image | Hours (training + testing) | Minutes (upload references + prompt) |
| Iteration speed | Retrain = hours + $5 | Change prompt = seconds + $0.04 |
| Fallback available | N/A | LoRA already trained and ready |

### Key Lesson for the Playbook

> **Do not let the project assume the holy grail is "train a LoRA and prompt it forever."**
> The defensible 2026 architecture is: reference-first editing → automated scoring → LoRA only as fallback → then video expansion.
> — Validated by both hands-on testing and independent deep research (ChatGPT analysis, April 2026)
