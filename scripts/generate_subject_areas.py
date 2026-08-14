#!/usr/bin/env python3
"""
Generate subject areas data for publications filter.
Extracts top 20 most frequent subject areas from all publications.
"""

import json
from pathlib import Path
from collections import Counter

def main():
    # Paths
    script_dir = Path(__file__).parent
    pubs_dir = script_dir.parent / "data" / "publications" / "by_eid"
    output_file = script_dir.parent / "data" / "subject_areas.json"

    print("=" * 60)
    print("GENERATING SUBJECT AREAS DATA")
    print("=" * 60)
    print()

    # Count subject areas
    subject_area_counts = Counter()
    subject_area_info = {}  # Store full info for each area

    total_pubs = 0
    pubs_with_areas = 0

    for pub_file in sorted(pubs_dir.glob("*.json")):
        total_pubs += 1

        with open(pub_file, 'r', encoding='utf-8') as f:
            pub = json.load(f)

        # Subject areas are nested under scopus.subject_areas
        scopus_data = pub.get('scopus', {})
        areas = scopus_data.get('subject_areas', [])

        if areas:
            pubs_with_areas += 1

            for area in areas:
                # In the data, 'code' contains the area name
                area_name = area.get('code', 'Unknown')
                subject_area_counts[area_name] += 1

                # Store full info (will be overwritten, but all entries are same)
                if area_name not in subject_area_info:
                    subject_area_info[area_name] = {
                        'name': area_name,
                        'abbrev': area.get('abbrev', ''),
                        'display': area.get('name') or area_name  # Use name if available, else code
                    }

    print(f"Total publications: {total_pubs}")
    print(f"Publications with subject areas: {pubs_with_areas}")
    print(f"Unique subject areas: {len(subject_area_counts)}")
    print()

    # Get top 20
    top_20 = subject_area_counts.most_common(20)

    print("Top 20 Subject Areas:")
    print("-" * 60)

    top_areas_list = []
    for i, (area_name, count) in enumerate(top_20, 1):
        info = subject_area_info.get(area_name, {'name': area_name, 'abbrev': '', 'display': area_name})

        top_areas_list.append({
            'name': info['name'],
            'abbrev': info['abbrev'],
            'display': info['display'],
            'count': count
        })

        print(f"{i:2}. {info['name'][:50]:50} ({count:4} pubs)")

    print()

    # Create output data
    output_data = {
        'metadata': {
            'total_publications': total_pubs,
            'publications_with_areas': pubs_with_areas,
            'unique_areas': len(subject_area_counts),
            'top_n': 20
        },
        'top_areas': top_areas_list
    }

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"Subject areas data saved to: {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
