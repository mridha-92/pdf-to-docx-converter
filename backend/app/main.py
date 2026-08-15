"""FastAPI application: high-precision PDF-to-DOCX converter API."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, UPLOAD_DIR
from .converter import PDFConversionError, analyze_pdf
from .tasks import STATUS_COMPLETED, STATUS_FAILED, JobManager, jobs

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="High-Precision PDF-to-DOCX Converter",
    version="1.0.0",
    description="Convert PDFs to Word documents while preserving layout, "
    "fonts and tables.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_uploaded_pdf(name: str, data: bytes) -> None:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415, detail="Only .pdf files are accepted."
        )
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 20MB size limit.",
        )
    if not data[:5].startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415,
            detail="The uploaded file is not a valid PDF.",
        )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
) -> dict:
    """Accept a PDF, store it under a job id, and start conversion."""
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Missing file name.")

    raw = await file.read()
    _validate_uploaded_pdf(file.filename, raw)

    # Quick pre-flight analysis to reject encrypted/corrupt files immediately.
    # Since the file is under the 20MB size limit we can safely read it entirely.
    temp_source = UPLOAD_DIR / "preflight.pdf"
    temp_source.write_bytes(raw)
    try:
        analysis = analyze_pdf(temp_source)
        if analysis.encrypted:
            raise HTTPException(
                status_code=422,
                detail="This PDF is password-protected. Remove the password "
                "and try again.",
            )
    except PDFConversionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        temp_source.unlink(missing_ok=True)

    job = jobs.create(UPLOAD_DIR / "pending.pdf")
    # Rename to a collision-safe path using the job id.
    safe_path = UPLOAD_DIR / f"{job.id}.pdf"
    safe_path.write_bytes(raw)
    job.source = safe_path

    jobs.run(job)
    return {"job_id": job.id}


@app.get("/api/status/{job_id}")
async def status(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    payload: dict = {
        "job_id": job.id,
        "status": job.status,
    }
    if job.status == STATUS_COMPLETED:
        payload["page_count"] = job.page_count
        payload["engine"] = job.engine
    if job.status == STATUS_FAILED:
        payload["error"] = job.error
    return payload


@app.get("/api/download/{job_id}")
async def download(job_id: str, background: BackgroundTasks) -> FileResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != STATUS_COMPLETED or job.output is None:
        raise HTTPException(status_code=409, detail="Conversion is not ready.")

    filename = f"{job.source.stem}.docx"
    response = FileResponse(
        job.output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename=filename,
    )
    # Clean up temporary files after the response has been sent.
    background.add_task(jobs.cleanup_job, job)
    return response
