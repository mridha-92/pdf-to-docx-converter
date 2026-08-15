"""API tests for the upload/status/download flow."""

import io
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "API test document", fontsize=16)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _make_encrypted_pdf_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "secret")
    buf = io.BytesIO()
    doc.save(buf, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="x", owner_pw="x")
    doc.close()
    return buf.getvalue()


def _upload(pdf_bytes: bytes, name: str = "doc.pdf") -> str:
    resp = client.post(
        "/api/upload",
        files={"file": (name, pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["job_id"]


def _wait_complete(job_id: str, timeout: float = 30.0) -> dict:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/status/{job_id}")
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.3)
    raise AssertionError("timed out waiting for job")


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_and_download_roundtrip():
    job_id = _upload(_make_pdf_bytes())
    payload = _wait_complete(job_id)
    assert payload["status"] == "completed"

    resp = client.get(f"/api/download/{job_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )
    assert len(resp.content) > 0


def test_upload_rejects_non_pdf():
    resp = client.post(
        "/api/upload",
        files={"file": ("evil.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


def test_upload_rejects_bad_content():
    resp = client.post(
        "/api/upload",
        files={"file": ("fake.pdf", b"this is not a pdf", "application/pdf")},
    )
    assert resp.status_code == 415


def test_upload_rejects_encrypted():
    resp = client.post(
        "/api/upload",
        files={"file": ("locked.pdf", _make_encrypted_pdf_bytes(), "application/pdf")},
    )
    assert resp.status_code == 422


def test_status_unknown_job():
    resp = client.get("/api/status/does-not-exist")
    assert resp.status_code == 404


def test_download_unknown_job():
    resp = client.get("/api/download/does-not-exist")
    assert resp.status_code == 404


def test_download_before_complete():
    job_id = _upload(_make_pdf_bytes())
    resp = client.get(f"/api/download/{job_id}")
    assert resp.status_code in {404, 409}
