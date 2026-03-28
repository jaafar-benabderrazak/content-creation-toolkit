"""
Faceless Tech & AI TikTok — Fully Automated Pipeline (Python)
------------------------------------------------------------
End‑to‑end script that:
  1) generates short tech/AI tutorial scripts with OpenAI,
  2) synthesizes a natural voiceover (OpenAI TTS or ElevenLabs fallback),
  3) assembles a vertical 1080x1920 video with captions using MoviePy + PIL,
  4) autogenerates a caption + hashtags,
  5) (optionally) posts directly to TikTok via the Content Posting API.*

*Direct posting requires: TikTok Developer app, `video.publish` scope, and (for public visibility) passing TikTok’s audit. See docs.

Tested with Python 3.10+.

Install (suggested virtualenv):
    pip install moviepy pillow pydub numpy requests pyyaml openai elevenlabs

Also install ffmpeg on your system (MoviePy & pydub need it):
  - macOS (brew):  brew install ffmpeg
  - Ubuntu:        sudo apt-get install ffmpeg
  - Windows (choco): choco install ffmpeg

Environment variables expected:
  OPENAI_API_KEY           — for OpenAI script + optional TTS
  ELEVEN_API_KEY           — for ElevenLabs TTS (fallback)
  TIKTOK_ACCESS_TOKEN      — OAuth access token for TikTok Content Posting API (video.publish scope)

Folder structure (auto-created if missing):
  ./assets/         — background images/videos, music (optional)
  ./out/            — final mp4s land here
  ./tmp/            — intermediate audio/image files

Run examples:
  python tiktok_ai_tutorial_bot.py --topics "3 free AI tools for students" "Automate Excel with ChatGPT" --post
  python tiktok_ai_tutorial_bot.py --from-file topics.txt --count 3

Cron (daily 18:30):
  30 18 * * * /usr/bin/python /path/to/tiktok_ai_tutorial_bot.py --from-file /path/to/topics.txt --count 1 --post >> /var/log/tiktok_bot.log 2>&1
"""
from __future__ import annotations

import os
import io
import re
import math
import json
import time
import uuid
import yaml
import glob
import shutil
import random
import string
import logging
import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydub import AudioSegment
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
)

# Optional SDKs (fail gracefully if not configured)
try:
    from openai import OpenAI  # Official OpenAI Python SDK
except Exception:
    OpenAI = None  # type: ignore

try:
    from elevenlabs import ElevenLabs, Voice
except Exception:
    ElevenLabs = None  # type: ignore

# --------------- Config ---------------
@dataclass
class Style:
    width: int = 1080
    height: int = 1920
    bg_blur: int = 6  # blur radius when using image backgrounds
    margin: int = 60
    title_font_path: Optional[str] = None  # e.g., assets/Inter-ExtraBold.ttf
    body_font_path: Optional[str] = None   # e.g., assets/Inter-SemiBold.ttf
    title_size: int = 72
    body_size: int = 54
    text_color: Tuple[int, int, int] = (255, 255, 255)
    shadow_color: Tuple[int, int, int] = (0, 0, 0)
    shadow_offset: Tuple[int, int] = (2, 2)
    caption_max_chars: int = 2200  # TikTok caption limit

@dataclass
class RenderCfg:
    fps: int = 30
    bitrate: str = "6000k"  # good balance for 1080x1920
    audio_bitrate: str = "160k"

@dataclass
class BotCfg:
    voice: str = "alloy"  # OpenAI TTS voice alias, or ElevenLabs voice id/name
    use_elevenlabs: bool = False  # if True, prefer ElevenLabs over OpenAI TTS
    music_path: Optional[str] = None  # optional background music file
    music_volume_db: float = -18.0
    
    watermark_text: Optional[str] = "@TechAIHacks"  # set None to disable

