#!/usr/bin/env python3
"""Static policy analysis (no containers needed): lint the flow list and compute worst-case blast radius.
usage: lint.py   -> prints results and writes results/lint.txt and results/blast.csv"""
import collections, csv, os, yaml

P = yaml.safe_load(open("policy.yaml"))
os.makedirs("results", exist_ok=True)
zone_of = {h: z for z, d in P["zones"].items() for h in d["hosts"]}
flows = P["flows"]
warn, err = [], []

seen = set()
for f in flows:
    i = f["id"]
    bad = False
    for k in ("src", "dst"):
        if f[k] not in zone_of:
            err.append(f"{i}: unknown host {f[k]}"); bad = True
    if bad: continue
    key = (f["src"], f["dst"], f["port"])
    if key in seen: warn.append(f"{i}: duplicate flow {key}")
    seen.add(key)
    zs, zd = zone_of[f["src"]], zone_of[f["dst"]]
    if zs == "user" and zd == "server": warn.append(f"{i}: user zone talks straight into the server zone (should go through the DMZ)")
    if zd == "mgmt" and zs != "mgmt": warn.append(f"{i}: traffic INTO the management zone from {zs}")
    if f["port"] == 22 and not f.get("rate"): warn.append(f"{i}: SSH flow without a rate limit")
    if f["dst"] == "db" and f["src"] != "app" and f["port"] == 5432: warn.append(f"{i}: database port reachable from {f['src']}, not only the app")
    if f["port"] in (23, 21, 69, 3389): warn.append(f"{i}: risky port {f['port']}")

# worst-case blast radius: if host X is fully compromised, which hosts can it reach by chaining allowed flows?
adj = collections.defaultdict(list)
for f in flows:
    if f["src"] in zone_of and f["dst"] in zone_of: adj[f["src"]].append(f["dst"])
hosts = list(zone_of)
rows = []
for start in hosts:
    depth, q = {start: 0}, collections.deque([start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in depth: depth[v] = depth[u] + 1; q.append(v)
    reach = {h: d for h, d in depth.items() if h != start}
    rows.append((start, sorted(h for h, d in reach.items() if d == 1), sorted(reach)))

lines = [f"Policy lint: {len(flows)} flows, {len(err)} errors, {len(warn)} warnings"]
lines += [f"  ERROR {e}" for e in err] + [f"  WARN  {w}" for w in warn]
lines += ["", "Worst-case blast radius if one host is fully compromised",
          f"{'host':6} {'flat network':14} {'segmented, direct':22} segmented, by pivoting through allowed flows"]
with open("results/blast.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["host", "flat_reach", "seg_direct", "seg_pivot"])
    for h, direct, reach in rows:
        lines.append(f"{h:6} {len(hosts)-1} of {len(hosts)-1:<9} {','.join(direct) or '-':22} {','.join(reach) or '-'}")
        w.writerow([h, len(hosts) - 1, len(direct), len(reach)])
open("results/lint.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
raise SystemExit(1 if err else 0)
