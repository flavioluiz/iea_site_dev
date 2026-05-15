# Pipeline Lattes

Extrai dados dos currículos Lattes dos professores para popular os perfis no site.

## O que é extraído

- Fotos dos professores (otimizadas para web)
- Métricas de citações (Google Scholar, Scopus, WoS)
- Status de bolsista CNPq
- Links para perfis acadêmicos (ORCID, Scholar, etc.)
- Publicações recentes

## Requisitos

```bash
pip install selenium webdriver-manager
```

Você precisa ter o **Google Chrome** instalado.

### Opcional: Para extração com IA

```bash
export SYNTHETIC_API_KEY='sua-chave-aqui'
```

## Fluxo Completo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Download    │ ──► │  2. Extração    │ ──► │  3. Integração  │
│  download_lattes│     │  extract_lattes │     │  update_site    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 lattes_html/*.html    lattes_extracted/      profiles/*.json
                       *_extracted.json
```

## Passo 1: Download dos Currículos

```bash
cd scripts

# Testar com 5 professores primeiro
python download_lattes.py --limit 5

# Baixar todos os professores
python download_lattes.py

# Continuar de onde parou
python download_lattes.py --start-from nome-professor
```

### Processo interativo

O script:
1. Abre o Chrome automaticamente
2. Carrega a página do Lattes
3. **Aguarda você resolver o CAPTCHA**
4. Você pressiona ENTER para continuar
5. Salva o HTML e passa para o próximo

### Comandos durante execução

| Comando | Ação |
|---------|------|
| `ENTER` | Salva e continua |
| `s + ENTER` | Pula este professor |
| `q + ENTER` | Sai do programa |

### Arquivos gerados

```
lattes_data/lattes_html/
├── download_log.json           # Progresso
├── professor-nome.html         # HTML do Lattes
└── professor-nome_metadata.json # Metadados
```

## Passo 2: Extração dos Dados

### Extração básica (sem IA)

```bash
python extract_lattes_improved.py
```

### Extração com IA (melhor qualidade)

```bash
export SYNTHETIC_API_KEY='sua-chave'
python extract_lattes_improved.py
```

### Opções

| Flag | Descrição |
|------|-----------|
| `--skip-existing` | Pula já processados |
| `--force` | Reprocessa todos |
| `--limit N` | Processa apenas N professores |

### Arquivos gerados

```
lattes_data/lattes_extracted/
├── professor-nome_extracted.json  # Dados extraídos
└── ...
```

## Passo 3: Integração no Site

```bash
# Com backup (recomendado)
python update_site_from_lattes.py --backup

# Apenas simular (não salva)
python update_site_from_lattes.py --dry-run

# Processar apenas um professor
python update_site_from_lattes.py --limit 1
```

### O que é atualizado

- `data/professores/profiles/*.json` - Perfis dos professores
- `static/images/professores/*.jpg` - Fotos

## Script Interativo

Para facilitar, use o menu interativo:

```bash
./COMANDOS_RAPIDOS.sh
```

Opções:
1. Extrair dados (sem LLM)
2. Extrair dados (com LLM)
3. Atualizar site
4. Processar tudo
5. Ver status
6. Baixar mais Lattes

## Verificar Resultados

```bash
# Quantos têm publicações?
grep -l '"publicacoes"' data/professores/profiles/*.json | wc -l

# Quantos têm fotos?
grep -l '"foto"' data/professores/profiles/*.json | wc -l

# Ver métricas de um professor
cat data/professores/profiles/nome-professor.json | python -m json.tool
```

## Troubleshooting

### "selenium not found"
```bash
pip install selenium webdriver-manager
```

### "Chrome driver not found"
Instale o Google Chrome.

### Página não carrega
Aguarde mais tempo antes de pressionar ENTER.

### Publicações com títulos estranhos
Use a extração com API Synthetic para melhor parsing.

## Status Atual

⚠️ **Pipeline parcialmente completo**

- 23/52 professores processados (44%)
- Fase 1 concluída
- Fase 2 pendente (29 professores restantes)

Para completar:
```bash
python download_lattes.py        # Baixar restantes
python extract_lattes_improved.py --skip-existing
python update_site_from_lattes.py --backup
```

## Scripts Relacionados

| Script | Descrição | Status |
|--------|-----------|--------|
| `download_lattes.py` | Download interativo | ✅ Estável |
| `extract_lattes_improved.py` | Extração com/sem IA | ✅ Estável |
| `update_site_from_lattes.py` | Integração final | ✅ Estável |
| `extract_lattes_data.py` | Versão anterior | ⚠️ Legado |
| `extract_lattes_metadata.py` | Apenas metadados | ⚠️ Legado |
| `integrate_lattes_data.py` | Versão anterior | ⚠️ Legado |

> **Nota:** Use `extract_lattes_improved.py` e `update_site_from_lattes.py`. Os scripts marcados como "Legado" foram substituídos mas mantidos para referência.