# --------------- Utilities ---------------
ASSETS = os.path.join(os.getcwd(), "assets")
OUT = os.path.join(os.getcwd(), "out")
TMP = os.path.join(os.getcwd(), "tmp")
FALLBACK_FONT = ImageFont.load_default()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_dirs():
    for p in (ASSETS, OUT, TMP):
        os.makedirs(p, exist_ok=True)


def slugify(text: str, max_len: int = 64) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return s[:max_len] or uuid.uuid4().hex[:8]


# --------------- Idea & script generation ---------------
OPENAI_MODEL_RESPONSES = os.getenv("OPENAI_MODEL_RESPONSES", "gpt-4o-mini")
OPENAI_MODEL_TTS = os.getenv("OPENAI_MODEL_TTS", "gpt-4o-mini-tts")


def openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        logging.warning(f"OpenAI client init failed: {e}")
        return None


def generate_tutorial_script(topic: str, client: Optional[OpenAI]) -> dict:
    """Return a dict with keys: title, bullets (list[str]), cta, hashtags.
    Falls back to simple templating if OpenAI is not configured.
    """
    if client is None:
        logging.warning("OpenAI not configured — using fallback script template.")
        title = f"{topic} — in 3 steps"
        bullets = [
            f"Step 1: What problem does {topic} solve?",
            "Step 2: The exact clicks/commands to do it",
            "Step 3: One pro tip & a gotcha",
        ]
        return {
            "title": title,
            "bullets": bullets,
            "cta": "Follow for daily Tech & AI hacks!",
            "hashtags": ["#AI", "#Tech", "#Productivity", "#Tutorial", "#LearnOnTikTok"],
        }

    prompt = f"""
    Create a 35–45 second TikTok tutorial ABOUT this topic: "{topic}".
    Return STRICT JSON with fields: title (<=70 chars), bullets (3-5 short imperative bullets),
    cta (short), hashtags (5-8 lowercase tags, no spaces, each starts with #, relevant to topic).
    Style: punchy, plain language, beginner-friendly, no emojis.
    """
    try:
        resp = client.responses.create(
            model=OPENAI_MODEL_RESPONSES,
            input=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        # Extract text safely
        text = resp.output_text if hasattr(resp, "output_text") else json.dumps(resp.dict())
        # Find JSON block in text
        m = re.search(r"\{[\s\S]*\}", text)
        data = json.loads(m.group(0)) if m else {}
        # Basic validation
        title = str(data.get("title") or f"{topic} in 60 seconds")[:70]
        bullets = [b.strip() for b in data.get("bullets", []) if str(b).strip()][:5]
        if not bullets:
            bullets = ["Open the tool", "Do the 3 key clicks", "Show one pro tip"]
        hashtags = [h if h.startswith('#') else f"#{h}" for h in data.get("hashtags", [])][:8]
        cta = str(data.get("cta") or "Follow for daily AI hacks!")
        return {"title": title, "bullets": bullets, "cta": cta, "hashtags": hashtags}
    except Exception as e:
        logging.error(f"OpenAI script generation failed: {e}")
        return generate_tutorial_script(topic, None)


# --------------- Text-to-Speech ---------------

def tts_openai(text: str, voice: str, outfile: str) -> str:
    client = openai_client()
    if client is None:
        raise RuntimeError("OpenAI SDK not available or OPENAI_API_KEY not set")
    try:
        # Audio API: text to speech to MP3 (supported by MoviePy/Pydub)
        with client.audio.speech.with_streaming_response.create(
            model=OPENAI_MODEL_TTS,
            voice=voice,
            input=text,
            format="mp3",
        ) as response:
            response.stream_to_file(outfile)
        return outfile
    except Exception as e:
        raise RuntimeError(f"OpenAI TTS failed: {e}")


def tts_elevenlabs(text: str, voice: str, outfile: str) -> str:
    if ElevenLabs is None:
        raise RuntimeError("ElevenLabs SDK not installed")
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVEN_API_KEY not set")
    try:
        el = ElevenLabs(api_key=api_key)
        # Resolve voice id by name if possible
        voice_id = None
        try:
            vs = el.voices.get_all().voices  # type: ignore
            for v in vs:
                if v.name.lower() == voice.lower() or v.voice_id == voice:
                    voice_id = v.voice_id
                    break
        except Exception:
            pass
        audio = el.text_to_speech.convert(
            voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",  # default Rachel ID if accessible
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=text,
        )
        with open(outfile, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        return outfile
    except Exception as e:
        raise RuntimeError(f"ElevenLabs TTS failed: {e}")


def synth_voiceover(script: dict, cfg: BotCfg, out_basename: str) -> str:
    text = f"{script['title']}\n" + "\n".join(script["bullets"]) + f"\n{script['cta']}"
    outfile = os.path.join(TMP, f"{out_basename}_voice.mp3")
    if cfg.use_elevenlabs:
        try:
            return tts_elevenlabs(text, cfg.voice, outfile)
        except Exception as e:
            logging.warning(f"ElevenLabs TTS unavailable ({e}) — falling back to OpenAI.")
    return tts_openai(text, cfg.voice, outfile)


# --------------- Visuals & captions ---------------

def choose_background(style: Style) -> Image.Image:
    """Pick a random image from assets or generate a soft gradient."""
    img_paths = [p for p in glob.glob(os.path.join(ASSETS, "*.jpg")) + glob.glob(os.path.join(ASSETS, "*.png"))]
    if img_paths:
        img = Image.open(random.choice(img_paths)).convert("RGB")
        img = img.resize((style.width, style.height)).filter(ImageFilter.GaussianBlur(style.bg_blur))
        return img
    # Generate gradient
    base = Image.new("RGB", (style.width, style.height), (18, 18, 24))
    top = Image.new("RGB", (style.width, style.height), (36, 36, 52))
    mask = Image.linear_gradient("L").resize((style.width, style.height)).rotate(90)
    return Image.composite(top, base, mask)


def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception as e:
            logging.warning(f"Failed to load font {path}: {e}")
    return FALLBACK_FONT


def draw_text_block(img: Image.Image, text: str, font: ImageFont.ImageFont, max_width: int, fill: Tuple[int, int, int], shadow: Tuple[int, int, int] | None = (0, 0, 0), shadow_offset: Tuple[int, int] = (2, 2)) -> Image.Image:
    """Render multiline text onto a transparent RGBA image capped at max_width."""
    # Simple word wrap using PIL to measure
    words = text.split()
    lines = []
    line = []
    draw = ImageDraw.Draw(img)
    for w in words:
        test = " ".join(line + [w])
        w_px, _ = draw.textsize(test, font=font)
        if w_px <= max_width or not line:
            line.append(w)
        else:
            lines.append(" ".join(line))
            line = [w]
    if line:
        lines.append(" ".join(line))

    # Create transparent layer big enough
    line_height = int(font.size * 1.25)
    h = line_height * len(lines)
    w = max(draw.textsize(l, font=font)[0] for l in lines) if lines else max_width
    layer = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer)
    y = 0
    for l in lines:
        if shadow:
            d2.text((shadow_offset[0], y + shadow_offset[1]), l, font=font, fill=shadow)
        d2.text((0, y), l, font=font, fill=fill)
        y += line_height
    return layer


def compose_poster(script: dict, style: Style, cfg: BotCfg, out_basename: str) -> str:
    bg = choose_background(style)
    canvas = bg.copy()

    title_font = load_font(style.title_font_path, style.title_size)
    body_font = load_font(style.body_font_path, style.body_size)

    # Title at top
    title_layer = draw_text_block(canvas, script["title"], title_font, style.width - 2 * style.margin, style.text_color, style.shadow_color, style.shadow_offset)
    canvas.paste(title_layer, (style.margin, style.margin), title_layer)

    # Bullets in middle
    bullets_text = "\n".join([f"• {b}" for b in script["bullets"]])
    bt_layer = draw_text_block(canvas, bullets_text, body_font, style.width - 2 * style.margin, style.text_color, style.shadow_color, style.shadow_offset)
    mid_y = style.margin + 240
    canvas.paste(bt_layer, (style.margin, mid_y), bt_layer)

    # CTA at bottom
    cta_layer = draw_text_block(canvas, script["cta"], body_font, style.width - 2 * style.margin, style.text_color, style.shadow_color, style.shadow_offset)
    canvas.paste(cta_layer, (style.margin, style.height - cta_layer.size[1] - style.margin - 120), cta_layer)

    # Watermark
    if cfg.watermark_text:
        wm_font = load_font(style.body_font_path, 36)
        wm_layer = draw_text_block(canvas, cfg.watermark_text, wm_font, 800, (220, 220, 220), (0, 0, 0), (2, 2))
        wm = wm_layer.resize((int(wm_layer.width * 0.9), int(wm_layer.height * 0.9)))
        canvas.paste(wm, (style.width - wm.width - style.margin, style.height - wm.height - style.margin), wm)

    poster_path = os.path.join(TMP, f"{out_basename}_poster.png")
    canvas.save(poster_path)
    return poster_path


# --------------- Subtitles ---------------

def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def make_srt(lines: List[Tuple[str, float, float]]) -> str:
    """lines: list of (text, start_sec, end_sec). Returns SRT text."""
    def fmt_ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec - int(sec)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    out = []
    for i, (txt, s, e) in enumerate(lines, start=1):
        out.append(str(i))
        out.append(f"{fmt_ts(s)} --> {fmt_ts(e)}")
        out.append(txt)
        out.append("")
    return "\n".join(out)


def auto_subtitles_from_audio(script: dict, audio_path: str) -> str:
    audio = AudioSegment.from_file(audio_path)
    duration = len(audio) / 1000.0  # seconds

    # We chunk: title (20%), bullets (60%), cta (20%)
    title = script["title"]
    bullets = script["bullets"]
    cta = script["cta"]

    segments: List[Tuple[str, float, float]] = []
    t0 = 0.0

    def alloc(texts: List[str] | str, frac: float, start: float) -> float:
        nonlocal segments
        target = duration * frac
        if isinstance(texts, str):
            texts = [texts]
        total_chars = sum(len(t) for t in texts) or 1
        cur = start
        for t in texts:
            seg_dur = max(1.2, target * (len(t) / total_chars))
            segments.append((t, cur, cur + seg_dur))
            cur += seg_dur
        return cur

    t0 = alloc([title], 0.2, t0)
    bullet_lines = [f"• {b}" for b in bullets]
    t0 = alloc(bullet_lines, 0.6, t0)
    t0 = alloc([cta], 0.2, t0)

    # Clamp to audio duration
    segments = [(txt, s, min(e, duration)) for (txt, s, e) in segments if s < duration]

    srt_text = make_srt(segments)
    srt_path = os.path.join(TMP, os.path.basename(audio_path).replace(".mp3", ".srt"))
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_text)
    return srt_path


