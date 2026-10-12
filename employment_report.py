"""Self-contained interactive report; all data embedded, no CDN or network."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write_html(result, folder):
    observed = ROOT / "data" / "observed" / "observed_summary.json"
    obs = json.loads(observed.read_text(encoding="utf-8")) if observed.exists() else {}
    template = (ROOT / "report_template.html").read_text(encoding="utf-8")
    # JSON in script is escaped against premature closing tags.
    payload = json.dumps(dict(sim=result,obs=obs),ensure_ascii=False).replace("<","\\u003c")
    (folder / "occupazione.html").write_text(template.replace("__PAYLOAD__",payload),encoding="utf-8")


if __name__ == "__main__":
    folder=ROOT/"outputs"/"employment"
    write_html(json.loads((folder/"results.json").read_text(encoding="utf-8")),folder)
