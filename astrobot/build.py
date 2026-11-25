"""Builds preview.html (single file, CSV data embedded) from index.html + static files."""
import csv, json
from pathlib import Path
B = Path(__file__).parent
rows = list(csv.DictReader(open(B/"data"/"knowledge.csv", encoding="utf-8")))
for r in rows: r["keywords"] = [k.strip().lower() for k in r["keywords"].split("|")]
h = (B/"index.html").read_text(encoding="utf-8")
h = h.replace('<link rel="stylesheet" href="static/style.css">', "<style>"+(B/"static"/"style.css").read_text(encoding="utf-8")+"</style>")
js = "<script>window.EMBEDDED="+json.dumps(rows, ensure_ascii=False)+";</script><script>"+(B/"static"/"script.js").read_text(encoding="utf-8")+"</script>"
h = h.replace('<script src="static/script.js"></script>', js)
(B/"preview.html").write_text(h, encoding="utf-8")
