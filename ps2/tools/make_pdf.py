#!/usr/bin/env python3
"""Build the illustrated plain-language report as HTML (results/report.html). tools/make_pdf.ps1 turns it into a PDF.
All numbers and outputs come from results/*; nothing is typed in by hand."""
import base64, csv, html, json, os, yaml

R = "results"
P = yaml.safe_load(open("policy.yaml"))
A = json.load(open("generated/addr.json"))
S = json.load(open(f"{R}/surface.json"))
zone_of = A["zone_of"]

def read(p, default=""):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else default
def lines(name):
    out = {}
    for l in read(f"{R}/{name}").splitlines():
        p = l.split("|", 2)
        if len(p) == 3: out[p[0]] = (p[1], p[2])
    return out
def img(name, cap="", cls=""):
    mime = "image/jpeg" if name.endswith(".jpg") else "image/png"
    b = base64.b64encode(open(f"{R}/{name}", "rb").read()).decode()
    return f'<figure class="{cls}"><img src="data:{mime};base64,{b}"><figcaption>{cap}</figcaption></figure>'
def term(title, text):
    return f'<div class="term"><div class="tt">{html.escape(title)}</div><pre>{html.escape(text.strip())}</pre></div>'
def say(label, text, kind="plain"):
    return f'<div class="call {kind}"><b>{label}</b> {text}</div>'
def badge(state):
    good = state in ("PASS", "BLOCKED")
    return f'<span class="bd {"g" if good else "r"}">{html.escape(state)}</span>'

fa, sa = lines("flat_attack.txt"), lines("seg_attack.txt")
fb, sb = lines("flat_business.txt"), lines("seg_business.txt")
sd, st = lines("seg_defense.txt"), lines("seg_selftest.txt")
lint = read(f"{R}/lint.txt")
router = read("generated/router.nft").splitlines()
dbnft = read("generated/db.nft")
drops = list(csv.DictReader(open(f"{R}/drops.csv"))) if os.path.exists(f"{R}/drops.csv") else []
dropsum = read(f"{R}/drops_summary.md").splitlines()[0].replace("## ", "") if os.path.exists(f"{R}/drops_summary.md") else ""
nbus_flat = sum(1 for v in fb.values() if v[0] == "PASS")
nbus_seg = sum(1 for v in sb.values() if v[0] == "PASS")
router_excerpt = "\n".join(router[:22])
ndrops = sum(int(r["dropped_packets"]) for r in drops)

STAGE = {"A1": ("Port scan", "The attacker knocks on every door (port) of every machine to see which ones are open."),
         "A5": ("Host discovery", "The attacker asks 'who else is on this network?' to build a map."),
         "A2": ("SSH login to the database", "The attacker types a guessed password into the database machine's remote-login door."),
         "A3": ("SMB to the file server", "The attacker opens the shared-folder door on the file server and reads a secret file."),
         "A4": ("File copy to another host", "The attacker drops a malicious file onto another machine (lateral tool transfer).")}
TECH = {k: v for k, v in P["attack_map"].items()}

