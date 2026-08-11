import os
from pypdf import PdfReader
import docx

def extract_text(file_path: str) -> str:
    """
    Extracts plain text from PDF and DOCX files based on extension.
    Raises ValueError for unsupported types or RuntimeError for extraction errors.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Extensión de archivo no soportada: '{ext}'. Solo se admiten PDF y DOCX.")

def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Error al procesar el archivo PDF: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text).strip()
    except Exception as e:
        raise RuntimeError(f"Error al procesar el archivo DOCX: {str(e)}")
