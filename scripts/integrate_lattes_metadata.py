#!/usr/bin/env python3
"""
Integração de Metadados do Lattes nos Perfis dos Professores

Integra os dados extraídos do Lattes nos perfis JSON existentes:
- Foto (caminho relativo)
- Bolsista CNPq
- ORCID (apenas se não existir)
- Formação acadêmica
- Resumo/Bio
- Prêmios e títulos
- Idiomas
"""

import json
from pathlib import Path
import argparse
from datetime import datetime


class LattesMetadataIntegrator:
    def __init__(self, metadata_dir, profiles_dir, dry_run=False):
        self.metadata_dir = Path(metadata_dir)
        self.profiles_dir = Path(profiles_dir)
        self.dry_run = dry_run

    def integrate_metadata(self, professor_id):
        """Integrate Lattes metadata into professor profile"""

        # Load metadata
        metadata_file = self.metadata_dir / f"{professor_id}_metadata.json"
        if not metadata_file.exists():
            print(f"  ⚠ Metadados não encontrados, pulando")
            return None

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load existing profile
        profile_file = self.profiles_dir / f"{professor_id}.json"
        if not profile_file.exists():
            print(f"  ⚠ Perfil não encontrado, pulando")
            return None

        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # Track changes
        changes = []

        # 1. Add/update photo
        if metadata.get('foto'):
            if profile.get('foto') != metadata['foto']:
                profile['foto'] = metadata['foto']
                changes.append(f"Foto: {metadata['foto']}")

        # 2. Add/update CNPq fellowship
        existing_cnpq = profile.get('bolsista_cnpq', 'Não')
        new_cnpq = metadata.get('bolsista_produtividade', 'Não')
        if existing_cnpq != new_cnpq:
            profile['bolsista_cnpq'] = new_cnpq
            changes.append(f"Bolsista CNPq: {new_cnpq}")

        # 3. Add ORCID only if doesn't exist
        if metadata.get('orcid') and not metadata.get('orcid_already_exists'):
            if 'links' not in profile:
                profile['links'] = {}

            if not profile['links'].get('orcid'):
                profile['links']['orcid'] = metadata['orcid']
                changes.append(f"ORCID adicionado: {metadata['orcid']}")

        # 4. Add/update academic background
        if metadata.get('formacao_academica'):
            profile['formacao_academica'] = metadata['formacao_academica']
            changes.append(f"Formação: {len(metadata['formacao_academica'])} títulos")

        # 5. Add/update resume/bio
        if metadata.get('resumo'):
            # Store in both PT and EN (same text for now)
            if 'resumo' not in profile:
                profile['resumo'] = {}

            profile['resumo']['pt'] = metadata['resumo']
            # If no EN version exists, use PT as placeholder
            if 'en' not in profile.get('resumo', {}):
                profile['resumo']['en'] = metadata['resumo']

            changes.append(f"Resumo: {len(metadata['resumo'])} caracteres")

        # 6. Add/update awards
        if metadata.get('premios_titulos'):
            profile['premios_titulos'] = metadata['premios_titulos']
            changes.append(f"Prêmios: {len(metadata['premios_titulos'])}")

        # 7. Add/update languages
        if metadata.get('idiomas'):
            profile['idiomas'] = metadata['idiomas']
            changes.append(f"Idiomas: {len(metadata['idiomas'])}")

        # 8. Update metadata timestamp
        if 'metadata' not in profile:
            profile['metadata'] = {}

        profile['metadata']['lattes_updated'] = datetime.now().isoformat()
        profile['metadata']['lattes_extraction_date'] = metadata.get('extraction_date')

        return profile, changes

    def save_profile(self, profile, professor_id):
        """Save updated profile"""
        profile_file = self.profiles_dir / f"{professor_id}.json"

        if self.dry_run:
            print(f"  [DRY-RUN] Salvaria em: {profile_file.name}")
        else:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Perfil atualizado: {profile_file.name}")

    def run(self, limit=None):
        """Run integration for all metadata files"""
        metadata_files = sorted(self.metadata_dir.glob('*_metadata.json'))

        if limit:
            metadata_files = metadata_files[:limit]

        total = len(metadata_files)
        print(f"\n{'='*80}")
        print(f"INTEGRAÇÃO DE METADADOS DO LATTES")
        print(f"{'='*80}")
        print(f"Total de arquivos: {total}")
        print(f"Diretório metadados: {self.metadata_dir}")
        print(f"Diretório perfis: {self.profiles_dir}")
        print(f"Modo: {'DRY-RUN (não salva)' if self.dry_run else 'GRAVAÇÃO ATIVA'}")
        print(f"{'='*80}")

        integrated_count = 0
        skipped_count = 0
        errors = []

        for idx, metadata_file in enumerate(metadata_files, 1):
            professor_id = metadata_file.stem.replace('_metadata', '')

            print(f"\n[{idx}/{total}] {professor_id}")

            try:
                result = self.integrate_metadata(professor_id)

                if result is None:
                    skipped_count += 1
                    continue

                profile, changes = result

                if changes:
                    print(f"  📝 Alterações ({len(changes)}):")
                    for change in changes:
                        print(f"     - {change}")

                    self.save_profile(profile, professor_id)
                    integrated_count += 1
                else:
                    print(f"  ⏭️  Sem alterações")
                    skipped_count += 1

            except Exception as e:
                print(f"  ✗ ERRO: {e}")
                import traceback
                traceback.print_exc()
                errors.append((professor_id, str(e)))

        # Summary
        print(f"\n{'='*80}")
        print(f"RESUMO")
        print(f"{'='*80}")
        print(f"✓ Integrados com sucesso: {integrated_count}")
        print(f"⏭️  Pulados (sem alterações/dados): {skipped_count}")
        print(f"✗ Erros: {len(errors)}")
        if errors:
            print(f"\nErros:")
            for prof_id, error in errors:
                print(f"  - {prof_id}: {error}")
        print(f"{'='*80}")

        if self.dry_run:
            print(f"\n⚠️  DRY-RUN: Nenhum arquivo foi modificado")
            print(f"Execute novamente sem --dry-run para salvar as alterações")


def main():
    parser = argparse.ArgumentParser(
        description='Integra metadados do Lattes nos perfis dos professores',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Dados integrados:
  - Foto (caminho)
  - Bolsista CNPq + Nível
  - ORCID (apenas se não existir)
  - Formação Acadêmica
  - Resumo/Bio
  - Prêmios e Títulos
  - Idiomas

Exemplos de uso:
  # Dry-run (não salva, apenas mostra o que seria alterado)
  python3 integrate_lattes_metadata.py --dry-run

  # Executar integração (salva alterações)
  python3 integrate_lattes_metadata.py

  # Testar com apenas 5 professores
  python3 integrate_lattes_metadata.py --dry-run --limit 5
        ''')

    parser.add_argument('--metadata-dir', type=str,
                        default='../../lattes_data/lattes_metadata',
                        help='Diretório com metadados extraídos do Lattes')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/professores/profiles',
                        help='Diretório com perfis JSON dos professores')

    parser.add_argument('--dry-run', action='store_true',
                        help='Modo dry-run: não salva alterações, apenas mostra o que seria feito')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de professores para teste')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    metadata_dir = (script_dir / args.metadata_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    integrator = LattesMetadataIntegrator(
        metadata_dir=metadata_dir,
        profiles_dir=profiles_dir,
        dry_run=args.dry_run
    )

    integrator.run(limit=args.limit)


if __name__ == '__main__':
    main()
