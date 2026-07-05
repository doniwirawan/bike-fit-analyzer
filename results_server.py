"""
Local results viewer for the bike-fit analyzer.
Run:  python results_server.py
Then open http://localhost:8080  to see every out_fit_* result:
the graded report, the bottom-of-stroke screenshot, and the overlay video.
"""
import http.server
import glob
import html
import os
import re

PORT = 8090
ROOT = os.path.dirname(os.path.abspath(__file__))

GRADE_COLOR = {"GREEN": "#16a34a", "AMBER": "#d97706", "RED": "#dc2626"}


def render_report(md):
    """Turn report.md into simple HTML with colored grades."""
    out = []
    for line in md.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("# "):
            out.append(f"<h3>{html.escape(line[2:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h4>{html.escape(line[3:])}</h4>")
        elif line.startswith("- "):
            txt = html.escape(line[2:])
            for g, c in GRADE_COLOR.items():
                txt = txt.replace(g, f'<b style="color:{c}">{g}</b>')
            out.append(f"<div class='li'>{txt}</div>")
        else:
            out.append(f"<div>{html.escape(line)}</div>")
    return "\n".join(out)


def page():
    dirs = sorted(glob.glob(os.path.join(ROOT, "out_fit*")))
    cards = []
    for d in dirs:
        name = os.path.basename(d)
        report_p = os.path.join(d, "report.md")
        still_p = os.path.join(d, "stills", "bdc.jpg")
        video_p = os.path.join(d, "overlay_h264.mp4")
        if not os.path.exists(report_p):
            cards.append(f"<div class='card'><h2>{name}</h2><p class='muted'>Still processing…</p></div>")
            continue
        report_html = render_report(open(report_p, encoding="utf-8").read())
        still = f"{name}/stills/bdc.jpg" if os.path.exists(still_p) else ""
        video = f"{name}/overlay_h264.mp4" if os.path.exists(video_p) else ""
        media = ""
        if still:
            media += f"<figure><figcaption>Bottom of pedal stroke</figcaption><img src='{still}'></figure>"
        if video:
            media += f"<figure><figcaption>Overlay (play it)</figcaption><video src='{video}' controls preload='metadata'></video></figure>"
        cards.append(f"""<div class='card'><h2>{name}</h2>
          <div class='grid'><div class='report'>{report_html}</div><div class='media'>{media}</div></div></div>""")
    if not cards:
        cards.append("<div class='card'><p class='muted'>No results yet. Run the analyzer first.</p></div>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bike Fit Results</title><style>
:root{{color-scheme:light dark}}*{{box-sizing:border-box}}
body{{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#f4f5f7;color:#15181c;padding:24px}}
@media(prefers-color-scheme:dark){{body{{background:#0f1115;color:#e7e9ee}}}}
h1{{font-size:1.5rem;margin:0 0 4px}} .sub{{opacity:.65;margin:0 0 22px}}
.card{{background:#fff;border-radius:16px;padding:22px 24px;margin:0 auto 22px;max-width:1050px;box-shadow:0 8px 30px rgba(0,0,0,.10)}}
@media(prefers-color-scheme:dark){{.card{{background:#181b22;box-shadow:0 8px 30px rgba(0,0,0,.5)}}}}
.card h2{{margin:0 0 14px;font-size:1.15rem}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}
.report h3{{margin:.2em 0}} .report h4{{margin:1em 0 .3em;opacity:.7;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em}}
.li{{padding:3px 0;font-size:.95rem;line-height:1.4}}
figure{{margin:0 0 16px}} figcaption{{font-size:.8rem;opacity:.6;margin-bottom:6px}}
img,video{{width:100%;border-radius:10px;background:#000}}
.muted{{opacity:.6}}
</style></head><body>
<h1>🚴 Bike Fit Results</h1>
<p class="sub">Green = dialed · Amber = borderline · Red = fix it. Auto-refreshes every 20s.</p>
{''.join(cards)}
<script>setTimeout(()=>location.reload(),20000)</script>
</body></html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


if __name__ == "__main__":
    print(f"Results viewer at http://localhost:{PORT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
