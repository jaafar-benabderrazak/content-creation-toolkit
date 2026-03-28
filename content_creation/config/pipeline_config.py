from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class SDXLSettings(BaseModel):
    negative_prompt: str  # required — no default; missing field raises ValidationError
    steps: int = Field(default=25, ge=1, le=150)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    enable_refiner: bool = False
    width: int = Field(default=1024, ge=512, le=2048)
    height: int = Field(default=1024, ge=512, le=2048)
    quality_suffix: str = ""  # appended to positive prompt; e.g. "masterpiece, best quality, 8k"


class SunoSettings(BaseModel):
    genre: str  # required — profile-specific genre tag; e.g. "lofi chill" or "orchestral cinematic"
    make_instrumental: bool = True
    track_count: int = Field(default=2, ge=1, le=5)
    model_version: str = "V4_5"  # overridden by quality_preset validator; kie.ai format
    api_key: Optional[str] = None  # loaded from SUNO_API_KEY env var; never hardcoded

    @model_validator(mode='after')
    def _load_api_key_from_env(self) -> 'SunoSettings':
        import os
        if self.api_key is None:
            self.api_key = os.environ.get('SUNO_API_KEY')
        return self


class VideoSettings(BaseModel):
    style_prompt: str = "cinematic, professional photography, warm lighting"
    music_prompt: str = "ambient lofi study music, soft piano, gentle rain, 70 bpm, calming"
    mood: str = "focused"
    duration_minutes: int = Field(default=120, ge=1, le=480)
    resolution: str = Field(default="1080p", pattern=r"^(1080p|720p|480p)$")
    quality_preset: str = Field(default="high", pattern=r"^(high|medium|fast)$")
    scene_count: int = Field(default=24, ge=1, le=200)
    scene_duration_seconds: float = Field(default=25.0, gt=0)
    enable_weather: bool = True
    enable_time_progression: bool = True
    enable_parallax: bool = True
    enable_particles: bool = True
    parallax_strength: float = Field(default=0.03, ge=0.0, le=1.0)


class PostSettings(BaseModel):
    watermark_enabled: bool = False
    watermark_text: str = ""
    watermark_position: str = Field(
        default="bottom-right",
        pattern=r"^(top-left|top-right|bottom-left|bottom-right|center)$",
    )
    subtitles_enabled: bool = False
    subtitles_srt_path: str = ""
    intro_enabled: bool = False
    intro_clip_path: str = ""
    outro_enabled: bool = False
    outro_clip_path: str = ""


class PublishSettings(BaseModel):
    youtube_enabled: bool = False
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_tags: List[str] = Field(default_factory=list)
    youtube_category_id: str = "27"
    youtube_privacy: str = Field(default="private", pattern=r"^(public|unlisted|private)$")
    thumbnail_enabled: bool = True


class NotifySettings(BaseModel):
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    require_approval: bool = True
    approval_timeout_seconds: int = Field(default=3600, ge=60)


class PipelineConfig(BaseModel):
    profile: str = "default"
    video: VideoSettings = Field(default_factory=VideoSettings)
    post: PostSettings = Field(default_factory=PostSettings)
    publish: PublishSettings = Field(default_factory=PublishSettings)
    notify: NotifySettings = Field(default_factory=NotifySettings)
    sdxl: Optional[SDXLSettings] = None
    suno: Optional[SunoSettings] = None

    @model_validator(mode='after')
    def _apply_quality_preset(self) -> 'PipelineConfig':
        preset = self.video.quality_preset
        preset_map = {
            'high':   {'steps': 35, 'guidance_scale': 8.0, 'model_version': 'V4_5',  'quality_suffix': 'masterpiece, best quality, 8k, photorealistic'},
            'medium': {'steps': 25, 'guidance_scale': 7.5, 'model_version': 'V4_5',  'quality_suffix': 'high quality, detailed'},
            'fast':   {'steps': 15, 'guidance_scale': 7.0, 'model_version': 'V3_5',  'quality_suffix': ''},
        }
        p = preset_map.get(preset, preset_map['medium'])
        if self.sdxl is not None:
            self.sdxl.steps = p['steps']
            self.sdxl.guidance_scale = p['guidance_scale']
            self.sdxl.quality_suffix = p['quality_suffix']
        if self.suno is not None:
            self.suno.model_version = p['model_version']
        return self

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> PipelineConfig:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"Config file is empty: {path}")
        try:
            return cls.model_validate(data)
        except AttributeError:
            return cls.parse_obj(data)  # Pydantic v1 fallback

    def to_yaml(self, path: Union[str, Path]) -> None:
        import yaml

        try:
            data = self.model_dump()
        except AttributeError:
            data = self.dict()  # Pydantic v1 fallback
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
