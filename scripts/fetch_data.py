import json
import os
import sys
import time
import urllib.request
from pathlib import Path

AQICN_TOKEN = os.environ.get("AQICN_TOKEN", "")
OWM_KEY = os.environ.get("OWM_KEY", "")

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "parks_manifest.json"
OUT_PATH = REPO_ROOT / "parks_live_data.json"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if not AQICN_TOKEN or not OWM_KEY:
        print("ERROR: AQICN_TOKEN and OWM_KEY environment variables must be set", file=sys.stderr)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        parks = json.load(f)

    results = []
    for p in parks:
        slug = p["slug"]
        lat, lon = p["lat"], p["lon"]
        entry = {"slug": slug, "aqicn": None, "owm": None, "errors": []}

        try:
            aqicn_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_TOKEN}"
            aqicn_data = fetch_json(aqicn_url)
            if aqicn_data.get("status") == "ok":
                entry["aqicn"] = aqicn_data["data"]
            else:
                entry["errors"].append(f"aqicn status={aqicn_data.get('status')}")
        except Exception as e:
            entry["errors"].append(f"aqicn error: {e}")

        try:
            owm_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_KEY}&units=metric&lang=th"
            owm_data = fetch_json(owm_url)
            entry["owm"] = owm_data
        except Exception as e:
            entry["errors"].append(f"owm error: {e}")

        results.append(entry)
        print(f"done: {slug} errors={entry['errors']}", file=sys.stderr)
        time.sleep(0.3)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"wrote {len(results)} entries to {OUT_PATH}")


if __name__ == "__main__":
    main()
