#!/usr/bin/env python3
"""Build Flatland_PS2_Deck.pptx from the saved results. Run: python tools/make_deck.py"""
import json, yaml
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

NAVY, TEAL, RED, AMBER = RGBColor(0x1F, 0x2A, 0x44), RGBColor(0x12, 0x8C, 0x7E), RGBColor(0xC8, 0x32, 0x32), RGBColor(0xD9, 0x8A, 0x1A)
INK, MUTED, LIGHT, WHITE = RGBColor(0x22, 0x2B, 0x38), RGBColor(0x5F, 0x6B, 0x7A), RGBColor(0xF2, 0xF5, 0xF8), RGBColor(0xFF, 0xFF, 0xFF)

P = yaml.safe_load(open("policy.yaml"))
surf = json.load(open("results/surface.json"))
def rows(name):
    out = {}
    for l in open(f"results/{name}"):
        p = l.rstrip("\n").split("|", 2)
        if len(p) == 3: out[p[0]] = p[1:]
    return out
fa, sa = rows("flat_attack.txt"), rows("seg_attack.txt")
fb, sb = rows("flat_business.txt"), rows("seg_business.txt")
sd, st = rows("seg_defense.txt"), rows("seg_selftest.txt")

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5

def tb(slide, x, y, w, h, text, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Calibri"):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, font
        r.font.color.rgb = color
        p.space_after = Pt(6)
    return s

def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s

def slide(title, sub=None, n=[1]):
    s = prs.slides.add_slide(BLANK); n[0] += 1
    rect(s, 0, 0, W, 0.12, TEAL)
    tb(s, 0.6, 0.35, 12.1, 0.8, title, 32, True, NAVY)
    if sub: tb(s, 0.6, 1.1, 12.1, 0.5, sub, 16, False, MUTED)
    tb(s, 0.6, 7.05, 8, 0.3, "Flatland | PS2 | Secure Networks Hackathon", 10, False, MUTED)
    tb(s, 12.0, 7.05, 0.8, 0.3, str(n[0]), 10, False, MUTED, PP_ALIGN.RIGHT)
    return s

def picture(s, path, x, y, maxw, maxh):
    w, h = Image.open(path).size
    sc = min(maxw / w, maxh / h)
    s.shapes.add_picture(path, Inches(x + (maxw - w * sc) / 2), Inches(y), Inches(w * sc), Inches(h * sc))

def table(s, x, y, w, data, colw, size=13, rowh=0.38, hdr=NAVY, colors=None):
    t = s.shapes.add_table(len(data), len(data[0]), Inches(x), Inches(y), Inches(w), Inches(rowh * len(data))).table
    for i, cw in enumerate(colw): t.columns[i].width = Inches(cw)
    for r, row in enumerate(data):
        t.rows[r].height = Inches(rowh)
        for c, val in enumerate(row):
            cell = t.cell(r, c); cell.text = str(val)
            cell.margin_left = cell.margin_right = Inches(0.08); cell.margin_top = cell.margin_bottom = Inches(0.03)
            p = cell.text_frame.paragraphs[0]; f = p.runs[0].font
            f.size, f.name = Pt(size), "Calibri"
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = hdr; f.color.rgb = WHITE; f.bold = True
            else:
                cell.fill.fore_color.rgb = WHITE if r % 2 else LIGHT; f.color.rgb = INK
                if colors and (r, c) in colors: f.color.rgb = colors[(r, c)]; f.bold = True
    return t

def stat(s, x, y, w, big, small, color):
    rect(s, x, y, w, 1.5, LIGHT)
    rect(s, x, y, 0.08, 1.5, color)
    tb(s, x + 0.25, y + 0.1, w - 0.3, 0.8, big, 40, True, color)
    tb(s, x + 0.25, y + 0.9, w - 0.3, 0.6, small, 14, False, MUTED)

# 1 title
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, H, NAVY); rect(s, 0.6, 2.2, 0.12, 1.9, TEAL)
tb(s, 0.95, 2.1, 11, 1.1, "Flatland", 60, True, WHITE)
tb(s, 0.95, 3.2, 11, 0.9, "Segmenting a flat network with policy-as-code and a proof you can re-run", 24, False, RGBColor(0xCF, 0xD8, 0xE3))
tb(s, 0.95, 5.2, 11, 0.5, "PS2 | Network segmentation and firewall design | Secure Networks Hackathon, 21 November 2026", 15, False, RGBColor(0x9F, 0xAE, 0xC0))

