#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# Negative control: prove the proof harness really detects holes. Needs the segmented lab running.
# Output lines: S<n>|PASS|FAIL|detail
mkdir -p results; OUT=results/seg_selftest.txt; : > "$OUT"
emit() { echo "$*" | tee -a "$OUT"; }
count() { python -c "import json;d=json.load(open('results/seg_$1_matrix.json'));print(len(d['violations']))"; }

# S1: add ONE wrong rule on the router (ws -> db:5432). The database host firewall must still block it.
docker exec ps2-router nft insert rule inet ps2 forward ip saddr 10.10.10.10 ip daddr 10.10.30.11 tcp dport 5432 ct state new accept
python tools/verify.py probe seg _s1 >/dev/null
v=$(count s1)
[ "$v" = 0 ] && emit "S1|PASS|router had a wrong rule but the db host firewall still blocked it (defense in depth)" \
             || emit "S1|FAIL|wrong router rule created $v unauthorized paths"

# S2: also add the matching hole on the host. Now the network really is wrong; the harness must flag it.
docker exec ps2-db nft insert rule inet hostfw input ip saddr 10.10.10.10 tcp dport 5432 ct state new accept
python tools/verify.py probe seg _s2 >/dev/null
v=$(count s2)
[ "$v" -ge 1 ] && emit "S2|PASS|harness detected the injected hole ($v unauthorized path: ws -> db:5432)" \
               || emit "S2|FAIL|harness missed the injected hole"

# S3: restore the generated rulesets; the proof must pass again.
docker exec ps2-router nft -f /etc/router.nft
docker exec ps2-db nft -f /etc/host.nft
python tools/verify.py probe seg _s3 >/dev/null
v=$(count s3)
[ "$v" = 0 ] && emit "S3|PASS|rulesets restored, proof passes again (0 unauthorized)" \
             || emit "S3|FAIL|still $v unauthorized paths after restore"
