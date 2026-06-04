"""
PDF PII Redaction API — FastAPI microservice
Accepts a PDF file upload or path, redacts PII anchors in-memory, streams the clean PDF.
"""
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from redactor import redact_pdf_bytes

app = FastAPI(title="PDF PII Redaction API", version="1.0.0")

@app.post("/redact", summary="Redact PII from uploaded PDF")
async def redact_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    pdf_bytes = await file.read()
    clean_bytes, stats = redact_pdf_bytes(pdf_bytes)
    return StreamingResponse(
        io.BytesIO(clean_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="redacted_{file.filename}"',
            "X-Redaction-Count": str(stats["total_redactions"]),
            "X-Pages-Processed": str(stats["pages_processed"]),
        },
    )

@app.get("/health")
def health():
    return {"status": "ok"}
