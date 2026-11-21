#!/usr/bin/env python3
"""Live demo dashboard. Run in WSL2 Ubuntu:  python tools/dashboard.py   then open http://localhost:8765
Every button runs the real lab commands; results and router drops stream in live. Binds to localhost only."""
import json, os, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADDR = json.load(open("generated/addr.json")) if os.path.exists("generated/addr.json") else {}
LOCK = threading.Lock()
ENV = dict(os.environ)

def sh(cmd):
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, cwd=ROOT).stdout

def mode():
    names = sh("docker ps --format '{{.Names}}'").split()
    return "seg" if "ps2-router" in names else "flat" if "ps2-ws" in names else "down"

def sweep(m):
    return ADDR.get("sweep_seg" if m == "seg" else "sweep_flat", "10.10.0.0/26")

def actions(m):
    return {
        "flat": "./lab.sh down; ./lab.sh flat",
        "seg": "./lab.sh down; ./lab.sh seg",
        "down": "./lab.sh down",
        "business": f"bash generated/business.sh {m}",
        "attack": f"CIDRS='{sweep(m)}' bash tests/attack.sh {m}",
        "probe": f"python tools/verify.py probe {m}",
        "defense": "bash tests/defense.sh",
        "selftest": "bash tests/selftest.sh",
        "lint": "python tools/lint.py",
    }

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body, ctype="text/html; charset=utf-8"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(b)

    def sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def sse(self, line):
        self.wfile.write(("data: " + json.dumps(line) + "\n\n").encode()); self.wfile.flush()

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/":
            return self.send(200, open("tools/dashboard.html", encoding="utf-8").read())
        if u.path == "/api/state":
            return self.send(200, json.dumps({"mode": mode(), "addr": ADDR, "flows": ADDR.get("flows", [])}), "application/json")
        if u.path == "/api/matrix":
            p = f"results/{q.get('phase', ['seg'])[0]}_matrix.json"
            return self.send(200, open(p).read() if os.path.exists(p) else "{}", "application/json")
        if u.path == "/api/run":
            return self.run(q.get("action", [""])[0])
        if u.path == "/api/drops":
            return self.drops()
        self.send(404, "not found", "text/plain")

    def run(self, action):
        m = mode(); cmds = actions(m)
        self.sse_start()
        if action not in cmds or (action in ("business", "attack", "probe") and m == "down") or \
           (action in ("defense", "selftest") and m != "seg"):
            return self.sse({"t": "err", "line": f"'{action}' is not available while the lab is {m}"})
        if not LOCK.acquire(blocking=False):
            return self.sse({"t": "err", "line": "another step is still running"})
        try:
            self.sse({"t": "start", "action": action, "mode": m})
            p = subprocess.Popen(["bash", "-c", cmds[action]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, cwd=ROOT, env=ENV)
            for line in p.stdout:
                line = line.rstrip("\n")
                if "Container" in line and ("Creating" in line or "Created" in line or "Starting" in line or "Running" in line): continue
                if line.startswith(" Network ") or line.startswith(" Container "): continue
                self.sse({"t": "line", "line": line})
            p.wait()
            self.sse({"t": "done", "action": action, "mode": mode()})
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            LOCK.release()

    def drops(self):
        self.sse_start()
        if mode() != "seg":
            return self.sse({"t": "info", "line": "no router yet (flat network): nothing is filtered"})
        p = subprocess.Popen(["docker", "exec", "ps2-router", "tcpdump", "-l", "-nn", "-q", "-i", "nflog:2"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        try:
            for line in p.stdout:
                parts = line.split()
                if len(parts) >= 5 and parts[1] == "IP":
                    self.sse({"t": "drop", "line": f"{parts[2]} > {parts[4].rstrip(':')}", "ts": time.strftime("%H:%M:%S")})
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            p.kill()

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", 8765), H)
    print("Live dashboard on http://localhost:8765  (Ctrl+C to stop)", flush=True)
    srv.serve_forever()
