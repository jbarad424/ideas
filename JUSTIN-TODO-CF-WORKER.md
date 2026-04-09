# Justin's TODO — Cloudflare Worker + API Key Rotation

**Purpose:** these are the external steps Justin must do to unblock PLAN Part 0.1 (secure API key proxy). Everything else (Worker code, wrangler config, deploy script, cb-review.html client integration) I can write locally — it just won't go LIVE until the steps below are done.

**Estimated time:** 20–30 minutes total across all steps. The Cloudflare signup is the longest single part (~5 min).

**Run these in order — later steps depend on earlier ones.**

---

## ✅ Step 1 — Create a Cloudflare account (5 min)

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with justin@chubbybuttons.io (or whichever email you want; team members don't need accounts, only you)
3. Verify email when the link arrives
4. Skip any "add a domain" prompt — we don't need one for Workers
5. Once logged in, **confirm you're on the Free plan** (Workers free tier includes 100,000 requests/day, way more than we need)

**When done:** tell me "Cloudflare account is created" and I'll walk you through step 2.

---

## ✅ Step 2 — Install the Wrangler CLI (2 min)

Wrangler is the command-line tool that deploys Cloudflare Workers.

Run this in your terminal:

```bash
npm install -g wrangler
wrangler --version
```

Expected output: something like `⛅️ wrangler 3.x.x`.

If `npm` is not installed, run `brew install node` first.

**When done:** tell me "Wrangler installed" and I'll walk you through step 3.

---

## ✅ Step 3 — Log in to Wrangler (1 min)

```bash
wrangler login
```

This opens a browser window. Click "Allow" to authorize Wrangler to deploy Workers on your CF account.

Then verify:

```bash
wrangler whoami
```

Should show your email and the accounts you have access to.

**When done:** tell me "Wrangler is logged in" and I'll deploy the Worker with one command.

---

## ✅ Step 4 — Generate a shared team password (1 min)

Pick any password you want to give your team. This gates access to the fal.ai + Anthropic proxy so only people with the password can fire API calls.

Good options:
- A passphrase like `purple-motorcycle-47` (memorable)
- A random 24-char string from `openssl rand -base64 18`
- Whatever you prefer

**Send it to me in the chat** and I'll store it as a `SHARED_PASSWORD` secret on the Worker. **Do NOT put it in any committed file or email.**

**Note on sharing with the team:** once the Worker is deployed, you'll share the password with Jordan / anyone else on the team via a secure channel (Signal, 1Password shared vault, or just telling them in person). Each team member pastes it once per browser in the `cb-review.html` password modal. It's stored in their localStorage, never in the HTML source.

**If the password ever leaks:** tell me and I'll rotate it in 10 seconds via `wrangler secret put SHARED_PASSWORD`.

---

## ✅ Step 5 — Rotate the leaked fal.ai API key (5 min)

**Why:** the current key `abd109db-5b32-…` has been sitting in `cb-review.html` on the public `jbarad424.github.io` for weeks. It's compromised. Once the Worker is live, the OLD key must be revoked and a NEW key put in the Worker's environment (server-side only, never in the browser).

**Steps:**

1. Go to https://fal.ai/dashboard/keys
2. Log in with your fal account
3. Find the key starting with `abd109db-5b32-…`
4. Click the **Delete** or **Revoke** button on that row. **CONFIRM.** (This breaks the currently-deployed `cb-review.html` Video Lab, but that's expected — we're about to replace it with the proxy.)
5. Click **"Create new key"**
6. Name it something like `cb2-cf-worker-2026-04-09`
7. Copy the new key (it shows the full key ONLY on the creation screen — copy it now or you'll never see it again)
8. **Send the new key to me in the chat** — I'll store it as the `FAL_KEY` secret on the Worker

**If you need the Video Lab to keep working between steps 5 and "Worker deployed":** don't rotate the key yet, do step 6 and step 7 first, then come back and rotate in step 5. That minimizes downtime. Your call.

---

## ✅ Step 6 — Generate an Anthropic API key (3 min)

**Why:** the "✨ Refine with Sonnet" button in the CREATE tab calls the Anthropic API server-side via the Worker. Needs a key.

**Steps:**

1. Go to https://console.anthropic.com/settings/keys
2. Log in with your Anthropic account
3. Click **"Create Key"**
4. Name it `cb2-cf-worker-sonnet-refiner`
5. Scope: **Default** (full access to your account — it's just you, no need to restrict)
6. Copy the key (starts with `sk-ant-…`). Same deal: only shown once.
7. **Send the key to me in the chat** — I'll store it as the `ANTHROPIC_KEY` secret on the Worker

**Cost check:** Sonnet refines cost ~$0.003 each. Even if you fire 100 scene refines a day it's $0.30/day. Budget impact is negligible.

---

## ✅ Step 7 — Done (I take over)

Once you've sent me:
- **Confirmation that CF account exists + Wrangler is logged in**
- **Shared team password**
- **New fal.ai key**
- **Anthropic key**

I will:

1. Run `wrangler deploy` — Worker goes live at `https://cb2-proxy.<your-subdomain>.workers.dev`
2. Run `wrangler secret put FAL_KEY`, `wrangler secret put ANTHROPIC_KEY`, `wrangler secret put SHARED_PASSWORD` — all three secrets stored server-side, never in code
3. Verify the Worker responds with a test ping
4. Edit `cb-review.html` to replace the 3 hardcoded fal.ai keys with `proxyCall()` helper calls
5. Add the first-time password modal
6. Redeploy `cb-review.html` to GitHub Pages
7. Smoke-test the Video Lab from an incognito browser to confirm it still works through the Worker
8. Fix `SYNC_URL` (PLAN Part 0.2) in the same deploy since we're already editing `cb-review.html`

**End state:** Justin's team can open `cb-review.html` on any browser, paste the team password once, and generate images / refine prompts / sync feedback — all without ever seeing a raw API key. If the password leaks, you rotate it in 10 seconds and everyone re-pastes. If any key leaks you rotate THAT in 10 seconds and nobody on the team has to do anything.

---

## FAQ

**Q: Why not just let each team member paste their own fal.ai key?**
A: Justin explicitly said he wants a no-hunt-for-API-keys experience for his team. This is the whole point of the proxy.

**Q: Why Cloudflare specifically?**
A: Free tier is 100k requests/day (we need maybe 100/day), deploy is one command (`wrangler deploy`), no cold-start delay, no account management friction. Vercel Edge Functions and Deno Deploy are equivalent alternatives if you hate Cloudflare for some reason — tell me and I'll swap.

**Q: Can I test this locally before deploying?**
A: Yes. `wrangler dev` runs the Worker locally at `http://localhost:8787`. I'll point `cb-review.html` at it for testing before going live.

**Q: What about Make.com scenario 4654266 (the SYNC_URL fix)?**
A: That's PLAN Part 0.2, separate from the Worker. I'll send you a separate short TODO for that — it's a ~2-minute edit in the Make.com UI (add a `filename` field to the HTTP module). You can do it any time; doesn't block the Worker.

**Q: How do I know the Worker is actually working?**
A: After step 7, I'll give you a test URL to hit from your browser. If it responds with a test image, we're good.

**Q: What if I get stuck on any step?**
A: Stop and paste the error into the chat. I'll debug it with you. Don't skip steps or fake outputs — that always blows up later.
