"""FastAPI application entrypoint.

Wired up in Step 3: /api/upload, /api/status/{job_id}, /api/download/{job_id}.
"""

from fastapi import FastAPI

app = FastAPI(
    title="High-Precision PDF-to-DOCX Converter",
    version="0.1.0",
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
