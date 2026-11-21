# Secure Networks Hackathon: PS2 "Flatland"

**Network segmentation and firewall design.** A flat company network lets an attacker who owns one workstation reach the database in minutes.
We prove the attack works, rebuild the network into zones behind a default-deny router, and prove the attack fails while every business flow still works.

**Idea:** one file (`ps2/policy.yaml`) lists the 8 allowed business flows. A generator turns it into the router firewall, host firewalls, lab setup and tests,
and a proof harness checks all 180 source/destination/port combinations against the policy.

| Result | Flat network | Segmented |
|---|---|---|
| Attack stages that succeed (scan, discovery, SSH, SMB, file copy) | 5 of 5 | 0 of 5 |
| Business flows that pass | 8 of 8 | 8 of 8 |
| Host/port pairs open (of 180) | 55 | 8 (exactly the policy) |
| Open but not needed by the business | 47 | 0 |

## Read first
- [`Flatland_PS2_Report.pdf`](Flatland_PS2_Report.pdf): illustrated, plain-language report with the real outputs.
- [`ps2/Flatland_PS2_Deck.pptx`](ps2/Flatland_PS2_Deck.pptx): presentation slides (PDF copy alongside).
- [`ps2/DEMO_RUNBOOK.md`](ps2/DEMO_RUNBOOK.md): talk track and judge-variation commands.

## Run the live demo (Windows with WSL2 Ubuntu and Docker Desktop)
```bash
cd ps2
./dashboard.sh        # live dashboard on http://localhost:8765 (every button runs the real lab)
./demo_live.sh        # same story in the terminal, press Enter between steps
```
Details are in [`ps2/README.md`](ps2/README.md). Warm-up lab and pre-flight script are in `warmup/`, cheat sheets in `notes/`.

## Contributors
- [@Rithvik-Ambati](https://github.com/Rithvik-Ambati)
- [@akshayy06](https://github.com/akshayy06)
- [@shashiiiiii45](https://github.com/shashiiiiii45)
- [@Abhichakra123](https://github.com/Abhichakra123)

## Safety
Attacks run only against containers on the local lab. Weak credentials (`Password123`) exist only inside the lab image on purpose.
