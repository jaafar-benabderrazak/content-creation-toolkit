#!/usr/bin/env python3
"""Content Creation Toolkit — unified launcher.

Usage:
    python run.py                      # Interactive menu
    python run.py video                # Generate video (prompts from tags)
    python run.py server               # Start pipeline server + ngrok
    python run.py dashboard            # Open Vercel dashboard
    python run.py ui                   # Start local Gradio UI
    python run.py setup                # First-run setup (env scan + starter profile)
    python run.py youtube-setup        # YouTube OAuth setup wizard
    python run.py style <handle>       # Build style profile from inspiration images
"""
from __future__ import annotations

import os
import subprocess
import sys
import webbrowser

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DASHBOARD_URL = "https://dashboard-mocha-seven-49.vercel.app"


def cmd_video():
    """Generate a video interactively."""
    profiles = ["lofi_study", "cinematic", "tech_tutorial"]
    print("\nProfiles: " + ", ".join(profiles))
    profile = input("Profile [lofi_study]: ").strip() or "lofi_study"
    tags = input("Tags (e.g., solarpunk, rain, cozy): ").strip()
    duration = input("Duration in minutes [3]: ").strip() or "3"
    out = input(f"Output path [out/{profile}_video.mp4]: ").strip() or f"out/{profile}_video.mp4"

    cmd = [
        sys.executable, "study_with_me_generator.py",
        "--out", out,
        "--config", f"config/profiles/{profile}.yaml",
        "--minutes", duration,
    ]
    if tags:
        cmd += ["--tags", tags]

    os.makedirs("out", exist_ok=True)
    print(f"\nRunning: {' '.join(cmd)}\n")
    subprocess.run(cmd)


def cmd_server():
    """Start pipeline server + ngrok."""
    print("\nStarting pipeline server on port 8000...")
    print("In another terminal, run: ngrok http 8000")
    print("Then set the ngrok URL in Vercel dashboard env vars.\n")
    subprocess.run([sys.executable, "pipeline_server.py"])


def cmd_dashboard():
    """Open Vercel dashboard."""
    print(f"\nOpening {DASHBOARD_URL}")
    webbrowser.open(DASHBOARD_URL)


def cmd_ui():
    """Start local Gradio UI."""
    print("\nStarting Gradio UI on http://localhost:7860\n")
    subprocess.run([sys.executable, "gradio_app.py"])


def cmd_setup():
    """First-run setup."""
    subprocess.run([sys.executable, "setup.py"])


def cmd_youtube_setup():
    """YouTube OAuth setup."""
    subprocess.run([sys.executable, "setup_youtube.py"])


def cmd_style(handle: str = ""):
    """Build style profile from images."""
    if not handle:
        handle = input("Instagram handle [radstream]: ").strip() or "radstream"
    print(f"\nBuilding style profile for @{handle}...")
    subprocess.run([
        sys.executable, "-c",
        f"from generators.style_reference import StyleReferenceManager; "
        f"mgr = StyleReferenceManager(); "
        f"p = mgr.build_or_load('{handle}', refresh=False); "
        f"print(f'Done: {{p.handle}} — {{p.prompt_prefix}}')"
    ])


def menu():
    """Interactive menu."""
    print("""
╔══════════════════════════════════════════╗
║   Content Creation Toolkit              ║
╠══════════════════════════════════════════╣
║  1. Generate Video                      ║
║  2. Start Pipeline Server (+ ngrok)     ║
║  3. Open Dashboard (Vercel)             ║
║  4. Start Local UI (Gradio)             ║
║  5. First-Run Setup                     ║
║  6. YouTube OAuth Setup                 ║
║  7. Build Style Profile                 ║
║  0. Exit                                ║
╚══════════════════════════════════════════╝
""")
    choice = input("Choose [1]: ").strip() or "1"
    actions = {
        "1": cmd_video,
        "2": cmd_server,
        "3": cmd_dashboard,
        "4": cmd_ui,
        "5": cmd_setup,
        "6": cmd_youtube_setup,
        "7": cmd_style,
        "0": lambda: sys.exit(0),
    }
    fn = actions.get(choice)
    if fn:
        fn()
    else:
        print(f"Unknown option: {choice}")


def main():
    args = sys.argv[1:]
    if not args:
        menu()
        return

    cmd = args[0]
    if cmd == "video":
        cmd_video()
    elif cmd == "server":
        cmd_server()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "ui":
        cmd_ui()
    elif cmd == "setup":
        cmd_setup()
    elif cmd == "youtube-setup":
        cmd_youtube_setup()
    elif cmd == "style":
        cmd_style(args[1] if len(args) > 1 else "")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
