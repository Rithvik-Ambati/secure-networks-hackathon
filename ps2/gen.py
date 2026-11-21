#!/usr/bin/env python3
"""Policy-as-code generator: policy.yaml -> compose files, router ruleset, host firewall,
business test script, flow matrix and addressing plan. Run: python3 gen.py"""
import os, shlex
from ipaddress import ip_network
import yaml

P = yaml.safe_load(open("policy.yaml"))
OUT = "generated"
os.makedirs(OUT, exist_ok=True)
flows, roles = P["flows"], P["roles"]
hosts = list(roles)

# ---------- addressing ----------
flat_net = ip_network(P["flat"]["subnet"])
flat_ip = {h: str(flat_net.network_address + o) for h, o in P["flat"]["hosts"].items()}
zone_of, seg_ip, zone_net, router_ip = {}, {}, {}, {}
for z, d in P["zones"].items():
    net = ip_network(d["subnet"])
    zone_net[z] = net
    router_ip[z] = str(net.network_address + P["router_host"])
    for h, o in d["hosts"].items():
        zone_of[h] = z
        seg_ip[h] = str(net.network_address + o)

def write(name, text, mode=None):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="\n") as f:
        f.write(text)
    if mode:
        os.chmod(path, mode)

# ---------- compose: flat ----------
def service(h, ips, net, extra=None):
    s = {
        "image": "ps2-node",
        "container_name": f"ps2-{h}",
        "hostname": h,
        "environment": {"ROLE": roles[h]},
        "cap_add": ["NET_ADMIN"],
        "extra_hosts": [f"{o}:{ips[o]}" for o in hosts if o != h],
        "networks": {net: {"ipv4_address": ips[h]}},
    }
    s["environment"].update((extra or {}).pop("environment", {}))
    s.update(extra or {})
    return s

flat = {"name": "ps2flat",
        "services": {h: service(h, flat_ip, "flat") for h in hosts},
        "networks": {"flat": {"internal": True, "ipam": {"config": [{"subnet": P["flat"]["subnet"]}]}}}}
write("compose.flat.yml", yaml.safe_dump(flat, sort_keys=False))

# ---------- compose: segmented ----------
# Docker's own bridge isolation drops traffic that is routed between its networks through a container,
# so the segmented lab uses network_mode none and lab.sh wires real veth links: every host gets one
# link into a per-zone bridge that lives INSIDE the router container. No other path exists.
seg = {"name": "ps2seg", "services": {}}
microseg = P.get("microseg", hosts)          # every host gets its own default-deny input firewall
egress_deny = P.get("egress_deny", ["db"])   # hosts that may not start outbound connections
hostsenv = ",".join(f"{o}={seg_ip[o]}" for o in hosts)
for h in hosts:
    s = {"image": "ps2-node", "container_name": f"ps2-{h}", "hostname": h, "network_mode": "none",
         "environment": {"ROLE": roles[h], "HOSTS": hostsenv}, "cap_add": ["NET_ADMIN"]}
    if h in microseg:
        s["volumes"] = [f"./{h}.nft:/etc/host.nft:ro"]
    seg["services"][h] = s
seg["services"]["router"] = {
    "image": "ps2-node", "container_name": "ps2-router", "hostname": "router", "network_mode": "none",
    "environment": {"ROLE": "router"}, "cap_add": ["NET_ADMIN"],
    "sysctls": {"net.ipv4.ip_forward": 1},
    "volumes": ["./router.nft:/etc/router.nft:ro"],
}
write("compose.seg.yml", yaml.safe_dump(seg, sort_keys=False))

w = ["#!/bin/sh", "# GENERATED. Runs in a privileged helper container; needs PID_<name> env vars (container PIDs).", "set -e",
     'R="nsenter -t $PID_router -n"']
for z, net in zone_net.items():
    w.append(f"$R sh -c 'ip link add br-{z} type bridge && ip addr add {router_ip[z]}/{net.prefixlen} dev br-{z} && ip link set br-{z} up'")
