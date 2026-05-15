# Pipeline Teses (BDITA)

Importa teses e dissertações da Biblioteca Digital do ITA (BDITA) para o site.

## O que é extraído

- Metadados de teses e dissertações
- Títulos, autores, orientadores
- Datas de defesa
- Links para o texto completo

## Requisitos

```bash
pip install requests beautifulsoup4
```

## Fluxo Completo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Scraping    │ ──► │  2. Processar   │ ──► │  3. Estatísticas│
│  scrape_bdita   │     │  generate_thesis│     │  generate_stats │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 tesesdigitais_eam.json  teses/by_id/          statistics.json
                         teses/index.json
                         teses/by_professor.json
```

## Passo 1: Baixar Dados da BDITA

```bash
cd scripts
python scrape_bdita_theses.py
```

### Opções

| Flag | Descrição |
|------|-----------|
| `--limit N` | Limita a N teses (para testes) |
| `--resume` | Continua download interrompido |
| `--output FILE` | Arquivo de saída |

### Arquivo gerado

`data/tesesdigitais_eam.json` - Todas as teses brutas

## Passo 2: Processar e Gerar Páginas

### Modo interativo (recomendado)

```bash
python generate_thesis_pages.py
```

O modo interativo permite verificar e corrigir matches entre orientadores e professores do programa.

### Modo não-interativo

```bash
python generate_thesis_pages.py --no-interactive
# ou
python generate_thesis_pages.py -y
```

Usa matches salvos anteriormente + matches automáticos.

## Modo Interativo

### Tela principal

Mostra todos os orientadores ordenados por quantidade de trabalhos:
- `[M]` - Match manual (você corrigiu)
- `[A]` - Match automático de alta confiança
- `[a]` - Match automático de baixa confiança
- `[ ]` - Sem match

### Comandos disponíveis

| Comando | Descrição |
|---------|-----------|
| `<número>` | Editar match do orientador #número |
| `f <texto>` | Buscar orientador por nome |
| `p` | Ver visão por professor |
| `u` | Ver professores sem orientações |
| `s` | Salvar e gerar páginas |
| `q` | Salvar e sair sem gerar |
| `?` | Listar professores do programa |

### Ao editar um match

| Comando | Descrição |
|---------|-----------|
| `<número>` | Associar ao professor #número |
| `0` | Marcar como não-match (externo) |
| `a` | Aceitar sugestão automática |
| `k` | Manter match atual |
| `?` | Ver lista de professores |

## Arquivos Gerados

```
data/teses/
├── index.json           # Índice leve para busca
├── statistics.json      # Estatísticas agregadas
├── by_professor.json    # Mapeamento orientador→teses
├── manual_matches.json  # Matches manuais (editável)
└── by_id/               # Arquivos individuais
    ├── 61542.json
    └── ...
```

## Editar Matches Manualmente

O arquivo `data/teses/manual_matches.json` pode ser editado diretamente:

```json
{
  "Nome do Orientador": "professor-id",
  "Outro Orientador": null
}
```

Use `null` para orientadores externos que não devem ser associados.

## Passo 3: Atualizar Estatísticas

```bash
python generate_statistics.py
```

Inclui estatísticas de teses no arquivo `data/statistics.json`.

## Verificar Resultados

```bash
# Total de teses
cat data/teses/index.json | python -c "import json,sys; print(len(json.load(sys.stdin)))"

# Teses por tipo
cat data/teses/statistics.json | python -m json.tool
```

## Status Atual

✅ **Pipeline funcional**

- 1.874 teses/dissertações indexadas
- 1.359 dissertações de mestrado
- 515 teses de doutorado
- 220 orientadores mapeados

## Troubleshooting

### Erro de conexão com BDITA
- Verifique sua conexão com a internet
- O servidor da BDITA pode estar temporariamente indisponível

### Match incorreto
1. Execute `python generate_thesis_pages.py`
2. Use `f <nome>` para buscar o orientador
3. Digite o número para editar
4. Corrija o match

### Orientador não encontrado
- Pode ser orientador externo ou aposentado
- Marque com `0` para registrar como não-match

## Scripts Relacionados

| Script | Descrição | Status |
|--------|-----------|--------|
| `scrape_bdita_theses.py` | Web scraping da BDITA | ✅ Estável |
| `generate_thesis_pages.py` | Processamento e matching | ✅ Estável |
| `generate_statistics.py` | Gera estatísticas | ✅ Estável |
