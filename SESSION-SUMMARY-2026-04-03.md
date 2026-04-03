# CB Creative Lab — Session 3 Summary
**Date:** April 3, 2026
**Last edit:** ~10:00 AM EST
**Secret phrase:** go hang a salami, I'm a lasagna hog

---

## Live URLs
- **App v1:** https://jbarad424.github.io/ideas/asset-tagger.html
- **App v2 (NEW, not fully ready):** https://jbarad424.github.io/ideas/asset-tagger-v2.html
- **Evolution Dashboard:** https://jbarad424.github.io/ideas/cb-evolution.html
- **JSON Data:** https://jbarad424.github.io/ideas/cb-ai-lab.json
- **Replicate LoRA Model:** https://replicate.com/jbarad424/cb2-lora (private)
- **GitHub Repos:** jbarad424/ideas (app) + jbarad424/cb-creative-studio (notes/training data, private)

---

## What Happened in Session 3

### The Pivot
Analyzed all 31 scored images from sessions 1-2. Found image-to-image (FLUX Kontext) had a fundamental ceiling:
- Product score 5 = boring flat-lay copies of reference photo
- Creative action shots = product vanishes 75% of the time
- Only 3 out of 14 action shots had product score 4+
- AI analysis notes: "Outstanding scene, product completely missing" over and over

**Decision:** Pivot from image-to-image editing to FLUX LoRA fine-tuning. Jordan's suggestion to fine-tune was correct — we used FLUX instead of Stable Diffusion because better photorealistic output.

### LoRA Training Experiments

| Run | Images | Rank | Steps | LR | Result | Justin's Score |
|-----|--------|------|-------|----|--------|----------------|
| v1 | 13 (Drive only, auto-caption) | 16 | 1500 | 0.0004 | Product visible but wrong button count (7 not 5) | Not shown |
| v2 | 28 (Drive + manual captions) | 16 | 2000 | 0.0004 | Product at realistic size, 4 buttons instead of 5 | Not shown |
| v3a | 37 (+ 9 website product shots, manual captions) | 16 | 2000 | 0.0004 | 5 buttons consistent in close-ups, motorcycle medium shot had device on forearm | Better but not there |
| **v3b** | **37 (same data)** | **32** | **2500** | **0.0003** | **Best detail on buttons/icons, lower training loss (0.31)** | **Wired into pipeline** |

**Training data sources:**
- PIC folder (Google Drive): 10 action shots with CB2 on arm
- Hunter Product Launch folder: 3 product/on-arm shots
- InstaPosts-CB2 folder: 11 diverse (moto, fitness, snow, yoga)
- Tahoe Media folder: 4 lifestyle shots
- chubbybuttons.io website: 9 clean product shots (all 3 colorways)
- All manually captioned with "5 large raised tactile buttons" in every caption

**Training zips on GitHub (ideas repo):**
- cb2-training.zip (v1, 13 images)
- cb2-training-v2.zip (v2, 28 images + captions)
- cb2-training-v3a.zip (v3a/v3b, 37 images + captions)

### Winning Model
- **Replicate version:** `3e92d342cd202cca741396e2588b9f43b6719ceea73cdf4876ef00070a2376fe`
- **Trigger word:** CB2REMOTE
- **Cost:** ~$16 total across 4 training runs + test generations

---

## HONEST Assessment of Current Quality (Justin's Feedback)

**Justin scored the best outputs at 5-6 out of 100.** The model learned "outdoor action sports vibes" and "some kind of rectangular thing with buttons" but did NOT learn what CB2 actually looks like. Specific issues:

- Close-up "Tron motorcycle" shot: Has 4 buttons (not 5), wrong proportions, no logo, wrong icon style, wrong body shape. Looks like *a* remote, not *their* remote. Justin: "looks nothing like our product"
- "Hiker with buttons on back": Buttons somewhat recognizable but on the BACK not the forearm. Justin: "1 out of 100"
- Skier scene: Gorgeous stock photo, zero product visible. Justin: "really bad, big fail"
- Squirrel on branch: Pipeline timing bug returned wrong image entirely. Waste of credits.

**Root cause:** Training dataset was ~80% wide-angle action shots where CB2 is tiny/distant, ~20% product close-ups. The model learned the vibe but not the product details. Need to flip this ratio to ~60-70% close-up product shots.

**I (Claude) was grading on a curve** — celebrating "the model generated something vaguely remote-shaped" when the bar is "this looks like OUR product and I'd put it on our website." Those are completely different standards. Justin was right to call this out.

---

## Pipeline Architecture (Working but Needs Reliability Fix)

### Make.com Scenarios

