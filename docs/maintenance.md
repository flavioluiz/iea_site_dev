# Plano de Manutenção e Melhorias

Este documento lista tarefas importantes para melhorar e manter o site em bom funcionamento.

## 🔍 Investigações Necessárias

### 1. Segurança da Extração de Dados do Lattes

**Status**: ⚠️ A investigar

**Questões a esclarecer**:
- Como funcionam exatamente os scripts `extract_lattes_*.py`?
- É seguro rodar a extração múltiplas vezes? Sobrescreve dados corretos?
- Existe modo "dry-run" ou "backup" antes de aplicar mudanças?
- É possível extrair dados de um único professor para teste?
- Como preservar dados editados manualmente pelos administradores?

**Arquivos relevantes**:
- `scripts/extract_lattes_improved.py`
- `scripts/extract_lattes_data.py` (legado)
- `scripts/update_site_from_lattes.py`

**Ação recomendada**:
- [ ] Ler e documentar o fluxo exato de extração
- [ ] Testar modo dry-run antes de aplicar mudanças
- [ ] Criar guia de "como extrair dados de um professor só"
- [ ] Documentar como fazer rollback de dados

---

### 2. Redundância de Arquivos de Professores (YAML vs JSON)

**Status**: ⚠️ A investigar

**Questões a esclarecer**:
- Por que existem dados de professores em YAML (`eam1.yaml`, `eam2.yaml`, `eam3.yaml`)?
- Por que também existem em JSON (`profiles/*.json`)?
- Qual é a fonte de verdade?
- Os arquivos YAML são obsoletos ou ainda usados?
- Como os dados fluem entre YAML e JSON?

**Arquivos relevantes**:
- `data/professores/eam1.yaml`, `eam2.yaml`, `eam3.yaml`
- `data/professores/profiles/*.json`

**Fluxo de dados aparente**:
```
Lattes → extract → profiles/*.json
                        ↓
                   templates (site)

eam*.yaml → templates (site)
```

**Questões adicionais**:
- Qual arquivo é renderizado nas páginas?
- Existe duplicação de dados?
- Um sobrescreve o outro?

**Ação recomendada**:
- [ ] Rastrear como os dados são usados nos templates
- [ ] Verificar se `eam*.yaml` é obsoleto
- [ ] Se obsoleto, remover ou arquivar
- [ ] Documentar a estrutura correta de dados

---

## 📅 Automação e Atualizações Frequentes

**Status**: 🔴 Não implementado

**Objetivo**: Estabelecer rotina automática de atualização dos bancos de dados

### Opções de implementação

#### Opção 1: GitHub Actions (CI/CD)
- Scripts rodam automaticamente em horário específico
- Não requer servidor próprio
- Limitado a certas funcionalidades (ex: CAPTCHAs do Lattes não funcionam)

#### Opção 2: Cron job em servidor
- Maior controle e flexibilidade
- Pode lidar com CAPTCHAs e interações manuais
- Requer infraestrutura própria

#### Opção 3: Combinação híbrida
- GitHub Actions para Scopus/Teses (sem CAPTCHA)
- Cron manual ou script interativo para Lattes

### Tarefas de automação por pipeline

#### Lattes (IMPOSSÍVEL AUTOMATIZAR COMPLETAMENTE)
- ⚠️ Requer resolução de CAPTCHA manual
- Sugestão: Baixar manualmente a cada semestre + extrair/atualizar via script

#### Scopus
- ✅ Pode ser automatizado
- Frequência: 1x por mês
- ```bash
  fetch_scopus_all_professors.py --resume
  deduplicate_publications.py
  merge_scopus_into_profiles.py
  generate_statistics.py
  ```

#### Teses (BDITA)
- ✅ Pode ser automatizado
- Frequência: 1x por mês
- ```bash
  scrape_bdita_theses.py
  generate_thesis_pages.py
  generate_statistics.py
  ```

### Exemplo: GitHub Actions workflow

```yaml
# .github/workflows/update-data.yml
name: Update publication data

on:
  schedule:
    - cron: '0 0 1 * *'  # 1º de cada mês

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: pip install -r scripts/requirements.txt
      - run: |
          cd scripts
          python fetch_scopus_all_professors.py --resume
          python deduplicate_publications.py
          python merge_scopus_into_profiles.py
          python generate_statistics.py
```

**Ação recomendada**:
- [ ] Definir frequência desejada de atualização
- [ ] Escolher estratégia de automação
- [ ] Implementar GitHub Actions ou cron
- [ ] Testar com dados reais
- [ ] Criar documentação de alertas/erros

