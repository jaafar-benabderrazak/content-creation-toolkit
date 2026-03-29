"""Gradio Config UI for Content Creation Toolkit.

Provides a web interface at localhost:7860 for:
- Loading and editing pipeline configs
- Selecting named profiles
- Launching pipelines as subprocesses with real-time streaming output
- Scheduling pipeline jobs for future execution
- Managing a video content roadmap
"""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Generator, Optional

import gradio as gr
import yaml

from config import PipelineConfig
from scheduler import get_queue
from roadmap import get_roadmap
from execution_log import start_execution, update_execution, format_history

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
        "require_approval": cfg.notify.require_approval,
    }


def save_config(
    profile, style_prompt, music_prompt, mood, duration_minutes, resolution,
    quality_preset, scene_count, watermark_enabled, watermark_text,
    subtitles_enabled, youtube_enabled, youtube_title, youtube_description,
    youtube_tags, youtube_privacy,
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
            "youtube_tags": [t.strip() for t in (youtube_tags or "").split(",") if t.strip()],
            "youtube_privacy": youtube_privacy,
        },
        notify={
            "require_approval": require_approval,
        },
    )

    LAST_RUN_FILE.parent.mkdir(exist_ok=True)
    cfg.to_yaml(LAST_RUN_FILE)
    return f"Config saved to {LAST_RUN_FILE}"


def _run_pipeline_blocking(pipeline: str, output_path: str) -> str:
    """(Fallback reference) Launch a pipeline as a subprocess and return all output."""
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


def stream_pipeline(pipeline: str, output_path: str, tags: str) -> Generator[str, None, None]:
    """Launch pipeline as subprocess; yield stdout lines as they arrive."""
    if not LAST_RUN_FILE.exists():
        yield "Error: Save config first (use Video Settings tab)"
        return

    if pipeline == "Study Video":
        cmd = [sys.executable, "study_with_me_generator.py",
               "--out", output_path, "--config", str(LAST_RUN_FILE)]
        if tags.strip():
            cmd += ["--tags", tags.strip()]
    elif pipeline == "TikTok Tutorial":
        cmd = [sys.executable,
               "faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py",
               "--config", str(LAST_RUN_FILE)]
    else:
        yield f"Unknown pipeline: {pipeline}"
        return

    entry = start_execution(pipeline, "(from UI)", tags, output_path)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        buffer = []
        for line in proc.stdout:
            buffer.append(line.rstrip())
            if len(buffer) > 500:
                buffer.pop(0)
            yield "\n".join(buffer)
        proc.wait()
        buffer.append(f"\n[Exit code: {proc.returncode}]")
        yield "\n".join(buffer)

        last_50 = "\n".join(buffer[-50:])
        status = "done" if proc.returncode == 0 else "failed"
        update_execution(entry.id, status, proc.returncode, last_50)
    except Exception as e:
        update_execution(entry.id, "failed", -1, str(e))
        yield f"Error launching pipeline: {e}"


# ---------------------------------------------------------------------------
# Schedule tab helper functions
# ---------------------------------------------------------------------------

def add_scheduled_job(profile: str, tags: str, output_path: str, scheduled_at: str) -> str:
    try:
        job = get_queue().add_job(profile, tags, output_path, scheduled_at)
        return f"Job queued: {job.id} — scheduled at {job.scheduled_at}"
    except Exception as e:
        return f"Error: {e}"


def list_jobs_display() -> str:
    jobs = get_queue().list_jobs()
    if not jobs:
        return "(no jobs)"
    lines = []
    for j in jobs:
        lines.append(
            f"[{j.status.upper():8}] {j.scheduled_at} | {j.profile} | "
            f"tags={j.tags or '—'} | id={j.id[:8]}..."
        )
    return "\n".join(lines)


def cancel_job(job_id: str) -> str:
    ok = get_queue().cancel_job(job_id.strip())
    return "Cancelled" if ok else f"Job not found: {job_id}"


# ---------------------------------------------------------------------------
# Content Roadmap tab helper functions
# ---------------------------------------------------------------------------

def add_roadmap_entry(title: str, tags: str, profile: str, notes: str) -> str:
    if not title.strip():
        return "Error: Title is required"
    try:
        e = get_roadmap().add_entry(title.strip(), tags.strip(), profile, notes.strip())
        return f"Added: {e.id[:8]}... — {e.title}"
    except Exception as ex:
        return f"Error: {ex}"


def list_roadmap(status_filter: str) -> list[list[str]]:
    entries = get_roadmap().list_entries(
        status_filter=None if status_filter == "all" else status_filter
    )
    if not entries:
        return [["—", "No entries", "—", "—", "—"]]
    rows = []
    for i, e in enumerate(entries, 1):
        rows.append([
            str(i),
            e.title,
            e.status.upper(),
            e.tags or "—",
            e.id[:8],
        ])
    return rows


