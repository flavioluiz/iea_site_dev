# Checklist de ativação do piloto

O código está publicado em um commit-raiz limpo e passou pela CI. As pendências abaixo pertencem às contas e ao aceite operacional.

## 1. Ação urgente de segurança

- [ ] Revogar a antiga chave Scopus que apareceu no histórico e emitir outra somente quando o runner privado estiver pronto.
- [x] Copiar as branches antigas para o backup privado `flavioluiz/iea_site_dev_history_private` e conferir os SHAs.
- [x] Substituir `main` por um único commit-raiz com a árvore validada e remover a branch remota antiga.
- [ ] Eliminar a referência retida pelo PR nº 1 antes de tornar o repositório público: recriar o repositório no mesmo endereço ou solicitar a purga ao suporte do GitHub.
- [ ] Avisar colaboradores para recarregar clones após a reescrita.
- [ ] Ativar autenticação em dois fatores na conta GitHub e na Cloudflare.

Não reutilize a chave antiga e não coloque a nova neste repositório.

## 2. GitHub Pages do piloto

- [x] Criar o repositório público `flavioluiz/iea_site` com branch `main`.
- [x] Em **Settings → Pages**, escolher **Deploy from a branch**, `main` e `/ (root)`.
- [ ] Criar um token fino limitado a esse repositório, com `Contents: Read and write`.
- [x] Criar no repositório fonte o environment `github-pages-production`.
- [ ] Gravar nele o secret `PAGES_DEPLOY_TOKEN`.
- [ ] Executar o workflow **Deploy pilot site** e conferir <https://flavioluiz.github.io/iea_site/>.

Detalhes: [GitHub Pages](github-pages.md).

## 3. Login GitHub do CMS na Cloudflare

- [x] Criar conta gratuita Cloudflare e escolher o subdomínio `flavioluiz.workers.dev`.
- [x] Criar um GitHub OAuth App com callback exato do Worker.
- [x] Configurar `flavioluiz` como subdomínio `workers.dev` em `wrangler.toml` e `static/admin/config.yml`.
- [x] Gravar `GITHUB_OAUTH_ID` e `GITHUB_OAUTH_SECRET` como secrets criptografados do Worker e rotacionar o secret usado durante a configuração.
- [x] Publicar `iea-decap-oauth` em `workers.dev` e testar `/health`.
- [ ] Cadastrar na allowlist todos os nomes de usuário GitHub autorizados.
- [x] Criar o projeto Direct Upload `iea-site-previews` no Cloudflare Pages.
- [x] Criar o environment `cloudflare-pages-preview` no GitHub, com `CLOUDFLARE_ACCOUNT_ID` e um `CLOUDFLARE_API_TOKEN` limitado ao Pages.
- [x] Publicar e validar a prévia isolada do PR nº 2 em `pr-2.iea-site-previews.pages.dev`.

Detalhes: [Cloudflare OAuth](cloudflare-oauth.md) e [prévias isoladas](github-pages.md#prévias-isoladas-de-pull-requests-externos).

## 4. Governança do repositório fonte

- [ ] Manter `iea_site_dev` público para Open Authoring.
- [ ] Definir pelo menos dois publicadores/contas de recuperação.
- [x] Criar o ruleset de `main`, com PR, histórico linear, cinco checks obrigatórios, bloqueio de force-push/exclusão e merge por squash.
- [ ] Ativar secret scanning e push protection assim que o repositório se tornar público; o recurso não está disponível neste repositório privado no plano atual.
- [ ] Autorizar explicitamente a opção combinada “Actions criar e aprovar PRs” ou configurar uma credencial/GitHub App restrita apenas às automações confiáveis.
- [x] Criar o label `bulk-reviewed`.
- [ ] Confirmar política de fotos, e-mails e campos Scopus publicáveis.

Detalhes: [governança GitHub](github-governance.md).

## 5. Gates que não devem ser contornados

- Biblioteca: consultar API/OAI-PMH/exportação e só definir `LIBRARY_AUTOMATION_ENABLED=true` após um dry run externo bem-sucedido.
- Scopus: criar `iea_data_automation` privado e registrar o runner exclusivamente nele. Nunca associe o runner institucional ao repositório público.
- Domínio oficial: solicitar à TI/DNS somente quando o piloto estiver aprovado; o CMS não precisa esperar por isso.
