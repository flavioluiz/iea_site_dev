#!/usr/bin/env python3
"""
Integra dados extraídos do Lattes com perfis JSON dos professores
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def integrate_data(extracted_file, profile_file):
    """Integrate extracted Lattes data into professor profile"""

    # Load extracted data
    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted = json.load(f)

    # Load existing profile
    with open(profile_file, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    # Update photo
    if extracted.get('foto'):
        profile['foto'] = extracted['foto']

    # Update ORCID
    if extracted.get('orcid'):
        profile['links']['orcid'] = extracted['orcid']

    # Update Web of Science link
    if extracted.get('citations', {}).get('web_of_science', {}).get('link'):
        profile['links']['web_of_science'] = extracted['citations']['web_of_science']['link']

    # Update Scopus link (if we can construct it)
    # Scopus usually doesn't provide direct link in Lattes

    # Update Google Scholar link
    if extracted.get('citations', {}).get('google_scholar', {}).get('link'):
        profile['links']['google_scholar'] = extracted['citations']['google_scholar']['link']

    # Update metrics
    wos = extracted.get('citations', {}).get('web_of_science', {})
    scopus = extracted.get('citations', {}).get('scopus', {})
    scholar = extracted.get('citations', {}).get('google_scholar', {})

    # Use highest h-index available
    h_indices = [wos.get('h_index', 0), scopus.get('h_index', 0)]
    if any(h_indices):
        profile['metrics']['h_index'] = max(h_indices)

    # Use highest citation count
    citations = [
        wos.get('citations', 0),
        scopus.get('citations', 0),
        scholar.get('citations', 0)
    ]
    if any(citations):
        profile['metrics']['citacoes'] = max(citations)

    # Use highest article count
    articles = [
        wos.get('works', 0),
        scopus.get('works', 0),
        scholar.get('works', 0)
    ]
    if any(articles):
        profile['metrics']['artigos'] = max(articles)

    # Update last update date
    profile['metrics']['ultima_atualizacao'] = datetime.now().strftime("%Y-%m-%d")

    # Add CNPq fellowship info
    profile['bolsista_cnpq'] = extracted.get('bolsista_produtividade', 'Não')

    # Add publications
    publications = extracted.get('publications', {})

    # Convert to standardized format
    profile['publicacoes'] = []

    # Add journal articles
    for artigo in publications.get('artigos_periodicos', []):
        pub = {
            'tipo': 'article',
            'authors': artigo.get('autores', []),
            'title': artigo.get('titulo', ''),
            'journal': artigo.get('periodico', ''),
            'year': artigo.get('ano', 0),
            'volume': artigo.get('volume', ''),
            'pages': artigo.get('paginas', ''),
            'doi': '',  # Not available from Lattes
            'abstract': '',  # Not available from Lattes
            'citations': 0,
            'fwci': 0,
            'scopus_id': '',
            'source': 'lattes'
        }
        profile['publicacoes'].append(pub)

    # Add books
    for livro in publications.get('livros', []):
        pub = {
            'tipo': 'book',
            'authors': livro.get('autores', []),
            'title': livro.get('titulo', ''),
            'publisher': livro.get('editora', ''),
            'year': livro.get('ano', 0),
            'source': 'lattes'
        }
        profile['publicacoes'].append(pub)

    # Add book chapters
    for capitulo in publications.get('capitulos_livros', []):
        pub = {
            'tipo': 'book_chapter',
            'authors': capitulo.get('autores', []),
            'title': capitulo.get('titulo', ''),
            'book_title': capitulo.get('livro', ''),
            'year': capitulo.get('ano', 0),
            'source': 'lattes'
        }
        profile['publicacoes'].append(pub)

    # Add conference papers
    for trabalho in publications.get('trabalhos_congressos', []):
        pub = {
            'tipo': 'conference',
            'authors': trabalho.get('autores', []),
            'title': trabalho.get('titulo', ''),
            'conference': trabalho.get('congresso', ''),
            'year': trabalho.get('ano', 0),
            'source': 'lattes'
        }
        profile['publicacoes'].append(pub)

    # Sort publications by year (descending)
    profile['publicacoes'].sort(key=lambda x: x.get('year', 0), reverse=True)

    return profile


def main():
    parser = argparse.ArgumentParser(description='Integra dados do Lattes com perfis JSON')

    parser.add_argument('--extracted-dir', type=str,
                        default='../../lattes_data/lattes_extracted',
                        help='Diretório com dados extraídos')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Diretório com perfis JSON')

    parser.add_argument('--backup', action='store_true',
                        help='Fazer backup dos perfis antes de atualizar')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de perfis para teste')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    extracted_dir = (script_dir / args.extracted_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    # Find all extracted files
    extracted_files = sorted(extracted_dir.glob('*_extracted.json'))

    if args.limit:
        extracted_files = extracted_files[:args.limit]

    print(f"\n{'='*80}")
    print(f"INTEGRAÇÃO DE DADOS DO LATTES")
    print(f"{'='*80}")
    print(f"Arquivos extraídos: {len(extracted_files)}")
    print(f"Diretório perfis: {profiles_dir}")
    print(f"Fazer backup: {args.backup}")
    print(f"{'='*80}\n")

    updated = 0
    errors = []

    for extracted_file in extracted_files:
        # Get professor ID from filename
        professor_id = extracted_file.stem.replace('_extracted', '')
        profile_file = profiles_dir / f"{professor_id}.json"

        if not profile_file.exists():
            print(f"✗ Perfil não encontrado: {professor_id}")
            errors.append((professor_id, "Profile not found"))
            continue

        print(f"📝 Atualizando: {professor_id}")

        try:
            # Backup if requested
            if args.backup:
                backup_file = profiles_dir / f"{professor_id}.json.backup"
                with open(profile_file, 'r') as f:
                    backup_data = f.read()
                with open(backup_file, 'w') as f:
                    f.write(backup_data)

            # Integrate data
            updated_profile = integrate_data(extracted_file, profile_file)

            # Save updated profile
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(updated_profile, f, indent=2, ensure_ascii=False)

            print(f"  ✓ Atualizado com sucesso")
            print(f"    - Publicações: {len(updated_profile['publicacoes'])}")
            print(f"    - H-index: {updated_profile['metrics']['h_index']}")
            print(f"    - Citações: {updated_profile['metrics']['citacoes']}")
            print(f"    - Bolsista CNPq: {updated_profile['bolsista_cnpq']}")

            updated += 1

        except Exception as e:
            print(f"  ✗ Erro: {e}")
            errors.append((professor_id, str(e)))

    # Summary
    print(f"\n{'='*80}")
    print(f"RESUMO")
    print(f"{'='*80}")
    print(f"✓ Perfis atualizados: {updated}")
    print(f"✗ Erros: {len(errors)}")
    if errors:
        print(f"\nErros:")
        for prof_id, error in errors:
            print(f"  - {prof_id}: {error}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