| Scenario | ID | Webhook | Status |
|----------|-----|---------|--------|
| **LoRA Generate (NEW)** | 4655593 | 32urtvvoi5x5wfpzjgm0vnfxzlehre1w | Active but has timing bug |
| FLUX Generate (legacy v1) | 4653737 | e95rfn1iz88bnhtejhqhadqtvblnp128 | Active |
| Recraft Generate | 4653740 | vzybkkhoi0powa0np6t2wr8m2pjr3dxu | Active but FAILED during batch test |
| Runway Video | 4653901 | ayflnfwjqehyblmvwnosatlbogwyil90 | Active but FAILED during batch test |
| Rate Image | 4653738 | b4l7shwxqblbeq5t36ttse62bivls9y3 | Active |
| Sync JSON | 4654266 | p3bt4ga6npqjs3608t9aou45qq1m5amh | Active |
| Vision Co-Rater | 4654454 | bffoci5zxq1uy28bc6l5e0rm73kgj9av | Active |

### LoRA Pipeline Flow
```
App (Generate More button)
  → LORA_API webhook (Make.com scenario 4655593)
    → POST to Replicate API (token server-side in Make.com, NOT in client HTML)
    → Sleep 60s → Poll Replicate → Sleep 15s → Poll again (double-poll)
    → Download generated image
    → Create batch subfolder in Drive (AI Creative Lab folder)
    → Upload image to Drive subfolder
    → Save to data store (CB AI Lab, ID 84188)
    → Return {success, imageId, driveFileId} to app
  → App shows image for rating
  → Vision Co-Rater scores image (product/scene/brand 1-5)
  → User sees AI scores → Agree or Disagree
  → Feedback feeds into next batch prompts
```

### Known Pipeline Bug: Make.com Polling Timing
The sleep(60) + sleep(15) double-poll sometimes isn't enough. Replicate occasionally takes longer, and when the poll happens before the prediction is done, it downloads a placeholder/wrong image (the squirrel, the nature photos). Hit rate through pipeline: ~40-50%. When calling Replicate directly via curl: ~70%.

**Fix needed:** Replace sleep+poll with a proper repeater loop that checks status every 10s until "succeeded", or use Replicate's webhook callback feature to notify Make.com when done.

---

## API Keys & Credentials

### Stored in .env (cb-creative-studio repo, gitignored)
- `FAL_KEY=REDACTED`
- `REPLICATE_API_TOKEN=REDACTED`

### Stored in Make.com (server-side)
- Replicate token: hardcoded in LoRA scenario 4655593 HTTP headers
- Anthropic API key: hardcoded in Vision Co-Rater scenario 4654454
- BFL API key (FLUX): hardcoded in FLUX scenario 4653737

### Google Connections in Make.com
- Google Drive: connection ID 4724749 (justin@chubbybuttons.io)
- Google Photos: connection ID 4728111 (authorized but missing Photos API scope — albums list returns empty)

### Replicate Account
- Username: jbarad424
- Model: jbarad424/cb2-lora (private)
- **Credits likely low** — ~$16 spent on training + tests. Free tier started with ~$5. Need to add credits at https://replicate.com/account/billing ($25-50 recommended)

---

## v2 App (asset-tagger-v2.html)

### What's New vs v1
- **Agree/Disagree** replaces product/scene up/down buttons
- **AI assessment panel** on every swipe card (product/scene/brand scores + notes)
- **LoRA generation** via Make.com proxy to Replicate (no API tokens in client HTML)
- **`analyzeRatings()`** reads BOTH human ratings AND AI scores to improve prompts
- **`convertAiNotesToPromptLanguage()`** turns AI critique into positive prompt fixes
- **AI scoring runs before sync** so scores persist in JSON
- **Grid view** shows colored dots (green/yellow/red) for AI product score
- **No passcode** — just tap your name
- **CB2REMOTE trigger word** in every FLUX prompt
- **Filters to only show LoRA-generated images** (old v1 images hidden)

### What's NOT Working Yet
- LoRA generation quality is not good enough (5-6/100 per Justin)
- Recraft and Runway scenarios failed during batch test
- Make.com polling has timing bug causing wrong images
- App needs QA before showing to team

---

## The Feedback Flywheel (Design, Not Yet Fully Working)
```
LoRA generates images (knows what CB2 looks like — BUT NEEDS BETTER TRAINING DATA)
    ↓
Claude Vision auto-scores (product/scene/brand 1-5)
    ↓
Low scores → specific diagnosis → prompt fixes
    ↓
Human sees pre-scored images → Agrees or Disagrees
    ↓
Human disagreements calibrate the system
    ↓
Everything compounds → next batch is better
```

---

## Google Photos Album (NOT YET ACCESSED)
Justin shared a Google Photos album with close-up product shots:
- **URL:** https://photos.app.goo.gl/RQgg7PV2RJhkzLDh8
- **Account:** justin@chubbybuttons.io
- **Status:** Created a credential request for Google Photos API access but the connection doesn't have the right scope. Albums list returns empty.
- **Workaround:** Justin needs to download photos to a local folder or a Drive folder we can access.
- **Why it matters:** These close-ups are the #1 thing blocking better LoRA training. Current dataset is too heavy on wide-angle action shots where the product is tiny.

