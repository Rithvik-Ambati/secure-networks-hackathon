#!/usr/bin/env python3
"""Reachability proof harness.
  verify.py probe <flat|seg>   probe every source -> every destination:port from inside the containers
  verify.py plot               draw before/after heatmap + attack-surface numbers (needs both probes)
A connection is a VIOLATION if it is open but not in the policy's flow list, a BREAK if allowed but closed."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

A = json.load(open("generated/addr.json"))
HOSTS = list(A["flat"])
PORTS = A["ports"]
ALLOWED = {tuple(f) for f in A["flows"]}
os.makedirs("results", exist_ok=True)

def probe_one(phase, src):
    ips = A[phase]
    me = ips[src]
    targets = " ".join(f"{h}={ips[h]}" for h in HOSTS if h != src)
    script = (f'for t in {targets}; do h=${{t%%=*}}; ip=${{t##*=}}; '
              f'for p in {" ".join(map(str, PORTS))}; do (nc -z -w1 $ip $p && echo "$h $p") & done; done; wait')
    out = subprocess.run(["docker", "exec", f"ps2-{src}", "bash", "-c", script],
                         capture_output=True, text=True, timeout=120).stdout
    return [(src, l.split()[0], int(l.split()[1])) for l in out.splitlines() if len(l.split()) == 2]

def probe(phase, tag=""):
    with ThreadPoolExecutor(len(HOSTS)) as ex:
        res = [t for r in ex.map(lambda s: probe_one(phase, s), HOSTS) for t in r]
    openset = sorted(set(res))
    viol = sorted(set(openset) - ALLOWED)
    brk = sorted(ALLOWED - set(openset))
    total = len(HOSTS) * (len(HOSTS) - 1) * len(PORTS)
    data = {"phase": phase, "probed": total, "open": openset, "violations": viol, "breaks": brk}
    json.dump(data, open(f"results/{phase}{tag}_matrix.json", "w"), indent=1)
    print(f"[{phase}{tag}] probed {total} host/port pairs: {len(openset)} open, "
          f"{len(viol)} not in policy (violations), {len(brk)} allowed-but-closed (breaks)")
    if phase == "seg":
        ok = not viol and not brk
        print(f"[seg{tag}] PROOF " + ("PASS: exactly the policy is reachable, nothing else" if ok else "FAIL: network does not match the policy"))
        for v in viol: print("   violation:", v)
        for b in brk: print("   break:", b)
    return data

def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    fl = json.load(open("results/flat_matrix.json"))
    sg = json.load(open("results/seg_matrix.json"))
    cols = [(d, p) for d in HOSTS for p in PORTS]
    fig, axes = plt.subplots(2, 1, figsize=(15, 7.5))
    for ax, data, title in ((axes[0], fl, "BEFORE: flat network"), (axes[1], sg, "AFTER: segmented, default deny")):
        openset = {tuple(x) for x in data["open"]}
        grid = []
        for s in HOSTS:
            row = []
            for d, p in cols:
                if s == d: row.append(0)
                else:
                    o = (s, d, p) in openset; al = (s, d, p) in ALLOWED
                    row.append(2 if o and al else 3 if o else 4 if al else 1)
            grid.append(row)
        ax.imshow(grid, cmap=ListedColormap(["#ffffff", "#e6e6e6", "#2e9e5b", "#d93a3a", "#f0a030"]), vmin=0, vmax=4, aspect="auto")
        ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"{d}:{p}" for d, p in cols], rotation=90, fontsize=6)
        ax.set_yticks(range(len(HOSTS))); ax.set_yticklabels(HOSTS)
        nv = len(data["violations"])
        ax.set_title(f"{title}: {len(data['open'])} open of {data['probed']} probed, {nv} unauthorized", fontsize=10, loc="left")
    fig.legend(handles=[Patch(color="#2e9e5b", label="allowed and open"), Patch(color="#d93a3a", label="open but NOT allowed (attack surface)"),
                        Patch(color="#f0a030", label="allowed but closed (broken business flow)"), Patch(color="#e6e6e6", label="blocked")],
               loc="lower center", ncol=4, fontsize=8)
    fig.suptitle("Reachability matrix: rows = source host, columns = destination:port", fontsize=11)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig("results/heatmap.png", dpi=130)
    nf, ns = len(fl["violations"]), len(sg["violations"])
    red = 100.0 * (nf - ns) / nf if nf else 0.0
    summary = {"flat_open": len(fl["open"]), "seg_open": len(sg["open"]), "flat_unauthorized": nf,
               "seg_unauthorized": ns, "attack_surface_reduction_pct": round(red, 1),
               "seg_breaks": len(sg["breaks"])}
    json.dump(summary, open("results/surface.json", "w"), indent=1)
    print(summary)

if __name__ == "__main__":
    if sys.argv[1] == "probe": probe(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif sys.argv[1] == "plot": plot()
