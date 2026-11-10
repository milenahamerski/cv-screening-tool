# CV Optimizer — Análise e Otimização de Currículos para ATS

Aplicação interativa e executiva de página única para análise técnica, otimização estrutural e reavaliação contínua de currículos com foco em sistemas ATS (*Applicant Tracking Systems*).

Desenvolvida com **FastAPI**, **ReportLab**, **python-docx** e JavaScript moderno sem frameworks pesados, garantindo pontuação determinística, proteção total contra alucinações de dados e fidelidade visual na exportação.

---

##  Como Executar

### 1. Clonar o repositório e preparar o ambiente

```bash
git clone https://github.com/milenahamerski/cv-screening-tool.git
cd cv-screening-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Iniciar a aplicação

```bash
python run.py
```

Acesse a interface no navegador: **http://localhost:8000**

### 3. Executar a Suíte de Testes Automatizados

```bash
pytest -v
```

---

##  Principais Funcionalidades

- **Diagnóstico Técnico ATS Objetivo (0 a 100)**: Avaliação determinística baseada em 6 critérios ponderados, sem notas infladas ou cálculos opacos.
- **Suporte a Currículos em Português e Inglês**: Motor de diagnóstico com detecção automática de idioma, avaliando verbos de ação internacionais (*engineered, architected, spearheaded*), métricas em moeda global (`$120k`, `10M users`) e convenções de títulos para vagas no Brasil ou exterior.
- **Links Clicáveis Nativos no Cabeçalho**:
  - Aceita formatos flexíveis: `LinkedIn: [https://linkedin.com/in/...]`, `GitHub: [https://github.com/...]`, `[LinkedIn](url)` ou `email@dominio.com`.
  - Gera **hiperlinks nativos** em PDF (`URI Annotations`) e em DOCX (relações de relacionamento OPC no Word XML), permitindo que recrutadores cliquem diretamente no documento.
- **Alinhamento Justificado e Tipografia Executiva**: Textos e marcadores de experiência formatados com alinhamento justificado (`WD_ALIGN_PARAGRAPH.JUSTIFY` no DOCX e `TA_JUSTIFY` no PDF).
- **Editor Markdown Split-Screen com Prévia em Tempo Real**: Permite colar Markdown diretamente, editar seções e visualizar a renderização idêntica ao PDF final.
- **Otimização Baseada na Fonte da Verdade**: Reorganiza a estrutura, fortalece os verbos de ação e destaca métricas sem jamais inventar dados, formações ou números inexistentes.
- **Auditoria Comparativa Antes & Depois**: Tabela detalhada critério a critério, identificando problemas resolvidos, parcialmente resolvidos e recomendações de ação humana.

---

## 📋 Fluxo da Aplicação

A interface é centralizada em **uma única página principal**, sem redirecionamentos, organizada nas seguintes seções:

### A. Upload ou Importação
- Suporte a upload de arquivos **PDF**, **DOCX** e **Markdown (.md)**.
- Identificação automática do formato e preservação do arquivo original como fonte da verdade estrita.

### B. Diagnóstico Inicial
Pontuação geral (0 a 100) calculada a partir de 6 critérios técnicos documentados:
1. **Estrutura e Títulos Convencionais (20 pts)**: Títulos padronizados reconhecidos por parsers ATS (*Experiência Profissional*, *Formação Acadêmica*, *Habilidades*, *Resumo*).
2. **Impacto e Resultados Concretos (20 pts)**: Densidade de métricas quantificáveis (porcentagens, volumes, prazos, economias financeiras).
3. **Escrita Profissional e Verbos de Ação (15 pts)**: Frases iniciadas por verbos de impacto no passado e ausência de vícios de linguagem (voz passiva, primeira pessoa).
4. **Palavras-chave e Competências Relevantes (15 pts)**: Presença e categorização de tecnologias, metodologias e linguagens sustentadas pelo currículo.
5. **Legibilidade e Parseabilidade ATS (15 pts)**: Clareza na extração textual, proporção de texto e facilidade de indexação.
6. **Completude de Dados de Contato (15 pts)**: Identificação de e-mail, telefone, LinkedIn e cidade/UF (sem dados sensíveis desencorajados, como CPF ou RG).

### C. Otimização Automatizada ("Melhorar CV")
- Botão destacado com acompanhamento das etapas reais de execução.
- Reorganiza a estrutura para padrões ATS, elimina poluição visual e padroniza a formatação.

### D. Inspeção Posterior à Otimização
- Reavaliação automática utilizando **exatamente os mesmos critérios e pesos**.
- Comprovação algorítmica de preservação factual de datas, empresas, cargos e formação acadêmica.

### E. Comparação Antes e Depois
- Comparação direta das notas, diferença absoluta em pontos e status de cada apontamento.
- *Nota de integridade:* os resultados refletem conformidade técnica com ATS e nunca probabilidade de contratação.

### F. Recomendações Finais (Revisão Humana)
Pendências classificadas por nível de prioridade (Alta, Média e Baixa), com explicação do problema, motivo de relevância e exemplos práticos de como o usuário pode enriquecer seu currículo com dados reais.

### H. Revisão Manual & Editor Markdown
- Permite editar o Markdown a qualquer momento.
- Botão **"Salvar e Reavaliar Pontuação"** para recalcular a conformidade com as novas edições.
- Ferramenta **"Auto-Formatar no Padrão"** para padronização automática de cabeçalhos e listas.

### G. Exportação dos Documentos
Download direto e instantâneo dos seguintes artefatos:
1. **Currículo Otimizado em DOCX**: Uma coluna, formatação profissional, texto selecionável e editável no Microsoft Word e LibreOffice.
2. **Currículo Otimizado em PDF**: Layout executivo com links clicáveis ativos e texto selecionável.
3. **Relatório de Auditoria ATS (PDF)**: Documento técnico completo com o comparativo antes/depois e notas detalhadas.
4. **Lista de Pendências (TXT)**: Guia de pendências para refinamento e intervenção humana.

---

##  Tecnologias Utilizadas

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2.
- **Processamento de Documentos**: `python-docx` (geração e manipulação de DOCX), `reportlab` (geração de PDF de alta fidelidade), `pypdf` e `pdfplumber` (extração textual).
- **Frontend**: HTML5, CSS3 moderno (Dark Mode executivo, layout responsivo), Vanilla JavaScript (sem dependências externas).
- **Testes & Qualidade**: Pytest (29 testes unitários e de integração de fluxo ponta a ponta).

---

##  Diretrizes de Confiabilidade

1. **Nunca inventar fatos profissionais**: Nenhum cargo, data, empresa ou habilidade ausente no original é gerado artificialmente.
2. **Nunca inflar notas sem evidência técnica**: Se uma métrica quantitativa não existe no original, a nota desse critério não é artificialmente elevada.
3. **Preservação de Conteúdo**: O arquivo original é mantido intacto.
4. **Respeito à Revisão Humana**: O sistema destaca pendências de responsabilidade do candidato que nenhuma IA deve preencher por suposição.

