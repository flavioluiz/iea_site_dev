# Pipeline Scopus

Importa publicações e métricas do Scopus (Elsevier) para os perfis dos professores.

## O que é extraído

- Lista completa de publicações
- Métricas: h-index, citações, artigos
- Dados bibliográficos: DOI, revista, coautores

## Requisitos

### Acesso à rede do ITA

⚠️ **OBRIGATÓRIO**: O computador deve estar:
- Conectado à **rede do ITA** (cabo ou Wi-Fi institucional), ou
- Usando **VPN do ITA**

Sem acesso à rede institucional, a API do Scopus retornará erro de autenticação.

### Dependências Python

```bash
pip install pybliometrics requests
```

## Fluxo Completo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Matching    │ ──► │  2. Download    │ ──► │  3. Deduplicar  │
│  match_profs    │     │  fetch_scopus   │     │  deduplicate    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 matched_profs.json      scopus/raw/            publications/
                         *_pubs.json            by_eid/*.json
                                                       │
                                                       ▼
                                          ┌─────────────────┐
                                          │  4. Merge       │
                                          │  merge_scopus   │
                                          └─────────────────┘
                                                  │
                                                  ▼
                                           profiles/*.json
```

## Passo 1: Associar Professores ao Scopus

```bash
cd scripts
python match_professors_to_scopus.py
```

### Modos de matching

| Modo | Confiança | Descrição |
|------|-----------|-----------|
| `--mode orcid` | 100% | Por ORCID |
| `--mode name` | 90% | Por nome normalizado |
| `--mode llm` | 70-95% | Assistido por IA |
| `--mode all` | - | Todos os métodos (padrão) |

### Arquivo gerado

`scripts/matched_professors.json` - Mapeamento professor → ID Scopus

## Passo 2: Baixar Dados do Scopus

```bash
python fetch_scopus_all_professors.py --resume
```

### Opções

| Flag | Descrição |
|------|-----------|
| `--resume` | Continua download interrompido |
| `--dry-run` | Simula sem baixar |
| `--force` | Sobrescreve dados existentes |
| `--delay N` | Segundos entre requisições (padrão: 2) |
| `--no-abstracts` | Não baixa abstracts (mais rápido) |

### Rate limiting

O script implementa delay automático (2s) entre requisições. Se receber erro 429, aumente o delay:

```bash
python fetch_scopus_all_professors.py --delay 5
```

### Arquivos gerados

```
data/scopus/raw/
├── professor-id_author.json    # Dados do autor
├── professor-id_pubs.json      # Publicações
└── ...
```

## Passo 3: Remover Duplicatas

```bash
python deduplicate_publications.py
```

Remove publicações duplicadas (baseado em DOI/EID/título) entre professores que coautoraram artigos.

### Arquivos gerados

```
data/publications/
├── index.json          # Índice de publicações
└── by_eid/             # Publicações individuais
    └── *.json
```

## Passo 4: Integrar aos Perfis

```bash
python merge_scopus_into_profiles.py --dry-run  # Simular primeiro
python merge_scopus_into_profiles.py            # Executar
```

### Opções

| Flag | Descrição |
|------|-----------|
| `--dry-run` | Simula sem salvar |
| `--professor ID` | Processa apenas um professor |

## Atualização Rápida

Se já tem matching configurado:

```bash
python fetch_scopus_all_professors.py --resume
python deduplicate_publications.py
python merge_scopus_into_profiles.py
python generate_statistics.py  # Atualiza estatísticas
hugo --gc --minify             # Rebuild do site
```

## Troubleshooting

### Erro de autenticação (403)
- Verifique se está na rede do ITA ou usando VPN
- A API requer IP institucional autorizado

### Rate limit (429)
- Aumente o delay: `--delay 5`
- O script implementa backoff automático

### Professor não encontrado
- Verifique se o ORCID está correto no perfil
- Use modo LLM: `--mode llm`

### Publicações duplicadas
- Execute `deduplicate_publications.py` novamente
- Verifique se DOIs estão corretos

## Scripts Relacionados

| Script | Descrição | Status |
|--------|-----------|--------|
| `match_professors_to_scopus.py` | Associa profs ao Scopus | ✅ Estável |
| `fetch_scopus_all_professors.py` | Baixa dados | ✅ Estável |
| `deduplicate_publications.py` | Remove duplicatas | ✅ Estável |
| `merge_scopus_into_profiles.py` | Integra aos perfis | ✅ Estável |
| `get_scopus.py` | Módulo auxiliar | ✅ Interno |
| `scopus_busca_autores_ita.py` | Busca autores ITA | ⚠️ Utilitário |

## Segurança

⚠️ **ALERTA**: Os scripts contêm uma chave de API Scopus hardcoded. Para uso seguro:

1. Remova a chave do código
2. Use variável de ambiente:
   ```bash
   export SCOPUS_API_KEY='sua-chave'
   ```
3. Rotacione a chave no painel do Scopus

A chave atual deve ser considerada comprometida se o repositório for público.
