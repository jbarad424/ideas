#!/usr/bin/env node
/**
 * Smoke test for scripts/create-tab/data.js against real cb-keepers.json.
 *
 * Run:
 *   cd scripts/create-tab
 *   node test-data.js
 */
const fs = require("fs");
const path = require("path");

// Shim browser globals for the data.js module
global.crypto = require("crypto").webcrypto;

const CB2 = require("./data.js");

async function main() {
  const keepersPath = path.join(__dirname, "..", "..", "cb-keepers.json");
  const keepers = JSON.parse(fs.readFileSync(keepersPath, "utf8"));
  console.log(`✓ Loaded cb-keepers.json: ${Object.keys(keepers.items).length} items, ${keepers.meta.super_count} super + ${keepers.meta.yes_count} yes`);

  // Smoke: constants
  console.log(`✓ REFS loaded: ${Object.keys(CB2.REFS).length} refs`);
  console.log(`  Hunter: ${CB2.filterRefsByColorway("Hunter").map(r => r.id).join(", ")}`);
  console.log(`  Patriot: ${CB2.filterRefsByColorway("Patriot").map(r => r.id).join(", ")}`);
  console.log(`  Tron: ${CB2.filterRefsByColorway("Tron").map(r => r.id).join(", ")}`);
  console.log(`✓ KILLED_REFS: ${Array.from(CB2.KILLED_REFS).join(", ")}`);

  // Smoke: normalization stability
  const n1 = CB2.normalizePrompt("  Foo   BAR\n\tBaz  ");
  const n2 = CB2.normalizePrompt("foo bar baz");
  console.log(`✓ normalizePrompt stable: "${n1}" === "${n2}" → ${n1 === n2}`);
  if (n1 !== n2) throw new Error("normalizePrompt is not stable");

  // Smoke: recipeIdFor stability + length
  const id1 = await CB2.recipeIdFor("Motorcycle rider at golden hour", 9101);
  const id2 = await CB2.recipeIdFor("Motorcycle rider at golden hour", 9101);
  const id3 = await CB2.recipeIdFor("Motorcycle rider at golden hour", 9102);
  console.log(`✓ recipeIdFor stable: ${id1} === ${id2} → ${id1 === id2}`);
  console.log(`✓ recipeIdFor differs on seed: ${id1} !== ${id3} → ${id1 !== id3}`);
  if (id1 !== id2) throw new Error("recipeIdFor is not stable");
  if (id1 === id3) throw new Error("recipeIdFor should differ on different seeds");

  // Smoke: build recipe index
  const recipes = await CB2.buildRecipeIndex(keepers);
  console.log(`✓ buildRecipeIndex: ${recipes.length} recipes from ${Object.keys(keepers.items).length} items`);
  console.log(`  avg items per recipe: ${(Object.keys(keepers.items).length / recipes.length).toFixed(2)}`);

  // Distribution
  const bySport = {};
  const withSeed = { seed: 0, noSeed: 0 };
  let totalSuper = 0, totalYes = 0;
  for (const r of recipes) {
    bySport[r.sport] = (bySport[r.sport] || 0) + 1;
    if (r.seed != null && r.seed !== "NA") withSeed.seed++; else withSeed.noSeed++;
    totalSuper += r.super_count;
    totalYes += r.yes_count;
  }
  console.log("  By sport:", bySport);
  console.log(`  With seed: ${withSeed.seed}, without: ${withSeed.noSeed}`);
  console.log(`  Total super: ${totalSuper}, total yes: ${totalYes}`);

  // Singletons (candidates for Rail 2 "one-offs")
  const singletons = recipes.filter(r => r.examples.length === 1);
  console.log(`  Singletons (Rail 2 candidates): ${singletons.length}`);

  // Multi-example (candidates for Rail 1 hit parade)
  const multis = recipes.filter(r => r.examples.length > 1);
  console.log(`  Multi-example (Rail 1 candidates): ${multis.length}`);

  // Top 5 cold-start
  const sorted = CB2.sortRecipesColdStart(multis);
  console.log("\n  TOP 5 cold-start recipes (super×2 + yes):");
  for (let i = 0; i < Math.min(5, sorted.length); i++) {
    const r = sorted[i];
    const score = r.super_count * 2 + r.yes_count;
    console.log(`    #${i+1} ${r.id} [${r.sport}] score=${score}, super=${r.super_count}, yes=${r.yes_count}, ${r.examples.length} examples`);
    console.log(`         prompt: "${(r.prompt || "").slice(0, 80)}…"`);
  }

  // Sanity: verify every refs_observed excludes KILLED_REFS
  for (const r of recipes) {
    for (const refId of r.refs_observed) {
      if (CB2.KILLED_REFS.has(refId)) {
        throw new Error(`Killed ref ${refId} appears in recipe ${r.id}.refs_observed`);
      }
    }
  }
  console.log("✓ No killed refs leaked into any recipe.refs_observed");

  console.log("\n=== ALL SMOKE TESTS PASSED ===");
}

main().catch(e => { console.error("FAIL:", e); process.exit(1); });
