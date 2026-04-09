# Proposed CLAUDE.md updates (Tron colorway unlocked)

**Status:** DRAFT for Justin's review. I did NOT commit these changes to CLAUDE.md directly because (a) the file has pre-existing uncommitted diffs from a prior session, and (b) ref-library changes warrant a manual eyeball before they become canonical.

**Rationale:** 80 NB Pro gens completed, Justin rated 77/80, patterns locked. Tron is now production-ready with 4 Tier-1 refs and 3 Tier-2 backups. 2 refs kill-listed.

---

## Section 1: Add Tron block to the "Reference Rotation Rule" production ref library table

**Insert after the Patriot p6 row:**

```markdown
| **Tron — production-ready 2026-04-09**                                                                           |
| t18 | IMG_7201_Tron_Product_A  | Tron    | product | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t18.jpeg`  |
| t01 | IMG_7184_Tron_Glove      | Tron    | jacket  | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t01.jpeg`  |
| t03 | IMG_7186_Tron_Sleeve_A   | Tron    | jacket  | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t03.jpeg`  |
| t11 | IMG_7194_Tron_Sleeve_B   | Tron    | jacket  | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t11.jpeg`  |
```

**Why these 4 are Tier-1:** all four scored pure 4×5s across both sports (moto_s0/s1, mtb_s0/s1) in the 2026-04-09 A/B, using NB Pro with identical prompts and seeds (9101/9102/9201/9202) to the Hunter/Patriot rotation A/B for direct comparison. **t18 is the one that scored 4×5 with ZERO rotation flags** — the only pure-pure in the entire 20-ref batch. The others got rot180 flags on 3/4 cells but Justin's rating semantics (and Jordan's intuition) treat rot180 as cosmetic, not a blocker.

**Tier-2 backups (≥ 3 fives, 0 rejects — use if Tier-1 causes scene-specific issues):**

