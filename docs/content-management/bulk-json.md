# Importação JSON em lote

Use este caminho somente quando muitos registros precisarem mudar. Edições comuns devem ser feitas pelos formulários do CMS.

O importador aceita as coleções `pessoas`, `departamentos`, `laboratorios`, `projetos`, `linhas` e `documentos`. O arquivo de entrada pode ser uma lista JSON ou o objeto coletivo já usado pela coleção, por exemplo `{ "professores": [...] }`.

## Conferir sem gravar

```sh
uv run --with-requirements scripts/requirements-cms.txt \
  python scripts/import_content_batch.py pessoas lote-pessoas.json
```

O relatório informa quantos registros são novos, atualizados ou idênticos. Sem `--apply`, nenhum arquivo é alterado.

## Confirmar a importação

Para criar apenas IDs novos:

```sh
uv run --with-requirements scripts/requirements-cms.txt \
  python scripts/import_content_batch.py pessoas lote-pessoas.json --apply
```

Se o relatório mostrar atualizações intencionais, confira cada ID e confirme explicitamente:

```sh
uv run --with-requirements scripts/requirements-cms.txt \
  python scripts/import_content_batch.py pessoas lote-pessoas.json --update-existing --apply
```

Troque `pessoas` pelo nome da outra coleção quando necessário. O importador preserva registros ausentes do lote, bloqueia IDs duplicados, valida o conjunto completo e nunca remove registros implicitamente. Pessoas e laboratórios são expandidos em fichas individuais para continuarem pesquisáveis e filtráveis no painel.

Depois da importação, confira o diff, crie uma branch/pull request e leia o artefato **content-diff**. Mudanças em mais de dez pessoas ou em mais de cinco laboratórios ficam bloqueadas até um mantenedor aplicar o label `bulk-reviewed` após conferência.

Se usar IA para preparar o lote, não forneça dados restritos e use esta instrução:

```text
Atualize somente os registros e campos explicitamente informados.
Preserve os IDs e todos os campos desconhecidos para você. Não invente
traduções, links, datas ou IDs. Devolva JSON válido, sem Markdown e sem comentários.
```
