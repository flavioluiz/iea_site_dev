# Ativar o login GitHub do Decap na Cloudflare

O Worker faz somente o login: não hospeda conteúdo, não usa banco de dados e não entrega permissão de publicação. A allowlist contém nomes de usuário GitHub específicos; pessoas autorizadas sem acesso ao repositório trabalham em fork e abrem pull request.

## 1. Criar a conta e descobrir o endereço do Worker

1. Crie uma conta em <https://dash.cloudflare.com/sign-up> e ative MFA.
2. Abra **Workers & Pages** e defina o subdomínio gratuito `workers.dev` da conta.
3. Escolha um endereço final, por exemplo:

```text
https://iea-decap-oauth.SEU-SUBDOMINIO.workers.dev
```

Usar `workers.dev` não exige registrar `aer.ita.br` na Cloudflare nem alterar o DNS do ITA.

## 2. Criar o GitHub OAuth App

Na conta que será proprietária da integração, abra **Settings → Developer settings → OAuth Apps → New OAuth App** e preencha:

```text
Application name: IEA/ITA CMS — piloto
Homepage URL: https://flavioluiz.github.io/iea_site/admin/
Authorization callback URL: https://iea-decap-oauth.SEU-SUBDOMINIO.workers.dev/callback
```

O callback precisa ser idêntico, inclusive `https`, nome e `/callback`. Copie o Client ID e gere um Client Secret. O secret será visto uma vez e deve ir apenas para o armazenamento de secrets do Worker.

## 3. Ajustar os arquivos públicos

Substitua `SUBDOMINIO-CLOUDFLARE` em:

- `infra/decap-worker/wrangler.toml`, no `OAUTH_CALLBACK_URL`;
- `static/admin/config.yml`, no `backend.base_url`.

No `wrangler.toml`:

```toml
ALLOWED_ORIGINS = "https://flavioluiz.github.io,http://localhost:1313"
ALLOWED_GITHUB_USERS = "flavioluiz,outro-usuario-autorizado"
```

Origins não contêm caminho. Usuários são logins GitHub, separados por vírgula e de preferência em minúsculas. Adicionar alguém à lista não o torna publicador nem colaborador direto do repositório.

Não autorize `iea-site-previews.pages.dev` nem seus subdomínios no Worker. A separação de origem impede que HTML ainda não aprovado tenha acesso à sessão do editor.

## 4. Testar e publicar

Na pasta `infra/decap-worker`:

```bash
npm ci
npm test
npx wrangler login
npx wrangler secret put GITHUB_OAUTH_ID
npx wrangler secret put GITHUB_OAUTH_SECRET
npx wrangler deploy
```

Cole cada valor somente quando o Wrangler solicitar. Depois:

```bash
curl https://iea-decap-oauth.SEU-SUBDOMINIO.workers.dev/health
```

A resposta deve indicar funcionamento sem mostrar configuração ou credenciais. Abra `/admin/` em janela anônima e teste: usuário permitido, usuário fora da lista, cancelamento no GitHub e retorno após mais de dez minutos.

## Autorizar ou retirar uma pessoa

1. Confirme o login exato na URL do perfil GitHub da pessoa.
2. Edite somente `ALLOWED_GITHUB_USERS`.
3. Rode testes e `npx wrangler deploy`.
4. Para retirada, remova o login e publique novamente. Autorizações OAuth já concedidas também podem ser revogadas no GitHub.

## Rotacionar o Client Secret

1. No OAuth App, gere um novo secret sem apagar imediatamente o anterior.
2. Execute `npx wrangler secret put GITHUB_OAUTH_SECRET` e publique/teste.
3. Apague o secret anterior no GitHub.
4. Registre data e responsável, sem copiar o valor para o registro.

## Migração para o domínio oficial

Quando `https://www.aer.ita.br/` estiver pronto:

1. altere Homepage URL do OAuth App para `https://www.aer.ita.br/admin/`; o callback do Worker pode continuar igual;
2. use temporariamente `ALLOWED_ORIGINS = "https://flavioluiz.github.io,https://www.aer.ita.br"`;
3. altere em `static/admin/config.yml` `site_url`, `display_url` e `backend.site_domain` para o domínio oficial;
4. publique, teste e depois retire `https://flavioluiz.github.io` da allowlist.

Se a instituição quiser um domínio próprio também para o Worker, crie um Custom Domain na Cloudflare e cadastre exatamente o novo callback no OAuth App antes de trocar.
