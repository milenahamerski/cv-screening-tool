"""Robust Markdown Resume Parser for CV Optimizer."""

import re
from typing import Dict, List, Optional, Tuple
from app.models import ResumeStructured, ResumeContact, ResumeExperience, ResumeEducation

# Complete regex for full and abbreviated months in Portuguese and English
MONTHS_PATTERN = r"(?:janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|january|february|march|april|may|june|july|august|september|october|november|december)"
DATE_PATTERN = rf"(\b(19\d{{2}}|20\d{{2}})\b|\b{MONTHS_PATTERN}\b|\b(atual|presente|em\s+andamento|atualmente|current|present)\b)"


def is_date_string(s: str) -> bool:
    return bool(re.search(DATE_PATTERN, s, re.IGNORECASE))


class MarkdownResumeParser:
    """Parses standard and flexible Markdown resumes into ResumeStructured models."""

    @classmethod
    def parse(cls, md_text: str) -> ResumeStructured:
        contact = ResumeContact()
        summary = ""
        experiences: List[ResumeExperience] = []
        education: List[ResumeEducation] = []
        skills: List[str] = []
        skill_categories: Dict[str, List[str]] = {}
        certifications: List[str] = []
        languages: List[str] = []

        lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        current_section = "topo"
        section_lines: Dict[str, List[str]] = {
            "topo": [],
            "resumo": [],
            "experiencia": [],
            "formacao": [],
            "habilidades": [],
            "certificacoes": [],
            "idiomas": [],
            "outros": []
        }

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # 1. Check for H1 (# Nome)
            if re.match(r"^#\s+", line_str) and not contact.name:
                contact.name = re.sub(r"^#\s+", "", line_str).replace("**", "").replace("__", "").strip()
                current_section = "topo"
                continue

            # 2. Check for Section Headers: H2 (## Seção) or uppercase standalone line
            is_h2 = bool(re.match(r"^##\s+", line_str))
            clean_heading = re.sub(r"^##\s+", "", line_str).replace("**", "").strip()
            sec_type = cls._identify_section(clean_heading)

            if is_h2:
                if sec_type:
                    current_section = sec_type
                    continue
                else:
                    current_section = "outros"
                    continue
            elif sec_type and len(clean_heading) < 40 and not line_str.startswith(("-", "•", "*", "+")):
                current_section = sec_type
                continue

            section_lines[current_section].append(line_str)

        # Parse contact details from topo lines
        topo_text = "\n".join(section_lines["topo"])
        contact = cls._parse_contact(topo_text, contact)

        # Parse summary
        summary_raw = "\n".join(section_lines["resumo"])
        summary = cls._clean_markdown(summary_raw)

        # Parse experiences
        experiences = cls._parse_experiences(section_lines["experiencia"])

        # Parse education
        education = cls._parse_education(section_lines["formacao"])

        # Parse skills
        skill_categories, skills = cls._parse_skills(section_lines["habilidades"])

        # Parse certifications
        certifications = cls._parse_simple_list(section_lines["certificacoes"])

        # Parse languages
        languages = cls._parse_languages(section_lines["idiomas"])

        return ResumeStructured(
            contact=contact,
            summary=summary,
            experiences=experiences,
            education=education,
            skills=skills,
            skill_categories=skill_categories,
            certifications=certifications,
            languages=languages,
            additional=[]
        )

    @staticmethod
    def _identify_section(title: str) -> Optional[str]:
        t = title.lower()
        if any(k in t for k in ["resumo", "perfil", "sobre mim", "summary", "objective", "profile", "about me"]):
            return "resumo"
        if any(k in t for k in ["experiência", "experiencia", "histórico", "atuação", "experience", "employment", "work history"]):
            return "experiencia"
        if any(k in t for k in ["formação", "formacao", "educação", "educacao", "escolaridade", "academic", "education", "graduação"]):
            return "formacao"
        if any(k in t for k in ["habilidade", "competência", "competencia", "tecnologia", "skills", "ferramenta", "technologies", "competencies"]):
            return "habilidades"
        if any(k in t for k in ["certifica", "curso", "projeto", "courses", "certificates", "projects"]):
            return "certificacoes"
        if any(k in t for k in ["idioma", "língua", "lingua", "language", "languages"]):
            return "idiomas"
        return None

    @classmethod
    def _parse_contact(cls, text: str, contact: ResumeContact) -> ResumeContact:
        for line in text.split("\n"):
            clean = line.replace("*", "").replace("#", "").strip()
            if clean and not contact.name and "@" not in clean and "http" not in clean and "|" not in clean:
                contact.name = clean
                break

        # Email
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        if email_match:
            contact.email = email_match.group(0).strip()

        # Phone
        phone_match = re.search(r"(\+?\d{1,3}\s*)?(\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}", text)
        if phone_match:
            contact.phone = phone_match.group(0).strip()

        # LinkedIn
        li_md = re.search(r"\[.*?\]\((https?://.*?linkedin\.com.*?)\)", text, re.IGNORECASE)
        if li_md:
            contact.linkedin = li_md.group(1).strip()
        else:
            li_plain = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
            if li_plain:
                contact.linkedin = li_plain.group(0).strip()
            elif "linkedin" in text.lower():
                contact.linkedin = "LinkedIn"

        # GitHub
        gh_md = re.search(r"\[.*?\]\((https?://.*?github\.com.*?)\)", text, re.IGNORECASE)
        if gh_md:
            contact.github = gh_md.group(1).strip()
        else:
            gh_plain = re.search(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
            if gh_plain:
                contact.github = gh_plain.group(0).strip()
            elif "github" in text.lower():
                contact.github = "GitHub"

        # Location
        loc_patterns = [
            r"\b([A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+)?\s*[-/,\s]+\s*[A-Z]{2})\b",
            r"\b(São Paulo|Rio de Janeiro|Curitiba|Belo Horizonte|Porto Alegre|Salvador|Brasília|Campinas|Florianópolis|Recife|Fortaleza|Guarapuava)\b",
            r"\b(Remoto|Híbrido|Presencial)\b"
        ]
        for pat in loc_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                contact.location = m.group(0).strip()
                break

        return contact

    @classmethod
    def _parse_experiences(cls, lines: List[str]) -> List[ResumeExperience]:
        experiences: List[ResumeExperience] = []
        current_exp: Optional[ResumeExperience] = None
        pending_company = ""

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            is_bullet = line_clean.startswith(("- ", "* ", "+ ", "• "))
            plain = re.sub(r"^#{1,4}\s+", "", line_clean)
            plain_no_bold = plain.replace("**", "").replace("__", "").strip()

            # Pattern A: Company in bold on its own line: **SICREDI PLANALTO...**
            is_bold_standalone = (
                line_clean.startswith("**") and line_clean.endswith("**")
                and not is_bullet
                and "|" not in plain_no_bold
                and not is_date_string(plain_no_bold)
            )

            if is_bold_standalone and len(plain_no_bold) < 90:
                pending_company = plain_no_bold
                continue

            has_pipe = " | " in plain_no_bold
            has_dates = is_date_string(plain_no_bold)
            is_h3 = line_clean.startswith("### ")

            # Pattern B: Job header line (Cargo | Período or Cargo | Empresa | Período)
            if not is_bullet and (is_h3 or has_dates or (has_pipe and len(plain_no_bold) < 130)):
                if current_exp:
                    experiences.append(current_exp)

                parts = [p.strip() for p in plain_no_bold.split("|") if p.strip()]
                title = ""
                company = pending_company
                period = ""

                if len(parts) >= 3:
                    title = parts[0]
                    company = parts[1]
                    period = parts[2]
                elif len(parts) == 2:
                    p1 = parts[1]
                    paren = re.search(r"\(([^)]+)\)", p1)
                    if paren and is_date_string(paren.group(1)):
                        title = parts[0]
                        period = paren.group(1).strip()
                        extracted_comp = (p1[:paren.start()] + p1[paren.end():]).strip()
                        if extracted_comp:
                            company = extracted_comp
                    elif pending_company and is_date_string(p1):
                        title = parts[0]
                        period = p1
                    elif is_date_string(p1) and not pending_company:
                        title = parts[0]
                        period = p1
                    else:
                        title = parts[0]
                        company = p1
                else:
                    title = parts[0]

                # Check if company or period were inside title like "Cargo - Empresa (Data)"
                if "(" in title and ")" in title and not period:
                    paren_match = re.search(r"\(([^)]+)\)", title)
                    if paren_match and is_date_string(paren_match.group(1)):
                        period = paren_match.group(1).strip()
                        title = title[:paren_match.start()] + title[paren_match.end():]
                        title = title.strip()

                if " - " in title and not company:
                    t_parts = title.split(" - ", 1)
                    title = t_parts[0].strip()
                    company = t_parts[1].strip()

                pending_company = ""
                current_exp = ResumeExperience(
                    title=title,
                    company=company,
                    location="",
                    period=period,
                    bullets=[]
                )
            else:
                if not current_exp:
                    current_exp = ResumeExperience(
                        title="Experiência Profissional",
                        company=pending_company,
                        location="",
                        period="",
                        bullets=[]
                    )
                    pending_company = ""

                bullet_text = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
                bullet_clean = cls._clean_markdown_inline(bullet_text)
                if bullet_clean:
                    current_exp.bullets.append(bullet_clean)

        if current_exp:
            experiences.append(current_exp)

        return experiences

    @classmethod
    def _parse_education(cls, lines: List[str]) -> List[ResumeEducation]:
        education: List[ResumeEducation] = []
        current_edu: Optional[ResumeEducation] = None
        pending_inst = ""

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            is_bullet = line_clean.startswith(("- ", "* ", "+ ", "• "))
            plain = re.sub(r"^#{1,4}\s+", "", line_clean)
            plain_no_bold = plain.replace("**", "").replace("__", "").strip()

            is_bold_standalone = (
                line_clean.startswith("**") and line_clean.endswith("**")
                and not is_bullet
                and "|" not in plain_no_bold
                and not is_date_string(plain_no_bold)
            )

            is_tcc = "tcc" in plain_no_bold.lower() or "conclusão de curso" in plain_no_bold.lower()

            # If TCC or thesis mention, attach to current education entry
            if is_tcc and current_edu:
                current_edu.details = plain_no_bold
                continue

            if is_bold_standalone and len(plain_no_bold) < 120 and not is_tcc:
                pending_inst = plain_no_bold
                continue

            has_pipe = " | " in plain_no_bold
            has_dates = is_date_string(plain_no_bold)
            is_h3 = line_clean.startswith("### ")

            if not is_bullet and not is_tcc and (is_h3 or has_dates or (has_pipe and len(plain_no_bold) < 130)):
                if current_edu:
                    education.append(current_edu)

                parts = [p.strip() for p in plain_no_bold.split("|") if p.strip()]
                degree = ""
                inst = pending_inst
                period = ""

                if len(parts) >= 3:
                    degree = parts[0]
                    inst = parts[1]
                    period = parts[2]
                elif len(parts) == 2:
                    p1 = parts[1]
                    paren = re.search(r"\(([^)]+)\)", p1)
                    if paren and is_date_string(paren.group(1)):
                        degree = parts[0]
                        period = paren.group(1).strip()
                        extracted_inst = (p1[:paren.start()] + p1[paren.end():]).strip()
                        if extracted_inst:
                            inst = extracted_inst
                    elif pending_inst and is_date_string(p1):
                        degree = parts[0]
                        period = p1
                    elif is_date_string(p1) and not pending_inst:
                        degree = parts[0]
                        period = p1
                    else:
                        degree = parts[0]
                        inst = p1
                else:
                    degree = parts[0]

                if not inst and " – " in degree:
                    d_parts = degree.split(" – ", 1)
                    degree = d_parts[0].strip()
                    inst = d_parts[1].strip()
                elif not inst and " - " in degree:
                    d_parts = degree.split(" - ", 1)
                    degree = d_parts[0].strip()
                    inst = d_parts[1].strip()

                pending_inst = ""
                current_edu = ResumeEducation(
                    degree=degree,
                    institution=inst,
                    period=period,
                    details="",
                    bullets=[]
                )
            elif current_edu:
                clean_b = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
                clean_b = cls._clean_markdown_inline(clean_b)
                if is_bullet:
                    current_edu.bullets.append(clean_b)
                else:
                    if current_edu.details:
                        current_edu.details += " " + clean_b
                    else:
                        current_edu.details = clean_b

        if current_edu:
            education.append(current_edu)

        return education

    @classmethod
    def _parse_skills(cls, lines: List[str]) -> Tuple[Dict[str, List[str]], List[str]]:
        categories: Dict[str, List[str]] = {}
        flat_skills: List[str] = []

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            clean = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
            # Match categorized formats: **Linguagens:** ... or **Linguagens**: ...
            cat_match = re.search(r"^\*\*(.*?)\*\*:\s*(.*)$", line_clean) or re.search(r"^\*\*(.*?):\*\*\s*(.*)$", line_clean)

            if cat_match:
                cat_name = cat_match.group(1).replace(":", "").strip()
                rest = cat_match.group(2).strip().rstrip(".")
                items = [re.sub(r"[*_]", "", i).strip().rstrip(".") for i in re.split(r"[,;•|]", rest) if i.strip()]
                categories[cat_name] = items
                for it in items:
                    if it not in flat_skills:
                        flat_skills.append(it)
            else:
                clean = clean.rstrip(".")
                items = [re.sub(r"[*_]", "", i).strip().rstrip(".") for i in re.split(r"[,;•|]", clean) if i.strip()]
                if items:
                    categories.setdefault("Competências", []).extend(items)
                    for it in items:
                        if it not in flat_skills:
                            flat_skills.append(it)

        return categories, flat_skills

    @classmethod
    def _parse_simple_list(cls, lines: List[str]) -> List[str]:
        items = []
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            clean = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
            clean = cls._clean_markdown_inline(clean)
            if clean:
                items.append(clean)
        return items

    @classmethod
    def _parse_languages(cls, lines: List[str]) -> List[str]:
        langs = []
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            clean = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
            clean = cls._clean_markdown_inline(clean)
            subitems = [i.strip() for i in re.split(r"[|•,;]", clean) if i.strip()]
            for s in subitems:
                if s and s not in langs:
                    langs.append(s)
        return langs

    @staticmethod
    def _clean_markdown(text: str) -> str:
        t = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
        t = re.sub(r"\*(.*?)\*", r"\1", t)
        t = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", t)
        return " ".join(t.split()).strip()

    @staticmethod
    def _clean_markdown_inline(text: str) -> str:
        t = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        t = re.sub(r"\*(.*?)\*", r"\1", t)
        t = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", t)
        return t.strip()
