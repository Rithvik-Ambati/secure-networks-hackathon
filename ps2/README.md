# PS2 Flatland: policy-as-code segmentation with a proof harness

## Run it (inside WSL2 Ubuntu, Docker Desktop running)
```bash
wsl -d Ubuntu
cd /mnt/d/hackathon_prep/ps2
./demo.sh          # whole before/after demo, about 4 minutes, writes results/REPORT.md
./demo.sh flat     # only the flat network (before)
./demo.sh seg      # only the segmented network (after)
./lab.sh down      # stop everything
```

## Live demo dashboard
`./dashboard.sh` then open http://localhost:8765. Every button runs the real lab (nothing pre-recorded) and router drops stream live.
The illustrated report is `results/Flatland_PS2_Report.pdf` (rebuild: `python tools/make_pdf.py` then `powershell -File tools/make_pdf.ps1`).

## What it shows
1. **Before (flat):** six containers on one network. Attack stages A1 to A5 all succeed and the 8 business flows pass.
2. **After (segmented):** four zones (user, DMZ, server, management) joined only by a router container with a default-deny nftables ruleset. All attack stages are BLOCKED and all 8 business flows still PASS.
3. **Proof:** `tools/verify.py` probes 180 source/destination/port pairs from inside the containers: 55 open before, exactly the 8 policy flows after, 0 unauthorized.
4. **Extras:** egress filtering, database host micro-segmentation, SSH rate limiting, dropped-traffic log mapped to ATT&CK.

## The novel part (say this in the demo)
`policy.yaml` is the single source of truth. `gen.py` generates the compose files, router ruleset, database firewall,
business test script and the flow table from it. Change one flow, re-run, and the proof harness tells you whether
the network matches the policy. Nothing is hand-edited.

## Files
| File | Purpose |
|---|---|
| policy.yaml | zones, addressing, business flows, ATT&CK mapping (edit this) |
| gen.py | generates everything into generated/ |
| lab.sh | build, flat, seg (wires veth links into the router), down |
| tests/attack.sh | attacker script: scan, discovery, SSH, SMB, file copy |
| generated/business.sh | the 8 legitimate flows (generated) |
| tests/defense.sh | egress, micro-segmentation and rate-limit checks |
| tools/verify.py | reachability proof and heatmap |
| tools/droplog.py | router drop capture to ATT&CK summary |
| results/ | REPORT.md, heatmap.png, topology.png, before/after outputs, drops.pcap |
| generated/flows.md | addressing plan, zones and data-flow table |
| generated/router.nft | the ruleset deliverable |

## Judge variations (quick commands)
```bash
./lab.sh seg                                  # if the lab is down
bash generated/business.sh seg                # all business flows
CIDRS="10.10.10.0/26 10.10.20.0/26 10.10.30.0/26 10.10.40.0/26" bash tests/attack.sh seg
python tools/verify.py probe seg              # proof: only policy flows reachable
docker exec ps2-router nft list ruleset       # show the ruleset
docker exec ps2-ws nmap -Pn -p 22,445,5432 10.10.30.11   # any ad-hoc attack from the workstation
```
Wait about 10 seconds between repeated SSH-heavy runs: the jump host SSH flows are rate limited (20/minute).

## Notes
- The segmented lab uses `network_mode: none` and lab.sh builds the veth links itself, because Docker Desktop's host firewall
  silently drops traffic routed between its bridge networks through a container.
- Weak credentials (`Password123`) exist only in the lab image on purpose, to make the attacks work.
- Report section 7 lists limits (TCP-only probing, intra-zone traffic).
