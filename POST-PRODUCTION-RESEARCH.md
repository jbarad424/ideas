# Video Post-Production: Logo & Text Overlay Research

## 1. Can AI Video Models Render Legible Text?

**No. Do not rely on any gen model for text overlays.**

Kling 3.0 is the best of the bunch — product labels and brand names stay somewhat legible at 4K — but "somewhat" is not production quality. Veo 3.1 explicitly lists readable text as a known limitation. Sora struggled with it consistently. Seedance 2.0 comparisons focus on motion/audio, never mention text quality (telling omission). None of these models can render a clean "Chubby Buttons" wordmark or logo. Text/logo overlays must be added in post.

## 2. Overlay APIs Compared

| Tool | Type | Cost | Latency | Client-side? | Notes |
|------|------|------|---------|-------------|-------|
| **FFmpeg WASM** | JS library | Free (OSS) | 10-60s in browser | Yes | Full FFmpeg in browser. ~25MB bundle. Proven for overlays, text, filters. No server needed. |
| **Creatomate** | SaaS API | $41/mo for 144 min ($0.28/min) | 5-30s server-side | No | JSON-driven templates. Logo + text overlay is core use case. Free trial: 50 credits. |
| **Shotstack** | SaaS API | $0.40/min PAYG, $0.20/min on $39/mo plan | 5-30s server-side | No | REST API, timeline-based JSON. Text + image overlay well-documented. 10 free credits. |
| **Bannerbear** | SaaS API | $49/mo base | 10-30s server-side | No | Template-driven. ~8 credits per 30s clip with 2 overlays. More image-focused. |
| **Remotion** | React framework | $10/1000 renders (self-host) + AWS Lambda | 10-60s on Lambda | Hybrid | Full design control via React. Overkill for simple overlays. |
| **WebCodecs + Canvas** | Browser API | Free | Real-time | Yes | Decode frames, draw on Canvas, re-encode. Chrome 94+, Firefox 130+. Most code, most control. No bundle bloat. |

**FFmpeg on Cloudflare Workers?** Not recommended. CF Workers cap at 10MB (paid) and 128MB memory. FFmpeg WASM is ~25MB. Multiple community threads report partial success but frequent failures.

## 3. Recommended Path

### Option A: FFmpeg WASM in Browser (RECOMMENDED)

One FFmpeg command does logo-in-corner + text-at-bottom:

```
ffmpeg -i input.mp4 -i logo.png -filter_complex
  "[0:v][1:v]overlay=W-w-20:20,
   drawtext=text='CB2 Wearable Remote':fontsize=28:fontcolor=white:
   x=(w-text_w)/2:y=h-60:box=1:boxcolor=black@0.5:boxborderw=8"
  -codec:a copy output.mp4
```

**Integration:** Add a "Brand It" button in Video Lab. Loads ffmpeg.wasm (~25MB, cached after first load), processes locally, produces a download. Zero server cost. 10-30s for a 5s clip.

### Option B: Creatomate API (server-side fallback)

Design template in visual editor, hit API with video URL. ~$0.02 per 5s clip. $41/mo gets 144 minutes. Best if mobile performance matters.

### Option C: WebCodecs + Canvas (zero-dependency)

Smallest bundle, hardest to implement. Only worth it if the 25MB WASM download is a dealbreaker.

## 4. AI Models for Post-Production Overlays?

No. Runway ML Gen-2 has generative overlays (AI-styled, not pixel-perfect). HeyGen adds text but targets talking-head videos. For pixel-perfect brand logos, traditional compositing is the only reliable path.

## 5. Bottom Line

**Go with FFmpeg WASM in the browser (Option A).** Zero ongoing cost, entirely client-side, handles logo + lower-third in one pass. If mobile performance is bad, upgrade to Creatomate at $41/mo. Do not attempt AI-based text insertion.
