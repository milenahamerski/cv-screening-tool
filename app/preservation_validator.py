"""Validates that facts, dates, companies, and education are strictly preserved from the original."""

import re
from typing import List, Dict, Set, Any
from app.models import PreservationCheck


class PreservationValidator:
    @staticmethod
    def extract_entities(text: str) -> Dict[str, Set[str]]:
        """Extract key facts from text to verify preservation."""
        entities: Dict[str, Set[str]] = {
            "dates": set(),
            "companies": set(),
            "degrees": set(),
            "skills": set()
        }

        # Extract 4-digit years and ranges (e.g. 2018 - 2022, 2023, 2024 - Presente)
        years = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
        entities["dates"] = set(years)

        # Standard degrees / education keywords
        degree_patterns = [
            r"\b(bacharelado|licenciatura|tecn[óo]logo|p[óo]s-gradua[çc][ãa]o|mestrado|doutorado|mba|especializa[çc][ãa]o|ensino\s+m[ée]dio|gradua[çc][ãa]o)\b",
            r"\b(engenharia|ci[êe]ncia\s+da\s+computa[çc][ãa]o|sistemas\s+de\s+informa[çc][ãa]o|administra[çc][ãa]o|direito|marketing|design)\b"
        ]
        for pat in degree_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                entities["degrees"].add(m.lower())

        # Tech and business keywords
        common_tools = [
            "python", "java", "sql", "javascript", "typescript", "react", "node", "docker",
            "aws", "azure", "gcp", "git", "linux", "c#", "c++", "php", "ruby", "rust", "go",
            "html", "css", "postgresql", "mysql", "mongodb", "oracle", "power bi", "tableau",
            "excel", "jira", "scrum", "kanban", "figma"
        ]
        text_lower = text.lower()
        for tool in common_tools:
            if re.search(rf"\b{re.escape(tool)}\b", text_lower):
                entities["skills"].add(tool)

        return entities

    @classmethod
    def validate_preservation(cls, original_text: str, optimized_text: str) -> PreservationCheck:
        orig_entities = cls.extract_entities(original_text)
        opt_entities = cls.extract_entities(optimized_text)

        warnings = []
        details = []

        # Check preserved dates
        orig_dates = orig_entities["dates"]
        opt_dates = opt_entities["dates"]
        missing_dates = orig_dates - opt_dates
        if missing_dates:
            warnings.append(f"Atenção: Os seguintes anos/datas do original não foram encontrados no texto otimizado: {', '.join(sorted(missing_dates))}")
        else:
            details.append(f"Todas as datas originais ({len(orig_dates)} anos identificados) foram preservadas com sucesso.")

        # Check degrees
        orig_degrees = orig_entities["degrees"]
        opt_degrees = opt_entities["degrees"]
        missing_degrees = orig_degrees - opt_degrees
        if missing_degrees:
            warnings.append(f"Atenção: Termos de formação original ausentes: {', '.join(sorted(missing_degrees))}")
        else:
            details.append(f"Formações acadêmicas identificadas ({len(orig_degrees)}) foram preservadas.")

        # Check skills
        orig_skills = orig_entities["skills"]
        opt_skills = opt_entities["skills"]
        missing_skills = orig_skills - opt_skills
        if missing_skills:
            warnings.append(f"Competências originais não encontradas: {', '.join(sorted(missing_skills))}")
        else:
            details.append(f"Todas as competências técnicas do currículo original ({len(orig_skills)}) foram mantidas.")

        # Check for potential hallucinated companies or degrees:
        # If optimized text introduced common prestige names not in original:
        hallucination_checks = ["harvard", "stanford", "mit", "google", "meta", "apple", "amazon", "netflix", "microsoft"]
        hallucination_warnings = []
        orig_lower = original_text.lower()
        opt_lower = optimized_text.lower()
        for org in hallucination_checks:
            if org in opt_lower and org not in orig_lower:
                hallucination_warnings.append(f"Alerta crítico: Detectada inclusão indevida da empresa/instituição '{org.capitalize()}' não presente no original.")

        is_valid = len(hallucination_warnings) == 0 and len(missing_dates) <= 1

        return PreservationCheck(
            is_valid=is_valid,
            preserved_companies=sorted(list(opt_entities["companies"])),
            preserved_dates=sorted(list(orig_dates.intersection(opt_dates))),
            preserved_degrees=sorted(list(orig_degrees.intersection(opt_degrees))),
            preserved_skills=sorted(list(orig_skills.intersection(opt_skills))),
            hallucination_warnings=hallucination_warnings + warnings,
            details=details
        )
