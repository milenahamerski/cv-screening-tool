"""Helper to create sample test resumes in PDF and DOCX formats."""

import io
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

SAMPLE_CV_RAW = """João Carlos Pereira
Email: joao.pereira@email.com | Tel: (11) 98765-4321 | São Paulo - SP
LinkedIn: linkedin.com/in/joaopereira-dev

Resumo
Profissional atuando com desenvolvimento de software e análise de dados.

Experiências
Analista de Sistemas - TechSolutions Corp (2020 - 2023)
- Responsável por desenvolver relatórios em Python e queries em SQL.
- Participei da modernização do banco PostgreSQL atendendo 5000 usuários ativos.
- Ajudei a equipe com metodologias ágeis e Scrum, reduzindo tempo de entrega em 20%.

Desenvolvedor Junior - InovaWeb Softwares (2018 - 2020)
- Responsável pela manutenção de APIs REST e rotinas em Linux.
- Atuei no suporte e resolução de chamados de clientes.

Formação
Bacharelado em Ciência da Computação - Universidade Federal (2014 - 2018)

Habilidades
Python, SQL, PostgreSQL, Git, Linux, Docker, Scrum
"""

def create_sample_docx(text: str = SAMPLE_CV_RAW) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def create_sample_pdf(text: str = SAMPLE_CV_RAW) -> bytes:
    buf = io.BytesIO()
    pdf_doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), styles["Normal"]))
            story.append(Spacer(1, 4))
    pdf_doc.build(story)
    return buf.getvalue()
