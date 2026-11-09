"""Objective and documented ATS Resume Analyzer supporting both Portuguese and English resumes."""

import re
from typing import Dict, Any, List, Tuple
from app.models import CriterionScore, DiagnosisResult


# Action verbs commonly expected in strong resumes (Portuguese and English)
ACTION_VERBS = [
    # Portuguese past tense / infinitive
    r"\b(desenvolveu|desenvolver|implementou|implementar|liderou|liderar|coordenou|coordenar)\b",
    r"\b(gerenciou|gerenciar|otimizou|otimizar|construiu|construir|arquitetou|arquitetar)\b",
    r"\b(reduziu|reduzir|aumentou|aumentar|estruturou|estruturar|conduziu|conduzir)\b",
    r"\b(elaborou|elaborar|automatizou|automatizar|integrou|integrar|entregou|entregar)\b",
    r"\b(executou|executar|criou|criar|padronizou|padronizar|negociou|negociar)\b",
    r"\b(supervisionou|supervisionar|transformou|transformar|modernizou|modernizar)\b",
    r"\b(superou|superar|gerou|gerar|alcançou|alcançar|acelerou|acelerar)\b",
    # English Action Verbs (US/UK ATS Standard)
    r"\b(developed|engineered|architected|implemented|built|designed|constructed|created|programmed|coded|authored)\b",
    r"\b(led|spearheaded|managed|directed|orchestrated|supervised|coordinated|guided|mentored|championed)\b",
    r"\b(optimized|streamlined|accelerated|automated|refactored|enhanced|boosted|maximized|upgraded|revamped)\b",
    r"\b(reduced|increased|scaled|delivered|launched|generated|achieved|cut|saved|doubled|tripled|expanded)\b",
    r"\b(collaborated|partnered|negotiated|integrated|deployed|migrated|published|formulated|executed|established)\b",
    r"\b(analyzed|investigated|diagnosed|resolved|troubleshot|solved|evaluated|audited|standardized|modernized)\b",
]

# Sensitive or outdated personal data that ATS and modern recruiters advise against
DISCOURAGED_DATA_PATTERNS = [
    (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "CPF exposto (desnecessário para triagem inicial)"),
    (r"\b(rg|identidade)\s*[:.\s]\s*\d+", "RG exposto (desnecessário)"),
    (r"\b(solteiro|solteira|casado|casada|divorciado|divorciada|viúvo|viúva|single|married|divorced)\b", "Estado civil mencionado (não recomendado em padrões ATS)"),
    (r"\b(habilitação\s*[ab]|cnh\s*[ab]|categoria\s*[ab]|driver'?s?\s+license)\b", "CNH/carteira de motorista mencionada sem contexto de vaga de motorista"),
    (r"\b(rua|avenida|travessa|alameda)\s+[a-z0-9\s]+,\s*n?[ºo]?\s*\d+", "Endereço residencial completo (recomenda-se apenas Cidade - UF / Country)"),
    (r"\b(ssn|social\s+security\s+number)\s*[:.\s]\s*\d+", "SSN exposto (altamente confidencial e desnecessário em currículo)"),
]

