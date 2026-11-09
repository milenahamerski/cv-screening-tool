import pytest
from app.markdown_parser import MarkdownResumeParser
from app.optimizer import ResumeOptimizer
from app.exporter import DocumentExporter

SAMPLE_MD = """# Mariana Costa Silva
São Paulo - SP | mariana.silva@email.com | (11) 98765-4321 | [linkedin.com/in/marianacosta](https://linkedin.com/in/marianacosta)

## Resumo Profissional
Engenheira de Software com 5 anos de experiência em microsserviços.

## Experiência Profissional
### Engenheira de Software Sênior | TechNova Inovações (2022 - Atual)
- Desenvolveu plataforma de pagamentos distribuída processando mais de 100.000 transações diárias.
- Otimizou consultas PostgreSQL reduzindo latência em 45%.

### Desenvolvedora Back-end | SoftCloud Soluções (2019 - 2022)
- Construiu APIs RESTful escaláveis em Python e FastAPI.

## Formação Acadêmica
### Bacharelado em Engenharia de Software | USP (2015 - 2019)

## Habilidades e Tecnologias
- Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL

## Certificações e Cursos
- AWS Certified Solutions Architect (2023)

## Idiomas
- Inglês Avançado
- Português Nativo
"""

def test_markdown_parser_extracts_all_fields():
    struct = MarkdownResumeParser.parse(SAMPLE_MD)

    assert struct.contact.name == "Mariana Costa Silva"
    assert struct.contact.email == "mariana.silva@email.com"
    assert struct.contact.phone == "(11) 98765-4321"
    assert struct.contact.location == "São Paulo - SP"
    assert "linkedin.com/in/marianacosta" in struct.contact.linkedin

    assert "Engenheira de Software" in struct.summary

    assert len(struct.experiences) == 2
    assert struct.experiences[0].title == "Engenheira de Software Sênior"
    assert struct.experiences[0].company == "TechNova Inovações"
    assert "2022 - Atual" in struct.experiences[0].period
    assert len(struct.experiences[0].bullets) == 2
    assert "100.000" in struct.experiences[0].bullets[0]

    assert len(struct.education) == 1
    assert "Engenharia de Software" in struct.education[0].degree
    assert "USP" in struct.education[0].institution

    assert "Python" in struct.skills
    assert "Docker" in struct.skills

    assert len(struct.certifications) == 1
    assert "AWS Certified" in struct.certifications[0]

    assert len(struct.languages) == 2
    assert any("Inglês" in l for l in struct.languages)


def test_render_to_markdown():
    struct = MarkdownResumeParser.parse(SAMPLE_MD)
    md_output = ResumeOptimizer.render_to_markdown(struct)

    assert "# Mariana Costa Silva" in md_output
    assert "## Experiência Profissional" in md_output
    assert "### Engenheira de Software Sênior | TechNova Inovações" in md_output


def test_generate_preview_html():
    struct = MarkdownResumeParser.parse(SAMPLE_MD)
    html = DocumentExporter.generate_preview_html(struct)

    assert "cv-paper" in html
    assert "MARIANA COSTA SILVA" in html
    assert "TechNova Inovações" in html
    assert "cv-skill-pill" in html
def test_user_screenshot_markdown():
    user_md = """# CARLOS EDUARDO
São Paulo - SP | carlos@email.com | (11) 91234-5678

## RESUMO PROFISSIONAL
Desenvolvedor e Engenheiro de Machine Learning com foco em modelos preditivos e APIs escaláveis.

## EXPERIÊNCIA PROFISSIONAL
### Engenheiro de Software | DataLab Corp (2021 - 2024)
- Desenvolveu modelos de Machine Learning com Scikit-Learn e XGBoost com 94% de acurácia.
- Construiu pipelines de automação com Playwright e APIs FastAPI.

## HABILIDADES E TECNOLOGIAS

**Linguagens:** Python, JavaScript, TypeScript, SQL.

**Backend e APIs:** FastAPI, Node.js, Express.js, APIs RESTful, Webhooks, Microsserviços.

**Dados e Machine Learning:** Pandas, Polars, Scikit-learn, XGBoost, Imbalanced-learn, Análise de Dados.

**Bancos de Dados:** MongoDB, SQL.

**DevOps e Ferramentas:** Docker, Git, GitLab, GitHub, Grafana, Prometheus.

**Automação e Testes:** Playwright, PyAutoGUI, Pytest, Testes Automatizados.

## IDIOMAS

Inglês | Francês
"""
    struct = MarkdownResumeParser.parse(user_md)
    assert struct.contact.name == "CARLOS EDUARDO"
    assert len(struct.experiences) == 1
    assert "DataLab Corp" in struct.experiences[0].company
    assert len(struct.skills) >= 10
    assert "Python" in struct.skills
    assert "FastAPI" in struct.skills
    assert "Docker" in struct.skills
    assert "Inglês" in struct.languages
    assert "Francês" in struct.languages

    # Check that preview HTML renders without any errors
    html = DocumentExporter.generate_preview_html(struct)
    assert "cv-paper" in html
    assert "CARLOS EDUARDO" in html
    assert "Python" in html


