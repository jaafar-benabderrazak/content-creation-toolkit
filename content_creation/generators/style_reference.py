"""Style reference subsystem — Instagram scraper, color/mood extractor, profile manager.

Provides the data layer that image generation reads to apply a consistent
visual aesthetic from a reference Instagram account.

Usage (CLI):
    python generators/style_reference.py --handle radstream --limit 30
    python generators/style_reference.py --handle radstream --extract-only
    python generators/style_reference.py --handle radstream --refresh

Note: instaloader and colorthief are lazy-imported inside their respective
functions so that `StyleReferenceManager` can be imported without these
packages installed (e.g., when only reading cached profiles).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# StyleProfile dataclass
# ---------------------------------------------------------------------------

@dataclass
class StyleProfile:
    handle: str
    scraped_at: str            # ISO datetime
    post_count: int
    dominant_colors: list      # list of [R, G, B] ints
    color_temperature: str     # "warm" | "cool" | "neutral"
    brightness_level: str      # "low" | "medium" | "high"
    contrast_level: str        # "low" | "medium" | "high"
    mood_descriptors: list     # list of str
    reference_images: list     # list of str paths (up to 10 best images)
    prompt_prefix: str         # derived prompt augmentation string


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def scrape_profile_images(
    handle: str,
    post_limit: int = 30,
    cache_dir: Path = Path(".cache/style_reference"),
    session_file: Optional[str] = None,
) -> list[Path]:
    """Download images from a public Instagram profile using instaloader.

    Parameters
    ----------
    handle : str
        Instagram handle (with or without leading @).
    post_limit : int
        Maximum number of posts to download.
    cache_dir : Path
        Root cache directory; images land in cache_dir/<handle>/posts/.
    session_file : str, optional
        Path to an instaloader session file (from `instaloader --login=<user>`).

    Returns
    -------
    list[Path]
        Paths to downloaded .jpg files.

    Raises
    ------
    RuntimeError
        When Instagram requires authentication or the profile does not exist.
    """
    # Lazy import — allows using StyleReferenceManager without instaloader installed
    try:
        import instaloader
    except ImportError as exc:
        raise RuntimeError(
            "instaloader is not installed. Run: pip install instaloader"
        ) from exc

    clean_handle = handle.lstrip("@")
    posts_dir = Path(cache_dir) / clean_handle / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    if session_file:
        L.load_session_from_file(username=None, sessionfile=session_file)

    try:
        profile = instaloader.Profile.from_username(L.context, clean_handle)
        downloaded = 0
        for post in profile.get_posts():
            if downloaded >= post_limit:
                break
            if post.is_video:
                continue
            L.download_post(post, target=str(posts_dir))
            downloaded += 1
        logger.info(f"[StyleRef] Downloaded {downloaded} posts for @{clean_handle}")
    except instaloader.exceptions.LoginRequiredException:
        raise RuntimeError(
            f"Instagram requires a session file to access @{clean_handle}. "
            "Run: `instaloader --login=<username>` once, then pass "
            "--session-file=<path> to this command. "
            f"Or drop images manually into .cache/style_reference/{clean_handle}/posts/ "
            "and run --extract-only."
        )
    except instaloader.exceptions.ProfileNotExistsException:
        raise RuntimeError(
            f"Profile @{clean_handle} not found. "
            "Verify the handle or use manual fallback: drop .jpg files into "
            f".cache/style_reference/{clean_handle}/posts/ and run --extract-only."
        )
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        raise RuntimeError(
            f"Profile @{clean_handle} is private and you are not following it. "
            "Use manual fallback: drop .jpg files into "
            f".cache/style_reference/{clean_handle}/posts/ and run --extract-only."
        )

    return list(posts_dir.glob("*.jpg"))


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _classify_temperature(dominant_colors: list) -> str:
    """Classify overall color temperature from a list of [R, G, B] centroids."""
    if not dominant_colors:
        return "neutral"
    avg_r = float(np.mean([c[0] for c in dominant_colors]))
    avg_b = float(np.mean([c[2] for c in dominant_colors]))
    if avg_r - avg_b > 15:
        return "warm"
    if avg_b - avg_r > 15:
        return "cool"
    return "neutral"


def _derive_mood_descriptors(
    color_temperature: str,
    brightness_level: str,
    contrast_level: str,
) -> list[str]:
    """Derive mood descriptor list from style feature combination."""
    descriptors: list[str] = []

    if color_temperature == "warm" and brightness_level == "low":
        descriptors = ["moody", "warm", "atmospheric", "cinematic"]
    elif color_temperature == "cool" and contrast_level == "high":
        descriptors = ["sharp", "cool", "dramatic", "editorial"]
    elif color_temperature == "warm" and brightness_level == "high":
        descriptors = ["vibrant", "warm", "airy", "golden"]
    else:
        # neutral + medium — catch-all
        descriptors = ["balanced", "clean", "natural"]

    # Additive rules
    if brightness_level == "low" or contrast_level == "medium":
        if "lofi" not in descriptors:
            descriptors.append("lofi")
    if "cinematic" not in descriptors:
        descriptors.append("cinematic")

    return descriptors


def _derive_prompt_prefix(
    mood_descriptors: list[str],
    color_temperature: str,
    brightness_level: str,
) -> str:
    """Build a prompt augmentation string from mood/color features."""
    parts: list[str] = []

    if color_temperature == "warm":
        parts.append("warm muted tones")
    elif color_temperature == "cool":
        parts.append("cool desaturated tones")
    else:
        parts.append("neutral balanced tones")

    parts.append("cinematic grain")

    if brightness_level == "low":
        parts.append("atmospheric low-key lighting")
    elif brightness_level == "high":
        parts.append("bright airy lighting")
    else:
        parts.append("soft natural lighting")

    if "lofi" in mood_descriptors:
        parts.append("film photography aesthetic")
    if "dramatic" in mood_descriptors:
        parts.append("dramatic contrast")

    return ", ".join(parts)


def extract_style_features(image_paths: list[Path]) -> dict:
    """Extract color palette and mood descriptors from a set of images.

    Parameters
    ----------
    image_paths : list[Path]
        Paths to images to analyse. Capped at 20 internally for speed.

    Returns
    -------
    dict
        Keys: dominant_colors, color_temperature, brightness_level,
              contrast_level, mood_descriptors, prompt_prefix.
    """
    # Lazy import
    try:
        from colorthief import ColorThief
    except ImportError as exc:
        raise RuntimeError(
            "colorthief is not installed. Run: pip install colorthief"
        ) from exc

    try:
        from sklearn.cluster import KMeans
    except ImportError as exc:
        raise RuntimeError(
            "scikit-learn is not installed. Run: pip install scikit-learn"
        ) from exc

    capped = list(image_paths[:20])
    if not capped:
        raise RuntimeError("No images provided to extract_style_features.")

    all_colors: list[list[int]] = []
    brightness_scores: list[float] = []
    contrast_scores: list[float] = []

    for path in capped:
        try:
            ct = ColorThief(str(path))
            palette = ct.get_palette(color_count=5, quality=1)
            all_colors.extend([list(c) for c in palette])

            img = Image.open(str(path)).convert("L")
            arr = np.array(img, dtype=np.float32)
            brightness_scores.append(float(arr.mean()))
            contrast_scores.append(float(arr.std()))
        except Exception as exc:
            logger.warning(f"[StyleRef] Skipping {path}: {exc}")
            continue

    if not all_colors:
        raise RuntimeError("Could not extract colors from any provided image.")

    # Aggregate dominant colors via KMeans
    km = KMeans(n_clusters=min(5, len(all_colors)), n_init=10, random_state=42)
    km.fit(all_colors)
    dominant_colors = [[int(v) for v in c] for c in km.cluster_centers_]

    avg_brightness = float(np.mean(brightness_scores)) if brightness_scores else 128.0
    avg_contrast = float(np.mean(contrast_scores)) if contrast_scores else 50.0

    brightness_level = (
        "low" if avg_brightness < 85 else
        "high" if avg_brightness > 170 else
        "medium"
    )
    contrast_level = (
        "low" if avg_contrast < 35 else
        "high" if avg_contrast > 70 else
        "medium"
    )
    color_temperature = _classify_temperature(dominant_colors)
    mood_descriptors = _derive_mood_descriptors(color_temperature, brightness_level, contrast_level)
    prompt_prefix = _derive_prompt_prefix(mood_descriptors, color_temperature, brightness_level)

    return {
        "dominant_colors": dominant_colors,
        "color_temperature": color_temperature,
        "brightness_level": brightness_level,
        "contrast_level": contrast_level,
        "mood_descriptors": mood_descriptors,
        "prompt_prefix": prompt_prefix,
    }


# ---------------------------------------------------------------------------
# Profile builder
# ---------------------------------------------------------------------------

def build_style_profile(
    handle: str,
    image_paths: list[Path],
    cache_dir: Path,
) -> StyleProfile:
    """Extract features, build StyleProfile, and persist profile.json.

    Parameters
    ----------
    handle : str
        Instagram handle (with or without leading @).
    image_paths : list[Path]
        List of image file paths to extract features from.
    cache_dir : Path
        Root cache directory; profile.json lands in cache_dir/<handle>/.

    Returns
    -------
    StyleProfile
        Fully populated style profile.
    """
    clean_handle = handle.lstrip("@")
    features = extract_style_features(image_paths)

    # Top 10 reference images (first 10 of sorted list — no reordering needed)
    reference_images = [str(p) for p in sorted(image_paths)[:10]]

    profile = StyleProfile(
        handle=clean_handle,
        scraped_at=datetime.now(timezone.utc).isoformat(),
        post_count=len(image_paths),
        dominant_colors=features["dominant_colors"],
        color_temperature=features["color_temperature"],
        brightness_level=features["brightness_level"],
        contrast_level=features["contrast_level"],
        mood_descriptors=features["mood_descriptors"],
        reference_images=reference_images,
        prompt_prefix=features["prompt_prefix"],
    )

    # Persist to disk
    profile_path = Path(cache_dir) / clean_handle / "profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        json.dumps(dataclasses.asdict(profile), indent=2),
        encoding="utf-8",
    )
    logger.info(f"[StyleRef] Profile written to {profile_path}")

    return profile


# ---------------------------------------------------------------------------
# StyleReferenceManager
# ---------------------------------------------------------------------------

class StyleReferenceManager:
    """Manages per-handle style profiles: scraping, extraction, caching."""

    def __init__(self, cache_dir: Path = Path(".cache/style_reference")) -> None:
        self.cache_dir = Path(cache_dir)

    def profile_path(self, handle: str) -> Path:
        return self.cache_dir / handle.lstrip("@") / "profile.json"

    def posts_dir(self, handle: str) -> Path:
        return self.cache_dir / handle.lstrip("@") / "posts"

    def load(self, handle: str) -> Optional[StyleProfile]:
        """Load existing profile.json without re-scraping.

        Returns None if no profile is cached.
        """
        p = self.profile_path(handle)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return StyleProfile(**data)

    def build_or_load(
        self,
        handle: str,
        session_file: Optional[str] = None,
        post_limit: int = 30,
        refresh: bool = False,
    ) -> StyleProfile:
        """Load cached profile or scrape + extract if absent or refresh=True.

        Parameters
        ----------
        handle : str
            Instagram handle.
        session_file : str, optional
            Path to instaloader session file.
        post_limit : int
            Maximum posts to download when scraping.
        refresh : bool
            If True, ignore existing cache and re-scrape.

        Returns
        -------
        StyleProfile
        """
        if not refresh:
            cached = self.load(handle)
            if cached:
                logger.info(f"[StyleRef] Loaded cached profile for @{handle}")
                return cached

        posts_dir = self.posts_dir(handle)
        existing_images = list(posts_dir.glob("*.jpg")) if posts_dir.exists() else []

        if existing_images and not refresh:
            # Manual fallback path: user-provided images, no scraping
            logger.info(
                f"[StyleRef] Using {len(existing_images)} manually placed images for @{handle}"
            )
            image_paths = existing_images
        else:
            # Scrape from Instagram
            image_paths = scrape_profile_images(handle, post_limit, self.cache_dir, session_file)

        if not image_paths:
            raise RuntimeError(
                f"No images found for @{handle}. "
                f"Place .jpg files in {posts_dir} and run --extract-only."
            )

        return build_style_profile(handle, image_paths, self.cache_dir)

    def get_reference_image_paths(self, handle: str, max_refs: int = 10) -> list[Path]:
        """Return reference image paths from the cached profile.

        Raises RuntimeError if no profile exists (call build_or_load first).
        """
        profile = self.load(handle)
        if not profile:
            raise RuntimeError(
                f"No style profile for @{handle}. Run build_or_load() first."
            )
        return [Path(p) for p in profile.reference_images[:max_refs] if Path(p).exists()]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_profile_summary(profile: StyleProfile) -> None:
    print(f"\nStyle Profile: @{profile.handle}")
    print(f"  Scraped at:        {profile.scraped_at}")
    print(f"  Post count:        {profile.post_count}")
    print(f"  Color temperature: {profile.color_temperature}")
    print(f"  Brightness:        {profile.brightness_level}")
    print(f"  Contrast:          {profile.contrast_level}")
    print(f"  Mood descriptors:  {', '.join(profile.mood_descriptors)}")
    print(f"  Prompt prefix:     {profile.prompt_prefix}")
    print(f"  Reference images:  {len(profile.reference_images)} paths stored")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(
        description="Build or load an Instagram style reference profile.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generators/style_reference.py --handle radstream --limit 30\n"
            "  python generators/style_reference.py --handle radstream --session-file ~/.instaloader/session-user\n"
            "  python generators/style_reference.py --handle radstream --extract-only\n"
            "  python generators/style_reference.py --handle radstream --refresh\n"
        ),
    )
    parser.add_argument("--handle", required=True, help="Instagram handle (e.g. radstream)")
    parser.add_argument("--limit", type=int, default=30, help="Max posts to scrape (default: 30)")
    parser.add_argument("--session-file", dest="session_file", default=None,
                        help="Path to instaloader session file")
    parser.add_argument("--extract-only", dest="extract_only", action="store_true",
                        help="Skip scraping; extract style from existing posts/ images only")
    parser.add_argument("--refresh", action="store_true",
                        help="Ignore cache and re-scrape / re-extract")
    args = parser.parse_args()

    mgr = StyleReferenceManager()

    if args.extract_only:
        posts_dir = mgr.posts_dir(args.handle)
        images = list(posts_dir.glob("*.jpg")) if posts_dir.exists() else []
        if not images:
            print(
                f"No images found for @{args.handle}. "
                f"Drop .jpg files into {posts_dir} first."
            )
            raise SystemExit(1)
        profile = build_style_profile(args.handle, images, mgr.cache_dir)
    else:
        profile = mgr.build_or_load(
            args.handle,
            session_file=args.session_file,
            post_limit=args.limit,
            refresh=args.refresh,
        )

    _print_profile_summary(profile)


if __name__ == "__main__":
    main()
