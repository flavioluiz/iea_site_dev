# Plano de Implementação — Site da Divisão de Engenharia Aeronáutica e Aeroespacial (AER/ITA)

> **Nota histórica:** este documento registra a concepção inicial do site e
> menciona o template PG-EAM que lhe deu origem. Para a arquitetura atual de
> conteúdo, CMS e publicação, use o [README](README.md) e o
> [checklist de ativação](docs/operations/activation-checklist.md).

> **Status:** Em andamento
> **Base:** Fork do site PGEAM (`pgeam_dev`) — Hugo + Tailwind CSS
> **Repositório:** `aer_dev`
> **Data de início:** 2026-05-13

---

## Visão Geral

Site institucional da **Divisão de Engenharia Aeronáutica e Aeroespacial do ITA**, com ênfase na área espacial como diferencial estratégico. Diferente do EAM (site de programa de pós-graduação), este é um site de **divisão acadêmica**, com foco em:

- Estrutura organizacional (departamentos, chefia)
- Pessoal (professores por departamento, técnicos)
- Laboratórios com infraestrutura detalhada
- Projetos de pesquisa (aeronáuticos e espaciais)
- Landing page dedicada à área espacial

**Audiência-alvo:** alunos de graduação e pós-graduação, candidatos, parceiros industriais, agências espaciais, sociedade em geral.

---

## Arquitetura de Conteúdo

### Navegação principal

```
Divisão AER
├── Sobre
│   ├── A Divisão (histórico, missão, visão)
│   ├── Organização (departamentos)
│   └── Infraestrutura
├── Pessoal
│   ├── Professores (por departamento)
│   └── Técnicos / Staff
├── Pesquisa
│   ├── Linhas de Pesquisa
│   │   ├── Aeronáutica
│   │   └── Espacial
│   ├── Projetos
│   └── Publicações
├── Laboratórios
│   ├── Aeronáuticos
│   └── Espaciais
├── Graduação
│   ├── Cursos oferecidos
│   └── Disciplinas
├── Pós-Graduação → links para PGEAM / PGCEA
└── Contato
```

### Área Espacial (landing page dedicada `/espaco/`)

Consolida transversalmente:
- Laboratórios com atuação espacial
- Projetos espaciais ativos
- Professores com pesquisa espacial
- Parcerias institucionais (AEB, DCTA/IAE, INPE, ESA, etc.)
- Missões e realizações históricas do ITA na área espacial

---

## Estrutura de Arquivos Hugo

```
aer_dev/
├── config/
│   └── _default/
│       ├── config.yaml          # Título "AER/ITA", URL, idiomas
│       ├── languages.yaml       # pt (primário) + en
│       └── params.yaml          # Chefe da divisão, contatos, logos
├── content/
│   ├── sobre/                   # A divisão
│   ├── departamentos/           # Subdepartamentos
│   ├── pessoal/                 # Professores + técnicos
│   │   └── {slug}/              # Perfil individual
│   ├── pesquisa/
│   │   ├── linhas/              # Linhas de pesquisa
│   │   └── projetos/            # Projetos individuais
│   ├── laboratorios/            # Laboratórios
│   │   └── {slug}/              # Lab individual
│   ├── espaco/                  # Landing page espacial
│   ├── publicacoes/             # Gerado por pipeline Scopus
│   ├── graduacao/               # Disciplinas e cursos
│   └── contato/
├── data/
│   ├── paginas/                 # Mapa do site PT/EN e páginas textuais comuns
│   ├── laboratorios/            # Uma ficha JSON por laboratório
│   ├── departamentos.yaml       # Lista e info dos departamentos
│   ├── projetos.yaml            # Projetos com financiadores, período
│   ├── linhas_pesquisa.yaml     # Linhas (aeronáutica / espacial)
│   ├── pessoal/
│   │   ├── {departamento}.yaml  # Professores por departamento
│   │   └── profiles/
│   │       └── *.json           # Perfil individual (Lattes, Scopus, ORCID)
│   └── publicacoes/             # Gerado por pipeline Scopus
├── layouts/
│   ├── _default/
│   ├── pessoal/                 # Baseado em docentes/ do EAM
│   ├── laboratorios/            # Baseado em laboratorios/ do EAM
│   ├── projetos/                # Baseado em projetos/ do EAM
│   ├── publicacoes/             # Baseado em publicacoes/ do EAM
│   ├── espaco/                  # Novo: landing page espacial
│   ├── departamentos/           # Novo: list + single de departamento
│   └── partials/
├── static/
│   ├── images/
│   │   ├── aer_logo.png
│   │   ├── gallery/             # Fotos da divisão, labs, satélites
│   │   ├── laboratorios/        # Fotos dos labs
│   │   └── pessoal/             # Fotos dos professores
│   └── js/                      # Filtros reutilizados do EAM
├── assets/                      # CSS Tailwind
├── i18n/
│   ├── pt.yaml
│   └── en.yaml
└── scripts/                     # Pipeline de dados (fork do EAM)
```

