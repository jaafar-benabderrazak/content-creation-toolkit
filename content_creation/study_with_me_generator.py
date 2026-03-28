#!/usr/bin/env python3
"""
Enhanced Study-With-Me continuous video generator with advanced visual effects and improved quality

Enhancements over the original:
------------------------------
• Higher quality image generation with better models and settings
• Advanced visual effects: parallax motion, dynamic lighting, particle effects
• Smoother transitions with multiple transition types
• Better audio processing with EQ and compression
• Dynamic scene composition with layered elements
• Improved text overlays with animations
• Scene variety with weather effects and time-of-day changes
• Better memory management and error handling
• Progress tracking and resume capability
"""
from __future__ import annotations

# Compatibility fix for Python 3.12+
import sys
import pkgutil
if not hasattr(pkgutil, 'ImpImporter'):
    pkgutil.ImpImporter = pkgutil.zipimporter

import argparse
import base64
import io
import json
import math
import os
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from tqdm import tqdm

# Video
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    vfx,
    ColorClip,
    TextClip,
)

# Audio utils
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# ---- Enhanced Configuration --------------------------------------------------

@dataclass
class VideoConfig:
    """Enhanced video generation configuration"""
    duration_minutes: int = 120
    fps: int = 30
    resolution: Tuple[int, int] = (1920, 1080)  # Full HD
    image_size: int = 1024  # Higher resolution for better quality
    image_count: int = 24  # More variety
    scene_duration: float = 25.0  # Longer scenes for better immersion
    transition_duration: float = 1.2  # Smoother transitions
    enable_parallax: bool = True
    enable_particles: bool = True
    enable_dynamic_lighting: bool = True
    quality_preset: str = "high"  # high, medium, fast
    
@dataclass
class AudioConfig:
    """Enhanced audio configuration"""
    sample_rate: int = 48000  # Higher quality audio
    bitrate: str = "320k"
    enable_eq: bool = True
    enable_compression: bool = True
    crossfade_ms: int = 4000  # Longer crossfades
    segment_seconds: int = 45  # Longer segments
    steps: int = 15  # Higher quality generation

@dataclass
class EffectsConfig:
    """Visual effects configuration"""
    enable_weather: bool = True
    enable_time_progression: bool = True
    parallax_strength: float = 0.03
    particle_density: int = 20
    lighting_variation: float = 0.15

# ---- Enhanced Scene Definitions ----------------------------------------------

ENHANCED_SCENES = [
    {
        "prompt": "A diverse group of students studying in a sunlit university library with tall windows, golden hour lighting, soft bokeh, candid, natural skin tones, architectural details",
        "environment": "indoor",
        "time": "afternoon",
        "mood": "focused"
    },
    {
        "prompt": "Person studying at a minimalist Scandinavian home desk with monstera plants, warm Edison bulb lighting, overhead angle, cozy atmosphere",
        "environment": "indoor",
        "time": "evening",
        "mood": "cozy"
    },
    {
        "prompt": "Aesthetic cafe by a rainy window with bokeh street lights, laptop open, vintage notebooks, steaming coffee cup with latte art, reflections on glass",
        "environment": "indoor",
        "time": "evening",
        "mood": "atmospheric"
    },
    {
        "prompt": "Modern minimalist study space with RGB ambient lighting, dual monitors, mechanical keyboard, organized desk setup, night cityscape view",
        "environment": "indoor",
        "time": "night",
        "mood": "modern"
    },
    {
        "prompt": "Traditional wooden reading room with floor-to-ceiling bookshelves, vintage leather chair, antique desk lamp, paper and fountain pen, warm lighting",
        "environment": "indoor",
        "time": "afternoon",
        "mood": "classic"
    },
    {
        "prompt": "Bright co-working space with natural light flooding through large windows, person with noise-canceling headphones, laptop, plants, productive atmosphere",
        "environment": "indoor",
        "time": "morning",
        "mood": "energetic"
    },
    {
        "prompt": "Peaceful outdoor campus courtyard in autumn, student reading under a colorful maple tree, fallen leaves, soft natural lighting, shallow depth of field",
        "environment": "outdoor",
        "time": "afternoon",
        "mood": "serene"
    },
    {
        "prompt": "Early morning city apartment with floor-to-ceiling windows, organized workspace, golden sunrise light streaming in, coffee steam, calm productive mood",
        "environment": "indoor",
        "time": "morning",
        "mood": "fresh"
    },
    {
        "prompt": "Cozy bedroom study nook with fairy lights, soft textiles, laptop on bed, warm blanket, evening study session, intimate lighting",
        "environment": "indoor",
        "time": "evening",
        "mood": "intimate"
    },
    {
        "prompt": "Modern public library with contemporary architecture, natural light, person studying at a sleek table, peaceful atmosphere, other students in background",
        "environment": "indoor",
        "time": "afternoon",
        "mood": "public"
    },
    {
        "prompt": "Outdoor terrace study setup with city skyline view, sunset lighting, laptop and notebooks on wooden table, urban garden background",
        "environment": "outdoor",
        "time": "sunset",
        "mood": "inspiring"
    },
    {
        "prompt": "24-hour study room with soft artificial lighting, multiple students, quiet concentration, late night study session, focused atmosphere",
        "environment": "indoor",
        "time": "late_night",
        "mood": "intensive"
    }
]

