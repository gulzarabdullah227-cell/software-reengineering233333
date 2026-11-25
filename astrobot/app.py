"""AstroBot - a space chatbot. Run: python app.py  (web)  |  python app.py --cli  (terminal)"""
import csv, difflib, json, mimetypes, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
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
    scored = [(sum(bool(re.search(r"\b" + re.escape(k) + r"\b", msg)) for k in r["keywords"]), r) for r in ROWS]
    best = max(scored, key=lambda s: s[0])
    if best[0] > 0:
        return best[1]["answer"]
    m = difflib.get_close_matches(msg, QUESTIONS.keys(), n=1, cutoff=0.5)
    return QUESTIONS[m[0]]["answer"] if m else FALLBACK


def cli():
    print("AstroBot 🚀 (type 'bye' to exit)")
    while (msg := input("You: ").lower().strip()) != "bye":
        print("Bot:", get_reply(msg))
    print("Bot: Goodbye, space explorer! 👋")


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="application/json", code=200):
        if ctype.startswith("text/") or ctype in {"application/json", "application/javascript"}:
            if "charset=" not in ctype:
                ctype = f"{ctype}; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        clean_path = urlparse(self.path).path
        if clean_path == "/health":
            return self._send(json.dumps({"status": "ok", "topics": len(ROWS)}).encode("utf-8"))
        if clean_path == "/api/data":
            return self._send(json.dumps(ROWS, ensure_ascii=False).encode("utf-8"))
        rel = "index.html" if clean_path == "/" else clean_path.lstrip("/")
        f = (BASE / rel).resolve()
        if BASE in f.parents and f.is_file() and f.suffix in {".html", ".css", ".js"}:
            ctype = mimetypes.guess_type(f.name)[0] or "text/plain"
            return self._send(f.read_bytes(), ctype)
        self._send(b"Not found", "text/plain", 404)

    def do_POST(self):
        clean_path = urlparse(self.path).path
        if clean_path != "/api/chat":
            return self._send(b"{}", code=404)
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(json.dumps({"error": "Invalid JSON"}).encode("utf-8"), code=400)
        reply = get_reply(str(data.get("message", "")))
        self._send(json.dumps({"reply": reply}, ensure_ascii=False).encode("utf-8"))


class AstroBotServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def get_port(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args):
            return int(args[idx + 1])
    return int(os.environ.get("PORT", "8000"))


def create_server(port=None):
    bind_port = get_port() if port is None else port
    return AstroBotServer(("", bind_port), Handler)


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        port = get_port()
        server = create_server(port)
        print(f"AstroBot running at http://localhost:{port}  (Ctrl+C to stop)", flush=True)
        server.serve_forever()
