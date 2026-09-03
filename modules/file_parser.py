"""
file_parser.py - helpers to parse uploaded resume files (.pdf, .docx, .txt)
"""
from typing import Tuple
import io

def parse_txt(file_bytes: bytes) -> str:
    """
    Return decoded text for a .txt file.
    """
    try:
        return file_bytes.decode("utf-8", errors="replace")
    except Exception:
        return file_bytes.decode("latin-1", errors="replace")

def parse_docx(file_obj: io.BytesIO) -> str:
    """
    Parse a DOCX file via python-docx.
    """
    from docx import Document
    document = Document(file_obj)
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs)

def parse_pdf(file_obj: io.BytesIO) -> str:
    """
    Parse PDF using pdfplumber, fallback to PyPDF2 if needed.
    """
    try:
        import pdfplumber
        text_chunks = []
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    text_chunks.append(txt)
        return "\n".join(text_chunks).strip()
    except Exception:
        # fallback
        try:
            from PyPDF2 import PdfReader
            file_obj.seek(0)
            reader = PdfReader(file_obj)
            pages = []
            for p in reader.pages:
                pages.append(p.extract_text() or "")
            return "\n".join(pages).strip()
        except Exception as e:
            raise RuntimeError("Failed to parse PDF. The file may be scanned/images-only or corrupted.") from e

def parse_uploaded_file(uploaded) -> Tuple[str, str]:
    """
    Given a Streamlit UploadedFile, return (text, error_message)
    """
    import os, io
    name = uploaded.name
    ext = os.path.splitext(name)[1].lower()
    content = uploaded.read()
    file_obj = io.BytesIO(content)
    try:
        if ext == ".txt":
            return parse_txt(content), ""
        elif ext == ".docx":
            return parse_docx(file_obj), ""
        elif ext == ".pdf":
            return parse_pdf(file_obj), ""
        else:
            return "", f"Unsupported file type: {ext}"
    except Exception as e:
        return "", str(e)