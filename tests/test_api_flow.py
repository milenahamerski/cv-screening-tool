import io
from fastapi.testclient import TestClient
from docx import Document
from pypdf import PdfReader

from app.server import app
from tests.test_helpers import create_sample_docx, create_sample_pdf, SAMPLE_CV_RAW


client = TestClient(app)


def test_complete_cv_optimizer_workflow():
    """
    Validates the 10 completion criteria required by the user:
    1. Carregar um currículo.
    2. Receber o diagnóstico inicial.
    3. Clicar em Melhorar CV.
    4. Obter uma versão otimizada.
    5. Executar uma nova inspeção.
    6. Comparar os resultados.
    7. Visualizar recomendações pendentes.
    8. Editar o conteúdo manualmente.
    9. Exportar um DOCX funcional e editável.
    10. Exportar a versão final em PDF.
    """

    # 1. Carregar currículo (DOCX)
    docx_bytes = create_sample_docx()
    upload_res = client.post(
        "/api/upload",
        files={"file": ("curriculo_joao.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert upload_res.status_code == 200, upload_res.text
    upload_data = upload_res.json()
    session_id = upload_data["session_id"]
    assert upload_data["format"] == "DOCX"
    assert upload_data["filename"] == "curriculo_joao.docx"

    # 2. Receber o diagnóstico inicial
    initial_diag = upload_data["initial_diagnosis"]
    assert "overall_score" in initial_diag
    assert 0 <= initial_diag["overall_score"] <= 100
    assert len(initial_diag["criteria"]) == 6
    assert len(initial_diag["key_issues"]) > 0
    assert len(initial_diag["positive_points"]) > 0
    assert len(initial_diag["initial_recommendations"]) > 0

    # 3. Clicar em Melhorar CV
    opt_res = client.post(
        "/api/optimize",
        json={"session_id": session_id}
    )
    assert opt_res.status_code == 200, opt_res.text
    opt_data = opt_res.json()

    # 4. Obter versão otimizada
    assert "optimized_text" in opt_data
    assert "optimized_structured" in opt_data
    assert len(opt_data["steps"]) >= 6
    opt_text = opt_data["optimized_text"]
    assert "JOÃO CARLOS PEREIRA" in opt_text.upper()
    assert "TechSolutions Corp" in opt_text

    # 5. Executar uma nova inspeção (post_diagnosis)
    post_diag = opt_data["post_diagnosis"]
    assert "overall_score" in post_diag
    assert len(post_diag["criteria"]) == 6
    init_names = [c["name"] for c in initial_diag["criteria"]]
    post_names = [c["name"] for c in post_diag["criteria"]]
    assert init_names == post_names

    # Check fact preservation & no hallucination
    preservation = opt_data["preservation"]
    assert preservation["is_valid"] is True
    assert "2020" in preservation["preserved_dates"]
    assert len(preservation["hallucination_warnings"]) == 0

    # 6. Comparar os resultados
    comparison = opt_data["comparison"]
    assert comparison["original_score"] == initial_diag["overall_score"]
    assert comparison["optimized_score"] == post_diag["overall_score"]
    assert comparison["absolute_delta"] == post_diag["overall_score"] - initial_diag["overall_score"]
    assert len(comparison["criteria_comparison"]) == 6

    # 7. Visualizar recomendações pendentes (divididas por prioridade)
    recs = comparison["human_recommendations"]
    assert len(recs) > 0
    priorities = {r["priority"] for r in recs}
    assert "alta" in priorities or "media" in priorities
    for r in recs:
        assert r["problem"]
        assert r["why_matters"]
        assert r["what_to_do"]

    # 8. Editar o conteúdo manualmente (Revisão manual)
    edited_text = opt_text + "\n\nCERTIFICAÇÕES E CURSOS\n• Certificação Kubernetes CKA (2024)"
    edit_res = client.post(
        "/api/manual-edit",
        json={
            "session_id": session_id,
            "edited_text": edited_text
        }
    )
    assert edit_res.status_code == 200, edit_res.text
    edit_data = edit_res.json()
    assert "post_diagnosis" in edit_data
    assert "comparison" in edit_data

    # 9. Exportar um DOCX funcional e editável
    docx_export_res = client.get(f"/api/export/docx?session_id={session_id}")
    assert docx_export_res.status_code == 200
    assert len(docx_export_res.content) > 1000
    exported_doc = Document(io.BytesIO(docx_export_res.content))
    doc_text = "\n".join(p.text for p in exported_doc.paragraphs)
    assert "JOÃO CARLOS PEREIRA" in doc_text
    assert "TechSolutions Corp" in doc_text

    # 10. Exportar a versão final em PDF
    pdf_export_res = client.get(f"/api/export/pdf?session_id={session_id}")
    assert pdf_export_res.status_code == 200
    assert len(pdf_export_res.content) > 1000
    exported_pdf = PdfReader(io.BytesIO(pdf_export_res.content))
    assert len(exported_pdf.pages) >= 1
    pdf_text = exported_pdf.pages[0].extract_text()
    assert "JOÃO CARLOS PEREIRA" in pdf_text
    assert "TechSolutions Corp" in pdf_text

    # Additional export validation: Report PDF and Checklist TXT
    report_res = client.get(f"/api/export/report?session_id={session_id}")
    assert report_res.status_code == 200
    assert len(report_res.content) > 1000

    checklist_res = client.get(f"/api/export/checklist?session_id={session_id}")
    assert checklist_res.status_code == 200
    assert "LISTA DE PEND" in checklist_res.text or "LISTA DE PENDÊNCIAS" in checklist_res.text


def test_upload_pdf_workflow():
    pdf_bytes = create_sample_pdf()
    upload_res = client.post(
        "/api/upload",
        files={"file": ("curriculo_joao.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["format"] == "PDF"
    assert data["has_extractable_text"] is True
    assert data["initial_diagnosis"]["overall_score"] > 0


def test_manual_edit_persists_in_final_export():
    """Verifies that manual user changes in Section H are preserved in final DOCX and PDF exports."""
    docx_bytes = create_sample_docx()
    up = client.post("/api/upload", files={"file": ("cv.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}).json()
    sid = up["session_id"]

    client.post("/api/optimize", json={"session_id": sid})

    # User manually pastes a complete Markdown CV into Section H
    custom_markdown = """# BEATRIZ MENDES ROCHA
Curitiba - PR | beatriz@email.com | (41) 99888-7777 | linkedin.com/in/beatrizmendes

## Resumo Profissional
Especialista em Engenharia de Dados com 6 anos de atuação em ambientes distribuídos de alta escala.

## Experiência Profissional
### Engenheira de Dados Sênior | DataFin Tech (2022 - 2024)
- Projetou pipelines de streaming com Kafka e Spark processando 2TB de dados diários.
- Reduziu custos de infraestrutura em 35% através de partições otimizadas no Delta Lake.

## Formação Acadêmica
### Bacharelado em Ciência da Computação | UFPR (2015 - 2019)

## Habilidades e Tecnologias
- Python, Apache Spark, Kafka, SQL, Docker, AWS, Databricks
"""

    edit_res = client.post("/api/manual-edit", json={"session_id": sid, "edited_text": custom_markdown})
    assert edit_res.status_code == 200
    res_data = edit_res.json()
    assert "preview_html" in res_data
    assert "BEATRIZ MENDES ROCHA" in res_data["preview_html"]

    # Download DOCX and check that Beatriz Mendes Rocha is there!
    d_res = client.get(f"/api/export/docx?session_id={sid}")
    doc = Document(io.BytesIO(d_res.content))
    all_text = "\n".join(p.text for p in doc.paragraphs)
    assert "BEATRIZ MENDES ROCHA" in all_text
    assert "DataFin Tech" in all_text

    # Download PDF and check that Beatriz Mendes Rocha is there!
    p_res = client.get(f"/api/export/pdf?session_id={sid}")
    pdf_reader = PdfReader(io.BytesIO(p_res.content))
    pdf_text = pdf_reader.pages[0].extract_text()
    assert "BEATRIZ MENDES ROCHA" in pdf_text
    assert "DataFin Tech" in pdf_text


def test_no_score_inflation_without_evidence():
    """Verifies that scores are not artificially inflated without technical justification."""
    # Text with zero metrics:
    text_no_metrics = """Maria Santos
Email: maria@email.com | Tel: 11 99999-9999
Experiências
Assistente
- Fez tarefas rotineiras e arquivamento de documentos.
- Atendeu telefone e recepcionou clientes.
"""
    pdf_bytes = create_sample_pdf(text_no_metrics)
    up = client.post("/api/upload", files={"file": ("cv_vazio.pdf", pdf_bytes, "application/pdf")}).json()
    sid = up["session_id"]

    opt = client.post("/api/optimize", json={"session_id": sid}).json()
    post_impact = next(c for c in opt["post_diagnosis"]["criteria"] if c["criterion_id"] == "impact")

    # Since no metrics were provided in original, optimizer does not invent numbers,
    # so impact score must remain honest and not artificially maxed out!
    assert post_impact["score"] <= 8.0  # Well below max (20.0)
    assert any("métrica" in iss["issue"].lower() or "quantitativ" in iss["issue"].lower() for iss in opt["comparison"]["unresolved_issues"])