---

## Novos Componentes (em relação ao EAM)

### Layouts novos

| Layout | Arquivo | Descrição |
|--------|---------|-----------|
| Departamentos — lista | `departamentos/list.html` | Cards com chefia, áreas, links |
| Departamentos — detalhe | `departamentos/single.html` | Professores, labs e projetos do dept |
| Espaço — landing | `espaco/list.html` | Showcase: missões, labs, projetos, parceiros |
| Linhas de pesquisa | `pesquisa/linhas/list.html` | Mapa visual aeronáutica vs espacial |

### Partials novos

| Partial | Arquivo | Descrição |
|---------|---------|-----------|
| Card de departamento | `dept-card.html` | Nome, chefe, áreas, contagem de docentes |
| Card de missão/projeto espacial | `mission-card.html` | Destaque para projetos espaciais |
| Grid de parceiros | `partner-logo.html` | Logos AEB, INPE, ESA, DCTA... |
| Card de linha de pesquisa | `research-line-card.html` | Com tags aeronáutica/espacial |

---

## Dados a Levantar (Curadoria de Conteúdo)

### Estrutura organizacional
- [ ] Lista oficial dos departamentos e siglas
- [ ] Chefe da Divisão (nome, e-mail, Lattes)
- [ ] Chefes de cada departamento
- [ ] Organograma formal

### Pessoal
- [ ] Lista de professores por departamento (nome, título, Lattes, e-mail)
- [ ] Fotos (mínimo 400×400px, preferencialmente 600×600px)
- [ ] Linhas de pesquisa individuais
- [ ] IDs Scopus, ORCID, Google Scholar por professor
- [ ] Técnicos de laboratório (nome, lab, especialidade)

### Laboratórios
Para cada laboratório:
- [ ] Nome completo + sigla + departamento responsável
- [ ] Descrição e capacidades
- [ ] Lista de equipamentos principais
- [ ] Professor responsável e técnicos
- [ ] Projetos associados
- [ ] Fotos do espaço físico (mínimo 3 por lab)
- [ ] Links externos (PNIPE, SISCOAF, etc.)
- [ ] Tema: aeronáutico / espacial / ambos

### Projetos de pesquisa
- [ ] Título e descrição
- [ ] Financiador (FAPESP, CNPq, AEB, FINEP, FAB, ESA...)
- [ ] Valor e período (início–fim ou "em andamento")
- [ ] Professores envolvidos
- [ ] Tema: aeronáutico / espacial / ambos

### Área espacial (curadoria especial)
- [ ] Histórico do ITA na área espacial (linha do tempo)
- [ ] Satélites e missões com participação do ITA
- [ ] Projetos CubeSat, propulsão, GNC, astrobiologia
- [ ] Parcerias: AEB, DCTA/IAE, INPE, ESA, parceiros internacionais
- [ ] Fotos de destaque (satélites, sala limpa, propulsores)

---

## Fases de Implementação

### Fase 1 — Setup e Template ✅ Concluída
**Duração estimada: 2 semanas**

- [x] Fork do `pgeam_dev` → `aer_dev`
- [x] Criar plano de implementação (`IMPLEMENTACAO.md`)
- [x] Configuração base: `config.yaml`, `params.yaml`, menus
- [ ] Substituir logo e favicon por identidade AER/ITA (aguarda asset)
- [ ] Definir paleta de cores oficial (aguarda identidade visual)
- [x] Remover seções específicas do EAM (regulamento, processo seletivo, teses, dissertações)
- [x] Renomear seção `docentes/` → `pessoal/`
- [x] Renomear seção `areas/` → `linhas/` (linhas de pesquisa)
- [x] Criar seções novas: `departamentos/`, `espaco/`, `graduacao/`
- [x] Reescrever homepage (`index.html`) para identidade AER
- [x] Criar `data/departamentos.yaml` (ALA, ALB, ALC, ALD, ALE)
- [x] Criar `data/linhas_pesquisa.yaml` (11 linhas: aeronáutica + espacial)
- [x] Adicionar campo `tema` (aeronautica/espacial/ambos) em labs e projetos
- [x] Criar layouts `departamentos/list.html` e `espaco/list.html`
- [x] Adaptar `pessoal/list.html` para agrupamento por departamento
- [x] Adaptar partials `header.html` e `footer.html` para AER
- [x] Build Hugo sem erros (2718 páginas geradas)