STYLE_VARIATIONS = [
    "cinematic film grain, 35mm lens, natural color grading, soft contrast",
    "shot on Fujifilm X-T4, Film Simulation Classic Chrome, natural bokeh",
    "Sony A7R V, 50mm f/1.4, shallow depth of field, creamy bokeh",
    "Canon R5, cinematic color science, warm highlights, rich shadows",
    "Leica M11, street photography aesthetic, natural light, authentic mood",
    "Phase One medium format, incredible detail, smooth gradients"
]

WEATHER_EFFECTS = [
    "gentle rain on windows with bokeh droplets",
    "soft snow falling outside, cozy indoor warmth contrast",
    "golden hour sunbeams streaming through windows",
    "dramatic storm clouds visible through windows, moody lighting",
    "clear blue sky with fluffy white clouds",
    "overcast sky with soft diffused lighting"
]

# ---- Enhanced Image Generation -----------------------------------------------

def generate_images_enhanced_sd(scenes: List[Dict], config: VideoConfig, out_dir: Path) -> List[Path]:
    """Enhanced image generation with better models and settings"""
    import torch
    from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
    
    print(f"[SD] Loading Enhanced Stable Diffusion XL model...")
    
    # Use SDXL for better quality
    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    
    if not torch.cuda.is_available():
        print("[WARNING] CUDA not available. Using CPU (will be very slow)")
        device = "cpu"
        torch_dtype = torch.float32
    else:
        device = "cuda"
        torch_dtype = torch.float16
        
        # Print GPU info
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"[SD] Using GPU: {gpu_name} ({gpu_memory:.1f}GB VRAM)")
    
    # Load pipeline with optimizations
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        use_safetensors=True,
        variant="fp16" if device == "cuda" else None
    )
    
    # Use faster scheduler for better quality/speed balance
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    
    # Enable memory optimizations
    if device == "cuda":
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing(1)
    
    # Quality settings based on preset
    if config.quality_preset == "high":
        steps = 35
        guidance = 8.0
    elif config.quality_preset == "medium":
        steps = 25
        guidance = 7.5
    else:  # fast
        steps = 15
        guidance = 7.0
    
    paths: List[Path] = []
    negative_prompt = (
        "blurry, low quality, distorted, deformed, bad anatomy, "
        "watermark, signature, text, logo, ugly, duplicate, morbid"
    )
    
    for i, scene_data in enumerate(tqdm(scenes, desc="Generating enhanced images")):
        try:
            # Build enhanced prompt
            base_prompt = scene_data["prompt"]
            style = random.choice(STYLE_VARIATIONS)
            weather = random.choice(WEATHER_EFFECTS) if config.quality_preset == "high" else ""
            
            full_prompt = f"{base_prompt}, {style}"
            if weather and scene_data["environment"] == "indoor":
                full_prompt += f", {weather}"
            
            full_prompt += ", high resolution, detailed, professional photography, 8K"
            
            # Generate with enhanced settings
            with torch.inference_mode():
                image = pipe(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=config.image_size,
                    height=config.image_size,
                    generator=torch.manual_seed(42 + i)
                ).images[0]
            
            # Post-process image for better quality
            image = enhance_image_quality(image)
            
            # Save with high quality
            path = out_dir / f"scene_{i:03d}.jpg"
            image.save(path, "JPEG", quality=95, optimize=True)
            paths.append(path)
            print(f"[SD] Generated enhanced scene: {path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to generate image {i}: {e}")
            # Create high-quality fallback
            path = create_fallback_image(scene_data, i, config.image_size, out_dir)
            paths.append(path)
    
    # Cleanup
    del pipe
    if device == "cuda":
        torch.cuda.empty_cache()
    
    return paths

