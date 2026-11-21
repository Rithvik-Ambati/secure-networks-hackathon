#!/usr/bin/env python3
"""Tiny app tier: /health reports whether it can reach the database."""
import os, socket
from http.server import BaseHTTPRequestHandler, HTTPServer

DB = os.environ.get("DBHOST", "db")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            socket.create_connection((DB, 5432), 2).close()
            state = "up"
        except OSError:
            state = "down"
        body = f"app ok db={state}\n".encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

HTTPServer(("0.0.0.0", 8080), H).serve_forever()
