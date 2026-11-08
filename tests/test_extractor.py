import pytest
from app.extractor import DocumentExtractor
from tests.test_helpers import create_sample_docx, create_sample_pdf, SAMPLE_CV_RAW


def test_extract_docx():
    docx_bytes = create_sample_docx()
    result = DocumentExtractor.extract_from_bytes(docx_bytes, "curriculo_teste.docx")

    assert result["format"] == "DOCX"
    assert result["filename"] == "curriculo_teste.docx"
    assert result["has_extractable_text"] is True
    assert "João Carlos Pereira" in result["raw_text"]
    assert "TechSolutions Corp" in result["raw_text"]
    assert result["word_count"] > 30
    assert result["original_size_bytes"] == len(docx_bytes)


def test_extract_pdf():
    pdf_bytes = create_sample_pdf()
    result = DocumentExtractor.extract_from_bytes(pdf_bytes, "meu_cv.pdf")

    assert result["format"] == "PDF"
    assert result["filename"] == "meu_cv.pdf"
    assert result["has_extractable_text"] is True
    assert "João Carlos Pereira" in result["raw_text"]
    assert result["word_count"] > 20
    assert result["original_size_bytes"] == len(pdf_bytes)


def test_unsupported_format():
    with pytest.raises(ValueError, match="Formato não suportado"):
        DocumentExtractor.extract_from_bytes(b"image data", "foto.png")
