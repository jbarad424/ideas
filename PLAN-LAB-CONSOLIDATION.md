# Plan: Gallery + Lab Consolidation

## Goal
Collapse 4 tabs (Gallery, Create, Video Lab, Discover) into 3 (Gallery, Lab, Discover) with a unified sequential funnel for all "do something with this image" actions.

## Current State (v11.5)
- **Gallery** — flat grid of 700+ images, Photos/Videos toggle, filters (show/sport/model), sort by recency, paginated to 60
- **Create** — Hit Parade (recipe cards grouped by seed, scored by keeper_rate), New Scene form, Run Again, Twist
- **Video Lab** — source image + platform/duration/direction + Job History
- **Discover** — CB2-free sketches + inspiration upload

## Target State
- **Gallery** — everything it does now PLUS a "Group by recipe" toggle that collapses super-likes into Hit Parade cards. Every image/recipe gets one button: "Bring to Lab"
- **Lab** — unified sequential funnel for stills + video. Replaces both Create and Video Lab.
- **Discover** — stays as-is, "Use in Lab" button sends to Lab

---

## Part 1: Gallery — Add "Group by Recipe" Mode

### 1.1 New toggle in filter bar
Add a toggle button in the filter bar row: **"Grouped"** (off by default). When ON, the gallery switches from flat grid to recipe cards. When OFF, flat grid as today.

### 1.2 Recipe grouping logic
Reuse the existing `buildRecipes()` from CR object — it already groups keepers by sport+seed into recipe objects. In grouped mode:
- Show only recipes with super-likes or keeper_rate > 0 (filter out noise)
- Each card shows: best thumbnail, sport icon, model badge, keeper count, super count, keeper_rate badge
- Cards sorted by the same score formula: `keeper_rate × 2 + super_count × 0.5 + yes_count × 0.1`
- Click card → expand inline to show all images in that recipe (horizontal scroll row)
- Each expanded image has ♥ super-like button
- Card-level action button: **"Bring to Lab →"**

### 1.3 "Bring to Lab" button on every image
In flat grid mode: clicking an image opens the overlay (as today), but the action buttons are simplified:
- **♥ Super-like** (keep)
- **Archive** (hide)
- **Bring to Lab →** (replaces both "Make More Stills" and "Make Video")
- **Download**

In grouped mode: the recipe card has a single "Bring to Lab →" button that sends the recipe's primary example to the Lab.

### 1.4 What to remove from Gallery
- "Make More Stills" button (moved to Lab)
- "Make Video" button (moved to Lab)
- The inline Make More panel (galToggleMM, galGenerate, galColorwaySwap — all move to Lab)

---

## Part 2: Lab — The Unified Action Center

### 2.1 Tab structure
Replace both CREATE and VIDEO LAB tabs with a single **LAB** tab. The tab bar becomes:
```
GALLERY | LAB | DISCOVER
```

### 2.2 Lab states
The Lab has 4 states, rendered sequentially on the same page:

**State 0: Empty (no source)**
- "Pick an image from the Gallery or Discover tab"
- Show Hit Parade below as quick-pick cards (reuse recipe card rendering)
- Show Job History (video jobs) at the bottom

**State 1: Source loaded**
- Big source image at top with label + model + score
- Two buttons: **"Make Stills"** | **"Make Video"**

**State 2a: Stills funnel**
Appears below State 1 when "Make Stills" is clicked:
- Two options: **"Run Again"** | **"Twist It"**
- **Run Again path:**
  - Shows the full original prompt (read-only, scrollable)
  - Batch size picker: [4] [6]
  - Colorway swap buttons (Hunter / Patriot / Tron) — optional, changes ref only
  - **"Generate →"** button with cost estimate
  - Results grid appears below (tiles with ♥ keep buttons)
  - "Save keepers" / "Archive all" bar at bottom
- **Twist path:**
  - Side-by-side layout:
    - LEFT: original prompt (read-only, full text, scrollable)
    - RIGHT: editable form (sport, colorway, model, vibe, gender, scene, gear)
  - "Refine with Claude" button
  - "Assemble → Preview" shows the final prompt
  - **"Generate →"** button with cost estimate
  - Results grid appears below (same as Run Again)

**State 2b: Video funnel**
Appears below State 1 when "Make Video" is clicked:
- Platform dropdown (Seedance, Kling, Veo, Sora, Runway)
- Duration picker (per platform)
- Aspect ratio (9:16 / 16:9 / 1:1)
- Direction textarea
- "Refine with Claude" button
- **"Create Video →"** button with cost confirmation
- Progress/status area
- Completed video with Keep/Archive + Download + "Create again"

