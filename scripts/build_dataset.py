import json
import base64
import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "parks_manifest.json"
LIVE_PATH = REPO_ROOT / "parks_live_data.json"
IMAGES_DIR = REPO_ROOT / "park_images"
OUT_JS_PATH = REPO_ROOT / "parks_data.js"


def tier_for_pm25(pm25, is_raining):
    if pm25 is None:
        tier = "unknown"
    elif pm25 <= 15:
        tier = "excellent"
    elif pm25 <= 25:
        tier = "good"
    elif pm25 <= 37.5:
        tier = "moderate"
    elif pm25 <= 75:
        tier = "caution"
    else:
        tier = "avoid"

    if is_raining and tier in ("excellent", "good", "moderate"):
        tier = "caution"
    return tier


TIER_META = {
    "excellent": {"label_th": "ดีเยี่ยม", "activity_th": "วิ่ง ปั่นจักรยาน หรือออกกำลังกายหนักได้เต็มที่"},
    "good":      {"label_th": "ดี", "activity_th": "วิ่งเบาๆ เดินเร็ว ออกกำลังกายกลางแจ้งได้ตามปกติ"},
    "moderate":  {"label_th": "ปานกลาง", "activity_th": "เดินเบาๆ โยคะกลางแจ้งได้ กลุ่มเสี่ยง (เด็ก/ผู้สูงอายุ/โรคทางเดินหายใจ) ควรใส่หน้ากากหรือลดเวลา"},
    "caution":   {"label_th": "ควรเลี่ยงกิจกรรมหนัก", "activity_th": "แนะนำออกกำลังกายเบาๆ ในที่ร่มแทน หรือใส่หน้ากาก N95 หากจำเป็นต้องออกกลางแจ้ง"},
    "avoid":     {"label_th": "งดออกกำลังกายกลางแจ้ง", "activity_th": "งดกิจกรรมกลางแจ้งทุกชนิด แนะนำออกกำลังกายในร่มแทน"},
    "unknown":   {"label_th": "ไม่มีข้อมูล", "activity_th": "ไม่สามารถประเมินได้ในขณะนี้"},
}


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(LIVE_PATH, "r", encoding="utf-8") as f:
        live = {e["slug"]: e for e in json.load(f)}

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    parks_out = []
    for p in manifest:
        slug = p["slug"]
        entry = live.get(slug, {})
        aqicn = entry.get("aqicn") or {}
        owm = entry.get("owm") or {}

        iaqi = aqicn.get("iaqi", {})
        pm25 = iaqi.get("pm25", {}).get("v")
        pm10 = iaqi.get("pm10", {}).get("v")
        aqi = aqicn.get("aqi")
        station_name = (aqicn.get("city") or {}).get("name")
        station_time_iso = (aqicn.get("time") or {}).get("iso")
        dominant_pol = aqicn.get("dominentpol")

        try:
            forecast_pm25 = aqicn.get("forecast", {}).get("daily", {}).get("pm25", [])
        except Exception:
            forecast_pm25 = []

        rain_1h = 0
        weather_desc = None
        weather_id = None
        weather_icon = None
        temp = None
        humidity = None
        wind_speed = None
        if owm:
            rain_obj = owm.get("rain") or {}
            rain_1h = rain_obj.get("1h", 0) or 0
            w = (owm.get("weather") or [{}])[0]
            weather_desc = w.get("description")
            weather_id = w.get("id")
            weather_icon = w.get("icon")
            main = owm.get("main") or {}
            temp = main.get("temp")
            humidity = main.get("humidity")
            wind_speed = (owm.get("wind") or {}).get("speed")

        is_raining = rain_1h and rain_1h > 0
        tier = tier_for_pm25(pm25, is_raining)
        meta = TIER_META[tier]

        img_path = IMAGES_DIR / f"{slug}.jpg"
        with open(img_path, "rb") as imgf:
            b64 = base64.b64encode(imgf.read()).decode("ascii")
        img_data_uri = f"data:image/jpeg;base64,{b64}"

        parks_out.append({
            "slug": slug,
            "name_th": p["name_th"],
            "name_en": p["name_en"],
            "province": p["province"],
            "lat": p["lat"],
            "lon": p["lon"],
            "image": img_data_uri,
            "image_credit": {
                "author": p["image_author"],
                "license": p["image_license"],
                "source_url": p["image_source_url"],
            },
            "pm25": pm25,
            "pm10": pm10,
            "aqi": aqi,
            "dominant_pollutant": dominant_pol,
            "station_name": station_name,
            "station_time_iso": station_time_iso,
            "forecast_pm25": forecast_pm25,
            "weather": {
                "desc_th": weather_desc,
                "id": weather_id,
                "icon": weather_icon,
                "temp_c": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "rain_1h_mm": rain_1h,
                "is_raining": bool(is_raining),
            },
            "tier": tier,
            "tier_label_th": meta["label_th"],
            "activity_th": meta["activity_th"],
            "errors": entry.get("errors", []),
        })

    payload = {
        "generated_at_utc": now_utc,
        "parks": parks_out,
    }

    with open(OUT_JS_PATH, "w", encoding="utf-8") as f:
        f.write("const PARKS_DATA = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")

    print(f"wrote {len(parks_out)} parks to {OUT_JS_PATH}")


if __name__ == "__main__":
    main()
