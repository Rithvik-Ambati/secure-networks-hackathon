#!/bin/bash
# One command for the whole before/after demo. Run in WSL2 Ubuntu:  ./demo.sh   (about 4 minutes)
# Re-run a single phase:  ./demo.sh flat | ./demo.sh seg
cd "$(dirname "$0")"
source ~/hack-env/bin/activate 2>/dev/null
mkdir -p results
phase=${1:-all}
CIDR_FLAT=$(python -c "import json;print(json.load(open('generated/addr.json'))['sweep_flat'])" 2>/dev/null)
CIDR_SEG=$(python -c "import json;print(json.load(open('generated/addr.json'))['sweep_seg'])" 2>/dev/null)

if [ "$phase" = all ] || [ "$phase" = flat ]; then
  echo "=== POLICY CHECK (static) ==="
  python tools/lint.py
  echo; echo "=== BEFORE: flat network ==="
  ./lab.sh down; ./lab.sh build >/dev/null; ./lab.sh flat
  bash generated/business.sh flat
  CIDRS="$CIDR_FLAT" bash tests/attack.sh flat
  python tools/verify.py probe flat
  ./lab.sh down
fi

if [ "$phase" = all ] || [ "$phase" = seg ]; then
  echo; echo "=== AFTER: segmented network ==="
  ./lab.sh down; ./lab.sh build >/dev/null; ./lab.sh seg
  bash generated/business.sh seg
  # capture only what the router drops while the attacker runs (nflog group 1)
  docker exec -d ps2-router sh -c 'rm -f /tmp/drops.pcap; tcpdump -l -nn -i nflog:1 -w /tmp/drops.pcap 2>/dev/null'
  sleep 2
  CIDRS="$CIDR_SEG" bash tests/attack.sh seg
  sleep 1; docker exec ps2-router pkill tcpdump; sleep 1
  docker cp ps2-router:/tmp/drops.pcap results/drops.pcap
  python tools/droplog.py results/drops.pcap
  python tools/verify.py probe seg
  bash tests/defense.sh
  bash tests/selftest.sh
fi

if [ "$phase" = all ]; then
  python tools/verify.py plot
  python tools/diagram.py
  python tools/report.py
  echo; echo "Report: results/REPORT.md   Heatmap: results/heatmap.png   Diagram: results/topology.png"
  echo "Lab is still running (segmented). Stop it with ./lab.sh down"
fi
