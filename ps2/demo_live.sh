#!/bin/bash
# Step-by-step live demo (about 6 minutes). Run in WSL2 Ubuntu:  ./demo_live.sh
# Press Enter between steps. NOPAUSE=1 ./demo_live.sh runs straight through (for rehearsal).
cd "$(dirname "$0")"
source ~/hack-env/bin/activate 2>/dev/null
mkdir -p results
pause() { [ -n "$NOPAUSE" ] || read -r -p $'\n--- press Enter for the next step ---'; echo; }
say()   { echo; echo "######## $*"; }
SWEEP_FLAT=$(python -c "import json;print(json.load(open('generated/addr.json'))['sweep_flat'])")
SWEEP_SEG=$(python -c "import json;print(json.load(open('generated/addr.json'))['sweep_seg'])")

say "STEP 0: the policy (single source of truth) and the static check"
python gen.py >/dev/null; sed -n '1,40p' policy.yaml; python tools/lint.py
pause

say "STEP 1: BEFORE. Flat network: bring it up"
./lab.sh down >/dev/null 2>&1; ./lab.sh build >/dev/null; ./lab.sh flat >/dev/null 2>&1
say "Business flows (should all PASS)"; bash generated/business.sh flat
pause
say "STEP 2: the attacker runs from the workstation. SUCCESS means the attacker wins"
CIDRS="$SWEEP_FLAT" bash tests/attack.sh flat
python tools/verify.py probe flat
pause

say "STEP 3: AFTER. Segmented network: four zones, router, default deny"
./lab.sh down >/dev/null 2>&1; ./lab.sh seg >/dev/null 2>&1
docker exec ps2-router nft list chain inet ps2 forward | head -14
pause
say "Same business flows (should all PASS)"; bash generated/business.sh seg
pause
say "Same attack. BLOCKED means the defense works"
docker exec -d ps2-router sh -c 'rm -f /tmp/drops.pcap; tcpdump -l -nn -i nflog:1 -w /tmp/drops.pcap 2>/dev/null'; sleep 2
CIDRS="$SWEEP_SEG" bash tests/attack.sh seg
sleep 1; docker exec ps2-router pkill tcpdump; sleep 1
docker cp ps2-router:/tmp/drops.pcap results/drops.pcap >/dev/null; python tools/droplog.py results/drops.pcap | head -4
pause

say "STEP 4: the proof. Every source against every destination and port"
python tools/verify.py probe seg
bash tests/defense.sh
pause

say "STEP 5: can you trust the tester? Break the network on purpose"
bash tests/selftest.sh
pause

say "STEP 6: judge variation. Try any ad-hoc attack from the workstation, for example:"
echo "  docker exec ps2-ws nmap -Pn -p 22,445,5432 10.10.30.11"
docker exec ps2-ws nmap -Pn -n -p 22,445,5432 --max-retries 1 10.10.30.11 | tail -6
echo; echo "Report: results/REPORT.md   Slides: Flatland_PS2_Deck.pptx"
echo "Stop the lab with ./lab.sh down"
