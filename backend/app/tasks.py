"""Background job management for PDF conversions.

Jobs are tracked in-memory and executed on worker threads so the FastAPI
event loop stays responsive while conversions run.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .config import OUTPUT_DIR, UPLOAD_DIR
from .converter import PDFConversionError, convert_pdf_to_docx

logger = logging.getLogger("tasks")

STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

STALE_AFTER_SECONDS = 60 * 60  # cleanup jobs older than 1 hour


@dataclass
class Job:
    id: str
    source: Path
    status: str = STATUS_PROCESSING
    error: Optional[str] = None
    page_count: Optional[int] = None
    engine: Optional[str] = None
    output: Optional[Path] = None
    created_at: float = field(default_factory=time.time)


class JobManager:
    """Thread-safe registry of conversion jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, source: Path) -> Job:
        job = Job(id=str(uuid4()), source=source)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def run(self, job: Job) -> None:
        """Execute the conversion on a worker thread."""
        thread = threading.Thread(
            target=self._work, args=(job,), daemon=True, name=f"convert-{job.id[:8]}"
        )
        thread.start()

    def _work(self, job: Job) -> None:
        output = OUTPUT_DIR / f"{job.id}.docx"
        try:
            meta = convert_pdf_to_docx(job.source, output)
            job.status = STATUS_COMPLETED
            job.output = output
            job.page_count = meta.get("page_count")
            job.engine = meta.get("engine")
        except PDFConversionError as exc:
            job.status = STATUS_FAILED
            job.error = str(exc)
            logger.warning("job %s failed: %s", job.id, exc)
        except Exception as exc:  # noqa: BLE001
            job.status = STATUS_FAILED
            job.error = "An unexpected error occurred during conversion."
            logger.exception("job %s crashed", job.id)
            del exc

    def cleanup_job(self, job: Job) -> None:
        """Remove the uploaded PDF and converted DOCX for a finished job."""
        for path in (job.source, job.output):
            try:
                if path and path.exists():
                    path.unlink()
            except OSError:  # noqa: BLE001
                logger.warning("could not remove %s", path)
        with self._lock:
            self._jobs.pop(job.id, None)

    def purge_stale(self) -> int:
        """Remove jobs (and their files) older than STALE_AFTER_SECONDS."""
        cutoff = time.time() - STALE_AFTER_SECONDS
        stale = [
            job for job in list(self._jobs.values()) if job.created_at < cutoff
        ]
        for job in stale:
            self.cleanup_job(job)
        if stale:
            logger.info("purged %d stale jobs", len(stale))
        return len(stale)


jobs = JobManager()
