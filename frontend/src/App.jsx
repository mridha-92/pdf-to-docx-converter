import React, { useState, useEffect } from "react"
import "./App.css"

function App() {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)

  // Poll the backend for conversion status
  useEffect(() => {
    if (status !== "processing") return
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`)
        const data = await res.json()
        if (data.status === "completed") {
          clearInterval(interval)
          setStatus("success")
        } else if (data.status === "failed") {
          clearInterval(interval)
          setStatus("error")
          setError(data.error || "Conversion failed")
        }
      } catch (e) {
        // ignore polling errors; keep trying
      }
    }, 1500)
    return () => clearInterval(interval)
  }, [jobId, status])

  const handleFileSelect = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate type and size client-side first
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      window.alert("Please upload a .pdf file only.")
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      window.alert("File must be under 20MB.")
      return
    }

    setStatus("processing")
    setError(null)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      })
      const result = await res.json()
      if (!result.job_id) throw new Error("No job_id returned")
      setJobId(result.job_id)
    } catch (e) {
      setStatus("error")
      setError(e.message || "Upload failed")
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.target.classList.add("border-blue-500")
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.target.classList.remove("border-blue-500")
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.target.classList.remove("border-blue-500")
    const file = e.dataTransfer?.files[0]
    if (!file) return

    // Reset input value so same file can be re-selected
    e.target.value = ""
    e.target.files = e.dataTransfer?.files

    handleFileSelect({
      target: { files: [file] }
    })
  }

  if (status === "success" && jobId) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center py-12">
        <h1 className="text-3xl font-bold mb-4">Conversion complete!</h1>
        <p className="text-slate-400 mb-8">
          Your DOCX file is ready. Click below to download.
        </p>
        <a
          href={`/api/download/${jobId}`}
          className="btn btn-primary text-lg px-8 py-3"
          download
        >
          Download DOCX
        </a>
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center py-12">
        <h1 className="text-xl font-bold mb-4">Conversion failed</h1>
        <p className="text-slate-400 mb-8">{error || "Unknown error"}</p>
        <button
          onClick={() => setStatus("idle")}
          className="btn btn-primary px-6 py-3"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 relative">
      {/* Hero section */}
      <header className="text-center py-12">
        <h1 className="text-4xl font-bold mb-2">
          High-Precision PDF-to-DOCX Converter
        </h1>
        <p className="text-slate-400 max-w-xl mx-auto">
          Convert your PDFs to editable Word documents while preserving layout,
          fonts, tables and content integrity.
        </p>
      </header>

      {/* Upload zone */}
      <main className="max-w-2xl mx-auto py-8">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className="border-2 border-dashed border-slate-600 rounded-xl p-12 text-center cursor-pointer transition-colors hover:border-blue-500"
        >
          <p className="text-slate-500 mb-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-12 w-12 mx-auto mb-2 text-slate-500 drop-shadow-lg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M10 5L19.5 12.5L21 7v12a2 2 0 002 2h4a2 2 0 002-2v-7l-5.5-6.5Z" />
            </svg>
            Drag & drop a PDF or <span className="underline cursor-pointer">browse</span>
          </p>
          <p className="text-slate-400 text-sm">
            .pdf up to 20MB
          </p>
          <input
            type="file"
            accept=".pdf"
            hidden
            onChange={handleFileSelect}
          />
          <span className="underline cursor-pointer">Browse</span>
        </div>
      </main>

      {/* Loading / progress state */}
      {status === "processing" && jobId && (
        <div className="max-w-2xl mx-auto py-12">
          <div className="flex justify-center items-center mb-6">
            <svg
              className="h-12 w-12 text-slate-400 animate-spin border-4 border-slate-800 rounded-full"
              viewBox="0 0 34 34"
            >
              <circle
                className="opacity-25"
                cx="17"
                cy="17"
                r="14"
                strokeWidth="8"
              />
              <path
                className="fill-none"
                stroke="currentColor"
                strokeWidth="8"
                d="M2 7l4 18 14-8 4-18-14 8-2-10-14-8L2 7Z"
              />
            </svg>
          </div>
          <p className="text-center text-slate-400 mb-4">
            Converting PDF...{" "}
            <span className="font-medium" id="progress-text">0%</span>
          </p>
        </div>
      )}

      {/* Error state */}
      {status === "error" && <p className="mt-8 text-center text-slate-400">{error}</p>}
    </div>
  )
}

export default App