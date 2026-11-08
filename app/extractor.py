"""Document text extractor for PDF and DOCX files with metadata preservation."""

import io
import re
from typing import Tuple, Dict, Any, List
from pypdf import PdfReader
from docx import Document


class DocumentExtractor:
    @staticmethod
    def extract_from_bytes(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF or DOCX bytes.
        Preserves original bytes without modifying them.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            file_format = "PDF"
            text, pages_count, extraction_notes = DocumentExtractor._extract_pdf(file_bytes)
        elif filename_lower.endswith(".docx") or filename_lower.endswith(".doc"):
            file_format = "DOCX"
            text, pages_count, extraction_notes = DocumentExtractor._extract_docx(file_bytes)
        else:
            raise ValueError(f"Formato não suportado: {filename}. Utilize arquivos .pdf ou .docx")

        clean_text = DocumentExtractor._normalize_extracted_text(text)
        has_text = len(clean_text.strip()) > 20

        return {
            "filename": filename,
            "format": file_format,
            "raw_text": clean_text,
            "char_count": len(clean_text),
            "word_count": len(clean_text.split()),
            "pages_count": pages_count,
            "has_extractable_text": has_text,
            "extraction_notes": extraction_notes,
            "original_size_bytes": len(file_bytes)
        }

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> Tuple[str, int, List[str]]:
        notes = []
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_count = len(reader.pages)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text)
            
            full_text = "\n\n".join(extracted_pages)
            if not full_text.strip():
                notes.append("O PDF pode ser baseado em imagem escaneada ou possuir texto protegido.")
            return full_text, pages_count, notes
        except Exception as e:
            return "", 0, [f"Erro na extração do PDF: {str(e)}"]

    @staticmethod
    def _extract_docx(file_bytes: bytes) -> Tuple[str, int, List[str]]:
        notes = []
        try:
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = []
            
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    paragraphs.append(p_text)
                    
            # Check tables as well (in case user put CV inside table)
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        paragraphs.append(" | ".join(row_texts))
                        
            full_text = "\n".join(paragraphs)
            pages_est = max(1, len(paragraphs) // 30)
            return full_text, pages_est, notes
        except Exception as e:
            return "", 0, [f"Erro na extração do DOCX: {str(e)}"]

    @staticmethod
    def _normalize_extracted_text(text: str) -> str:
        # Standardize newlines, remove null bytes and excessive whitespace
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
        # Remove repeated excessive empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
