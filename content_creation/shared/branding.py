"""Channel branding fetch, avatar download, and local cache.

Fetches YouTube channel data (name, avatar, description) once and caches it
under .cache/branding/.  All downstream consumers (watermark, thumbnail,
intro/outro) read from this single source.

Public API:
    fetch_channel_branding(refresh: bool = False) -> BrandingData
    BrandingData  (dataclass with 6 fields)
"""
from __future__ import annotations

import dataclasses
import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CREDENTIALS_DIR = Path("credentials")
TOKEN_FILE = CREDENTIALS_DIR / "youtube_token.json"
TOKEN_PICKLE = CREDENTIALS_DIR / "youtube_token.pickle"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CACHE_DIR = Path(".cache/branding")
CACHE_FILE = CACHE_DIR / "branding.json"
AVATAR_FILE = CACHE_DIR / "avatar.jpg"
CACHE_TTL_HOURS = 24 * 7  # 7 days — explicit refresh is the primary invalidation


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class BrandingData:
    channel_name: str
    avatar_url: str
    avatar_local_path: str   # absolute path to .cache/branding/avatar.jpg
    description: str
    tagline: str             # first sentence of description, max 80 chars
    fetched_at: str          # ISO 8601 datetime string


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> Optional[BrandingData]:
    """Return cached BrandingData, or None if absent/expired/corrupt."""
    if not CACHE_FILE.exists():
        return None
    try:
        raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("[Branding] Cache file corrupt — will re-fetch")
        return None

    fetched_at_str = raw.get("fetched_at", "")
    try:
        fetched_at = datetime.fromisoformat(fetched_at_str)
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
        if age_hours > CACHE_TTL_HOURS:
            logger.info(f"[Branding] Cache expired ({age_hours:.1f}h old) — will re-fetch")
            return None
    except ValueError:
        return None

    return BrandingData(
        channel_name=raw.get("channel_name", ""),
        avatar_url=raw.get("avatar_url", ""),
        avatar_local_path=raw.get("avatar_local_path", ""),
        description=raw.get("description", ""),
        tagline=raw.get("tagline", ""),
        fetched_at=fetched_at_str,
    )


def _save_cache(data: BrandingData) -> None:
    """Persist BrandingData to disk as JSON."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(dataclasses.asdict(data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Avatar download
# ---------------------------------------------------------------------------

def _download_avatar(url: str) -> Path:
    """Download avatar image to AVATAR_FILE; return path even on failure."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(AVATAR_FILE))
        logger.info(f"[Branding] Avatar downloaded to {AVATAR_FILE}")
    except Exception as exc:
        logger.warning(f"[Branding] Avatar download failed: {exc}")
    return AVATAR_FILE


# ---------------------------------------------------------------------------
# YouTube service
# ---------------------------------------------------------------------------

def _get_youtube_service():
    """Build YouTube Data API v3 service, mirroring publisher.py credential loading."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "Branding fetch requires: pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        )

    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Branding fetch requires: pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        )

    creds = None

    # Try JSON token first, then pickle (study_yt format)
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    elif TOKEN_PICKLE.exists():
        import pickle
        with open(TOKEN_PICKLE, "rb") as f:
            creds = pickle.load(f)
        logger.info("[Branding] Loaded token from pickle (study_yt format)")
    else:
        raise FileNotFoundError(
            f"No YouTube token found. Expected {TOKEN_FILE} or {TOKEN_PICKLE}. "
            f"Run: python shared/publisher.py --setup"
        )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("[Branding] Token refreshed silently")
        except Exception as exc:
            logger.warning(f"[Branding] Token refresh failed: {exc}")
            creds = None

    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"OAuth client secrets not found at {CLIENT_SECRETS_FILE}. "
                f"Download from Google Cloud Console and run: python shared/publisher.py --setup"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        # Persist renewed token
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
        logger.info("[Branding] New token saved after OAuth consent")

    return build("youtube", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_channel_branding(refresh: bool = False) -> BrandingData:
    """Fetch channel branding data, using cache when available.

    Args:
        refresh: When True, delete cached files and re-fetch from the YouTube API.

    Returns:
        BrandingData with channel_name, avatar_url, avatar_local_path,
        description, tagline, and fetched_at.

    Raises:
        RuntimeError: No YouTube channel found for authenticated account.
        FileNotFoundError: No valid OAuth token on disk.
        ImportError: google-api-python-client not installed.
    """
    if refresh:
        CACHE_FILE.unlink(missing_ok=True)
        AVATAR_FILE.unlink(missing_ok=True)
        logger.info("[Branding] Cache cleared for refresh")
    else:
        cached = _load_cache()
        if cached is not None:
            logger.info("[Branding] loaded from cache")
            return cached

    # --- Live fetch ---
    service = _get_youtube_service()
    response = (
        service.channels()
        .list(part="snippet", mine=True, maxResults=1)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        raise RuntimeError("No YouTube channel found for authenticated account")

    snippet = items[0]["snippet"]
    channel_name: str = snippet.get("title", "")
    description: str = snippet.get("description", "")

    # Best available thumbnail: high > medium > default
    thumbnails = snippet.get("thumbnails", {})
    avatar_url: str = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
        or ""
    )

    # Tagline: first sentence of description, capped at 80 chars
    if description:
        first_sentence = description.split(".")[0].strip()
        tagline = first_sentence[:80]
        if not tagline:
            tagline = channel_name
    else:
        tagline = channel_name

    # Download avatar
    if avatar_url:
        _download_avatar(avatar_url)
    avatar_local_path = str(AVATAR_FILE.absolute())

    data = BrandingData(
        channel_name=channel_name,
        avatar_url=avatar_url,
        avatar_local_path=avatar_local_path,
        description=description,
        tagline=tagline,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )

    _save_cache(data)
    logger.info(f"[Branding] fetched channel: {channel_name}")
    return data
