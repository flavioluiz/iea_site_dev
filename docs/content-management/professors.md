# Gerenciamento de Professores

## Estrutura de Dados

Os dados de professores estão organizados em dois formatos:

### 1. Listas por área (YAML)
```
data/professores/
├── eam1.yaml    # Projeto Aeronáutico
├── eam2.yaml    # Propulsão e Energia
└── eam3.yaml    # Materiais e Manufatura
```

### 2. Perfis detalhados (JSON)
```
data/professores/profiles/
├── nome-sobrenome.json
├── outro-professor.json
└── ...
```

## Adicionar um Novo Professor

### Passo 1: Adicionar à lista da área

Abra o arquivo correspondente (`eam1.yaml`, `eam2.yaml` ou `eam3.yaml`):

```yaml
- nome: "João da Silva"
  nome_destaque: "João"
  lattes: "http://lattes.cnpq.br/1234567890"
  site: "https://joao.exemplo.com"  # opcional
  linhas_pesquisa:
    - "Machine Learning"
    - "Computer Vision"
```

### Passo 2: Criar perfil detalhado

Crie `data/professores/profiles/joao-silva.json`:

```json
{
  "id": "joao-silva",
  "nome": "João da Silva",
  "area": "eam1",
  "lattes": "http://lattes.cnpq.br/1234567890",
  "email": "joao@ita.br",
  "linhas_pesquisa": [
    "Machine Learning",
    "Computer Vision"
  ],
  "linhas_pesquisa_en": [
    "Machine Learning",
    "Computer Vision"
  ],
  "metrics": {
    "h_index": 0,
    "citacoes": 0,
    "artigos": 0
  },
  "links": {
    "orcid": "",
    "google_scholar": "",
    "web_of_science": ""
  }
}
```

### Passo 3: Criar páginas de conteúdo

```bash
touch content/professores/joao-silva.md
touch content/professores/joao-silva.en.md
```

Conteúdo básico (`joao-silva.md`):
```markdown
---
title: "João da Silva"
professor_id: "joao-silva"
---
```

## Atualizar Dados de um Professor

### Edição manual

1. Edite o arquivo JSON em `data/professores/profiles/`
2. Campos comuns:
   - `linhas_pesquisa` / `linhas_pesquisa_en` - Linhas de pesquisa
   - `metrics` - H-index, citações, artigos
   - `links` - ORCID, Scholar, WoS
   - `bolsista_cnpq` - Status de bolsista
   - `foto` - Nome do arquivo de foto

### Atualização automatizada via Lattes

Veja [Pipeline Lattes](../data-pipelines/lattes.md) para atualização em massa.

### Atualização via Scopus

Veja [Pipeline Scopus](../data-pipelines/scopus.md) para importar publicações.

## Adicionar Foto de Professor

1. Coloque a foto em `static/images/professores/`
2. Nome do arquivo: `nome-sobrenome.jpg`
3. Tamanho recomendado: 400x400px, JPEG
4. Atualize o perfil JSON:

```json
{
  "foto": "nome-sobrenome.jpg"
}
```

## Campos do Perfil JSON

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único (slug) |
| `nome` | string | Nome completo |
| `area` | string | Área: eam1, eam2 ou eam3 |
| `lattes` | string | URL do currículo Lattes |
| `email` | string | Email institucional |
| `linhas_pesquisa` | array | Linhas de pesquisa (PT) |
| `linhas_pesquisa_en` | array | Linhas de pesquisa (EN) |
| `bolsista_cnpq` | string | Ex: "Sim - Nível 1D" |
| `foto` | string | Nome do arquivo de foto |
| `metrics.h_index` | number | Índice H |
| `metrics.citacoes` | number | Total de citações |
| `metrics.artigos` | number | Total de artigos |
| `links.orcid` | string | URL do ORCID |
| `links.google_scholar` | string | URL do Google Scholar |
| `links.web_of_science` | string | URL do ResearcherID |
| `publicacoes` | array | Lista de publicações |

## Migração YAML → JSON

Se precisar converter dados antigos em YAML para o novo formato JSON:

```bash
cd scripts
python migrate_yaml_to_json.py
```

Este script foi usado na migração inicial e pode servir de referência.
