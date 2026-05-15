# Referência de Scripts

Todos os scripts estão em `scripts/`.

## Scripts Principais

### Lattes

| Script | Descrição | Status |
|--------|-----------|--------|
| `download_lattes.py` | Download interativo de currículos Lattes | ✅ Estável |
| `extract_lattes_improved.py` | Extração de dados com/sem IA | ✅ Estável |
| `update_site_from_lattes.py` | Integração dos dados ao site | ✅ Estável |

### Scopus

| Script | Descrição | Status |
|--------|-----------|--------|
| `match_professors_to_scopus.py` | Associa professores a IDs Scopus | ✅ Estável |
| `fetch_scopus_all_professors.py` | Baixa dados do Scopus | ✅ Estável |
| `deduplicate_publications.py` | Remove publicações duplicadas | ✅ Estável |
| `merge_scopus_into_profiles.py` | Integra publicações aos perfis | ✅ Estável |

### Teses

| Script | Descrição | Status |
|--------|-----------|--------|
| `scrape_bdita_theses.py` | Web scraping da BDITA | ✅ Estável |
| `generate_thesis_pages.py` | Processa teses e gera páginas | ✅ Estável |

### Estatísticas e Conteúdo

| Script | Descrição | Status |
|--------|-----------|--------|
| `generate_statistics.py` | Gera métricas agregadas | ✅ Estável |
| `generate_publication_pages.py` | Gera páginas de publicações | ✅ Estável |
| `generate_subject_areas.py` | Lista áreas temáticas | ✅ Estável |

### Deploy

| Script | Descrição | Status |
|--------|-----------|--------|
| `deploy.sh` | Deploy automatizado para GitHub Pages | ✅ Estável |
| `COMANDOS_RAPIDOS.sh` | Menu interativo de comandos | ✅ Estável |

## Scripts Legados/Auxiliares

⚠️ Estes scripts foram substituídos ou são auxiliares:

| Script | Descrição | Status |
|--------|-----------|--------|
| `extract_lattes_data.py` | Versão anterior de extração | ⚠️ Substituído |
| `extract_lattes_metadata.py` | Extração apenas de metadados | ⚠️ Substituído |
| `integrate_lattes_data.py` | Versão anterior de integração | ⚠️ Substituído |
| `integrate_lattes_metadata.py` | Integração de metadados | ⚠️ Substituído |
| `get_scopus.py` | Módulo auxiliar do Scopus | ✅ Interno |
| `scopus_busca_autores_ita.py` | Busca autores por afiliação | ⚠️ Utilitário |
| `migrate_yaml_to_json.py` | Migração YAML→JSON (única vez) | ✅ Concluído |
| `generate_content.py` | Gerador simples de Markdown | ⚠️ Legado |

## Uso Rápido

### Atualizar dados do Lattes
```bash
cd scripts
python download_lattes.py           # Baixar HTMLs
python extract_lattes_improved.py   # Extrair dados
python update_site_from_lattes.py --backup  # Atualizar perfis
```

### Atualizar publicações do Scopus
```bash
cd scripts
python fetch_scopus_all_professors.py --resume
python deduplicate_publications.py
python merge_scopus_into_profiles.py
```

### Atualizar teses
```bash
cd scripts
python scrape_bdita_theses.py
python generate_thesis_pages.py
```

### Atualizar estatísticas
```bash
cd scripts
python generate_statistics.py
```

### Deploy
```bash
./scripts/deploy.sh
```

## Variáveis de Ambiente

| Variável | Script | Descrição |
|----------|--------|-----------|
| `SYNTHETIC_API_KEY` | `extract_lattes_improved.py` | Chave da API Synthetic (opcional) |
| `SCOPUS_API_KEY` | Scripts Scopus | Chave da API Scopus (recomendado) |

## Arquivos de Configuração

| Arquivo | Descrição |
|---------|-----------|
| `requirements.txt` | Dependências Python |
| `matched_professors.json` | Mapeamento professor→Scopus ID |

## Documentação Auxiliar em scripts/

| Arquivo | Descrição |
|---------|-----------|
| `README_LATTES.md` | Documentação do download Lattes |
| `GUIA_ATUALIZACAO_SITE.md` | Guia de atualização |
| `COMO_USAR_LATTES.txt` | Quick start Lattes |
| `STATUS.txt` | Status do projeto |
| `NEXT_STEPS.md` | Próximos passos |

> **Nota**: Grande parte dessa documentação foi consolidada em `docs/`.