for h in hosts:
    z = zone_of[h]
    net = zone_net[z]
    routes = " && ".join(f"ip route add {zone_net[o]} via {router_ip[z]}" for o in zone_net if o != z)
    w += [f"ip link del v-{h} 2>/dev/null || true",
          f"ip link add v-{h} type veth peer name p-{h}",
          f"ip link set v-{h} netns $PID_{h} name eth0",
          f"ip link set p-{h} netns $PID_router",
          f"$R sh -c 'ip link set p-{h} master br-{z} && ip link set p-{h} up'",
          f"nsenter -t $PID_{h} -n sh -c 'ip link set lo up && ip addr add {seg_ip[h]}/{net.prefixlen} dev eth0 && ip link set eth0 up && {routes}'"]
w.append('echo "wired $(echo $PID_router | wc -l) router and %d hosts"' % len(hosts))
write("wire.sh", "\n".join(w) + "\n")

# ---------- router ruleset (default deny + logging) ----------
r = ["flush ruleset", "", "table inet ps2 {",
     "  chain input {",
     "    type filter hook input priority 0; policy drop;",
     "    ct state established,related accept",
     "    iif lo accept",
     "  }",
     "  chain forward {",
     "    type filter hook forward priority 0; policy drop;",
     "    ct state invalid drop",
     "    ct state established,related accept"]
for f in flows:
    rate = f" limit rate {f['rate']} burst 20 packets" if f.get("rate") else ""
    r.append(f'    ip saddr {seg_ip[f["src"]]} ip daddr {seg_ip[f["dst"]]} tcp dport {f["port"]} ct state new{rate} accept comment "{f["id"]} {f["src"]}->{f["dst"]}:{f["port"]}"')
r.append("    # log what is dropped, per source zone (read with: tcpdump -i nflog:1)")
for z, net in zone_net.items():
    r.append(f'    ip saddr {net} limit rate 100/second burst 200 packets log prefix "PS2-DROP zone={z} " group 1')
    r.append(f'    ip saddr {net} limit rate 100/second burst 200 packets log prefix "PS2-DROP zone={z} " group 2  # live dashboard feed')
r += ["    counter drop", "  }", "  chain output { type filter hook output priority 0; policy accept; }", "}", ""]
write("router.nft", "\n".join(r))

# ---------- host micro-segmentation (database) ----------
for h in microseg:
    n = ["flush ruleset", "", "table inet hostfw {",
         "  chain input {",
         "    type filter hook input priority 0; policy drop;",
         "    iif lo accept",
         "    ct state established,related accept"]
    for f in flows:
        if f["dst"] == h:
            rate = f" limit rate {f['rate']} burst 20 packets" if f.get("rate") else ""
            n.append(f'    ip saddr {seg_ip[f["src"]]} tcp dport {f["port"]} ct state new{rate} accept comment "{f["id"]}"')
    n += ["    counter drop", "  }"]
    if h in egress_deny:
        n += ["  chain output {",
              "    type filter hook output priority 0; policy drop;",
              "    oif lo accept",
              "    ct state established,related accept",
              "    counter drop  # egress filtering: no outbound callbacks from this host",
              "  }"]
    else:
        n += ["  chain output { type filter hook output priority 0; policy accept; }"]
    n += ["}", ""]
    write(f"{h}.nft", "\n".join(n))

# ---------- business test script ----------
def test_cmd(f):
    s, d, p = f["src"], f["dst"], f["port"]
    if p == 443:
        return ["docker", "exec", f"ps2-{s}", "curl", "-sk", "-m5", "-o", "/dev/null", "-w", "%{http_code}", f"https://{d}/"], "200"
    if p == 8080:
        return ["docker", "exec", f"ps2-{s}", "curl", "-s", "-m5", f"http://{d}:8080/health"], "app ok db=up"
    if p == 5432:
        return ["docker", "exec", f"ps2-{s}", "sh", "-c", f"nc -z -w3 {d} 5432 && echo open"], "open"
    if p == 445:
        return ["docker", "exec", f"ps2-{s}", "timeout", "10", "smbclient", "-N", f"//{d}/public", "-c", "ls"], "secret.txt"
    if p == 22:
        return ["docker", "exec", "-u", "admin", f"ps2-{s}", "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=3", f"admin@{d}", "echo", "SSH-OK"], "SSH-OK"
    raise SystemExit(f"no test for port {p}")

b = ["#!/bin/bash", "# GENERATED from policy.yaml. Runs every legitimate business flow.",
     "# Output lines: <id>|PASS|FAIL|<description>",
     'PHASE=${1:-flat}', 'mkdir -p results; OUT=results/${PHASE}_business.txt; : > "$OUT"',
     'emit() { echo "$*" | tee -a "$OUT"; }',
     't() { id=$1; desc=$2; expect=$3; shift 3; out=$("$@" 2>&1); '
     'if echo "$out" | grep -q "$expect"; then emit "$id|PASS|$desc"; else emit "$id|FAIL|$desc"; fi; }']
for f in flows:
    cmd, expect = test_cmd(f)
    desc = f'{f["src"]} -> {f["dst"]}:{f["port"]} {f["desc"]}'
    b.append(f"t {f['id']} {shlex.quote(desc)} {shlex.quote(expect)} {shlex.join(cmd)}")
write("business.sh", "\n".join(b) + "\n", 0o755)

# ---------- flow matrix / addressing plan ----------
def zn(h): return zone_of[h]
md = ["# PS2 design: addressing plan, zones and flow matrix", "",
      "_Generated from `policy.yaml` by `gen.py`. Edit the policy, not this file._", "",
      "## Security zones and addressing plan", "",
      "| Zone | Subnet | Router interface | Hosts |", "|---|---|---|---|"]
for z, net in zone_net.items():
    hs = ", ".join(f"{h} ({seg_ip[h]})" for h in hosts if zone_of[h] == z)
    md.append(f"| {z} | {net} | {router_ip[z]} | {hs} |")
md += ["", "Flat (before) network: " + P["flat"]["subnet"] + " with " + ", ".join(f"{h} {flat_ip[h]}" for h in hosts), "",
       "## Data-flow table (the only allowed traffic)", "",
       "| ID | From | Zone | To | Zone | Port/proto | Rate limit | Purpose |", "|---|---|---|---|---|---|---|---|"]
for f in flows:
    md.append(f"| {f['id']} | {f['src']} | {zn(f['src'])} | {f['dst']} | {zn(f['dst'])} | {f['port']}/tcp | {f.get('rate','-')} | {f['desc']} |")
md += ["", "Everything else is dropped by default and logged (`PS2-DROP zone=...`).", "",
       "## Controls", "",
       "- Zones on separate Docker networks, joined only by the router container (no direct path).",
       "- Router `forward` chain: default deny, stateful (established/related), one rule per flow.",
       "- Management SSH rate limited at the router and on the database host.",
       "- Host micro-segmentation on every host (second layer): each host only accepts the flows listed for it, so one wrong router rule cannot open a hole.",
       "- Egress filtering: the database host may not start outbound connections; the router drops any server-to-user or server-to-DMZ start of a connection.",
       "- Dropped traffic is logged per source zone and mapped to ATT&CK by `tools/droplog.py`.", ""]
write("flows.md", "\n".join(md))
import json
write("addr.json", json.dumps({"flat": flat_ip, "seg": seg_ip, "zone_of": zone_of,
                               "ports": P["probe_ports"], "flows": [[f["src"], f["dst"], f["port"]] for f in flows],
                               "sweep_flat": "10.10.0.0/26",
                               "sweep_seg": " ".join(str(ip_network(str(n.network_address) + "/27")) for n in zone_net.values())}, indent=1))
print("generated:",", ".join(sorted(os.listdir(OUT))))
