"""AstroBot - a space chatbot. Run: python app.py  (web)  |  python app.py --cli  (terminal)"""
import csv, difflib, json, re, sys, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent
FALLBACK = "Hmm 🤔 I didn't catch that. Try one of the suggested questions!"

def load_data():
    with open(BASE / "data" / "knowledge.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["keywords"] = [k.strip().lower() for k in r["keywords"].split("|") if k.strip()]
    return rows

ROWS = load_data()
QUESTIONS = {r["question"].lower(): r for r in ROWS}

def get_reply(msg):
    msg = msg.lower().strip()
    # 1) keyword match (from the first code): pick the row with most keyword hits
    scored = [(sum(bool(re.search(r'\b'+re.escape(k)+r'\b', msg)) for k in r["keywords"]), r) for r in ROWS]
    best = max(scored, key=lambda s: s[0])
    if best[0] > 0:
        return best[1]["answer"]
    # 2) fuzzy match (from the second code) using difflib
    m = difflib.get_close_matches(msg, QUESTIONS.keys(), n=1, cutoff=0.5)
    return QUESTIONS[m[0]]["answer"] if m else FALLBACK

def cli():
    print("AstroBot 🚀 (type 'bye' to exit)")
    while (msg := input("You: ").lower().strip()) != "bye":
        print("Bot:", get_reply(msg))
    print("Bot: Goodbye, space explorer! 👋")

class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="application/json", code=200):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/data":
            return self._send(json.dumps(ROWS).encode())
        path = "index.html" if self.path == "/" else self.path.lstrip("/")
        f = (BASE / path).resolve()
        if BASE in f.parents and f.is_file() and f.suffix in {".html", ".css", ".js"}:
            return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "text/plain")
        self._send(b"Not found", "text/plain", 404)

    def do_POST(self):
        if self.path != "/api/chat":
            return self._send(b"{}", code=404)
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        self._send(json.dumps({"reply": get_reply(data.get("message", ""))}).encode())

if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        print("AstroBot running at http://localhost:8000  (Ctrl+C to stop)")
        ThreadingHTTPServer(("", 8000), Handler).serve_forever()
