"""Document Exporter for DOCX, PDF, and Comparison Reports."""

import io
from typing import Dict, Any, List
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models import ResumeStructured, ComparisonResult, DiagnosisResult


class DocumentExporter:
    """Generates professional, ATS-compliant DOCX and PDF documents."""

    # -------------------------------------------------------------
    # 1. OPTIMIZED RESUME IN DOCX (Single-column, fully editable)
    # -------------------------------------------------------------
    @classmethod
    def generate_resume_docx(cls, resume: ResumeStructured) -> bytes:
        doc = Document()

        # Set single-column standard 1 inch (2.54 cm) margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)

        # Base style: Calibri, 10.5 pt, clean line spacing
        normal_style = doc.styles["Normal"]
        normal_style.font.name = "Calibri"
        normal_style.font.size = Pt(10.5)
        normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

        # Header / Name
        name_p = doc.add_paragraph()
        name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_p.paragraph_format.space_before = Pt(0)
        name_p.paragraph_format.space_after = Pt(4)
        name_str = (resume.contact.name or "CURRÍCULO PROFISSIONAL").upper()
        run_name = name_p.add_run(name_str)
        run_name.bold = True
        run_name.font.size = Pt(20)
        run_name.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

        # Contact line
        contact_items = []
        if resume.contact.location:
            contact_items.append(resume.contact.location)
        if resume.contact.phone:
            contact_items.append(resume.contact.phone)
        if resume.contact.email:
            contact_items.append(resume.contact.email)
        if resume.contact.linkedin:
            contact_items.append(resume.contact.linkedin)
        if resume.contact.github:
            contact_items.append(resume.contact.github)

        if contact_items:
            cont_p = doc.add_paragraph()
            cont_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cont_p.paragraph_format.space_after = Pt(14)
            run_cont = cont_p.add_run("  |  ".join(contact_items))
            run_cont.font.size = Pt(9.5)
            run_cont.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

        # Helper for adding section headings with standard ATS formatting
        def add_heading(title: str):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)

            # Add a clean bottom border or divider line under the heading
            pPr = p._element.get_or_add_pPr()
            pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="2" w:color="0F2C59"/></w:pBdr>')
            pPr.append(pBdr)

        # Resumo Profissional
        if resume.summary:
            add_heading("Resumo Profissional")
            sum_p = doc.add_paragraph()
            sum_p.paragraph_format.space_after = Pt(8)
            sum_p.paragraph_format.line_spacing = 1.15
            run_sum = sum_p.add_run(resume.summary)
            run_sum.font.size = Pt(10)

        # Experiência Profissional
        if resume.experiences:
            add_heading("Experiência Profissional")
            for exp in resume.experiences:
                job_p = doc.add_paragraph()
                job_p.paragraph_format.space_before = Pt(6)
                job_p.paragraph_format.space_after = Pt(2)
                job_p.paragraph_format.keep_with_next = True

                title_run = job_p.add_run(exp.title or "Cargo")
                title_run.bold = True
                title_run.font.size = Pt(10.5)

                if exp.company:
                    comp_run = job_p.add_run(f" | {exp.company}")
                    comp_run.bold = True
                    comp_run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

                if exp.period:
                    per_run = job_p.add_run(f"  ({exp.period})")
                    per_run.italic = True
                    per_run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

                for b in exp.bullets:
                    bp = doc.add_paragraph(style="List Bullet")
                    bp.paragraph_format.space_before = Pt(1)
                    bp.paragraph_format.space_after = Pt(2)
                    bp.paragraph_format.line_spacing = 1.1
                    brun = bp.add_run(b)
                    brun.font.size = Pt(10)

        # Formação Acadêmica
        if resume.education:
            add_heading("Formação Acadêmica")
            for edu in resume.education:
                edu_p = doc.add_paragraph()
                edu_p.paragraph_format.space_before = Pt(4)
                edu_p.paragraph_format.space_after = Pt(2)

                d_run = edu_p.add_run(edu.degree or "Curso")
                d_run.bold = True
                d_run.font.size = Pt(10.5)

                if edu.institution:
                    i_run = edu_p.add_run(f" | {edu.institution}")
                    i_run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

                if edu.period:
                    p_run = edu_p.add_run(f"  ({edu.period})")
                    p_run.italic = True
                    p_run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

        # Habilidades e Tecnologias
        if resume.skills:
            add_heading("Habilidades e Tecnologias")
            sk_p = doc.add_paragraph()
            sk_p.paragraph_format.space_after = Pt(6)
            sk_run = sk_p.add_run(" • ".join(resume.skills))
            sk_run.font.size = Pt(10)

        # Certificações e Cursos
        if resume.certifications:
            add_heading("Certificações e Cursos")
            for cert in resume.certifications:
                cp = doc.add_paragraph(style="List Bullet")
                cp.paragraph_format.space_before = Pt(1)
                cp.paragraph_format.space_after = Pt(2)
                c_run = cp.add_run(cert)
                c_run.font.size = Pt(10)

        # Idiomas
        if resume.languages:
            add_heading("Idiomas")
            lang_p = doc.add_paragraph()
            lang_p.paragraph_format.space_after = Pt(6)
            lang_run = lang_p.add_run("  |  ".join(resume.languages))
            lang_run.font.size = Pt(10)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    # -------------------------------------------------------------
    # 2. OPTIMIZED RESUME IN SELECTABLE PDF (ReportLab)
    # -------------------------------------------------------------
    @classmethod
    def generate_resume_pdf(cls, resume: ResumeStructured) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            "NameStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=1,  # Center
            textColor=colors.HexColor("#0f2c59")
        )

        contact_style = ParagraphStyle(
            "ContactStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            alignment=1,  # Center
            textColor=colors.HexColor("#4b5563")
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f2c59"),
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#222222")
        )

        bullet_style = ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            leftIndent=14,
            firstLineIndent=-10,
            textColor=colors.HexColor("#222222")
        )

        story = []

        # Header: Name
        name_text = (resume.contact.name or "CURRÍCULO PROFISSIONAL").upper()
        story.append(Paragraph(name_text, name_style))
        story.append(Spacer(1, 4))

        # Contact Info
        contact_items = []
        if resume.contact.location:
            contact_items.append(resume.contact.location)
        if resume.contact.phone:
            contact_items.append(resume.contact.phone)
        if resume.contact.email:
            contact_items.append(resume.contact.email)
        if resume.contact.linkedin:
            contact_items.append(resume.contact.linkedin)
        if resume.contact.github:
            contact_items.append(resume.contact.github)

        if contact_items:
            story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_items), contact_style))
            story.append(Spacer(1, 8))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

        # Helper for headings
        def add_pdf_heading(title: str):
            story.append(Paragraph(title.upper(), heading_style))
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#0f2c59"), spaceAfter=6))

        # Summary
        if resume.summary:
            add_pdf_heading("Resumo Profissional")
            story.append(Paragraph(resume.summary, body_style))
            story.append(Spacer(1, 6))

        # Experience
        if resume.experiences:
            add_pdf_heading("Experiência Profissional")
            for exp in resume.experiences:
                exp_header = f"<b>{exp.title or 'Cargo'}</b>"
                if exp.company:
                    exp_header += f" &nbsp;|&nbsp; <b>{exp.company}</b>"
                if exp.period:
                    exp_header += f" &nbsp;<i>({exp.period})</i>"
                story.append(Paragraph(exp_header, body_style))
                story.append(Spacer(1, 2))

                for b in exp.bullets:
                    story.append(Paragraph(f"• {b}", bullet_style))
                    story.append(Spacer(1, 1.5))
                story.append(Spacer(1, 4))

        # Education
        if resume.education:
            add_pdf_heading("Formação Acadêmica")
            for edu in resume.education:
                edu_line = f"<b>{edu.degree}</b>"
                if edu.institution:
                    edu_line += f" &nbsp;|&nbsp; {edu.institution}"
                if edu.period:
                    edu_line += f" &nbsp;<i>({edu.period})</i>"
                story.append(Paragraph(edu_line, body_style))
                story.append(Spacer(1, 3))

        # Skills
        if resume.skills:
            add_pdf_heading("Habilidades e Tecnologias")
            skills_line = " &nbsp;•&nbsp; ".join(resume.skills)
            story.append(Paragraph(skills_line, body_style))
            story.append(Spacer(1, 6))

        # Certifications
        if resume.certifications:
            add_pdf_heading("Certificações e Cursos")
            for cert in resume.certifications:
                story.append(Paragraph(f"• {cert}", bullet_style))
            story.append(Spacer(1, 6))

        # Languages
        if resume.languages:
            add_pdf_heading("Idiomas")
            story.append(Paragraph(" &nbsp;|&nbsp; ".join(resume.languages), body_style))

        doc.build(story)
        return buf.getvalue()

    # -------------------------------------------------------------
    # 3. COMPARISON AUDIT REPORT (PDF)
    # -------------------------------------------------------------
    @classmethod
    def generate_report_pdf(cls, comparison: ComparisonResult, initial: DiagnosisResult, post: DiagnosisResult) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "RepTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f2c59")
        )

        sub_style = ParagraphStyle(
            "RepSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b5563")
        )

        h2_style = ParagraphStyle(
            "RepH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f2c59"),
            spaceBefore=10,
            spaceAfter=4
        )

        cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11)
        cell_bold = ParagraphStyle("CellB", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11)

        story = []
        story.append(Paragraph("CV Optimizer — Relatório de Análise e Auditoria ATS", title_style))
        story.append(Paragraph("Comparação técnica detalhada entre o documento original e a versão otimizada.", sub_style))
        story.append(Spacer(1, 10))

        # Score Overview Table
        score_data = [
            [
                Paragraph("<b>Versão Original</b>", cell_bold),
                Paragraph("<b>Versão Otimizada</b>", cell_bold),
                Paragraph("<b>Diferença Absoluta</b>", cell_bold)
            ],
            [
                Paragraph(f"<font size=14 color='#b91c1c'><b>{comparison.original_score}/100</b></font>", cell_style),
                Paragraph(f"<font size=14 color='#15803d'><b>{comparison.optimized_score}/100</b></font>", cell_style),
                Paragraph(f"<font size=14 color='#0284c7'><b>+{comparison.absolute_delta} pts</b></font>", cell_style),
            ]
        ]
        score_table = Table(score_data, colWidths=[175, 175, 175])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 14))

        # Disclaimer required by prompt: Not a hiring probability
        disclaimer = Paragraph(
            "<i>Nota: A pontuação reflete a conformidade técnica estrutural e textual com leitores ATS (Applicant Tracking Systems), não representando probabilidade de aprovação ou contratação.</i>",
            sub_style
        )
        story.append(disclaimer)
        story.append(Spacer(1, 10))

        # Criteria Breakdown Table
        story.append(Paragraph("Comparação por Critério de Avaliação", h2_style))
        crit_rows = [[
            Paragraph("<b>Critério</b>", cell_bold),
            Paragraph("<b>Antes</b>", cell_bold),
            Paragraph("<b>Depois</b>", cell_bold),
            Paragraph("<b>Delta</b>", cell_bold),
            Paragraph("<b>Status Pós-Otimização</b>", cell_bold)
        ]]

        for c in comparison.criteria_comparison:
            delta_str = f"+{c['delta']}" if c['delta'] > 0 else f"{c['delta']}"
            crit_rows.append([
                Paragraph(c["name"], cell_style),
                Paragraph(f"{c['before_score']}/{c['max_score']}", cell_style),
                Paragraph(f"{c['after_score']}/{c['max_score']}", cell_style),
                Paragraph(f"<b>{delta_str}</b>", cell_style),
                Paragraph(c["status_after"], cell_style)
            ])

        crit_table = Table(crit_rows, colWidths=[185, 60, 60, 55, 165])
        crit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(crit_table)
        story.append(Spacer(1, 14))

        # Issues Resolution
        story.append(Paragraph("Status de Resolução dos Problemas Identificados", h2_style))
        
        if comparison.resolved_issues:
            story.append(Paragraph("<b>Problemas Resolvidos Automaticamente:</b>", cell_bold))
            for r in comparison.resolved_issues:
                story.append(Paragraph(f"• <b>{r.issue}</b>: {r.explanation}", cell_style))
                story.append(Spacer(1, 2))
            story.append(Spacer(1, 6))

        if comparison.unresolved_issues:
            story.append(Paragraph("<b>Problemas Não Resolvidos (Preservação Ética / Dados Ausentes):</b>", cell_bold))
            for u in comparison.unresolved_issues:
                story.append(Paragraph(f"• <b>{u.issue}</b>: {u.explanation}", cell_style))
                story.append(Spacer(1, 2))
            story.append(Spacer(1, 6))

        # Human Action Checklist
        story.append(Paragraph("Pendências para Revisão Manual (Ações Humanas)", h2_style))
        for rec in comparison.human_recommendations:
            badge = f"[{rec.priority.upper()}]"
            story.append(Paragraph(f"<b>{badge} {rec.title}</b>", cell_bold))
            story.append(Paragraph(f"<b>Problema:</b> {rec.problem}", cell_style))
            story.append(Paragraph(f"<b>Por que importa:</b> {rec.why_matters}", cell_style))
            story.append(Paragraph(f"<b>O que fazer:</b> {rec.what_to_do}", cell_style))
            if rec.example:
                story.append(Paragraph(f"<b>Exemplo:</b> <i>{rec.example}</i>", cell_style))
            story.append(Spacer(1, 5))

        doc.build(story)
        return buf.getvalue()

    # -------------------------------------------------------------
    # 4. PENDING ACTION CHECKLIST (Markdown / TXT)
    # -------------------------------------------------------------
    @classmethod
    def generate_checklist_text(cls, comparison: ComparisonResult) -> str:
        lines = [
            "# CV OPTIMIZER — LISTA DE PENDÊNCIAS E REVISÃO MANUAL",
            "=====================================================",
            "Este checklist contém melhorias essenciais que dependem exclusivamente",
            "da confirmação e inserção de dados pelo candidato (sem invenção de dados).",
            "",
            "## 1. RECOMENDAÇÕES DE ALTA PRIORIDADE (Dados importantes ausentes)",
        ]

        high = [r for r in comparison.human_recommendations if r.priority == "alta"]
        for r in high:
            lines.append(f"[{r.id}] {r.title}")
            lines.append(f"  - Problema: {r.problem}")
            lines.append(f"  - Por que importa: {r.why_matters}")
            lines.append(f"  - O que você deve fazer: {r.what_to_do}")
            if r.example:
                lines.append(f"  - Exemplo prático: {r.example}")
            lines.append("")

        lines.append("## 2. RECOMENDAÇÕES DE MÉDIA PRIORIDADE (Conteúdo e Detalhamento)")
        med = [r for r in comparison.human_recommendations if r.priority == "media"]
        for r in med:
            lines.append(f"[{r.id}] {r.title}")
            lines.append(f"  - Problema: {r.problem}")
            lines.append(f"  - Por que importa: {r.why_matters}")
            lines.append(f"  - O que você deve fazer: {r.what_to_do}")
            if r.example:
                lines.append(f"  - Exemplo prático: {r.example}")
            lines.append("")

        lines.append("## 3. RECOMENDAÇÕES DE BAIXA PRIORIDADE (Refinamento de Escrita)")
        low = [r for r in comparison.human_recommendations if r.priority == "baixa"]
        for r in low:
            lines.append(f"[{r.id}] {r.title}")
            lines.append(f"  - Problema: {r.problem}")
            lines.append(f"  - Por que importa: {r.why_matters}")
            lines.append(f"  - O que você deve fazer: {r.what_to_do}")
            if r.example:
                lines.append(f"  - Exemplo prático: {r.example}")
            lines.append("")

        return "\n".join(lines)
