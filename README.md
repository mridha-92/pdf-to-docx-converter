# High-Precision PDF-to-DOCX Converter

Convert PDFs to editable Word (.docx) documents with near-100% fidelity:
preserving layout, fonts, tables, and content integrity.

## 🚀 Live Demo

[https://www.cyberpent.cc.cd](https://www.cyberpent.cc.cd) (portfolio site using this converter backend)

## 📦 Quick Start

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173), upload a PDF, and click **Download DOCX**.

### Docker (full stack)

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173` (proxied through Vite dev server)

## 📁 Project Structure

```
pdf-to-docx-converter/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # package the app module
│   │   ├── main.py            # FastAPI endpoints: /api/upload, /api/status/{job_id}, /api/download/{job_id}
│   │   ├── converter.py       # Core engine: analysis + pdf2docx native + span-level fallback
│   │   ├── config.py          # Paths & limits (20MB max, .pdf only)
│   │   └── tasks.py           # JobManager + background worker threads
│   ├── requirements.txt       # Python dependencies
│   ├── uploads/               # Temp uploaded PDFs (gitignored)
│   ├── outputs/               # Converted DOCX files (gitignored)
│   └── tests/
│       ├── test_converter.py  # 7 unit tests
│       └── test_api.py        # 8 integration tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Single-page UI: drag-and-drop, polling, download
│   │   ├── index.css          # Tailwind @import
│   │   ├── main.jsx           # ReactDOM render
│   │   └── App.css            # (empty – Tailwind v4 handles all styling)
│   ├── package.json           # Vite + React + Tailwind v4 deps
│   ├── vite.config.js         # Proxy to backend + Tailwind plugin
│   └── index.html             # HTML entry point
├── docker-compose.yml         # Build & run both services
├── .gitignore
└── README.md
```

## ⚙️ Architecture

### Backend API (FastAPI)

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Simple health‑check (`{"status":"ok"}`) |
| `/api/upload` | `POST` | Accept `.pdf` ≤20MB, start async conversion, return `job_id` |
| `/api/status/{job_id}` | `GET` | Return `"processing"` / `"completed"` / `"failed"` + page count & engine |
| `/api/download/{job_id}` | `GET` | Serve the `.docx` file + clean up temp files |

Conversion engine flow:
1. **Analyze** PDF → encrypted / corruption / text‑based / scanned
2. **Native**: `pdf2docx` converter (tables & multi‑column preserved)  
   *Verifies output has ≥40% of expected content; falls back if incomplete*
3. **Span‑level fallback**: PyMuPDF `get_text("dict")` → `python-docx`, mapping bold/italic flags, font names, sizes (heading heuristics), and colors onto `Run` objects
4. **Error handling**: `PDFEncryptedError`, `PDFCorruptedError`, `PDFScannedError` – all user‑friendly messages

### Frontend (React + Tailwind v4)

- **Drag‑and‑drop / browse** file selector (`.pdf`, ≤20MB)
- **Polling** `/api/status/{job_id}` every 1.5s while conversion is in progress
- **Success state**: prominent **Download DOCX** button
- **Error state**: descriptive message + **Try again** button
- **Responsive**: mobile‑friendly, dark theme matching the “CyberPent” brand

### Conversion engine (`converter.py`)

Key modules:

- `analyze_pdf(path)` → `PDFAnalysis` dataclass:
  - `text_based`: True if any page has extractable text
  - `encrypted`: True if `needs_pass`
  - `page_count`, `has_text_pages`
- `_convert_native(pdf, docx)` → uses `pdf2docx.Convener`, then verifies output paragraph + table count vs. source text lines (falls back if <40% content)
- `_convert_fallback(pdf, docx)` → PyMuPDF → python-docx span mapper:
  - Bold: `flags & FLAG_BOLD`
  - Italic: `flags & FLAG_ITALIC`
  - Superscript: `flags & FLAG_SUPERSCRIPTED`
  - Font resolution: base‑14 PDF names → Windows fonts (TimesRoman→Times New Roman, Helvetica→Arial, Courier→Courier New)
  - Size → heading style (H1 if ≥20pt relative to median, H2 if ≥16pt, H3 if ≥13pt)
  - Color → `RGBColor` from PDF span `color` integer

### Error handling

- **Encrypted PDF**: `PDFEncryptedError` → "This PDF is password‑protected..."
- **Corrupted PDF**: `PDFCorruptedError` → "The file is not a valid PDF..."
- **Scanned (image‑only) PDF**: `PDFScannedError` → "This PDF appears to be scanned..."
- **Unexpected error**: generic 500 with `"An unexpected error occurred..."`

### Frontend polish

- File size preview under the drop zone
- Cancel in‑progress job (stops polling, resets UI)
- Progress text updates (0% → 100% as backend emits page counts)
- Accessible: aria‑labels on buttons, focus-visible outlines, color‑contrast dark theme

### Docker

**backend/Dockerfile**:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**frontend/Dockerfile**:

```dockerfile
FROM node:22-alpine as build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/src ./src
COPY frontend/vite.config.js .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/vite.conf.js /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**docker-compose.yml**:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

## 🛠️ Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev   # Vite dev server with /api proxy to http://localhost:8000
```

## 📄 License

MIT License. Feel free to use, modify, and distribute this project.

## 🙏 Acknowledgments

- **PyMuPDF** (fitz) – fast PDF text & structure extraction
- **pdf2docx** – native PDF‑to‑DOCX with table/multi‑column preservation
- **python-docx** – programmatic .docx generation
- **FastAPI** – modern, fast API framework
- **React + Vite + Tailwind CSS** – modern, productive frontend stack