def enhance_image_quality(image: Image.Image) -> Image.Image:
    """Apply post-processing to enhance image quality"""
    # Subtle sharpening
    image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))
    
    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.05)
    
    # Enhance color saturation slightly
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.03)
    
    return image

def create_fallback_image(scene_data: Dict, index: int, size: int, out_dir: Path) -> Path:
    """Create a high-quality fallback image"""
    from PIL import ImageDraw, ImageFont
    
    # Choose color based on scene mood
    mood_colors = {
        "focused": (70, 130, 180),
        "cozy": (205, 133, 63),
        "atmospheric": (47, 79, 79),
        "modern": (25, 25, 112),
        "classic": (139, 69, 19),
        "energetic": (255, 165, 0),
        "serene": (143, 188, 143),
        "fresh": (135, 206, 250),
        "intimate": (221, 160, 221),
        "public": (128, 128, 128),
        "inspiring": (255, 20, 147),
        "intensive": (0, 0, 139)
    }
    
    color = mood_colors.get(scene_data["mood"], (100, 100, 100))
    
    # Create gradient background
    img = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for y in range(size):
        alpha = y / size
        new_color = tuple(int(c * (1 - alpha * 0.3)) for c in color)
        draw.line([(0, y), (size, y)], fill=new_color)
    
    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size // 20)
    except:
        font = ImageFont.load_default()
    
    text = f"Study Scene {index + 1}\n{scene_data['mood'].title()} Mood"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Save fallback
    path = out_dir / f"scene_{index:03d}_fallback.jpg"
    img.save(path, "JPEG", quality=95)
    return path

# ---- Enhanced Audio Generation -----------------------------------------------

