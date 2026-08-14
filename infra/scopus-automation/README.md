# Automação Scopus isolada

Este diretório é somente um modelo seguro para o repositório privado `iea_data_automation`. Não copie o workflow para `.github/workflows` deste repositório público.

O runner deve ser registrado exclusivamente no repositório privado, usar uma conta de sistema sem privilégios, aceitar somente saída HTTPS necessária e nunca executar eventos de pull request. Os secrets `SCOPUS_API_KEY`, `SCOPUS_INST_TOKEN` e `SITE_BOT_TOKEN` ficam no repositório privado. A saída bruta permanece no diretório temporário do runner e deve ser removida ao final conforme o runbook.

Antes do agendamento, execute duas atualizações assistidas: primeiro com `professor` preenchido e `dry_run: true`; depois o conjunto completo ainda em `dry_run`. Só então habilite a agenda e a abertura de PR.
