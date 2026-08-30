import os
from pypdf import PdfReader
import docx

try:
    import pymupdf4llm
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False


def extract_text(file_path: str) -> str:
    """
    Extracts plain text from PDF and DOCX files.
    Used as a quick fallback when Markdown is not needed.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return _extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Extensión no soportada: '{ext}'. Solo PDF y DOCX.")


def extract_to_markdown(file_path: str) -> str:
    """
    Converts a PDF or DOCX file to Markdown, preserving headings,
    paragraphs, and tables as much as possible.

    For PDFs, uses pymupdf4llm if available (best quality),
    otherwise falls back to plain text wrapped in a code block.
    For DOCX, reconstructs basic Markdown from heading styles.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _pdf_to_markdown(file_path)
    elif ext in [".docx", ".doc"]:
        return _docx_to_markdown(file_path)
    else:
        raise ValueError(f"Extensión no soportada: '{ext}'. Solo PDF y DOCX.")


# ── PDF helpers ──────────────────────────────────────────────────────────────

def _pdf_to_markdown(file_path: str) -> str:
    if _HAS_PYMUPDF:
        try:
            md = pymupdf4llm.to_markdown(file_path)
            if md and len(md.strip()) >= 50:
                return md
        except Exception as e:
            print(f"[extractor] pymupdf4llm failed, falling back to plain text: {e}")

    # Fallback: plain text
    text = _extract_text_from_pdf(file_path)
    return text


def _extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        lines = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                lines.append(content)
        return "\n".join(lines).strip()
    except Exception as e:
        raise RuntimeError(f"Error al procesar el PDF: {str(e)}")


# ── DOCX helpers ─────────────────────────────────────────────────────────────

def _docx_to_markdown(file_path: str) -> str:
    """
    Converts DOCX paragraphs to Markdown using heading styles.
    Heading 1 → # , Heading 2 → ##, Heading 3 → ###, body → plain paragraph.
    """
    try:
        doc = docx.Document(file_path)
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                lines.append("")
                continue
            style = para.style.name if para.style else ""
            if "Heading 1" in style:
                lines.append(f"# {text}")
            elif "Heading 2" in style:
                lines.append(f"## {text}")
            elif "Heading 3" in style:
                lines.append(f"### {text}")
            else:
                lines.append(text)
        return "\n\n".join(lines).strip()
    except Exception as e:
        raise RuntimeError(f"Error al procesar el DOCX: {str(e)}")


def _extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception as e:
        raise RuntimeError(f"Error al procesar el DOCX: {str(e)}")
