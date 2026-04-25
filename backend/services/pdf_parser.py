"""
PDF text extraction using PyMuPDF (fitz).
Handles both native-text PDFs and image-based scans.
"""

import io
import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.
    Returns cleaned plain text.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")

            if text.strip():
                pages_text.append(f"[Page {page_num + 1}]\n{text.strip()}")

        doc.close()

        full_text = "\n\n".join(pages_text)

        # Basic cleanup
        full_text = "\n".join(
            line for line in full_text.splitlines() if line.strip()
        )

        return full_text

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    For image files (JPG/PNG), we return a placeholder —
    Gemini Vision API handles the actual reading.
    """
    return "[IMAGE_DOCUMENT]"


def get_pdf_metadata(file_bytes: bytes) -> dict:
    """Extract basic metadata from a PDF."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        meta = doc.metadata
        page_count = len(doc)
        doc.close()
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "page_count": page_count,
        }
    except Exception:
        return {"title": "", "author": "", "page_count": 0}
