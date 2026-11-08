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
