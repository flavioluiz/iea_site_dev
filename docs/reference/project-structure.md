# Estrutura do Projeto

```
pgeam_dev/
├── config/                    # Configurações Hugo
│   ├── _default/
│   │   ├── config.yaml        # Config principal
│   │   ├── languages.yaml     # Idiomas PT/EN
│   │   ├── menus.yaml         # Menu PT
│   │   ├── menus.en.yaml      # Menu EN
│   │   └── params.yaml        # Parâmetros do site
│   └── production/
│       └── config.yaml        # Config para GitHub Pages
│
├── content/                   # Conteúdo em Markdown
│   ├── _index.md              # Homepage PT
│   ├── _index.en.md           # Homepage EN
│   ├── sobre/                 # Página Sobre
│   ├── areas/                 # Áreas de concentração
│   ├── professores/           # Páginas dos professores
│   ├── teses/                 # Páginas de teses
│   ├── publicacoes/           # Páginas de publicações
│   ├── laboratorios/          # Laboratórios
│   ├── projetos/              # Projetos de pesquisa
│   ├── documentos/            # Documentos
│   ├── estatisticas/          # Estatísticas
│   └── contato/               # Contato
│
├── data/                      # Dados estruturados
│   ├── professores/
│   │   ├── eam1.yaml          # Professores EAM-1
│   │   ├── eam2.yaml          # Professores EAM-2
│   │   ├── eam3.yaml          # Professores EAM-3
│   │   └── profiles/          # Perfis detalhados (JSON)
│   ├── teses/
│   │   ├── index.json         # Índice de teses
│   │   ├── by_id/             # Teses individuais
│   │   ├── by_professor.json  # Mapa orientador→teses
│   │   └── manual_matches.json # Matches manuais
│   ├── scopus/
│   │   └── raw/               # Dados brutos do Scopus
│   ├── publications/
│   │   ├── index.json         # Índice de publicações
│   │   └── by_eid/            # Publicações individuais
│   ├── laboratorios.yaml      # Laboratórios
│   ├── projetos.yaml          # Projetos de pesquisa
│   ├── documentos.yaml        # Documentos
│   ├── areas.yaml             # Áreas de concentração
│   └── statistics.json        # Estatísticas agregadas
│
├── layouts/                   # Templates HTML
│   ├── _default/              # Templates padrão
│   ├── partials/              # Componentes reutilizáveis
│   ├── shortcodes/            # Shortcodes customizados
│   ├── professores/           # Template de professores
│   ├── teses/                 # Template de teses
│   ├── estatisticas/          # Template de estatísticas
│   └── index.html             # Template da homepage
│
├── static/                    # Arquivos estáticos PERMANENTES
│   ├── images/
│   │   ├── ita_logo.png       # Logo do ITA
│   │   ├── favicon.ico        # Favicon
│   │   └── professores/       # Fotos dos professores
│   ├── documents/             # PDFs
│   └── js/                    # JavaScript customizado
│
├── i18n/                      # Traduções
│   ├── pt.yaml                # Strings em português
│   └── en.yaml                # Strings em inglês
│
├── scripts/                   # Scripts de automação
│   ├── deploy.sh              # Deploy automatizado
│   ├── download_lattes.py     # Download de Lattes
│   ├── extract_lattes_*.py    # Extração de Lattes
│   ├── fetch_scopus_*.py      # Download do Scopus
│   ├── scrape_bdita_theses.py # Scraping de teses
│   ├── generate_*.py          # Scripts de geração
│   └── *.md, *.txt            # Documentação auxiliar
│
├── lattes_data/               # Dados do Lattes (não versionado)
│   ├── lattes_html/           # HTMLs baixados
│   └── lattes_extracted/      # Dados extraídos
│
├── public/                    # [GERADO] Build local
├── deploy/                    # [GERADO] Build para produção
├── resources/                 # [GERADO] Cache do Hugo
│
├── docs/                      # Documentação
└── README.md                  # README principal
```

## Diretórios Importantes

### `config/`
Configurações do Hugo. O subdiretório `_default/` contém configurações base, e `production/` sobrescreve para deploy.

### `content/`
Conteúdo do site em Markdown. Cada página tem versões `.md` (PT) e `.en.md` (EN).

### `data/`
Dados estruturados em YAML/JSON. Acessíveis nos templates via `.Site.Data`.

### `layouts/`
Templates HTML usando a linguagem de templates do Hugo.

### `static/`
Arquivos copiados diretamente para o build. **Não deletar.**

### `scripts/`
Scripts Python e Shell para automação de dados.

## Arquivos Gerados (Ignorar no Git)

| Diretório | Propósito |
|-----------|-----------|
| `public/` | Build de desenvolvimento |
| `deploy/` | Build de produção (repo separado) |
| `resources/` | Cache de processamento |
| `lattes_data/` | Dados Lattes baixados |

## Convenções de Nomenclatura

### IDs de professor
- Formato: `nome-sobrenome` (slug)
- Exemplo: `joao-silva`, `andre-cavalieri`

### Arquivos de conteúdo
- Português: `arquivo.md` ou `arquivo.pt.md`
- Inglês: `arquivo.en.md`

### Áreas de concentração
- `eam1` - Projeto Aeronáutico
- `eam2` - Propulsão e Energia
- `eam3` - Materiais e Manufatura
