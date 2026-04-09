# CREATE Tab v2 — Updated Plan

**Source:** imported from `~/Desktop/Updated Plan.rtf` on 2026-04-09.
**Context as of import:** iCloud→`~/code/cb2-ideas` migration complete (commit 5b726f3). `cb-keepers.json` deployed (217 curated photos: 37 super + 180 yes, 100% substantive prompts). Pipeline validated across GPT Image 1.5, Nano Banana Pro, NB2, FLUX 2 Flex with rotated h3/h5/h6/p4/p6 refs. This plan replaces Tinder-style `cb-rate.html` flow for **new generations** with a multi-select keeper grid. `cb-rate.html` stays as-is for backfill review of the existing 694-photo corpus.

> **Path note (drive snafu fix):** the RTF version was written against the old iCloud path `/Users/justinbarad/Documents/Claude Code/ideas/`. Everything below has been rewritten to the current repo path `/Users/justinbarad/code/cb2-ideas/`. Any future session reading this file is reading the canonical paths.

---

## 📍 END-OF-DAY STATE (2026-04-09 evening)

**What shipped today (fully deployed):**
- ✅ **Tron colorway unlocked** — 80 NB Pro gens ($12), 77/80 rated, 7 refs locked into production (t18 champion, t01/t03/t11 Tier 1, t05/t09/t17 Tier 2). t10/t16 killed.
- ✅ **tron-ab-review.html** live on GitHub Pages with permanent image URLs + keyboard shortcuts
- ✅ **80 gens + 20 original refs archived** on `jbarad424/ideas` at permanent URLs (`tron-ab-gens/` and `ref-library/tron-raw/`)
- ✅ **🔥 NB Pro 25 button retired** from cb-rate.html (batch complete)
- ✅ **`cb-learning.json` scaffold shipped** (Part 0.3 done)
- ✅ **CLAUDE.md updated** with Tron ref table entries, killed list, session priorities rewrite (commit `5755a55`)
- ✅ **`tron-triage.html` retired** and auto-redirects to the review page

**What's code-complete but not deployed (waiting on Justin's external actions):**
- ⏸ **CF Worker code** at `scripts/cf-worker/worker.js` — ready to `wrangler deploy`. Blocks on Justin: CF account + Wrangler install + shared password + rotated fal.ai key + Anthropic key. See `JUSTIN-TODO-CF-WORKER.md`.
- ⏸ **CREATE tab Part 1 data layer** at `scripts/create-tab/data.js` — tested against real `cb-keepers.json`, produces 93 recipes from 217 keepers, 32 multi-example Hit Parade candidates, top recipe is moto desert canyon with 22 examples + 8 super-likes. Can ship standalone; integrates into cb-review.html once Worker is deployed.

