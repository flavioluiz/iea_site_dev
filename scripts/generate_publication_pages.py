#!/usr/bin/env python3
"""
Generate Hugo markdown files for individual publication pages.
Creates content files at: content/publicacoes/{eid}/index.pt.md and index.en.md
"""

import json
from pathlib import Path
import sys

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "publications" / "by_eid"
CONTENT_DIR = Path(__file__).parent.parent / "content" / "publicacoes"

def generate_publication_pages():
    """Generate markdown files for all publications."""

    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        return 1

    # Get all publication JSON files
    pub_files = list(DATA_DIR.glob("*.json"))

    if not pub_files:
        print(f"❌ No publication JSON files found in {DATA_DIR}")
        return 1

    print(f"\n{'='*60}")
    print(f"GENERATING PUBLICATION PAGES")
    print(f"{'='*60}\n")
    print(f"Found {len(pub_files)} publications to process")

    created_count = 0
    skipped_count = 0
    error_count = 0

    for pub_file in pub_files:
        eid_numeric = pub_file.stem  # e.g., "85210484189"

        try:
            # Load publication data
            with open(pub_file, 'r', encoding='utf-8') as f:
                pub_data = json.load(f)

            # Create directory for this publication
            pub_dir = CONTENT_DIR / eid_numeric
            pub_dir.mkdir(parents=True, exist_ok=True)

            # Generate Portuguese markdown
            pt_file = pub_dir / "index.pt.md"
            en_file = pub_dir / "index.en.md"

            # Markdown content (minimal - all data comes from JSON via template)
            title = pub_data.get('title', 'Publicação')

            # Escape title for YAML - replace double quotes with single quotes
            title_safe = title.replace('"', "'")

            pt_content = f"""---
title: "{title_safe}"
date: {pub_data.get('date', '2024-01-01')}
draft: false
type: publicacoes
layout: single
eid: "{eid_numeric}"
---
"""

            en_content = f"""---
title: "{title_safe}"
date: {pub_data.get('date', '2024-01-01')}
draft: false
type: publicacoes
layout: single
eid: "{eid_numeric}"
---
"""

            # Write files
            with open(pt_file, 'w', encoding='utf-8') as f:
                f.write(pt_content)

            with open(en_file, 'w', encoding='utf-8') as f:
                f.write(en_content)

            created_count += 1

            if created_count % 100 == 0:
                print(f"  Processed {created_count}/{len(pub_files)}...")

        except Exception as e:
            print(f"❌ Error processing {eid_numeric}: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Created: {created_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*60}\n")

    return 0

if __name__ == "__main__":
    sys.exit(generate_publication_pages())
