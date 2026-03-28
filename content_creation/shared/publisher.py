"""YouTube publisher with OAuth persistence and resumable upload.

Handles:
- One-time OAuth consent flow (--setup)
- Token persistence and silent refresh
- Resumable video upload with exponential backoff
- Thumbnail upload via thumbnails.set
- Pre-upload quota guard
"""
from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Optional

from config import PipelineConfig

logger = logging.getLogger(__name__)

CREDENTIALS_DIR = Path("credentials")
TOKEN_FILE = CREDENTIALS_DIR / "youtube_token.json"
TOKEN_PICKLE = CREDENTIALS_DIR / "youtube_token.pickle"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
UPLOAD_QUOTA_COST = 1600
THUMBNAIL_QUOTA_COST = 50
MAX_RETRIES = 5


def _get_credentials():
    """Load or refresh YouTube OAuth credentials."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "YouTube publishing requires: pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        )

    creds = None

    # Try JSON token first, then pickle (from study_yt project)
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    elif TOKEN_PICKLE.exists():
        import pickle
        with open(TOKEN_PICKLE, "rb") as f:
            creds = pickle.load(f)
        logger.info("[YouTube] Loaded token from pickle (study_yt format)")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            logger.info("[YouTube] Token refreshed silently")
        except Exception as e:
            logger.warning(f"[YouTube] Token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"OAuth client secrets not found at {CLIENT_SECRETS_FILE}. "
                f"Download from Google Cloud Console → APIs & Services → Credentials → "
                f"OAuth 2.0 Client ID → Download JSON, save as {CLIENT_SECRETS_FILE}"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        _save_token(creds)
        logger.info("[YouTube] New token saved after OAuth consent")

    return creds


def _save_token(creds) -> None:
    """Save credentials to disk."""
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def _build_service():
    """Build YouTube Data API v3 service."""
    from googleapiclient.discovery import build

    creds = _get_credentials()
    return build("youtube", "v3", credentials=creds)


def check_quota_available(service, required: int = UPLOAD_QUOTA_COST) -> bool:
    """Estimate if enough quota remains for an upload.

    YouTube doesn't expose remaining quota via API, so this is a
    best-effort check based on the daily limit (10,000 units default).
    We track uploads in a local counter file.
    """
    counter_file = CREDENTIALS_DIR / "quota_counter.json"
    import json
    from datetime import date

    today = date.today().isoformat()

    if counter_file.exists():
        data = json.loads(counter_file.read_text())
        if data.get("date") == today:
            used = data.get("used", 0)
        else:
            used = 0
    else:
        used = 0

    remaining = 10000 - used
    if remaining < required:
        logger.warning(
            f"[YouTube] Quota guard: ~{remaining} units remaining, "
            f"need {required}. Refusing upload."
        )
        return False

    logger.info(f"[YouTube] Quota estimate: ~{remaining} units remaining")
    return True


def _record_quota_usage(units: int) -> None:
    """Record quota usage for today."""
    import json
    from datetime import date

    counter_file = CREDENTIALS_DIR / "quota_counter.json"
    today = date.today().isoformat()

    if counter_file.exists():
        data = json.loads(counter_file.read_text())
        if data.get("date") != today:
            data = {"date": today, "used": 0}
    else:
        data = {"date": today, "used": 0}

    data["used"] += units
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    counter_file.write_text(json.dumps(data))


def upload_video(
    video_path: Path,
    config: PipelineConfig,
) -> Optional[str]:
    """Upload video to YouTube with resumable protocol.

    Returns the video ID on success, None on failure.
    """
    if not config.publish.youtube_enabled:
        logger.info("[YouTube] Publishing disabled in config")
        return None

    service = _build_service()

    if not check_quota_available(service, UPLOAD_QUOTA_COST):
        return None

    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    body = {
        "snippet": {
            "title": config.publish.youtube_title or video_path.stem,
            "description": config.publish.youtube_description,
            "tags": config.publish.youtube_tags,
            "categoryId": config.publish.youtube_category_id,
        },
        "status": {
            "privacyStatus": config.publish.youtube_privacy,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    video_id = None
    retry = 0

    while retry <= MAX_RETRIES:
        try:
            status, response = request.next_chunk()
            if response is not None:
                video_id = response.get("id")
                logger.info(f"[YouTube] Upload complete: https://youtube.com/watch?v={video_id}")
                _record_quota_usage(UPLOAD_QUOTA_COST)
                break
        except HttpError as e:
            if e.resp.status == 404:
                # Session expired — restart
                logger.warning("[YouTube] Upload session expired (404), restarting")
                request = service.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media,
                )
                retry += 1
            elif e.resp.status in (500, 502, 503, 504):
                retry += 1
                wait = min(2**retry + random.random(), 64)
                logger.warning(f"[YouTube] Server error {e.resp.status}, retry {retry}/{MAX_RETRIES} in {wait:.1f}s")
                time.sleep(wait)
            else:
                logger.error(f"[YouTube] Upload failed: {e}")
                return None
        except Exception as e:
            retry += 1
            wait = min(2**retry + random.random(), 64)
            logger.warning(f"[YouTube] Transport error, retry {retry}/{MAX_RETRIES} in {wait:.1f}s: {e}")
            time.sleep(wait)

    return video_id


def upload_thumbnail(video_id: str, thumbnail_path: Path) -> bool:
    """Upload thumbnail to a published video."""
    if not thumbnail_path.exists():
        logger.warning(f"[YouTube] Thumbnail not found: {thumbnail_path}")
        return False

    try:
        from googleapiclient.http import MediaFileUpload

        service = _build_service()
        media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
        service.thumbnails().set(videoId=video_id, media_body=media).execute()
        _record_quota_usage(THUMBNAIL_QUOTA_COST)
        logger.info(f"[YouTube] Thumbnail uploaded for {video_id}")
        return True
    except Exception as e:
        logger.error(f"[YouTube] Thumbnail upload failed: {e}")
        return False


def publish_to_youtube(
    video_path: Path,
    config: PipelineConfig,
    thumbnail_path: Optional[Path] = None,
) -> Optional[str]:
    """Full publish flow: upload video + thumbnail."""
    video_id = upload_video(video_path, config)
    if video_id and thumbnail_path and config.publish.thumbnail_enabled:
        upload_thumbnail(video_id, thumbnail_path)
    return video_id


def setup_oauth():
    """Interactive one-time OAuth setup."""
    print("[YouTube Setup] Starting OAuth consent flow...")
    print(f"[YouTube Setup] Looking for client secrets at: {CLIENT_SECRETS_FILE}")

    if not CLIENT_SECRETS_FILE.exists():
        print(
            f"\nERROR: {CLIENT_SECRETS_FILE} not found.\n"
            "1. Go to https://console.cloud.google.com/apis/credentials\n"
            "2. Create an OAuth 2.0 Client ID (Desktop application)\n"
            "3. Download the JSON file\n"
            f"4. Save it as: {CLIENT_SECRETS_FILE.absolute()}\n"
            "5. Re-run this command"
        )
        sys.exit(1)

    _get_credentials()
    print(f"[YouTube Setup] Token saved to {TOKEN_FILE}")
    print("[YouTube Setup] You can now use YouTube publishing in your pipelines.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Publisher — Setup & Test")
    parser.add_argument("--setup", action="store_true", help="Run OAuth consent flow")
    parser.add_argument("--check-quota", action="store_true", help="Check estimated quota remaining")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.setup:
        setup_oauth()
    elif args.check_quota:
        service = _build_service()
        check_quota_available(service)
    else:
        parser.print_help()
