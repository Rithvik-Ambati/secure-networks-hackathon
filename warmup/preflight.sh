#!/usr/bin/env bash
# Guide pre-flight check (run inside WSL2). Uses ~/hack-env for python libs.
source ~/hack-env/bin/activate 2>/dev/null
chk() { command -v "$1" >/dev/null 2>&1 && echo "OK $1" || echo "FAIL $1"; }
for t in docker git python3 pip nmap openssl curl jq tcpdump tshark wg nft; do chk $t; done
docker compose version >/dev/null 2>&1 && echo "OK docker compose" || echo "FAIL docker compose"
docker run --rm hello-world >/dev/null 2>&1 && echo "OK docker run" || echo "FAIL docker run"
python3 -c 'import scapy, pandas; print("OK python libs")' 2>/dev/null || echo "FAIL python libs"
for i in zeek/zeek jasonish/suricata drwetter/testssl.sh; do
  docker image inspect $i >/dev/null 2>&1 && echo "OK image $i" || echo "FAIL image $i"
done
df -h . | tail -1
