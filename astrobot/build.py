"""Builds preview.html (single file, CSV data embedded) from index.html + static files."""
import csv, json
from pathlib import Path

B = Path(__file__).resolve().parent


def build_preview():
    with open(B / "data" / "knowledge.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["keywords"] = [k.strip().lower() for k in r["keywords"].split("|") if k.strip()]
    h = (B / "index.html").read_text(encoding="utf-8")
    css = (B / "static" / "style.css").read_text(encoding="utf-8")
    js_code = (B / "static" / "script.js").read_text(encoding="utf-8")
    h = h.replace('<link rel="stylesheet" href="static/style.css">', f"<style>{css}</style>")
    js = f"<script>window.EMBEDDED={json.dumps(rows, ensure_ascii=False)};</script><script>{js_code}</script>"
    h = h.replace('<script src="static/script.js"></script>', js)
    out = B / "preview.html"
    out.write_text(h, encoding="utf-8")
    root_preview = B.parent / "AstroBot_preview.html"
    if root_preview.parent.exists():
        root_preview.write_text(h, encoding="utf-8")
    return out


if __name__ == "__main__":
    output_path = build_preview()
    print(f"Built preview: {output_path}")
