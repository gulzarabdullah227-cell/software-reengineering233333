"""Automated unit and HTTP integration tests for AstroBot."""
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app
import build


class TestAstroBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.create_server(port=0)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_load_data(self):
        rows = app.load_data()
        self.assertGreaterEqual(len(rows), 20)
        for row in rows:
            self.assertTrue(row["question"])
            self.assertTrue(row["answer"])
            self.assertTrue(row["keywords"])

    def test_get_reply_keyword_and_fuzzy(self):
        self.assertIn("iron oxide", app.get_reply("Why is Mars red?").lower())
        self.assertIn("gravity", app.get_reply("what is a black hole").lower())
        self.assertEqual(app.get_reply("zzzzzz unknown query 12345"), app.FALLBACK)

    def test_health_and_static_endpoints(self):
        with urlopen(f"{self.base_url}/health") as res:
            self.assertEqual(res.status, 200)
            payload = json.loads(res.read().decode("utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertGreaterEqual(payload["topics"], 20)

        with urlopen(f"{self.base_url}/") as res:
            self.assertEqual(res.status, 200)
            html = res.read().decode("utf-8")
            self.assertIn("AstroBot", html)

        with urlopen(f"{self.base_url}/static/style.css") as res:
            self.assertEqual(res.status, 200)
            self.assertIn("text/css", res.headers.get("Content-Type", ""))

        with urlopen(f"{self.base_url}/static/script.js") as res:
            self.assertEqual(res.status, 200)
            self.assertIn("buildSuggestions", res.read().decode("utf-8"))

    def test_api_data_and_chat(self):
        with urlopen(f"{self.base_url}/api/data") as res:
            self.assertEqual(res.status, 200)
            rows = json.loads(res.read().decode("utf-8"))
            self.assertGreaterEqual(len(rows), 20)

        req = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"message": "Why is Mars red?"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("rust", data["reply"].lower())

    def test_not_found(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/does-not-exist")
        self.assertEqual(ctx.exception.code, 404)

    def test_build_preview(self):
        out = build.build_preview()
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("window.EMBEDDED=", content)


if __name__ == "__main__":
    unittest.main()
