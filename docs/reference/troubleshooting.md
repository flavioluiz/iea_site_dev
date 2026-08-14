# Diagnóstico rápido

- Login “conta não autorizada”: confirme login exato em `ALLOWED_GITHUB_USERS` e publique o Worker.
- Callback inválido: OAuth App, `OAUTH_CALLBACK_URL` e URL real precisam coincidir exatamente.
- Link sem `/iea_site/`: faça build com a configuração de produção do piloto e rode `check_links.py`.
- Foto/PDF bloqueado: leia o caminho e motivo no check; não renomeie arquivo para disfarçar formato.
- Biblioteca fora do ar: mantenha `LIBRARY_AUTOMATION_ENABLED` desativado e consulte a Biblioteca.
- Scopus 403: confirme rede/VPN, credencial e institutional token apenas no runner privado.
- Deploy do piloto não inicia: confira o `CI`, o environment `github-pages-production`, o secret `PAGES_DEPLOY_KEY` e se a deploy key correspondente ainda tem escrita em `flavioluiz/iea_site`.
- Prévia não aparece: confira `cloudflare-pages-preview`, os dois secrets Cloudflare e se o projeto se chama exatamente `iea-site-previews`.
