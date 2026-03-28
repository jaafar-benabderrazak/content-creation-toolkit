"""Gradio Config UI for Content Creation Toolkit.

Provides a web interface at localhost:7860 for:
- Loading and editing pipeline configs
- Selecting named profiles
- Launching pipelines as subprocesses
- Viewing pipeline output in real-time
"""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

import gradio as gr
import yaml

from config import PipelineConfig

PROFILES_DIR = Path("config/profiles")
LAST_RUN_FILE = Path("configs/last_run.yaml")


def list_profiles() -> list[str]:
    """List available named profiles."""
    profiles = ["(default)"]
    if PROFILES_DIR.exists():
        for f in sorted(PROFILES_DIR.glob("*.yaml")):
            profiles.append(f.stem)
    return profiles


def load_profile(name: str) -> dict:
    """Load a profile and return field values."""
    if name == "(default)":
        cfg = PipelineConfig()
    else:
        path = PROFILES_DIR / f"{name}.yaml"
        if path.exists():
            cfg = PipelineConfig.from_yaml(path)
        else:
            cfg = PipelineConfig()

    return {
        "profile": cfg.profile,
        "style_prompt": cfg.video.style_prompt,
        "music_prompt": cfg.video.music_prompt,
        "mood": cfg.video.mood,
        "duration_minutes": cfg.video.duration_minutes,
        "resolution": cfg.video.resolution,
        "quality_preset": cfg.video.quality_preset,
        "scene_count": cfg.video.scene_count,
        "watermark_enabled": cfg.post.watermark_enabled,
        "watermark_text": cfg.post.watermark_text,
        "subtitles_enabled": cfg.post.subtitles_enabled,
        "youtube_enabled": cfg.publish.youtube_enabled,
        "youtube_title": cfg.publish.youtube_title,
        "youtube_description": cfg.publish.youtube_description,
        "youtube_tags": ", ".join(cfg.publish.youtube_tags),
        "youtube_privacy": cfg.publish.youtube_privacy,
        "discord_webhook_url": cfg.notify.discord_webhook_url or "",
        "slack_webhook_url": cfg.notify.slack_webhook_url or "",
        "require_approval": cfg.notify.require_approval,
    }


def save_config(
    profile, style_prompt, music_prompt, mood, duration_minutes, resolution,
    quality_preset, scene_count, watermark_enabled, watermark_text,
    subtitles_enabled, youtube_enabled, youtube_title, youtube_description,
    youtube_tags, youtube_privacy, discord_webhook_url, slack_webhook_url,
    require_approval,
) -> str:
    """Build PipelineConfig from UI fields and save to YAML."""
    cfg = PipelineConfig(
        profile=profile,
        video={
            "style_prompt": style_prompt,
            "music_prompt": music_prompt,
            "mood": mood,
            "duration_minutes": int(duration_minutes),
            "resolution": resolution,
            "quality_preset": quality_preset,
            "scene_count": int(scene_count),
        },
        post={
            "watermark_enabled": watermark_enabled,
            "watermark_text": watermark_text,
            "subtitles_enabled": subtitles_enabled,
        },
        publish={
            "youtube_enabled": youtube_enabled,
            "youtube_title": youtube_title,
            "youtube_description": youtube_description,
            "youtube_tags": [t.strip() for t in youtube_tags.split(",") if t.strip()],
            "youtube_privacy": youtube_privacy,
        },
        notify={
            "discord_webhook_url": discord_webhook_url or None,
            "slack_webhook_url": slack_webhook_url or None,
            "require_approval": require_approval,
        },
    )

    LAST_RUN_FILE.parent.mkdir(exist_ok=True)
    cfg.to_yaml(LAST_RUN_FILE)
    return f"Config saved to {LAST_RUN_FILE}"


def run_pipeline(pipeline: str, output_path: str) -> str:
    """Launch a pipeline as a subprocess and return output."""
    if not LAST_RUN_FILE.exists():
        return "Error: Save config first"

    if pipeline == "Study Video":
        cmd = [sys.executable, "study_with_me_generator.py",
               "--out", output_path, "--config", str(LAST_RUN_FILE)]
    elif pipeline == "TikTok Tutorial":
        cmd = [sys.executable, "faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py",
               "--config", str(LAST_RUN_FILE)]
    else:
        return f"Unknown pipeline: {pipeline}"

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=7200,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Pipeline timed out after 2 hours"
    except Exception as e:
        return f"Error launching pipeline: {e}"


