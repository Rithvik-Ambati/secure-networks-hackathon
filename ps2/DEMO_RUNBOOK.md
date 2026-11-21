# PS2 demo runbook (5 to 7 minutes)

## Live dashboard (recommended for the demo)
Everything on it is real: each button runs the actual lab, attack, tests and proof, and the router's refused packets stream in as they happen.
```bash
wsl -d Ubuntu
cd /mnt/d/hackathon_prep/ps2
./dashboard.sh        # then open http://localhost:8765 in Chrome or Edge
```
Click in order: 1 Build flat network, 2 Attack, 3 Business flows, 4 Prove reachability, then 5 Segment it and repeat 2, 3, 4. Then 6 Extra defenses and 7 Break it on purpose. The terminal-only version is `./demo_live.sh`.

## Before you go on stage (2 minutes)
1. Start Docker Desktop, wait until it is steady.
2. Open Ubuntu: `wsl -d Ubuntu`, then `cd /mnt/d/hackathon_prep/ps2`.
3. `./lab.sh down` so nothing is left over.
4. Optional rehearsal: `NOPAUSE=1 ./demo_live.sh` (about 4 minutes, proves everything still passes).
5. Open `Flatland_PS2_Deck.pptx` and `results/REPORT.md` in a second window.
6. Backup if the live lab fails: show `results/REPORT.md`, `results/heatmap.png` and the saved outputs in `results/*.txt`.

## Talk track (follow `./demo_live.sh`, press Enter between steps)
| Time | Step | Say |
|---|---|---|
| 0:00 | 0. Policy | "One YAML file lists the 8 business flows. Everything else is generated from it. The static linter finds 0 problems." |
| 0:45 | 1. Flat network | "Six hosts on one network. All 8 business flows pass." |
| 1:30 | 2. Attack | "Same attacker from the workstation: scan, discovery, SSH to the database, SMB, file copy. All 5 succeed. 55 of 180 host/port pairs are reachable, 47 of them not needed." |
| 2:30 | 3. Segmented | "Four zones, one router, default deny, drops logged. The 8 business flows still pass." |
| 3:15 | 3b. Attack again | "Same attack script. All 5 blocked. The router logged 120 drops, mapped to ATT&CK." |
| 4:00 | 4. Proof | "We probe every source against every destination and port from inside the containers. Exactly 8 are open, the 8 in the policy. Nothing else." |
| 4:45 | 5. Negative control | "We break it on purpose. One wrong router rule: the host firewall still blocks it. Add the matching hole on the host: the harness flags it. Restore: proof passes again." |
| 5:30 | 6. Judge variation | "Pick any attack from the workstation." |

## If a judge asks for a variation
| Request | Command |
|---|---|
| Re-run business flows | `bash generated/business.sh seg` |
| Re-run the attack | `CIDRS="10.10.10.0/26 10.10.20.0/26 10.10.30.0/26 10.10.40.0/26" bash tests/attack.sh seg` |
| Any ad-hoc scan | `docker exec ps2-ws nmap -Pn -p 22,445,5432 10.10.30.11` |
| Show the ruleset | `docker exec ps2-router nft list ruleset` |
| Re-run the proof | `python tools/verify.py probe seg` |
| Add or change a flow | edit `policy.yaml`, then `./lab.sh down && ./lab.sh build && ./lab.sh seg` and re-run the business script and proof |
| Show what was dropped | `python tools/droplog.py results/drops.pcap` |

Wait about 10 seconds between repeated SSH-heavy runs: management SSH is rate limited to 20 per minute.

## Likely questions
- **Why did you not use Docker's networks directly?** Docker Desktop's host firewall drops traffic routed between its bridge networks through a container, so we wired the zones with veth links into bridges inside the router container. No path around the router exists.
- **What stops an attacker pivoting through an allowed flow?** Nothing at the network layer. That is why the blast radius table shows what a compromise of each host can reach, and why SSH is rate limited.
- **Why two firewall layers?** Self-test S1: one wrong router rule did not open a hole because the host firewall still blocked it.
- **What does the proof not cover?** TCP only, six ports. UDP and IPv6 are listed as next steps.
- **Are the weak passwords real?** Lab only (`Password123` in the lab image), to make the attacks work.

## If something breaks
- Docker not responding: restart Docker Desktop, then `./lab.sh down` and retry.
- Containers left over: `./lab.sh down`, then `docker ps -a` should be empty.
- A single step fails: skip it and show the saved result in `results/`.
