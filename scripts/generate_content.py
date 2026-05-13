#!/usr/bin/env python3
"""
Content Generation Script
Generates markdown files for professor pages
"""

import json
import argparse
from pathlib import Path


def generate_professor_markdown(professor_id, professor_data, lang='pt'):
    """Generate markdown content for a professor page"""

    if lang == 'pt':
        title = professor_data['nome']
        content_note = "<!-- Conteúdo adicional pode ser adicionado aqui se necessário -->"
    else:  # en
        title = professor_data['nome']
        content_note = "<!-- Additional content can be added here if needed -->"

    frontmatter = f"""---
title: "{title}"
layout: professor
professor_id: "{professor_id}"
type: professores
---

{content_note}
"""

    return frontmatter


def generate_all_content(profiles_dir, output_dir, dry_run=False):
    """Generate markdown files for all professors"""

    profiles_dir = Path(profiles_dir)
    output_dir = Path(output_dir)

    if not profiles_dir.exists():
        print(f"ERROR: Profiles directory not found: {profiles_dir}")
        return 1

    if not output_dir.exists():
        print(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(profiles_dir.glob('*.json'))

    if not json_files:
        print(f"ERROR: No JSON files found in {profiles_dir}")
        return 1

    print(f"\nFound {len(json_files)} professor profiles")
    print(f"Generating content files in: {output_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}\n")

    generated_count = 0

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        professor_id = data['id']

        # Generate Portuguese version
        pt_file = output_dir / f"{professor_id}.pt.md"
        pt_content = generate_professor_markdown(professor_id, data, lang='pt')

        # Generate English version
        en_file = output_dir / f"{professor_id}.en.md"
        en_content = generate_professor_markdown(professor_id, data, lang='en')

        if dry_run:
            print(f"  [DRY RUN] Would create: {pt_file}")
            print(f"  [DRY RUN] Would create: {en_file}")
        else:
            pt_file.write_text(pt_content, encoding='utf-8')
            en_file.write_text(en_content, encoding='utf-8')
            print(f"  ✓ Created: {pt_file}")
            print(f"  ✓ Created: {en_file}")

        generated_count += 1

    # Generate index pages
    index_pt = """---
title: "Corpo Docente"
layout: list
type: professores
---

Conheça os professores permanentes do PG-EAM.
"""

    index_en = """---
title: "Faculty"
layout: list
type: professores
---

Meet the permanent faculty of PG-EAM.
"""

    index_pt_file = output_dir / "_index.pt.md"
    index_en_file = output_dir / "_index.en.md"

    if dry_run:
        print(f"\n  [DRY RUN] Would create: {index_pt_file}")
        print(f"  [DRY RUN] Would create: {index_en_file}")
    else:
        index_pt_file.write_text(index_pt, encoding='utf-8')
        index_en_file.write_text(index_en, encoding='utf-8')
        print(f"\n  ✓ Created: {index_pt_file}")
        print(f"  ✓ Created: {index_en_file}")

    print("\n" + "=" * 60)
    print(f"Content generation {'simulation' if dry_run else 'execution'} complete!")
    print(f"Professors processed: {generated_count}")
    print(f"Total markdown files: {generated_count * 2} + 2 index files")

    if dry_run:
        print("\nThis was a DRY RUN. No files were created.")
        print("Run with --execute to generate the files.")

    print("=" * 60)

    return 0


def main():
    parser = argparse.ArgumentParser(description='Generate professor markdown content files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--execute', action='store_true',
                        help='Execute the content generation')
    parser.add_argument('--profiles-dir', type=str,
                        default='../data/professores/profiles',
                        help='Directory containing JSON profile files')
    parser.add_argument('--output-dir', type=str,
                        default='../content/professores',
                        help='Output directory for markdown files')

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("ERROR: You must specify either --dry-run or --execute")
        parser.print_help()
        return 1

    # Get script directory
    script_dir = Path(__file__).parent

    profiles_dir = (script_dir / args.profiles_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()

    return generate_all_content(profiles_dir, output_dir, dry_run=args.dry_run)


if __name__ == '__main__':
    exit(main())
