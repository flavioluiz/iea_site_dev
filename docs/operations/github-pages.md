# GitHub Pages, previews e publicação

## Arquitetura do piloto

O código fonte permanece em `flavioluiz/iea_site_dev`. O HTML gerado é publicado em `flavioluiz/iea_site`, produzindo <https://flavioluiz.github.io/iea_site/>.

O deploy nunca ocorre a partir de um pull request. O workflow `Deploy pilot site` aguarda o CI de `main` terminar com sucesso, recompila com Hugo 0.152.2 verificado por SHA-256 e envia um commit normal ao repositório de saída. A versão anterior permanece disponível no histórico para rollback.

## Configuração inicial

1. Crie <https://github.com/new> com proprietário `flavioluiz`, nome `iea_site`, visibilidade pública e um README para inicializar `main`.
2. Em `iea_site`, abra **Settings → Pages**. Em **Build and deployment**, selecione **Deploy from a branch**, branch `main`, pasta `/ (root)` e salve.
3. Gere uma chave SSH Ed25519 dedicada, sem senha. Em `iea_site`, abra **Settings → Deploy keys**, cadastre apenas a chave pública e marque **Allow write access**. Uma deploy key pertence somente a esse repositório e não concede acesso aos demais repositórios da conta.
4. No repositório fonte, crie em **Settings → Environments** o environment `github-pages-production`.
5. Nele, adicione a chave privada como secret `PAGES_DEPLOY_KEY`. O environment pode exigir aprovação de um publicador. `PAGES_DEPLOY_TOKEN` continua aceito apenas como fallback de migração e, se usado, deve ser um token fino limitado a `flavioluiz/iea_site`, com `Contents: Read and write`.
6. Em **Actions**, execute `CI` manualmente sobre `main`. O workflow `Deploy pilot site` será acionado automaticamente somente quando essa execução terminar com sucesso; ele não possui atalho manual que contorne o CI.

Não coloque a chave privada ou o token em variável comum, arquivo versionado ou log. Para rotacionar a deploy key, cadastre uma nova chave pública no repositório de saída, substitua `PAGES_DEPLOY_KEY` e só então remova a chave anterior.

## Prévias isoladas de pull requests externos

Não publique HTML ainda não aprovado sob `flavioluiz.github.io`: todos os projetos dessa conta compartilham a mesma origem do navegador e uma prévia maliciosa poderia tentar ler a sessão do CMS. As prévias usam, por isso, um projeto Cloudflare Pages sem acesso às credenciais do editor.

Ativação única:

1. Em **Workers & Pages**, crie um projeto **Direct Upload** chamado exatamente `iea-site-previews`.
2. Crie um API Token restrito à conta usada, com somente a permissão necessária para editar Cloudflare Pages, e copie também o Account ID.
3. No repositório fonte, crie o environment `cloudflare-pages-preview`.
4. Grave nele os secrets `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID`.
5. Não acrescente `*.pages.dev` a `ALLOWED_ORIGINS` do Worker OAuth.

O CI renderiza o PR sem secrets. Depois dos checks, um workflow confiável baixa somente o artefato estático, recusa Workers/Functions embutidos e publica em:

```text
https://pr-NUMERO.iea-site-previews.pages.dev/
```

O código do PR nunca é executado no job que possui o token. O workflow comenta o endereço no pull request. Ao fechar o PR, o alias passa a mostrar somente “prévia encerrada”; versões imutáveis antigas podem ser removidas depois pela tela de deployments do Pages conforme a política de retenção. O Cloudflare Pages envia `X-Robots-Tag: noindex` nas prévias.

## Rollback

1. No repositório fonte, reverta o pull request problemático pelo botão **Revert** e incorpore o novo PR.
2. O CI e o deploy publicam novamente a versão revertida.
3. Em emergência, o repositório `iea_site` mantém commits de cada deploy; um publicador pode republicar o commit anterior, mas depois deve reconciliar a fonte.

## Migração para `www.aer.ita.br`

Há duas opções:

- continuar no GitHub Pages: configurar **Custom domain** como `www.aer.ita.br`, manter `CNAME` no repositório de saída e pedir à TI um CNAME `www` para `flavioluiz.github.io`; depois habilitar HTTPS;
- publicar no host institucional: usar o build com `config/production/config-ita-domain.yaml` e o environment protegido de SFTP já separado.

Em ambos os casos, altere o CMS e o Worker conforme o [runbook Cloudflare](cloudflare-oauth.md). Durante a transição, o Worker pode aceitar os dois origins; retire o piloto da allowlist ao encerrar os testes.

`config/production/config-ita-domain.yaml` mantém `temporary_noindex: true` por segurança. Retire essa opção somente no lançamento oficial, depois de conteúdo, DNS, HTTPS e política de dados aprovados.