# 2 problem
s = slide("The problem: one flat network, one compromised workstation", "An attacker who owns a workstation can reach the database in minutes")
bul = ["Everything sits on one network: workstation, web, app, database, file server, jump host.",
       "Nothing stops a scan, an SSH login, an SMB connection or a file copy between them.",
       "Our task: prove the attack works, redesign the network, and prove the attack fails without breaking a single legitimate business flow."]
tb(s, 0.7, 1.9, 7.2, 4.5, bul, 20)
stat(s, 8.4, 1.9, 4.2, "6", "hosts on one flat network", NAVY)
stat(s, 8.4, 3.65, 4.2, "5 of 5", "attack stages succeed", RED)
stat(s, 8.4, 5.4, 4.2, "8 of 8", "business flows must keep working", TEAL)

# 3 approach
s = slide("Our approach: the policy is the single source of truth", "Nothing is hand-edited. Change a flow, regenerate, re-prove.")
boxes = [("policy.yaml", "zones, addressing,\n8 business flows", NAVY),
         ("gen.py", "generates compose,\nrouter + host firewalls,\ntests, tables", TEAL),
         ("Segmented lab", "router container,\ndefault deny, logging", TEAL),
         ("Proof harness", "probes 180 source/\ndestination/port pairs", AMBER)]
