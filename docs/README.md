# Documentação do Site PG-EAM

Esta documentação explica como atualizar e manter o site do Programa de Pós-Graduação em Engenharia Aeronáutica e Mecânica (PG-EAM) do ITA.

## 🚀 Novo no projeto?

Comece por aqui: **[Início Rápido](getting-started.md)** - Configure o ambiente em 5 minutos.

## Guias por Objetivo

### Preciso atualizar conteúdo do site

| O que fazer | Guia |
|-------------|------|
| Adicionar/editar página de texto | [Gerenciamento de Páginas](content-management/pages.md) |
| Atualizar dados de professor | [Gerenciamento de Professores](content-management/professors.md) |
| Adicionar/editar laboratório | [Gerenciamento de Laboratórios](content-management/laboratories.md) |
| Adicionar/editar projeto de pesquisa | [Gerenciamento de Projetos](content-management/projects.md) |
| Adicionar documento (PDF) | [Gerenciamento de Documentos](content-management/documents.md) |
| Modificar menu de navegação | [Menus de Navegação](content-management/menus.md) |

### Preciso atualizar bancos de dados

| O que fazer | Guia |
|-------------|------|
| Baixar/atualizar dados do Lattes | [Pipeline Lattes](data-pipelines/lattes.md) |
| Atualizar publicações do Scopus | [Pipeline Scopus](data-pipelines/scopus.md) |
| Atualizar teses e dissertações | [Pipeline Teses](data-pipelines/theses.md) |
| Regenerar estatísticas | [Geração de Estatísticas](data-pipelines/statistics.md) |

### Preciso fazer deploy ou desenvolver

| O que fazer | Guia |
|-------------|------|
| Rodar o site localmente | [Desenvolvimento Local](deployment/local-development.md) |
| Publicar no GitHub Pages | [Deploy para Produção](deployment/github-pages.md) |

### Preciso de referência técnica

| O que fazer | Guia |
|-------------|------|
| Entender a estrutura do projeto | [Estrutura do Projeto](reference/project-structure.md) |
| Ver todos os scripts disponíveis | [Referência de Scripts](reference/scripts.md) |
| Resolver problemas comuns | [Troubleshooting](reference/troubleshooting.md) |

## Início Rápido

```bash
# Clonar o repositório
git clone https://github.com/flavioluiz/pgeam_dev.git
cd pgeam_dev

# Iniciar servidor de desenvolvimento
hugo server -D

# Acessar em: http://localhost:1313
```

## Pré-requisitos

- [Hugo](https://gohugo.io/installation/) versão 0.121.0+
- Git
- Python 3.8+ (para scripts de atualização de dados)

### Dependências Python (para pipelines de dados)

```bash
pip install requests beautifulsoup4 pybliometrics selenium webdriver-manager
```

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                         FONTES DE DADOS                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Lattes/CNPq   │     Scopus      │         BDITA               │
│   (currículos)  │  (publicações)  │   (teses/dissertações)      │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCRIPTS DE EXTRAÇÃO                          │
│  download_lattes.py │ fetch_scopus_*.py │ scrape_bdita_theses.py│
└────────┬────────────┴────────┬──────────┴───────────┬───────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DADOS (data/)                           │
│  professores/profiles/ │ scopus/raw/ │ teses/by_id/             │
│       (JSON)           │   (JSON)    │   (JSON)                 │
└────────┬────────────────────┬────────────────┬──────────────────┘
         │                    │                │
         ▼                    ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         HUGO BUILD                              │
│               layouts/ + content/ + data/ → public/             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SITE PUBLICADO                               │
│              https://flavioluiz.github.io/pgeam/                │
└─────────────────────────────────────────────────────────────────┘
```

## Status dos Pipelines de Dados

| Pipeline | Status | Observações |
|----------|--------|-------------|
| Lattes | ⚠️ Parcial | 23/52 professores processados. Requer intervenção manual (CAPTCHAs) |
| Scopus | ✅ Funcional | Requer acesso à rede do ITA ou VPN |
| Teses BDITA | ✅ Funcional | 1.874 teses/dissertações indexadas |
| Estatísticas | ✅ Funcional | Geradas automaticamente |

## 📋 Plano de Manutenção e Melhorias

Existem questões pendentes sobre a estrutura dos dados e rotinas de automação que precisam ser investigadas e implementadas.

**[→ Ver Plano de Manutenção](maintenance.md)**

### Principais tarefas:
- ⚠️ Verificar segurança de extração do Lattes
- 🔍 Esclarecer redundância YAML vs JSON de professores
- 📅 Implementar automação de atualização (GitHub Actions?)
- 📸 Completar fotos de professores (44% completo)
- 🏢 Adicionar fotos de laboratórios
- ✅ Verificar completude de projetos e laboratórios

## Suporte

- Email: pgeam@ita.br
- Repositório: https://github.com/flavioluiz/pgeam_dev
