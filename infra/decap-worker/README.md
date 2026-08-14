# Worker OAuth do Decap CMS

Worker sem banco de dados usado somente para autenticar o painel editorial no GitHub. Ele valida origem, login autorizado, `state` assinado e PKCE; não persiste conteúdo nem tokens.

Não coloque credenciais neste diretório. Para desenvolvimento local, copie `.dev.vars.example` para `.dev.vars` (ignorado pelo Git) e use credenciais de um OAuth App exclusivo de teste.

Comandos:

```bash
npm ci
npm test
npm run dev
```

O procedimento de cadastro, configuração de secrets e implantação está em `docs/operations/cloudflare-oauth.md`.
