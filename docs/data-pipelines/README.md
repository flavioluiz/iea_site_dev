# Pipelines de Dados

Os pipelines de dados são scripts Python que extraem informações de fontes externas e integram aos dados do site.

## Visão Geral

| Pipeline | Fonte | O que extrai | Frequência sugerida |
|----------|-------|--------------|---------------------|
| [Lattes](lattes.md) | Plataforma Lattes | Fotos, métricas, publicações, CNPq | Semestral |
| [Scopus](scopus.md) | Elsevier Scopus | Publicações, citações, h-index | Semestral |
| [Teses](theses.md) | BDITA | Teses e dissertações | Semestral |
| [Estatísticas](statistics.md) | Dados locais | Métricas agregadas | Após outros pipelines |

## Fluxo de Dados

```
Lattes  ─────►  data/professores/profiles/*.json  ─────►
                        ▲                              │
Scopus  ────────────────┘                              │
                                                       ▼
                                                   HUGO BUILD
                                                       │
BDITA   ─────►  data/teses/                ────────────┘
```

## Dependências

```bash
pip install requests beautifulsoup4 pybliometrics selenium webdriver-manager
```

## Status Atual

| Pipeline | Status | Observações |
|----------|--------|-------------|
| Lattes | ⚠️ **Parcial** | 23/52 professores. Requer CAPTCHA manual |
| Scopus | ✅ Funcional | Requer rede ITA/VPN |
| Teses | ✅ Funcional | 1.874 registros |
| Estatísticas | ✅ Funcional | Depende dos outros |

## Ordem de Execução Recomendada

1. **Lattes** - Atualiza fotos, métricas, publicações
2. **Scopus** - Complementa publicações e métricas
3. **Teses** - Atualiza banco de teses
4. **Estatísticas** - Recalcula métricas agregadas

## Alertas Importantes

### ⚠️ Chave API Scopus

Os scripts de Scopus contêm uma chave de API hardcoded. Para uso em produção, mova para variável de ambiente:

```bash
export SCOPUS_API_KEY='sua-chave-aqui'
```

### ⚠️ Rede do ITA

O pipeline Scopus requer acesso à rede institucional do ITA (ou VPN). Sem isso, as requisições à API falharão.

### ⚠️ CAPTCHAs do Lattes

O download de currículos Lattes requer resolução manual de CAPTCHAs. Não é possível automatizar completamente.
