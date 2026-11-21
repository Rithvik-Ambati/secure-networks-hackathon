#!/usr/bin/env python3
"""Assemble results/REPORT.md from the saved run outputs."""
import json, os, yaml

P = yaml.safe_load(open("policy.yaml"))
R = "results"

def load(name):
    rows = {}
    path = os.path.join(R, name)
    if os.path.exists(path):
        for line in open(path):
            parts = line.rstrip("\n").split("|", 2)
            if len(parts) == 3: rows[parts[0]] = (parts[1], parts[2])
    return rows

fa, sa = load("flat_attack.txt"), load("seg_attack.txt")
fb, sb = load("flat_business.txt"), load("seg_business.txt")
sd = load("seg_defense.txt")
st = load("seg_selftest.txt")
lint = open(f"{R}/lint.txt").read() if os.path.exists(f"{R}/lint.txt") else ""
surf = json.load(open(f"{R}/surface.json")) if os.path.exists(f"{R}/surface.json") else {}
drops = open(f"{R}/drops_summary.md").read() if os.path.exists(f"{R}/drops_summary.md") else ""

L = ["# PS2 Flatland: results report", "",
     "Approach: **policy-as-code with a proof harness.** One file (`policy.yaml`) lists the business flows. "
     "`gen.py` generates the segmented compose file, the router's default-deny nftables ruleset, the host "
     "firewall, the business test script and the design tables. `tools/verify.py` then probes every source against "
     "every destination and port from inside the containers and checks the result against the policy.", "",
     "## 1. Attack results (run from the workstation)", "",
     "| Stage | Behaviour | ATT&CK | Flat network | Segmented network |", "|---|---|---|---|---|"]
for k, m in P["attack_map"].items():
    L.append(f"| {k} | {m['name']} | {m['technique']} | {fa.get(k, ('-',))[0]} | {sa.get(k, ('-',))[0]} |")
L += ["", "SUCCESS = attacker wins. BLOCKED = defense works. Detail from the flat run:", ""]
for k in P["attack_map"]:
    if k in fa: L.append(f"- {k}: {fa[k][1]}")
L += ["", "## 2. Business flows (must pass in both networks)", "",
      "| ID | Flow | Flat | Segmented |", "|---|---|---|---|"]
for f in P["flows"]:
    i = f["id"]
    L.append(f"| {i} | {f['src']} to {f['dst']}:{f['port']} ({f['desc']}) | {fb.get(i, ('-',))[0]} | {sb.get(i, ('-',))[0]} |")
npass = sum(1 for v in sb.values() if v[0] == "PASS")
L += ["", f"Segmented: {npass} of {len(P['flows'])} business flows pass.", "",
      "## 3. Reachability proof", "",
      f"- Flat network: **{surf.get('flat_open', '?')}** host/port pairs open, **{surf.get('flat_unauthorized', '?')}** not in the policy.",
      f"- Segmented: **{surf.get('seg_open', '?')}** open (exactly the policy flows), **{surf.get('seg_unauthorized', '?')}** unauthorized, "
      f"{surf.get('seg_breaks', '?')} business flows broken.",
      f"- **Attack surface reduction: {surf.get('attack_surface_reduction_pct', '?')}%** (unauthorized reachable pairs).", "",
      "![heatmap](heatmap.png)", "",
      "## 4. Network design", "", "![topology](topology.png)", "",
      "See `generated/flows.md` for the addressing plan, zones and data-flow table.", "",
      "## 5. Extra defenses (stretch goals)", "",
      "| Check | Result | Detail |", "|---|---|---|"]
for k, (state, detail) in sd.items():
    L.append(f"| {k} | {state} | {detail} |")
L += ["", "## 5b. Negative control: does the proof harness really catch holes?", "",
      "| Step | Result | Detail |", "|---|---|---|"]
for k, (state, detail) in st.items():
    L.append(f"| {k} | {state} | {detail} |")
L += ["", "## 5c. Static policy check and blast radius", "", "```", lint.rstrip(), "```", "",
      "Blast radius assumes the attacker fully controls the host and chains the allowed flows. "
      "In the flat network any host reaches every other host directly.", ""]
L += ["", drops, "",
      "## 6. MITRE mapping", "",
      "| Stage | Technique | D3FEND | Mitigation |", "|---|---|---|---|"]
for k, m in P["attack_map"].items():
    L.append(f"| {k} {m['name']} | {m['technique']} | {m['d3fend']} | {m['mitigation']} |")
L += ["", "## 7. Limits and known evasions", "",
      "- The proof harness probes TCP on six ports. UDP and ICMP are not probed; the router drops everything not listed, but this was not measured.",
      "- Same-zone traffic: on this Docker Desktop kernel it also passes the router's forward chain (br_netfilter), and the probe confirms it is blocked. "
      "To avoid depending on that kernel setting, every host also has its own default-deny input firewall (check E5 and self-test S1 show both layers).",
      "- Allowed flows can still be abused (for example SSH from the jump host), which is why they are rate limited.",
      "- Test credentials (`Password123`) are deliberately weak and exist only in the lab image.", ""]
open(f"{R}/REPORT.md", "w").write("\n".join(L))
print("wrote results/REPORT.md")
