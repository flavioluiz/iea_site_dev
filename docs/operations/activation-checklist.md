# Checklist de ativação do piloto

As mudanças locais estão prontas, mas quatro integrações pertencem às suas contas e precisam ser ativadas fora do repositório.

## 1. Ação urgente de segurança

- [ ] Revogar a antiga chave Scopus que apareceu no histórico e emitir outra somente quando o runner privado estiver pronto.
- [ ] Tratar o histórico com o procedimento institucional; avisar colaboradores para recarregar clones depois da reescrita, se ela for feita.
- [ ] Ativar autenticação em dois fatores na conta GitHub e na Cloudflare.

Não reutilize a chave antiga e não coloque a nova neste repositório.

## 2. GitHub Pages do piloto

- [x] Criar o repositório público `flavioluiz/iea_site` com branch `main`.
- [x] Em **Settings → Pages**, escolher **Deploy from a branch**, `main` e `/ (root)`.
- [ ] Criar um token fino limitado a esse repositório, com `Contents: Read and write`.
- [ ] Criar no repositório fonte o environment `github-pages-production`, com o secret `PAGES_DEPLOY_TOKEN`.
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

Detalhes: [Cloudflare OAuth](cloudflare-oauth.md) e [prévias isoladas](github-pages.md#prévias-isoladas-de-pull-requests-externos).

## 4. Governança do repositório fonte

- [ ] Manter `iea_site_dev` público para Open Authoring.
- [ ] Definir pelo menos dois publicadores/contas de recuperação.
- [ ] Criar o ruleset de `main`, checks obrigatórios e merge por squash.
- [ ] Ativar secret scanning e permitir que Actions criem pull requests.
- [ ] Criar o label `bulk-reviewed`.
- [ ] Confirmar política de fotos, e-mails e campos Scopus publicáveis.

Detalhes: [governança GitHub](github-governance.md).

## 5. Gates que não devem ser contornados

- Biblioteca: consultar API/OAI-PMH/exportação e só definir `LIBRARY_AUTOMATION_ENABLED=true` após um dry run externo bem-sucedido.
- Scopus: criar `iea_data_automation` privado e registrar o runner exclusivamente nele. Nunca associe o runner institucional ao repositório público.
- Domínio oficial: solicitar à TI/DNS somente quando o piloto estiver aprovado; o CMS não precisa esperar por isso.
