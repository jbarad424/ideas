/**
 * CREATE Tab Part 1 Data Layer (PLAN-CREATE-TAB-V2.md §1)
 *
 * Pure-data module. No network calls, no DOM, no external deps.
 * Safe to import into cb-review.html once the CREATE tab UI is built.
 *
 * Exports (attached to window.CB2_CREATE):
 *   REFS                       — production reference library (incl Tron 2026-04-09)
 *   KILLED_REFS                — never show, never default
 *   MANDATORY_GEAR             — sport → required wardrobe string
 *   DEFAULT_MODEL_BY_SPORT     — sport → fal.ai endpoint
 *   PER_SCENE_ARM              — scene key → arm lock + seed
 *   LOCKED_CB2_BLOCK_LEFT      — canonical CB2 prompt block for LEFT arm
 *   LOCKED_CB2_BLOCK_RIGHT     — same for RIGHT arm
 *   normalizePrompt(s)         — strip whitespace, lowercase, collapse
 *   recipeIdFor(prompt, seed)  — SHA-256 hash, stable across sessions
 *   buildRecipeIndex(keepers)  — group cb-keepers.json items into recipes
 *   filterRefsByColorway(cw)   — REFS entries for a colorway, excl killed
 *   sortRecipesColdStart(recs) — rank by super_count*2 + yes_count
 *   sortRecipesLearned(recs, l) — rank by EMA keeper_rate from cb-learning.json
 */

