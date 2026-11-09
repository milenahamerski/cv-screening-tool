"""Objective and documented ATS Resume Analyzer."""

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
    # English
    r"\b(developed|implemented|led|managed|optimized|built|engineered|architected)\b",
    r"\b(reduced|increased|automated|integrated|delivered|designed|created|scaled)\b",
]

# Sensitive or outdated personal data that ATS and modern recruiters advise against
DISCOURAGED_DATA_PATTERNS = [
    (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "CPF exposto (desnecessário para triagem inicial)"),
    (r"\b(rg|identidade)\s*[:.\s]\s*\d+", "RG exposto (desnecessário)"),
    (r"\b(solteiro|solteira|casado|casada|divorciado|divorciada|viúvo|viúva)\b", "Estado civil mencionado (não recomendado em padrões ATS)"),
    (r"\b(habilitação\s*[ab]|cnh\s*[ab]|categoria\s*[ab])\b", "CNH mencionada sem contexto de vaga de motorista"),
    (r"\b(rua|avenida|travessa|alameda)\s+[a-z0-9\s]+,\s*n?[ºo]?\s*\d+", "Endereço residencial completo (recomenda-se apenas Cidade - UF)"),
]

# Standard ATS Section Titles
STANDARD_SECTIONS = {
    "contato": [r"\bcontato\b", r"\binformações\s+de\s+contato\b", r"\bdados\s+pessoais\b", r"\bcontact\b"],
    "resumo": [r"\bresumo\b", r"\bresumo\s+profissional\b", r"\bperfil\b", r"\bperfil\s+profissional\b", r"\bsobre\s+mim\b", r"\bobjective\b", r"\bsummary\b"],
    "experiencia": [r"\bexperi[êe]ncia(s)?\b", r"\bexperi[êe]ncia\s+profissional\b", r"\bhist[óo]rico\s+profissional\b", r"\batua[çc][ãa]o\s+profissional\b", r"\bwork\s+experience\b"],
    "formacao": [r"\bforma[çc][ãa]o\b", r"\bforma[çc][ãa]o\s+acad[êe]mica\b", r"\beduca[çc][ãa]o\b", r"\bescolaridade\b", r"\beducation\b"],
    "habilidades": [r"\bhabilidades\b", r"\bcompet[êe]ncias\b", r"\bconhecimentos\s+t[ée]cnicos\b", r"\btecnologias\b", r"\bskills\b", r"\bferramentas\b"],
    "certificacoes": [r"\bcertifica[çc][õo]es\b", r"\bcursos\b", r"\bcertificados\b", r"\bprojetos\b", r"\bidiomas\b", r"\bcourses\b"],
}


