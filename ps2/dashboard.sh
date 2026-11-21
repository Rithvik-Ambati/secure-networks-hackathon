#!/bin/bash
# Start the live demo dashboard. Run in WSL2 Ubuntu:  ./dashboard.sh   then open http://localhost:8765 in your browser.
cd "$(dirname "$0")"
source ~/hack-env/bin/activate 2>/dev/null
python gen.py >/dev/null
docker image inspect ps2-node >/dev/null 2>&1 || ./lab.sh build >/dev/null
exec python tools/dashboard.py