# --------------- Video assembly ---------------

def assemble_video(poster_path: str, audio_path: str, style: Style, cfg: BotCfg, render: RenderCfg, out_basename: str) -> str:
    # Convert the poster into a video with subtle motion (Ken Burns) for visual interest
    base_img = Image.open(poster_path).convert("RGB")

    # Create slow zoom frames via MoviePy's ImageClip set with slight resize/position animation
    clip_img = ImageClip(poster_path).set_duration(AudioSegment.from_file(audio_path).duration_seconds)

    # Add audio
    voice = AudioFileClip(audio_path)

    # Optional music (ducked under voice)
    if cfg.music_path and os.path.exists(cfg.music_path):
        music = AudioFileClip(cfg.music_path).volumex(10 ** (cfg.music_volume_db / 20.0))
        # Loop music if shorter than voice
        music = music.audio_loop(duration=voice.duration)
        audio_mix = voice.audio_fadein(0.05).fx(lambda a: a)  # placeholder to keep ref
        # Simple manual mix: set audio clips and their volumes; CompositeAudioClip often flaky across versions
        from moviepy.audio.AudioClip import CompositeAudioClip
        audio = CompositeAudioClip([voice, music])
    else:
        audio = voice

    # Motion: zoom from 100% to 107%
    def zoom(get_frame, t):
        frame = get_frame(t)
        # Compute scale factor linearly over duration
        d = max(clip_img.duration, 1.0)
        scale = 1.0 + 0.07 * (t / d)
        w, h = frame.shape[1], frame.shape[0]
        nw, nh = int(w * scale), int(h * scale)
        img = Image.fromarray(frame).resize((nw, nh), Image.LANCZOS)
        # center-crop back to original size
        x0 = (nw - w) // 2
        y0 = (nh - h) // 2
        img = img.crop((x0, y0, x0 + w, y0 + h))
        return np.array(img)

    anim = clip_img.fl(zoom, apply_to=["mask"]).set_audio(audio)

    # Export
    out_path = os.path.join(OUT, f"{out_basename}.mp4")
    anim.write_videofile(
        out_path,
        fps=render.fps,
        codec="libx264",
        audio_codec="aac",
        bitrate=render.bitrate,
        audio_bitrate=render.audio_bitrate,
        threads=4,
        preset="medium",
        temp_audiofile=os.path.join(TMP, f"{out_basename}_temp-audio.m4a"),
        remove_temp=True,
        verbose=False,
        logger=None,
    )
    return out_path


