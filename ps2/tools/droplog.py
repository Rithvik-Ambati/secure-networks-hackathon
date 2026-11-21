#!/usr/bin/env python3
"""Turn the router's dropped-packet capture (nflog) into an ATT&CK-mapped summary.
usage: droplog.py results/drops.pcap"""
import collections, csv, json, subprocess, sys

pcap = sys.argv[1]
A = json.load(open("generated/addr.json"))
name = {ip: h for h, ip in A["seg"].items()}
zone = A["zone_of"]
out = subprocess.run(["tshark", "-r", pcap, "-Y", "ip", "-T", "fields", "-E", "separator=,",
                      "-e", "ip.src", "-e", "ip.dst", "-e", "tcp.dstport", "-e", "udp.dstport"],
                     capture_output=True, text=True).stdout
ev = collections.Counter()
for line in out.splitlines():
    s, d, tp, up = (line.split(",") + ["", "", "", ""])[:4]
    port = tp or up
    if s in name and d in name and port:
        ev[(name[s], name[d], int(port))] += 1

def technique(src, targets):
    t = []
    dsts = {d for d, _ in targets}
    if len(targets) >= 10: t.append("T1046 service discovery")
    if len(dsts) >= 3: t.append("T1018 remote system discovery")
    ports = {p for _, p in targets}
    if 22 in ports: t.append("T1021.004 SSH attempt")
    if 445 in ports: t.append("T1021.002 SMB attempt")
    return ", ".join(t) or "policy violation"

by_src = collections.defaultdict(set)
for (s, d, p) in ev: by_src[s].add((d, p))

rows = sorted(ev.items(), key=lambda kv: -kv[1])
with open("results/drops.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["src", "src_zone", "dst", "dst_zone", "port", "dropped_packets"])
    for (s, d, p), n in rows: w.writerow([s, zone[s], d, zone[d], p, n])

total = sum(ev.values())
md = [f"## Dropped traffic seen at the router ({total} packets, {len(ev)} distinct src/dst/port)", ""]
for s, tg in sorted(by_src.items()):
    n = sum(c for (src, _, _), c in ev.items() if src == s)
    md.append(f"- **{s}** ({zone[s]} zone): {n} dropped packets to {len(tg)} host/port targets. Behaviour: {technique(s, tg)}")
md += ["", "| Source (zone) | Destination (zone) | Port | Dropped packets |", "|---|---|---|---|"]
for (s, d, p), n in rows[:15]:
    md.append(f"| {s} ({zone[s]}) | {d} ({zone[d]}) | {p} | {n} |")
open("results/drops_summary.md", "w").write("\n".join(md) + "\n")
print("\n".join(md[:2 + len(by_src) + 1]))