for i, (a, b, c) in enumerate(boxes):
    x = 0.7 + i * 3.15
    rect(s, x, 2.2, 2.7, 2.0, c, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tb(s, x + 0.1, 2.35, 2.5, 0.5, a, 20, True, WHITE, PP_ALIGN.CENTER)
    tb(s, x + 0.1, 3.0, 2.5, 1.1, b.split("\n"), 14, False, WHITE, PP_ALIGN.CENTER)
    if i < 3: tb(s, x + 2.7, 2.9, 0.45, 0.6, ">", 28, True, MUTED, PP_ALIGN.CENTER)
tb(s, 0.7, 4.8, 12, 1.8, ["The proof compares what is actually reachable with what the policy allows.",
                          "Anything open but not in the policy is a violation. Anything allowed but closed is a broken business flow.",
                          "A judge can change a rule and see the result in one command."], 18)

# 4 before
s = slide("Before: on the flat network every attack stage wins", "Run from the workstation against the lab only")
data = [["Stage", "Behaviour", "ATT&CK", "Result"]]
col = {}
for i, (k, m) in enumerate(P["attack_map"].items(), 1):
    data.append([k, m["name"], m["technique"], fa[k][0]]); col[(i, 3)] = RED
table(s, 0.7, 1.9, 7.6, data, [0.8, 3.7, 1.4, 1.7], 14, 0.5, colors=col)
stat(s, 8.8, 1.9, 3.8, str(surf["flat_open"]), "of 180 host/port pairs open", RED)
stat(s, 8.8, 3.65, 3.8, str(surf["flat_unauthorized"]), "reachable paths not needed by the business", RED)
tb(s, 0.7, 5.3, 12, 1.5, ["The port scan alone exposed 9 services beyond the web portal, and a weak password gave a shell on the database host.",
                          "All 8 business flows pass, so the flat network 'works', which is exactly why it is dangerous."], 16, False, MUTED)

# 5 design
s = slide("Design: four zones joined only by a router", "User, DMZ, server and management zones, each on its own subnet")
picture(s, "results/topology.png", 0.9, 1.7, 11.5, 5.2)

# 6 flows
s = slide("Data-flow table: the only traffic allowed", "Everything else is dropped by default and logged")
zone_of = {h: z for z, d in P["zones"].items() for h in d["hosts"]}
data = [["ID", "From (zone)", "To (zone)", "Port", "Rate limit", "Purpose"]]
for f in P["flows"]:
    data.append([f["id"], f"{f['src']} ({zone_of[f['src']]})", f"{f['dst']} ({zone_of[f['dst']]})", f"{f['port']}/tcp", f.get("rate", "-"), f["desc"]])
table(s, 0.6, 1.8, 12.1, data, [0.6, 1.9, 1.9, 1.0, 1.3, 5.4], 13, 0.46)
tb(s, 0.6, 6.0, 12.1, 0.8, "Addressing plan: user 10.10.10.0/24, DMZ 10.10.20.0/24, server 10.10.30.0/24, management 10.10.40.0/24. Router at .254 in each zone.", 14, False, MUTED)

# 7 layers
s = slide("Defense in depth: four layers, each tested", "One wrong rule must not open a hole")
layers = [("1  Router: default deny", "Stateful forward chain, one rule per business flow, dropped traffic logged per zone."),
          ("2  Host firewalls on every host", "Each host only accepts the flows listed for it. Same-zone lateral movement is blocked."),
          ("3  Egress filtering", "The database host cannot start outbound connections. Server zone cannot call into the user zone."),
          ("4  Rate limiting", "Management SSH is limited to 20 per minute: 60 rapid attempts, only 20 got through.")]
for i, (a, b) in enumerate(layers):
    y = 1.85 + i * 1.2
    rect(s, 0.7, y, 0.1, 1.0, TEAL)
    tb(s, 1.0, y - 0.02, 11.5, 0.45, a, 20, True, NAVY)
    tb(s, 1.0, y + 0.45, 11.5, 0.6, b, 15, False, MUTED)
tb(s, 0.7, 6.65, 12, 0.4, "Checks E1 to E5: " + ", ".join(f"{k} {v[0]}" for k, v in sd.items()), 12, False, TEAL, font="Calibri")

# 8 proof
s = slide("The proof: reachability matrix before and after", "Rows are source hosts, columns are destination:port. Probed from inside the containers.")
picture(s, "results/heatmap.png", 0.6, 1.65, 12.1, 5.3)

# 9 results
s = slide("Result: every attack blocked, every business flow still works", "Same attack script and same business script, before and after")
data = [["Measure", "Flat network", "Segmented network"],
        ["Attack stages that succeed", "5 of 5", "0 of 5"],
        ["Business flows that pass", f"{sum(1 for v in fb.values() if v[0]=='PASS')} of 8", f"{sum(1 for v in sb.values() if v[0]=='PASS')} of 8"],
        ["Host/port pairs open (of 180)", str(surf["flat_open"]), str(surf["seg_open"])],
        ["Open but not in the policy", str(surf["flat_unauthorized"]), str(surf["seg_unauthorized"])],
        ["Broken business flows", "0", str(surf["seg_breaks"])]]
table(s, 0.7, 1.9, 8.0, data, [3.8, 2.0, 2.2], 16, 0.6, colors={(1, 1): RED, (1, 2): TEAL, (4, 1): RED, (4, 2): TEAL, (2, 2): TEAL})
stat(s, 9.2, 1.9, 3.4, f"{surf['attack_surface_reduction_pct']:.0f}%", "attack surface removed (unauthorized paths)", TEAL)
stat(s, 9.2, 3.65, 3.4, "8", "open paths left, exactly the 8 business flows", NAVY)
tb(s, 0.7, 5.8, 12, 0.9, "Dropped-traffic log at the router: 120 packets from the workstation, mapped to T1046, T1018, T1021.004 and T1021.002.", 15, False, MUTED)

# 10 trust the tester
s = slide("Can you trust the tester? We break the network on purpose", "Negative control plus static analysis")
tb(s, 0.7, 1.8, 6.4, 0.5, "Negative control (live)", 20, True, NAVY)
y = 2.4
for k, (state, detail) in st.items():
    tb(s, 0.7, y, 6.4, 1.1, [f"{k}  {state}", detail], 14, False, INK); y += 1.2
tb(s, 7.5, 1.8, 5.2, 0.5, "Worst-case blast radius", 20, True, NAVY)
blast = [["Compromised", "Flat", "Segmented"], ["ws", "5 hosts", "web, then app, db, files"], ["web", "5 hosts", "app, db, files"],
         ["app", "5 hosts", "db, files"], ["db / files", "5 hosts", "none"]]
table(s, 7.5, 2.4, 5.2, blast, [1.5, 1.0, 2.7], 13, 0.5)
tb(s, 7.5, 5.1, 5.2, 1.5, ["Policy lint: 8 flows, 0 errors, 0 warnings.", "Pivoting needs a compromise of each allowed service on the way."], 13, False, MUTED)

# 11 mapping
s = slide("MITRE ATT&CK and D3FEND mapping")
data = [["Stage", "ATT&CK", "D3FEND", "Mitigation"]]
for k, m in P["attack_map"].items(): data.append([f"{k} {m['name']}", m["technique"], m["d3fend"], m["mitigation"]])
table(s, 0.7, 1.7, 12.0, data, [4.6, 1.5, 3.7, 2.2], 14, 0.55)
tb(s, 0.7, 5.4, 12, 1.2, "M1030 Network Segmentation and M1037 Filter Network Traffic are the core mitigations. Techniques follow our reading of the statement and the current ATT&CK matrix.", 14, False, MUTED)

# 12 limits
s = slide("Limits and what we would do next")
tb(s, 0.7, 1.7, 6.0, 0.5, "Known limits", 20, True, NAVY)
tb(s, 0.7, 2.3, 6.0, 4.3, ["The proof probes TCP on six ports. UDP and ICMP are not probed.",
                          "Allowed flows can still be abused, for example SSH from the jump host. Rate limiting reduces it, it does not remove it.",
                          "Same-zone blocking relies on two layers, so neither alone is a single point of failure."], 15)
tb(s, 7.0, 1.7, 5.6, 0.5, "Next steps", 20, True, NAVY)
tb(s, 7.0, 2.3, 5.6, 4.3, ["Probe UDP and IPv6 in the proof harness.",
                          "Alert on drops in real time and quarantine a repeat offender.",
                          "Run the proof in CI so a policy change cannot ship a hole."], 15)

# 13 demo plan
s = slide("Live demo plan (about 6 minutes)", "Live: the dashboard runs the real lab on stage (./dashboard.sh). Fallback: ./demo_live.sh in the terminal.")
steps = [("0:00", "Show policy.yaml and the data-flow table"), ("0:45", "Dashboard: build the flat network, attack it live, business flows pass"),
         ("2:15", "Segmented network: same attack blocked, same business flows pass"), ("3:45", "Proof: only the 8 policy paths are reachable"),
         ("4:30", "Break it on purpose: the harness catches the hole"), ("5:15", "Judge variation: any ad-hoc attack from the workstation")]
for i, (t, d) in enumerate(steps):
    y = 1.9 + i * 0.78
    rect(s, 0.7, y, 1.1, 0.55, TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tb(s, 0.7, y + 0.04, 1.1, 0.5, t, 16, True, WHITE, PP_ALIGN.CENTER)
    tb(s, 2.1, y + 0.05, 10.5, 0.5, d, 18, False, INK)

prs.save("Flatland_PS2_Deck.pptx")
print("saved Flatland_PS2_Deck.pptx,", len(prs.slides), "slides")