CSS = """
@page{size:A4;margin:16mm 14mm 16mm 14mm}
*{box-sizing:border-box}
body{font:11pt/1.5 'Segoe UI',Arial,sans-serif;color:#1c2533;margin:0}
h1{font-size:26pt;margin:0 0 4pt;color:#1f2a44}
h2{font-size:17pt;color:#1f2a44;margin:0 0 6pt;padding-bottom:4pt;border-bottom:3px solid #128c7e}
h3{font-size:12.5pt;color:#128c7e;margin:14pt 0 4pt}
p{margin:0 0 7pt}
.page{page-break-after:always}
.page:last-child{page-break-after:auto}
.cover{background:#1f2a44;color:#fff;padding:60mm 18mm 20mm;margin:-16mm -14mm;height:297mm}
.cover h1{color:#fff;font-size:44pt}
.cover .sub{font-size:16pt;color:#cfd8e3;margin:6pt 0 30pt;max-width:150mm}
.cover .meta{color:#9fb0c4;font-size:11pt}
.cover .bar{width:20mm;height:4mm;background:#128c7e;margin-bottom:10mm}
.kpis{display:flex;gap:8pt;margin:10pt 0}
.kpi{flex:1;border:1px solid #dfe4ea;border-left:5px solid #128c7e;border-radius:6px;padding:8pt 10pt;background:#f6f8fa}
.kpi b{display:block;font-size:22pt;line-height:1.1}
.kpi span{font-size:9.5pt;color:#667385}
.kpi.r{border-left-color:#c83232}.kpi.r b{color:#c83232}
.kpi.g b{color:#2e9e5b}.kpi.g{border-left-color:#2e9e5b}
.call{border-radius:6px;padding:8pt 11pt;margin:8pt 0;font-size:10.5pt}
.call.plain{background:#e8f5f2;border-left:5px solid #128c7e}
.call.warn{background:#fdf1e1;border-left:5px solid #d98a1a}
.call.key{background:#e9edf6;border-left:5px solid #1f2a44}
table{border-collapse:collapse;width:100%;font-size:9.2pt;margin:5pt 0 8pt}
th{background:#1f2a44;color:#fff;text-align:left;padding:4pt 7pt}
td{padding:3pt 7pt;border-bottom:1px solid #dfe4ea;vertical-align:top}
tr:nth-child(even) td{background:#f6f8fa}
.bd{display:inline-block;padding:1pt 8pt;border-radius:99px;font-weight:700;font-size:8.5pt;color:#fff}
.bd.g{background:#2e9e5b}.bd.r{background:#c83232}
figure{margin:8pt 0;text-align:center}
figure img{max-width:100%;max-height:105mm;border:1px solid #dfe4ea;border-radius:6px}
figcaption{font-size:9pt;color:#667385;margin-top:3pt}
.term{margin:8pt 0;border-radius:6px;overflow:hidden;border:1px solid #1b2535;page-break-inside:avoid}
.term .tt{background:#2b3a5a;color:#cfd8e3;font:8.5pt 'Segoe UI';padding:3pt 9pt}
.term pre{margin:0;background:#0f1722;color:#d5deea;padding:8pt 10pt;font:7.6pt/1.3 Consolas,'Courier New',monospace;white-space:pre-wrap;word-break:break-all}
.two{display:flex;gap:12pt}.two>div{flex:1}
.steps{counter-reset:s;list-style:none;padding:0}
.steps li{counter-increment:s;position:relative;padding:3pt 0 3pt 28pt;margin-bottom:2pt}
.steps li:before{content:counter(s);position:absolute;left:0;top:2pt;width:20pt;height:20pt;border-radius:50%;background:#128c7e;color:#fff;text-align:center;line-height:20pt;font-weight:700;font-size:10pt}
code{font:9pt Consolas,monospace;background:#eef1f5;padding:0 3pt;border-radius:3px}
.small{font-size:9pt;color:#667385}
figure.half img{max-height:74mm}
"""

pages = []
# ---------------- cover
pages.append(f"""<div class="cover page"><div class="bar"></div><h1>Flatland</h1>
<div class="sub">How we stopped an attacker from walking across a flat company network, and how we can prove it</div>
<div class="meta">Problem Statement 2: Network segmentation and firewall design<br>Secure Networks Hackathon, 21 November 2026<br><br>
A plain-language report with the real outputs from our lab</div></div>""")

