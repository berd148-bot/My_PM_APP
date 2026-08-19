import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

with open(REPO_ROOT / "template.html", "r", encoding="utf-8") as f:
    tpl = f.read()

with open(REPO_ROOT / "fonts" / "embedded_fonts.css", "r", encoding="utf-8") as f:
    fonts_css = f.read()

with open(REPO_ROOT / "thailand_map_datauri.txt", "r", encoding="utf-8") as f:
    map_datauri = f.read()

with open(REPO_ROOT / "parks_data.js", "r", encoding="utf-8") as f:
    parks_js = f.read()

out = tpl.replace("/*__FONTS_CSS__*/", fonts_css)
out = out.replace("__MAP_IMAGE_DATAURI__", map_datauri)
out = out.replace("/*__PARKS_DATA__*/", parks_js)

out_path = REPO_ROOT / "airpark.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out)

print("wrote", out_path, "size bytes:", os.path.getsize(out_path))
