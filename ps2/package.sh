#!/bin/bash
# Build the submission ZIP (configs, scripts, evidence, report, slides). Run in WSL2 Ubuntu: ./package.sh
cd "$(dirname "$0")"
source ~/hack-env/bin/activate 2>/dev/null
python gen.py >/dev/null
python tools/make_deck.py >/dev/null
python - <<'PY'
import os, zipfile
out = "../PS2_Flatland_submission.zip"
skip_dirs, skip_files = {"__pycache__"}, {"w.sh"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if f in skip_files or (f.startswith("t") and f.endswith(".sh") and len(f) <= 7) or f.startswith("_sheet"): continue
            p = os.path.join(root, f)
            z.write(p, os.path.join("ps2", os.path.relpath(p, ".")))
print("wrote", os.path.abspath(out), round(os.path.getsize(out) / 1e6, 2), "MB,", len(zipfile.ZipFile(out).namelist()), "files")
PY