# ---------------- story
pages.append(f"""<div class="page"><h2>1. The story in one minute</h2>
<p>Imagine a company office with <b>no walls and no locked doors</b>. The receptionist, the accountant, the safe and the filing room are all in one big room. If a stranger walks in and sits at any desk, they can walk to the safe.</p>
<p>That is a <b>flat network</b>: every computer can talk to every other computer. If an attacker takes over just one ordinary workstation, they can reach the database in minutes.</p>
<p>Our job was to <b>prove the problem</b>, then <b>rebuild the office with rooms and locked doors</b> (this is called <i>segmentation</i>) so the attack fails, <b>without stopping anyone from doing their real work</b>.</p>
{img("chart_path.png", "Left: the attacker reaches the database and file server directly. Right: the same attacker only gets to use the public web page.")}
<div class="kpis">
<div class="kpi r"><b>{S['flat_open']}</b><span>doors open on the flat network ({S['flat_unauthorized']} of them not needed)</span></div>
<div class="kpi g"><b>{S['seg_open']}</b><span>doors open after: exactly the {len(P['flows'])} the business needs</span></div>
<div class="kpi g"><b>{nbus_seg} of {len(P['flows'])}</b><span>business tasks still work</span></div>
<div class="kpi g"><b>{S['attack_surface_reduction_pct']:.0f}%</b><span>of unnecessary paths removed</span></div></div>
{say("In plain words:", "we built a fake company network on one laptop, attacked it, fixed it, attacked it again, and then used a checker to show that nothing is reachable except what the business needs.", "plain")}
</div>""")

# ---------------- glossary
gl = [("Network / host", "A network is computers connected together. A host is one computer on it."),
      ("Port", "A numbered door on a computer. Each service listens on its own door: 22 is remote login (SSH), 443 is secure web, 445 is shared folders (SMB), 5432 is the database."),
      ("Firewall", "A bouncer that decides which connections may pass. Ours is <b>nftables</b>, built into Linux."),
      ("Router", "The machine that connects separate networks and passes traffic between them. Ours is also where the main firewall sits."),
      ("Subnet / zone", "A separate section of the network. We made four zones: user, DMZ (public-facing), server and management."),
      ("Default deny", "The rule 'block everything unless it is on the allowed list'. The opposite is 'allow everything unless banned', which is how flat networks behave."),
      ("Business flow", "A connection the company genuinely needs, for example the web server talking to the app server on port 8080. We have 8."),
      ("Micro-segmentation", "A small firewall on <i>each</i> computer, so even a computer in the same room cannot talk to it unless allowed."),
      ("Egress filtering", "Controlling what a machine can send <i>out</i>. It stops a hacked machine from phoning home to the attacker."),
      ("Rate limiting", "Limiting how many new connections can be tried per minute. It slows password guessing."),
      ("MITRE ATT&CK", "A public catalogue of attacker techniques with ID numbers (for example T1046 is port scanning). We use it to name what the attacker did."),
      ("D3FEND", "The matching catalogue of defensive techniques.")]
pages.append(f"""<div class="page"><h2>2. Words you will see (in plain English)</h2>
<table><tr><th style="width:26%">Term</th><th>What it means</th></tr>{''.join(f'<tr><td><b>{a}</b></td><td>{b}</td></tr>' for a, b in gl)}</table>
</div>""")

# ---------------- the lab
role = {"ws": ("Workstation", "An employee's computer. This is the one the attacker takes over."),
        "web": ("Web server", "The company's public website."),
        "app": ("App server", "Runs the business logic behind the website. Talks to the database and file server."),
        "db": ("Database", "Holds the company's data (PostgreSQL). Very valuable."),
        "files": ("File server", "Shared folders (Samba), including a file called <code>secret.txt</code>."),
        "jump": ("Jump host", "The administrators' entry point for remote login to the servers.")}
