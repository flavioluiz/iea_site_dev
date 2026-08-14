# Pipeline Biblioteca/BDITA

O workflow `Update Library data` coleta metadados em staging, testa o parser com fixtures, associa orientadores conservadoramente, aplica limite de queda de 5% e abre pull request. Indisponibilidade ou mudança de HTML preserva a última versão boa e abre/atualiza uma issue operacional.

## Gate antes de habilitar a agenda

O endpoint legado da BDITA não respondeu ao teste externo de implantação. Consulte a Biblioteca nesta ordem:

1. API/exportação documentada;
2. OAI-PMH;
3. exportação periódica CSV/JSON/XML;
4. HTML legado, somente se autorizado e estável.

Rode manualmente o workflow com `dry_run: true`. Somente após acesso externo, formato e termos confirmados, crie a variável de repositório:

```text
LIBRARY_AUTOMATION_ENABLED=true
```

Sem essa variável, a agenda semanal fica deliberadamente inativa; execuções manuais continuam disponíveis.

Se a Biblioteca fornecer URLs diferentes, cadastre variáveis de ambiente/runner `BDITA_TESES_URL`, `BDITA_TG_AERO_URL` e `BDITA_TG_ESP_URL` sem alterar o parser às cegas.

## Correspondência de orientadores

O pipeline reaproveita correspondências previamente aprovadas, nomes completos exatos de pessoas ativas e `data/pessoal/aliases_biblioteca.json`. Ele não usa fuzzy matching para adivinhar. Nomes sem correspondência aparecem no relatório; um editor acrescenta o alias pelo CMS e reexecuta.

## Teste local sem rede

```bash
python -m pip install -r scripts/requirements-library.txt
python -m unittest discover -s scripts/library/tests -v
```

O coletor não baixa PDFs. Os dados derivados ficam em `data/generated/biblioteca/`; as páginas Hugo são Content Adapters, sem milhares de Markdown gerados.
