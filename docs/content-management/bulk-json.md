# Edição JSON em massa e uso de IA

Use este caminho somente quando muitos registros precisarem mudar. Edições comuns devem ser feitas pelo formulário do CMS.

1. Abra `data/pessoal/professores.json` no GitHub e escolha **Edit this file**.
2. Copie antes o [modelo mínimo](../modelos/professores.exemplo.json).
3. Se usar IA, peça para preservar todos os campos, IDs e pessoas que não devem mudar; não forneça dados restritos.
4. Confira o diff do GitHub e envie para uma branch/pull request, nunca diretamente para `main`.
5. Leia o artefato **content-diff**: ele lista pessoas adicionadas, removidas, desativadas e campos alterados.
6. Mudanças em mais de 10 pessoas ficam bloqueadas até um mantenedor aplicar o label `bulk-reviewed` após conferência.

Erros de campo, ID, URL, ORCID, departamento ou referência aparecem com o caminho exato no check `validate-data`. Corrija o JSON; não peça para ignorar o check.

Prompt útil para uma IA:

```text
Atualize somente os campos explicitamente informados neste JSON.
Preserve schema_version, IDs, todos os registros não mencionados e todos os
campos desconhecidos para você. Não invente traduções, links, datas ou IDs.
Devolva JSON válido, sem Markdown e sem comentários.
```