### 2.3 Data flow
- `labSource` — the selected image (from Gallery "Bring to Lab" or from a recipe card)
- `labMode` — null (empty), 'stills', 'video'
- `labStillsMode` — null, 'again', 'twist'
- `labBatch` — the current batch (tiles, status, results) — persisted in localStorage
- `labVideoJob` — the current video job (same as today's vidLabJob)

### 2.4 What moves from CREATE to Lab
- `buildPayload()` — unchanged
- `startBatch()` — becomes `labRunAgain()`
- `fireNewScene()` — becomes `labTwist()`
- `fireBatch()` / `fireOne()` — unchanged
- `buildRecipes()` / `scoreRecipes()` — moves to Gallery (for grouped mode) AND Lab (for empty-state Hit Parade)
- `assemblePrompt()` / `refineWithSonnet()` — moves to Lab twist form
- Learning loop (`saveBatch`, `applyCounterBump`, `loadLearning`) — stays, used by Lab

### 2.5 What moves from VIDEO LAB to Lab
- `vidLabGenerate()` — becomes `labCreateVideo()`
- `vidLabResumePoll()` — unchanged
- `vidLabCheck()` — becomes part of Lab init
- `vidLabUpdateOptions()` — unchanged
- Job History rendering — moves to Lab bottom section
- Keep/Archive/CreateAgain — unchanged

### 2.6 Hit Parade in Lab empty state
When you open the Lab with no source image:
- Show "Pick an image, or start from a proven recipe:"
- Render the Hit Parade recipe cards (same as today's CREATE parade)
- Clicking a recipe card loads it as the Lab source (State 1)
- Also show Job History below the recipes

---

## Part 3: Sequential Page Build (UX)

The Lab page GROWS DOWNWARD. Each choice reveals the next section. Nothing disappears. Scroll position stays natural.

```
┌─ ALWAYS VISIBLE ──────────────────────────────┐
│ Source image + metadata                         │
│ [Make Stills]  [Make Video]                     │
├─ VISIBLE AFTER "Make Stills" ──────────────────┤
│ [Run Again]  [Twist It]                         │
├─ VISIBLE AFTER "Run Again" ────────────────────┤
│ Original prompt (read-only)                     │
│ Batch: [4] [6]  Colorway: [H] [P] [T]         │
│ [Generate → ~$0.60]                             │
├─ VISIBLE AFTER generation completes ───────────┤
│ ♥ ♥ ♡ ♥  (4 tiles)                            │
│ [Save 3 keepers]  [Archive all]                 │
└────────────────────────────────────────────────┘
```

Each section has a subtle top-border separator and a small "collapse" chevron in case the user wants to scroll back up.

---

## Part 4: What Gets Deleted

- The entire `CREATE` tab HTML (`createArea` div)
- The `CR.renderParade()`, `CR.renderNewScene()`, `CR.renderBatch()` functions (replaced by Lab equivalents)
- The `VIDEO LAB` tab HTML (`videosArea` div) — replaced by Lab video section
- The old `galToggleMM`, `galGenerate`, `galColorwaySwap` inline panel (replaced by Lab stills funnel)
- The `vidLabSource` panel (replaced by Lab source area)
- Tab count drops from 4 to 3

## Part 5: What Gets Preserved (DO NOT TOUCH)

- `buildPayload()` — the ref resolution logic is finally correct, don't change it
- `pickRefAuto()` — weighted random ref selection
- `CB2_BLOCK` — the locked product description
- `assemblePrompt()` — the prompt assembly with scene splitting
- `refineWithSonnet()` — the Claude refiner with sport/model/vibe awareness
- Learning loop (`applyCounterBump`, `saveBatch`, `loadLearning`)
- `buildRecipes()` / `scoreRecipes()` — recipe grouping logic
- ALL_IMAGES, ALL_VIDEOS arrays
- Feedback system (D, S, getC, isR, galScore, galIsAccepted, galIsSuper)
- Archive manifest loading (loadArchiveManifest, archivedUrl, archivedVideoUrl)
- The Gallery filter system (filter bar, faceted counts, pagination)

---

## Build Order

1. **Gallery: add "Group by recipe" toggle** (30 min)
   - New button in filter bar
   - Reuse buildRecipes() output
   - Recipe cards in the gallery grid area
   - "Bring to Lab" button on cards + overlay

2. **Lab: scaffold the tab + states** (30 min)
   - New `labArea` div
   - State machine: empty → source → stills/video → results
   - Render functions for each state
   - localStorage persistence for labSource + labBatch

3. **Lab: wire Run Again** (20 min)
   - Move startBatch logic → labRunAgain
   - Prompt display (read-only)
   - Batch size picker + colorway swap
   - Results grid with ♥ buttons + save bar

4. **Lab: wire Twist** (20 min)
   - Move assemblePrompt + refineWithSonnet → Lab twist form
   - Side-by-side original vs edit
   - Same results grid

5. **Lab: wire Video** (20 min)
   - Move vidLabGenerate → labCreateVideo
   - Platform/duration/direction controls
   - Poll + results display
   - Job History at bottom

6. **Lab: empty state Hit Parade** (15 min)
   - Show recipe cards when no source
   - Click card → load as source

7. **Delete old tabs** (15 min)
   - Remove CREATE tab HTML + tab bar entry
   - Remove VIDEO LAB tab HTML + tab bar entry
   - Update setTab() to 3-tab array
   - Clean up dead code

8. **Test everything** (30 min)
   - Run Again on proven recipe → verify correct ref + model
   - Twist → verify form pre-populates correctly
   - Video → verify platform picker + polling
   - Gallery grouped mode → verify recipe cards
   - Bring to Lab from Gallery → verify source loads
   - Bring to Lab from Discover → verify handoff
   - Tab persistence → verify Lab remembers state on reload
   - Mobile → verify page loads fast

---

## Estimated Time: 3-4 hours

## Risk Assessment
- **Low risk:** Gallery changes (additive, doesn't touch existing filters)
- **Medium risk:** Lab scaffold (new code, but reuses proven functions)
- **High risk:** Deleting old tabs (if we miss a reference, things break)
- **Mitigation:** Build Lab FIRST with old tabs still present. Test everything. THEN delete old tabs as the last step.

---

*Plan written: April 10, 2026, v11.5 stable*
