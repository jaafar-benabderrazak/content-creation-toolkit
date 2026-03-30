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
RUN_LOGS: dict[str, list[str]] = {}  # run_id → list of log lines (live)


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

        if self.path.startswith("/logs"):
            # /logs?run_id=xxx&offset=0
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            run_id = qs.get("run_id", [""])[0]
            offset = int(qs.get("offset", ["0"])[0])

            if not run_id:
                # Return latest run's logs
                if ACTIVE_RUNS:
                    run_id = list(ACTIVE_RUNS.keys())[-1]
                elif RUN_LOGS:
                    run_id = list(RUN_LOGS.keys())[-1]

            lines = RUN_LOGS.get(run_id, [])
            status = ACTIVE_RUNS.get(run_id, {}).get("status", "unknown")
            self._send_json(200, {
                "run_id": run_id,
                "status": status,
                "total_lines": len(lines),
                "offset": offset,
                "lines": lines[offset:offset + 200],
            })
            return

        # --- Content Roadmap ---
        if self.path.startswith("/roadmap"):
            from urllib.parse import urlparse, parse_qs
            from roadmap import get_roadmap
            qs = parse_qs(urlparse(self.path).query)
            status_filter = qs.get("status", [None])[0]
            entries = get_roadmap().list_entries(status_filter=status_filter)
            self._send_json(200, {
                "entries": [
                    {"id": e.id, "title": e.title, "tags": e.tags,
                     "profile": e.profile, "status": e.status, "notes": e.notes}
                    for e in entries
                ],
                "total": len(entries),
            })
            return

        # --- Scheduler / Jobs ---
        if self.path.startswith("/jobs"):
            from scheduler import get_queue
            jobs = get_queue().list_jobs()
            self._send_json(200, {
                "jobs": [
                    {"id": j.id, "profile": j.profile, "tags": j.tags,
                     "scheduled_at": j.scheduled_at, "status": j.status}
                    for j in jobs
                ],
            })
            return

        # --- Last Artifacts ---
        if self.path.startswith("/artifacts"):
            from pathlib import Path
            import glob
            out_dir = Path("out")
            artifacts = {"video": None, "thumbnail": None, "image": None, "audio": None}

            # Find most recent video
            videos = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True) if out_dir.exists() else []
            if videos:
                v = videos[0]
                artifacts["video"] = {"path": str(v), "size_mb": round(v.stat().st_size / (1024*1024), 1), "name": v.name}
                # Find associated assets
                assets_dir = v.with_name(v.stem + "_enhanced_assets")
                if assets_dir.exists():
                    # Thumbnail
                    thumbs = list(assets_dir.glob("*thumb*")) + list(assets_dir.glob("*_processed_thumb*"))
                    if not thumbs:
                        thumbs = list(Path(".").glob(f"out/*thumb*.jpg"))
                    if thumbs:
                        artifacts["thumbnail"] = {"path": str(thumbs[0]), "name": thumbs[0].name}
                    # Audio
                    audio_files = list(assets_dir.glob("*.wav")) + list(assets_dir.glob("*.mp3"))
                    if audio_files:
                        a = audio_files[0]
                        artifacts["audio"] = {"path": str(a), "size_mb": round(a.stat().st_size / (1024*1024), 1), "name": a.name}

            # Find most recent generated image
            cache_scenes = Path(".cache/images/scenes")
            if cache_scenes.exists():
                images = sorted(cache_scenes.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
                if images:
                    artifacts["image"] = {"path": str(images[0]), "name": images[0].name, "count": len(images)}

            self._send_json(200, artifacts)
            return

        # --- Prompt Preview ---
        if self.path.startswith("/preview-prompts"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            tags = qs.get("tags", [""])[0]
            profile = qs.get("profile", ["cinematic"])[0]
            if not tags:
                self._send_json(400, {"error": "tags parameter required"})
                return
            try:
                from generators.prompt_generator import PromptGenerator
                pg = PromptGenerator()
                result = pg.generate(tags, profile)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        # --- Execution History ---
        if self.path.startswith("/history"):
            from execution_log import get_execution_history
            entries = get_execution_history(30)
            self._send_json(200, {"entries": entries})
            return

        self._send_json(404, {"error": "Endpoints: /health, /status, /trigger, /logs, /roadmap, /jobs, /preview-prompts, /history"})

    def do_POST(self):
        if self.path == "/roadmap":
            if not self._auth_check():
                return
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
            action = body.get("action", "")
            from roadmap import get_roadmap
            rm = get_roadmap()
            if action == "add":
                e = rm.add_entry(body["title"], body.get("tags", ""), body.get("profile", "cinematic"), body.get("notes", ""))
                self._send_json(200, {"id": e.id, "title": e.title})
                return
            if action == "update_status":
                ok = rm.update_status(body["id"], body["status"])
                self._send_json(200, {"ok": ok})
                return
            if action == "delete":
                ok = rm.delete_entry(body["id"])
                self._send_json(200, {"ok": ok})
                return
            self._send_json(400, {"error": "action must be add/update_status/delete"})
            return

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

        # Run in background thread with live stdout streaming
        def _run():
            ACTIVE_RUNS[run_id] = {"status": "running", "cmd": cmd, "started": datetime.now().isoformat()}
            RUN_LOGS[run_id] = []
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                for line in proc.stdout:
                    stripped = line.rstrip()
                    RUN_LOGS[run_id].append(stripped)
                    # Cap at 2000 lines to prevent memory bloat
                    if len(RUN_LOGS[run_id]) > 2000:
                        RUN_LOGS[run_id] = RUN_LOGS[run_id][-1500:]
                    logger.info(f"[Run {run_id[:8]}] {stripped}")

                proc.wait()
                exit_code = proc.returncode
                status = "done" if exit_code == 0 else "failed"
                RUN_LOGS[run_id].append(f"\n[Exit code: {exit_code}]")
                last_lines = "\n".join(RUN_LOGS[run_id][-50:])
                update_execution(run_id, status, exit_code, last_lines)
                ACTIVE_RUNS[run_id]["status"] = status
                logger.info(f"[Trigger] Run {run_id} {status} (exit={exit_code})")

                _notify_dashboard(run_id, status, output, exit_code)

            except Exception as e:
                RUN_LOGS.setdefault(run_id, []).append(f"[ERROR] {e}")
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
