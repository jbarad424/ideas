# Lessons Learned: AI Product Photography Pipeline

**Reusable patterns from 400+ images, 21 failed approaches, and 10 days of iteration.**
Built for Chubby Buttons CB2, but everything here generalizes to any small product + lifestyle marketing use case.

---

## 1. AI Image Generation — What Actually Works

- **Scene-first prompt structure.** Describe the environment BEFORE the product. Models anchor on whatever comes first — if you lead with the product, you get a product photo. If you lead with the scene, you get a lifestyle photo with the product in it.
- **Specific camera/lens language beats generic quality boosters.** "Shot on Sony A7R IV 85mm f/2.0" produces better results than "4K, hyperrealistic, ultra HD." The generic boosters trigger an over-polished CGI look.
- **Add imperfections to fight the AI look.** Film grain, slight lens vignetting, chromatic aberration — these make AI output look photographed rather than rendered.
- **Reference photo orientation is the #1 failure mode.** In testing, 73% of outputs had the product rotated 180 degrees. The fix: shoot reference photos in multiple orientations, then A/B test rotated vs. original to find what the model expects. This single discovery fixed more output quality issues than any prompt change.
- **Dual-reference technique.** Send TWO reference images: image 1 shows the product in context (on a person, in the right position), image 2 shows a clean product close-up (symbols, buttons, details). Without image 2, models render "something that looks like the product" but get the details wrong.
- **Generate-and-filter with human review is the only reliable quality gate.** AI auto-scoring achieved 57-63% accuracy and produced false positives (garbage rated 85+) and false negatives (keepers rated below 50). Human eyes are irreplaceable for product-specific detail assessment.
- **Multi-model strategy.** Different models excel at different things. GPT Image 1.5 has the best photorealism. Nano Banana Pro has the best compositions. FLUX 2 Flex has the best product placement accuracy. Use the right model for each use case, not one model for everything.

## 2. Prompt Engineering Patterns

- **Locked product block + creative bookends.** The product description in the prompt should NEVER change between generations. The scene/setting (before) and style/mood/camera (after) are the creative variables. This ensures consistent product rendering across diverse scenes.
- **Mandatory gear per context.** Always include the appropriate gear for the activity in the prompt. Without it, models render bare skin, missing helmets, or inappropriate clothing. A gear checklist per sport/activity prevents this.
- **Placement reinforcement phrases matter:**
  - "OVER the jacket sleeve" prevents bare-skin hallucination
  - "halfway between wrist and elbow" fixes above-elbow/wrong-position placement
  - "velcro strap wrapped fully around" fixes missing attachment mechanism
  - Exact item count ("five round tactile buttons") prevents models adding or removing features
- **Colorway/color comes from the reference photo, NOT from prompt text.** Describing colors in the prompt causes glowing/illuminated artifacts. Let the reference image handle appearance.
- **Words to never use:**
  - "product photography" — triggers sterile white-background aesthetic
  - "photorealistic" or "hyperrealistic" — triggers over-smoothed CGI
  - "4K" / "ultra HD" — same CGI trigger
  - Device-irrelevant accessories ("wireless earbuds") — cause floating/Photoshopped artifacts

## 3. Reference Photo Best Practices

- **Shoot 10-20 candidates, then A/B test.** Don't guess which reference photo works best — test them all. Our rotation A/B: 12 candidates x 48 generations, scored by the product owner, found that rotating 180 degrees won 26-2 over originals.
- **Vertical standalone product shots are gold.** A clean product photo on a neutral surface (wood table, plain background), shot vertically with the "top" of the product pointing up, consistently outperformed on-body reference photos.
- **Multi-orientation physical variants beat post-processing.** It's better to physically rotate the product and shoot multiple angles than to digitally rotate reference photos after the fact.
- **Kill references that consistently fail — don't keep trying.** Track failure rates per reference. If a ref produces wrong orientation, wrong arm, or garbled output in 3+ tests, remove it from the pool permanently. Our kill list grew to 6 of 18 candidates.
- **Some references are "arm-committed."** A reference showing the product on a left arm will produce left-arm outputs regardless of what the prompt says. The reference geometry overrides prompt text. Account for this in your reference selection.

## 4. Video Generation Rules

- **NEVER describe hands touching/pressing/interacting with the product.** This causes phantom hands — models hallucinate extra limbs reaching from off-screen. Instead, translate physical interactions into environmental effects: "a beat later, music surges on the soundtrack" instead of "he presses the play button."
- **ONE primary action or camera movement per prompt.** Video models cannot reliably chain multiple sequential events. "Rider accelerates" works. "Finger touches button THEN music starts THEN finger lifts off" does not.
- **Describe camera motion explicitly.** "Slow dolly in," "tracking shot from left at speed," "static 85mm lock-off" — be concrete. "Cinematic" alone means nothing.
- **Platform-specific prompt length matters.** Kling truncates aggressively (~100 words max). Sora handles long narrative prompts (~200 words). Match your prompt length to the platform.
- **Preserve temporal ordering.** If the user describes a sequence (A then B then C), keep that order even if you simplify the actions. The sequence IS the creative intent.

