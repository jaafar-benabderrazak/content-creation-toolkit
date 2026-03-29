"""Local HTTP server for remote pipeline triggering.

Exposes the video generation pipeline as an HTTP endpoint.
Pair with ngrok to allow the Vercel dashboard to trigger runs remotely.

Usage:
    python pipeline_server.py                    # Start on port 8000
    python pipeline_server.py --port 9000        # Custom port
    ngrok http 8000                              # Expose publicly

Then set PIPELINE_TRIGGER_URL in Vercel env vars to the ngrok URL.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from execution_log import start_execution, update_execution

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Auth: shared secret between Vercel dashboard and local server
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "pipeline-local-secret")
ACTIVE_RUNS: dict[str, dict] = {}


class PipelineHandler(BaseHTTPRequestHandler):
    """HTTP handler for pipeline trigger and status endpoints."""

    def _send_json(self, status: int, data: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-webhook-secret")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _auth_check(self) -> bool:
        secret = self.headers.get("x-webhook-secret", "")
        if secret != WEBHOOK_SECRET:
            self._send_json(401, {"error": "Invalid webhook secret"})
            return False
        return True

    def do_OPTIONS(self):
        self._send_json(200, {})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "active_runs": len(ACTIVE_RUNS),
                "timestamp": datetime.now().isoformat(),
            })
            return

        if self.path == "/status":
            self._send_json(200, {
                "active_runs": {k: v["status"] for k, v in ACTIVE_RUNS.items()},
                "timestamp": datetime.now().isoformat(),
            })
            return

        self._send_json(404, {"error": "Not found. Endpoints: /health, /status, /trigger"})

    def do_POST(self):
        if self.path != "/trigger":
            self._send_json(404, {"error": "POST to /trigger"})
            return

        if not self._auth_check():
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

        profile = body.get("profile", "cinematic")
        tags = body.get("tags", "")
        output = body.get("output", f"out/{profile}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

        # Build command
        cmd = [
            sys.executable, "study_with_me_generator.py",
            "--out", output,
            "--config", f"config/profiles/{profile}.yaml",
        ]
        if tags:
            cmd += ["--tags", tags]

        # Log execution
        entry = start_execution("Study Video (remote)", profile, tags, output)
        run_id = entry.id

        logger.info(f"[Trigger] Starting run {run_id}: profile={profile}, tags={tags!r}")

        # Run in background thread
        def _run():
            ACTIVE_RUNS[run_id] = {"status": "running", "cmd": cmd, "started": datetime.now().isoformat()}
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=7200,
                )
                status = "done" if result.returncode == 0 else "failed"
                last_lines = (result.stdout or "")[-2000:]
                if result.stderr:
                    last_lines += f"\n--- STDERR ---\n{result.stderr[-500:]}"
                update_execution(run_id, status, result.returncode, last_lines)
                ACTIVE_RUNS[run_id]["status"] = status
                logger.info(f"[Trigger] Run {run_id} {status} (exit={result.returncode})")

                # Send status back to Vercel dashboard if configured
                _notify_dashboard(run_id, status, output, result.returncode)

            except subprocess.TimeoutExpired:
                update_execution(run_id, "failed", -1, "Timeout after 2 hours")
                ACTIVE_RUNS[run_id]["status"] = "timeout"
                logger.error(f"[Trigger] Run {run_id} timed out")
            except Exception as e:
                update_execution(run_id, "failed", -1, str(e))
                ACTIVE_RUNS[run_id]["status"] = "error"
                logger.error(f"[Trigger] Run {run_id} error: {e}")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        self._send_json(202, {
            "accepted": True,
            "run_id": run_id,
            "profile": profile,
            "tags": tags,
            "output": output,
            "message": "Pipeline started in background",
        })

    def log_message(self, format, *args):
        # Suppress default access logging
        pass


def _notify_dashboard(run_id: str, status: str, output: str, exit_code: int) -> None:
    """POST status update to Vercel dashboard /api/status endpoint."""
    import requests
    dashboard_url = os.environ.get("DASHBOARD_STATUS_URL")
    if not dashboard_url:
        return
    try:
        requests.post(
            dashboard_url,
            json={
                "run_id": run_id,
                "status": status,
                "output": output,
                "exit_code": exit_code,
                "timestamp": datetime.now().isoformat(),
            },
            headers={"x-webhook-secret": WEBHOOK_SECRET},
            timeout=10,
        )
    except Exception:
        pass  # Non-critical


def main():
    parser = argparse.ArgumentParser(description="Pipeline HTTP server for remote triggering")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), PipelineHandler)
    logger.info(f"Pipeline server running on http://{args.host}:{args.port}")
    logger.info(f"Endpoints: GET /health, GET /status, POST /trigger")
    logger.info(f"Auth: x-webhook-secret header required for /trigger")
    logger.info(f"")
    logger.info(f"To expose remotely:")
    logger.info(f"  ngrok http {args.port}")
    logger.info(f"  Then set PIPELINE_TRIGGER_URL in Vercel to the ngrok URL + /trigger")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
