# cb2-proxy — Cloudflare Worker API Proxy

**Purpose:** PLAN Part 0.1. Shields fal.ai + Anthropic API keys from the public `cb-review.html` on GitHub Pages by routing all network calls through this Worker.

**Status:** Code complete, NOT deployed. Blocked on Justin completing the steps in `JUSTIN-TODO-CF-WORKER.md` (CF account, Wrangler login, key rotation, password).

## Files

- `worker.js` — the Worker itself (~200 lines). Routes fal.ai and Anthropic calls, gates on a shared password, rate-limits at 100 req/min per IP, sets CORS for `https://jbarad424.github.io`.
- `wrangler.toml` — Cloudflare deploy config.
- `README.md` — this file.

## Deploy (for future Justin or future me)

```bash
cd scripts/cf-worker

# One-time: authenticate Wrangler with CF account
wrangler login

# Set the three secrets (interactive — Wrangler prompts for each value)
wrangler secret put FAL_KEY
wrangler secret put ANTHROPIC_KEY
wrangler secret put SHARED_PASSWORD

# Deploy
wrangler deploy
```

On success, Wrangler prints a URL like `https://cb2-proxy.<your-subdomain>.workers.dev`. That's the `WORKER_URL` the browser-side `proxyCall()` helper will hit.

## Test it

```bash
# Health check (no auth)
curl https://cb2-proxy.<your-subdomain>.workers.dev
# → {"ok":true,"service":"cb2-api-proxy","version":"1.0.0","supported":["fal","anthropic"]}

# Test fal call (needs correct password)
curl -X POST https://cb2-proxy.<your-subdomain>.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "password": "<SHARED_PASSWORD>",
    "service": "fal",
    "endpoint": "fal-ai/nano-banana-pro/edit",
    "body": {
      "image_urls": ["https://lh3.googleusercontent.com/d/1qfm8HT8vpD0wh8K9q8vZw6zYK7ohPsq7=w800"],
      "prompt": "test gen",
      "seed": 1,
      "num_images": 1
    }
  }'

# Test Anthropic call (Sonnet refiner dry run)
curl -X POST https://cb2-proxy.<your-subdomain>.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "password": "<SHARED_PASSWORD>",
    "service": "anthropic",
    "endpoint": "/v1/messages",
    "body": {
      "model": "claude-sonnet-4-5",
      "max_tokens": 100,
      "messages": [{"role":"user","content":"Say hi in one word"}]
    }
  }'
```

## Client integration (goes in cb-review.html once deployed)

```js
const WORKER_URL = "https://cb2-proxy.<your-subdomain>.workers.dev";

function getSharedPassword() {
  let pw = localStorage.getItem("cb2_team_pw");
  if (!pw) {
    pw = prompt("Paste the CB2 team password to enable image generation.");
    if (pw) localStorage.setItem("cb2_team_pw", pw);
  }
  return pw;
}

async function proxyCall({ service, endpoint, body, method = "POST" }) {
  const password = getSharedPassword();
  if (!password) throw new Error("No team password — cannot call API");
  const resp = await fetch(WORKER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password, service, endpoint, method, body }),
  });
  if (resp.status === 401) {
    // Password was wrong or rotated — clear and prompt again
    localStorage.removeItem("cb2_team_pw");
    throw new Error("Team password rejected — please reload and re-enter");
  }
  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Proxy error ${resp.status}: ${errText}`);
  }
  return resp.json();
}

// Example fal.ai call
const result = await proxyCall({
  service: "fal",
  endpoint: "fal-ai/nano-banana-pro/edit",
  body: {
    image_urls: ["..."],
    prompt: "...",
    seed: 9101,
    num_images: 1,
  },
});

// Example Anthropic Sonnet refine call
const refined = await proxyCall({
  service: "anthropic",
  endpoint: "/v1/messages",
  body: {
    model: "claude-sonnet-4-5",
    max_tokens: 500,
    system: "You are a photography director for an action-sports marketing brand...",
    messages: [{ role: "user", content: userScene }],
  },
});
```

## Rotation (future)

- **Rotate `SHARED_PASSWORD`:** `wrangler secret put SHARED_PASSWORD` → enter new value. All team members need to re-enter on next use (their old localStorage value will get a 401, the helper catches it and re-prompts).
- **Rotate `FAL_KEY`:** revoke on fal.ai dashboard → create new → `wrangler secret put FAL_KEY`. Zero client-side changes.
- **Rotate `ANTHROPIC_KEY`:** same pattern via Anthropic console.

## Pitfall mitigations (from PLAN-CREATE-TAB-V2.md Part 5)

- #1 (fal.ai key public leak) — keys are server-side only, never touch browser
- #26 (password leak) — rate limit 100/min per IP bounds damage window; rotation is one command
- #27 (Worker down) — client `proxyCall()` throws on non-200, frontend shows clear error banner
- #28 (Sonnet off-script) — system prompt enforced client-side (editable via gear icon in UI), Worker is transparent to it

## What the Worker explicitly does NOT do

- No request logging (privacy)
- No response caching (every call is fresh)
- No multi-account support (one team, one password, simple is better)
- No upstream budget caps (cost visibility via `cost_usd` in batch records per PLAN Part 4.1, not enforced at proxy level)
