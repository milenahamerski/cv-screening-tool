import io
from docx import Document
from pypdf import PdfReader

from app.models import ResumeStructured, ResumeContact, ResumeExperience, ResumeEducation
from app.analyzer import ResumeAnalyzer
from app.comparer import ResumeComparer
from app.exporter import DocumentExporter
from tests.test_helpers import SAMPLE_CV_RAW


def create_mock_structured():
    return ResumeStructured(
        contact=ResumeContact(
            name="João Carlos Pereira",
            email="joao.pereira@email.com",
            phone="(11) 98765-4321",
            location="São Paulo - SP",
            linkedin="linkedin.com/in/joaopereira-dev"
        ),
        summary="Profissional experiente em engenharia de software e análise de dados.",
        experiences=[
            ResumeExperience(
                title="Analista de Sistemas",
                company="TechSolutions Corp",
                period="2020 - 2023",
                bullets=[
                    "Desenvolveu relatórios automatizados utilizando Python e consultas SQL avançadas.",
                    "Modernizou banco de dados PostgreSQL atendendo a mais de 5.000 usuários ativos."
                ]
            )
        ],
        education=[
            ResumeEducation(
                degree="Bacharelado em Ciência da Computação",
                institution="Universidade Federal",
                period="2014 - 2018"
            )
        ],
        skills=["Python", "SQL", "PostgreSQL", "Docker", "Git", "Scrum"],
        certifications=["Certificação AWS Cloud Practitioner"],
        languages=["Inglês Intermediário", "Português Nativo"]
    )


def test_export_docx_valid_and_editable():
    resume = create_mock_structured()
    docx_bytes = DocumentExporter.generate_resume_docx(resume)

    assert len(docx_bytes) > 1000

    # Validate that it can be opened by python-docx (proving it is a genuine Word document)
    doc = Document(io.BytesIO(docx_bytes))
    paragraphs_text = [p.text for p in doc.paragraphs]
    full_text = "\n".join(paragraphs_text)

    # Validate single column margins
    assert len(doc.sections) == 1
    assert round(doc.sections[0].left_margin.inches, 1) == 0.8

    # Validate content
    assert "JOÃO CARLOS PEREIRA" in full_text
    assert "TechSolutions Corp" in full_text
    assert "Bacharelado em Ciência da Computação" in full_text
    assert "Python" in full_text


def test_export_pdf_valid_and_selectable():
    resume = create_mock_structured()
    pdf_bytes = DocumentExporter.generate_resume_pdf(resume)

    assert len(pdf_bytes) > 1000

    # Validate that it is a valid PDF and extract selectable text
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() or ""

    assert "JOÃO CARLOS PEREIRA" in extracted_text
    assert "joao.pereira@email.com" in extracted_text
    assert "TechSolutions Corp" in extracted_text
    assert "Python" in extracted_text


def test_export_comparison_report_pdf():
    diag_before = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "cv.pdf")
    diag_after = ResumeAnalyzer.analyze(SAMPLE_CV_RAW + "\n• Otimizou processos em 30%.", "cv.pdf")
    comparison = ResumeComparer.compare(diag_before, diag_after)

    report_bytes = DocumentExporter.generate_report_pdf(comparison, diag_before, diag_after)
    assert len(report_bytes) > 1000

    reader = PdfReader(io.BytesIO(report_bytes))
    assert len(reader.pages) >= 1
    extracted_text = reader.pages[0].extract_text()
    assert "CV Optimizer" in extracted_text
    assert "Relatório de Análise" in extracted_text


def test_export_checklist_text():
    diag_before = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "cv.pdf")
    diag_after = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "cv.pdf")
    comparison = ResumeComparer.compare(diag_before, diag_after)

    checklist_txt = DocumentExporter.generate_checklist_text(comparison)
    assert "LISTA DE PENDÊNCIAS E REVISÃO MANUAL" in checklist_txt
    assert "ALTA PRIORIDADE" in checklist_txt
    assert "MÉDIA PRIORIDADE" in checklist_txt
    assert "BAIXA PRIORIDADE" in checklist_txt