def test_milena_cv_parsing_and_export():
    from app.exporter import DocumentExporter
    from pypdf import PdfReader
    from docx import Document
    import io

    milena_cv = """# MILENA HAMERSKI

 hamerskimilena@gmail.com | (42) 98883-9268 | LinkedIn | GitHub

## RESUMO PROFISSIONAL

Desenvolvedora de Sistemas com experiência em desenvolvimento backend, integração de sistemas, construção de APIs RESTful e automação de processos. Atuação com Python, FastAPI, Node.js e bancos de dados SQL e NoSQL, com foco em arquitetura de software, otimização de fluxos operacionais, observabilidade e qualidade das entregas. Pós-graduanda em Ciência de Dados, com conhecimentos em análise de dados e aprendizado de máquina.

## EXPERIÊNCIA PROFISSIONAL

**SICREDI PLANALTO DAS ÁGUAS PR/SP**

**Desenvolvedora de Sistemas | Janeiro/2025 – Atual**

- Desenvolvimento de automação de notificações via WhatsApp, otimizando a comunicação com associados e reduzindo em aproximadamente 5 horas o esforço operacional anteriormente dedicado ao processo manual.
- Integração de API de consulta veicular e reestruturação de fluxo de apoio à concessão de crédito, substituindo uma solução de terceiros e proporcionando uma redução de aproximadamente 3 vezes nos custos operacionais.
- Reestruturação de API Gateway para integração com serviços externos, com componentização e padronização de logs estruturados para monitoramento via Grafana, facilitando a manutenção, aumentando a visibilidade operacional e agilizando a identificação e mitigação de falhas por meio da preservação dos códigos de resposta originais das APIs integradas.

**FIQON**

**Desenvolvedora Full Stack | Julho/2023 – Julho/2024**

- Integração entre API de e-commerce e plataforma de comunicação via WhatsApp, utilizando webhooks para automatizar notificações e permitir o acompanhamento das etapas do pós-venda até a entrega, reduzindo atividades manuais e agilizando a comunicação com clientes.
- Desenvolvimento de aplicação web com painel administrativo para gerenciamento e monitoramento de produtos, incluindo preços, estoque e descrições, com sincronização das informações com a plataforma de e-commerce do cliente.

## FORMAÇÃO ACADÊMICA

**UNIVERSIDADE FEDERAL DE OURO PRETO (UFOP)**

Pós-graduação em Ciência de Dados | Agosto 2026 – Em andamento

**UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ (UTFPR) – GUARAPUAVA/PR**

Tecnologia em Sistemas para Internet | Setembro/2023 – Julho/2026

**Trabalho de Conclusão de Curso (TCC):**

"Predição de Inadimplência no Pós-Concessão de Crédito: Aprendizado de Máquina com Dados do Sistema de Informações de Crédito (SCR)"

- Desenvolvimento e avaliação de modelos de aprendizado de máquina para predição de inadimplência em operações de crédito.
- Preparação, tratamento e engenharia de atributos utilizando dados públicos do Sistema de Informações de Crédito (SCR).
- Aplicação e otimização de algoritmos de classificação, com comparação de desempenho por métricas como Accuracy, Precision, Recall, F1-Score e ROC-AUC.
- Utilização de Python, Pandas, Polars, Scikit-learn, XGBoost e Imbalanced-learn no processo de análise, treinamento e avaliação dos modelos.

## HABILIDADES E TECNOLOGIAS

**Linguagens:** Python, JavaScript, TypeScript, SQL.

**Backend e APIs:** FastAPI, Node.js, Express.js, APIs RESTful, Webhooks, Microsserviços.

**Dados e Machine Learning:** Pandas, Polars, Scikit-learn, XGBoost, Imbalanced-learn, Análise de Dados.

**Bancos de Dados:** MongoDB, SQL.

**DevOps e Ferramentas:** Docker, Git, GitLab, GitHub, Grafana, Prometheus.

**Automação e Testes:** Playwright, PyAutoGUI, Pytest, Testes Automatizados.

## IDIOMAS

Inglês | Francês
"""

    struct = MarkdownResumeParser.parse(milena_cv)

    # 1. Verification of structural integrity
    assert struct.contact.name == "MILENA HAMERSKI"
    assert struct.contact.email == "hamerskimilena@gmail.com"
    assert struct.contact.phone == "(42) 98883-9268"

    assert len(struct.experiences) == 2
    assert struct.experiences[0].title == "Desenvolvedora de Sistemas"
    assert "SICREDI" in struct.experiences[0].company
    assert "Janeiro/2025" in struct.experiences[0].period
    assert len(struct.experiences[0].bullets) == 3

    assert struct.experiences[1].title == "Desenvolvedora Full Stack"
    assert struct.experiences[1].company == "FIQON"
    assert "Julho/2023" in struct.experiences[1].period
    assert len(struct.experiences[1].bullets) == 2

    assert len(struct.education) == 2
    assert "UFOP" in struct.education[0].institution or "OURO PRETO" in struct.education[0].institution
    assert "UTFPR" in struct.education[1].institution
    assert len(struct.education[1].bullets) == 4

    assert len(struct.skill_categories) == 6
    assert "Python" in struct.skill_categories["Linguagens"]
    assert "FastAPI" in struct.skill_categories["Backend e APIs"]

    # 2. PDF Generation
    pdf_bytes = DocumentExporter.generate_resume_pdf(struct)
    assert len(pdf_bytes) > 2000
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pdf_full = "".join(p.extract_text() or "" for p in reader.pages)
    assert "MILENA HAMERSKI" in pdf_full
    assert "SICREDI" in pdf_full
    assert "FIQON" in pdf_full
    assert "Janeiro/2025" in pdf_full
    assert "Julho/2023" in pdf_full
    assert "Linguagens" in pdf_full
    assert "Inglês" in pdf_full

    # 3. DOCX Generation
    docx_bytes = DocumentExporter.generate_resume_docx(struct)
    assert len(docx_bytes) > 2000
    doc = Document(io.BytesIO(docx_bytes))
    docx_full = "\n".join(p.text for p in doc.paragraphs)
    assert "MILENA HAMERSKI" in docx_full
    assert "SICREDI" in docx_full
    assert "FIQON" in docx_full
    assert "Linguagens:" in docx_full
