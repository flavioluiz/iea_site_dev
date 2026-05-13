#!/bin/bash
# Script para deploy do site PG-EAM no GitHub Pages

set -e  # Sair se houver erro

echo "🚀 Iniciando deploy do PG-EAM para GitHub Pages..."

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Configurações
DEPLOY_DIR="$PROJECT_DIR/deploy"
REMOTE_URL="https://github.com/flavioluiz/pgeam.git"
BRANCH="main"

# 1. Preparar pasta deploy
echo "🧹 Preparando pasta deploy..."

# Se a pasta deploy não existe ou não tem .git, clonar o repositório
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "📥 Clonando repositório de deploy..."
    rm -rf "$DEPLOY_DIR"
    git clone --depth 1 "$REMOTE_URL" "$DEPLOY_DIR" || {
        # Se o clone falhar (repo vazio), criar do zero
        mkdir -p "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
        git init
        git remote add origin "$REMOTE_URL"
        cd "$PROJECT_DIR"
    }
fi

# Limpar conteúdo antigo (mantendo .git)
echo "🗑️  Limpando conteúdo antigo..."
cd "$DEPLOY_DIR"
git rm -rf . 2>/dev/null || true
cd "$PROJECT_DIR"

# 2. Reconstruir site para produção
echo "🔨 Construindo site para produção..."
hugo --gc --minify --buildFuture --environment production --destination "$DEPLOY_DIR"

# 3. Criar arquivos necessários
echo "📝 Criando arquivos de configuração..."
touch "$DEPLOY_DIR/.nojekyll"

cat > "$DEPLOY_DIR/.gitignore" << 'EOF'
# Este repositório contém apenas arquivos estáticos gerados
# Nada deve ser ignorado aqui
EOF

cat > "$DEPLOY_DIR/README.md" << EOF
# PG-EAM Website - GitHub Pages Deploy

Este repositório contém os arquivos estáticos gerados para deploy do site PG-EAM no GitHub Pages.

## 🌐 URL do Site

**Produção:** https://flavioluiz.github.io/pgeam/

## 📦 Conteúdo

Este repositório contém apenas os arquivos HTML, CSS, JavaScript e assets estáticos gerados pelo Hugo.

⚠️ **IMPORTANTE:** Este repositório é gerado automaticamente. Não edite arquivos aqui manualmente.

## 📅 Última atualização

Gerado em: $(date +"%Y-%m-%d %H:%M:%S")

## 📞 Suporte

Para problemas com o conteúdo do site, entre em contato com a equipe do PG-EAM.
EOF

# 4. Fazer commit
echo "💾 Fazendo commit..."
cd "$DEPLOY_DIR"
git add -A
git commit -m "Update site - $(date +%Y-%m-%d\ %H:%M:%S)" || {
    echo "ℹ️  Nada para commitar (site não mudou)"
    exit 0
}

# 5. Perguntar se quer fazer push
echo ""
echo "✅ Site construído e commitado com sucesso!"
echo ""
read -p "Deseja fazer push para GitHub Pages? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Fazendo push para GitHub..."
    git push origin "$BRANCH" --force-with-lease || git push origin "$BRANCH" --force
    echo ""
    echo "✨ Deploy concluído com sucesso!"
    echo "🌐 Site disponível em: https://flavioluiz.github.io/pgeam/"
    echo "⏱️  Aguarde alguns minutos para o GitHub processar o deploy"
else
    echo "⏸️  Push cancelado. Execute 'cd deploy && git push --force' quando estiver pronto."
fi

cd "$PROJECT_DIR"
echo ""
echo "✅ Processo finalizado!"