### Fase 2 — Estrutura de Conteúdo
**Duração estimada: 3 semanas**

- [ ] Criar seções de conteúdo base com markdown placeholder
- [ ] Implementar layouts de Departamentos (`list.html` + `single.html`)
- [ ] Adaptar layout de Pessoal (baseado em `docentes/` do EAM)
- [ ] Adaptar layout de Laboratórios (adicionar campo `tema` e filtro)
- [ ] Adaptar layout de Projetos (adicionar campo `tema` e filtro)
- [ ] Implementar layout de Linhas de Pesquisa
- [ ] Criar partials novos (`dept-card`, `mission-card`, `partner-logo`, `research-line-card`)

### Fase 3 — Área Espacial
**Duração estimada: 2 semanas**

- [ ] Design e implementação da landing page `/espaco/`
- [ ] Timeline de missões e marcos espaciais do ITA
- [ ] Grid de parceiros institucionais com logos
- [ ] Showcase de projetos espaciais em destaque
- [ ] Sistema de tags transversais: marcar labs, projetos, pessoal com `espacial: true`
- [ ] Galeria de imagens temáticas (satélites, propulsores, sala limpa)

### Fase 4 — Dados e Perfis
**Duração estimada: 3 semanas**

- [ ] Criar `data/departamentos.yaml` com todos os departamentos
- [ ] Criar arquivos YAML por departamento em `data/pessoal/`
- [ ] Criar perfis JSON individuais dos professores em `data/pessoal/profiles/`
- [ ] Popular `data/laboratorios.yaml` com infra detalhada
- [ ] Popular `data/projetos.yaml` com todos os projetos
- [ ] Popular `data/linhas_pesquisa.yaml`
- [ ] Padronizar e redimensionar fotos dos professores
- [ ] Fotos dos laboratórios

### Fase 5 — Publicações e Métricas
**Duração estimada: 2 semanas**

- [ ] Adaptar scripts Scopus do EAM para IDs dos professores da AER
- [ ] Sincronizar publicações via API Scopus
- [ ] Gerar páginas de publicações por professor
- [ ] Dashboard de estatísticas da divisão (número de labs, projetos, publicações)

### Fase 6 — i18n, Revisão e Deploy
**Duração estimada: 2 semanas**

- [ ] Tradução de strings para inglês (`i18n/en.yaml`)
- [ ] Tradução do conteúdo principal (sobre, linhas, labs, projetos)
- [ ] Revisão com equipe da divisão AER
- [ ] Testes de responsividade (mobile, tablet, desktop)
- [ ] Testes de acessibilidade (WCAG 2.1 AA)
- [ ] Deploy em servidor ITA (pipeline SFTP, baseado no EAM)
- [ ] Configuração de domínio (`aer.ita.br`)

**Total estimado: ~14 semanas**

---

## Diferenças em Relação ao EAM

| Aspecto | EAM (pós-graduação) | AER (divisão) |
|---------|--------------------|--------------------|
| Foco | Programa acadêmico | Divisão institucional |
| Audiência | Candidatos ao programa | Ampla: alunos, indústria, sociedade |
| Teses/Dissertações | Seção central | Fora do escopo (EAM/PGCEA têm isso) |
| Departamentos | Inexistente | Seção central |
| Ênfase espacial | Inexistente | Landing page + tagging transversal |
| Técnicos de lab | Inexistente | Incluídos |
| Parcerias institucionais | Internacional genérico | Grid de parceiros (AEB, IAE, INPE, ESA) |
| Processo seletivo | Seção central | Fora do escopo |
| Regulamento | Seção central | Fora do escopo |

---

## Referências

- **Template base:** `/Users/flavioribeiro/github/pgeam_dev`
- **Site antigo AER:** https://web.archive.org/web/20220119200627/http://www.aer.ita.br/
- **Site atual AER:** https://www.aer.ita.br/
- **Hugo docs:** https://gohugo.io/documentation/
- **Tailwind CSS:** https://tailwindcss.com/docs
