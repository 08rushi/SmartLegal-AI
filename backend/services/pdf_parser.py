"""
PDF text extraction using PyMuPDF (fitz).
Preserves page numbers and positions for accurate clause references.
"""

import fitz  # PyMuPDF
import re


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF file with page number markers.
    Returns cleaned plain text with [Page X] markers preserved.
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
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        full_text = "\n".join(
            line for line in full_text.splitlines() if line.strip()
        )
        return full_text

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def split_into_chunks(text: str, max_chars: int = 18000) -> list[dict]:
    """
    Split document text into chunks, preserving page boundaries.
    Each chunk includes metadata about which pages it covers.
    Returns list of: { text, start_page, end_page, chunk_index }
    """
    chunks = []
    current_chunk = []
    current_chars = 0
    current_start_page = 1
    current_page = 1
    chunk_index = 0

    lines = text.split('\n')

    for line in lines:
        page_match = re.match(r'\[Page (\d+)\]', line)
        if page_match:
            current_page = int(page_match.group(1))
            if chunk_index == 0 and not current_chunk:
                current_start_page = current_page

        line_len = len(line) + 1

        if current_chars + line_len > max_chars and current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'start_page': current_start_page,
                'end_page': current_page,
                'chunk_index': chunk_index,
            })
            chunk_index += 1
            current_start_page = current_page
            current_chunk = [line]
            current_chars = line_len
        else:
            current_chunk.append(line)
            current_chars += line_len

    if current_chunk:
        chunks.append({
            'text': '\n'.join(current_chunk),
            'start_page': current_start_page,
            'end_page': current_page,
            'chunk_index': chunk_index,
        })

    return chunks


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


def count_approximate_tokens(text: str) -> int:
    """Rough token count estimate (4 chars per token)."""
    return len(text) // 4
