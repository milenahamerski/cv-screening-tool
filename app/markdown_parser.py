"""Robust Markdown Resume Parser for CV Optimizer."""

import re
from typing import Dict, List, Optional
from app.models import ResumeStructured, ResumeContact, ResumeExperience, ResumeEducation


class MarkdownResumeParser:
    """Parses standard Markdown resumes into ResumeStructured models."""

    @classmethod
    def parse(cls, md_text: str) -> ResumeStructured:
        contact = ResumeContact()
        summary = ""
        experiences: List[ResumeExperience] = []
        education: List[ResumeEducation] = []
        skills: List[str] = []
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
                # Plain text uppercase section header like "EXPERIÊNCIA PROFISSIONAL"
                current_section = sec_type
                continue

            # Line belongs to current active section
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
        skills = cls._parse_skills(section_lines["habilidades"])

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
            certifications=certifications,
            languages=languages,
            additional=[]
        )

    @staticmethod
    def _identify_section(title: str) -> Optional[str]:
        t = title.lower()
        if any(k in t for k in ["resumo", "perfil", "sobre mim", "summary", "objective"]):
            return "resumo"
        if any(k in t for k in ["experiência", "experiencia", "histórico", "atuação", "experience"]):
            return "experiencia"
        if any(k in t for k in ["formação", "formacao", "educação", "educacao", "escolaridade", "academic", "graduação"]):
            return "formacao"
        if any(k in t for k in ["habilidade", "competência", "competencia", "tecnologia", "skills", "ferramenta"]):
            return "habilidades"
        if any(k in t for k in ["certifica", "curso", "projeto"]):
            return "certificacoes"
        if any(k in t for k in ["idioma", "língua", "lingua", "languages"]):
            return "idiomas"
        return None  # Crucial: return None so that subheadings like ### Job do not switch section!

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

        # LinkedIn (extract markdown link [LinkedIn](url) or plain URL)
        li_md = re.search(r"\[.*?\]\((https?://.*?linkedin\.com.*?)\)", text, re.IGNORECASE)
        if li_md:
            contact.linkedin = li_md.group(1).strip()
        else:
            li_plain = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
            if li_plain:
                contact.linkedin = li_plain.group(0).strip()

        # GitHub
        gh_md = re.search(r"\[.*?\]\((https?://.*?github\.com.*?)\)", text, re.IGNORECASE)
        if gh_md:
            contact.github = gh_md.group(1).strip()
        else:
            gh_plain = re.search(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
            if gh_plain:
                contact.github = gh_plain.group(0).strip()

        # Location
        loc_patterns = [
            r"\b([A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+)?\s*[-/,\s]+\s*[A-Z]{2})\b",
            r"\b(São Paulo|Rio de Janeiro|Curitiba|Belo Horizonte|Porto Alegre|Salvador|Brasília|Campinas|Florianópolis|Recife|Fortaleza)\b",
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

        date_pattern = r"(\b(19\d{2}|20\d{2})\b|\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|presente|atual|atualmente)\b)"

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Check if this line is a Job Header:
            # Starts with ###, or starts with **Cargo**, or has dates and separators without being a bullet
            is_h3 = line_clean.startswith("### ")
            is_bullet = line_clean.startswith(("- ", "* ", "+ ", "• "))
            has_dates = bool(re.search(date_pattern, line_clean, re.IGNORECASE))
            has_sep = any(sep in line_clean for sep in [" | ", " - ", " – "])

            if is_h3 or (not is_bullet and (has_dates or has_sep) and len(line_clean) < 130):
                if current_exp:
                    experiences.append(current_exp)

                header = re.sub(r"^#{1,4}\s+", "", line_clean).strip()
                header = header.replace("**", "").replace("__", "")

                period = ""
                paren_match = re.search(r"\(([^)]*(?:19\d{2}|20\d{2}|atual|presente)[^)]*)\)", header, re.IGNORECASE)
                if paren_match:
                    period = paren_match.group(1).strip()
                    header = header[:paren_match.start()] + header[paren_match.end():]
                else:
                    dm = re.search(r"((?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|\d{2})?[/.\s]?(?:19\d{2}|20\d{2})\s*(?:[-–a]\s*|\s*at[ée]\s*)(?:(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|\d{2})?[/.\s]?(?:19\d{2}|20\d{2})|presente|atual)?)", header, re.IGNORECASE)
                    if dm:
                        period = dm.group(1).strip()
                        header = header[:dm.start()] + header[dm.end():]

                parts = [p.strip() for p in re.split(r"(?:\s+[-–—]\s+|\s*\|\s*)", header) if p.strip()]
                title = parts[0] if len(parts) > 0 else header
                company = parts[1] if len(parts) > 1 else ""

                current_exp = ResumeExperience(
                    title=title,
                    company=company,
                    location="",
                    period=period,
                    bullets=[]
                )
            else:
                if not current_exp:
                    current_exp = ResumeExperience(title="Experiência Profissional", company="", location="", period="", bullets=[])

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
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            clean = re.sub(r"^#{1,4}\s+", "", line_clean).strip()
            clean = re.sub(r"^[\s•\-\*\+]+", "", clean).strip()
            clean = clean.replace("**", "").replace("__", "")

            period = ""
            paren_match = re.search(r"\(([^)]*(?:19\d{2}|20\d{2})[^)]*)\)", clean)
            if paren_match:
                period = paren_match.group(1).strip()
                clean = clean[:paren_match.start()] + clean[paren_match.end():]
            else:
                ym = re.search(r"\b(19\d{2}|20\d{2})\b", clean)
                if ym:
                    period = ym.group(0)

            parts = [p.strip() for p in re.split(r"(?:\s+[-–—]\s+|\s*\|\s*)", clean) if p.strip()]
            degree = parts[0] if len(parts) > 0 else clean
            inst = parts[1] if len(parts) > 1 else ""

            education.append(ResumeEducation(
                degree=degree,
                institution=inst,
                period=period,
                details=""
            ))
        return education

    @classmethod
    def _parse_skills(cls, lines: List[str]) -> List[str]:
        skills = []
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            clean = re.sub(r"^[\s•\-\*\+]+", "", line_clean).strip()
            # If line is categorized like "**Linguagens:** Python" or "**Linguagens**: Python"
            clean = re.sub(r"^\*\*[^*]+?\*\*:\s*|^\*\*[^*]+?:\*\*\s*", "", clean).strip()
            # Remove trailing dots
            clean = clean.rstrip(".")
            # Split items
            items = [re.sub(r"[*_]", "", i).strip().rstrip(".") for i in re.split(r"[,;•|]", clean) if i.strip()]
            for item in items:
                # Strip any leftover category label if preceded by colon
                if ":" in item:
                    item = item.split(":", 1)[1].strip()
                if item and len(item) < 45 and item not in skills:
                    skills.append(item)
        return skills

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
            # Split if piped like "Inglês | Francês" or comma separated
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