# --------------- Caption & hashtags ---------------

def build_caption(script: dict) -> str:
    base = f"{script['title']} — {script['cta']}\n"
    tags = " ".join(script["hashtags"]) if script.get("hashtags") else ""
    caption = (base + tags).strip()
    # TikTok limit guard
    return caption[: Style().caption_max_chars]


# --------------- TikTok Direct Post API ---------------
TT_BASE = "https://open.tiktokapis.com/v2"


def tiktok_direct_post(video_path: str, caption: str, privacy: str = "PUBLIC_TO_EVERYONE") -> dict:
    """Directly post a video to TikTok via Content Posting API.
    Requirements: TIKTOK_ACCESS_TOKEN env var with video.publish scope; app may be restricted to private visibility until audited by TikTok.
    Returns TikTok publish status payload.
    """
    token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("TIKTOK_ACCESS_TOKEN not set (OAuth with video.publish scope required)")

    # 1) Query creator info (optional but recommended by TikTok UX guidelines)
    try:
        r = requests.post(
            f"{TT_BASE}/post/publish/creator_info/query/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json={},
            timeout=30,
        )
        r.raise_for_status()
    except Exception as e:
        logging.warning(f"TikTok creator_info query failed: {e}")

    size = os.path.getsize(video_path)

    # 2) Init direct post
    init_payload = {
        "post_info": {
            "title": caption,
            "privacy_level": privacy,  # PUBLIC_TO_EVERYONE | MUTUAL_FOLLOW_FRIENDS | SELF_ONLY
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1200,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": size,  # single-chunk PUT; for large files you can chunk
            "total_chunk_count": 1,
        },
    }

    r = requests.post(
        f"{TT_BASE}/post/publish/video/init/",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
        json=init_payload,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json().get("data", {})
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")
    if not upload_url or not publish_id:
        raise RuntimeError(f"Unexpected init response: {r.text}")

    # 3) PUT video bytes to upload_url
    with open(video_path, "rb") as f:
        body = f.read()
    headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{size-1}/{size}",
    }
    up = requests.put(upload_url, headers=headers, data=body, timeout=300)
    if up.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed: {up.status_code} {up.text}")

    # 4) Poll status
    for _ in range(20):  # ~20 * 5s = ~100s max
        time.sleep(5)
        st = requests.post(
            f"{TT_BASE}/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json={"publish_id": publish_id},
            timeout=30,
        )
        try:
            st.raise_for_status()
        except Exception:
            continue
        payload = st.json()
        status = (payload.get("data") or {}).get("status")
        if status in {"PUBLISHED", "FAILED", "REJECTED", "CANCELED"}:
            return payload
    return {"data": {"status": "TIMEOUT", "publish_id": publish_id}, "error": {"code": "timeout", "message": "Polling timed out"}}


