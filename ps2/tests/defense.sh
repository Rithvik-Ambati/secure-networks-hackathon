#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# Extra defense checks on the segmented lab. PASS = the defense works.
mkdir -p results; OUT=results/seg_defense.txt; : > "$OUT"
emit() { echo "$*" | tee -a "$OUT"; }

# E1: egress filtering on the database host: it may not start outbound connections (callback to attacker)
out=$(docker exec ps2-db sh -c 'nc -z -w2 10.10.10.10 4444 && echo CONNECTED' 2>&1)
if echo "$out" | grep -q CONNECTED; then emit "E1|FAIL|db host opened an outbound connection to the user zone"
else emit "E1|PASS|db host cannot call out (host egress filter)"; fi

# E2: egress filtering at the router: server zone may not start connections into the user zone
out=$(docker exec ps2-app sh -c 'nc -z -w2 10.10.10.10 4444 && echo CONNECTED' 2>&1)
if echo "$out" | grep -q CONNECTED; then emit "E2|FAIL|app server opened a connection into the user zone"
else emit "E2|PASS|server-to-user connection blocked at the router"; fi

# E3: micro-segmentation: another server-zone host cannot reach the database directly
out=$(docker exec ps2-files sh -c 'nc -z -w2 db 5432 && echo CONNECTED' 2>&1)
if echo "$out" | grep -q CONNECTED; then emit "E3|FAIL|file server reached the database on 5432"
else emit "E3|PASS|only the app can reach db:5432 (host micro-segmentation)"; fi

# E5: no lateral movement inside a zone: the file server cannot SSH to the app server
out=$(docker exec ps2-files sh -c 'nc -z -w2 app 22 && echo CONNECTED' 2>&1)
if echo "$out" | grep -q CONNECTED; then emit "E5|FAIL|file server reached the app server on 22 (same zone)"
else emit "E5|PASS|same-zone lateral movement blocked (files cannot reach app:22)"; fi

# E4: rate limiting: 60 parallel SSH connection attempts from the jump host; the limiter must cut most of them
ok=$(docker exec ps2-jump sh -c 'for i in $(seq 1 60); do (nc -z -w1 db 22 2>/dev/null && echo y) & done; wait' 2>/dev/null | grep -c y)
if [ "$ok" -ge 1 ] && [ "$ok" -lt 60 ]; then emit "E4|PASS|SSH rate limit: only $ok of 60 rapid attempts got through"
else emit "E4|FAIL|SSH rate limit ineffective ($ok of 60 got through)"; fi
sleep 8   # let the rate limiter refill before anyone re-runs the business script
