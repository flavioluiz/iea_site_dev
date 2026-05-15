# 🚀 Deploy do PG-EAM para GitHub Pages

Este documento explica como fazer deploy do site PG-EAM no GitHub Pages.

## 📦 Arquitetura dos Repositórios

Este projeto utiliza **dois repositórios** separados:

| Repositório | Conteúdo | URL |
|-------------|----------|-----|
| **pgeam_dev** (este) | Código fonte Hugo, templates, dados | https://github.com/flavioluiz/pgeam_dev |
| **pgeam** | Site estático gerado (deploy) | https://github.com/flavioluiz/pgeam |

- **URL de Produção**: https://flavioluiz.github.io/pgeam/

## 📦 Estrutura de Deploy

- **Pasta `deploy/`**: Gerada localmente, contém os arquivos estáticos prontos para publicação
- **Tamanho**: ~319 MB (não versionada neste repo)

## 🎯 Deploy Rápido (Primeira Vez)

### 1. Criar Repositório no GitHub

```bash
# Acesse: https://github.com/new
# Nome do repositório: pgeam
# Deixe como público (necessário para GitHub Pages gratuito)
```

### 2. Fazer Deploy

```bash
cd deploy/

# Adicionar remote (apenas primeira vez)
git remote add origin https://github.com/flavioluiz/pgeam.git

# Commit e push
git add .
git commit -m "Initial deploy: PG-EAM website"
git branch -M main
git push -u origin main
```

### 3. Ativar GitHub Pages

1. Acesse: https://github.com/flavioluiz/pgeam/settings/pages
2. Em **Source**, selecione: `Deploy from a branch`
3. Em **Branch**, selecione: `main` e `/ (root)`
4. Clique em **Save**
5. Aguarde ~2-5 minutos

✅ Site estará disponível em: https://flavioluiz.github.io/pgeam/

## 🔄 Atualizações Futuras

### Opção 1: Script Automatizado (Recomendado)

```bash
./scripts/deploy.sh
```

O script irá:
1. Limpar a pasta deploy anterior
2. Reconstruir o site com configurações de produção
3. Criar arquivos necessários (.nojekyll, index.html, etc.)
4. Fazer commit das alterações
5. Perguntar se deseja fazer push

### Opção 2: Manual

```bash
# 1. Limpar deploy anterior
rm -rf deploy/*
rm -rf deploy/.nojekyll

# 2. Reconstruir site
hugo --buildFuture --environment production --destination deploy

# 3. Criar arquivo .nojekyll
touch deploy/.nojekyll

# 4. Criar index.html de redirecionamento
cat > deploy/index.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=/pgeam/pt/">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecionando...</title>
    <link rel="canonical" href="/pgeam/pt/">
</head>
<body>
    <p>Redirecionando para <a href="/pgeam/pt/">PG-EAM</a>...</p>
    <script>window.location.href = "/pgeam/pt/";</script>
</body>
</html>
EOF

# 5. Commit e push
cd deploy/
git add .
git commit -m "Update site - $(date +%Y-%m-%d)"
git push
```

## ⚙️ Configurações Importantes

### Base URL
O site está configurado para: `https://flavioluiz.github.io/pgeam/`

**Arquivo:** `config/_default/config.production.yaml`
```yaml
baseURL: "https://flavioluiz.github.io/pgeam/"
buildFuture: true
```

### Arquivo .nojekyll
**Essencial!** Este arquivo evita que o GitHub Pages processe o site com Jekyll.

### Redirecionamento Raiz
O arquivo `deploy/index.html` redireciona automaticamente de `/` para `/pt/` (idioma padrão).

## 📁 Estrutura da Pasta Deploy

```
deploy/
├── .git/              # Repositório Git separado
├── .nojekyll          # Desabilita Jekyll no GitHub Pages
├── .gitignore         # Git ignore (vazio para deploy)
├── index.html         # Redireciona para /pt/
├── README.md          # Documentação do deploy
├── pt/                # Site em português
│   ├── index.html
│   ├── publicacoes/   # ~2600 páginas de publicações
│   ├── professores/   # ~54 páginas de professores
│   └── ...
├── en/                # Site em inglês
│   └── ...
└── production/        # Assets de produção
    ├── images/
    ├── js/
    └── ...
```

## 🐛 Troubleshooting

### Site não carrega após deploy
- Aguarde 2-5 minutos para propagação
- Verifique GitHub Actions: https://github.com/flavioluiz/pgeam/actions
- Limpe cache do navegador (Ctrl+Shift+R ou Cmd+Shift+R)

### Links quebrados
- Verifique se `baseURL` está correto: `https://flavioluiz.github.io/pgeam/`
- Confirme que usou `--environment production` no build
- Verifique se o `.nojekyll` existe

### Erro 404 nas páginas
- Confirme que GitHub Pages está ativado
- Verifique se a branch `main` está correta
- Verifique se a source está configurada para `/ (root)`

### Site mostra código HTML
- Verifique se `.nojekyll` existe na raiz
- Pode ser necessário aguardar alguns minutos

## 📊 Estatísticas do Site

- **Páginas PT**: 2.717
- **Páginas EN**: 2.717
- **Publicações**: ~2.600 páginas individuais
- **Professores**: ~54 perfis
- **Tamanho Total**: ~319 MB
- **Build Time**: ~5 segundos

## 🔐 Domínio Customizado (Opcional)

Para usar um domínio como `pgeam.ita.br`:

1. Criar arquivo `CNAME` em `deploy/`:
   ```bash
   echo "pgeam.ita.br" > deploy/CNAME
   ```

2. Configurar DNS do domínio:
   ```
   CNAME: pgeam.ita.br -> flavioluiz.github.io
   ```

3. Aguardar propagação DNS (pode levar até 48h)

4. Atualizar `baseURL` para o novo domínio:
   ```yaml
   baseURL: "https://pgeam.ita.br/"
   ```

## 📝 Notas Importantes

- ⚠️ **NÃO edite arquivos em `deploy/` diretamente**
- Todas as mudanças devem ser feitas no código-fonte Hugo
- A pasta `deploy/` é regenerada a cada build
- O repositório `deploy/` é **separado** do repositório principal
- GitHub Pages gratuito requer repositório público
- Limite de ~1GB para sites no GitHub Pages

## 🆘 Precisa de Ajuda?

1. Verifique os logs de build: `hugo --buildFuture --environment production --verbose`
2. Confira as Actions do GitHub: https://github.com/flavioluiz/pgeam/actions
3. Leia a documentação do Hugo: https://gohugo.io/hosting-and-deployment/hosting-on-github/
4. Consulte o README em `deploy/README.md`

---

**Última atualização:** 2025-12-06