# Standard ATS Section Titles (Portuguese and English)
STANDARD_SECTIONS = {
    "contato": [
        r"\bcontato\b", r"\binformações\s+de\s+contato\b", r"\bdados\s+pessoais\b",
        r"\bcontact\b", r"\bcontact\s+(information|info|details)\b", r"\bpersonal\s+details\b"
    ],
    "resumo": [
        r"\bresumo\b", r"\bresumo\s+profissional\b", r"\bperfil\b", r"\bperfil\s+profissional\b", r"\bsobre\s+mim\b",
        r"\bobjective\b", r"\bsummary\b", r"\bprofessional\s+summary\b", r"\bexecutive\s+summary\b", r"\bcareer\s+objective\b", r"\babout\s+me\b"
    ],
    "experiencia": [
        r"\bexperi[êe]ncia(s)?\b", r"\bexperi[êe]ncia\s+profissional\b", r"\bhist[óo]rico\s+profissional\b", r"\batua[çc][ãa]o\s+profissional\b",
        r"\bwork\s+experience\b", r"\bprofessional\s+experience\b", r"\bemployment\s+history\b", r"\bexperience\b", r"\bwork\s+history\b"
    ],
    "formacao": [
        r"\bforma[çc][ãa]o\b", r"\bforma[çc][ãa]o\s+acad[êe]mica\b", r"\beduca[çc][ãa]o\b", r"\bescolaridade\b",
        r"\beducation\b", r"\bacademic\s+background\b", r"\beducational\s+background\b", r"\bacademic\s+history\b"
    ],
    "habilidades": [
        r"\bhabilidades\b", r"\bcompet[êe]ncias\b", r"\bconhecimentos\s+t[ée]cnicos\b", r"\btecnologias\b",
        r"\bskills\b", r"\btechnical\s+skills\b", r"\bcore\s+competencies\b", r"\btools\b", r"\btechnologies\b"
    ],
    "certificacoes": [
        r"\bcertifica[çc][õo]es\b", r"\bcursos\b", r"\bcertificados\b", r"\bprojetos\b", r"\bidiomas\b",
        r"\bcertifications\b", r"\bcertificates\b", r"\bcourses\b", r"\blanguages\b", r"\bprojects\b"
    ],
}


