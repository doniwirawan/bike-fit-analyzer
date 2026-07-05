# Browser version (Vercel-deployable)

A single static page that runs the whole bike-fit analysis **in the visitor's
browser** — pose detection uses [MediaPipe Pose](https://ai.google.dev/edge/mediapipe)
(WebGPU, falling back to WASM). The video never leaves the device, and there is
**no server compute**, so it deploys anywhere static — including Vercel's free tier.

This is the browser port of the Python `analyze_bikefit.py`: same angles, same
BDC-median logic, same green/amber/red grading, drawn on a `<canvas>`.

## Run locally

```bash
cd web
python -m http.server 5173
# open http://localhost:5173
```

(A server is needed because it loads as an ES module — opening the file directly
via `file://` won't work.)

## Deploy to Vercel

```bash
npm i -g vercel
cd web
vercel        # follow prompts; it's a static deploy, no build step
```

Or drag the `web/` folder into the Vercel dashboard. No config needed — it's
plain HTML/JS. MediaPipe's model + WASM load from public CDNs at runtime.

## Notes / trade-offs

- **First load** downloads the MediaPipe model (~10 MB) once, then it's cached.
- **WebGPU** browsers (recent Chrome/Edge) are fast; older browsers fall back to
  slower WASM.
- Uses MediaPipe's **33-landmark** BlazePose model (not YOLO11). It's lighter and
  browser-native — and **Apache-2.0 licensed**, which avoids YOLO11's AGPL terms
  for a shipped product.
- It's a **proof-of-concept**: accuracy on heavy pedaling blur is lower than the
  desktop `yolo11x` pipeline. For the most accurate read, use the Python version.
