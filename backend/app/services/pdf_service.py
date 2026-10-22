import os
import re
import pymupdf as fitz
from pathlib import Path
from typing import Tuple, Optional

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False

def extract_pdf_to_markdown(pdf_path: str) -> str:
    """
    Semantic PDF extraction (RF-006, RNF-002 <= 15s CPU)
    Preserves document structure, headings, tables, and formatting in Markdown.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")

    if HAS_PYMUPDF4LLM:
        try:
            md_text = pymupdf4llm.to_markdown(pdf_path)
            if md_text and len(md_text.strip()) > 20:
                return md_text
        except Exception:
            pass  # Fall back to standard PyMuPDF layout parsing

    from backend.app.config import settings
    md_lines = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            if not text:
                if not page.get_images() and not page.get_drawings():
                    continue  # Ignore genuinely blank cover/trailing pages.
                if not settings.OCR_ENABLED:
                    raise ValueError('PDF escaneado: habilita OCR y configura los datos de idioma para extraer su texto')
                try:
                    text_page = page.get_textpage_ocr(language=settings.OCR_LANGUAGE, dpi=150, full=True, tessdata=settings.TESSDATA_PREFIX or None)
                    text = page.get_text(textpage=text_page).strip()
                except Exception as exc:
                    raise ValueError('OCR no disponible: revisa TESSDATA_PREFIX y los idiomas instalados') from exc
            if text:
                md_lines.append(f'\n\n<!-- Página {page_num + 1} -->\n{text}\n')
    if not md_lines:
        raise ValueError('El documento no contiene texto extraíble; revisa el contenido y la configuración OCR')
    return '\n'.join(md_lines)

def match_student_filename(filename: str, student_names_emails: list[dict]) -> Optional[int]:
    """
    Fuzzy match PDF filename to student roster by name, email, or rut (RF-005)
    student_names_emails = [{'id': 1, 'nombre': 'Juan Perez', 'correo': 'juan.perez@alumnos.cl', 'rut': '20.123.456-7'}]
    """
    import unicodedata
    def normalize(value):
        text = unicodedata.normalize('NFKD', value.lower())
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]', ' ', text)
    filename_normal = normalize(Path(filename).stem)
    compact = filename_normal.replace(' ', '')
    for key in ('correo', 'rut'):
        matches = []
        for student in student_names_emails:
            value = student.get(key) or ''
            if key == 'correo':
                value = value.split('@')[0]
            normalized = normalize(value).replace(' ', '')
            if normalized and normalized in compact:
                matches.append(student['id'])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None
    tokens = set(filename_normal.split())
    scores = []
    for student in student_names_emails:
        parts = {p for p in normalize(student['nombre']).split() if len(p) > 2}
        score = len(parts & tokens)
        if score >= 2 or (len(parts) == 1 and score == 1):
            scores.append((score, student['id']))
    scores.sort(reverse=True)
    if scores and (len(scores) == 1 or scores[0][0] > scores[1][0]):
        return scores[0][1]
    return None
