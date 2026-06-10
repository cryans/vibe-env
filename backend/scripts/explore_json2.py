import json
from pathlib import Path
from collections import defaultdict
from html import escape

DATA_DIR = Path("/workspace/data/jsonl")
OUT_DIR = Path("/workspace/data/html")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Load JSONL
# ----------------------------
def load_all_jsonl():
    records = []

    for file in DATA_DIR.glob("*.jsonl"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    r = json.loads(line)
                    r["_file"] = file.name
                    records.append(r)
                except Exception as e:
                    records.append({
                        "error": str(e),
                        "raw": line,
                        "_file": file.name
                    })

    return records


# ----------------------------
# Group sessions
# ----------------------------
def group_by_session(records):
    sessions = defaultdict(list)

    for r in records:
        sid = r.get("session_id", "NO_SESSION")
        sessions[sid].append(r)

    for sid in sessions:
        sessions[sid].sort(key=lambda x: x.get("timestamp", ""))

    return sessions


# ----------------------------
# Session stats (overview layer)
# ----------------------------
def summarize_sessions(sessions):
    summary = []

    for sid, events in sessions.items():
        summary.append({
            "session_id": sid,
            "count": len(events),
            "models": ", ".join(sorted(set(e.get("model_id", "") for e in events))),
            "has_empty_response": any(not e.get("response") for e in events),
            "start": events[0].get("timestamp", ""),
            "end": events[-1].get("timestamp", ""),
        })

    # sort biggest sessions first
    summary.sort(key=lambda x: x["count"], reverse=True)

    return summary


# ----------------------------
# Clean text
# ----------------------------
def clean_text(text):
    if not text:
        return ""
    return str(text).replace("\\n", "\n").replace("\\t", "\t")


# ----------------------------
# Render full HTML
# ----------------------------
def render_html(summary, sessions):
    html = []

    html.append("""
<html>
<head>
<meta charset="utf-8">
<title>JSONL Explorer</title>

<style>
body {
    font-family: sans-serif;
    margin: 0;
    background: #f6f6f6;
}

.container {
    display: flex;
    height: 100vh;
}

/* LEFT PANE */
.left {
    width: 35%;
    overflow-y: scroll;
    background: #ffffff;
    border-right: 1px solid #ddd;
    padding: 10px;
}

.session-item {
    padding: 10px;
    margin-bottom: 8px;
    border: 1px solid #eee;
    border-radius: 6px;
    cursor: pointer;
    background: #fafafa;
}

.session-item:hover {
    background: #f0f0f0;
}

.small {
    font-size: 12px;
    color: #666;
}

/* RIGHT PANE */
.right {
    flex: 1;
    overflow-y: scroll;
    padding: 20px;
}

.msg {
    margin-bottom: 12px;
    padding: 12px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
}

.meta {
    font-size: 12px;
    color: #666;
    margin-bottom: 8px;
}

pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    background: #f7f7f7;
    padding: 10px;
    border-radius: 6px;
}
</style>

<script>
function showSession(id) {
    document.querySelectorAll('.session-view').forEach(el => {
        el.style.display = 'none';
    });

    const target = document.getElementById(id);
    if (target) {
        target.style.display = 'block';
    }
}
</script>

</head>
<body>

<div class="container">
""")

    # ----------------------------
    # LEFT: session index
    # ----------------------------
    html.append('<div class="left">')
    html.append("<h2>Sessions</h2>")

    for s in summary:
        sid = s["session_id"]

        html.append(f"""
        <div class="session-item" onclick="showSession('{sid}')">
            <b>{sid[:8]}...</b><br>
            <div class="small">
                msgs: {s['count']}<br>
                models: {s['models']}<br>
                {s['start']} → {s['end']}
            </div>
        </div>
        """)

    html.append("</div>")

    # ----------------------------
    # RIGHT: session viewer
    # ----------------------------
    html.append('<div class="right">')
    html.append("<h2>Session View</h2>")

    for sid, events in sessions.items():
        html.append(f'<div class="session-view" id="{sid}" style="display:none;">')
        html.append(f"<h3>{sid}</h3>")

        for e in events:
            ts = e.get("timestamp", "")
            model = e.get("model_id", "")
            prompt = escape(clean_text(e.get("prompt", "")))
            response = escape(clean_text(e.get("response", "")))

            html.append(f"""
            <div class="msg">
                <div class="meta">{ts} | {model}</div>
                <b>Prompt</b>
                <pre>{prompt}</pre>
                <b>Response</b>
                <pre>{response}</pre>
            </div>
            """)

        html.append("</div>")

    html.append("</div>")  # right
    html.append("</div>")  # container
    html.append("</body></html>")

    return "\n".join(html)


# ----------------------------
# Main
# ----------------------------
def main():
    records = load_all_jsonl()
    sessions = group_by_session(records)
    summary = summarize_sessions(sessions)

    html = render_html(summary, sessions)

    out_file = OUT_DIR / "explorer.html"
    out_file.write_text(html, encoding="utf-8")

    print(f"[OK] written: {out_file}")
    print(f"[OPEN] explorer.exe {out_file.resolve()}")


if __name__ == "__main__":
    main()