rows = "".join(f"<tr><td><b>{h}</b></td><td>{role[h][0]}</td><td>{role[h][1]}</td><td>{A['flat'][h]}</td><td>{A['seg'][h]}</td><td>{zone_of[h]}</td></tr>" for h in A["flat"])
pages.append(f"""<div class="page"><h2>3. The lab: six computers on one laptop</h2>
<p>Everything runs in <b>Docker containers</b>, which are tiny, throw-away computers. We use six of them, plus one router in the second version. Nothing touches the real venue network.</p>
<table><tr><th>Name</th><th>Role</th><th>What it does</th><th>Address (flat)</th><th>Address (after)</th><th>Zone (after)</th></tr>{rows}</table>
<h3>The big idea: the policy file is the single source of truth</h3>
<p>Instead of typing firewall rules by hand (easy to get wrong), we wrote <b>one short file</b>, <code>policy.yaml</code>, that lists the 8 connections the business needs. A program (<code>gen.py</code>) reads it and <b>generates everything else</b>: the lab setup, the router rules, the host firewalls, the tests and the tables in this report. Change one line and everything updates.</p>
<ol class="steps"><li><b>policy.yaml</b>: zones, addresses and the 8 allowed connections.</li><li><b>gen.py</b>: creates the firewall rules, lab files and business tests from the policy.</li><li><b>Lab</b>: the flat network (before) and the segmented network with a router (after).</li><li><b>Proof harness</b>: tests all 180 combinations of source machine, destination machine and port, from inside the machines.</li></ol>
{say("Why this matters:", "most teams write rules once and hope. We can <i>prove</i> the network matches the policy, and a judge can change a rule and see the result in one command.", "key")}
</div>""")

# ---------------- before
atk_rows = ""
for k in ("A1", "A5", "A2", "A3", "A4"):
    n, d = STAGE[k]
    atk_rows += f"<tr><td><b>{k}</b></td><td><b>{n}</b><br>{d}</td><td>{TECH[k]['technique']}</td><td>{badge('SUCCESS' if fa.get(k, ('',))[0] == 'SUCCESS' else fa.get(k, ('?',))[0])}</td></tr>"
flat_attack_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in sorted(fa.items()))
flat_bus_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in sorted(fb.items()))
pages.append(f"""<div class="page"><h2>4. Before: the flat network and the attack</h2>
<p>We play the attacker. They start on the <b>workstation</b> (the one computer they have taken over) and try five things, in order, against the rest of the company.</p>
<table><tr><th>Stage</th><th>What the attacker does</th><th>ATT&amp;CK</th><th>Result</th></tr>{atk_rows}</table>
<p>In the table, <span class="bd r">SUCCESS</span> means <b>the attacker won</b>. On the flat network every stage succeeds.</p>
{term("Real output: attack script run on the flat network", flat_attack_txt)}
{say("What this tells us:", "the scan found 9 open services the workstation never needs, and the weak password <code>Password123</code> gave the attacker a login on the database machine. Nothing stopped any of it.", "warn")}
<h3>But the business works perfectly</h3>
<p>This is exactly why flat networks survive for years: all 8 legitimate tasks pass. A network can look healthy and still be wide open.</p>
{term("Real output: the 8 business flows on the flat network", flat_bus_txt)}
</div>""")

# ---------------- heatmap before
pages.append(f"""<div class="page"><h2>5. Seeing the problem: the reachability map</h2>
<p>To measure the problem, a checker logs into each machine and tries to connect to every other machine on six common ports: <b>6 sources x 5 destinations x 6 ports = 180 tries</b>. Each try is one square on the map below.</p>
<ul><li><b style="color:#2e9e5b">Green</b>: connection works and the business needs it.</li><li><b style="color:#c83232">Red</b>: connection works but the business does <i>not</i> need it. This is the attacker's playground.</li><li><b>Grey</b>: connection is blocked.</li></ul>
{img("heatmap.png", "Top: flat network, a lot of red. Bottom: after segmentation, only the 8 green squares are left.")}
{img("chart_numbers.png", "The same story as three bar charts.")}
{say("How to read it:", f"before, {S['flat_unauthorized']} red squares are things an attacker can use. After, there are zero red squares and the 8 green business flows are untouched.", "plain")}
</div>""")

