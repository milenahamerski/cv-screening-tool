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

    # Validate paragraph alignment (justified text for summary and bullets)
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    justified_paragraphs = [p for p in doc.paragraphs if p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY]
    assert len(justified_paragraphs) >= 2  # summary and bullet points are justified


def test_export_docx_and_pdf_english_headings():
    resume_en = ResumeStructured(
        contact=ResumeContact(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1 555-0199",
            location="San Francisco, CA"
        ),
        summary="Senior Software Engineer with 7 years of experience in distributed systems and cloud services.",
        experiences=[
            ResumeExperience(
                title="Lead Software Engineer",
                company="Tech Corp",
                period="2020 - Present",
                bullets=[
                    "Architected high-throughput microservices using Go and PostgreSQL handling 50k RPS.",
                    "Optimized cloud infrastructure reducing AWS operational expenses by 35%."
                ]
            )
        ],
        education=[
            ResumeEducation(
                degree="B.S. in Computer Science",
                institution="Stanford University",
                period="2013 - 2017"
            )
        ],
        skills=["Python", "Go", "Docker", "Kubernetes", "AWS"]
    )

    docx_bytes = DocumentExporter.generate_resume_docx(resume_en)
    doc = Document(io.BytesIO(docx_bytes))
    docx_text = "\n".join([p.text for p in doc.paragraphs])
    assert "WORK EXPERIENCE" in docx_text
    assert "EDUCATION" in docx_text
    assert "SKILLS & TECHNOLOGIES" in docx_text

    pdf_bytes = DocumentExporter.generate_resume_pdf(resume_en)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_text = reader.pages[0].extract_text()
    assert "WORK EXPERIENCE" in pdf_text
    assert "EDUCATION" in pdf_text



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