---

## 📸 Fotos de Professores

**Status**: ⏳ Parcialmente completo

**Situação atual**: 23/52 professores têm fotos (44%)

### Fotos faltantes

Os seguintes professores **ainda não têm foto**:
- 29 professores da Fase 2 (não tiveram Lattes baixado ainda)

**Ação recomendada**:
- [ ] Completar download de Lattes dos 29 professores restantes
- [ ] Extrair fotos automaticamente via `extract_lattes_improved.py`
- [ ] Se foto não disponível no Lattes:
  - [ ] Coletar de outras fontes (ORCID, instituição)
  - [ ] Usar placeholder padrão
- [ ] Verificar qualidade das fotos (tamanho, resolução)
- [ ] Garantir padronização: 400x400px, JPEG

**Armazenamento**: `static/images/professores/nome-professor.jpg`

---

## 🏢 Fotos de Laboratórios

**Status**: 🔴 Não existem

**Objetivo**: Adicionar fotos dos 16 laboratórios

**Localização esperada**: `static/images/laboratorios/`

**Tarefas**:
- [ ] Fotografar cada laboratório
- [ ] Padronizar tamanho/resolução
- [ ] Nomear arquivos: `lab-eam1-nome.jpg`
- [ ] Atualizar `data/laboratorios.yaml` com campo de imagem:
  ```yaml
  imagem: "lab-eam1-nome.jpg"
  ```
- [ ] Atualizar template para exibir imagens

**Laboratórios**:
```
EAM1 (8 laboratórios):
- [ ] Lab 1
- [ ] Lab 2
- ...

EAM2 (4 laboratórios):
- [ ] Lab 1
- ...

EAM3 (4 laboratórios):
- [ ] Lab 1
- ...
```

---

## ✅ Verificação de Dados

**Status**: 🔴 Não feito

### Laboratórios

**Tarefas**:
- [ ] Verificar se todos os 16 laboratórios estão cadastrados
- [ ] Verificar descrições em PT e EN
- [ ] Verificar equipamentos listados
- [ ] Verificar projetos associados
- [ ] Adicionar fotos (veja seção anterior)
- [ ] Atualizar links PNIPE se disponíveis

**Arquivo**: `data/laboratorios.yaml`

### Projetos de Pesquisa

**Tarefas**:
- [ ] Verificar se todos os projetos ativos estão cadastrados
- [ ] Verificar valores de financiamento (moeda, montante)
- [ ] Verificar datas de vigência
- [ ] Verificar descrições em PT e EN
- [ ] Remover/atualizar projetos concluídos
- [ ] Verificar agências de fomento

**Arquivo**: `data/projetos.yaml`

**Questões a responder**:
- Quantos projetos ativos existem realmente?
- Quais agências financiam?
- Qual é o total de investimento?
- Há projetos sem representação no site?

---

## 📋 Checklist Geral de Manutenção

### Mensal
- [ ] Atualizar dados do Scopus (`fetch_scopus_*.py`)
- [ ] Verificar se há novos projetos aprovados
- [ ] Revisar teses/dissertações recentes

### Semestral
- [ ] Baixar e processar currículos Lattes
- [ ] Atualizar fotos de professores
- [ ] Revisar descrições de laboratórios
- [ ] Atualizar menus se houver mudanças estruturais

### Anual
- [ ] Auditar completude dos dados
- [ ] Atualizar links quebrados
- [ ] Revisar SEO e descrições

---

## 🔐 Segurança

### Pendências
- [ ] Remover chave Scopus hardcoded (vê `docs/data-pipelines/scopus.md`)
- [ ] Usar variáveis de ambiente para credenciais
- [ ] Adicionar arquivo `.env.example`
- [ ] Auditar outros scripts por hardcoded secrets

---

## 📖 Documentação Adicional Necessária

- [ ] Guia: "Extrair dados de um professor específico"
- [ ] Guia: "Como fazer rollback de dados"
- [ ] Guia: "Limpeza e consolidação de dados"
- [ ] Decisão: Remover arquivos YAML de professores? (Sim/Não/Arquivar)
- [ ] Especificação: Estrutura final de dados de professores

---

## 🚀 Próximas Prioridades

### Alto (bloqueia funcionalidade)
1. Esclarecer YAML vs JSON de professores
2. Completar Lattes (29 professores restantes)
3. Implementar automação de atualização

### Médio (melhora UX)
4. Adicionar fotos de laboratórios
5. Verificar completude de projetos

### Baixo (técnico)
6. Remover chave API hardcoded
7. Consolidar scripts legados