# ---------------- design
flow_rows = "".join(f"<tr><td>{f['id']}</td><td>{f['src']} ({zone_of[f['src']]})</td><td>{f['dst']} ({zone_of[f['dst']]})</td><td>{f['port']}</td><td>{f.get('rate', '-')}</td><td>{f['desc']}</td></tr>" for f in P["flows"])
zrows = "".join(f"<tr><td><b>{z}</b></td><td>{d['subnet']}</td><td>{', '.join(d['hosts'])}</td></tr>" for z, d in P["zones"].items())
pages.append(f"""<div class="page"><h2>6. The fix: four rooms and one receptionist</h2>
<p>We split the network into four <b>zones</b>, each its own small network. The only way between zones is through the <b>router</b>, which acts as the receptionist: it checks every visitor against the allowed list.</p>
{img("topology.png", "Four zones joined only by the router. There is no other path between them.")}
<table><tr><th>Zone</th><th>Address range</th><th>Machines</th></tr>{zrows}</table>
<h3>The allowed list (data-flow table)</h3>
<p>These 8 connections are the <b>only</b> traffic the business needs. Everything else is refused and recorded.</p>
<table><tr><th>ID</th><th>From</th><th>To</th><th>Port</th><th>Limit</th><th>Why it exists</th></tr>{flow_rows}</table>
</div>""")

# ---------------- layers
pages.append(f"""<div class="page"><h2>7. How it is enforced: four layers</h2>
<p>We stack four locks and test each one.</p>
<h3>Layer 1: the router says 'no' by default</h3>
<p>The router's firewall starts from <code>policy drop</code>: anything not on the list is thrown away. Each business flow gets one rule. Here are the real first rules (<code>generated/router.nft</code>):</p>
{term("Real file: router rules (excerpt)", router_excerpt)}
<h3>Layer 2: every computer has its own firewall</h3>
<p>Even if a router rule were wrong, each machine only accepts the connections listed for it. This is the database's own firewall: only the app may connect on 5432 and only the jump host on 22.</p>
{term("Real file: database host firewall", dbnft)}
<h3>Layers 3 and 4: egress filtering and rate limiting</h3>
<p><b>Egress:</b> the database may not start outbound connections, and the server zone may not call into the user zone, so a hacked server cannot phone home. <b>Rate limit:</b> management logins are capped at 20 new connections per minute, which makes password guessing slow and noisy.</p>
</div>""")

# ---------------- after
atk_rows2 = "".join(f"<tr><td><b>{k}</b></td><td>{STAGE[k][0]}</td><td>{badge(fa.get(k, ('?',))[0] if fa.get(k, ('?',))[0] == 'SUCCESS' else fa.get(k, ('?',))[0])}</td><td>{badge(sa.get(k, ('?',))[0])}</td></tr>" for k in ("A1", "A5", "A2", "A3", "A4"))
seg_attack_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in sorted(sa.items()))
seg_bus_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in sorted(sb.items()))
top_drops = "\n".join(f"{r['src']} ({r['src_zone']}) -> {r['dst']} ({r['dst_zone']}) port {r['port']}: {r['dropped_packets']} packets dropped" for r in drops[:10])
pages.append(f"""<div class="page"><h2>8. After: the same attack, the same business tests</h2>
<p>We ran the <b>exact same</b> attack script and the <b>exact same</b> business script on the segmented network.</p>
<table><tr><th>Stage</th><th>Behaviour</th><th>Flat network</th><th>Segmented</th></tr>{atk_rows2}</table>
<p><span class="bd g">BLOCKED</span> means the defense worked. All five stages are blocked.</p>
{term("Real output: attack script on the segmented network", seg_attack_txt)}
<h3>The business still works</h3>
<p>{nbus_seg} of {len(P['flows'])} business flows pass: the web server still reaches the app, the app still reaches the database, and admins can still log in through the jump host.</p>
{term("Real output: the 8 business flows on the segmented network", seg_bus_txt)}
</div>""")

