"""Tests for the PDF-to-DOCX conversion engine."""

from pathlib import Path

import fitz
import pytest

from app.converter import (
    PDFConversionError,
    PDFCorruptedError,
    PDFEncryptedError,
    PDFScannedError,
    analyze_pdf,
    convert_pdf_to_docx,
)

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURES.mkdir(exist_ok=True)


def _make_text_pdf(path: Path, lines: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    for idx, line in enumerate(lines):
        page.insert_text((72, 72 + idx * 30), line, fontsize=12)
    doc.save(path)
    doc.close()


@pytest.fixture(scope="module")
def native_pdf() -> Path:
    path = FIXTURES / "native.pdf"
    _make_text_pdf(path, ["Header Line", "Body line one", "Body line two"])
    return path


@pytest.fixture(scope="module")
def encrypted_pdf() -> Path:
    path = FIXTURES / "encrypted.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "secret")
    doc.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="pw", owner_pw="pw")
    doc.close()
    return path


@pytest.fixture(scope="module")
def corrupted_pdf() -> Path:
    path = FIXTURES / "corrupt.pdf"
    path.write_bytes(b"not a pdf %%%%")
    return path


@pytest.fixture(scope="module")
def scanned_pdf() -> Path:
    path = FIXTURES / "scanned.pdf"
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 100), 0)
    pix.set_rect(fitz.IRect(0, 0, 200, 100), (120, 120, 120))
    page.insert_image(fitz.Rect(50, 50, 250, 150), pixmap=pix)
    doc.save(path)
    doc.close()
    return path


def test_analyze_native(native_pdf):
    result = analyze_pdf(native_pdf)
    assert result.text_based is True
    assert result.has_text_pages >= 1


def test_analyze_encrypted(encrypted_pdf):
    result = analyze_pdf(encrypted_pdf)
    assert result.encrypted is True


def test_convert_native_ok(native_pdf, tmp_path):
    out = tmp_path / "out.docx"
    meta = convert_pdf_to_docx(native_pdf, out)
    assert out.exists()
    assert out.stat().st_size > 0
    assert meta["page_count"] >= 1
    assert meta["engine"] in {"pdf2docx", "span-fallback"}


def test_convert_encrypted(encrypted_pdf, tmp_path):
    with pytest.raises(PDFEncryptedError):
        convert_pdf_to_docx(encrypted_pdf, tmp_path / "out.docx")


def test_convert_corrupted(corrupted_pdf, tmp_path):
    with pytest.raises(PDFCorruptedError):
        convert_pdf_to_docx(corrupted_pdf, tmp_path / "out.docx")


def test_convert_scanned(scanned_pdf, tmp_path):
    with pytest.raises(PDFScannedError):
        convert_pdf_to_docx(scanned_pdf, tmp_path / "out.docx")


def test_convert_missing_file(tmp_path):
    with pytest.raises(PDFConversionError):
        convert_pdf_to_docx(tmp_path / "nope.pdf", tmp_path / "out.docx")
