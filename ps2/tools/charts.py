#!/usr/bin/env python3
"""Extra charts for the PDF report -> results/chart_*.png"""
import csv, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

NAVY, TEAL, RED, GREEN, GREY = "#1f2a44", "#128c7e", "#c83232", "#2e9e5b", "#9aa5b4"
S = json.load(open("results/surface.json"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

# 1) before / after bars
fig, ax = plt.subplots(figsize=(9, 3.6))
labels = ["Attack stages that succeed (of 5)", "Reachable paths not needed by the business", "Host/port pairs open (of 180)"]
before = [5, S["flat_unauthorized"], S["flat_open"]]
after = [0, S["seg_unauthorized"], S["seg_open"]]
y = range(len(labels))
ax.barh([i + 0.2 for i in y], before, 0.38, color=RED, label="Flat network (before)")
ax.barh([i - 0.2 for i in y], after, 0.38, color=GREEN, label="Segmented (after)")
for i, (b, a) in enumerate(zip(before, after)):
    ax.text(b + 0.8, i + 0.2, str(b), va="center", fontweight="bold", color=RED)
    ax.text(a + 0.8, i - 0.2, str(a), va="center", fontweight="bold", color=GREEN)
ax.set_yticks(list(y)); ax.set_yticklabels(labels); ax.invert_yaxis()
ax.set_xlim(0, 66); ax.legend(loc="upper right", frameon=False)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_title("Before and after, in numbers", loc="left", fontweight="bold", color=NAVY)
fig.tight_layout(); fig.savefig("results/chart_numbers.png", dpi=150); plt.close(fig)

# 2) what the router dropped, by destination port
rows = list(csv.DictReader(open("results/drops.csv")))
byport = {}
for r in rows: byport[r["port"]] = byport.get(r["port"], 0) + int(r["dropped_packets"])
names = {"22": "22 SSH", "445": "445 SMB", "5432": "5432 database", "8080": "8080 app", "443": "443 HTTPS", "80": "80 HTTP"}
items = sorted(byport.items(), key=lambda kv: -kv[1])
fig, ax = plt.subplots(figsize=(9, 3.2))
ax.bar([names.get(p, p) for p, _ in items], [n for _, n in items], color=TEAL)
for i, (_, n) in enumerate(items): ax.text(i, n + 0.5, str(n), ha="center", fontweight="bold", color=NAVY)
ax.set_ylabel("dropped packets")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_title("What the router refused while the attacker ran (by destination port)", loc="left", fontweight="bold", color=NAVY)
fig.tight_layout(); fig.savefig("results/chart_drops.png", dpi=150); plt.close(fig)

# 3) attack path before / after
def box(ax, x, y, t, c="#ffffff"):
    ax.add_patch(FancyBboxPatch((x - 0.07, y - 0.05), 0.14, 0.10, boxstyle="round,pad=0.005", fc=c, ec=NAVY, lw=1.4))
    ax.text(x, y, t, ha="center", va="center", fontweight="bold", fontsize=10, color=NAVY)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
nodes = {"ws": (0.12, 0.5), "web": (0.45, 0.82), "app": (0.45, 0.5), "db": (0.82, 0.78), "files": (0.82, 0.22)}
for ax, title, ok in ((axes[0], "BEFORE: attacker walks straight in", True), (axes[1], "AFTER: every door is locked", False)):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.set_title(title, fontweight="bold", color=RED if ok else GREEN)
    for n, (x, y) in nodes.items(): box(ax, x, y, n, "#fde8e8" if (ok and n in ("db", "files")) else "#ffffff")
    def arrow(a, b, label, good):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        ax.annotate("", xy=(x2 - 0.07 * (x2 > x1) + 0.07 * (x2 < x1), y2), xytext=(x1 + 0.07 * (x2 > x1) - 0.07 * (x2 < x1), y1),
                    arrowprops=dict(arrowstyle="->", lw=2, color=good, ls="-" if good == RED or good == GREEN else "--"))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.04, label, ha="center", fontsize=9, color=good, bbox=dict(fc="white", ec="none", pad=0.5))
    if ok:
        arrow("ws", "web", "scan", RED); arrow("ws", "db", "SSH login", RED); arrow("ws", "files", "SMB + file copy", RED)
    else:
        arrow("ws", "web", "HTTPS only (allowed)", GREEN)
        for lbl, t in (("SSH login", "db"), ("SMB + copy", "files")):
            (x1, y1), (x2, y2) = nodes["ws"], nodes[t]
            ax.plot([x1 + 0.07, x2 - 0.07], [y1, y2], color=GREY, ls="--", lw=1.6)
            mx, my = (x1 + x2) / 2 + 0.05, (y1 + y2) / 2
            ax.text(mx, my, "X " + lbl, ha="center", fontsize=9, color=RED, fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.5))
fig.tight_layout(); fig.savefig("results/chart_path.png", dpi=150); plt.close(fig)
print("wrote results/chart_numbers.png, chart_drops.png, chart_path.png")
