# Deploy para GitHub Pages

## Repositórios

O deploy usa dois repositórios:

| Repositório | Conteúdo |
|-------------|----------|
| `pgeam_dev` | Código fonte Hugo (este repositório) |
| `pgeam` | Site estático gerado |

A pasta `deploy/` é um submódulo Git apontando para o repositório `pgeam`.

## Deploy Automatizado (Recomendado)

```bash
./scripts/deploy.sh
```

O script:
1. Limpa a pasta `deploy/`
2. Executa build com `--environment production` (URLs corretas)
3. Cria arquivo `.nojekyll`
4. Faz commit das alterações
5. Pergunta se deseja fazer push

## Deploy Manual

```bash
# 1. Limpar pasta deploy
rm -rf deploy/*

# 2. Build para produção
hugo --buildFuture --environment production --destination deploy

# 3. Criar arquivo necessário para GitHub Pages
touch deploy/.nojekyll

# 4. Commit e push
cd deploy/
git add .
git commit -m "Update site"
git push
```

## Configuração de Ambiente

O arquivo `config/production/config.yaml` define a URL de produção:

```yaml
baseURL: "https://flavioluiz.github.io/pgeam/"
```

## Verificar Deploy

Após o push, aguarde alguns minutos e acesse:
https://flavioluiz.github.io/pgeam/

## Troubleshooting

### Links quebrados após deploy

Verifique se usou `--environment production`:
```bash
hugo --environment production --destination deploy
```

### CSS/JS não carregam

Verifique se o arquivo `.nojekyll` existe em `deploy/`:
```bash
ls -la deploy/.nojekyll
```

### Alterações não aparecem

1. Verifique se fez push do repositório `deploy/`
2. Aguarde a propagação do GitHub Pages (pode levar alguns minutos)
3. Limpe o cache do navegador

### Erro no submódulo

Se a pasta `deploy/` estiver corrompida:
```bash
rm -rf deploy/
git clone https://github.com/flavioluiz/pgeam.git deploy
```

## GitHub Actions (Opcional)

Para deploy automático via CI/CD, crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy Hugo site

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: 'latest'

      - name: Build
        run: hugo --minify --environment production

      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

> **Nota**: Este workflow não está configurado atualmente. O deploy é feito manualmente via `deploy.sh`.