**What's explicitly deferred (not blocking v1):**
- ⏳ Part 2.3 "Write your own" Flavor C → v2
- ⏳ Part 2.4 "Twist this recipe" Flavor A → v2
- ⏳ Part 4.4 Auto-defaulting model/ref → v2 (after ≥ 20 batches of real data)
- ⏳ Part 4.6 Novel scene auto-promotion → v2
- ⏳ Rail 2 "Creative One-offs" → v2 (only if Rail 1 isn't enough)

**Critical path to ship CREATE tab v1:** CF Worker deployed → `cb-review.html` edits (strip keys, add proxyCall, add password modal, fix SYNC_URL, add CREATE tab UI) → integrate Part 1 data layer → build Part 2.1 recipe cards + Part 2.2 "+New Scene" + Part 3 keeper grid + Parts 4.1-4.3 learning loop. **Every step after "CF Worker deployed" is my work; Worker deployment is the blocker on Justin.**

---

---

## Guiding Principle — the 80/20 rule (North Star)

> Every exchange spawns six or seven ways to keep going. Guide me toward the 80/20 route. Seeds are random — don't chase randomness. If UX is getting complicated, pull me back to "let's finish this."

Applied to this plan:
- Scope is deliberately narrow. Only v1 ships first. v2 unlocks only after real batch data shows the need.
- No auto-learning magic in v1. Show the signal, let Justin trust it, don't pretend the counters know more than they do.
- Per-image fiddling is banned. A batch is the unit of work — 6 images in, N keepers out, done.
- Cost visibility over cost control. Preview the bill before firing.
- When in doubt, cut.

---

## Part 0 — Blocking Prerequisites

### 0.1 API key exposure + multi-user access — CRITICAL

The fal.ai key `abd109db-5b32-4be9-8e80-55d543ef21b5:…` is hardcoded three times in `cb-review.html` (lines 1584, 1671, 1693) and deployed publicly to `jbarad424.github.io`. Any crawler can drain the fal.ai quota right now.

**Fix: tiny Cloudflare Worker proxy with a shared password gate.**

1. **Deploy a Cloudflare Worker** (~20 lines, free tier):
   - Env vars stored server-side: `FAL_KEY`, `ANTHROPIC_KEY`, `SHARED_PASSWORD`
   - Accepts `POST {password, endpoint, body}` → validates password → forwards to `fal.run/<endpoint>` with server-side key → streams response back
   - Handles both fal.ai image/video endpoints AND Anthropic messages endpoint (for Sonnet refiner in 2.2)
   - CORS: `Access-Control-Allow-Origin: https://jbarad424.github.io`
   - Rate limit: 100 req/min per IP

2. **Strip keys from `cb-review.html` entirely.** Replace the three hardcoded FAL const declarations with:
   ```js
   async function proxyCall(endpoint, body) {
     const pw = getSharedPassword(); // from localStorage
     return fetch(WORKER_URL, {
       method: 'POST',
       body: JSON.stringify({password: pw, endpoint, body})
     });
   }
   ```

3. **One-time password modal** (first visit): "Paste team password to enable image generation. Ask Justin if you don't have it." Stored in `localStorage.cb2_team_pw`. Apply to Video Lab AND new CREATE tab.

4. **Rotate the leaked fal.ai key** at the dashboard after Worker deploys. Old key is compromised.

5. **Sharing with team:** Justin sends the URL + shared password once. If password leaks → rotate in CF dashboard in 10 seconds.

**Why not per-user keys:** Justin explicitly wants no-hunt-for-API-keys for his team. **Why not Make.com proxy:** 30s default timeout doesn't fit long fal.ai polling. **Why Cloudflare:** free tier, single-file `wrangler deploy`, 5-min signup. Vercel/Deno Deploy are equivalent.

### 0.2 SYNC_URL webhook bug

Line 393 of `cb-review.html` has `SYNC_URL` pointing to the Rate Image webhook, not the Sync JSON webhook (Make.com scenario 4654266). Feedback has been silently dropped for weeks.

**Fix:**
- Update Make.com scenario 4654266 to accept a dynamic `filename` field (currently hardcoded to `cb-ai-lab.json`).
- Change `SYNC_URL` in `cb-review.html` to the correct Sync JSON webhook.
- Rewrite `syncFeedback()` to send `{jsonContent: stringified, filename: "cb-feedback.json"}`.
- `cb-feedback.json` already exists locally (169 KB). First successful sync either overwrites with merged state or we manually deploy once.
- Verify: hit Sync → check `jbarad424.github.io/ideas/cb-feedback.json` updates within 60s.

### 0.3 Create `cb-learning.json` scaffold

Empty starter at `/Users/justinbarad/code/cb2-ideas/cb-learning.json`:

```json
{
  "meta": {"version": 1, "alpha": 0.3, "created": "<iso>"},
  "batches": [],
  "recipes": {},
  "refs": {},
  "models_by_sport": {}
}
```

Deploy to GitHub Pages so CREATE can fetch-before-push.

---

## Part 1 — Data Layer

### 1.1 Recipe index (client-side, built on tab switch)

Load `cb-keepers.json` once. Group items by `(normalize_prompt, seed)` tuple to form recipes:

```js
recipe = {
  id: sha256(normalize(prompt) + "|" + seed),  // stable
  prompt: "…full prompt text, verbatim…",       // snapshotted
  seed: 9101,
  sport: "moto",                                 // from galDetectSport() or prompt scan
  refs_observed: ["h3", "p4", "refc"],           // refs that produced keepers
  model: "nano-banana-pro",                      // modal model
  examples: [url1, url2, …],                     // thumbnails from cb-keepers.json
  super_count: 4,
  yes_count: 7,
}
```

Cold-start sort: `super_count × 2 + yes_count`. One-offs rail = singletons (1 example).
`normalize()` = strip whitespace, lowercase, collapse runs of spaces. Same function at index time AND query time to prevent drift.

### 1.2 Production ref library (authoritative)

From CLAUDE.md, all hosted on `jbarad424.github.io/ideas/rotated-refs/`:

```js
REFS = {
  h3:  {colorway:"Hunter",  type:"jacket",  url:"…/rotated-refs/h3.jpg"},
  h5:  {colorway:"Hunter",  type:"jacket",  url:"…/rotated-refs/h5.jpg"},
  h6:  {colorway:"Hunter",  type:"product", url:"…/rotated-refs/h6.jpg"},
  p4:  {colorway:"Patriot", type:"jacket",  url:"…/rotated-refs/p4.jpg"},
  p6:  {colorway:"Patriot", type:"jacket",  url:"…/rotated-refs/p6.jpg"},
  refc:{colorway:"Hunter",  type:"dual",    url:"https://lh3.googleusercontent.com/d/1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7=w800"},
  // Tron refs drop in here as t1, t2, … once the Tron A/B identifies winners
}
KILLED_REFS = ["p1","h1","h4","p5"]  // never show, never default
```

**Tron status (updated 2026-04-09):** Jordan shot 20 Tron refs on 2026-04-09 (Drive folder `1DfR8YHW9L2BLb_w-JZhKEdj_Vfo1D4es`, IMG_7184–IMG_7203). Downloaded to `tron-refs/originals/`.

**Key improvement over Hunter/Patriot:** Jordan intentionally shot the same device in multiple physical orientations this time — PLUS-up and PLUS-down variants of the same scene. That means the `sips -r 180` post-processing step from the rotation A/B isn't needed for Tron; the orientation variants are already in the corpus. The A/B test compares 20 candidates as-shot, not 40 (original + rotated).

**Next step:** automated rotation-free A/B — 20 refs × 2 sports × 2 scenes = 80 gens @ NB Pro, Justin rates the *generated images* (not raw refs — that's a v1 anti-pattern that burns user attention on pre-filtering the model should do for us). Refs with high keeper rate → production, refs with perpendicular/wrongArm/garbled output → kill-listed. Winners become `t1…tN` in `rotated-refs/` (name kept for consistency with Hunter/Patriot even though these weren't post-rotated).

- Colorway dropdown in "+ New Scene" always shows Hunter / Patriot / Tron.
- If zero Tron refs exist in REFS, the Tron option is selectable but shows a tooltip: "Tron A/B in progress — drops here once winners are identified."
- Once Tron winners exist, the same EMA learning loop (Part 4) scores them alongside h3/p4.

### 1.3 Mandatory gear by sport (from CLAUDE.md)

```js
MANDATORY_GEAR = {
  moto: "full-face helmet, leather riding jacket with armor, thick leather riding gloves",
  ski:  "ski helmet, goggles, ski gloves, ski jacket",
  snow: "snowboard helmet, gloves, snowboard jacket",
  mtb:  "full-face DH helmet, gloves, jersey with armor",
  sled: "full-face helmet, snowmobile gloves, snowmobile suit",
}
```

### 1.4 Per-sport model picker (v1: manual, v2: auto-learned)

```js
DEFAULT_MODEL_BY_SPORT = {
  moto: "fal-ai/gpt-image-1.5/edit",       // 99 GPT masked inpaint, 90 GPT solo
  ski:  "fal-ai/nano-banana-2/edit",       // 100 NB2
  snow: "fal-ai/nano-banana-pro/edit",     // 99 NB Pro
  mtb:  "fal-ai/nano-banana-pro/edit",     // 94-98 NB Pro
  sled: "fal-ai/nano-banana-pro/edit",     // test batch awaiting review
}
```

v2 overrides with `argmax(models_by_sport[sport].keeper_rate)` once data arrives.

---

## Part 2 — CREATE Tab UI

Inject `<div class="tab" onclick="setTab('create')">CREATE</div>` between VIDEOS and AI SCORING. Add `'create'` to `tabList`. Add `<div id="createArea">` body.

```
┌─ CREATE HEADER ─────────────────────────────────────┐
│ [+ New Scene]  [Write your own]  Cost: $---         │
└─────────────────────────────────────────────────────┘
┌─ HIT PARADE (Rail 1) ──────────────────────────────┐
│ Sorted by learning score, cold start by super×2+yes │
│ [card] [card] [card] [card] …                        │
│   ⭐4    ⭐3    ⭐2    ⭐1                              │
└─────────────────────────────────────────────────────┘
┌─ ONE-OFFS (Rail 2) ────────────────────────────────┐
│ [tile] [tile] [tile] [tile] … (singletons)          │
└─────────────────────────────────────────────────────┘
┌─ KEEPER GRID (appears when generating) ────────────┐
│ [img1 ♡] [img2 ♡] [img3 ♡]                           │
│ [img4 ♡] [img5 ♡] [img6 ♡]                           │
│  3 of 6 keepers            [Save batch]              │
└─────────────────────────────────────────────────────┘
```

### 2.1 Recipe card (Rail 1)

Each card shows:
- Thumbnail of top-scoring example
- ⭐ `super_count` badge (if > 0)
- Sport icon (🏍 🎿 🏂 🚵 🛷)
- Colorway toggle: Hunter / Patriot / Tron — filters `refs_observed` to that colorway, excludes `KILLED_REFS`. Defaults to colorway with highest `refs[…].by_recipe[id].keeper_rate` (v2; v1 defaults to most-recent used).
- **"Make 4 more like this"** button → fires batch with identical prompt + seed, selected colorway's top ref
- Live keeper_rate badge after Phase 4 data arrives ("last batch: 4/6")

Tap anywhere else on the card → lightbox gallery (reuses `lbDist`/`lbReset`/`lbApply` from `cb-rate.html:706–789`).

### 2.2 "+ New Scene" form (Flavor B) — with Sonnet prompt refiner

Modal form:
- **Sport:** dropdown (moto / ski / snow / mtb / sled)
- **Colorway:** dropdown (Hunter / Patriot / Tron)
- **Scene description:** textarea, free natural language
- **Vibe:** dropdown (editorial / documentary / golden hour / harsh midday / moody night)
- **Model:** defaults from `DEFAULT_MODEL_BY_SPORT`, manual override
- **Arm:** defaults from CLAUDE.md Per-Scene Arm Decision Table, manual override. Flag a warning if the sport's table says prompt arm lock is cosmetic (e.g. snow → use stance, not prompt).
- **Ref:** filtered to known-good refs for colorway (excludes `KILLED_REFS`), defaults to highest recent keeper_rate
- **Seed:** auto-random, manual override available
- **Batch size:** 4 or 6 (default 6)

**Step A — Refine with Sonnet.** Between the textarea and the final prompt preview, add a **✨ Refine with Sonnet** button:

1. Send user's natural-language scene to CF Worker → Anthropic API (`claude-sonnet-4-6`)
2. System prompt (client-side, editable via gear icon): *"You are a photography director for an action-sports marketing brand. Rewrite the user's scene description into industry-standard photographic language that would produce exceptional marketing photos — but preserve 100% of the user's creative intent. Use specific camera/lens terminology (e.g. 'shot on Sony A7R IV 85mm f/2.0'), concrete lighting vocabulary (e.g. 'raking sidelight', 'golden-hour backlight'), evocative setting detail, and atmospheric descriptors. Do NOT add a product description, subject description, wardrobe, or framing — those are added separately. Output only the rewritten scene paragraph, no preamble."*
3. Show refined scene in a diff view next to original (accept / reject / re-refine)
4. Accept → refined scene replaces textarea content

**Step B — Construct final prompt.**

```
[refined_scene + vibe_prefix]. [sport_subject + MANDATORY_GEAR[sport]].
[LOCKED CB2 BLOCK per arm choice from CLAUDE.md § Locked CB2 block].
[camera/style from vibe].
```

**Step C — Inline-edit and fire.** Final prompt is inline-editable in a preview box. Nothing fires until Justin clicks **Generate**. Cost preview above button: "6 × NB Pro = $0.90".

**Why Sonnet:** Justin's natural language is the best signal about creative intent. Templates flatten it. Sonnet catches ambiguity and injects industry conventions Justin shouldn't have to know. Model = `claude-sonnet-4-6`, ~$0.003/refine, <2s.

### 2.3 "Write your own" (Flavor C) — v2

Free textarea with checkboxes: "Inject locked CB2 block" (on), "Inject mandatory gear" (on). Deferred.

### 2.4 "Twist this recipe" (Flavor A) — v2

Prefills "+ New Scene" with recipe's locked bits (sport, seed, model, ref, CB2 block), leaves scene+vibe empty. Deferred.

---

## Part 3 — Generation + Keeper Grid

### 3.1 Direct-from-browser fal.ai submission

Reuse Video Lab pattern (`cb-review.html:1584–1726`). Differences:
- Image endpoints: `fal-ai/nano-banana-pro/edit`, `fal-ai/gpt-image-1.5/edit`, `fal-ai/nano-banana-2/edit`, `fal-ai/flux-2-flex/edit`
- Submit N parallel calls (4 or 6)
- Poll each request independently with backoff (1s → 2s → 4s → 8s → cap 15s)
- Render skeletons immediately, replace with images as they arrive
- Per-tile status: queued / generating / done / failed
- Use `getFalKey()` helper (Part 0.1)

### 3.2 Keeper grid component

- 2×3 grid (6 images) or 2×2 (4 images), responsive
- Each tile: image + ♡ keeper toggle (corner) + tap-anywhere-else opens lightbox
- Lightbox: copy `lbDist`/`lbReset`/`lbApply` from `cb-rate.html:706–789` (pure vanilla)
- Live counter: "N of 6 keepers"
- **Save batch** disabled until all 6 tiles reach terminal state (done OR failed)
- **Retry failed** button per failed tile
- Partial failures allowed: 4/6 succeed, 2/6 fail → save counts 4 as denominator, logs 2 failed URLs separately

### 3.3 Save batch flow

On Save:
1. Fetch current `cb-learning.json` from `https://jbarad424.github.io/ideas/cb-learning.json?t=<cachebust>`
2. Append new batch record (Part 4.1 schema)
3. Update EMA counters for recipe, ref, model-by-sport (Part 4.2)
4. POST merged JSON to fixed `SYNC_URL` with `{jsonContent, filename: "cb-learning.json"}`
5. Update local state immediately — do not wait for sync. Hit Parade re-sorts instantly.
6. Toast: "Batch saved — 3 keepers added"

**Merge strategy:** fetch-before-push. If GitHub has a `batch_id` we don't, keep theirs. If we have one GitHub doesn't, append ours. Never overwrite by timestamp.

---

## Part 4 — Learning Loop

### 4.1 Batch record schema

Appended to `cb-learning.json.batches[]`:

```json
{
  "batch_id": "2026-04-09T18:34:12Z_a1b2c3",
  "recipe_id": "moto_s0_9101",
  "recipe_prompt": "…full prompt text, snapshotted at batch time…",
  "ref_id": "h3",
  "model": "fal-ai/nano-banana-pro/edit",
  "sport": "moto",
  "generated": 6,
  "kept_urls": ["url1", "url2", "url3"],
  "rejected_urls": ["url4", "url5"],
  "failed_urls": [],
  "keeper_rate": 0.5,
  "cost_usd": 0.90,
  "is_novel": false
}
```

`recipe_prompt` is snapshotted verbatim so future drift never retroactively changes history.

### 4.2 EMA counters (α = 0.3)

Formula: `new = 0.3 × batch_rate + 0.7 × prior`

```json
{
  "recipes": {
    "moto_s0_9101": {
      "keeper_rate": 0.42,
      "batches_run": 7,
      "total_generated": 42,
      "total_kept": 18,
      "last_batch_at": "2026-04-09T…"
    }
  },
  "refs": {
    "h3": {
      "overall": {"keeper_rate": 0.38, "batches_run": 12},
      "by_recipe": {
        "moto_s0_9101": {"keeper_rate": 0.60, "batches_run": 3}
      }
    }
  },
  "models_by_sport": {
    "moto": {
      "fal-ai/nano-banana-pro/edit": {"keeper_rate": 0.45, "batches_run": 4},
      "fal-ai/gpt-image-1.5/edit":   {"keeper_rate": 0.60, "batches_run": 3}
    }
  }
}
```

### 4.3 Hit Parade sort

`score = (recipe.keeper_rate × 2) + (super_count × 0.5) + (yes_count × 0.1)`

Cold start (0 batches): fall back to `super_count × 2 + yes_count`.

### 4.4 Auto-defaulting — v1 SHOW ONLY, v2 AUTO

**v1:** Display keeper rates on cards and in dropdowns. Let Justin see the signal, don't auto-switch yet.

**v2 (after ≥ 20 batches):**
- "+ New Scene" model dropdown auto-selects `argmax(models_by_sport[sport])`
- Colorway toggle auto-selects `argmax(ref.by_recipe[recipe_id])`

### 4.5 Never deletes — fade, don't kill

Recipes with `keeper_rate < 0.2` over 3+ batches → desaturated card, moved to bottom of rail. Still clickable. One good batch → back to top.

### 4.6 Novel scene auto-promotion — v2

A `is_novel: true` recipe auto-promotes to Hit Parade after 2 batches with `keeper_rate ≥ 0.4`. Before that, lives in an "Experimental" stripe at the bottom.

---

## Part 5 — 29 Pitfalls & Mitigations

| # | Pitfall | Mitigation |
|---|---------|-----------|
| 1 | fal.ai key public leak | Part 0.1 — CF Worker proxy + rotate |
| 2 | Feedback sync silently broken | Part 0.2 — fix SYNC_URL, dynamic filename |
| 3 | Caption loss regression | Prompts snapshotted into each batch record (Part 4.1). Upstream changes can never retroactively wipe context. Every deploy runs `git diff --cached` pre-check. |
| 4 | Cross-device sync clobbering | Fetch-before-push merge. Merge by `batch_id`, never by timestamp. |
| 5 | Partial batch failures | Save counts succeeded only, failed URLs logged separately, per-tile retry. |
| 6 | Cost surprises | Cost preview before firing. Cost logged in batch record. |
| 7 | Mandatory gear forgotten | Auto-injected by sport. Visible in preview; override allowed. |
| 8 | Arm lock is cosmetic | Form uses Per-Scene Arm Decision Table. Snow warns: "use stance, not prompt." |
| 9 | Killed refs drift back in | `KILLED_REFS = ['p1','h1','h4','p5']` enforced client-side everywhere. |
| 10 | Locked CB2 block drifts | Each recipe stores full prompt verbatim. Re-runs use stored text. |
| 11 | Cold start | Hit Parade falls back to super/yes pile rank. First ~10 batches manual. |
| 12 | Novel scene hit rate (~20-40%) | Experimental stripe at bottom. Cost preview. Auto-promote only after 2 successes. |
| 13 | Mobile usability | Tap toggles keeper, tap-hold opens lightbox. 2×3 fits 390px. Mirror `cb-rate.html` touch handlers. |
| 14 | Save before all gens arrive | Button disabled until all tiles terminal. |
| 15 | Race between sync write and next batch | Local state is session source of truth; sync is fire-and-forget; next batch re-fetches before push. |
| 16 | Model scoring polluted across sports | `models_by_sport` scopes counters. NB Pro moto ≠ NB Pro ski. |
| 17 | Normalization drift on recipe IDs | `normalize()` = strip+lower+collapse. Same function at index AND query. |
| 18 | `fal.media` URL expiration | All production refs on GitHub Pages (permanent). `cb2-ref-front.jpg` — flag for Justin to confirm if used in dual-ref prompts; deploy to `/ideas/ref-library/` if needed. |
| 19 | `localStorage` key collisions | All new keys prefixed `cb2_create_`. Documented in code header. |
| 20 | GitHub Pages CDN cache lag | Local state is source of truth for session. Next session re-fetches (~60s). Cachebust query param. |
| 21 | Deploy without testing | Use Claude Preview MCP (`mcp__Claude_Preview__*`) to test `cb-review.html` locally before deploy. |
| 22 | CREATE tab sync fights `cb-feedback.json` sync | Same fixed `SYNC_URL` + filename param. Scenario 4654266 switches by filename. |
| 23 | Accidental huge batch | Hard cap 6/batch. Dropdown limited to 4 or 6. |
| 24 | Dry-run mode for dev | `localStorage.cb2_create_dryrun = true` → skip real fal.ai, return mock URLs. |
| 25 | Recipe card shows stale examples after kills | Filter `examples[]` to exclude URLs that ever appeared in `cb-feedback.json[url].verdict === "no"`. |
| 26 | Proxy password leak | Rate-limit Worker at 100 req/min per IP. Password rotation = 10-second dashboard change. |
| 27 | Worker is down | Worker failures return HTTP 503. Frontend shows: "Generation service unreachable — ping Justin". |
| 28 | Sonnet refiner goes off-script | System prompt explicitly forbids adding subject/wardrobe/framing. Justin sees refined output before firing and can reject or edit inline. |
| 29 | Team mis-uses CREATE (e.g. 50 batches) | Cost preview + Worker rate limit. No hard per-user cap in v1. |

---

## Scope Split

### v1 — Ship First
- Part 0 (all three prereqs — blocking)
- Part 1 (data layer — full)
- Part 2.1 (Rail 1 recipe cards)
- Part 2.2 ("+ New Scene" Flavor B with prompt preview)
- Part 3 (generation + keeper grid — full)
- Parts 4.1, 4.2, 4.3 (batch records + EMA + Hit Parade sort)
- All 29 pitfall mitigations

### v2 — After Signal
- Part 2.3 "Write your own" (Flavor C)
- Part 2.4 "Twist this recipe" (Flavor A)
- Part 4.4 Auto-defaulting (after ≥ 20 batches)
- Part 4.6 Novel scene auto-promotion
- Rail 2 "Creative One-offs" (if Rail 1 isn't enough)
- Failure analytics dashboard

### Deferred (absorbed from old plan, not blocking)
- Automated health checks — valuable parallel track
- `fal.media` reference backup to Drive — mitigated by GitHub Pages-hosted refs
- Cancel Recraft subscription — admin task

### New workstream (added 2026-04-09) — Permanent archival pipeline

**Problem:** Generated images live on `fal.media` URLs which expire weeks-to-months after creation. Runway videos live on `runway.com` / `fal.media` with similar expiration. `cb-keepers.json` and `cb-feedback.json` reference these URLs directly. Once they expire, every super-liked / kept image becomes a broken link.

**Decision (Justin, 2026-04-09):** "Every image Justin ever liked and super-liked is permanently archived" on GitHub Pages. He's paying for the storage and trusts GitHub as much as Drive.

**Scope:**
1. **Archival script** (`scripts/archive_winners.py`): reads `cb-feedback.json`, finds every URL with `verdict === "yes" || "super"`, downloads the original to `winners/{sport}/{id}.jpg`, rewrites the URL in a new `cb-keepers-archived.json` → GitHub Pages hosts both the images and the rewritten JSON.
2. **Incremental mode:** on every CREATE batch save (Part 3.3), if a keeper is marked, immediately pull the image from `fal.media` and commit to `winners/pending/{batch_id}_{idx}.jpg`. Background job promotes `pending/` → final path.
3. **Full-res download button:** in `cb-review.html` **Gallery tab only**, each thumbnail gets a ⬇ button that links to the archived file (if available) or falls back to the original `fal.media` URL. NOT added to cb-rate.html, CREATE tab keeper grid, or review flows — gallery is the only place Justin wants it.
4. **Migration pass for existing corpus:** one-time run across the 694-photo corpus (cb-keepers.json + cb-feedback.json historical data). Catches anything already on the brink of expiring.

**How it fits in:** Independent of the CREATE tab. Can ship before or after it. Probably ships right after the Tron A/B (this session) as a small 2-3 file addition — doesn't need the CF Worker gating since it's read-only on fal.media.

**Storage note:** GitHub Pages itself is unlimited; repo size caps at 1 GB recommended. 694 photos @ ~500KB each = ~350MB. Comfortably fits. Videos would push it — may need to keep videos on external storage or use git-lfs.

---

## Files to Modify (current repo paths)

- **`/Users/justinbarad/code/cb2-ideas/cb-review.html`**
  - Remove 3 hardcoded FAL const declarations (lines 1584, 1671, 1693), replace with `proxyCall()` helper
  - Add modal HTML + JS for first-use team password prompt
  - Fix `SYNC_URL` (line 393) and rewrite `syncFeedback()` to send `filename` field
  - Add `<div class="tab">CREATE</div>` to tab bar
  - Add `'create'` to `tabList` (currently `['new','done','progress','gallery','videos','aiscore']`)
  - Add `#createArea` body markup
  - Add CREATE tab JS: recipe index builder, rail renderers, keeper grid, lightbox (copied from `cb-rate.html`), generation/polling, Sonnet refine flow, save flow
  - Add top-of-file comment: `// NEVER hardcode API keys — all network calls go through proxyCall() → CF Worker`
- **`/Users/justinbarad/code/cb2-ideas/cb-learning.json`** — NEW empty scaffold (Part 0.3)
- **Cloudflare Worker** (new project, ~20 lines) — proxies fal.ai + Anthropic with shared password + rate limit
- **Make.com scenario 4654266** — update to accept dynamic `filename` field

## Files to Read (reference, do not modify)

- `/Users/justinbarad/code/cb2-ideas/cb-keepers.json` — recipe source data
- `/Users/justinbarad/code/cb2-ideas/cb-rate.html` — lightbox functions to copy (`lbDist`/`lbReset`/`lbApply`, lines 706–789)
- `/Users/justinbarad/code/cb2-ideas/rotated-refs/*.jpg` — ref library (h3, h5, h6, p4, p6)
- `/Users/justinbarad/code/cb2-ideas/CLAUDE.md` — mandatory gear, arm rules, per-scene table, locked CB2 block, failure log

---

## External Actions Justin Must Take

1. Create a Cloudflare account (free, 5 min) — or confirm Vercel / Deno Deploy instead
2. Provide a shared team password (one-time) → CF Worker env var
3. Rotate the leaked fal.ai key at the dashboard after Worker deploys; new key → Worker env var
4. Provide Anthropic API key for Sonnet refiner → same env var location
5. Paste team password once per browser when first-use modal appears
6. **Tron refs:** already shot (2026-04-09, 20 photos). Ref A/B test will auto-run — Justin rates the generated images (not raw refs) and winners become `t1…tN`.
7. Confirm whether `cb2-ref-front.jpg` needs GitHub Pages deploy for dual-ref prompts

---

## Verification — End-to-End Smoke Test

1. Deploy CF Worker, set env vars (`FAL_KEY`, `ANTHROPIC_KEY`, `SHARED_PASSWORD`). Confirm worker URL responds to a test ping.
2. Open `cb-review.html` fresh → password modal → paste. Confirm Video Lab still works (uses `proxyCall`).
3. Click CREATE tab → Hit Parade renders with cold-start ranking.
4. Click a recipe card → lightbox opens with all examples, pinch/zoom works.
5. Close lightbox. Click "Make 4 more like this" → cost preview → confirm → 4 keeper grid skeletons appear.
6. Wait for gens. Expect 4/4 tiles populated (or clear failure state with retry).
7. Mark 2 as keepers. Click Save batch. Expect toast + Hit Parade re-sort.
8. Hard reload. Expect keeper rate persisted from GitHub `cb-learning.json`.
9. Open on different device. Expect same data after ~60s CDN propagation.
10. Open "+ New Scene" → sport=moto, colorway=Hunter, scene="desert sandstorm canyon at dusk".
11. Click Refine with Sonnet → expect industry-standard rewrite. Accept.
12. Expect constructed prompt shows refined scene + helmet + gloves + jacket + locked CB2 block. Inline-edit, submit.
13. Mark keepers → save → new "novel" recipe appears in Experimental stripe.
14. Open "+ New Scene" → colorway=Tron → expect appropriate tooltip based on current Tron A/B status (in progress / winners available).
15. DevTools → confirm no plaintext fal.ai or Anthropic key in HTML source.
16. `git diff --cached` before commit → no accidental deletions.
17. Visit from incognito → expect password modal, cannot generate without it.

---

## Open Design Defaults (changeable)

1. Constructed prompt is inline-editable in "+ New Scene" (default: yes)
2. Default batch size: 6 (6 = $0.90 NB Pro / $0.48 NB2; 4 = $0.60 / $0.32)
3. Default model per sport = all-time high scorer (moto=GPT 1.5, ski=NB2, snow/mtb/sled=NB Pro)
4. Lightbox is single-tap-to-open (not double-tap — desktop convention)
5. Keeper toggle is ♡, not a checkbox — matches `cb-rate.html` super-like visual language
6. Sonnet refine is opt-in (button, not auto-fire) — preserves Justin's agency
7. CF Worker is the proxy choice — swappable for Vercel/Deno

---

## Changelog vs RTF source

- **2026-04-09** — imported from `~/Desktop/Updated Plan.rtf`.
  - Paths rewritten from old iCloud location (`~/Documents/Claude Code/ideas/`) to current repo (`~/code/cb2-ideas/`).
  - Tron ref status updated: 20 photos downloaded, A/B test is the next action, Justin rates generated images (not raw refs). Jordan shot multi-orientation variants so no `sips -r 180` post-processing needed — physical rotation, not post-hoc.
  - Scope split corrected: "All 25 pitfall mitigations" → "All 29 pitfall mitigations" (RTF heading said 25 but numbered list went to 29).
  - `🔥 NB Pro 25` button retired in same session (Justin finished the 25-photo batch).