class ResumeAnalyzer:
    """Evaluates resumes using objective, transparent, and documented criteria."""

    @classmethod
    def analyze(cls, text: str, original_filename: str = "") -> DiagnosisResult:
        if not text or len(text.strip()) < 10:
            return cls._empty_result()

        norm_text = text.strip()
        lines = [line.strip() for line in norm_text.split("\n") if line.strip()]
        word_count = len(norm_text.split())
        char_count = len(norm_text)

        # 1. Evaluate Structure & Headings (Max 20 pts)
        c_structure = cls._eval_structure(norm_text, lines)

        # 2. Evaluate Impact & Concrete Metrics (Max 20 pts)
        c_impact = cls._eval_impact(norm_text, lines)

        # 3. Evaluate Professional Writing & Action Verbs (Max 15 pts)
        c_verbs = cls._eval_verbs_and_tone(norm_text, lines)

        # 4. Evaluate Keywords & Skills (Max 15 pts)
        c_keywords = cls._eval_keywords(norm_text)

        # 5. Evaluate ATS Readability & Parsing (Max 15 pts)
        c_readability = cls._eval_readability(norm_text, word_count)

        # 6. Evaluate Contact Completeness (Max 15 pts)
        c_contact = cls._eval_contact(norm_text)

        criteria = [c_structure, c_impact, c_verbs, c_keywords, c_readability, c_contact]
        overall_score = int(round(sum(c.score for c in criteria)))
        overall_score = max(0, min(100, overall_score))

        key_issues = []
        positive_points = []
        initial_recommendations = []

        for c in criteria:
            if c.percentage >= 80:
                positive_points.append(f"{c.name}: {c.details[0] if c.details else 'Atende plenamente aos padrões recomendados.'}")
            elif c.percentage < 60:
                for det in c.details:
                    if any(det.startswith(p) for p in ["[Atenção]", "[Ausente]", "[Incompleto]", "⚠️", "❌"]) or "Ausente" in det or "pouco" in det.lower() or "não encontrado" in det.lower():
                        clean = det
                        for prefix in ["[Atenção] ", "[Ausente] ", "[Incompleto] ", "[Atenção] ", "[Ausente] "]:
                            clean = clean.replace(prefix, "")
                        key_issues.append(f"[{c.name}] {clean}")
            
            # Extract actionable recommendations
            for det in c.details:
                if det.startswith("[Recomendação]") or det.startswith("💡"):
                    clean = det.replace("[Recomendação] ", "").replace("[Recomendação] ", "")
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
            detected_sections=detected
        )

    @staticmethod
    def _eval_structure(text: str, lines: List[str]) -> CriterionScore:
        weight = 20.0
        score = 0.0
        details = []

        found_sections = {}
        for sec, patterns in STANDARD_SECTIONS.items():
            found = any(re.search(pat, text, re.IGNORECASE) for pat in patterns)
            found_sections[sec] = found

        # Essential sections:
        # Experiência (6 pts), Formação (5 pts), Habilidades (4 pts), Contato/Dados (3 pts), Resumo (2 pts)
        if found_sections["experiencia"]:
            score += 6.0
            details.append("Seção de Experiência Profissional identificada.")
        else:
            details.append("[Ausente] Seção de Experiência Profissional não identificada com título convencional.")

        if found_sections["formacao"]:
            score += 5.0
            details.append("Seção de Formação Acadêmica identificada.")
        else:
            details.append("[Ausente] Seção de Formação Acadêmica ausente ou com nomenclatura não convencional.")

        if found_sections["habilidades"]:
            score += 4.0
            details.append("Seção de Habilidades e Competências presente.")
        else:
            details.append("[Atenção] Seção dedicada de Habilidades e Tecnologias ausente.")
            details.append("[Recomendação] Crie uma seção 'Habilidades e Tecnologias' para facilitar a indexação automática pelo ATS.")

        if found_sections["contato"]:
            score += 3.0
            details.append("Cabeçalho de informações de contato identificado.")
        else:
            score += 1.5  # Partial if at least email/phone exist even without explicit title
            details.append("Informações de contato detectadas no topo, mas sem seção explícita.")

        if found_sections["resumo"]:
            score += 2.0
            details.append("Resumo/Perfil Profissional presente no início do documento.")
        else:
            details.append("[Recomendação] Inclua um Resumo Profissional conciso (3 a 5 linhas) no início do currículo.")

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
    def _eval_impact(text: str, lines: List[str]) -> CriterionScore:
        weight = 20.0
        score = 0.0
        details = []

        # Find numbers, percentages, currency, multipliers, metrics
        metric_patterns = [
            r"\b\d+([.,]\d+)?\s*%\b",                      # Percentages: 25%, 15.5%
            r"\b(r\$|usd|\$|€)\s*\d+([.,]\d+)?\b",         # Currency
            r"\b\d+\s*(milhões|mil|milhoes|k|m|mil|usuarios|usuários|clientes|projetos|processos|membros|equipes|pessoas)\b",
            r"\b\d+\s*(horas|dias|meses|anos|pontos|reuniões|sprints)\b",
            r"\b(aumento|redução|reducao|crescimento|economia|eficiência|ganho)\s+de\s+\d+",
            r"\b(top\s*\d+|1º|2º|3º|primeiro\s+lugar)\b",
            r"\b\d+\s*(x|vezes)\b"
        ]

        found_metrics = []
        for pat in metric_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            if matches:
                found_metrics.extend(matches)

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
            details.append("[Recomendação] Inclua números reais nos resultados das suas experiências (ex: % de aumento de eficiência, economia gerada, volume de entregas).")
        elif metric_count == 1:
            score = 6.0
            details.append("Apenas 1 resultado quantitativo encontrado.")
            details.append("[Recomendação] Destaque impactos mensuráveis nas descrições de cargo em vez de listar apenas tarefas rotineiras.")
        else:
            score = 3.0
            details.append("[Ausente] Nenhuma métrica mensurável (porcentagens, prazos, reduções, volumes) identificada.")
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
    def _eval_verbs_and_tone(text: str, lines: List[str]) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        # Count action verbs
        matched_verbs = set()
        for pat in ACTION_VERBS:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                matched_verbs.add(m.lower())

        verb_count = len(matched_verbs)

        # Check for first-person pronouns
        first_person_matches = re.findall(r"\b(eu\s|meu\s|minha\s|participei\b|fiz\b|trabalhei\b|ajudei\b)", text, re.IGNORECASE)

        if verb_count >= 8:
            score += 10.0
            details.append(f"Excelente emprego de verbos de ação ({verb_count} verbos de impacto distintos identificados).")
        elif verb_count >= 4:
            score += 7.0
            details.append(f"Bom uso de verbos de ação ({verb_count} verbos identificados).")
        elif verb_count >= 2:
            score += 4.0
            details.append(f"Uso modesto de verbos de ação ({verb_count} verbos identificados).")
            details.append("[Recomendação] Inicie os tópicos de experiência com verbos no passado de ação (ex: 'Desenvolveu', 'Implementou', 'Coordenou').")
        else:
            score += 1.5
            details.append("[Ausente] Pouquíssimos verbos de ação identificados. As frases parecem descrições passivas.")
            details.append("[Recomendação] Substitua 'Responsável por...' por verbos diretos como 'Liderou', 'Otimizou', 'Implementou'.")

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
    def _eval_keywords(text: str) -> CriterionScore:
        weight = 15.0
        score = 0.0
        details = []

        common_tech_business_keywords = [
            "python", "java", "sql", "javascript", "typescript", "react", "node", "docker", "aws", "azure", "gcp",
            "git", "linux", "html", "css", "api", "rest", "ci/cd", "agile", "scrum", "kanban", "devops",
            "excel", "power bi", "tableau", "dados", "analise", "analytics", "gestao", "liderança", "comunicacao",
            "vendas", "marketing", "atendimento", "crm", "sap", "erp", "kpi", "okr", "machine learning"
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
        has_skills_section = bool(re.search(r"\b(habilidades|skills|competências|tecnologias|ferramentas)\b", text, re.IGNORECASE))
        if has_skills_section:
            score += 3.0
            details.append("Competências organizadas em seção dedicada.")
        else:
            details.append("[Recomendação] Organize suas competências em tópicos de fácil leitura por sistemas ATS.")

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
    def _eval_readability(text: str, word_count: int) -> CriterionScore:
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
    def _eval_contact(text: str) -> CriterionScore:
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

        # Phone
        has_phone = bool(re.search(r"(\+?\d{1,3}\s*)?(\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}", text))
        if has_phone:
            score += 4.0
            details.append("Telefone/WhatsApp identificado.")
        else:
            details.append("[Ausente] Telefone para contato não identificado.")
            details.append("[Recomendação] Adicione número de telefone celular/WhatsApp com DDD.")

        # Professional Links (LinkedIn, GitHub, Portfolio)
        has_linkedin = bool(re.search(r"linkedin\.com/in/[a-zA-Z0-9-_]+", text, re.IGNORECASE) or "linkedin" in text.lower())
        has_github = bool(re.search(r"github\.com/[a-zA-Z0-9-_]+", text, re.IGNORECASE) or "github" in text.lower())
        if has_linkedin or has_github:
            score += 4.0
            details.append("Link de perfil profissional (LinkedIn ou GitHub) identificado.")
        else:
            details.append("[Atenção] Link para LinkedIn ou portfólio não encontrado.")
            details.append("[Recomendação] Adicione o link limpo do seu LinkedIn no cabeçalho.")

        # Location (City / State)
        has_location = bool(re.search(r"\b(são paulo|rio de janeiro|curitiba|belo horizonte|porto alegre|salvador|brasília|campinas|remoto|híbrido|brasil|[a-z\s]+[-/]\s*[a-z]{2})\b", text, re.IGNORECASE))
        if has_location:
            score += 3.0
            details.append("Localização (cidade/estado ou modelo de trabalho) indicada.")
        else:
            score += 1.0
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
        criteria = [
            CriterionScore(criterion_id="structure", name="Estrutura e Títulos Convencionais", weight=20.0, score=0.0, max_score=20.0, percentage=0.0, status="Crítico", details=["Documento vazio ou texto ilegível."]),
            CriterionScore(criterion_id="impact", name="Impacto e Resultados Concretos", weight=20.0, score=0.0, max_score=20.0, percentage=0.0, status="Crítico", details=["Nenhum conteúdo para análise."]),
            CriterionScore(criterion_id="action_verbs", name="Escrita Profissional e Verbos de Ação", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Nenhum conteúdo para análise."]),
            CriterionScore(criterion_id="keywords", name="Palavras-chave e Competências", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Nenhum conteúdo para análise."]),
            CriterionScore(criterion_id="readability", name="Legibilidade e Parseabilidade ATS", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Nenhum conteúdo para análise."]),
            CriterionScore(criterion_id="contact", name="Completude de Dados de Contato", weight=15.0, score=0.0, max_score=15.0, percentage=0.0, status="Crítico", details=["Nenhum conteúdo para análise."]),
        ]
        return DiagnosisResult(
            overall_score=0,
            criteria=criteria,
            key_issues=["O documento carregado não contém texto selecionável ou está vazio."],
            positive_points=[],
            initial_recommendations=["Envie um arquivo PDF ou DOCX com conteúdo textual extraível."],
            char_count=0,
            word_count=0,
            has_extractable_text=False
        )
