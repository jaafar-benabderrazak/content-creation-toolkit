#!/usr/bin/env python3
"""Start pipeline server + ngrok + auto-update Vercel env var.

One command to start everything:
    python start.py

Does:
1. Kills any existing ngrok/pipeline_server
2. Starts pipeline_server.py on port 8000
3. Starts ngrok tunnel
4. Gets the new ngrok URL
5. Updates PIPELINE_TRIGGER_URL on Vercel
6. Keeps running until Ctrl+C
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PORT = 8000
VERCEL_SCOPE = "jaafar-benabderrazaks-projects"


def kill_existing():
    """Kill any existing ngrok and pipeline_server processes."""
    if sys.platform == "win32":
        subprocess.run("taskkill /F /IM ngrok.exe 2>NUL", shell=True, capture_output=True)
        # Kill python processes on port 8000
        result = subprocess.run(
            f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{PORT} ^| findstr LISTENING\') do taskkill /F /PID %a',
            shell=True, capture_output=True
        )
    else:
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


def start_ngrok() -> subprocess.Popen:
    """Start ngrok tunnel in background."""
    print(f"[2/4] Starting ngrok tunnel...")
    proc = subprocess.Popen(
        ["ngrok", "http", str(PORT), "--log=stdout", "--log-format=json"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    time.sleep(5)
    return proc


def get_ngrok_url() -> str:
    """Get the public ngrok URL from the local API."""
    import urllib.request
    for port in [4040, 4041]:
        try:
            resp = urllib.request.urlopen(f"http://localhost:{port}/api/tunnels", timeout=5)
            data = json.loads(resp.read())
            return data["tunnels"][0]["public_url"]
        except Exception:
            continue
    raise RuntimeError("Could not get ngrok URL — is ngrok running?")


def update_vercel_env(url: str):
    """Update PIPELINE_TRIGGER_URL on Vercel."""
    print(f"[3/4] Updating Vercel env: {url}/trigger")
    # Remove old
    subprocess.run(
        f"vercel env rm PIPELINE_TRIGGER_URL production --yes --scope {VERCEL_SCOPE}",
        shell=True,
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
        print(f"    Warning: Vercel env update may have failed. Set manually if needed.")
        print(f"    URL: {url}/trigger")


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
        print("    Warning: Redeploy may have failed. Dashboard might use cached env.")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("\n" + "=" * 50)
    print("  Content Creation Toolkit — Start")
    print("=" * 50 + "\n")

    kill_existing()

    server_proc = start_pipeline_server()
    ngrok_proc = start_ngrok()

    try:
        url = get_ngrok_url()
        print(f"\n    ngrok URL: {url}")
        print(f"    Pipeline:  http://localhost:{PORT}")
    except RuntimeError as e:
        print(f"\n    ERROR: {e}")
        print("    Pipeline server is running but ngrok failed.")
        print(f"    Local access: http://localhost:{PORT}")
        print("    Start ngrok manually: ngrok http 8000")
        url = None

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
        ngrok_proc.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
