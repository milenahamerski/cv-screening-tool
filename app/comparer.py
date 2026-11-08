"""Comparison and Human Recommendations Engine."""

from typing import List, Dict, Any, Tuple
from app.models import (
    DiagnosisResult,
    ComparisonResult,
    IssueResolutionStatus,
    PendingRecommendation
)


class ResumeComparer:
    """Compares pre- and post-optimization analyses and generates human action items."""

    @classmethod
    def compare(
        cls,
        initial: DiagnosisResult,
        post: DiagnosisResult,
        has_metrics_in_original: bool = True
    ) -> ComparisonResult:
        original_score = initial.overall_score
        optimized_score = post.overall_score
        absolute_delta = optimized_score - original_score

        # Build criterion-by-criterion comparison
        criteria_comparison = []
        init_criteria_map = {c.criterion_id: c for c in initial.criteria}

        for post_c in post.criteria:
            init_c = init_criteria_map.get(post_c.criterion_id)
            before_val = init_c.score if init_c else 0.0
            delta_val = round(post_c.score - before_val, 1)

            criteria_comparison.append({
                "criterion_id": post_c.criterion_id,
                "name": post_c.name,
                "max_score": post_c.max_score,
                "before_score": before_val,
                "after_score": post_c.score,
                "delta": delta_val,
                "status_before": init_c.status if init_c else "Desconhecido",
                "status_after": post_c.status,
                "progress_percentage": round((post_c.score / post_c.max_score) * 100, 1)
            })

        # Categorize issue resolution
        resolved_issues: List[IssueResolutionStatus] = []
        partially_resolved: List[IssueResolutionStatus] = []
        unresolved_issues: List[IssueResolutionStatus] = []

        # Analyze initial key issues and see how they evolved
        for issue_text in initial.key_issues:
            issue_lower = issue_text.lower()
            if "título convencional" in issue_lower or "estrutura" in issue_lower or "seção dedicada" in issue_lower:
                # Structure issues are resolved by standard ATS layout
                resolved_issues.append(IssueResolutionStatus(
                    issue=issue_text,
                    status="resolvido",
                    explanation="Estrutura reordenada em blocos padronizados com cabeçalhos convencionais reconhecidos por ATS."
                ))
            elif "verbos de ação" in issue_lower or "primeira pessoa" in issue_lower or "marcadores" in issue_lower:
                resolved_issues.append(IssueResolutionStatus(
                    issue=issue_text,
                    status="resolvido",
                    explanation="Frases passivas reescritas com verbos fortes de ação no pretérito e marcadores em tópicos."
                ))
            elif "palavras-chave" in issue_lower or "competências" in issue_lower:
                if any(c["criterion_id"] == "keywords" and c["delta"] > 0 for c in criteria_comparison):
                    resolved_issues.append(IssueResolutionStatus(
                        issue=issue_text,
                        status="resolvido",
                        explanation="Competências e ferramentas sustentadas no texto agrupadas em seção dedicada."
                    ))
                else:
                    partially_resolved.append(IssueResolutionStatus(
                        issue=issue_text,
                        status="partially_resolved",
                        explanation="Termos existentes foram estruturados, mas é recomendável que você adicione tecnologias específicas adicionais."
                    ))
            elif "métrica" in issue_lower or "quantitativ" in issue_lower or "resultado" in issue_lower:
                # Metrics cannot be hallucinated!
                unresolved_issues.append(IssueResolutionStatus(
                    issue=issue_text,
                    status="nao_resolvido",
                    explanation="Métricas numéricas não foram inventadas para preservar a integridade ética do currículo. Requer preenchimento com seus números reais."
                ))
            elif "e-mail" in issue_lower or "telefone" in issue_lower or "linkedin" in issue_lower:
                if "não encontrado" in issue_lower or "ausente" in issue_lower:
                    unresolved_issues.append(IssueResolutionStatus(
                        issue=issue_text,
                        status="nao_resolvido",
                        explanation="Informação de contato ausente no arquivo original não pode ser inventada pelo sistema."
                    ))
                else:
                    partially_resolved.append(IssueResolutionStatus(
                        issue=issue_text,
                        status="partially_resolved",
                        explanation="Formatação de contato higienizada, mas confirme se seus links estão atualizados."
                    ))
            else:
                partially_resolved.append(IssueResolutionStatus(
                    issue=issue_text,
                    status="partially_resolved",
                    explanation="Melhoria parcial aplicada no documento estruturado."
                ))

        # Generate human pending recommendations categorized in Alta, Média, Baixa prioridade
        human_recommendations = cls._generate_human_recommendations(initial, post)

        return ComparisonResult(
            original_score=original_score,
            optimized_score=optimized_score,
            absolute_delta=absolute_delta,
            criteria_comparison=criteria_comparison,
            resolved_issues=resolved_issues,
            partially_resolved_issues=partially_resolved,
            unresolved_issues=unresolved_issues,
            human_recommendations=human_recommendations
        )

    @classmethod
    def _generate_human_recommendations(
        cls,
        initial: DiagnosisResult,
        post: DiagnosisResult
    ) -> List[PendingRecommendation]:
        recs = []

        # 1. ALTA PRIORIDADE: Informações importantes ausentes ou que precisam de confirmação
        # Check contact completeness
        post_contact = next((c for c in post.criteria if c.criterion_id == "contact"), None)
        if post_contact and post_contact.percentage < 80:
            recs.append(PendingRecommendation(
                id="rec-contact-data",
                priority="alta",
                title="Completar Informações de Contato e Links Profissionais",
                problem="Links diretos para LinkedIn, GitHub ou telefone com DDD estão ausentes ou incompletos.",
                why_matters="Recrutadores e sistemas ATS precisam de canais rápidos e inequívocos para contato e validação de histórico.",
                what_to_do="Insira o link direto do seu perfil no LinkedIn (ex: linkedin.com/in/seunome) e confirme seu telefone/WhatsApp.",
                example="LinkedIn: linkedin.com/in/ana-silva-dev | Telefone: (11) 98765-4321"
            ))

        # Check impact metrics (cannot be invented!)
        post_impact = next((c for c in post.criteria if c.criterion_id == "impact"), None)
        if post_impact and post_impact.percentage < 75:
            recs.append(PendingRecommendation(
                id="rec-impact-metrics",
                priority="alta",
                title="Adicionar Métricas e Resultados Reais nas Experiências",
                problem="As experiências listam atribuições, mas contêm poucos dados numéricos ou resultados mensuráveis comprovados.",
                why_matters="O sistema preservou suas informações sem inventar dados, mas sistemas ATS e recrutadores priorizam candidatos que comprovam impacto com números.",
                what_to_do="Edite os tópicos das suas experiências informando números reais da sua atuação: porcentagens de melhoria, orçamento, tamanho de equipe ou volume de projetos.",
                example="Em vez de 'Desenvolveu relatórios gerenciais', use: 'Desenvolveu 12 relatórios automatizados, reduzindo em 35% o tempo de fechamento mensal'."
            ))

        # 2. MÉDIA PRIORIDADE: Conteúdo, detalhamento e apresentação
        post_kw = next((c for c in post.criteria if c.criterion_id == "keywords"), None)
        if post_kw and post_kw.percentage < 85:
            recs.append(PendingRecommendation(
                id="rec-keywords-alignment",
                priority="media",
                title="Alinhar Palavras-chave com a Vaga Desejada",
                problem="O currículo possui competências gerais, mas pode faltar alinhamento com termos específicos da sua área de interesse.",
                why_matters="Sistemas de triagem comparam a descrição da vaga com as palavras exatas contidas na seção de habilidades e no corpo das experiências.",
                what_to_do="Abra a vaga que você deseja concorrer, identifique as tecnologias e metodologias pedidas nos requisitos e adicione aquelas que você realmente domina.",
                example="Adicionar frameworks específicos dominados, tais como: 'FastAPI', 'Docker', 'PostgreSQL', 'Scrum' na seção de Habilidades."
            ))

        recs.append(PendingRecommendation(
            id="rec-experience-context",
            priority="media",
            title="Detalhamento do Escopo dos Projetos Recentes",
            problem="Cargos mais recentes podem beneficiar-se de contextualização do tamanho do projeto e tecnologias centrais.",
            why_matters="Demonstra a complexidade dos desafios enfrentados pelo candidato nas últimas posições ocupadas.",
            what_to_do="Para o seu cargo mais recente, garanta de 3 a 5 tópicos detalhando o objetivo do projeto e a sua contribuição individual.",
            example="Ex: 'Liderou a migração de sistema legado para arquitetura em nuvem (AWS), atendendo a mais de 10.000 usuários ativos'."
        ))

        # 3. BAIXA PRIORIDADE: Refinamentos de escrita e organização
        recs.append(PendingRecommendation(
            id="rec-review-dates",
            priority="baixa",
            title="Conferência de Datas e Períodos",
            problem="Garantir consistência na notação de datas entre as diferentes posições.",
            why_matters="Padronização visual e cronologia clara evitam dúvidas durante a leitura humana.",
            what_to_do="Verifique se as datas de início e fim seguem o mesmo padrão em todo o documento (ex: '2021 - 2023' ou 'Jan/2021 - Atual').",
            example="Padronizar todos os cargos no modelo: 'Mês/Ano - Mês/Ano' ou apenas 'Ano - Ano'."
        ))

        recs.append(PendingRecommendation(
            id="rec-tailor-summary",
            priority="baixa",
            title="Personalização do Resumo Profissional para Cada Inscrição",
            problem="O resumo otimizado fornece uma base sólida, mas ganha ainda mais força quando ajustado para cada empresa.",
            why_matters="Recrutadores leem as três primeiras linhas para decidir se aprofundam a leitura do currículo.",
            what_to_do="Adapte a primeira frase do resumo mencionando seu cargo-alvo exato da vaga almejada.",
            example="'Desenvolvedor Back-end Sênior com 6 anos de experiência em Python e microsserviços...'"
        ))

        return recs
