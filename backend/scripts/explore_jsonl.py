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
# Evidence tagging (simple heuristic)
# ----------------------------
def is_evidence(record):
    text = (
        str(record.get("prompt", "")) + " " +
        str(record.get("response", ""))
    ).lower()

    keywords = [
        "decision",
        "important",
        "bug",
        "root cause",
        "architecture",
        "final",
        "chose",
        "we will",
        "we decided",
        "fix",
        "issue",
        "conclusion"
    ]

    return any(k in text for k in keywords)


# ----------------------------
# Group by session
# ----------------------------
def group_by_session(records):
    sessions = defaultdict(list)

    for r in records:
        sid = r.get("session_id", "NO_SESSION")

        r["_evidence"] = is_evidence(r)

        sessions[sid].append(r)

    # best-effort ordering
    for sid in sessions:
        sessions[sid].sort(key=lambda x: x.get("timestamp", ""))

    return sessions


# ----------------------------
# Clean escaped text
# ----------------------------
def clean_text(text):
    if not text:
        return ""

    return (
        str(text)
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


# ----------------------------
# HTML rendering
# ----------------------------
def render_html(sessions):
    html = [
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<style>",

        "body { font-family: sans-serif; margin: 20px; background: #fafafa; }",

        ".session {",
        "  margin-bottom: 50px;",
        "  padding: 15px;",
        "  border: 1px solid #ddd;",
        "  background: white;",
        "  border-radius: 8px;",
        "}",

        ".msg {",
        "  margin: 12px 0;",
        "  padding: 12px;",
        "  border: 1px solid #eee;",
        "  border-radius: 6px;",
        "  background: #fcfcfc;",
        "}",

        ".meta { font-size: 12px; color: #666; margin-bottom: 8px; }",

        ".evidence { color: #b8860b; font-weight: bold; }",

        "pre {",
        "  white-space: pre-wrap;",
        "  word-wrap: break-word;",
        "  background: #f6f6f6;",
        "  padding: 10px;",
        "  border-radius: 6px;",
        "}",

        "</style>",
        "</head>",
        "<body>",

        "<h1>JSONL Session Explorer</h1>",
        "<p>⭐ = Evidence flagged interaction</p>",
    ]

    for sid, events in sessions.items():
        html.append(f"<div class='session'>")
        html.append(f"<h2>Session: {sid}</h2>")

        for e in events:
            ts = e.get("timestamp", "")
            model = e.get("model_id", "")

            prompt = escape(clean_text(e.get("prompt", "")))
            response = escape(clean_text(e.get("response", "")))

            evidence_flag = "⭐ EVIDENCE" if e.get("_evidence") else ""

            html.append(f"""
            <div class='msg'>
                <div class='meta'>
                    {ts} | {model}
                    <span class="evidence">{evidence_flag}</span>
                </div>

                <div class='prompt'>
                    <b>User:</b>
                    <pre>{prompt}</pre>
                </div>

                <div class='response'>
                    <b>Assistant:</b>
                    <pre>{response}</pre>
                </div>
            </div>
            """)

        html.append("</div>")

    html.append("</body></html>")
    return "\n".join(html)


# ----------------------------
# Main
# ----------------------------
def main():
    records = load_all_jsonl()
    sessions = group_by_session(records)

    html = render_html(sessions)

    out_file = OUT_DIR / "sessions.html"
    out_file.write_text(html, encoding="utf-8")

    print(f"[OK] written: {out_file}")
    print("[INFO] open manually:")
    print(f"       explorer.exe {out_file.resolve()}")


if __name__ == "__main__":
    main()
