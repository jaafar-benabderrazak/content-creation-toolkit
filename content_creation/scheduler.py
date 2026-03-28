"""Video job scheduler — APScheduler-backed queue with JSON persistence."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger(__name__)

_LOG_LINES_KEEP = 200


@dataclass
class Job:
    id: str                 # uuid4 hex
    profile: str            # profile name (e.g. "cinematic")
    tags: str               # comma-separated tags or "" if not used
    output_path: str        # e.g. "out/video.mp4"
    scheduled_at: str       # ISO 8601 string
    status: str             # pending | running | done | failed
    created_at: str         # ISO 8601 string
    log: str = ""           # last N lines of stdout captured


class JobQueue:
    """Persistent job queue backed by a JSON file with APScheduler firing."""

    def __init__(self, queue_file: Path = Path("jobs.json")) -> None:
        self._queue_file = Path(queue_file)
        self._jobs: List[Job] = self._load()
        self._lock = threading.Lock()

        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.start()

        # Ensure the queue file exists (creates [] on first run)
        if not self._queue_file.exists():
            self._save()

        # Reschedule all pending future jobs on restart
        now = datetime.now()
        for job in self._jobs:
            if job.status == "pending":
                try:
                    scheduled = datetime.fromisoformat(job.scheduled_at)
                except ValueError:
                    logger.warning("Job %s has invalid scheduled_at; skipping reschedule", job.id)
                    continue
                if scheduled > now:
                    self._schedule(job)
                else:
                    # Past-due pending job — run immediately in thread
                    threading.Thread(target=self._run_job, args=(job.id,), daemon=True).start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_job(
        self,
        profile: str,
        tags: str,
        output_path: str,
        scheduled_at_iso: str,
    ) -> Job:
        """Create a new Job, persist it, schedule it, and return it."""
        job = Job(
            id=uuid.uuid4().hex,
            profile=profile,
            tags=tags,
            output_path=output_path,
            scheduled_at=scheduled_at_iso,
            status="pending",
            created_at=datetime.now().isoformat(),
        )
        with self._lock:
            self._jobs.append(job)
            self._save()
        self._schedule(job)
        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job. Sets status to 'failed'. Returns True if found."""
        with self._lock:
            for job in self._jobs:
                if job.id == job_id:
                    job.status = "failed"
                    # Remove from APScheduler if scheduled
                    try:
                        self._scheduler.remove_job(job_id)
                    except Exception:
                        pass  # Not scheduled or already fired — ignore
                    self._save()
                    return True
        return False

    def list_jobs(self) -> List[Job]:
        """Return a sorted copy of all jobs (ascending scheduled_at)."""
        with self._lock:
            return sorted(list(self._jobs), key=lambda j: j.scheduled_at)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _schedule(self, job: Job) -> None:
        """Register a DateTrigger with APScheduler for the given job."""
        try:
            scheduled = datetime.fromisoformat(job.scheduled_at)
        except ValueError:
            logger.warning("Job %s has invalid scheduled_at; cannot schedule", job.id)
            return

        now = datetime.now()
        if scheduled <= now:
            # Already past — fire immediately in a daemon thread
            threading.Thread(target=self._run_job, args=(job.id,), daemon=True).start()
        else:
            try:
                self._scheduler.add_job(
                    func=self._run_job,
                    trigger=DateTrigger(run_date=scheduled),
                    args=[job.id],
                    id=job.id,
                    replace_existing=True,
                )
            except Exception as exc:
                logger.error("Failed to schedule job %s: %s", job.id, exc)

    def _run_job(self, job_id: str) -> None:
        """Execute the pipeline for the given job id and update status."""
        with self._lock:
            job = next((j for j in self._jobs if j.id == job_id), None)
            if job is None:
                logger.warning("_run_job: job %s not found", job_id)
                return
            if job.status not in ("pending",):
                logger.info("_run_job: job %s status=%s, skipping", job_id, job.status)
                return
            job.status = "running"
            self._save()

        returncode = self._launch_pipeline(job)

        with self._lock:
            job.status = "done" if returncode == 0 else "failed"
            self._save()

    def _launch_pipeline(self, job: Job) -> int:
        """Launch study_with_me_generator.py as a subprocess and capture output."""
        cmd = [
            sys.executable,
            "study_with_me_generator.py",
            "--config",
            "configs/last_run.yaml",
            "--out",
            job.output_path,
        ]
        if job.tags:
            cmd += ["--tags", job.tags]

        logger.info("Launching pipeline: %s", " ".join(cmd))

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except Exception as exc:
            logger.error("Failed to launch pipeline for job %s: %s", job.id, exc)
            return 1

        lines: List[str] = []
        for line in process.stdout:  # type: ignore[union-attr]
            lines.append(line.rstrip())
            if len(lines) > _LOG_LINES_KEEP:
                lines = lines[-_LOG_LINES_KEEP:]

        process.wait()

        with self._lock:
            job.log = "\n".join(lines)
            self._save()

        return process.returncode

    def _save(self) -> None:
        """Atomically write jobs to JSON (write to .tmp then replace)."""
        tmp = self._queue_file.with_suffix(".json.tmp")
        data = [asdict(j) for j in self._jobs]
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self._queue_file)

    def _load(self) -> List[Job]:
        """Load jobs from JSON file. Returns [] on missing file."""
        try:
            raw = json.loads(self._queue_file.read_text(encoding="utf-8"))
            return [Job(**d) for d in raw]
        except FileNotFoundError:
            return []
        except Exception as exc:
            logger.error("Failed to load %s: %s — starting with empty queue", self._queue_file, exc)
            return []


# ---------------------------------------------------------------------------
# Module-level singleton (lazy)
# ---------------------------------------------------------------------------

_queue: Optional[JobQueue] = None


def get_queue() -> JobQueue:
    """Return the module-level singleton JobQueue, creating it on first call."""
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue
