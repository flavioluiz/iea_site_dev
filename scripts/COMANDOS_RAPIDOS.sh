#!/bin/bash
# Comandos Rápidos - Atualização do Site PGEAM
# Execute: chmod +x COMANDOS_RAPIDOS.sh

echo "════════════════════════════════════════════════════════"
echo "  🚀 Atualização do Site PGEAM - Comandos Rápidos"
echo "════════════════════════════════════════════════════════"
echo ""

# Vai para o diretório scripts
cd "$(dirname "$0")"

# Função para perguntar confirmação
confirm() {
    read -p "$1 (s/N): " response
    case "$response" in
        [sS]|[sS][iI][mM]) return 0 ;;
        *) return 1 ;;
    esac
}

# Menu
echo "Escolha uma opção:"
echo ""
echo "1) Extrair dados dos 22 professores restantes (rápido, sem LLM)"
echo "2) Extrair com LLM Synthetic (melhor qualidade)"
echo "3) Atualizar site com dados extraídos"
echo "4) Processar tudo (extrair + atualizar)"
echo "5) Ver status atual"
echo "6) Baixar mais Lattes HTMLs"
echo "0) Sair"
echo ""
read -p "Opção: " opcao

case $opcao in
    1)
        echo ""
        echo "📊 Extraindo dados dos Lattes (sem LLM)..."
        echo "⏭️  Pulando automaticamente arquivos já extraídos..."
        python3 extract_lattes_improved.py --skip-existing
        echo ""
        echo "✅ Extração completa!"
        echo "➡️  Execute a opção 3 para atualizar o site"
        ;;

    2)
        echo ""
        if [ -z "$SYNTHETIC_API_KEY" ]; then
            echo "⚠️  SYNTHETIC_API_KEY não definida!"
            echo ""
            read -p "Cole sua chave API: " api_key
            export SYNTHETIC_API_KEY="$api_key"
        fi
        echo "📊 Extraindo dados com LLM Synthetic (melhor qualidade)..."
        echo "⏭️  Pulando automaticamente arquivos já extraídos..."
        python3 extract_lattes_improved.py --skip-existing
        echo ""
        echo "✅ Extração completa com LLM!"
        echo "➡️  Execute a opção 3 para atualizar o site"
        ;;

    3)
        echo ""
        if confirm "Fazer backup dos perfis antes de atualizar?"; then
            echo "💾 Atualizando site COM backup..."
            python3 update_site_from_lattes.py --backup
        else
            echo "⚡ Atualizando site SEM backup..."
            python3 update_site_from_lattes.py
        fi
        echo ""
        echo "✅ Site atualizado!"
        echo "➡️  Execute: cd .. && hugo server -D"
        echo "   E abra: http://localhost:1313/pt/professores/"
        ;;

    4)
        echo ""
        echo "🚀 Processamento completo..."
        echo ""

        # Extração
        if [ -z "$SYNTHETIC_API_KEY" ]; then
            echo "📊 Fase 1: Extraindo dados (sem LLM)..."
            python3 extract_lattes_improved.py --skip-existing
        else
            echo "📊 Fase 1: Extraindo dados (com LLM)..."
            python3 extract_lattes_improved.py --skip-existing
        fi

        echo ""
        echo "✓ Extração completa"
        echo ""

        # Atualização
        echo "📝 Fase 2: Atualizando site..."
        python3 update_site_from_lattes.py --backup

        echo ""
        echo "✅ Tudo pronto!"
        echo ""
        echo "📊 Ver estatísticas:"
        echo "   grep -c '\"publicacoes\"' ../data/professores/profiles/*.json"
        echo ""
        echo "🌐 Ver no site:"
        echo "   cd .. && hugo server -D"
        echo "   Abra: http://localhost:1313/pt/professores/"
        ;;

    5)
        echo ""
        echo "📊 STATUS ATUAL"
        echo "════════════════════════════════════════════════════════"
        echo ""

        # Conta HTMLs baixados
        html_count=$(ls -1 ../../lattes_data/lattes_html/*.html 2>/dev/null | wc -l | tr -d ' ')
        echo "📥 Lattes baixados: $html_count/52"

        # Conta extraídos
        extracted_count=$(ls -1 ../../lattes_data/lattes_extracted/*_extracted.json 2>/dev/null | wc -l | tr -d ' ')
        echo "📊 Dados extraídos: $extracted_count"

        # Conta com publicações
        pubs_count=$(grep -l '"publicacoes"' ../data/professores/profiles/*.json 2>/dev/null | wc -l | tr -d ' ')
        echo "📚 Com publicações: $pubs_count/52"

        # Conta com fotos
        photos_count=$(ls -1 ../static/images/professores/*.jpg 2>/dev/null | wc -l | tr -d ' ')
        echo "📸 Fotos otimizadas: $photos_count"

        # Conta bolsistas CNPq
        cnpq_count=$(grep -c '"bolsista_cnpq": "Sim' ../data/professores/profiles/*.json 2>/dev/null)
        echo "🏆 Bolsistas CNPq: $cnpq_count"

        echo ""
        echo "════════════════════════════════════════════════════════"

        # Mostra alguns detalhes
        if [ "$pubs_count" -gt 0 ]; then
            echo ""
            echo "Professores com mais publicações:"
            for f in ../data/professores/profiles/*.json; do
                python3 -c "
import json, sys
try:
    p = json.load(open('$f'))
    pubs = len(p.get('publicacoes', []))
    if pubs > 0:
        print(f'{p[\"nome\"]}: {pubs} artigos, h-index={p[\"metrics\"][\"h_index\"]}')
except:
    pass
" 2>/dev/null
            done | sort -t: -k2 -rn | head -5
        fi
        ;;

    6)
        echo ""
        echo "📥 Baixando mais Lattes..."
        echo "⚠️  Isso abrirá o Chrome e você precisará resolver captchas"
        echo ""
        if confirm "Continuar?"; then
            python3 download_lattes.py
        fi
        ;;

    0)
        echo "Saindo..."
        exit 0
        ;;

    *)
        echo "Opção inválida!"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════"