# --------------- Pipeline ---------------

def build_one(topic: str, style: Style, render: RenderCfg, cfg: BotCfg, post: bool) -> Tuple[str, str]:
    ensure_dirs()
    base = slugify(topic)
    logging.info(f"Topic: {topic}")

    client = openai_client()
    script = generate_tutorial_script(topic, client)
    voice_mp3 = synth_voiceover(script, cfg, base)
    poster_png = compose_poster(script, style, cfg, base)
    final_mp4 = assemble_video(poster_png, voice_mp3, style, cfg, render, base)

    caption = build_caption(script)

    if post:
        try:
            resp = tiktok_direct_post(final_mp4, caption)
            logging.info(f"TikTok post status: {json.dumps(resp, ensure_ascii=False)}")
        except Exception as e:
            logging.error(f"Posting failed: {e}")

    return final_mp4, caption


# --------------- CLI ---------------

def parse_args():
    p = argparse.ArgumentParser(description="Faceless Tech & AI TikTok — Automated Pipeline")
    p.add_argument("--topics", nargs="*", help="One or more topics to generate videos for")
    p.add_argument("--from-file", dest="from_file", help="Path to a text file with one topic per line")
    p.add_argument("--count", type=int, default=1, help="Number of topics to take from file (default 1)")
    p.add_argument("--post", action="store_true", help="Post to TikTok after rendering")
    p.add_argument("--voice", default=None, help="Voice name/id (overrides cfg)")
    p.add_argument("--music", default=None, help="Optional path to background music")
    p.add_argument("--title-font", dest="title_font", default=None, help="Path to title TTF/OTF font")
    p.add_argument("--body-font", dest="body_font", default=None, help="Path to body TTF/OTF font")
    p.add_argument("--config", type=str, default=None,
                   help="Path to YAML config file (PipelineConfig format)")
    return p.parse_args()