(function (global) {
  "use strict";

  //--------------------------------------------------------------------------
  // 1.2 Production ref library — authoritative, mirrored in CLAUDE.md
  //--------------------------------------------------------------------------

  const REFS = {
    // Hunter — 2026-04-03 shoot (Jordan), rotated 180° in 2026-04-08 A/B
    h3: { colorway: "Hunter", type: "jacket", tier: 1, source: "jordan-2026-04-03",
          url: "https://jbarad424.github.io/ideas/rotated-refs/h3.jpg",
          name: "IMG_0534_Hunter_Jacket_A" },
    h5: { colorway: "Hunter", type: "jacket", tier: 1, source: "jordan-2026-04-03",
          url: "https://jbarad424.github.io/ideas/rotated-refs/h5.jpg",
          name: "IMG_0542_Hunter_Jacket_C",
          notes: "Use for everything EXCEPT snow (2 wrongArm flags on snow in batch v1)" },
    h6: { colorway: "Hunter", type: "product", tier: 2, source: "jordan-2026-04-03",
          url: "https://jbarad424.github.io/ideas/rotated-refs/h6.jpg",
          name: "IMG_0566_Hunter_Product_C" },

    // Patriot — 2026-04-03 shoot (Jordan)
    p4: { colorway: "Patriot", type: "jacket", tier: 1, source: "jordan-2026-04-03",
          url: "https://jbarad424.github.io/ideas/rotated-refs/p4.jpg",
          name: "IMG_0550_Patriot_Jacket_B" },
    p6: { colorway: "Patriot", type: "jacket", tier: 1, source: "jordan-2026-04-03",
          url: "https://jbarad424.github.io/ideas/rotated-refs/p6.jpg",
          name: "IMG_0560_Patriot_Jacket_D" },

    // Tron — 2026-04-09 shoot (Justin himself, multi-orientation physical variants)
    // Tier 1 = pure 4×5 in A/B, Tier 2 = ≥3 fives, 0 rejects
    t18: { colorway: "Tron", type: "product", tier: 1, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t18.jpeg",
           name: "IMG_7201_Tron_Product_A",
           notes: "CHAMPION — only pure 4×5 with ZERO rot180 flags in entire Tron A/B" },
    t01: { colorway: "Tron", type: "jacket", tier: 1, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t01.jpeg",
           name: "IMG_7184_Tron_Glove" },
    t03: { colorway: "Tron", type: "jacket", tier: 1, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t03.jpeg",
           name: "IMG_7186_Tron_Sleeve_A" },
    t11: { colorway: "Tron", type: "jacket", tier: 1, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t11.jpeg",
           name: "IMG_7194_Tron_Sleeve_B" },
    t05: { colorway: "Tron", type: "jacket", tier: 2, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t05.jpeg",
           name: "IMG_7188_Tron_Sleeve_C" },
    t09: { colorway: "Tron", type: "jacket", tier: 2, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t09.jpeg",
           name: "IMG_7192_Tron_Sleeve_D" },
    t17: { colorway: "Tron", type: "product", tier: 2, source: "justin-2026-04-09",
           url: "https://jbarad424.github.io/ideas/ref-library/tron-raw/t17.jpeg",
           name: "IMG_7200_Tron_Product_B" },

    // Ref C — J&Mike Dual baseline (kept for backwards compat with older
    // recipes that use it, but superseded by colorway-specific refs above)
    refc: { colorway: "Hunter", type: "dual", tier: 1, source: "legacy",
            url: "https://lh3.googleusercontent.com/d/1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7=w800",
            name: "J&Mike Dual (Ref C)",
            notes: "Two-people baseline. 0 flags in original A/B." },
  };

  const KILLED_REFS = new Set([
    "h1", "h4",           // 3 rot=1 fails each in 2026-04-08 rotation A/B
    "p1", "p5",           // 3 rot=1 fails + production batch v1 kill (p5)
    "t10", "t16",         // 2026-04-09 Tron A/B kills (score-1 + orientation)
  ]);

  //--------------------------------------------------------------------------
  // 1.3 Mandatory gear by sport
  //--------------------------------------------------------------------------

  const MANDATORY_GEAR = {
    moto: "full-face helmet, leather riding jacket with armor, thick leather riding gloves",
    ski:  "ski helmet, goggles, ski gloves, ski jacket",
    snow: "snowboard helmet, gloves, snowboard jacket",
    mtb:  "full-face DH helmet, gloves, jersey with armor",
    sled: "full-face helmet, snowmobile gloves, snowmobile suit",
  };

  //--------------------------------------------------------------------------
  // 1.4 Per-sport default model
  // v1 is hand-picked from CLAUDE.md all-time highs.
  // v2 will override from models_by_sport EMA counters in cb-learning.json.
  //--------------------------------------------------------------------------

  const DEFAULT_MODEL_BY_SPORT = {
    moto: "fal-ai/gpt-image-1.5/edit",    // 99 GPT masked inpaint, 90 GPT solo
    ski:  "fal-ai/nano-banana-2/edit",    // 100 NB2
    snow: "fal-ai/nano-banana-pro/edit",  // 99 NB Pro
    mtb:  "fal-ai/nano-banana-pro/edit",  // 94-98 NB Pro
    sled: "fal-ai/nano-banana-pro/edit",
  };

  //--------------------------------------------------------------------------
  // Per-Scene Arm Decision Table (CLAUDE.md)
  //--------------------------------------------------------------------------

  const PER_SCENE_ARM = {
    "moto_s0": { seed: 9101, arm: "LEFT", label: "coastal golden hour" },
    "moto_s1": { seed: 9102, arm: "LEFT", label: "desert canyon" },
    "mtb_s0":  { seed: 9201, arm: "LEFT", label: "forest descend" },
    "mtb_s1":  { seed: 9202, arm: "LEFT", label: "alpine ridge" },
    "ski":     { seed: null, arm: "RIGHT", label: "ski carve" },
    "snow_L":  { seed: 9401, arm: "LEFT",  label: "snowboard regular stance", requires: "h3" },
    "snow_R":  { seed: 9402, arm: "RIGHT", label: "snowboard goofy stance",   requires: "h3" },
    "sled":    { seed: null, arm: "LEFT",  label: "snowmobile" },
  };

  // CRITICAL: prompt arm-lock text is COSMETIC only (CLAUDE.md 2026-04-08).
  // Real arm control = reference image geometry + rider body orientation.
  // For snow specifically, use h3 + stance to flip L/R.
  const PROMPT_ARM_LOCK_IS_COSMETIC = true;

  //--------------------------------------------------------------------------
  // Locked CB2 block — NEVER modify these strings outside of a prompt rewrite
  // session with Justin. They're the most expensive thing in the whole repo.
  //--------------------------------------------------------------------------

  // Simple single-ref version (FLUX 2 Flex, NB Pro, NB2, GPT Image 1.5)
  const LOCKED_CB2_BLOCK_LEFT =
    "the wearable remote from image 1 with its velcro strap wrapped fully around the LEFT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, PLUS button closest to wrist, LED window closest to wrist, five round tactile buttons";

  const LOCKED_CB2_BLOCK_RIGHT =
    "the wearable remote from image 1 with its velcro strap wrapped fully around the RIGHT lower forearm OVER the jacket sleeve, positioned halfway between wrist and elbow, MINUS button closest to wrist, LED window closest to elbow, five round tactile buttons";

  //--------------------------------------------------------------------------
  // Normalization + recipe ID
  //--------------------------------------------------------------------------

  function normalizePrompt(s) {
    if (typeof s !== "string") return "";
    return s.trim().toLowerCase().replace(/\s+/g, " ");
  }

  // SHA-256 via SubtleCrypto (browser-native, no deps).
  // Returns a hex string. Fallback to a fast non-crypto hash if SubtleCrypto
  // isn't available (shouldn't happen in modern browsers, but defensive).
  async function recipeIdFor(prompt, seed) {
    const key = normalizePrompt(prompt) + "|" + String(seed);
    if (typeof crypto !== "undefined" && crypto.subtle && crypto.subtle.digest) {
      const buf = new TextEncoder().encode(key);
      const hash = await crypto.subtle.digest("SHA-256", buf);
      return Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("")
        .slice(0, 16); // 16 hex chars is plenty to avoid collisions at this scale
    }
    // Simple FNV-1a fallback
    let h = 0x811c9dc5;
    for (let i = 0; i < key.length; i++) {
      h ^= key.charCodeAt(i);
      h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
    }
    return "fnv_" + h.toString(16);
  }

  //--------------------------------------------------------------------------
  // Recipe index builder
  //--------------------------------------------------------------------------

  /**
   * Groups cb-keepers.json items into recipes by (normalized prompt, seed).
   *
   * @param {Object} keepers — parsed cb-keepers.json ({meta, items: {url: item}})
   * @returns {Promise<Array<Recipe>>} — unsorted recipe list
   *
   * Recipe shape:
   *   {
   *     id: "a1b2c3d4…",
   *     prompt: "…verbatim from first example…",
   *     seed: 9101,
   *     sport: "moto",
   *     refs_observed: ["h3", "p4", "refc"],
   *     model: "nano-banana-pro",         // modal model across examples
   *     examples: [{url, super, ref, model}, …],
   *     super_count: 4,
   *     yes_count: 7,
   *   }
   */
  async function buildRecipeIndex(keepers) {
    if (!keepers || !keepers.items) return [];

    const items = Object.entries(keepers.items).map(([url, item]) => ({ url, ...item }));
    const byKey = new Map();

    for (const item of items) {
      const prompt = item.prompt || "";
      const seed = item.seed != null ? item.seed : "NA";
      const key = normalizePrompt(prompt) + "|" + seed;

      if (!byKey.has(key)) {
        byKey.set(key, {
          _key: key,
          prompt,        // keep the unnormalized original for display
          seed: item.seed,
          sport: item.sport || detectSport(prompt),
          refs_observed: new Set(),
          models: new Map(),   // model → count, for modal selection
          examples: [],
          super_count: 0,
          yes_count: 0,
        });
      }

      const r = byKey.get(key);
      r.examples.push({
        url: item.url,
        super: item.label === "super",
        ref: item.ref && item.ref.id,
        model: item.model,
      });
      if (item.ref && item.ref.id) r.refs_observed.add(item.ref.id);
      if (item.model) r.models.set(item.model, (r.models.get(item.model) || 0) + 1);
      if (item.label === "super") r.super_count++;
      if (item.label === "super" || item.label === "yes") r.yes_count++;
    }

    // Finalize: convert Sets/Maps, compute stable id
    const recipes = [];
    for (const r of byKey.values()) {
      const id = await recipeIdFor(r.prompt, r.seed);
      let modalModel = null;
      let maxCount = 0;
      for (const [m, c] of r.models) {
        if (c > maxCount) { modalModel = m; maxCount = c; }
      }
      recipes.push({
        id,
        prompt: r.prompt,
        seed: r.seed,
        sport: r.sport,
        refs_observed: Array.from(r.refs_observed).filter((id) => !KILLED_REFS.has(id)),
        model: modalModel,
        examples: r.examples,
        super_count: r.super_count,
        yes_count: r.yes_count,
      });
    }
    return recipes;
  }

  // Fallback sport detector — mirrors galDetectSport() in cb-review.html
  function detectSport(prompt) {
    const p = (prompt || "").toLowerCase();
    if (/motorcycle|moto\b|rider|motorbike|bike.*highway|riding.*jacket/.test(p)) return "moto";
    if (/mountain.*bik|mtb\b|singletrack|trail rider|downhill/.test(p)) return "mtb";
    if (/ski(?!n)|skier|slalom|carve/.test(p)) return "ski";
    if (/snowboard/.test(p)) return "snow";
    if (/snowmobile|sled|snowcat/.test(p)) return "sled";
    return "other";
  }

  //--------------------------------------------------------------------------
  // Filtering + sorting
  //--------------------------------------------------------------------------

  function filterRefsByColorway(colorway) {
    return Object.entries(REFS)
      .filter(([id, r]) => r.colorway === colorway && !KILLED_REFS.has(id))
      .map(([id, r]) => ({ id, ...r }))
      .sort((a, b) => (a.tier || 99) - (b.tier || 99)); // tier 1 first
  }

  // Cold-start sort: super × 2 + yes (CLAUDE.md Part 1.1 + Part 4.3)
  function sortRecipesColdStart(recipes) {
    return recipes.slice().sort((a, b) => {
      const scoreA = a.super_count * 2 + a.yes_count;
      const scoreB = b.super_count * 2 + b.yes_count;
      return scoreB - scoreA;
    });
  }

  // Learned sort: keeper_rate × 2 + super × 0.5 + yes × 0.1
  // learning = parsed cb-learning.json
  function sortRecipesLearned(recipes, learning) {
    const recipeStats = (learning && learning.recipes) || {};
    return recipes.slice().sort((a, b) => {
      const rateA = (recipeStats[a.id] && recipeStats[a.id].keeper_rate) || 0;
      const rateB = (recipeStats[b.id] && recipeStats[b.id].keeper_rate) || 0;
      const scoreA = rateA * 2 + a.super_count * 0.5 + a.yes_count * 0.1;
      const scoreB = rateB * 2 + b.super_count * 0.5 + b.yes_count * 0.1;
      return scoreB - scoreA;
    });
  }

  //--------------------------------------------------------------------------
  // Export
  //--------------------------------------------------------------------------

  const CB2_CREATE = {
    REFS,
    KILLED_REFS,
    MANDATORY_GEAR,
    DEFAULT_MODEL_BY_SPORT,
    PER_SCENE_ARM,
    PROMPT_ARM_LOCK_IS_COSMETIC,
    LOCKED_CB2_BLOCK_LEFT,
    LOCKED_CB2_BLOCK_RIGHT,
    normalizePrompt,
    recipeIdFor,
    buildRecipeIndex,
    filterRefsByColorway,
    sortRecipesColdStart,
    sortRecipesLearned,
    detectSport,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = CB2_CREATE;          // Node / test harness
  }
  if (typeof global !== "undefined") {
    global.CB2_CREATE = CB2_CREATE;       // Browser: window.CB2_CREATE
  }
})(typeof window !== "undefined" ? window : globalThis);
