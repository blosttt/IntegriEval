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

    # Robust fallback layout parser using PyMuPDF (fitz)
    doc = fitz.open(pdf_path)
    md_lines = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        md_lines.append(f"\n\n<!-- Página {page_num + 1} -->\n")
        
        # Extract structured text blocks
        blocks = page.get_text("blocks")
        for b in blocks:
            # block tuple: (x0, y0, x1, y1, text, block_no, block_type)
            if b[6] == 0:  # Text block
                text = b[4].strip()
                if not text:
                    continue
                # Heuristic heading detection based on block length and casing
                if len(text.splitlines()) == 1 and len(text) < 80:
                    if text.isupper() or re.match(r"^(Cap[íi]tulo|\d+(\.\d+)*|[A-Z][a-z]+(\s+[A-Z][a-z]+)*:)", text):
                        md_lines.append(f"\n### {text}\n")
                        continue
                md_lines.append(f"{text}\n")
                
    doc.close()
    return "\n".join(md_lines)

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
