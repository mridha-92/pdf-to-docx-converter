# High-Precision PDF-to-DOCX Converter

Convert PDFs to editable Word (.docx) documents with near-100% fidelity: layout, fonts, tables and content preserved.

## Tech Stack

- **Backend:** Python / FastAPI, PyMuPDF, pdf2docx, python-docx
- **Frontend:** React (Vite) + Tailwind CSS
- **Deployment:** Docker (optional)

## Project Structure

```
pdf-to-docx-converter/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── config.py        # Settings (paths, limits)
│   │   ├── converter.py     # Conversion engine
│   │   └── tasks.py         # Background job manager
│   ├── uploads/             # Temp upload dir (gitignored)
│   ├── outputs/             # Temp output dir (gitignored)
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```
