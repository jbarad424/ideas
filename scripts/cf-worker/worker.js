/**
 * CB2 API Proxy Worker (PLAN Part 0.1)
 *
 * Shields the fal.ai + Anthropic API keys from the public cb-review.html by
 * routing all API calls through this Cloudflare Worker. The browser only ever
 * sends a shared team password; the real keys live in Worker env vars.
 *
 * Request contract (browser → worker):
 *   POST /
 *   Content-Type: application/json
 *   {
 *     password: "<SHARED_PASSWORD>",           // gates access
 *     service:  "fal" | "anthropic",           // which upstream
 *     endpoint: "fal-ai/nano-banana-pro/edit"  // fal only; ignored for anthropic
 *              | "/v1/messages",                // anthropic path
 *     method:   "POST" | "GET",                // optional, default POST
 *     body:     { ...upstream request body }   // forwarded as-is
 *   }
 *
 * Response: upstream response body + status code, with CORS headers.
 *
 * Secrets (set via `wrangler secret put`):
 *   FAL_KEY           — fal.ai API key (e.g. abd109db-5b32-…:25db06d5…)
 *   ANTHROPIC_KEY     — Anthropic API key (sk-ant-…)
 *   SHARED_PASSWORD   — the team gate password
 *
 * Rate limiting: 100 requests/minute per client IP (simple in-memory map,
 * resets when the Worker is recycled — acceptable for team scale).
 *
 * CORS: allows GET/POST/OPTIONS from https://jbarad424.github.io only.
 */

const ALLOWED_ORIGIN = "https://jbarad424.github.io";
const RATE_LIMIT_RPM = 100;
const RATE_LIMIT_WINDOW_MS = 60_000;

// In-memory rate limiter (per IP). Keyed by CF-Connecting-IP.
// Worker instances are isolated per colo so this is approximate but
// effective for deterring abuse.
const rateLimitMap = new Map();

function corsHeaders(extra = {}) {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
    ...extra,
  };
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: corsHeaders({ "Content-Type": "application/json" }),
  });
}

function errorResponse(status, message) {
  return jsonResponse({ error: message }, status);
}

function checkRateLimit(ip) {
  const now = Date.now();
  const bucket = rateLimitMap.get(ip) || [];
  const recent = bucket.filter((t) => now - t < RATE_LIMIT_WINDOW_MS);
  if (recent.length >= RATE_LIMIT_RPM) {
    return false;
  }
  recent.push(now);
  rateLimitMap.set(ip, recent);
  // Occasionally GC
  if (rateLimitMap.size > 500) {
    for (const [k, v] of rateLimitMap) {
      const fresh = v.filter((t) => now - t < RATE_LIMIT_WINDOW_MS);
      if (fresh.length === 0) rateLimitMap.delete(k);
      else rateLimitMap.set(k, fresh);
    }
  }
  return true;
}

async function proxyFal(payload, env) {
  const { endpoint, method = "POST", body = {} } = payload;
  if (!endpoint || typeof endpoint !== "string") {
    return errorResponse(400, "Missing or invalid 'endpoint'");
  }
  // Strip any leading slashes and disallow protocol-ful inputs
  const clean = endpoint.replace(/^\/+/, "");
  if (clean.includes("://") || clean.includes("..")) {
    return errorResponse(400, "Invalid endpoint");
  }
  const url = `https://fal.run/${clean}`;
  const upstream = await fetch(url, {
    method,
    headers: {
      Authorization: `Key ${env.FAL_KEY}`,
      "Content-Type": "application/json",
    },
    body: method === "GET" ? undefined : JSON.stringify(body),
  });
  const text = await upstream.text();
  return new Response(text, {
    status: upstream.status,
    headers: corsHeaders({
      "Content-Type": upstream.headers.get("Content-Type") || "application/json",
    }),
  });
}

async function proxyAnthropic(payload, env) {
  const { endpoint = "/v1/messages", method = "POST", body = {} } = payload;
  // Only allow /v1/messages for now (the Sonnet prompt refiner use case).
  // Expand this allowlist if we add more Anthropic features.
  const allowedEndpoints = new Set(["/v1/messages"]);
  if (!allowedEndpoints.has(endpoint)) {
    return errorResponse(400, `Endpoint ${endpoint} not allowed`);
  }
  const url = `https://api.anthropic.com${endpoint}`;
  const upstream = await fetch(url, {
    method,
    headers: {
      "x-api-key": env.ANTHROPIC_KEY,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: method === "GET" ? undefined : JSON.stringify(body),
  });
  const text = await upstream.text();
  return new Response(text, {
    status: upstream.status,
    headers: corsHeaders({
      "Content-Type": upstream.headers.get("Content-Type") || "application/json",
    }),
  });
}

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    // Health check (GET /) — returns OK without touching secrets
    if (request.method === "GET") {
      return jsonResponse({
        ok: true,
        service: "cb2-api-proxy",
        version: "1.0.0",
        supported: ["fal", "anthropic"],
      });
    }

    if (request.method !== "POST") {
      return errorResponse(405, "Method not allowed");
    }

    // Rate limit
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    if (!checkRateLimit(ip)) {
      return errorResponse(429, "Rate limit exceeded (100 req/min per IP)");
    }

    // Parse body
    let payload;
    try {
      payload = await request.json();
    } catch {
      return errorResponse(400, "Invalid JSON body");
    }
    if (!payload || typeof payload !== "object") {
      return errorResponse(400, "Body must be a JSON object");
    }

    // Auth gate
    if (!env.SHARED_PASSWORD) {
      return errorResponse(500, "Server misconfigured: SHARED_PASSWORD not set");
    }
    if (payload.password !== env.SHARED_PASSWORD) {
      // Intentionally opaque error — don't leak whether the password was close
      return errorResponse(401, "Unauthorized");
    }

    // Route by service
    const { service } = payload;
    if (service === "fal") {
      if (!env.FAL_KEY) {
        return errorResponse(500, "Server misconfigured: FAL_KEY not set");
      }
      return proxyFal(payload, env);
    } else if (service === "anthropic") {
      if (!env.ANTHROPIC_KEY) {
        return errorResponse(500, "Server misconfigured: ANTHROPIC_KEY not set");
      }
      return proxyAnthropic(payload, env);
    } else {
      return errorResponse(400, `Unknown service: ${service}`);
    }
  },
};
