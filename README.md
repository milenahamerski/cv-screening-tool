# CV Optimizer — Análise e Otimização de Currículos para ATS

Aplicação interativa centralizada em página única para análise técnica, otimização estrutural e reavaliação de currículos com foco em sistemas ATS (Applicant Tracking Systems).

---

## 🚀 Como Executar

### 1. Criar o ambiente virtual e instalar dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Iniciar o servidor

```bash
python run.py
```

Acesse a interface no navegador: **http://localhost:8000**

### 3. Executar os Testes Automatizados

```bash
pytest -v
```

---

## 📋 Arquitetura e Fluxo da Aplicação

A interface é centralizada em **uma única página principal**, sem redirecionamentos, organizada rigorosamente na seguinte sequência de seções:

### A. Upload do currículo
- Suporte a arquivos **PDF** e **DOCX**.
- Apresenta o nome do arquivo, formato detectado e contagem de palavras/estatísticas.
- Opção para substituir o documento a qualquer momento.
- O arquivo original é mantido em memória e em disco estritamente inalterado (fonte da verdade).

### B. Diagnóstico inicial
- **Pontuação geral de 0 a 100** calculada a partir de 6 critérios objetivos e documentados:
  1. *Estrutura e Títulos Convencionais* (20 pts)
  2. *Impacto e Resultados Concretos* (20 pts)
  3. *Escrita Profissional e Verbos de Ação* (15 pts)
  4. *Palavras-chave e Competências Relevantes* (15 pts)
  5. *Legibilidade e Parseabilidade ATS* (15 pts)
  6. *Completude de Dados de Contato* (15 pts)
- Barra de progresso visual.
- Principais problemas identificados.
- Pontos positivos do documento.
- Recomendações técnicas iniciais.

### C. Botão principal: "Melhorar CV"
- Botão visualmente destacado com animação de progresso real.
- Executa a pipeline que reorganiza a estrutura, remove dados desencorajados (ex: CPF/RG), padroniza cabeçalhos, fortalece as frases com verbos de ação e consolida palavras-chave sustentadas pelo documento.
- **Regra de ouro:** Nunca inventa informações profissionais.

### D. Inspeção posterior à otimização
- Reexecuta a análise completa utilizando **exatamente os mesmos critérios, pesos e regras** do diagnóstico inicial.
- Validação automática de legibilidade, estrutura, palavras-chave, clareza e preservação factual (datas, empresas, cargos e formação).
- Se um critério não melhorou por ausência de dados no original (ex: falta de métricas quantitativas), sua nota **não** é aumentada artificialmente.

### E. Comparação antes e depois
- Nota original vs. Nota otimizada e diferença absoluta em pontos.
- Comparação individual de cada critério em tabela com barras de progresso.
- Status detalhado de resolução de problemas:
  - **Resolvidos**: solucionados na reestruturação do documento.
  - **Parcialmente resolvidos**: melhorados na apresentação estruturada.
  - **Não resolvidos**: requerem dados reais que o usuário deve fornecer.
- **Aviso de conformidade:** O resultado é estritamente técnico e nunca apresentado como probabilidade de contratação ou aprovação.

### F. Recomendações finais (Ação Humana)
Divididas em três categorias para intervenção do candidato:
1. **Alta prioridade:** informações essenciais ausentes ou que precisam de confirmação (métricas de impacto, links de contato).
2. **Média prioridade:** refinamento de escopo de projetos e alinhamento com palavras-chave da vaga alvo.
3. **Baixa prioridade:** conferência de estilo e personalização da primeira frase do resumo.
- Cada recomendação traz: *Qual é o problema*, *Por que importa*, *O que fazer* e *Exemplo prático de melhoria*.

### H. Revisão manual
- Editor de texto integrado para que o usuário ajuste o conteúdo otimizado antes de exportar.
- Botão **"Salvar e Reavaliar Pontuação"**: recalcula dinamicamente as notas de inspeção e a comparação antes/depois.
- Todas as alterações manuais são salvas na sessão e refletidas fielmente na exportação final.

### G. Exportação dos documentos
Disponibilização imediata para download de:
1. **Currículo em DOCX:** em uma coluna, títulos padrão, fontes comuns, totalmente editável no Word e LibreOffice (sem imagens nem PDFs embutidos).
2. **Currículo em PDF:** layout limpo e profissional com texto 100% selecionável.
3. **Relatório de Auditoria ATS (PDF):** documento técnico com a comparação antes e depois, notas por critério e status de pendências.
4. **Lista de Pendências (TXT):** checklist estruturado com orientações acionáveis para revisão humana.

---

## 🛡️ Regras e Diretrizes Estritas
- ✅ **Nunca modificar o arquivo original.**
- ✅ **Nunca inventar fatos ou números profissionais.**
- ✅ **Nunca aumentar notas sem justificativa técnica.**
- ✅ **Nunca tratar a nota como probabilidade de aprovação.**
- ✅ **Preservação comprovada por testes unitários e de integração.**