---

## Training Data on Disk (cb-creative-studio repo)

```
training-images/          # Original full-res downloads from Drive (13 images)
training-images-resized/  # Resized to 1024px + .txt captions (28 images)
training-v3a/             # v3a/v3b training set (37 images + captions)
website-product-shots/    # 9 product shots from chubbybuttons.io
lora-test/                # All test generation outputs
  v2-skier-1.webp         # v2 test: action (no product)
  v2-product-1.webp       # v2 test: product visible but wrong details
  v3a-action.webp         # v3a test: snowboarder (no product)
  v3a-medium.webp         # v3a test: motorcycle with device on arm
  v3a-closeup.webp        # v3a test: 5 buttons, green body, on blue jacket
  v3b-action.webp         # v3b test: snowboarder (product on wrist area)
  v3b-medium.webp         # v3b test: motorcycle guy (editorial, no jacket)
  v3b-closeup.webp        # v3b test: 5 buttons detailed, held up to camera
  pipeline-test.webp      # First successful pipeline image (CB2 on blue jacket)
  doublepoll-test.webp    # Double-poll fix test (3 buttons visible, strap)
  batch1-*.webp           # First batch (mostly wrong images due to timing)
  final-*.webp            # Final batch (2 OK, 2 wrong, 1 redirect)
```

---

## Costs So Far

| Item | Cost |
|------|------|
| Replicate LoRA training (4 runs: v1, v2, v3a, v3b) | ~$16 |
| Replicate test generations (~20 images) | ~$1.50 |
| fal.ai (1 test queue) | ~$0.02 |
| Make.com operations (all scenarios) | Included in plan |
| Previous image-to-image generation (sessions 1-2) | ~$2 |
| **Total invested** | **~$20** |
| **Budget remaining** | **~$50 (if credits added)** |

---

## Memory/Preferences (from .claude project memory)

- **UI text sizing:** Team needs bigger/brighter text, not spring chickens
- **Positive feedback popups:** Capture what's good too, not just what's wrong
- **Create tab on hold:** Coming Soon until rating workflow is solid
- **Generate More flow:** Per-user recursive loop, new assets go to everyone
- **Action shot north star:** "Damn, I wish that were me" is the bar for action shots
- **Push back and lead:** Don't be a yes man — recommend the smarter path, push back confidently. Say "here's what I'd do if I were 100x smarter than you." Don't assume Justin knows what he's talking about.
- **LoRA pivot:** Switched from image-to-image to FLUX LoRA fine-tuning, Replicate model jbarad424/cb2-lora

---

## What's Next (Priority Order)

### BLOCKER: Get close-up product photos for v4 training
1. **Download Google Photos album** to a local folder (Justin needs to do this — Photos API scope isn't working)
2. OR: Justin drops photos into a Google Drive folder we can access
3. Need 15-20 close-ups showing: all angles, all 3 colorways, 5 buttons visible, on-arm + off-arm, logo visible

### Then: Train v4 LoRA
4. Build training set with 60-70% close-up product shots, 30-40% lifestyle/action
5. Manual captions emphasizing exact product details (5 buttons, specific icon layout, colorway names)
6. Train on Replicate with rank 32, 2500+ steps
7. Test with the SAME prompts we've been using so we can compare apples to apples

### Then: Fix Pipeline Reliability
8. Replace Make.com sleep+poll with proper retry loop or Replicate webhook callback
9. Fix Recraft and Runway scenarios (both failed during batch test)
10. Add error handling in app for failed generations

### Then: Polish v2 App
11. Only show LoRA-generated images that pass a quality threshold
12. Run AI scoring on all images before showing to team
13. QA the agree/disagree flow end-to-end
14. Deploy clean version for team to test

### Then: WhatsApp Team Update
15. Draft message is in the conversation — search for "Hey team"
16. Don't send until we have at least a few images Justin would score 50+/100

---

## Pickup Instructions
1. Say "lets continue CB Creative Lab"
2. Read `SESSION-SUMMARY-2026-04-03.md` for complete state
3. The secret phrase is: **go hang a salami, I'm a lasagna hog**
4. **First thing to do:** Ask Justin if the Google Photos close-ups are downloaded yet
5. If yes → build v4 training set (60-70% close-ups) and retrain
6. If no → help get the photos downloaded, that's the blocker
7. Don't generate more images until training data improves — every bad image wastes Replicate credits
8. Don't celebrate incremental progress that's still nowhere near usable — Justin's standard is "would I put this on our website" not "does it vaguely resemble a remote"
