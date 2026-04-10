// DEPLOYED WORKER SOURCE — pasted by Justin 2026-04-10
// This is the LIVE version at cb2-proxy.chubbybuttons.workers.dev
// The local worker.js is the OLD version (pre fal-submit/fal-get).
export default {
  async fetch(r, env) {
    const c = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type,X-Team-Password,X-Proxy-Target",
    };
    if (r.method === "OPTIONS") return new Response(null, { headers: c });
    if (new URL(r.url).pathname === "/ping")
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { "Content-Type": "application/json", ...c },
      });
    const p = r.headers.get("X-Team-Password");
    if (!p || p !== env.SHARED_PASSWORD)
      return new Response(JSON.stringify({ error: "Invalid team password" }), {
        status: 401,
        headers: { "Content-Type": "application/json", ...c },
      });
    const t = r.headers.get("X-Proxy-Target");
    let b;
    try {
      b = await r.json();
    } catch (e) {
      return json({ error: "Bad JSON body", detail: e.message }, 400, c);
    }
    try {
      if (t === "fal")        return await pF(b, env, c);
      if (t === "fal-submit") return await pFS(b, env, c);
      if (t === "fal-get")    return await pFG(b, env, c);
      if (t === "anthropic")  return await pA(b, env, c);
      return json({ error: "Unknown target", got: t }, 400, c);
    } catch (e) {
      return json({ error: "Worker exception", detail: e.message, stack: String(e.stack || "").slice(0, 500) }, 502, c);
    }
  },
};

function json(obj, status, c) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...c },
  });
}

async function safeJson(resp) {
  const text = await resp.text();
  try {
    return { ok: true, data: JSON.parse(text), text, status: resp.status };
  } catch (e) {
    return { ok: false, data: null, text, status: resp.status, parseErr: e.message };
  }
}

async function pF(b, env, c) {
  if (!b.endpoint || !b.input)
    return json({ error: "Missing endpoint or input", got: Object.keys(b) }, 400, c);
  const submitUrl = "https://queue.fal.run/" + b.endpoint;
  const s = await fetch(submitUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Key " + env.FAL_KEY },
    body: JSON.stringify(b.input),
  });
  const parsed = await safeJson(s);
  if (!parsed.ok) {
    return json({
      error: "fal submit returned non-JSON",
      upstreamStatus: parsed.status,
      upstreamUrl: submitUrl,
      bodyPreview: parsed.text.slice(0, 800),
    }, 502, c);
  }
  const d = parsed.data;
  if (!d.request_id) {
    return new Response(JSON.stringify(d), {
      status: s.status,
      headers: { "Content-Type": "application/json", ...c },
    });
  }
  const base = b.endpoint.replace(/\/[^/]+$/, "");
  const statusUrl = d.status_url || ("https://queue.fal.run/" + base + "/requests/" + d.request_id + "/status");
  const resultUrl = d.response_url || ("https://queue.fal.run/" + base + "/requests/" + d.request_id);
  for (let i = 0; i < 45; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    const sr = await fetch(statusUrl, { headers: { Authorization: "Key " + env.FAL_KEY } });
    const sp = await safeJson(sr);
    if (!sp.ok) {
      if (i === 0) {
        return json({
          error: "fal status returned non-JSON on first poll",
          upstreamStatus: sp.status,
          upstreamUrl: statusUrl,
          bodyPreview: sp.text.slice(0, 800),
          request_id: d.request_id,
        }, 502, c);
      }
      continue;
    }
    const status = sp.data.status;
    if (status === "COMPLETED") {
      const rr = await fetch(resultUrl, { headers: { Authorization: "Key " + env.FAL_KEY } });
      const rp = await safeJson(rr);
      if (!rp.ok) {
        return json({
          error: "fal result returned non-JSON",
          upstreamStatus: rp.status,
          bodyPreview: rp.text.slice(0, 800),
          request_id: d.request_id,
        }, 502, c);
      }
      return new Response(JSON.stringify(rp.data), {
        status: rr.status,
        headers: { "Content-Type": "application/json", ...c },
      });
    }
    if (status === "FAILED" || status === "ERROR") {
      return json({ error: "fal job failed", detail: sp.data }, 502, c);
    }
  }
  return json({
    error: "fal polling timeout after 135s",
    request_id: d.request_id,
    statusUrlUsed: statusUrl,
  }, 504, c);
}

async function pFS(b, env, c) {
  if (!b.endpoint || !b.input)
    return json({ error: "Missing endpoint or input", got: Object.keys(b) }, 400, c);
  const submitUrl = "https://queue.fal.run/" + b.endpoint;
  const s = await fetch(submitUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Key " + env.FAL_KEY },
    body: JSON.stringify(b.input),
  });
  const parsed = await safeJson(s);
  if (!parsed.ok) {
    return json({
      error: "fal submit returned non-JSON",
      upstreamStatus: parsed.status,
      upstreamUrl: submitUrl,
      bodyPreview: parsed.text.slice(0, 800),
    }, 502, c);
  }
  return new Response(JSON.stringify(parsed.data), {
    status: s.status,
    headers: { "Content-Type": "application/json", ...c },
  });
}

async function pFG(b, env, c) {
  if (!b.url || typeof b.url !== "string")
    return json({ error: "Missing url" }, 400, c);
  if (!b.url.startsWith("https://queue.fal.run/")) {
    return json({ error: "url must be a queue.fal.run URL" }, 400, c);
  }
  const r = await fetch(b.url, {
    headers: { Authorization: "Key " + env.FAL_KEY },
  });
  const parsed = await safeJson(r);
  if (!parsed.ok) {
    return json({
      error: "fal-get returned non-JSON",
      upstreamStatus: parsed.status,
      upstreamUrl: b.url,
      bodyPreview: parsed.text.slice(0, 800),
    }, 502, c);
  }
  return new Response(JSON.stringify(parsed.data), {
    status: r.status,
    headers: { "Content-Type": "application/json", ...c },
  });
}

async function pA(b, env, c) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": env.ANTHROPIC_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: b.model || "claude-sonnet-4-5",
      max_tokens: b.max_tokens || 1024,
      system: b.system || "",
      messages: b.messages || [],
    }),
  });
  const parsed = await safeJson(r);
  if (!parsed.ok)
    return json({
      error: "anthropic returned non-JSON",
      upstreamStatus: parsed.status,
      bodyPreview: parsed.text.slice(0, 800),
    }, 502, c);
  return new Response(JSON.stringify(parsed.data), {
    status: r.status,
    headers: { "Content-Type": "application/json", ...c },
  });
}
