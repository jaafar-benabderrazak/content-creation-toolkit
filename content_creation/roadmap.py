"""Video content roadmap — CRUD with JSON persistence."""
from __future__ import annotations
import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

VALID_STATUSES = {"planned", "producing", "published"}


@dataclass
class RoadmapEntry:
    id: str           # uuid4 hex
    title: str        # human-readable video title
    tags: str         # comma-separated content tags
    profile: str      # profile name (e.g. "cinematic")
    notes: str        # free-form notes
    status: str       # planned | producing | published
    created_at: str   # ISO 8601
    updated_at: str   # ISO 8601


class VideoRoadmap:
    """Manages a list of video roadmap entries with JSON persistence."""

    def __init__(self, roadmap_file: Path = Path("video_roadmap.json")) -> None:
        self._roadmap_file = Path(roadmap_file)
        self._entries: List[RoadmapEntry] = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_entry(
        self,
        title: str,
        tags: str,
        profile: str,
        notes: str = "",
    ) -> RoadmapEntry:
        """Create a new planned entry and persist it."""
        now = datetime.utcnow().isoformat()
        entry = RoadmapEntry(
            id=uuid.uuid4().hex,
            title=title,
            tags=tags,
            profile=profile,
            notes=notes,
            status="planned",
            created_at=now,
            updated_at=now,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def update_status(self, entry_id: str, status: str) -> bool:
        """Set status for entry_id. Returns True if found, False otherwise."""
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
        entry = self._find(entry_id)
        if entry is None:
            return False
        entry.status = status
        entry.updated_at = datetime.utcnow().isoformat()
        self._save()
        return True

    def update_entry(
        self,
        entry_id: str,
        title: str = None,
        tags: str = None,
        profile: str = None,
        notes: str = None,
    ) -> bool:
        """Update any non-None fields. Returns True if found, False otherwise."""
        entry = self._find(entry_id)
        if entry is None:
            return False
        if title is not None:
            entry.title = title
        if tags is not None:
            entry.tags = tags
        if profile is not None:
            entry.profile = profile
        if notes is not None:
            entry.notes = notes
        entry.updated_at = datetime.utcnow().isoformat()
        self._save()
        return True

    def delete_entry(self, entry_id: str) -> bool:
        """Remove entry by id. Returns True if found and removed."""
        original_len = len(self._entries)
        self._entries = [e for e in self._entries if e.id != entry_id]
        if len(self._entries) == original_len:
            return False
        self._save()
        return True

    def move_up(self, entry_id: str) -> bool:
        """Swap entry with the one before it. Returns True if swapped."""
        idx = self._index_of(entry_id)
        if idx is None or idx == 0:
            return False
        self._entries[idx - 1], self._entries[idx] = self._entries[idx], self._entries[idx - 1]
        self._save()
        return True

    def move_down(self, entry_id: str) -> bool:
        """Swap entry with the one after it. Returns True if swapped."""
        idx = self._index_of(entry_id)
        if idx is None or idx == len(self._entries) - 1:
            return False
        self._entries[idx], self._entries[idx + 1] = self._entries[idx + 1], self._entries[idx]
        self._save()
        return True

    def list_entries(self, status_filter: str = None) -> List[RoadmapEntry]:
        """Return entries in order; filter by status if provided. Returns a copy."""
        entries = list(self._entries)
        if status_filter is not None:
            entries = [e for e in entries if e.status == status_filter]
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find(self, entry_id: str) -> Optional[RoadmapEntry]:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def _index_of(self, entry_id: str) -> Optional[int]:
        for i, entry in enumerate(self._entries):
            if entry.id == entry_id:
                return i
        return None

    def _save(self) -> None:
        """Atomically write entries to JSON via a .tmp file."""
        tmp_path = self._roadmap_file.with_suffix(".tmp")
        data = [asdict(e) for e in self._entries]
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(self._roadmap_file)
        logger.debug("Saved %d entries to %s", len(self._entries), self._roadmap_file)

    def _load(self) -> List[RoadmapEntry]:
        """Read JSON and reconstruct entries. Returns [] on missing/empty file."""
        try:
            text = self._roadmap_file.read_text(encoding="utf-8").strip()
            if not text:
                return []
            data = json.loads(text)
            return [RoadmapEntry(**item) for item in data]
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Could not load %s: %s. Starting empty.", self._roadmap_file, exc)
            return []


# ------------------------------------------------------------------
# Module-level singleton (lazy)
# ------------------------------------------------------------------

_roadmap: Optional[VideoRoadmap] = None


def get_roadmap() -> VideoRoadmap:
    global _roadmap
    if _roadmap is None:
        _roadmap = VideoRoadmap()
    return _roadmap
