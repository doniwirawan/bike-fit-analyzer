# Bike Fit Analyzer — MCP server

Exposes the analyzer as MCP tools, so a clip can be graded from a chat client
instead of a browser.

## Tools

- `analyze_bike_fit(video_path, bike_type="road_endurance", start_sec, end_sec)`
  → verdict, the four angles, their grades, targets, and what to change.
- `list_bike_types()` → the torso target for each bike type.

## Install

The server runs on the repo's virtualenv (it needs `ultralytics`, `opencv`, `mcp`)
and on `yolo11x-pose.pt` in the repo root.

```sh
.venv/Scripts/python -m pip install mcp ultralytics opencv-python
```

### Claude Code

`.mcp.json` in the repo root already registers it — Claude Code picks it up when
started from this directory. Or register it globally:

```sh
claude mcp add bike-fit -- /path/to/.venv/Scripts/python.exe /path/to/mcp/server.py
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bike-fit": {
      "command": "C:\\Users\\doniw\\Downloads\\bike-fitting-v2\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\doniw\\Downloads\\bike-fitting-v2\\mcp\\server.py"]
    }
  }
}
```

Use absolute paths there — Claude Desktop does not run from the repo directory —
and **double** the backslashes, or the JSON won't parse.

## Using it

Ask in plain language and give the client a path to the clip:

> Analyze `C:\Users\me\Videos\ride.mp4` as a gravel bike, using seconds 5 to 35.
>
> What torso angle should a TT bike be graded against?

`analyze_bike_fit` shells out to the YOLO pipeline, so it is **slow**: budget a few
minutes per clip on CPU, most of it pose inference. Trim with `start_sec`/`end_sec`
to the steadiest few seconds of pedalling — that is both faster and more accurate
than handing it the whole clip. It needs at least one full pedal stroke, so windows
under ~2 seconds fail with "No clear pedal strokes found".

If the call runs past 15 minutes it gives up and returns the exact shell command it
tried, so you can run that yourself and see the real error.

**After editing `server.py`, restart the MCP connection** — the client keeps one
long-lived server process, so a running server is still executing the code that was
on disk when it started, and edits do nothing until it is restarted.

## It does NOT agree exactly with the website

This server runs the **YOLO** pose pipeline (`files/analyze_bikefit.py`). The web
app runs **MediaPipe**. The grading zones are identical, but the pose models
differ, and on the same clip they disagree by a few degrees:

| angle | web (MediaPipe) | MCP (YOLO) | Δ |
|---|---|---|---|
| knee at bottom | 20° RED | 23.3° RED | 3.3 |
| torso | 42° GREEN | 43.0° GREEN | 1.0 |
| elbow | 20° GREEN | 23.4° GREEN | 3.4 |
| shoulder | 81° **GREEN** | 77.1° **AMBER** | 3.9 |

Three of four grades match. The shoulder does not — 81 and 77 sit either side of
the 80° boundary, so a 4° difference flips the verdict. Treat this server as a
convenience, not a second opinion: **the web app is the reference.**

Each result carries that caveat in its `caveats` field.