class ResumeAnalyzer:
    """Evaluates resumes using objective, transparent, and documented criteria for Portuguese and English."""

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detects whether resume is primarily in English ('en') or Portuguese ('pt')."""
        t = text.lower()
        pt_markers = [
            r"\bexperi[êe]ncia(s)?\b", r"\bforma[çc][ãa]o\b", r"\bdesenvolveu\b", r"\bresumo\b",
            r"\bhabilidades\b", r"\bcompet[êe]ncias\b", r"\bcom\b", r"\bpara\b", r"\batual\b",
            r"\bano(s)?\b", r"\batuou\b", r"\bconhecimento(s)?\b", r"\bgradua[çc][ãa]o\b",
            r"\bmeses\b", r"\bempresa\b", r"\bcargo\b"
        ]
        en_markers = [
            r"\bexperience\b", r"\beducation\b", r"\bdeveloped\b", r"\bsummary\b",
            r"\bskills\b", r"\btechnologies\b", r"\bwith\b", r"\bfor\b", r"\bpresent\b",
            r"\byear(s)?\b", r"\bmanaged\b", r"\bimplemented\b", r"\bdegree\b", r"\bengineered\b",
            r"\bmonths\b", r"\bcompany\b", r"\bposition\b"
        ]
        pt_matches = sum(1 for p in pt_markers if re.search(p, t))
        en_matches = sum(1 for p in en_markers if re.search(p, t))
        return "en" if en_matches > pt_matches else "pt"

    @classmethod
    def analyze(cls, text: str, original_filename: str = "") -> DiagnosisResult:
        if not text or len(text.strip()) < 10:
            return cls._empty_result()

        norm_text = text.strip()
        lines = [line.strip() for line in norm_text.split("\n") if line.strip()]
        word_count = len(norm_text.split())
        char_count = len(norm_text)

        language = cls.detect_language(norm_text)
        is_en = (language == "en")

        # 1. Evaluate Structure & Headings (Max 20 pts)
        c_structure = cls._eval_structure(norm_text, lines, is_en)

        # 2. Evaluate Impact & Concrete Metrics (Max 20 pts)
        c_impact = cls._eval_impact(norm_text, lines, is_en)

        # 3. Evaluate Professional Writing & Action Verbs (Max 15 pts)
        c_verbs = cls._eval_verbs_and_tone(norm_text, lines, is_en)

        # 4. Evaluate Keywords & Skills (Max 15 pts)
        c_keywords = cls._eval_keywords(norm_text, is_en)

        # 5. Evaluate ATS Readability & Parsing (Max 15 pts)
        c_readability = cls._eval_readability(norm_text, word_count, is_en)

        # 6. Evaluate Contact Completeness (Max 15 pts)
        c_contact = cls._eval_contact(norm_text, is_en)

        criteria = [c_structure, c_impact, c_verbs, c_keywords, c_readability, c_contact]
        overall_score = int(round(sum(c.score for c in criteria)))
        overall_score = max(0, min(100, overall_score))

        key_issues = []
        positive_points = []
        initial_recommendations = []

        if is_en:
            positive_points.append("Padrão ATS Internacional: Documento analisado sob convenções de triagem US/UK/Global.")

        for c in criteria:
            if c.percentage >= 80:
                positive_points.append(f"{c.name}: {c.details[0] if c.details else 'Atende plenamente aos padrões recomendados.'}")
            elif c.percentage < 60:
                for det in c.details:
                    if any(det.startswith(p) for p in ["[Atenção]", "[Ausente]", "[Incompleto]", "⚠️", "❌"]) or "Ausente" in det or "pouco" in det.lower() or "não encontrado" in det.lower():
                        clean = det
                        for prefix in ["[Atenção] ", "[Ausente] ", "[Incompleto] ", "⚠️ ", "❌ "]:
                            clean = clean.replace(prefix, "")
                        key_issues.append(f"[{c.name}] {clean}")
            
            # Extract actionable recommendations
            for det in c.details:
                if det.startswith("[Recomendação]") or det.startswith("💡"):
                    clean = det.replace("[Recomendação] ", "").replace("💡 ", "")
                    initial_recommendations.append(clean)

        # Detected sections list
        detected = []
        for sec, patterns in STANDARD_SECTIONS.items():
            for pat in patterns:
                if re.search(pat, norm_text, re.IGNORECASE):
                    detected.append(sec.capitalize())
                    break

        return DiagnosisResult(
            overall_score=overall_score,
            criteria=criteria,
            key_issues=key_issues[:8],
            positive_points=positive_points[:6],
            initial_recommendations=initial_recommendations[:8],
            char_count=char_count,
            word_count=word_count,
            has_extractable_text=True,
            detected_sections=detected,
            language=language
        )

    @staticmethod
    def _eval_structure(text: str, lines: List[str], is_en: bool = False) -> CriterionScore:
        weight = 20.0
        score = 0.0
        details = []

        found_sections = {}
        for sec, patterns in STANDARD_SECTIONS.items():
            found = any(re.search(pat, text, re.IGNORECASE) for pat in patterns)
            found_sections[sec] = found

        # 1. Experiência (6 pts)
        if found_sections["experiencia"]:
            score += 6.0
            sec_name = "Experiência Profissional ('Work Experience')" if is_en else "Experiência Profissional"
            details.append(f"Seção de {sec_name} identificada.")
        else:
            missing_name = "Work Experience / Professional Experience" if is_en else "Experiência Profissional"
            details.append(f"[Ausente] Seção de {missing_name} não identificada com título convencional.")

        # 2. Formação (5 pts)
        if found_sections["formacao"]:
            score += 5.0
            sec_name = "Formação Acadêmica ('Education')" if is_en else "Formação Acadêmica"
            details.append(f"Seção de {sec_name} identificada.")
        else:
            missing_name = "Education / Academic Background" if is_en else "Formação Acadêmica"
            details.append(f"[Ausente] Seção de {missing_name} ausente ou com nomenclatura não convencional.")

        # 3. Habilidades (4 pts)
        if found_sections["habilidades"]:
            score += 4.0
            sec_name = "Habilidades e Competências ('Skills & Technologies')" if is_en else "Habilidades e Competências"
            details.append(f"Seção de {sec_name} presente.")
        else:
            rec_sec = "Skills / Technologies" if is_en else "Habilidades e Tecnologias"
            details.append("[Atenção] Seção dedicada de Habilidades e Tecnologias ausente.")
            details.append(f"[Recomendação] Crie uma seção '{rec_sec}' para facilitar a indexação automática pelo ATS.")

        # 4. Contato (3 pts)
        if found_sections["contato"]:
            score += 3.0
            sec_name = "informações de contato ('Contact Info')" if is_en else "informações de contato"
            details.append(f"Cabeçalho de {sec_name} identificado.")
        else:
            score += 1.5
            details.append("Informações de contato detectadas no topo, mas sem seção explícita.")

        # 5. Resumo (2 pts)
        if found_sections["resumo"]:
            score += 2.0
            sec_name = "Resumo/Perfil Profissional ('Summary')" if is_en else "Resumo/Perfil Profissional"
            details.append(f"{sec_name} presente no início do documento.")
        else:
            rec_sum = "Professional Summary" if is_en else "Resumo Profissional"
            details.append(f"[Recomendação] Inclua um {rec_sum} conciso (3 a 5 linhas) no início do currículo.")

        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="structure",
            name="Estrutura e Títulos Convencionais",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @staticmethod
    def _eval_impact(text: str, lines: List[str], is_en: bool = False) -> CriterionScore:
        weight = 20.0
        score = 0.0
        details = []

        # Find numbers, percentages, currency, multipliers, metrics (PT and EN)
        metric_patterns = [
            r"\d+(?:[.,]\d+)?\s*%",                          # Percentages: 25%, 15.5%, 99.99%
            r"(?:r\$|usd|\$|€|£)\s*\d+(?:[.,]\d+)*",        # Currency: $100,000, R$ 50.000, £80k
            r"\b\d+(?:[.,]\d+)?\s*(?:k|m|b|million|millions|billion|billions)\b", # 100k, 2.5M
            r"\b\d+(?:[.,]\d+)*\s*(?:milhões|mil|milhoes|usuarios|usuários|clientes|projetos|processos|membros|equipes|pessoas)\b",
            r"\b\d+(?:[.,]\d+)*\s*(?:users|clients|customers|projects|processes|members|teams|engineers|people|stakeholders|events|requests|features)\b",
            r"\b\d+\s*(?:horas|dias|meses|anos|pontos|reuniões|sprints)\b",
            r"\b\d+\s*(?:hours|days|weeks|months|years|sprints|points|pts)\b",
            r"\b(?:aumento|redução|reducao|crescimento|economia|eficiência|ganho)\s+de\s+\d+",
            r"\b(?:increased|reduced|decreased|saved|cut|boosted|grew|accelerated)\s+(?:by\s+)?\d+",
            r"\b(?:top\s*\d+|1º|2º|3º|primeiro\s+lugar|first\s+place)\b",
            r"\b\d+\s*(?:x|vezes|times|-fold)\b"
        ]

        found_spans = set()
        found_metrics = []
        for pat in metric_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                span = match.span()
                # Check for overlap
                if not any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in found_spans):
                    found_spans.add(span)
                    found_metrics.append(match.group(0))

        metric_count = len(found_metrics)

        # Baseline points
        if metric_count >= 6:
            score = 20.0
            details.append(f"Excelente densidade de métricas e resultados quantitativos ({metric_count} ocorrências identificadas).")
        elif metric_count >= 4:
            score = 16.0
            details.append(f"Boa quantidade de dados quantitativos ({metric_count} resultados/métricas encontrados).")
        elif metric_count >= 2:
            score = 11.0
            details.append(f"Poucos resultados numéricos ou métricas concretas identificadas ({metric_count} ocorrências).")
            if is_en:
                details.append("[Recomendação] Inclua números reais nos resultados das suas experiências (ex: 'reduced latency by 30%', 'saved $50k annually', 'managed team of 8 engineers').")
            else:
                details.append("[Recomendação] Inclua números reais nos resultados das suas experiências (ex: % de aumento de eficiência, economia gerada, volume de entregas).")
        elif metric_count == 1:
            score = 6.0
            details.append("Apenas 1 resultado quantitativo encontrado.")
            details.append("[Recomendação] Destaque impactos mensuráveis nas descrições de cargo em vez de listar apenas tarefas rotineiras.")
        else:
            score = 3.0
            details.append("[Ausente] Nenhuma métrica mensurável (porcentagens, prazos, reduções, volumes) identificada.")
            if is_en:
                details.append("[Recomendação] ATS e recrutadores internacionais valorizam resultados concretos (ex: 'scaled infrastructure to 500k active users', 'improved throughput by 2x').")
            else:
                details.append("[Recomendação] ATS e recrutadores valorizam resultados concretos (ex: 'reduziu tempo de resposta em 30%', 'gerenciou equipe de 8 profissionais').")

        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="impact",
            name="Impacto e Resultados Concretos",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @staticmethod
    def _eval_verbs_and_tone(text: str, lines: List[str], is_en: bool = False) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        # Count action verbs (PT and EN)
        matched_verbs = set()
        for pat in ACTION_VERBS:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                matched_verbs.add(m.lower())

        verb_count = len(matched_verbs)

        # Check for first-person pronouns
        if is_en:
            first_person_matches = re.findall(r"\b(i\s|my\s|me\s|myself\s|we\s|our\s)", text, re.IGNORECASE)
            passive_matches = re.findall(r"\b(responsible\s+for|duties\s+included|tasked\s+with|worked\s+on)\b", text, re.IGNORECASE)
        else:
            first_person_matches = re.findall(r"\b(eu\s|meu\s|minha\s|participei\b|fiz\b|trabalhei\b|ajudei\b)", text, re.IGNORECASE)
            passive_matches = re.findall(r"\b(respons[áa]vel\s+por|trabalhou\s+com|ajudou\s+em)\b", text, re.IGNORECASE)

        sample_verbs = ", ".join(sorted(list(matched_verbs))[:4])

        if verb_count >= 8:
            score += 10.0
            lang_label = "em inglês" if is_en else "profissionais"
            details.append(f"Excelente emprego de verbos de ação {lang_label} ({verb_count} verbos de impacto distintos identificados: {sample_verbs}...).")
        elif verb_count >= 4:
            score += 7.0
            lang_label = "em inglês" if is_en else "de ação"
            details.append(f"Bom uso de verbos {lang_label} ({verb_count} verbos identificados: {sample_verbs}).")
        elif verb_count >= 2:
            score += 4.0
            details.append(f"Uso modesto de verbos de ação ({verb_count} verbos identificados).")
            if is_en:
                details.append("[Recomendação] Inicie os tópicos de experiência com verbos no passado de ação (ex: 'Developed', 'Engineered', 'Optimized', 'Spearheaded').")
            else:
                details.append("[Recomendação] Inicie os tópicos de experiência com verbos no passado de ação (ex: 'Desenvolveu', 'Implementou', 'Coordenou').")
        else:
            score += 1.5
            details.append("[Ausente] Pouquíssimos verbos de ação identificados. As frases parecem descrições passivas.")
            if is_en:
                details.append("[Recomendação] Substitua 'Responsible for...' por verbos diretos como 'Led', 'Engineered', 'Optimized', 'Architected'.")
            else:
                details.append("[Recomendação] Substitua 'Responsável por...' por verbos diretos como 'Liderou', 'Otimizou', 'Implementou'.")

        # Flag passive phrases if detected
        if len(passive_matches) > 0 and is_en:
            details.append("[Recomendação] Detectado uso de frases passivas ('Responsible for...'). Recomenda-se iniciar diretamente com o verbo de ação.")

        # Bullet point formatting check
        bullet_lines = [l for l in lines if l.startswith("-") or l.startswith("•") or l.startswith("*")]
        if len(bullet_lines) >= 4:
            score += 4.0
            details.append("Experiências estruturadas em tópicos (bullet points), facilitando a leitura rápida.")
        elif len(bullet_lines) >= 1:
            score += 2.0
            details.append("Uso parcial de tópicos.")
        else:
            details.append("[Atenção] Poucos ou nenhum marcador de tópico (bullets). Textos em blocos densos dificultam a triagem.")
            details.append("[Recomendação] Separe realizações em tópicos curtos iniciados por verbos de ação.")

        # First person check
        if len(first_person_matches) > 2:
            score = max(0.0, score - 2.0)
            if is_en:
                details.append("[Atenção] Detectado uso de primeira pessoa em inglês ('I', 'my', 'we'). Em currículos no padrão US/UK, recomenda-se voz ativa impessoal.")
            else:
                details.append("[Atenção] Detectado uso de primeira pessoa ('eu', 'meu', 'participei'). Em currículos, recomenda-se voz ativa impessoal.")
        else:
            score += 1.0

        score = min(weight, score)
        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="action_verbs",
            name="Escrita Profissional e Verbos de Ação",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @staticmethod
    def _eval_keywords(text: str, is_en: bool = False) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        common_tech_business_keywords = [
            "python", "java", "sql", "javascript", "typescript", "react", "node", "docker", "aws", "azure", "gcp",
            "git", "linux", "html", "css", "api", "rest", "restful", "ci/cd", "agile", "scrum", "kanban", "devops",
            "kubernetes", "microservices", "postgresql", "mongodb", "redis", "kafka", "pandas", "machine learning",
            "excel", "power bi", "tableau", "analytics", "crm", "sap", "erp", "kpi", "okr", "data pipelines",
            "leadership", "project management", "product management", "architecture", "testing", "pytest"
        ]

        text_lower = text.lower()
        matched_kw = [kw for kw in common_tech_business_keywords if re.search(rf"\b{re.escape(kw)}\b", text_lower)]
        kw_count = len(matched_kw)

        if kw_count >= 10:
            score += 12.0
            details.append(f"Forte vocabulário técnico/estratégico ({kw_count} palavras-chave identificadas).")
        elif kw_count >= 6:
            score += 9.0
            details.append(f"Boa quantidade de competências e palavras-chave ({kw_count} identificadas).")
        elif kw_count >= 3:
            score += 6.0
            details.append(f"Quantidade moderada de palavras-chave ({kw_count} encontradas).")
            details.append("[Recomendação] Inclua termos técnicos, metodologias e ferramentas que você realmente utilizou.")
        else:
            score += 2.5
            details.append("[Ausente] Baixa densidade de palavras-chave técnicas e metodologias.")
            details.append("[Recomendação] Adicione competências explícitas (ferramentas, softwares, metodologias ágeis, etc.).")

        # Check if skills section exists
        has_skills_section = bool(re.search(r"\b(habilidades|skills|competências|tecnologias|ferramentas|technical\s+skills)\b", text, re.IGNORECASE))
        if has_skills_section:
            score += 3.0
            details.append("Competências organizadas em seção dedicada.")
        else:
            rec_sec = "Skills" if is_en else "Habilidades e Tecnologias"
            details.append(f"[Recomendação] Organize suas competências em uma seção dedicada '{rec_sec}'.")

        score = min(weight, score)
        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="keywords",
            name="Palavras-chave e Competências",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @staticmethod
    def _eval_readability(text: str, word_count: int, is_en: bool = False) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        # Length check: 200 - 1000 words is typically ideal (1 - 2 pages)
        if 250 <= word_count <= 950:
            score += 7.0
            details.append(f"Extensão ideal para triagem ATS ({word_count} palavras, equivalente a 1-2 páginas bem aproveitadas).")
        elif 150 <= word_count < 250:
            score += 4.5
            details.append(f"Documento um pouco sucinto ({word_count} palavras). Pode detalhar melhor as realizações.")
        elif 950 < word_count <= 1600:
            score += 5.0
            details.append(f"Documento extenso ({word_count} palavras). Risco de prolixidade em triagens rápidas.")
            details.append("[Recomendação] Foque nos últimos 5 a 10 anos de carreira e sintetize experiências antigas.")
        elif word_count > 1600:
            score += 2.0
            details.append(f"Documento excessivamente longo ({word_count} palavras).")
            details.append("[Recomendação] Reduza para até 2 páginas objetivas.")
        else:
            score += 1.0
            details.append(f"Documento muito curto ({word_count} palavras). Informações insuficientes.")

        # Formatting cleanliness & ATS friendly characters
        odd_chars = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text)
        if not odd_chars:
            score += 4.0
            details.append("Texto limpo e totalmente decodificável por parsers ATS.")
        else:
            details.append("[Atenção] Presença de caracteres especiais ou artefatos de codificação.")

        # Check paragraph density (avoid single gigantic block)
        paragraphs = [p for p in text.split("\n\n") if len(p.strip()) > 20]
        if len(paragraphs) >= 5:
            score += 4.0
            details.append("Boa separação visual de blocos e parágrafos.")
        else:
            score += 1.5
            details.append("[Atenção] Pouca divisão de blocos; texto pode parecer denso.")

        score = min(weight, score)
        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="readability",
            name="Legibilidade e Parseabilidade ATS",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @staticmethod
    def _eval_contact(text: str, is_en: bool = False) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        # Email
        has_email = bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))
        if has_email:
            score += 4.0
            details.append("E-mail válido identificado.")
        else:
            details.append("[Ausente] E-mail não encontrado no currículo.")
            details.append("[Recomendação] Inclua um e-mail profissional de fácil contato.")

        # Phone (Brazilian or International format)
        has_phone = bool(re.search(r"(\+?\d{1,4}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}", text))
        if has_phone:
            score += 4.0
            details.append("Telefone para contato identificado.")
        else:
            details.append("[Ausente] Telefone para contato não identificado.")
            details.append("[Recomendação] Adicione número de telefone celular/WhatsApp com código de área.")

        # Professional Links (LinkedIn, GitHub, Portfolio)
        has_linkedin = bool(re.search(r"linkedin\.com/in/[a-zA-Z0-9-_]+", text, re.IGNORECASE) or "linkedin" in text.lower())
        has_github = bool(re.search(r"github\.com/[a-zA-Z0-9-_]+", text, re.IGNORECASE) or "github" in text.lower())
        if has_linkedin or has_github:
            score += 4.0
            details.append("Link de perfil profissional (LinkedIn ou GitHub) identificado.")
        else:
            details.append("[Atenção] Link para LinkedIn ou portfólio não encontrado.")
            details.append("[Recomendação] Adicione o link limpo do seu LinkedIn no cabeçalho.")

        # Location (City / State / Country)
        loc_pattern = (
            r"\b(são paulo|rio de janeiro|curitiba|belo horizonte|porto alegre|salvador|brasília|campinas|remoto|híbrido|brasil|"
            r"remote|hybrid|united states|usa|us|uk|london|new york|san francisco|austin|toronto|canada|berlin|germany|dublin|ireland|"
            r"[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}|[a-z\s]+[-/]\s*[a-z]{2})\b"
        )
        has_location = bool(re.search(loc_pattern, text, re.IGNORECASE))
        if has_location:
            score += 3.0
            details.append("Localização (cidade/país ou modelo de trabalho) indicada.")
        else:
            score += 1.0
            if is_en:
                details.append("[Recomendação] Indique sua localização no topo (ex: 'New York, NY', 'London, UK' ou 'Remote').")
            else:
                details.append("[Recomendação] Indique sua cidade e estado no topo (ex: 'São Paulo - SP' ou 'Disponível para trabalho remoto').")

        # Check discouraged personal data
        found_discouraged = []
        for pat, desc in DISCOURAGED_DATA_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                found_discouraged.append(desc)

        if found_discouraged:
            score = max(0.0, score - 2.0)
            for d in found_discouraged:
                details.append(f"[Atenção] {d}")

        score = min(weight, score)
        pct = (score / weight) * 100.0
        status = "Excelente" if pct >= 85 else ("Bom" if pct >= 65 else ("Atenção" if pct >= 45 else "Crítico"))

        return CriterionScore(
            criterion_id="contact",
            name="Completude de Dados de Contato",
            weight=weight,
            score=round(score, 1),
            max_score=weight,
            percentage=round(pct, 1),
            status=status,
            details=details
        )

    @classmethod
    def _empty_result(cls) -> DiagnosisResult:
        return DiagnosisResult(
            overall_score=0,
            criteria=[
                CriterionScore(criterion_id="structure", name="Estrutura e Títulos Convencionais", weight=20.0, score=0.0, max_score=20.0, percentage=0.0, status="Crítico", details=["Documento vazio ou ilegível."]),
                CriterionScore(criterion_id="impact", name="Impacto e Resultados Concretos", weight=20.0, score=0.0, max_score=20.0, percentage=0.0, status="Crítico", details=["Sem métricas detectáveis."]),
                CriterionScore(criterion_id="action_verbs", name="Escrita Profissional e Verbos de Ação", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Sem verbos de ação detectáveis."]),
                CriterionScore(criterion_id="keywords", name="Palavras-chave e Competências", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Sem competências indexáveis."]),
                CriterionScore(criterion_id="readability", name="Legibilidade e Parseabilidade ATS", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Volume textual insuficiente."]),
                CriterionScore(criterion_id="contact", name="Completude de Dados de Contato", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Dados de contato ausentes."])
            ],
            key_issues=["O documento fornecido está vazio ou não pôde ser lido."],
            positive_points=[],
            initial_recommendations=["Envie um arquivo PDF ou DOCX contendo texto selecionável."],
            char_count=0,
            word_count=0,
            has_extractable_text=False,
            detected_sections=[],
            language="pt"
        )
