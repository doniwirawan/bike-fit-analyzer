"""
Tiny dependency-free upload page for the bike-fit video.
Run:  python upload_server.py
Then open http://localhost:8000 in your browser and drop your clip in.
The file is saved to ./uploads/ and the path is printed here.
"""
import http.server
import os
import socketserver
import re

PORT = 8000
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB limit

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload your bike-fit video</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    min-height:100vh; display:grid; place-items:center;
    background:#f5f6f8; color:#15181c; }
  @media (prefers-color-scheme: dark){ body{ background:#0f1115; color:#e7e9ee; } }
  .card { width:min(560px,92vw); background:#fff; border-radius:16px; padding:32px;
    box-shadow:0 10px 40px rgba(0,0,0,.12); }
  @media (prefers-color-scheme: dark){ .card{ background:#181b22; box-shadow:0 10px 40px rgba(0,0,0,.5);} }
  h1 { font-size:1.35rem; margin:0 0 6px; }
  p.sub { margin:0 0 22px; opacity:.7; font-size:.92rem; line-height:1.45; }
  #drop { border:2px dashed #b9c0cc; border-radius:14px; padding:40px 20px; text-align:center;
    cursor:pointer; transition:.15s; }
  #drop.hi { border-color:#3b82f6; background:rgba(59,130,246,.08); }
  #drop .big { font-size:2.4rem; }
  #drop .hint { margin-top:8px; opacity:.65; font-size:.88rem; }
  #name { margin-top:16px; font-weight:600; word-break:break-all; }
  #bar { height:10px; background:#e6e8ee; border-radius:6px; overflow:hidden; margin-top:16px; display:none; }
  @media (prefers-color-scheme: dark){ #bar{ background:#2a2e38; } }
  #fill { height:100%; width:0%; background:#3b82f6; transition:width .2s; }
  #status { margin-top:14px; font-size:.92rem; min-height:1.2em; }
  .ok { color:#16a34a; font-weight:600; } .err { color:#dc2626; font-weight:600; }
  button { margin-top:18px; width:100%; padding:12px; border:0; border-radius:10px;
    background:#3b82f6; color:#fff; font-size:1rem; font-weight:600; cursor:pointer; }
  button:disabled { opacity:.5; cursor:default; }
</style></head>
<body><div class="card">
  <h1>Upload your bike-fit video</h1>
  <p class="sub">Side-on clip of you pedaling, 20-30s. Drag it in or click to pick.
     It's saved locally on your own computer only.</p>
  <div id="drop">
    <div class="big">&#127909;</div>
    <div>Drop your video here or <u>click to browse</u></div>
    <div class="hint">.mp4 .mov .m4v .avi .mkv</div>
    <input id="file" type="file" accept="video/*" hidden>
  </div>
  <div id="name"></div>
  <div id="bar"><div id="fill"></div></div>
  <div id="status"></div>
  <button id="go" disabled>Upload</button>
</div>
<script>
  const drop=document.getElementById('drop'), inp=document.getElementById('file'),
        nameEl=document.getElementById('name'), go=document.getElementById('go'),
        bar=document.getElementById('bar'), fill=document.getElementById('fill'),
        st=document.getElementById('status');
  let chosen=null;
  function pick(f){ chosen=f; nameEl.textContent=f? ('Selected: '+f.name+' ('+(f.size/1048576).toFixed(1)+' MB)'):''; go.disabled=!f; st.textContent=''; }
  drop.onclick=()=>inp.click();
  inp.onchange=e=>pick(e.target.files[0]);
  ['dragover','dragenter'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('hi');}));
  ['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('hi');}));
  drop.addEventListener('drop',e=>{ if(e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]); });
  go.onclick=()=>{
    if(!chosen) return;
    go.disabled=true; bar.style.display='block'; st.textContent='Uploading...';
    const fd=new FormData(); fd.append('file',chosen,chosen.name);
    const xhr=new XMLHttpRequest(); xhr.open('POST','/upload');
    xhr.upload.onprogress=e=>{ if(e.lengthComputable){ fill.style.width=(e.loaded/e.total*100).toFixed(0)+'%'; } };
    xhr.onload=()=>{ if(xhr.status===200){ st.innerHTML='<span class="ok">&#10003; Uploaded! You can close this tab — the analysis will start.</span>'; }
      else { st.innerHTML='<span class="err">Upload failed: '+xhr.responseText+'</span>'; go.disabled=false; } };
    xhr.onerror=()=>{ st.innerHTML='<span class="err">Network error.</span>'; go.disabled=false; };
    xhr.send(fd);
  };
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/upload":
            self.send_error(404)
            return
        ctype = self.headers.get("Content-Type", "")
        m = re.search(r"boundary=(.+)$", ctype)
        if not m:
            self._reply(400, "no boundary")
            return
        boundary = ("--" + m.group(1).strip('"')).encode()
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_UPLOAD_BYTES:
            self._reply(413, f"File too large (max {MAX_UPLOAD_BYTES // (1024*1024)} MB)")
            return
        body = self._read_exact(length)
        # split the one file part out of the multipart body
        parts = body.split(boundary)
        for part in parts:
            if b'filename="' in part:
                fn = re.search(rb'filename="([^"]*)"', part).group(1).decode("utf-8", "replace")
                fn = os.path.basename(fn) or "upload.bin"
                # Avoid silent filename collision: append counter suffix if file exists
                base, ext = os.path.splitext(fn)
                counter = 1
                dest = os.path.join(UPLOAD_DIR, fn)
                while os.path.exists(dest):
                    fn = f"{base}_{counter}{ext}"
                    dest = os.path.join(UPLOAD_DIR, fn)
                    counter += 1
                data = part.split(b"\r\n\r\n", 1)[1]
                if data.endswith(b"\r\n"):
                    data = data[:-2]
                dest = os.path.join(UPLOAD_DIR, fn)
                with open(dest, "wb") as f:
                    f.write(data)
                print(f"\n>>> RECEIVED: {dest} ({len(data)/1048576:.1f} MB)\n", flush=True)
                self._reply(200, "ok")
                return
        self._reply(400, "no file field")

    def _read_exact(self, n):
        buf = bytearray()
        while len(buf) < n:
            chunk = self.rfile.read(min(1 << 20, n - len(buf)))
            if not chunk:
                break
            buf += chunk
        return bytes(buf)

    def _reply(self, code, msg):
        b = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    print(f"Upload page ready.  Open  http://localhost:{PORT}  in your browser.")
    print(f"Saving uploads to: {UPLOAD_DIR}")
    Server(("127.0.0.1", PORT), Handler).serve_forever()