def main():
    args = parse_args()

    # Load pipeline config if provided (read-only for now; Phase 6 wires behavior)
    pipeline_config = None
    if args.config:
        from config import PipelineConfig
        pipeline_config = PipelineConfig.from_yaml(args.config)
        print(f"[Config] Loaded profile: {pipeline_config.profile}")

    topics: List[str] = []
    if args.topics:
        topics.extend(args.topics)
    if args.from_file and os.path.exists(args.from_file):
        with open(args.from_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        topics.extend(lines[: args.count])

    if not topics:
        # Defaults if nothing provided
        topics = [
            "3 free AI tools that automate boring tasks",
            "How to summarize PDFs with ChatGPT (free)",
            "5 Chrome extensions every developer should know",
        ]

    style = Style(
        title_font_path=args.title_font or os.path.join(ASSETS, "Inter-ExtraBold.ttf"),
        body_font_path=args.body_font or os.path.join(ASSETS, "Inter-SemiBold.ttf"),
    )
    render = RenderCfg()
    cfg = BotCfg(
        voice=os.getenv("BOT_VOICE", "alloy") if args.voice is None else args.voice,
        use_elevenlabs=bool(os.getenv("USE_ELEVENLABS", "0") == "1"),
        music_path=args.music or os.getenv("MUSIC_PATH"),
    )

    for t in topics:
        try:
            mp4, cap = build_one(t, style, render, cfg, post=args.post)
            logging.info(f"DONE — {mp4}\nCAPTION: {cap}")
        except Exception as e:
            logging.exception(f"Failed topic '{t}': {e}")


if __name__ == "__main__":
    main()
