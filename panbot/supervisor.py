from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .config import load_settings
from .health import start_health_server

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("panbot.supervisor")


def _stop(child: subprocess.Popen[bytes] | None) -> None:
    if child is None or child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        log.warning("Poller did not stop gracefully; killing it")
        child.kill()
        child.wait(timeout=5)


def main() -> None:
    settings = load_settings()
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    heartbeat = settings.runtime_dir / "poller.heartbeat"
    heartbeat.unlink(missing_ok=True)
    child: subprocess.Popen[bytes] | None = None
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True
        _stop(child)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    server = start_health_server(settings.port, heartbeat, lambda: child if child and child.poll() is None else None)
    try:
        while not stopping:
            heartbeat.unlink(missing_ok=True)
            log.info("Starting polling worker")
            child = subprocess.Popen([sys.executable, "-m", "panbot.poller"])
            started = time.monotonic()
            while not stopping:
                exit_code = child.poll()
                if exit_code is not None:
                    log.warning("Polling worker exited with code %s", exit_code)
                    break
                if heartbeat.exists():
                    age = time.time() - heartbeat.stat().st_mtime
                else:
                    age = time.monotonic() - started
                if age > settings.poll_stale_seconds:
                    log.error("Polling heartbeat is stale (%.1fs); restarting worker", age)
                    _stop(child)
                    break
                time.sleep(2)
            if child is not None and child.poll() is None:
                _stop(child)
            child = None
            if not stopping:
                time.sleep(settings.restart_backoff_seconds)
    finally:
        _stop(child)
        server.shutdown()
        server.server_close()
        log.info("Supervisor stopped")


if __name__ == "__main__":
    main()