def build_ui() -> gr.Blocks:
    """Build the Gradio Blocks interface."""
    with gr.Blocks(title="Content Creation Toolkit") as app:
        gr.Markdown("# Content Creation Toolkit")

        with gr.Row():
            profile_dropdown = gr.Dropdown(
                choices=list_profiles(),
                value="(default)",
                label="Profile",
            )
            load_btn = gr.Button("Load Profile")

        with gr.Tabs():
            with gr.Tab("Video Settings"):
                profile_name = gr.Textbox(label="Profile Name", value="default")
                style_prompt = gr.Textbox(label="Style Prompt", lines=3)
                music_prompt = gr.Textbox(label="Music Prompt", lines=2)
                mood = gr.Textbox(label="Mood", value="focused")
                with gr.Row():
                    duration = gr.Number(label="Duration (minutes)", value=120)
                    resolution = gr.Dropdown(choices=["1080p", "720p", "480p"], value="1080p", label="Resolution")
                    quality = gr.Dropdown(choices=["high", "medium", "fast"], value="high", label="Quality")
                    scenes = gr.Number(label="Scene Count", value=24)

            with gr.Tab("Post-Production"):
                watermark_on = gr.Checkbox(label="Watermark", value=False)
                watermark_txt = gr.Textbox(label="Watermark Text")
                subtitles_on = gr.Checkbox(label="Burn Subtitles", value=False)

            with gr.Tab("Publishing"):
                yt_enabled = gr.Checkbox(label="YouTube Upload", value=False)
                yt_title = gr.Textbox(label="YouTube Title")
                yt_desc = gr.Textbox(label="YouTube Description", lines=3)
                yt_tags = gr.Textbox(label="Tags (comma-separated)")
                yt_privacy = gr.Dropdown(choices=["private", "unlisted", "public"], value="private", label="Privacy")

            with gr.Tab("Notifications"):
                discord_url = gr.Textbox(label="Discord Webhook URL")
                slack_url = gr.Textbox(label="Slack Webhook URL")
                approval = gr.Checkbox(label="Require Approval Before Publish", value=True)

        with gr.Row():
            save_btn = gr.Button("Save Config", variant="primary")
            save_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("---")
        gr.Markdown("## Launch Pipeline")

        with gr.Row():
            pipeline_choice = gr.Dropdown(
                choices=["Study Video", "TikTok Tutorial"],
                value="Study Video",
                label="Pipeline",
            )
            output_path = gr.Textbox(label="Output Path", value="out/video.mp4")
            launch_btn = gr.Button("Launch", variant="primary")

        pipeline_output = gr.Textbox(label="Pipeline Output", lines=15, interactive=False)

        # Wire events
        all_fields = [
            profile_name, style_prompt, music_prompt, mood, duration, resolution,
            quality, scenes, watermark_on, watermark_txt, subtitles_on,
            yt_enabled, yt_title, yt_desc, yt_tags, yt_privacy,
            discord_url, slack_url, approval,
        ]

        def on_load(name):
            vals = load_profile(name)
            return [
                vals["profile"], vals["style_prompt"], vals["music_prompt"],
                vals["mood"], vals["duration_minutes"], vals["resolution"],
                vals["quality_preset"], vals["scene_count"],
                vals["watermark_enabled"], vals["watermark_text"],
                vals["subtitles_enabled"], vals["youtube_enabled"],
                vals["youtube_title"], vals["youtube_description"],
                vals["youtube_tags"], vals["youtube_privacy"],
                vals["discord_webhook_url"], vals["slack_webhook_url"],
                vals["require_approval"],
            ]

        load_btn.click(fn=on_load, inputs=[profile_dropdown], outputs=all_fields)
        save_btn.click(fn=save_config, inputs=all_fields, outputs=[save_status])
        launch_btn.click(fn=run_pipeline, inputs=[pipeline_choice, output_path], outputs=[pipeline_output])

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="127.0.0.1", server_port=7860)