## 5. Architecture / Infrastructure Patterns

- **Single HTML file + Cloudflare Worker proxy = surprisingly powerful.** Our entire app is one HTML file with inline JS + a 150-line CF Worker that holds API keys. GitHub Pages hosts it. No build step, no framework, no deployment pipeline. Ships in seconds.
- **localStorage for local state, GitHub Pages JSON for shared state.** Fast local-first experience with async sync to a shared JSON file. Merge-before-push prevents overwrites when multiple devices edit.
- **EMA learning loop (alpha=0.3).** Exponential moving average on keeper rate per recipe/reference/model. Converges in 3-5 batches. Simple, no ML infrastructure needed.
- **Safety guard on manifest pushes.** Before pushing an archive manifest, fetch the live version and refuse to push if the new one has FEWER entries. Saved us from a bug that silently wiped 693 entries.
- **Archive everything permanently — generation URLs expire.** fal.ai URLs last days to weeks. Auto-upload completed work to permanent storage (catbox.moe for immediate, GitHub Pages for long-term). Never rely on generation platform URLs.
- **Debounce async loaders.** When 3+ async data sources all trigger a UI re-render on completion, the DOM rebuilds 3x in 500ms causing visible flicker. A 150ms debounce coalesces them into one render.

## 6. UX / Product Patterns

- **Human review > AI scoring for product-specific quality.** AI can't tell if buttons are in the right order or if a strap is missing. The product owner's eyes are the only reliable quality gate. Build the UX around fast human review, not automated scoring.
- **Filter bars need labeled rows on mobile.** One flat row of 15 filter buttons is unusable on a phone. Three labeled rows (Show / Sport / Model) with a row label on the left is clean.
- **Explicit "Create" button, not click-to-fire.** Platform selection should NOT immediately trigger an expensive operation. Add a confirmation step with cost estimate.
- **Persist batch results in localStorage.** Generated images should survive tab switches and page reloads. Don't lose work because the user accidentally navigated away.
- **Remember which tab the user was on.** Tab persistence via localStorage is trivial to implement and prevents the frustration of always landing on the default tab after reload.
- **Model badge ON the image, not as separate caption text.** Small gradient overlay at the bottom of the thumbnail. Users can see the model at a glance without reading metadata.
- **Sort by recency, not score.** Users care about what's new more than what scored highest. Freshness > ranking.

## 7. What Failed (and Why)

21 approaches were tested and killed. The key insight: most failures are CONCEPTUAL, not implementation bugs.

| Category | What failed | Why (concept, not implementation) |
|----------|-----------|-----------------------------------|
| **LoRA fine-tuning** | 9 training runs, all garbled | Small products have too many precise details (5 buttons, LED, logo, strap) for a LoRA to memorize |
| **Virtual try-on** | 6 VTON models, all failed | VTON is built for CLOTHING — it segments the body looking for garments. A forearm accessory isn't a garment. |
| **Inpainting (text-only)** | Text description alone | Text cannot describe a specific product well enough for a model to render it recognizably. Reference images are essential. |
| **Inpainting (global ref)** | reference_image_url parameter | This is a GLOBAL control that warps the entire image, not just the masked region. API architecture limitation. |
| **AI auto-scoring** | Two approaches, 57-63% accuracy | AI sees "something on arm" and says YES even for garbled blobs. Can't distinguish the real product from a dark rectangle. |
| **Outpainting** | Extending from a real photo crop | Outpainting is designed for background extension, not constructing full-body athletes from arm fragments. |
| **Micro-inpainting** | Small masks on the product area | Models regenerate the ENTIRE product during inpainting, losing details that were already correct. Cannot selectively sharpen. |
| **Colorway-specific prompting** | Describing colors in text | Models illuminate/glow the colors instead of rendering them naturally. Colorway must come from the reference photo. |

## 8. Process Rules

- **Test before recommending.** State what would prove you wrong BEFORE testing, not after. Don't flip-flop on recommendations.
- **Research what's current before spending credits.** The AI landscape changes weekly. What was best-in-class last session may be obsolete.
- **Run parallel tests, not sequential theories.** If there are 3 possible approaches, test all 3 simultaneously instead of theorizing about which might work.
- **Distinguish "concept failed" from "implementation failed."** Before declaring an approach dead, ask: did the fundamental concept fail, or did I just implement it wrong? This distinction determines whether to retry or abandon.
- **The failed approaches list is append-only.** Never remove entries. It's scar tissue that prevents repeating mistakes. New sessions read it before suggesting anything.
- **Update the knowledge base at session end.** Every session must leave a clear handoff: what was tested, what the results were, what's dead, and what's next. The knowledge file IS the handoff.

---

*Extracted April 10, 2026 from 10 days of pipeline development. 400+ images generated, 21 approaches tested, 4 production-validated models.*
