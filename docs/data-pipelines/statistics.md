# Geração de Estatísticas

Gera métricas agregadas do programa para a página de estatísticas.

## Quando executar

Execute após atualizar qualquer pipeline de dados:
- Após atualizar teses (`scrape_bdita_theses.py`)
- Após atualizar publicações do Scopus
- Após atualizar perfis de professores

## Uso

```bash
cd scripts
python generate_statistics.py
```

## Arquivo gerado

`data/statistics.json` - Usado pelo template `layouts/estatisticas/list.html`

## Métricas calculadas

### Publicações

- Total de publicações
- Total de citações
- Distribuição por ano (últimos 10 anos)
- Top 10 publicações mais citadas por período:
  - Últimos 2 anos
  - Últimos 5 anos
  - Últimos 10 anos
  - Todos os tempos

### Professores

- Estatísticas por professor:
  - Total de artigos
  - Total de citações
  - H-index calculado

### Teses e Dissertações

- Total de teses e dissertações
- Distribuição por tipo (Mestrado/Doutorado)
- Distribuição por ano
- Distribuição por área de concentração

### Bolsistas CNPq

- Total de bolsistas
- Distribuição por nível (1A, 1B, 1C, 1D, 2)

## Estrutura do JSON

```json
{
  "publications": {
    "total": 1234,
    "total_citations": 5678,
    "by_year": {
      "2024": 45,
      "2023": 52
    },
    "top_cited": {
      "2_years": [...],
      "5_years": [...],
      "10_years": [...],
      "all_time": [...]
    }
  },
  "theses": {
    "total": 1874,
    "mestrado": 1359,
    "doutorado": 515,
    "by_year": {...},
    "by_area": {...}
  },
  "cnpq": {
    "total": 13,
    "by_level": {
      "1A": 1,
      "1D": 3,
      "2": 9
    }
  },
  "last_updated": "2025-01-22"
}
```

## Exibição no Site

As estatísticas são exibidas em:
- `/pt/estatisticas/`
- `/en/statistics/`

## Scripts Relacionados

| Script | Descrição | Status |
|--------|-----------|--------|
| `generate_statistics.py` | Gera statistics.json | ✅ Estável |
| `generate_subject_areas.py` | Gera lista de áreas temáticas | ✅ Estável |