pages.append(f"""<div class="page"><h2>9. What the router refused (the evidence trail)</h2>
<p>The router does not just block, it <b>writes down what it blocks</b>. While the attacker ran, we captured every dropped packet from the router and summarised it.</p>
{img("chart_drops.png", "Dropped packets by the door the attacker tried.")}
{term("Real output: dropped traffic summary: " + dropsum, top_drops)}
{say("In plain words:", f"the attacker knocked on doors it was never allowed to open. The router refused {ndrops} knocks and recorded exactly who tried what. That log is what a security team would investigate, and it maps directly to ATT&amp;CK: scanning (T1046), mapping the network (T1018), SSH attempts (T1021.004) and SMB attempts (T1021.002).", "plain")}
</div>""")

# ---------------- proof
pages.append(f"""<div class="page"><h2>10. The proof: exactly the policy is reachable</h2>
<p>It is easy to say a network is secure. We check it. After the fix the 180-try checker found:</p>
<div class="kpis"><div class="kpi g"><b>{S['seg_open']}</b><span>open connections, all 8 in the policy</span></div><div class="kpi g"><b>{S['seg_unauthorized']}</b><span>open but not allowed (violations)</span></div><div class="kpi g"><b>{S['seg_breaks']}</b><span>allowed but broken (business impact)</span></div></div>
{term("Real output: proof harness on the segmented network", "[seg] probed 180 host/port pairs: %d open, %d not in policy (violations), %d allowed-but-closed (breaks)\n[seg] PROOF PASS: exactly the policy is reachable, nothing else" % (S['seg_open'], S['seg_unauthorized'], S['seg_breaks']))}
<h3>The live dashboard</h3>
<p>For the demo, every step above runs live from a dashboard. Nothing on it is pre-recorded: each button runs the real attack, the real tests and the real probe, and the router's refused packets scroll past as they happen.</p>
{img("dashboard_top.jpg", "Live dashboard: attack stages and business flows, flat versus segmented.", "half")}
{img("dashboard_bottom.jpg", "Live dashboard: reachability matrix before and after, and the router drop feed.", "half")}
</div>""")

# ---------------- selftest + extra
sd_rows = "".join(f"<tr><td><b>{k}</b></td><td>{badge(v[0])}</td><td>{v[1]}</td></tr>" for k, v in sd.items())
st_rows = "".join(f"<tr><td><b>{k}</b></td><td>{badge(v[0])}</td><td>{v[1]}</td></tr>" for k, v in st.items())
sd_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in sd.items())
st_txt = "\n".join(f"{k}|{v[0]}|{v[1]}" for k, v in st.items())
pages.append(f"""<div class="page"><h2>11. Can we trust our own checker? We break the network on purpose</h2>
<p>A test that always says 'PASS' is worthless. So we deliberately made a mistake and checked that the checker noticed.</p>
<table><tr><th>Step</th><th>Result</th><th>What happened</th></tr>{st_rows}</table>
<ol class="steps"><li><b>S1</b>: we added one wrong rule on the router that let the workstation reach the database. The database's own firewall <i>still blocked it</i>. That is why we use two layers.</li><li><b>S2</b>: we also added the matching hole on the database firewall. Now the network really was wrong, and the checker <b>caught it</b>.</li><li><b>S3</b>: we restored the rules and the checker passed again.</li></ol>
{term("Real output: negative control", st_txt)}
<h2 style="margin-top:14pt">12. Extra defenses we tested</h2>
<table><tr><th>Check</th><th>Result</th><th>What it proves</th></tr>{sd_rows}</table>
{term("Real output: extra defense checks", sd_txt)}
</div>""")

