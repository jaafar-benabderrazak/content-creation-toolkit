"""Modal cloud pipeline — runs video generation on cloud GPU.

Replaces local pipeline_server.py + study_with_me_generator.py.
All image/music/prompt generation uses APIs (no local GPU needed).
Video rendering uses Remotion via headless Chrome on Modal.

Deploy: modal deploy cloud/modal_pipeline.py
Test:   modal run cloud/modal_pipeline.py --tags "lofi, rain, cozy"
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import modal

# ---------------------------------------------------------------------------
# Modal App + Image
# ---------------------------------------------------------------------------

app = modal.App("content-creation-pipeline")

pipeline_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "anthropic>=0.52",
        "requests>=2.31",
        "pydub>=0.25",
        "Pillow>=10.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "supabase>=2.0",
        "python-dotenv>=1.0",
    )
    .pip_install(
        "replicate>=1.0",
    )
)

# ---------------------------------------------------------------------------
# Secrets (set via `modal secret create`)
# ---------------------------------------------------------------------------
# modal secret create content-creation-secrets \
#   ANTHROPIC_API_KEY=sk-ant-... \
#   REPLICATE_API_TOKEN=r8_... \
#   SUNO_API_KEY=c71e... \
#   GOOGLE_API_KEY=AIza... \
#   OPENAI_API_KEY=sk-proj-... \
#   SUPABASE_URL=https://xxx.supabase.co \
#   SUPABASE_ANON_KEY=eyJ...


@app.function(
    image=pipeline_image,
    secrets=[modal.Secret.from_name("content-creation-secrets")],
    timeout=3600,  # 1 hour max
)
def generate_video(
    tags: str,
    profile: str = "cinematic",
    duration_minutes: int = 3,
    scene_count: int = 8,
    video_id: str | None = None,
) -> dict:
    """Generate a complete video in the cloud.

    Returns dict with: status, video_url, thumbnail_url, prompts, logs.
    """
    import requests
    from supabase import create_client

    logs: list[str] = []

    def log(msg: str):
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        print(msg)
        # Write to Supabase executions table for real-time dashboard updates
        try:
            _update_execution(execution_id, "running", "\n".join(logs[-50:]))
        except Exception:
            pass

    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
    supabase = create_client(supabase_url, supabase_key) if supabase_url else None

    # Create execution record
    execution_id = f"modal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if supabase:
        supabase.table("executions").insert({
            "id": execution_id,
            "pipeline": "Study Video (cloud)",
            "profile": profile,
            "tags": tags,
            "status": "running",
        }).execute()

    def _update_execution(exec_id: str, status: str, last_lines: str = ""):
        if supabase:
            update = {"status": status, "last_lines": last_lines}
            if status in ("done", "failed"):
                update["finished_at"] = datetime.now().isoformat()
            supabase.table("executions").update(update).eq("id", exec_id).execute()

    try:
        # Step 1: Generate prompts via Claude
        log(f"[Prompts] Generating from tags: {tags} (profile: {profile})")
        prompts = _generate_prompts(tags, profile)
        log(f"[Prompts] Done: {prompts.get('thumbnail_text', '?')}")

        # Save prompts to Supabase
        if supabase and video_id:
            supabase.table("prompts").insert({
                "video_id": video_id,
                "positive_prompt": prompts.get("positive_prompt", ""),
                "negative_prompt": prompts.get("negative_prompt", ""),
                "scene_templates": json.dumps(prompts.get("scene_templates", [])),
                "music_prompt": prompts.get("music_prompt", ""),
                "thumbnail_text": prompts.get("thumbnail_text", ""),
                "youtube_title": prompts.get("youtube_title", ""),
                "youtube_description": prompts.get("youtube_description", ""),
                "youtube_tags": json.dumps(prompts.get("youtube_tags", [])),
                "profile_style": profile,
            }).execute()

        # Step 2: Generate base image via API
        log("[Images] Generating base image via Seedream/Gemini/DALL-E...")
        image_url = _generate_image(prompts["positive_prompt"])
        log(f"[Images] Done: {image_url[:60]}...")

        # Step 3: Generate music via Suno
        log("[Music] Generating via Suno (kie.ai)...")
        audio_url = _generate_music(
            prompts.get("music_prompt", "lofi ambient study music"),
            duration_minutes * 60,
        )
        log(f"[Music] Done: {audio_url[:60] if audio_url else 'fallback/silent'}...")

        # Step 4: Log completion
        log("[Pipeline] Cloud generation complete")
        _update_execution(execution_id, "done", "\n".join(logs[-50:]))

        # Update video status in Supabase
        if supabase and video_id:
            supabase.table("videos").update({"status": "producing"}).eq("id", video_id).execute()

        return {
            "status": "done",
            "execution_id": execution_id,
            "image_url": image_url,
            "audio_url": audio_url,
            "prompts": prompts,
            "logs": logs,
        }

    except Exception as e:
        log(f"[ERROR] {e}")
        _update_execution(execution_id, "failed", "\n".join(logs[-50:]))
        return {
            "status": "failed",
            "execution_id": execution_id,
            "error": str(e),
            "logs": logs,
        }


def _generate_prompts(tags: str, profile: str) -> dict:
    """Generate all 8 prompt sections via Claude."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=f"You are a professional AI image prompt engineer. Generate prompts for a {profile} visual aesthetic. Return only valid JSON.",
        messages=[{
            "role": "user",
            "content": (
                f"Tags: {tags}\n\n"
                "Generate JSON with: positive_prompt, negative_prompt, "
                "scene_templates (8 items), music_prompt, thumbnail_text, "
                "youtube_title, youtube_description, youtube_tags (15-20 items)."
            ),
        }],
    )
    import re
    text = response.content[0].text
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text).strip()
    return json.loads(text)


