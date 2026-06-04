"""
Core redaction engine — coordinate-based PyMuPDF PII removal.
Searches for anchor labels, computes bounding boxes of following values,
applies irreversible page.apply_redactions() to destroy underlying characters.
"""
import io
import fitz  # PyMuPDF

# PII anchor labels — values following these on the same line are redacted
DEFAULT_ANCHORS = [
    "Subject ID:",
    "Client ID:",
    "Original Filename:",
    "Patient:",
    "Patient Name:",
    "Name:",
    "DOB:",
    "Date of Birth:",
    "MRN:",
    "SSN:",
]

PAD_X = 4   # horizontal padding around redaction rect (pts)
PAD_Y = 2   # vertical padding


def redact_pdf_bytes(
    pdf_bytes: bytes,
    anchors: list[str] | None = None,
    fill_color: tuple = (1, 1, 1),  # white fill preserves template design
) -> tuple[bytes, dict]:
    """
    Redact PII values following anchor labels in a PDF.

    Returns (redacted_pdf_bytes, stats_dict).
    Stats: {"pages_processed": N, "total_redactions": N}
    """
    anchors = [a.lower().rstrip(":") for a in (anchors or DEFAULT_ANCHORS)]
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_redactions = 0

    for page in doc:
        page_redactions = 0
        words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_idx

        # Group words by (block_no, line_no) to reconstruct lines
        lines: dict[tuple, list] = {}
        for w in words:
            lines.setdefault((w[5], w[6]), []).append(w)

        for line_words in lines.values():
            line_text = " ".join(w[4] for w in line_words).lower()

            for anchor in anchors:
                if anchor not in line_text:
                    continue

                # Locate which word index ends the anchor
                cumulative = ""
                anchor_end_idx = None
                for idx, w in enumerate(line_words):
                    cumulative += w[4].lower() + " "
                    if anchor in cumulative:
                        anchor_end_idx = idx
                        break

                if anchor_end_idx is None:
                    continue

                value_words = line_words[anchor_end_idx + 1:]
                if not value_words:
                    continue

                x0 = min(w[0] for w in value_words) - PAD_X
                y0 = min(w[1] for w in value_words) - PAD_Y
                x1 = max(w[2] for w in value_words) + PAD_X
                y1 = max(w[3] for w in value_words) + PAD_Y

                page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=fill_color)
                page_redactions += 1
                break  # one match per anchor per line is enough

        # Destroys underlying text data — not just visual masking
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        total_redactions += page_redactions

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue(), {
        "pages_processed": len(doc),
        "total_redactions": total_redactions,
    }
