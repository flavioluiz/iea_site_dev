# Manutenção

- Conteúdo humano: use o CMS e revise o pull request.
- Dados canônicos: `data/pessoal/professores.json` e demais JSON editoriais.
- Dados gerados: somente pipelines em `data/generated/`; não edite à mão.
- Deploy: workflows de Pages após CI, conforme [runbook](operations/github-pages.md).
- OAuth: teste Worker e faça rotação conforme [runbook](operations/cloudflare-oauth.md).
- Biblioteca/Scopus: preserve staging e thresholds conforme os runbooks próprios.

Mensalmente, confira expiração de tokens, alertas de segurança, workflows agendados e ao menos uma conta de recuperação. Após incidente ou atualização automática, ensaie rollback por revert.
