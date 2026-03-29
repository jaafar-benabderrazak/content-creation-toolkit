"""Persistent execution log — survives page reloads and restarts.

Stores pipeline execution history in execution_log.json.
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

LOG_FILE = Path("execution_log.json")
_lock = threading.Lock()


@dataclass
class ExecutionEntry:
    id: str = ""
    started_at: str = ""
    finished_at: str = ""
    pipeline: str = ""
    profile: str = ""
    tags: str = ""
    output_path: str = ""
    status: str = "running"  # running, done, failed
    exit_code: Optional[int] = None
    last_lines: str = ""  # last 50 lines of output

    def __post_init__(self):
        if not self.id:
            self.id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


def _load() -> List[dict]:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(entries: List[dict]) -> None:
    tmp = LOG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    tmp.replace(LOG_FILE)


def start_execution(pipeline: str, profile: str, tags: str, output_path: str) -> ExecutionEntry:
    entry = ExecutionEntry(
        pipeline=pipeline, profile=profile, tags=tags, output_path=output_path,
    )
    with _lock:
        entries = _load()
        entries.append(asdict(entry))
        _save(entries)
    return entry


def update_execution(entry_id: str, status: str, exit_code: Optional[int] = None, last_lines: str = "") -> None:
    with _lock:
        entries = _load()
        for e in entries:
            if e["id"] == entry_id:
                e["status"] = status
                e["finished_at"] = datetime.now().isoformat()
                if exit_code is not None:
                    e["exit_code"] = exit_code
                if last_lines:
                    e["last_lines"] = last_lines
                break
        _save(entries)


def get_execution_history(limit: int = 20) -> List[dict]:
    entries = _load()
    return list(reversed(entries[-limit:]))


def format_history() -> str:
    entries = get_execution_history(20)
    if not entries:
        return "(no execution history)"
    lines = []
    for e in entries:
        status_icon = {"running": "...", "done": "OK", "failed": "ERR"}.get(e["status"], "?")
        exit_str = f" exit={e.get('exit_code', '?')}" if e["status"] != "running" else ""
        lines.append(
            f"[{status_icon:3}] {e['started_at'][:19]} | {e['pipeline']} | "
            f"tags={e.get('tags') or '—'} | {e.get('output_path', '?')}{exit_str}"
        )
    return "\n".join(lines)
