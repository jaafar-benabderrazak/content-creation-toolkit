#!/usr/bin/env python3
"""Start pipeline server + Cloudflare Tunnel + auto-update Vercel env var.

One command to start everything:
    python start.py

Does:
1. Kills any existing tunnel/pipeline_server
2. Starts pipeline_server.py on port 8000
3. Starts Cloudflare Tunnel (free, no request limits)
4. Gets the tunnel URL
5. Updates PIPELINE_TRIGGER_URL on Vercel
6. Redeploys dashboard
7. Keeps running until Ctrl+C
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PORT = 8080
VERCEL_SCOPE = "jaafar-benabderrazaks-projects"
CLOUDFLARED_URL = [None]  # mutable container for thread


def kill_existing():
    """Kill any existing tunnel and pipeline_server processes."""
    if sys.platform == "win32":
        subprocess.run("taskkill /F /IM cloudflared.exe 2>NUL", shell=True, capture_output=True)
        subprocess.run("taskkill /F /IM ngrok.exe 2>NUL", shell=True, capture_output=True)
        subprocess.run(
            f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{PORT} ^| findstr LISTENING\') do taskkill /F /PID %a',
            shell=True, capture_output=True
        )
    else:
        subprocess.run("pkill -f cloudflared 2>/dev/null", shell=True, capture_output=True)
        subprocess.run("pkill -f ngrok 2>/dev/null", shell=True, capture_output=True)
        subprocess.run("pkill -f pipeline_server 2>/dev/null", shell=True, capture_output=True)
    time.sleep(2)


def start_pipeline_server() -> subprocess.Popen:
    """Start pipeline_server.py in background."""
    print(f"[1/4] Starting pipeline server on port {PORT}...")
    proc = subprocess.Popen(
        [sys.executable, "pipeline_server.py", "--port", str(PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    time.sleep(2)
    return proc


def start_cloudflare_tunnel() -> subprocess.Popen:
    """Start Cloudflare Tunnel in background, capture URL from stderr."""
    print("[2/4] Starting Cloudflare Tunnel (free, no limits)...")
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Read stderr in a thread to capture the URL
    def _read_stderr():
        for line in proc.stderr:
            text = line.decode("utf-8", errors="replace").strip()
            # cloudflared prints: "... https://xxx-xxx.trycloudflare.com ..."
            match = re.search(r"(https://[a-z0-9-]+\.trycloudflare\.com)", text)
            if match and CLOUDFLARED_URL[0] is None:
                CLOUDFLARED_URL[0] = match.group(1)

    t = threading.Thread(target=_read_stderr, daemon=True)
    t.start()

    # Wait up to 15s for the URL to appear
    for _ in range(30):
        if CLOUDFLARED_URL[0]:
            break
        time.sleep(0.5)

    return proc


def update_vercel_env(url: str):
    """Update PIPELINE_TRIGGER_URL on Vercel."""
    print(f"[3/4] Updating Vercel env: {url}/trigger")
    # Remove old
    subprocess.run(
        f"vercel env rm PIPELINE_TRIGGER_URL production --yes --scope {VERCEL_SCOPE}",
        capture_output=True, shell=True,
    )
    # Add new
    proc = subprocess.run(
        f'echo {url}/trigger | vercel env add PIPELINE_TRIGGER_URL production --scope {VERCEL_SCOPE}',
        capture_output=True, shell=True,
    )
    if proc.returncode == 0:
        print(f"    Updated PIPELINE_TRIGGER_URL = {url}/trigger")
    else:
        print(f"    Warning: Vercel env update may have failed.")
        print(f"    URL to set manually: {url}/trigger")


def redeploy_vercel():
    """Redeploy dashboard to pick up new env var."""
    print("[4/4] Redeploying dashboard...")
    result = subprocess.run(
        f"vercel deploy --prod --yes --scope {VERCEL_SCOPE}",
        capture_output=True, text=True, shell=True,
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard"),
    )
    if result.returncode == 0:
        print("    Dashboard redeployed.")
    else:
        print("    Warning: Redeploy may have failed.")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("\n" + "=" * 50)
    print("  Content Creation Toolkit — Start")
    print("=" * 50 + "\n")

    kill_existing()

    server_proc = start_pipeline_server()
    tunnel_proc = start_cloudflare_tunnel()

    url = CLOUDFLARED_URL[0]
    if url:
        print(f"\n    Tunnel URL: {url}")
        print(f"    Pipeline:   http://localhost:{PORT}")
    else:
        print(f"\n    WARNING: Could not get Cloudflare Tunnel URL.")
        print(f"    Pipeline server is running locally: http://localhost:{PORT}")
        print(f"    Try: cloudflared tunnel --url http://localhost:{PORT}")

    if url:
        update_vercel_env(url)
        redeploy_vercel()

    print("\n" + "=" * 50)
    print("  All services running. Press Ctrl+C to stop.")
    print("=" * 50)
    print(f"\n  Local:     http://localhost:{PORT}/health")
    if url:
        print(f"  Remote:    {url}/health")
    print(f"  Dashboard: https://dashboard-mocha-seven-49.vercel.app")
    print(f"  Gradio UI: python run.py ui")
    print()

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server_proc.terminate()
        tunnel_proc.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
