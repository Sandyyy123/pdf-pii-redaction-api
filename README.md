> **⚠️ Proprietary — All Rights Reserved.** © 2026 Sandeep Grover. This repository is licensed to Sandeep Grover and may **not** be used, run, copied, modified, distributed, or used to train models without prior written permission. Public visibility does not grant a license. See [LICENSE](LICENSE).

---

# PDF PII Redaction API

High-performance FastAPI microservice for **irreversible, coordinate-based PII redaction** from medical PDF reports.

Built for health-tech/neurotech SaaS platforms that generate automated reports (qEEG, EHR, etc.) and need to anonymize them on-the-fly before streaming to clients.

## Why not regex/pdftk?

Raw byte replacement corrupts PDFs with `TJ`/`Tj` kerning arrays. This service uses **PyMuPDF visual-coordinate redaction** (`page.apply_redactions()`) which:
- Permanently destroys underlying character data (not just visual masking)
- Preserves the original template design with a white fill
- Processes entirely in-memory — no temp files written to disk

## Architecture

```
Client Request
     │
     ▼
FastAPI /redact endpoint
     │  receives PDF bytes
     ▼
redactor.py
     │  1. Parse word bounding boxes (fitz "words" mode)
     │  2. Locate anchor labels (Subject ID:, Client ID:, etc.)
     │  3. Compute bounding box of value following anchor
     │  4. page.add_redact_annot() — mark for redaction
     │  5. page.apply_redactions() — destroy character data
     ▼
StreamingResponse → clean PDF bytes
```

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Usage

```bash
curl -X POST http://localhost:8000/redact \
  -F "file=@patient_report.pdf" \
  --output redacted_report.pdf
```

Response headers include:
- `X-Redaction-Count`: number of PII fields redacted
- `X-Pages-Processed`: total pages scanned

## Configurable anchors

Edit `DEFAULT_ANCHORS` in `redactor.py` or pass a custom list to `redact_pdf_bytes()`.

Default anchors: `Subject ID`, `Client ID`, `Original Filename`, `Patient`, `Name`, `DOB`, `MRN`, `SSN`

## Tested on

- qEEGpro EC LinkedEars reports (27-page, 29 PII fields redacted in <200ms)
- PyMuPDF 1.24+, FastAPI 0.111+, Python 3.11+

## Author

Dr. Sandeep Grover | https://groverautomationhub.lovable.app/portfolio
