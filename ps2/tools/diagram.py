#!/usr/bin/env python3
"""Draw the segmented network diagram from policy.yaml / generated/addr.json -> results/topology.png"""
import json, yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

P = yaml.safe_load(open("policy.yaml"))
A = json.load(open("generated/addr.json"))
zone_box = {"user": (0.03, 0.58, 0.28, 0.34), "dmz": (0.69, 0.58, 0.28, 0.34),
            "mgmt": (0.03, 0.06, 0.28, 0.34), "server": (0.52, 0.06, 0.45, 0.34)}
color = {"user": "#dbe9fb", "dmz": "#fde9c9", "mgmt": "#e5dbf5", "server": "#d8f0df"}
fig, ax = plt.subplots(figsize=(13, 7.5)); ax.set_xlim(0, 1); ax.set_ylim(-0.32, 1); ax.axis("off")
pos = {}
for z, (x, y, w, h) in zone_box.items():
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.005,rounding_size=0.02", fc=color[z], ec="#555", lw=1.2))
    ax.text(x + 0.01, y + h - 0.035, f"{z.upper()} zone  {P['zones'][z]['subnet']}", fontsize=10, weight="bold")
    hs = list(P["zones"][z]["hosts"])
    for i, hname in enumerate(hs):
        cx = x + w * (i + 0.5) / len(hs); cy = y + h * 0.38
        ax.add_patch(FancyBboxPatch((cx - 0.055, cy - 0.06), 0.11, 0.12, boxstyle="round,pad=0.004", fc="white", ec="#333"))
        ax.text(cx, cy + 0.02, hname, ha="center", fontsize=10, weight="bold")
        ax.text(cx, cy - 0.025, A["seg"][hname], ha="center", fontsize=8)
        pos[hname] = (cx, cy)
ax.add_patch(FancyBboxPatch((0.42, 0.42), 0.16, 0.16, boxstyle="round,pad=0.005", fc="#ffd9d9", ec="#a00", lw=2))
ax.text(0.5, 0.52, "ROUTER", ha="center", weight="bold", fontsize=11)
ax.text(0.5, 0.47, "nftables\ndefault deny + log", ha="center", fontsize=8)
# zone <-> router links
for z, (x, y, w, h) in zone_box.items():
    cx, cy = x + w / 2, y + h / 2
    tx = 0.42 if cx < 0.5 else 0.58
    ty = 0.5 + (0.05 if cy > 0.5 else -0.05)
    ex = x + w if cx < 0.5 else x
    ey = y if cy > 0.5 else y + h
    ax.plot([ex, tx], [ey, ty], color="#a00", lw=2.2, solid_capstyle="round")
ax.text(0.5, -0.04, "Allowed flows (default deny for everything else, drops are logged)", ha="center", fontsize=10, weight="bold")
for i, f in enumerate(P["flows"]):
    col, row = divmod(i, 4)
    z1, z2 = A["zone_of"][f["src"]], A["zone_of"][f["dst"]]
    rate = f"  [{f['rate']}]" if f.get("rate") else ""
    ax.text(0.04 + col * 0.50, -0.09 - row * 0.05,
            f"{f['id']}  {f['src']} ({z1}) -> {f['dst']} ({z2})  {f['port']}/tcp{rate}", fontsize=9, family="monospace")
ax.text(0.5, 0.97, "Segmented network: four zones joined only by the router",
        ha="center", fontsize=11, weight="bold")
fig.savefig("results/topology.png", dpi=130, bbox_inches="tight")
print("wrote results/topology.png")
