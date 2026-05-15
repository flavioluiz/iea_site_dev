# Site PG-EAM

Site do Programa de Pós-Graduação em Engenharia Aeronáutica e Mecânica (PG-EAM) do ITA.

**URL**: https://flavioluiz.github.io/pgeam/

## Quick Start

```bash
# Clonar
git clone https://github.com/flavioluiz/pgeam_dev.git
cd pgeam_dev

# Rodar localmente
hugo server -D

# Acessar
open http://localhost:1313
```

## Documentação

📚 **[Ver documentação completa](docs/README.md)**

### Guias Rápidos

| Objetivo | Guia |
|----------|------|
| Editar páginas de texto | [Gerenciamento de Páginas](docs/content-management/pages.md) |
| Atualizar dados de professor | [Gerenciamento de Professores](docs/content-management/professors.md) |
| Atualizar publicações (Scopus) | [Pipeline Scopus](docs/data-pipelines/scopus.md) |
| Atualizar currículos (Lattes) | [Pipeline Lattes](docs/data-pipelines/lattes.md) |
| Atualizar teses | [Pipeline Teses](docs/data-pipelines/theses.md) |
| Fazer deploy | [Deploy GitHub Pages](docs/deployment/github-pages.md) |

## Pré-requisitos

- [Hugo](https://gohugo.io/installation/) 0.121.0+
- Git
- Python 3.8+ (para scripts de dados)

```bash
pip install requests beautifulsoup4 pybliometrics selenium webdriver-manager
```

## Estrutura

```
pgeam_dev/
├── content/           # Conteúdo Markdown (PT/EN)
├── data/              # Dados (professores, teses, publicações)
├── layouts/           # Templates HTML
├── static/            # Arquivos estáticos (imagens, PDFs)
├── scripts/           # Scripts de automação
├── docs/              # Documentação detalhada
└── deploy/            # Build de produção (repo separado)
```

## Repositórios

| Repositório | Conteúdo |
|-------------|----------|
| [pgeam_dev](https://github.com/flavioluiz/pgeam_dev) | Código fonte (este) |
| [pgeam](https://github.com/flavioluiz/pgeam) | Site publicado |

## Deploy

```bash
./scripts/deploy.sh
```

## Estatísticas

- 3 Áreas de Concentração
- 52 Professores Permanentes
- 16 Laboratórios
- 1.874 Teses e Dissertações
- Site Bilíngue (PT/EN)

## Suporte

- Email: pgeam@ita.br
- Issues: https://github.com/flavioluiz/pgeam_dev/issues

---

© 2025 Instituto Tecnológico de Aeronáutica - ITA