```markdown
| t05 | IMG_7188_Tron_Sleeve_C   | Tron    | jacket  | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t05.jpeg`  |
| t09 | IMG_7192_Tron_Sleeve_D   | Tron    | jacket  | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t09.jpeg`  |
| t17 | IMG_7200_Tron_Product_B  | Tron    | product | `https://jbarad424.github.io/ideas/ref-library/tron-raw/t17.jpeg`  |
```

## Section 2: Killed refs list

**Append to `KILLED_REFS`:**

```
KILLED_REFS = ["p1", "h1", "h4", "p5", "t10", "t16"]
```

- **t10** (IMG_7193): produced a score-1 on mtb_s1 (aesthetic composition failure — two-rider weird frame) + one score-3. Not worth the risk when better refs exist.
- **t16** (IMG_7199): upside-down capture (MINUS at top instead of PLUS at top), produced a score-1 on mtb_s1 + one unrated on mtb_s0. Model can still make 5s from it but with high rot180 rate and occasional aesthetic rejection.

## Section 3: Update "Tron unvalidated" note

**Find in "Reference Photo Rotation Rule" section:**
> Tron is unvalidated — no on-jacket ref exists. First Tron signal came from `dual_ref_test.py`…

**Replace with:**
> **Tron is production-ready (2026-04-09).** Justin shot 20 Tron refs himself on 2026-04-09 (Hunter/Patriot were Jordan's shoot on 2026-04-03; Tron is Justin's). The A/B test (`tron_ab_test.py`, `tron_ab_results.json`, ratings in `ratings/tron_ab_ratings_2026-04-09.json`) identified t18 as the sole pure-gold reference (4×5, 0 flags) plus t01/t03/t11 as Tier-1 backups (pure 4×5 with cosmetic rot180). Unlike the Hunter/Patriot shoot, Justin captured multi-orientation variants physically, so no `sips -r 180` post-processing was needed. Per Justin + Jordan: rot180 flags are cosmetic, not blockers — production can ship refs with or without.

## Section 4: Per-Scene Arm Decision Table — add Tron column

No table change needed. Tron uses the same per-scene arm locks as Hunter/Patriot (default LEFT for moto/mtb, scene-specific for snow/ski).

## Section 5: Key Resources — add a row

```markdown
| Tron ref A/B results | https://jbarad424.github.io/ideas/tron-ab-review.html |
```

## Section 6: Stats update

**Key Stats section, bump counts:**
- Add 80 new Tron A/B gens to the total
- Note: Tron colorway validated, 4 Tier-1 refs + 3 Tier-2 backups, 2 killed
- Key insight: reshoot-ready pattern for Hunter/Patriot (see Section 7 below)

---

# Section 7: Pattern analysis for Hunter/Patriot reshoot (Justin's offer)

**Justin's offer (2026-04-09):** *"If you learn anything about these reference photos with the Tron, I can also retake some of the Hunter and Patriot if I'm getting like some really good results with certain orientations of the Tron."*

**What Tron winners have in common (based on reading t18, t01, t03, t11):**

| Attribute | t18 🏆 (pure 5s, 0 flags) | t01/t03/t11 (pure 5s, 3 rot180) |
|-----------|---------------------------|----------------------------------|
| Mount | Standalone on wood table | On leather jacket sleeve |
| Orientation | **Vertical, PLUS at top** | Landscape (horizontal) |
| Lighting | Warm natural, even | Warm natural, even |
| Strap | Wrapped fully, visible | Wrapped fully, visible |
| Background | Clean wood grain | Leather jacket sleeve, minimal distraction |
| Symbol clarity | Sharp | Sharp |
| Device angle | Slightly tilted ~15° from straight-on | Nearly head-on to camera |

**What Tron losers have in common (t10, t16):**

| t10 | t16 |
|-----|-----|
| Landscape on sleeve, different lighting/angle from t03/t11 | Vertical standalone **but upside down (MINUS at top)** |
| Produced weird two-rider compositions on mtb_s1 seed | Produced clean-symbol outputs but with pose/aesthetic issues |

**→ Reshoot recommendations for Hunter and Patriot:**

1. **Top priority: t18-clone.** Hunter standalone on wood table, vertical, PLUS at top, LED at top-left, branded strap wrapped horizontally, warm natural light, slight ~15° tilt, no jacket/sleeve in frame. Same for Patriot. **This is the composition that produced the only pure-gold ref in the entire 20-photo Tron shoot.** If it works the same for Hunter and Patriot, it should replace/supplement h3 and p4 as the top-scoring refs in those colorways.

2. **Secondary: landscape sleeve shots like t03/t11.** Already covered by h3/h5/p4/p6. Don't reshoot unless targeting a specific issue.

3. **Do NOT reshoot with:**
   - Upside-down vertical standalone (MINUS at top) — that's the t16 anti-pattern. Model can still work with it but rot180 rate is high and it trips aesthetic failures.
   - Heavy shadow on sleeve mounting — produces t10-style two-rider weird compositions in mtb_s1 seed.
   - Extreme landscape where LEFT vs RIGHT of device is ambiguous — model has to guess wrist/elbow direction and ~50% of the time guesses wrong.

4. **Shoot count:** 3-5 variations per colorway is enough. Tron had 20 shots and only 1 was pure-gold, but the top 4 were all Tier-1. Over-shooting is wasted effort.

5. **Testing protocol:** After reshoot, run `tron_ab_test.py` pattern on the new refs (20 refs × 2 sports × 2 scenes @ NB Pro = $12, or just the new refs if <6 new shots to save money). Rate in `cb-ab-review.html` (generalized review page). Lock winners same way.

**Honest caveat:** With 20 refs we have a small sample, and the winners might be confounded by lighting quality, camera angle, or ref subject (jacket fabric vs wood table) in ways we can't fully separate. The t18 pattern is a *hypothesis* to test, not proof. But it's cheap to test when products arrive — Justin shoots 6 photos (3 Hunter + 3 Patriot t18-clones), I fire $3 of gens, Justin rates, done.
