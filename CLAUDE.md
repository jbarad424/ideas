# CB2 AI Creative Lab — Project Context

## What This Is
AI product photography pipeline for Chubby Buttons CB2 wearable Bluetooth remote. Generates lifestyle marketing photos and videos of the CB2 on people doing sports.

## Who
Justin Barad, co-founder of Chubby Buttons. Prefers direct, no-BS communication. Trusts his own visual assessment over AI scoring. Don't suggest break times or comment on session length.

## Production Pipeline (What Works)
1. **Generate:** fal.ai FLUX 2 Pro edit with Ref C (J&Mike Dual) reference photo
2. **Cherry-pick:** Generate 5-10 seeds, pick 90+ winners
3. **Optional two-pass:** Add helmet/earbuds via second FLUX edit (CB2 survives)
4. **Review:** cb-review.html on GitHub Pages (5 tabs: TO REVIEW, REVIEWED, PROGRESS, GALLERY, VIDEOS)

## Key Rules
- LEFT arm: volume-up toward wrist. RIGHT arm: volume-down toward wrist
- Waist-up framing always. Simple prompts beat complex ones
- "Bright button icons" causes glowing artifact — don't use
- Ref C (J&Mike Dual) is the production reference photo (Drive ID: 1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7)

## What's Dead (Don't Retry)
- LoRA fine-tuning (9 runs, 2 base models, best 17/100)
- Inpainting pipelines B/C/E (0-5/100)
- ControlNet + IP-Adapter (systems conflict)
- SAM rotation post-processing (compositing looks unnatural)
- AI auto-scoring (unreliable)

## Current Stats (April 7, 2026)
- 270+ images generated and reviewed, 41 scored 90+
- 13 test videos across 6 models (Gen-4 Turbo scored 97!)
- Best scores: 100, 98, 97, 95 across motorcycle, hiking, skiing, snowboard, MTB
- Orientation correct 65-70% with Ref C + arm rules
- Multi-ref colorway: colors transfer, orientation same as baseline
- Two-pass gear addition: proven for helmets (CB2 survives)
- Colorway-specific prompting: DEAD (causes glowing/wrong colors)
- Action shots with colorway in prompt: DEAD (10-22 avg)
- FLUX 2 Flex g7.0: NEW PRODUCTION MODEL — scored 90-96, 33% cheaper than Pro
- AI auto-scoring: DEAD (57-63% accuracy, filters out winners)
- Prompt restructure (CB2-first): DEAD (scene-first wins)
- Tahoe single-person refs: too constraining (copies original person)
- Mike Moto refs: motorcycle gear transfers but hit rate lower than J&Mike
- Hiking: DEPRIORITIZED (not core use case per Justin)

## API Keys
Stored in local memory files (not in repo for security). Keys: fal.ai, Replicate, Runway Gen-4.
Check ~/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas/memory/project_architecture.md for keys.

## Next Session Priorities
1. Switch production to FLUX 2 Flex g7.0 (validated: 90-96 scores, 33% cheaper)
2. Jordan's shot list: 7 must-have photos (3 Hunter + 3 Patriot + 1 Tron winter) — see jordan-shot-list.html
3. Build CREATE tab (sport/colorway/vibe dropdowns → auto-generate)
4. Scale video production (Gen-4 Turbo scored 97, Gen-4.5 scored 94)
5. Two-pass for small gear additions (helmets, earbuds — NOT full clothing swaps)
6. Test Mike Moto photos as Tron motorcycle ref (gear transfers, lower hit rate)

## Key Resources
- Review page: https://jbarad424.github.io/ideas/cb-review.html
- Feedback JSON: https://jbarad424.github.io/ideas/cb-feedback.json
- Notion status: https://www.notion.so/33af45bfc038813f8b09f0d6efdffc49
- Google Drive: CB2 AI Generated Photos folder
- Memory files: ~/.claude/projects/-Users-justinbarad-Documents-Claude-Code-ideas/memory/

## Working Preferences
- Always research best-in-class before spending credits
- Never claim something works without verifying yourself
- Distinguish "concept failed" from "implementation failed"
- Don't over-build infrastructure — simple tools + chat > complex apps
- Justin's visual assessment is more reliable than AI analysis of images
