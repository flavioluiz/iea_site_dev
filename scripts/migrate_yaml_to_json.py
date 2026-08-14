#!/usr/bin/env python3
"""
Migration Script: YAML to JSON
Converts existing YAML professor data to new JSON structure
"""

import yaml
import json
import re
import argparse
from pathlib import Path
from datetime import datetime
import unicodedata


def generate_slug(name):
    """Generate URL-friendly slug from professor name"""
    # Remove accents
    nfkd_form = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')

    # Convert to lowercase and replace spaces with hyphens
    slug = ascii_str.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = slug.strip('-')

    return slug


def extract_first_name(nome, nome_destaque):
    """Extract a reasonable first name for photo filename"""
    # Use nome_destaque if it's a last name, otherwise use first word of nome
    if nome_destaque in nome:
        # Get the part before nome_destaque
        first_part = nome.split(nome_destaque)[0].strip()
        if first_part:
            return first_part.split()[0]

    # Fallback: use first word of name
    return nome.split()[0]


def migrate_professor(prof_data, area_id):
    """Migrate a single professor from YAML to JSON format"""
    nome = prof_data['nome']
    slug = generate_slug(nome)

    # Extract Scopus ID from Scopus link if available
    scopus_link = prof_data.get('scopus', '')
    scopus_id = ''
    if scopus_link and 'authorId=' in scopus_link:
        scopus_id = scopus_link.split('authorId=')[-1].split('&')[0]

    # Build JSON structure
    professor_json = {
        "id": slug,
        "nome": nome,
        "nome_destaque": prof_data.get('nome_destaque', ''),
        "slug": slug,
        "area": area_id,
        "foto": f"{slug}.jpg",  # Default photo filename

        "links": {
            "lattes": prof_data.get('lattes', ''),
            "scopus": scopus_link,
            "google_scholar": prof_data.get('google_scholar', ''),
            "researchgate": prof_data.get('researchgate', ''),
            "site": prof_data.get('site', '')
        },

        "metrics": {
            "h_index": 0,  # To be populated by Scopus import
            "citacoes": 0,
            "artigos": 0,
            "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d")
        },

        "linhas_pesquisa": {
            "pt": prof_data.get('linhas_pesquisa', []),
            "en": []  # To be filled manually or via translation
        },

        "publicacoes": []  # To be populated by Scopus import
    }

    return slug, professor_json


def migrate_yaml_file(yaml_file, output_dir, dry_run=False):
    """Migrate a single YAML file to multiple JSON files"""
    print(f"\nProcessing {yaml_file}...")

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    area_id = data['area_id']
    area_nome = data['area_nome']
    representante = data.get('representante', '')

    print(f"  Area: {area_nome} ({area_id})")
    print(f"  Representante: {representante}")

    permanentes = data.get('permanentes', [])
    print(f"  Professores permanentes: {len(permanentes)}")

    migrated_count = 0
    for prof in permanentes:
        slug, prof_json = migrate_professor(prof, area_id)

        output_file = output_dir / f"{slug}.json"

        if dry_run:
            print(f"    [DRY RUN] Would create: {output_file}")
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prof_json, f, indent=2, ensure_ascii=False)
            print(f"    ✓ Created: {output_file}")

        migrated_count += 1

    return migrated_count


def main():
    parser = argparse.ArgumentParser(description='Migrate YAML professor data to JSON')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--execute', action='store_true',
                        help='Execute the migration')
    parser.add_argument('--yaml-dir', type=str,
                        default='../data/pessoal',
                        help='Directory containing YAML files')
    parser.add_argument('--output-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Output directory for JSON files')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: You must specify either --dry-run or --execute")
        parser.print_help()
        return 1

    # Get script directory
    script_dir = Path(__file__).parent
    yaml_dir = (script_dir / args.yaml_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()

    # Validate directories
    if not yaml_dir.exists():
        print(f"ERROR: YAML directory not found: {yaml_dir}")
        return 1

    if not output_dir.exists():
        print(f"ERROR: Output directory not found: {output_dir}")
        print(f"Please create it first: mkdir -p {output_dir}")
        return 1

    print("=" * 60)
    print("YAML to JSON Migration Script")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"YAML Directory: {yaml_dir}")
    print(f"Output Directory: {output_dir}")

    # Find all YAML files
    yaml_files = sorted(yaml_dir.glob('eam*.yaml'))

    if not yaml_files:
        print(f"\nERROR: No eam*.yaml files found in {yaml_dir}")
        return 1

    print(f"\nFound {len(yaml_files)} YAML files to process")

    total_migrated = 0
    for yaml_file in yaml_files:
        count = migrate_yaml_file(yaml_file, output_dir, dry_run=args.dry_run)
        total_migrated += count

    print("\n" + "=" * 60)
    print(f"Migration {'simulation' if args.dry_run else 'execution'} complete!")
    print(f"Total professors migrated: {total_migrated}")

    if args.dry_run:
        print("\nThis was a DRY RUN. No files were created.")
        print("Run with --execute to perform the actual migration.")
    else:
        print(f"\nJSON files created in: {output_dir}")
        print("\nNext steps:")
        print("1. Review the generated JSON files")
        print("2. Add missing data (Scopus IDs, Google Scholar, ResearchGate)")
        print("3. Run validation: python validate_data.py --all")
        print("4. Translate research lines to English")

    print("=" * 60)

    return 0


if __name__ == '__main__':
    exit(main())