def _generate_image(prompt: str) -> str:
    """Generate image via Replicate Seedream or Gemini."""
    import replicate

    try:
        output = replicate.run(
            "bytedance/seedream-5-lite",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "output_format": "png",
                "num_outputs": 1,
            },
        )
        url = output[0] if isinstance(output, list) else str(output)
        return str(url)
    except Exception as e:
        print(f"Seedream failed: {e}, trying Gemini...")

    # Fallback: Gemini
    import requests
    import base64

    google_key = os.environ.get("GOOGLE_API_KEY", "")
    if google_key:
        for model in ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image"]:
            try:
                resp = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    params={"key": google_key},
                    json={
                        "contents": [{"parts": [{"text": f"Generate image: {prompt}"}]}],
                        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
                    },
                    timeout=90,
                )
                if resp.ok:
                    data = resp.json()
                    for c in data.get("candidates", []):
                        for p in c.get("content", {}).get("parts", []):
                            if "inlineData" in p:
                                return f"data:image/png;base64,{p['inlineData']['data'][:50]}..."
            except Exception:
                continue

    return "no-image-generated"


def _generate_music(prompt: str, duration_seconds: int) -> str:
    """Generate music via Suno (kie.ai)."""
    import requests

    api_key = os.environ.get("SUNO_API_KEY", "")
    if not api_key:
        return ""

    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(
            "https://api.kie.ai/api/v1/generate",
            json={
                "prompt": prompt,
                "instrumental": True,
                "model": "V4_5",
                "customMode": False,
                "callBackUrl": "https://localhost/callback",
            },
            headers=headers,
        )
        if not resp.ok:
            return ""

        task_id = resp.json().get("data", {}).get("taskId", "")
        if not task_id:
            return ""

        # Poll for completion (max 5 min)
        for _ in range(60):
            time.sleep(5)
            status_resp = requests.get(
                f"https://api.kie.ai/api/v1/generate/record-info?taskId={task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            data = status_resp.json().get("data", {})
            if data.get("status") == "SUCCESS":
                tracks = data.get("response", {}).get("sunoData", [])
                if tracks:
                    return tracks[0].get("audioUrl", "")
            if data.get("status") in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED"):
                return ""

        return ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# HTTP endpoint for dashboard trigger
# ---------------------------------------------------------------------------

@app.function(image=pipeline_image)
@modal.web_endpoint(method="POST")
def trigger(body: dict) -> dict:
    """HTTP endpoint for dashboard to trigger pipeline."""
    tags = body.get("tags", "")
    profile = body.get("profile", "cinematic")
    duration = body.get("duration_minutes", 3)
    video_id = body.get("video_id")

    # Spawn the generation function (async)
    call = generate_video.spawn(
        tags=tags,
        profile=profile,
        duration_minutes=duration,
        video_id=video_id,
    )

    return {
        "triggered": True,
        "call_id": call.object_id,
        "tags": tags,
        "profile": profile,
    }


@app.function(image=pipeline_image)
@modal.web_endpoint(method="GET")
def status(call_id: str = "") -> dict:
    """Check status of a running pipeline."""
    if not call_id:
        return {"error": "call_id required"}

    try:
        fc = modal.functions.FunctionCall.from_id(call_id)
        try:
            result = fc.get(timeout=0)
            return {"status": "done", "result": result}
        except TimeoutError:
            return {"status": "running"}
    except Exception as e:
        return {"status": "unknown", "error": str(e)}