def _find_entry_id(partial_id: str) -> Optional[str]:
    """Match entry by full id or 8-char prefix."""
    partial = partial_id.strip()
    for e in get_roadmap().list_entries():
        if e.id == partial or e.id.startswith(partial):
            return e.id
    return None


def update_roadmap_status(entry_id: str, new_status: str) -> str:
    full_id = _find_entry_id(entry_id)
    if not full_id:
        return f"Not found: {entry_id}"
    ok = get_roadmap().update_status(full_id, new_status)
    return "Updated" if ok else "Failed"


def delete_roadmap_entry(entry_id: str) -> str:
    full_id = _find_entry_id(entry_id)
    if not full_id:
        return f"Not found: {entry_id}"
    ok = get_roadmap().delete_entry(full_id)
    return "Deleted" if ok else "Failed"


def move_entry_up(entry_id: str) -> str:
    full_id = _find_entry_id(entry_id)
    if not full_id:
        return f"Not found: {entry_id}"
    return "Moved up" if get_roadmap().move_up(full_id) else "Already at top"


def move_entry_down(entry_id: str) -> str:
    full_id = _find_entry_id(entry_id)
    if not full_id:
        return f"Not found: {entry_id}"
    return "Moved down" if get_roadmap().move_down(full_id) else "Already at bottom"


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------

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
            # ------------------------------------------------------------------
            # Execute tab — streaming pipeline launch
            # ------------------------------------------------------------------
            with gr.Tab("Execute"):
                gr.Markdown("### Run Pipeline")
                with gr.Row():
                    exec_pipeline = gr.Dropdown(
                        choices=["Study Video", "TikTok Tutorial"],
                        value="Study Video",
                        label="Pipeline",
                    )
                    exec_out = gr.Textbox(label="Output Path", value="out/video.mp4")
                exec_tags = gr.Textbox(
                    label="Tags (comma-separated, optional — triggers AI prompt generation)",
                    placeholder="lofi, rain, cozy, study",
                )
                exec_btn = gr.Button("Launch Pipeline", variant="primary")
                exec_output = gr.Textbox(
                    label="Pipeline Output", lines=20, interactive=False,
                    autoscroll=True,
                )
                exec_btn.click(
                    fn=stream_pipeline,
                    inputs=[exec_pipeline, exec_out, exec_tags],
                    outputs=[exec_output],
                )

                gr.Markdown("### Execution History (persists across reloads)")
                exec_history = gr.Dataframe(
                    headers=["Time", "Status", "Pipeline", "Tags", "Output"],
                    datatype=["str", "str", "str", "str", "str"],
                    col_count=(5, "fixed"),
                    interactive=False,
                    value=format_history(),
                )
                exec_refresh_btn = gr.Button("Refresh History")
                exec_refresh_btn.click(fn=lambda: format_history(), outputs=[exec_history])

            # ------------------------------------------------------------------
            # Video Settings tab
            # ------------------------------------------------------------------
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

            # ------------------------------------------------------------------
            # Post-Production tab
            # ------------------------------------------------------------------
            with gr.Tab("Post-Production"):
                watermark_on = gr.Checkbox(label="Watermark", value=False)
                watermark_txt = gr.Textbox(label="Watermark Text")
                subtitles_on = gr.Checkbox(label="Burn Subtitles", value=False)

            # ------------------------------------------------------------------
            # Publishing tab
            # ------------------------------------------------------------------
            with gr.Tab("Publishing"):
                yt_enabled = gr.Checkbox(label="YouTube Upload", value=False)
                yt_title = gr.Textbox(label="YouTube Title")
                yt_desc = gr.Textbox(label="YouTube Description", lines=3)
                yt_tags = gr.Textbox(label="Tags (comma-separated)")
                yt_privacy = gr.Dropdown(choices=["private", "unlisted", "public"], value="private", label="Privacy")

            # ------------------------------------------------------------------
            # Notifications tab
            # ------------------------------------------------------------------
            with gr.Tab("Notifications"):
                gr.Markdown("*Discord/Slack webhook URLs are loaded from environment variables (`NOTF_DISCORD_WEBHOOK_URL`, `NOTF_SLACK_WEBHOOK_URL`). No need to set them here.*")
                approval = gr.Checkbox(label="Require Approval Before Publish", value=True)

            # ------------------------------------------------------------------
            # Schedule tab
            # ------------------------------------------------------------------
            with gr.Tab("Schedule"):
                gr.Markdown("### Queue a Video for Later")
                with gr.Row():
                    sched_profile = gr.Dropdown(
                        choices=list_profiles(),
                        value="(default)",
                        label="Profile",
                    )
                    sched_tags = gr.Textbox(
                        label="Tags (optional)",
                        placeholder="lofi, rain, cozy",
                    )
                with gr.Row():
                    sched_out = gr.Textbox(label="Output Path", value="out/video.mp4")
                    sched_datetime = gr.Textbox(
                        label="Scheduled At (ISO 8601)",
                        placeholder="2026-04-01T22:00:00",
                    )
                sched_add_btn = gr.Button("Add to Queue", variant="primary")
                sched_status = gr.Textbox(label="Status", interactive=False)
                gr.Markdown("### Job Queue")
                sched_refresh_btn = gr.Button("Refresh")
                sched_jobs_display = gr.Textbox(
                    label="Jobs", lines=10, interactive=False,
                )
                sched_cancel_id = gr.Textbox(label="Job ID to Cancel")
                sched_cancel_btn = gr.Button("Cancel Job")
                sched_cancel_status = gr.Textbox(label="Cancel Status", interactive=False)

                sched_add_btn.click(fn=add_scheduled_job,
                    inputs=[sched_profile, sched_tags, sched_out, sched_datetime],
                    outputs=[sched_status])
                sched_refresh_btn.click(fn=list_jobs_display, inputs=[], outputs=[sched_jobs_display])
                sched_cancel_btn.click(fn=cancel_job, inputs=[sched_cancel_id], outputs=[sched_cancel_status])

            # ------------------------------------------------------------------
            # Content Roadmap tab
            # ------------------------------------------------------------------
            with gr.Tab("Content Roadmap"):
                gr.Markdown("### Add Video to Roadmap")
                with gr.Row():
                    rm_title = gr.Textbox(label="Title")
                    rm_profile = gr.Dropdown(choices=list_profiles(), value="(default)", label="Profile")
                with gr.Row():
                    rm_tags = gr.Textbox(label="Tags", placeholder="lofi, rain, cozy")
                    rm_notes = gr.Textbox(label="Notes")
                rm_add_btn = gr.Button("Add Entry", variant="primary")
                rm_add_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("### Roadmap")
                with gr.Row():
                    rm_filter = gr.Dropdown(
                        choices=["all", "planned", "producing", "published"],
                        value="all",
                        label="Filter by Status",
                    )
                    rm_refresh_btn = gr.Button("Refresh")
                rm_display = gr.Dataframe(
                    headers=["#", "Title", "Status", "Tags", "ID"],
                    datatype=["str", "str", "str", "str", "str"],
                    col_count=(5, "fixed"),
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### Update Entry")
                with gr.Row():
                    rm_entry_id = gr.Textbox(label="Entry ID (first 8 chars OK)")
                    rm_new_status = gr.Dropdown(
                        choices=["planned", "producing", "published"],
                        value="planned",
                        label="New Status",
                    )
                rm_status_btn = gr.Button("Update Status")
                rm_delete_btn = gr.Button("Delete Entry")
                with gr.Row():
                    rm_move_up_btn = gr.Button("Move Up")
                    rm_move_down_btn = gr.Button("Move Down")
                rm_action_status = gr.Textbox(label="Action Status", interactive=False)

                rm_add_btn.click(fn=add_roadmap_entry,
                    inputs=[rm_title, rm_tags, rm_profile, rm_notes], outputs=[rm_add_status])
                rm_refresh_btn.click(fn=list_roadmap, inputs=[rm_filter], outputs=[rm_display])
                rm_filter.change(fn=list_roadmap, inputs=[rm_filter], outputs=[rm_display])
                rm_status_btn.click(fn=update_roadmap_status,
                    inputs=[rm_entry_id, rm_new_status], outputs=[rm_action_status])
                rm_delete_btn.click(fn=delete_roadmap_entry,
                    inputs=[rm_entry_id], outputs=[rm_action_status])
                rm_move_up_btn.click(fn=move_entry_up, inputs=[rm_entry_id], outputs=[rm_action_status])
                rm_move_down_btn.click(fn=move_entry_down, inputs=[rm_entry_id], outputs=[rm_action_status])

        # ------------------------------------------------------------------
        # Save config row (below all tabs)
        # ------------------------------------------------------------------
        with gr.Row():
            save_btn = gr.Button("Save Config", variant="primary")
            save_status = gr.Textbox(label="Status", interactive=False)

        # Wire load/save events
        all_fields = [
            profile_name, style_prompt, music_prompt, mood, duration, resolution,
            quality, scenes, watermark_on, watermark_txt, subtitles_on,
            yt_enabled, yt_title, yt_desc, yt_tags, yt_privacy,
            approval,
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
                vals["require_approval"],
            ]

        load_btn.click(fn=on_load, inputs=[profile_dropdown], outputs=all_fields)
        save_btn.click(fn=save_config, inputs=all_fields, outputs=[save_status])

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="127.0.0.1", server_port=7860)