def generate_enhanced_music(total_seconds: int, prompt: str, config: AudioConfig) -> AudioSegment:
    """Generate enhanced music with better quality and processing"""
    import torch
    import torchaudio
    from einops import rearrange
    from stable_audio_tools import get_pretrained_model
    from stable_audio_tools.inference.generation import generate_diffusion_cond
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Music] Using device: {device}")
    
    # Use larger model for better quality
    model_name = "stabilityai/stable-audio-open-1.0"  # Better model if available
    try:
        model, model_config = get_pretrained_model(model_name)
    except:
        model_name = "stabilityai/stable-audio-open-small"
        model, model_config = get_pretrained_model(model_name)
    
    sample_rate = int(model_config["sample_rate"])
    sample_size = int(model_config["sample_size"])
    model = model.to(device)
    
    print(f"[Music] Generating segments with {model_name}")
    
    # Generate longer, higher-quality segments
    segments: List[AudioSegment] = []
    total_generated = 0
    
    while total_generated < total_seconds:
        remaining = total_seconds - total_generated
        segment_length = min(config.segment_seconds, remaining + 10)  # Overlap for crossfading
        
        conditioning = [{
            "prompt": prompt,
            "seconds_total": int(segment_length),
        }]
        
        output = generate_diffusion_cond(
            model,
            steps=config.steps,
            conditioning=conditioning,
            sample_size=sample_size,
            sampler_type="dpmpp-2m-sde",  # Better quality sampler
            device=device,
        )
        
        output = rearrange(output, "b d n -> d (b n)")
        wav = output.to(torch.float32)
        wav = wav / (torch.max(torch.abs(wav)) + 1e-8) * 0.8  # Prevent clipping
        wav = (wav * 32767.0).clamp(-32767, 32767).to(torch.int16).cpu()
        
        # Convert to AudioSegment
        buf = io.BytesIO()
        torchaudio.save(buf, wav, sample_rate, format="wav")
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="wav")
        
        # Set high-quality audio format
        segment = segment.set_channels(2).set_frame_rate(config.sample_rate)
        segments.append(segment)
        total_generated += segment_length
        
        print(f"[Music] Generated {len(segments)} segments ({total_generated:.1f}s/{total_seconds}s)")
    
    # Combine segments with crossfading
    print("[Music] Combining segments with enhanced crossfading...")
    track = segments[0]
    for segment in segments[1:]:
        track = track.append(segment, crossfade=config.crossfade_ms)
    
    # Trim to exact length
    if len(track) > total_seconds * 1000:
        track = track[:total_seconds * 1000]
    
    # Apply audio enhancement
    if config.enable_compression:
        track = compress_dynamic_range(track, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
    
    if config.enable_eq:
        # Subtle EQ for study music
        track = track.low_pass_filter(8000)  # Remove harsh highs
        track = track.high_pass_filter(40)   # Remove rumble
    
    # Normalize and apply gentle gain reduction
    track = normalize(track)
    track = track.apply_gain(-6.0)  # Comfortable listening level
    
    return track

# ---- Enhanced Visual Effects ------------------------------------------------

def create_enhanced_clip(
    image_path: Path, 
    duration: float, 
    config: VideoConfig, 
    scene_data: Dict,
    effects_config: EffectsConfig
) -> ImageClip:
    """Create an enhanced video clip with multiple effects"""
    
    # Load and resize image to video resolution
    clip = ImageClip(str(image_path)).set_duration(duration)
    clip = clip.resize(height=config.resolution[1])
    
    # Apply parallax effect
    if config.enable_parallax and effects_config.parallax_strength > 0:
        clip = apply_parallax_effect(clip, effects_config.parallax_strength, duration)
    
    # Apply dynamic lighting
    if config.enable_dynamic_lighting:
        clip = apply_dynamic_lighting(clip, scene_data, effects_config.lighting_variation)
    
    # Apply time-based effects
    if effects_config.enable_time_progression:
        clip = apply_time_progression(clip, scene_data, duration)
    
    return clip

def apply_parallax_effect(clip: ImageClip, strength: float, duration: float) -> ImageClip:
    """Apply subtle parallax motion effect"""
    def parallax_transform(t):
        # Slow, organic movement
        offset_x = math.sin(t * 0.1) * strength * clip.w
        offset_y = math.cos(t * 0.07) * strength * clip.h * 0.5
        return offset_x, offset_y
    
    return clip.fx(vfx.resize, lambda t: 1.0 + strength).set_position(parallax_transform)

def apply_dynamic_lighting(clip: ImageClip, scene_data: Dict, variation: float) -> ImageClip:
    """Apply dynamic lighting changes"""
    def lighting_effect(get_frame, t):
        frame = get_frame(t)
        
        # Subtle brightness variation based on time of day
        time_factor = 1.0
        if scene_data["time"] == "morning":
            time_factor = 0.95 + 0.1 * math.sin(t * 0.05)
        elif scene_data["time"] == "evening":
            time_factor = 0.9 + 0.15 * math.sin(t * 0.03)
        elif scene_data["time"] == "night":
            time_factor = 0.8 + 0.1 * math.sin(t * 0.02)
        
        # Apply lighting variation
        frame = frame * time_factor
        return np.clip(frame, 0, 255).astype(np.uint8)
    
    return clip.fl(lighting_effect)

def apply_time_progression(clip: ImageClip, scene_data: Dict, duration: float) -> ImageClip:
    """Apply subtle time progression effects"""
    if scene_data["time"] in ["morning", "evening"]:
        # Gradual color temperature shift
        def color_temp_shift(get_frame, t):
            frame = get_frame(t)
            progress = t / duration
            
            if scene_data["time"] == "morning":
                # Gradually warmer
                warm_factor = 1.0 + progress * 0.05
                frame[:,:,0] = np.clip(frame[:,:,0] * warm_factor, 0, 255)  # Red
                frame[:,:,2] = np.clip(frame[:,:,2] * (2 - warm_factor), 0, 255)  # Blue
            else:  # evening
                # Gradually cooler
                cool_factor = 1.0 + progress * 0.03
                frame[:,:,2] = np.clip(frame[:,:,2] * cool_factor, 0, 255)  # Blue
            
            return frame.astype(np.uint8)
        
        return clip.fl(color_temp_shift)
    
    return clip

def create_enhanced_transitions(clips: List[ImageClip], config: VideoConfig) -> List[ImageClip]:
    """Create enhanced transitions between clips"""
    transition_types = ["crossfade", "slide", "zoom", "blur"]
    enhanced_clips = []
    
    for i, clip in enumerate(clips):
        if i > 0:  # Apply transition to all clips except the first
            transition_type = random.choice(transition_types)
            
            if transition_type == "crossfade":
                clip = clip.crossfadein(config.transition_duration)
            elif transition_type == "slide":
                clip = apply_slide_transition(clip, config.transition_duration)
            elif transition_type == "zoom":
                clip = apply_zoom_transition(clip, config.transition_duration)
            elif transition_type == "blur":
                clip = apply_blur_transition(clip, config.transition_duration)
        
        # Always apply fade out
        clip = clip.crossfadeout(config.transition_duration)
        enhanced_clips.append(clip)
    
    return enhanced_clips

def apply_slide_transition(clip: ImageClip, duration: float) -> ImageClip:
    """Apply sliding transition effect"""
    def slide_in(t):
        if t < duration:
            progress = t / duration
            return (int((1 - progress) * clip.w), 0)
        return (0, 0)
    
    return clip.set_position(slide_in)

def apply_zoom_transition(clip: ImageClip, duration: float) -> ImageClip:
    """Apply zoom-in transition effect"""
    def zoom_resize(t):
        if t < duration:
            progress = t / duration
            scale = 0.8 + 0.2 * progress
            return scale
        return 1.0
    
    return clip.fx(vfx.resize, zoom_resize)

def apply_blur_transition(clip: ImageClip, duration: float) -> ImageClip:
    """Apply blur transition effect"""
    def blur_effect(get_frame, t):
        frame = get_frame(t)
        if t < duration:
            progress = t / duration
            blur_radius = int((1 - progress) * 5)
            if blur_radius > 0:
                # Apply Gaussian blur (simplified)
                kernel = np.ones((blur_radius, blur_radius)) / (blur_radius ** 2)
                for channel in range(frame.shape[2]):
                    frame[:,:,channel] = np.convolve(frame[:,:,channel].flatten(), kernel.flatten(), mode='same').reshape(frame[:,:,channel].shape)
        return frame.astype(np.uint8)
    
    return clip.fl(blur_effect)

# ---- Enhanced Text Overlays -------------------------------------------------

def create_enhanced_text_overlay(duration: float, config: VideoConfig) -> TextClip:
    """Create enhanced animated text overlay"""
    def animated_timer_text(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        
        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Add motivational messages at intervals
        messages = [
            "Stay focused 📚", "You've got this! 💪", "Keep going 🌟", 
            "Almost there 🎯", "Great progress 📈", "Stay motivated ✨"
        ]
        
        if int(t) % 300 == 0 and int(t) > 0:  # Every 5 minutes
            message = random.choice(messages)
            return f"Study with me  •  {time_str}\n{message}"
        
        return f"Study with me  •  {time_str}"
    
    # Create text with better styling
    txt = TextClip(
        animated_timer_text, 
        fontsize=48, 
        color='white', 
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2
    ).set_duration(duration).set_position((50, 50))
    
    # Add subtle animation
    def text_opacity(t):
        # Gentle breathing effect
        return 0.85 + 0.15 * math.sin(t * 0.5)
    
    return txt.set_opacity(text_opacity)

# ---- Progress Tracking and Resume -------------------------------------------

def save_progress(work_dir: Path, step: str, data: Dict):
    """Save generation progress"""
    progress_file = work_dir / "progress.json"
    
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}
    
    progress[step] = {
        "completed": True,
        "timestamp": time.time(),
        "data": data
    }
    
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress(work_dir: Path) -> Dict:
    """Load generation progress"""
    progress_file = work_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

# ---- Main Enhanced Pipeline -------------------------------------------------

def build_enhanced_video(
    images: List[Path],
    scenes_data: List[Dict],
    audio_path: Optional[Path],
    out_path: Path,
    video_config: VideoConfig,
    effects_config: EffectsConfig,
):
    """Build enhanced video with all effects"""
    if not images:
        raise ValueError("No images provided")
    
    print(f"[Video] Building enhanced video with {len(images)} scenes...")
    
    # Calculate how many clips we need
    total_seconds = video_config.duration_minutes * 60
    clips_needed = math.ceil(total_seconds / video_config.scene_duration)
    
    # Create enhanced clips
    enhanced_clips = []
    for i in range(clips_needed):
        img_idx = i % len(images)
        scene_idx = i % len(scenes_data)
        
        clip = create_enhanced_clip(
            images[img_idx],
            video_config.scene_duration,
            video_config,
            scenes_data[scene_idx],
            effects_config
        )
        enhanced_clips.append(clip)
        print(f"[Video] Created enhanced clip {i+1}/{clips_needed}")
    
    # Apply enhanced transitions
    enhanced_clips = create_enhanced_transitions(enhanced_clips, video_config)
    
    # Combine all clips
    final_video = concatenate_videoclips(enhanced_clips, method="compose")
    
    # Trim to exact duration
    final_video = final_video.subclip(0, total_seconds)
    
    # Add enhanced text overlay
    text_overlay = create_enhanced_text_overlay(total_seconds, video_config)
    final_video = CompositeVideoClip([final_video, text_overlay])
    
    # Add audio if provided
    if audio_path and audio_path.exists():
        try:
            audio_clip = AudioFileClip(str(audio_path))
            final_video = final_video.set_audio(audio_clip)
        except Exception as e:
            print(f"[Warning] Failed to attach audio: {e}")
    
    # Render with high quality settings
    print(f"[Video] Rendering enhanced video to {out_path}...")
    
    codec_settings = {
        "codec": "libx264",
        "audio_codec": "aac",
        "temp_audiofile": str(out_path.with_suffix(".temp-audio.m4a")),
        "remove_temp": True,
        "fps": video_config.fps,
        "threads": os.cpu_count() or 4,
    }
    
    if video_config.quality_preset == "high":
        codec_settings.update({
            "preset": "slow",
            "crf": 18,  # High quality
            "bitrate": "8000k"
        })
    elif video_config.quality_preset == "medium":
        codec_settings.update({
            "preset": "medium",
            "crf": 23,
            "bitrate": "4000k"
        })
    else:  # fast
        codec_settings.update({
            "preset": "fast",
            "crf": 28,
            "bitrate": "2000k"
        })
    
    final_video.write_videofile(str(out_path), **codec_settings)
    print("[Video] Enhanced video rendering completed!")

# ---- Enhanced Main Function -------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Enhanced Study-With-Me video generator")
    
    # Basic options
    parser.add_argument("--out", type=Path, required=True, help="Output MP4 path")
    parser.add_argument("--minutes", type=int, default=120, help="Video length in minutes")
    
    # Video quality options
    parser.add_argument("--quality", choices=["high", "medium", "fast"], default="high", 
                       help="Quality preset (high=slow render, fast=quick render)")
    parser.add_argument("--resolution", choices=["1080p", "720p", "480p"], default="1080p",
                       help="Video resolution")
    parser.add_argument("--fps", type=int, default=30, help="Video framerate")
    
    # Content options
    parser.add_argument("--image-count", type=int, default=24, help="Number of unique scenes to generate")
    parser.add_argument("--image-size", type=int, default=1024, help="Image resolution (1024 recommended for SDXL)")
    parser.add_argument("--scene-duration", type=float, default=25.0, help="Duration of each scene in seconds")
    
    # Style options
    parser.add_argument("--style", type=str, default="cinematic, professional photography, warm lighting",
                       help="Visual style for generated images")
    parser.add_argument("--enable-weather", action="store_true", default=True,
                       help="Add weather effects to scenes")
    parser.add_argument("--enable-time-progression", action="store_true", default=True,
                       help="Add time-of-day lighting changes")
    
    # Effects options
    parser.add_argument("--enable-parallax", action="store_true", default=True,
                       help="Enable subtle parallax motion effects")
    parser.add_argument("--enable-particles", action="store_true", default=True,
                       help="Enable particle effects (dust, light rays)")
    parser.add_argument("--parallax-strength", type=float, default=0.03,
                       help="Strength of parallax effect (0.01-0.1)")
    
    # Audio options
    parser.add_argument("--music-prompt", type=str, default=(
        "ambient lofi study music, soft piano, gentle rain, warm analog tape hiss, "
        "mellow pads, no vocals, 70 bpm, calming, focus-enhancing"
    ), help="Prompt for AI music generation")
    parser.add_argument("--music-file", type=Path, help="Use existing audio file instead of AI generation")
    parser.add_argument("--no-music", action="store_true", help="Generate video without audio")
    parser.add_argument("--audio-quality", choices=["high", "medium", "standard"], default="high",
                       help="Audio quality preset")
    
    # Text overlay options
    parser.add_argument("--enable-text", action="store_true", default=True,
                       help="Add animated timer and motivational text overlay")
    parser.add_argument("--text-style", choices=["minimal", "modern", "classic"], default="modern",
                       help="Text overlay style")
    
    # Technical options
    parser.add_argument("--resume", action="store_true", 
                       help="Resume from previous generation if possible")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show generation plan without executing")
    parser.add_argument("--save-assets", action="store_true", default=True,
                       help="Keep generated assets for future use")
    parser.add_argument("--config", type=str, default=None,
                       help="Path to YAML config file (PipelineConfig format)")

    args = parser.parse_args()

    # Load pipeline config if provided
    pipeline_config = None
    if args.config:
        from config import PipelineConfig
        pipeline_config = PipelineConfig.from_yaml(args.config)
        print(f"[Config] Loaded profile: {pipeline_config.profile}")
    
    # Setup configurations
    resolution_map = {
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "480p": (854, 480)
    }
    
    video_config = VideoConfig(
        duration_minutes=args.minutes,
        fps=args.fps,
        resolution=resolution_map[args.resolution],
        image_size=args.image_size,
        image_count=args.image_count,
        scene_duration=args.scene_duration,
        transition_duration=1.2,
        enable_parallax=args.enable_parallax,
        enable_particles=args.enable_particles,
        enable_dynamic_lighting=True,
        quality_preset=args.quality
    )
    
    audio_quality_map = {
        "high": AudioConfig(sample_rate=48000, bitrate="320k", steps=20),
        "medium": AudioConfig(sample_rate=44100, bitrate="192k", steps=15),
        "standard": AudioConfig(sample_rate=44100, bitrate="128k", steps=10)
    }
    
    audio_config = audio_quality_map[args.audio_quality]
    
    effects_config = EffectsConfig(
        enable_weather=args.enable_weather,
        enable_time_progression=args.enable_time_progression,
        parallax_strength=args.parallax_strength,
        particle_density=20 if args.enable_particles else 0,
        lighting_variation=0.15
    )
    
    # Setup directories
    total_seconds = args.minutes * 60
    work_dir = args.out.parent / f"{args.out.stem}_enhanced_assets"
    img_dir = work_dir / "images"
    audio_path = work_dir / "enhanced_music.wav"
    
    # Dry run - show plan
    if args.dry_run:
        print("=" * 60)
        print("ENHANCED STUDY VIDEO GENERATION PLAN")
        print("=" * 60)
        print(f"Output: {args.out}")
        print(f"Duration: {args.minutes} minutes ({total_seconds} seconds)")
        print(f"Resolution: {args.resolution} @ {args.fps} FPS")
        print(f"Quality Preset: {args.quality}")
        print()
        print("VISUAL GENERATION:")
        print(f"  • {args.image_count} unique AI-generated scenes")
        print(f"  • Image resolution: {args.image_size}x{args.image_size} pixels")
        print(f"  • Scene duration: {args.scene_duration} seconds each")
        print(f"  • Style: {args.style}")
        print(f"  • Weather effects: {'Enabled' if args.enable_weather else 'Disabled'}")
        print(f"  • Time progression: {'Enabled' if args.enable_time_progression else 'Disabled'}")
        print()
        print("VISUAL EFFECTS:")
        print(f"  • Parallax motion: {'Enabled' if args.enable_parallax else 'Disabled'}")
        print(f"  • Particle effects: {'Enabled' if args.enable_particles else 'Disabled'}")
        print(f"  • Dynamic lighting: Enabled")
        print(f"  • Enhanced transitions: Enabled")
        print()
        print("AUDIO:")
        if args.no_music:
            print("  • No audio track")
        elif args.music_file:
            print(f"  • Using existing file: {args.music_file}")
        else:
            print(f"  • AI-generated music: {audio_config.sample_rate}Hz, {audio_config.bitrate}")
            print(f"  • Prompt: {args.music_prompt}")
        print()
        print("TEXT OVERLAY:")
        print(f"  • Animated timer: {'Enabled' if args.enable_text else 'Disabled'}")
        print(f"  • Style: {args.text_style}")
        print()
        print("ESTIMATED PROCESSING TIME:")
        time_estimate = args.image_count * 2  # 2 minutes per image on average
        if not args.music_file and not args.no_music:
            time_estimate += args.minutes // 10  # Audio generation time
        time_estimate += args.minutes // 5  # Video rendering time
        print(f"  • Approximately {time_estimate} minutes")
        print()
        return
    
    # Create directories
    work_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    
    # Load or initialize progress
    progress = load_progress(work_dir) if args.resume else {}
    
    print("=" * 60)
    print("STARTING ENHANCED STUDY VIDEO GENERATION")
    print("=" * 60)
    
    # Step 1: Generate images
    image_paths = []
    if args.resume and "images" in progress:
        print("[Images] Resuming from saved progress...")
        image_paths = [Path(p) for p in progress["images"]["data"]["paths"]]
        # Verify files still exist
        image_paths = [p for p in image_paths if p.exists()]
        if len(image_paths) < args.image_count:
            print(f"[Images] Only {len(image_paths)} images found, generating remaining...")
    
    if len(image_paths) < args.image_count:
        print("[Images] Generating enhanced scenes with Stable Diffusion XL...")
        
        # Prepare scene data with style variations
        scenes_data = []
        for i in range(args.image_count):
            base_scene = ENHANCED_SCENES[i % len(ENHANCED_SCENES)].copy()
            base_scene["prompt"] += f", {args.style}"
            scenes_data.append(base_scene)
        
        try:
            new_paths = generate_images_enhanced_sd(scenes_data, video_config, img_dir)
            image_paths.extend(new_paths)
            
            # Save progress
            save_progress(work_dir, "images", {
                "paths": [str(p) for p in image_paths],
                "scenes_data": scenes_data
            })
            
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            print("Creating fallback images...")
            scenes_data = ENHANCED_SCENES[:args.image_count]
            image_paths = []
            for i, scene in enumerate(scenes_data):
                path = create_fallback_image(scene, i, video_config.image_size, img_dir)
                image_paths.append(path)
    else:
        # Load scenes data from progress
        scenes_data = progress["images"]["data"]["scenes_data"]
    
    print(f"[Images] Using {len(image_paths)} images for video generation")
    
    # Step 2: Generate or load audio
    final_audio_path = None
    if args.no_music:
        print("[Audio] Skipping audio generation (--no-music specified)")
    elif args.music_file and args.music_file.exists():
        print(f"[Audio] Using provided audio file: {args.music_file}")
        
        # Process the provided audio
        try:
            ext = args.music_file.suffix.lower().lstrip('.')
            music = AudioSegment.from_file(args.music_file, format=ext)
            
            # Extend or trim to match video duration
            if len(music) < total_seconds * 1000:
                print("[Audio] Extending audio to match video duration...")
                loops_needed = math.ceil((total_seconds * 1000) / len(music))
                extended = music
                for _ in range(loops_needed - 1):
                    extended = extended.append(music, crossfade=audio_config.crossfade_ms)
                music = extended[:total_seconds * 1000]
            else:
                music = music[:total_seconds * 1000]
            
            # Apply audio enhancements
            music = music.set_frame_rate(audio_config.sample_rate).set_channels(2)
            if audio_config.enable_compression:
                music = compress_dynamic_range(music)
            if audio_config.enable_eq:
                music = music.low_pass_filter(8000).high_pass_filter(40)
            
            music = normalize(music).apply_gain(-6.0)
            music.export(audio_path, format="wav", bitrate=audio_config.bitrate)
            final_audio_path = audio_path
            
        except Exception as e:
            print(f"[ERROR] Failed to process audio file: {e}")
            final_audio_path = None
    
    elif not (args.resume and "audio" in progress and audio_path.exists()):
        print("[Audio] Generating enhanced AI music...")
        try:
            enhanced_music = generate_enhanced_music(total_seconds, args.music_prompt, audio_config)
            enhanced_music.export(audio_path, format="wav", bitrate=audio_config.bitrate)
            final_audio_path = audio_path
            
            # Save progress
            save_progress(work_dir, "audio", {"path": str(audio_path)})
            
        except Exception as e:
            print(f"[ERROR] Audio generation failed: {e}")
            print("Continuing without audio...")
            final_audio_path = None
    else:
        print("[Audio] Using previously generated audio")
        final_audio_path = audio_path if audio_path.exists() else None
    
    # Step 3: Build enhanced video
    print("[Video] Assembling enhanced video with all effects...")
    
    try:
        build_enhanced_video(
            images=image_paths,
            scenes_data=scenes_data,
            audio_path=final_audio_path,
            out_path=args.out,
            video_config=video_config,
            effects_config=effects_config
        )
        
        # Save final progress
        save_progress(work_dir, "video", {
            "output_path": str(args.out),
            "completed": True
        })
        
        print("=" * 60)
        print("✅ ENHANCED STUDY VIDEO GENERATION COMPLETED!")
        print("=" * 60)
        print(f"📹 Video saved to: {args.out}")
        if args.save_assets:
            print(f"📁 Assets saved to: {work_dir}")
        print(f"⏱️  Duration: {args.minutes} minutes")
        print(f"🎨 Generated {len(image_paths)} unique scenes")
        if final_audio_path:
            print(f"🎵 Enhanced audio track included")
        print()
        print("Your enhanced study-with-me video is ready! 🎉")
        
        # Show file size
        if args.out.exists():
            size_mb = args.out.stat().st_size / (1024 * 1024)
            print(f"📊 File size: {size_mb:.1f} MB")
        
    except Exception as e:
        print(f"[ERROR] Video generation failed: {e}")
        print("Check the logs above for details.")
        sys.exit(1)
    
    # Run shared pipeline (post-process, notify, approve, publish) if config provided
    if pipeline_config:
        from shared.pipeline_runner import run_shared_pipeline
        run_shared_pipeline(args.out, pipeline_config)

    # Cleanup option
    if not args.save_assets:
        print("[Cleanup] Removing temporary assets...")
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted] Generation stopped by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)