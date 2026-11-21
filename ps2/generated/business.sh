#!/bin/bash
# GENERATED from policy.yaml. Runs every legitimate business flow.
# Output lines: <id>|PASS|FAIL|<description>
PHASE=${1:-flat}
mkdir -p results; OUT=results/${PHASE}_business.txt; : > "$OUT"
emit() { echo "$*" | tee -a "$OUT"; }
t() { id=$1; desc=$2; expect=$3; shift 3; out=$("$@" 2>&1); if echo "$out" | grep -q "$expect"; then emit "$id|PASS|$desc"; else emit "$id|FAIL|$desc"; fi; }
t F1 'ws -> web:443 Users reach the web portal over HTTPS' 200 docker exec ps2-ws curl -sk -m5 -o /dev/null -w '%{http_code}' https://web/
t F2 'web -> app:8080 Web tier calls the app API' 'app ok db=up' docker exec ps2-web curl -s -m5 http://app:8080/health
t F3 'app -> db:5432 App reads and writes the database' open docker exec ps2-app sh -c 'nc -z -w3 db 5432 && echo open'
t F4 'app -> files:445 App stores documents on the file server' secret.txt docker exec ps2-app timeout 10 smbclient -N //files/public -c ls
t F5 'jump -> web:22 Admin SSH to web' SSH-OK docker exec -u admin ps2-jump ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 admin@web echo SSH-OK
t F6 'jump -> app:22 Admin SSH to app' SSH-OK docker exec -u admin ps2-jump ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 admin@app echo SSH-OK
t F7 'jump -> db:22 Admin SSH to database' SSH-OK docker exec -u admin ps2-jump ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 admin@db echo SSH-OK
t F8 'jump -> files:22 Admin SSH to file server' SSH-OK docker exec -u admin ps2-jump ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 admin@files echo SSH-OK
