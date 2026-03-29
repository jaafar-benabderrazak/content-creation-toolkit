---
phase: 19-local-gradio-ui-with-pipeline-execution-scheduling-and-video-content-roadmap
plan: "01"
subsystem: scheduler
tags: [scheduling, apscheduler, persistence, subprocess]
dependency_graph:
  requires: []
  provides: [scheduler.JobQueue, scheduler.Job, scheduler.get_queue]
  affects: [19-03-gradio-schedule-tab]
tech_stack:
  added: [APScheduler>=3.10,<4.0]
  patterns: [dataclass-persistence, atomic-json-write, daemon-background-scheduler, subprocess-pipeline-launch]
key_files:
  created: [scheduler.py, jobs.json]
  modified: [requirements.txt]
decisions:
  - "JobQueue creates jobs.json on first instantiation if absent — Plan 03 can assume file always present"
  - "Past-due pending jobs on restart fire immediately via daemon thread — no queue drain delay"
  - "Atomic save via .json.tmp then Path.replace — prevents partial-write corruption on crash"
  - "_run_job checks status=='pending' before running — prevents double-execution on restart"
  - "stdout log capped at 200 lines — bounded memory even for long-running pipelines"
metrics:
  duration: "~5 min"
  completed: "2026-03-29"
  tasks: 2
  files: 3
---

# Phase 19 Plan 01: Scheduler Backend Summary

APScheduler-backed JobQueue with JSON persistence firing study_with_me_generator.py subprocesses at scheduled datetimes.

## What Was Built

`scheduler.py` — fully importable, self-contained scheduling module with:

- `Job` dataclass: id (uuid4 hex), profile, tags, output_path, scheduled_at (ISO 8601), status (pending/running/done/failed), created_at, log (last 200 stdout lines)
- `JobQueue` class: thread-safe with `threading.Lock`; loads/reschedules jobs on init; atomic JSON persistence via `.tmp` + `Path.replace`
- `add_job` / `cancel_job` / `list_jobs` public API
- `_schedule` uses `APScheduler.DateTrigger`; past-due jobs fire immediately in daemon threads
- `_run_job` guards on `status == "pending"` to prevent double-execution
- `_launch_pipeline` calls `[sys.executable, "study_with_me_generator.py", "--config", "configs/last_run.yaml", "--out", job.output_path]` with optional `--tags`
- `get_queue()` module-level lazy singleton for Gradio import
- `jobs.json` created on first instantiation with `[]`

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build scheduler.py with JobQueue, Job dataclass, APScheduler | d58c73d | scheduler.py, jobs.json |
| 2 | Add APScheduler to requirements, smoke test | 96fa034 | requirements.txt |

## Verification Results

- `from scheduler import JobQueue, Job, get_queue` imports without error
- `JobQueue()` creates `jobs.json` with `[]` content
- `add_job()` adds job and persists to JSON
- `cancel_job()` transitions status to "failed" and persists
- `list_jobs()` returns sorted list (ascending scheduled_at)
- APScheduler entry present in requirements.txt
- Smoke test: `PASS`
- Full checklist: all 6 checks passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing behavior] jobs.json not created on empty init**
- **Found during:** Task 1 verification
- **Issue:** `_save()` is only called on mutation; fresh instantiation with no jobs never wrote the file, but plan specified jobs.json should be created on first instantiation
- **Fix:** Added `if not self._queue_file.exists(): self._save()` in `__init__` after scheduler start
- **Files modified:** scheduler.py
- **Commit:** d58c73d (included in same task commit)

## Self-Check: PASSED

- `scheduler.py` exists: FOUND
- `jobs.json` exists: FOUND
- `requirements.txt` has APScheduler: FOUND
- Commit d58c73d: FOUND
- Commit 96fa034: FOUND