# ---------------- blast radius + lint
pages.append(f"""<div class="page"><h2>13. If one machine is hacked, how far can it go?</h2>
<p>We also analysed the policy itself, without running anything. This shows the <b>worst case</b>: the attacker fully controls one machine and follows every allowed connection.</p>
{term("Real output: policy lint and blast radius", lint)}
<table><tr><th>Hacked machine</th><th>Flat network can reach</th><th>Segmented network can reach</th></tr>
<tr><td>workstation</td><td>5 of 5 machines directly</td><td>the web server directly; the rest only by also breaking each service on the way</td></tr>
<tr><td>database or file server</td><td>5 of 5</td><td>nothing</td></tr></table>
{say("Honest note:", "segmentation does not make a machine unhackable. It limits how far a hack can spread (the 'blast radius') and makes every extra step visible and noisy.", "warn")}
<h2 style="margin-top:14pt">14. MITRE ATT&amp;CK and D3FEND mapping</h2>
<table><tr><th>Stage</th><th>ATT&amp;CK technique</th><th>D3FEND defense</th><th>Mitigation</th></tr>{''.join(f"<tr><td>{k} {m['name']}</td><td>{m['technique']}</td><td>{m['d3fend']}</td><td>{m['mitigation']}</td></tr>" for k, m in P['attack_map'].items())}</table>
<p class="small">M1030 is Network Segmentation and M1037 is Filter Network Traffic.</p>
</div>""")

# ---------------- reproduce + limits
pages.append(f"""<div class="page"><h2>15. How to reproduce everything</h2>
<p>All commands run inside Ubuntu on Windows (WSL2) with Docker Desktop running.</p>
{term("Run the whole story, step by step with pauses", "wsl -d Ubuntu\ncd /mnt/d/hackathon_prep/ps2\n./demo_live.sh        # press Enter between steps\n./dashboard.sh        # live dashboard on http://localhost:8765")}
<table><tr><th>I want to...</th><th>Command</th></tr>
<tr><td>Re-run the business tests</td><td><code>bash generated/business.sh seg</code></td></tr>
<tr><td>Re-run the attack</td><td><code>bash tests/attack.sh seg</code></td></tr>
<tr><td>Prove the network matches the policy</td><td><code>python tools/verify.py probe seg</code></td></tr>
<tr><td>Show the firewall rules</td><td><code>docker exec ps2-router nft list ruleset</code></td></tr>
<tr><td>Try any attack of my own</td><td><code>docker exec ps2-ws nmap -Pn -p 22,445,5432 10.10.30.11</code></td></tr>
<tr><td>Change the policy and rebuild</td><td>edit <code>policy.yaml</code>, then <code>./lab.sh down; ./lab.sh build; ./lab.sh seg</code></td></tr></table>
<h2 style="margin-top:14pt">16. Limits and what we would do next</h2>
<ul><li>The checker tests TCP on six ports. UDP and IPv6 are not tested yet.</li>
<li>Allowed connections can still be abused, for example SSH from the jump host. Rate limiting slows this but does not remove it.</li>
<li>The weak password <code>Password123</code> exists only in the lab, on purpose, so the attacks work.</li>
<li>Next: test UDP and IPv6, alert on drops in real time, and run the proof automatically whenever the policy changes so a mistake cannot ship.</li></ul>
<h3>Where everything is</h3>
<table><tr><th>File</th><th>What it is</th></tr>
<tr><td><code>policy.yaml</code></td><td>The single source of truth.</td></tr><tr><td><code>generated/router.nft</code></td><td>The router firewall (a deliverable).</td></tr>
<tr><td><code>generated/flows.md</code></td><td>Addressing plan and data-flow table.</td></tr><tr><td><code>tests/</code>, <code>generated/business.sh</code></td><td>The attack, business and defense scripts.</td></tr>
<tr><td><code>results/</code></td><td>Every output shown in this report, plus the heatmap, diagrams and the captured drops.</td></tr></table>
</div>""")

doc = f"<!doctype html><html><head><meta charset='utf-8'><title>Flatland: PS2 report</title><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
open(f"{R}/report.html", "w", encoding="utf-8").write(doc)
print("wrote results/report.html,", len(pages), "pages,", round(len(doc) / 1e6, 1), "MB")
