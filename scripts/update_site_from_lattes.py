#!/usr/bin/env python3
"""
Atualiza os dados do site a partir das extrações do Lattes
Integra fotos, métricas, CNPq, links e publicações nos perfis JSON
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def update_profile_from_extraction(extracted_file, profile_file):
    """Atualiza perfil do professor com dados extraídos do Lattes"""

    # Carrega dados extraídos
    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted = json.load(f)

    # Carrega perfil existente
    with open(profile_file, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    # 1. Atualiza foto
    if extracted.get('foto'):
        profile['foto'] = extracted['foto']

    # 2. Atualiza ORCID
    if extracted.get('orcid'):
        profile['links']['orcid'] = extracted['orcid']

    # 3. Atualiza links de plataformas acadêmicas
    citations = extracted.get('citations', {})

    # Web of Science
    if citations.get('web_of_science', {}).get('link'):
        profile['links']['web_of_science'] = citations['web_of_science']['link']

    # Google Scholar
    if citations.get('google_scholar', {}).get('link'):
        profile['links']['google_scholar'] = citations['google_scholar']['link']

    # 4. Atualiza métricas - usa valores MÁXIMOS entre todas as fontes
    wos = citations.get('web_of_science', {})
    scopus = citations.get('scopus', {})
    scholar = citations.get('google_scholar', {})
    scielo = citations.get('scielo', {})

    # H-index: maior valor entre WoS e Scopus
    h_indices = [
        wos.get('h_index', 0),
        scopus.get('h_index', 0)
    ]
    if any(h_indices):
        profile['metrics']['h_index'] = max(h_indices)

    # Citações: maior valor entre todas as fontes
    citations_values = [
        wos.get('citations', 0),
        scopus.get('citations', 0),
        scholar.get('citations', 0),
        scielo.get('citations', 0)
    ]
    if any(citations_values):
        profile['metrics']['citacoes'] = max(citations_values)

    # Artigos: maior valor entre todas as fontes
    works_values = [
        wos.get('works', 0),
        scopus.get('works', 0),
        scholar.get('works', 0),
        scielo.get('works', 0)
    ]
    if any(works_values):
        profile['metrics']['artigos'] = max(works_values)

    # Data de atualização
    profile['metrics']['ultima_atualizacao'] = datetime.now().strftime("%Y-%m-%d")

    # 5. Atualiza status CNPq
    profile['bolsista_cnpq'] = extracted.get('bolsista_produtividade', 'Não')

    # 6. Atualiza publicações (artigos de periódicos)
    publications = extracted.get('publications', {})
    artigos = publications.get('artigos_periodicos', [])

    if artigos:
        # Converte artigos para formato do site
        profile['publicacoes'] = []

        for artigo in artigos:
            # Monta estrutura de publicação
            pub = {
                'tipo': 'article',
                'title': artigo.get('titulo', ''),
                'year': artigo.get('ano', 0),
                'doi': artigo.get('doi', ''),
                'abstract': '',  # Não disponível no Lattes
                'journal': artigo.get('periodico', ''),
                'volume': artigo.get('volume', ''),
                'pages': artigo.get('paginas', ''),
                'citations': max(
                    artigo.get('citations_wos', 0),
                    artigo.get('citations_scopus', 0)
                ),
                'fwci': 0,  # Não disponível no Lattes, virá do Scopus depois
                'scopus_id': '',
                'source': 'lattes'
            }

            # Adiciona autores se disponível
            if 'autores' in artigo:
                pub['authors'] = artigo['autores']
            elif 'full_text' in artigo:
                # Tenta extrair autores do texto completo
                # Formato: AUTOR1 ; AUTOR2 ; ... . Título ...
                text = artigo['full_text']
                if ' . ' in text:
                    authors_part = text.split(' . ')[0]
                    authors = [a.strip() for a in authors_part.split(';')]
                    pub['authors'] = authors
                else:
                    pub['authors'] = []
            else:
                pub['authors'] = []

            profile['publicacoes'].append(pub)

        # Ordena por ano (mais recentes primeiro)
        profile['publicacoes'].sort(key=lambda x: x.get('year', 0), reverse=True)

    return profile


def main():
    parser = argparse.ArgumentParser(
        description='Atualiza dados do site a partir das extrações do Lattes'
    )

    parser.add_argument('--extracted-dir', type=str,
                        default='../../lattes_data/lattes_extracted',
                        help='Diretório com dados extraídos (_extracted.json)')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Diretório com perfis JSON do site')

    parser.add_argument('--backup', action='store_true',
                        help='Fazer backup dos perfis antes de atualizar')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de perfis (para teste)')

    parser.add_argument('--dry-run', action='store_true',
                        help='Simula atualização sem salvar alterações')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    extracted_dir = (script_dir / args.extracted_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    # Encontra todos os arquivos extraídos
    extracted_files = sorted(extracted_dir.glob('*_extracted.json'))

    if args.limit:
        extracted_files = extracted_files[:args.limit]

    print(f"\n{'='*80}")
    print(f"ATUALIZAÇÃO DO SITE COM DADOS DO LATTES")
    print(f"{'='*80}")
    print(f"Arquivos extraídos: {len(extracted_files)}")
    print(f"Diretório perfis: {profiles_dir}")
    print(f"Fazer backup: {args.backup}")
    print(f"Modo simulação: {args.dry_run}")
    print(f"{'='*80}\n")

    updated = 0
    errors = []

    for extracted_file in extracted_files:
        # Obtém ID do professor do nome do arquivo
        professor_id = extracted_file.stem.replace('_extracted', '')
        profile_file = profiles_dir / f"{professor_id}.json"

        if not profile_file.exists():
            print(f"✗ Perfil não encontrado: {professor_id}")
            errors.append((professor_id, "Profile not found"))
            continue

        print(f"📝 Atualizando: {professor_id}")

        try:
            # Backup se solicitado
            if args.backup and not args.dry_run:
                # Salva backup fora do diretório data/ para não ser processado pelo Hugo
                backup_dir = script_dir.parent / 'backups' / 'profiles'
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_file = backup_dir / f"{professor_id}.json.backup"
                with open(profile_file, 'r') as f:
                    backup_data = f.read()
                with open(backup_file, 'w') as f:
                    f.write(backup_data)
                print(f"  💾 Backup salvo em backups/profiles/")

            # Atualiza perfil
            updated_profile = update_profile_from_extraction(extracted_file, profile_file)

            # Salva perfil atualizado (se não for dry-run)
            if not args.dry_run:
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_profile, f, indent=2, ensure_ascii=False)

            # Mostra resumo
            print(f"  ✓ {'Simulado' if args.dry_run else 'Atualizado'} com sucesso")
            print(f"    📊 Métricas:")
            print(f"       - H-index: {updated_profile['metrics']['h_index']}")
            print(f"       - Citações: {updated_profile['metrics']['citacoes']}")
            print(f"       - Trabalhos: {updated_profile['metrics']['artigos']}")
            print(f"    📚 Publicações: {len(updated_profile.get('publicacoes', []))}")
            print(f"    🏆 Bolsista CNPq: {updated_profile.get('bolsista_cnpq', 'Não')}")
            print(f"    🔗 ORCID: {'Sim' if updated_profile['links'].get('orcid') else 'Não'}")
            print(f"    📸 Foto: {'Sim' if updated_profile.get('foto') else 'Não'}")

            updated += 1

        except Exception as e:
            print(f"  ✗ Erro: {e}")
            import traceback
            traceback.print_exc()
            errors.append((professor_id, str(e)))

    # Resumo final
    print(f"\n{'='*80}")
    print(f"RESUMO")
    print(f"{'='*80}")
    print(f"✓ Perfis atualizados: {updated}")
    print(f"✗ Erros: {len(errors)}")

    if errors:
        print(f"\n❌ Erros encontrados:")
        for prof_id, error in errors:
            print(f"  - {prof_id}: {error}")

    if args.dry_run:
        print(f"\n⚠️  MODO SIMULAÇÃO - Nenhuma alteração foi salva")
    else:
        print(f"\n✅ Atualizações salvas nos perfis JSON")
        print(f"   Execute 'hugo server' para ver as mudanças no site")

    print(f"{'='*80}")


if __name__ == '__main__':
    main()
