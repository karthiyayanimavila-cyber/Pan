from __future__ import annotations

import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

log = logging.getLogger("panbot.health")


def start_health_server(port: int, heartbeat: Path, process_getter):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path not in {"/", "/healthz"}:
                self.send_error(404)
                return
            age = None
            if heartbeat.exists():
                age = round(max(0.0, time.time() - heartbeat.stat().st_mtime), 2)
            payload = {"ok": True, "poller_alive": process_getter() is not None, "last_poll_age_seconds": age}
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A002
            log.info("health: " + format, *args)

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    thread = Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    log.info("Health server listening on 0.0.0.0:%s", port)
    return server
