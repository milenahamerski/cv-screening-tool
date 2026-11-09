"""FastAPI application for CV Optimizer."""

import os
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.extractor import DocumentExtractor
from app.analyzer import ResumeAnalyzer
from app.optimizer import ResumeOptimizer
from app.markdown_parser import MarkdownResumeParser
from app.preservation_validator import PreservationValidator
from app.comparer import ResumeComparer
from app.exporter import DocumentExporter
from app.models import ResumeStructured


app = FastAPI(
    title="CV Optimizer",
    description="Análise e otimização de currículos para ATS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (keyed by session_id)
sessions: Dict[str, Dict[str, Any]] = {}


class OptimizeRequest(BaseModel):
    session_id: str


class FromMarkdownRequest(BaseModel):
    markdown_text: str
    session_id: Optional[str] = None


class FormatMarkdownRequest(BaseModel):
    markdown_text: str


class ManualEditRequest(BaseModel):
    session_id: Optional[str] = None
    edited_text: str
    structured_data: Optional[Dict[str, Any]] = None


@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Receives and analyzes a resume (PDF, DOCX or MD), keeping the original strictly unmodified."""
    filename = file.filename or "curriculo.pdf"
    valid_exts = (".pdf", ".docx", ".doc", ".md", ".markdown", ".txt")
    if not any(filename.lower().endswith(ext) for ext in valid_exts):
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Por favor, envie um arquivo em formato .pdf, .docx ou .md"
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")

    # Extract text while preserving original bytes
    try:
        extracted = DocumentExtractor.extract_from_bytes(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar documento: {str(e)}")

    # Initial diagnosis using objective criteria
    diagnosis = ResumeAnalyzer.analyze(extracted["raw_text"], filename)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "original_bytes": content,  # Preserved without modification
        "filename": filename,
        "format": extracted["format"],
        "raw_text": extracted["raw_text"],
        "pages_count": extracted["pages_count"],
        "initial_diagnosis": diagnosis,
        "optimized_structured": None,
        "optimized_text": None,
        "post_diagnosis": None,
        "comparison": None,
        "preservation": None,
        "steps": []
    }

    return {
        "session_id": session_id,
        "filename": filename,
        "format": extracted["format"],
        "char_count": extracted["char_count"],
        "word_count": extracted["word_count"],
        "pages_count": extracted["pages_count"],
        "has_extractable_text": extracted["has_extractable_text"],
        "initial_diagnosis": diagnosis.model_dump()
    }


@app.post("/api/optimize")
async def optimize_resume(req: OptimizeRequest):
    """Runs the automated optimization flow and re-inspects using identical criteria."""
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada. Faça o upload do currículo primeiro.")

    sess = sessions[session_id]
    original_text = sess["raw_text"]
    filename = sess["filename"]

    # 1. Optimize without hallucinating facts
    structured, opt_text, steps = ResumeOptimizer.optimize(original_text, filename)
    opt_markdown = ResumeOptimizer.render_to_markdown(structured)
    preview_html = DocumentExporter.generate_preview_html(structured)

    # 2. Re-inspect with EXACT SAME rules & criteria
    post_diagnosis = ResumeAnalyzer.analyze(opt_text, filename)

    # 3. Validate preservation of facts
    preservation = PreservationValidator.validate_preservation(original_text, opt_text)

    # 4. Compare before vs after
    comparison = ResumeComparer.compare(sess["initial_diagnosis"], post_diagnosis)

    # Save to session
    sess["optimized_structured"] = structured
    sess["optimized_text"] = opt_text
    sess["optimized_markdown"] = opt_markdown
    sess["post_diagnosis"] = post_diagnosis
    sess["comparison"] = comparison
    sess["preservation"] = preservation
    sess["steps"] = steps

    return {
        "session_id": session_id,
        "steps": [s.model_dump() for s in steps],
        "optimized_structured": structured.model_dump(),
        "optimized_text": opt_text,
        "optimized_markdown": opt_markdown,
        "preview_html": preview_html,
        "post_diagnosis": post_diagnosis.model_dump(),
        "comparison": comparison.model_dump(),
        "preservation": preservation.model_dump()
    }


@app.post("/api/format-markdown")
async def format_markdown(req: FormatMarkdownRequest):
    """Auto-formats messy or non-standard markdown into the canonical ATS standard."""
    raw_md = req.markdown_text.strip()
    if not raw_md:
        raise HTTPException(status_code=400, detail="Texto vazio.")

    structured = MarkdownResumeParser.parse(raw_md)
    canonical_md = ResumeOptimizer.render_to_markdown(structured)
    preview_html = DocumentExporter.generate_preview_html(structured)

    return {
        "formatted_markdown": canonical_md,
        "preview_html": preview_html,
        "structured": structured.model_dump()
    }


@app.post("/api/from-markdown")
async def from_markdown(req: FromMarkdownRequest):
    """Creates or updates a session directly from pasted Markdown and generates the beautiful CV."""
    markdown_text = req.markdown_text.strip()
    if not markdown_text:
        raise HTTPException(status_code=400, detail="O texto em Markdown não pode estar vazio.")

    session_id = req.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "session_id": session_id,
            "original_bytes": markdown_text.encode("utf-8"),
            "filename": "curriculo_markdown.md",
            "format": "MD",
            "raw_text": markdown_text,
            "pages_count": 1,
            "initial_diagnosis": None,
            "optimized_structured": None,
            "optimized_text": None,
            "post_diagnosis": None,
            "comparison": None,
            "preservation": None,
            "steps": []
        }

    sess = sessions[session_id]
    structured = MarkdownResumeParser.parse(markdown_text)
    opt_text = ResumeOptimizer.render_to_text(structured)
    opt_markdown = ResumeOptimizer.render_to_markdown(structured)
    preview_html = DocumentExporter.generate_preview_html(structured)

    diagnosis = ResumeAnalyzer.analyze(opt_text, sess["filename"])
    if not sess.get("initial_diagnosis"):
        sess["initial_diagnosis"] = diagnosis

    preservation = PreservationValidator.validate_preservation(sess["raw_text"], opt_text)
    comparison = ResumeComparer.compare(sess["initial_diagnosis"], diagnosis)

    sess["optimized_structured"] = structured
    sess["optimized_text"] = opt_text
    sess["optimized_markdown"] = opt_markdown
    sess["post_diagnosis"] = diagnosis
    sess["comparison"] = comparison
    sess["preservation"] = preservation

    return {
        "session_id": session_id,
        "preview_html": preview_html,
        "optimized_text": opt_text,
        "optimized_markdown": opt_markdown,
        "post_diagnosis": diagnosis.model_dump(),
        "comparison": comparison.model_dump(),
        "preservation": preservation.model_dump()
    }


@app.post("/api/manual-edit")
async def manual_edit_resume(req: ManualEditRequest):
    """Updates the optimized resume with user edits (plain text or Markdown) and recalculates inspection scores."""
    updated_input = req.edited_text.strip()
    if not updated_input:
        raise HTTPException(status_code=400, detail="O texto editado não pode estar vazio.")

    session_id = req.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "session_id": session_id,
            "original_bytes": updated_input.encode("utf-8"),
            "filename": "curriculo_editado.md",
            "format": "MD",
            "raw_text": updated_input,
            "pages_count": 1,
            "initial_diagnosis": None,
            "optimized_structured": None,
            "optimized_text": None,
            "post_diagnosis": None,
            "comparison": None,
            "preservation": None,
            "steps": []
        }

    sess = sessions[session_id]

    # Detect if user pasted Markdown (starts with # or contains ## or markdown links/bullets)
    is_markdown = "#" in updated_input or "**" in updated_input or "- " in updated_input

    if req.structured_data:
        try:
            structured = ResumeStructured(**req.structured_data)
        except Exception:
            structured = MarkdownResumeParser.parse(updated_input)
    elif is_markdown:
        structured = MarkdownResumeParser.parse(updated_input)
    else:
        structured, _, _ = ResumeOptimizer.optimize(updated_input, sess["filename"])

    opt_text = ResumeOptimizer.render_to_text(structured)
    opt_markdown = ResumeOptimizer.render_to_markdown(structured)
    preview_html = DocumentExporter.generate_preview_html(structured)

    sess["optimized_structured"] = structured
    sess["optimized_text"] = opt_text
    sess["optimized_markdown"] = opt_markdown

    # Re-inspect edited version with exact same rules
    post_diagnosis = ResumeAnalyzer.analyze(opt_text, sess["filename"])
    if not sess.get("initial_diagnosis"):
        sess["initial_diagnosis"] = post_diagnosis

    preservation = PreservationValidator.validate_preservation(sess["raw_text"], opt_text)
    comparison = ResumeComparer.compare(sess["initial_diagnosis"], post_diagnosis)

    sess["post_diagnosis"] = post_diagnosis
    sess["preservation"] = preservation
    sess["comparison"] = comparison

    return {
        "session_id": session_id,
        "optimized_text": opt_text,
        "optimized_markdown": opt_markdown,
        "preview_html": preview_html,
        "post_diagnosis": post_diagnosis.model_dump(),
        "comparison": comparison.model_dump(),
        "preservation": preservation.model_dump()
    }


@app.get("/api/export/docx")
async def export_docx(session_id: str):
    """Exports optimized resume in fully editable single-column DOCX."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    sess = sessions[session_id]

    struct = sess.get("optimized_structured")
    if not struct:
        # Fallback to structuring the text
        struct, _, _ = ResumeOptimizer.optimize(sess.get("optimized_text") or sess["raw_text"])

    docx_bytes = DocumentExporter.generate_resume_docx(struct)
    out_name = f"Curriculo_Otimizado_{sess['filename'].rsplit('.', 1)[0]}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )


@app.get("/api/export/pdf")
async def export_pdf(session_id: str):
    """Exports optimized resume in selectable PDF."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    sess = sessions[session_id]

    struct = sess.get("optimized_structured")
    if not struct:
        struct, _, _ = ResumeOptimizer.optimize(sess.get("optimized_text") or sess["raw_text"])

    pdf_bytes = DocumentExporter.generate_resume_pdf(struct)
    out_name = f"Curriculo_Otimizado_{sess['filename'].rsplit('.', 1)[0]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )


@app.get("/api/export/report")
async def export_report(session_id: str):
    """Exports detailed comparison audit report PDF."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    sess = sessions[session_id]

    comp = sess.get("comparison")
    init_diag = sess.get("initial_diagnosis")
    post_diag = sess.get("post_diagnosis")

    if not comp or not init_diag or not post_diag:
        raise HTTPException(status_code=400, detail="Execute a otimização antes de gerar o relatório.")

    report_bytes = DocumentExporter.generate_report_pdf(comp, init_diag, post_diag)
    out_name = f"Relatorio_Auditoria_ATS_{sess['filename'].rsplit('.', 1)[0]}.pdf"

    return Response(
        content=report_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )


@app.get("/api/export/checklist")
async def export_checklist(session_id: str):
    """Exports human pending recommendations checklist."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    sess = sessions[session_id]

    comp = sess.get("comparison")
    if not comp:
        raise HTTPException(status_code=400, detail="Execute a otimização primeiro.")

    text_content = DocumentExporter.generate_checklist_text(comp)
    out_name = f"Pendencias_Revisao_Manual_{sess['filename'].rsplit('.', 1)[0]}.txt"

    return Response(
        content=text_content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )


# Mount static directory for single-page app
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>CV Optimizer</h1><p>Frontend não encontrado em static/index.html</p>")
