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
    normalized_fname = re.sub(r"[^a-zA-Z0-9]", " ", filename.lower())
    
    # 1. Exact match on email prefix
    for s in student_names_emails:
        email_prefix = s['correo'].split('@')[0].lower()
        if email_prefix in normalized_fname:
            return s['id']
            
    # 2. Match on rut if available
    for s in student_names_emails:
        if s.get('rut'):
            clean_rut = re.sub(r"[^0-9kK]", "", s['rut']).lower()
            if clean_rut and clean_rut in normalized_fname.replace(" ", ""):
                return s['id']

    # 3. Match on surname or first name combination
    for s in student_names_emails:
        parts = [p.lower() for p in s['nombre'].split() if len(p) > 2]
        matches = sum(1 for p in parts if p in normalized_fname)
        if matches >= 2 or (len(parts) == 1 and matches == 1):
            return s['id']

    return None
