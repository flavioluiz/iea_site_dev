#!/usr/bin/env python3
"""
Merge Scopus Data into Professor Profiles

This script updates professor profiles with Scopus data:
1. Removes ALL Lattes publication data
2. Adds references to Scopus publications
3. Updates metrics (h-index, citations, etc.)
4. Adds Scopus metadata (subject areas, affiliations)
5. Preserves manual fields (linhas_pesquisa, links)

Usage:
    python merge_scopus_into_profiles.py [--dry-run] [--professor PROF_ID]

    --dry-run: Don't save changes, just print what would be done
    --professor: Only process a specific professor
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProfileMerger:
    """Merges Scopus data into professor profiles"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.profiles_path = base_path / "data" / "professores" / "profiles"
        self.raw_path = base_path / "data" / "scopus" / "raw"
        self.pubs_index_file = base_path / "data" / "publications" / "index.json"
        self.matched_file = base_path / "scripts" / "matched_professors.json"

        # Load data
        self.matched_profs = self._load_matched()
        self.pubs_index = self._load_publications_index()

        # Statistics
        self.stats = {
            "profiles_processed": 0,
            "profiles_updated": 0,
            "lattes_pubs_removed": 0,
            "scopus_pubs_added": 0,
            "metrics_updated": 0
        }

    def _load_matched(self) -> Dict:
        """Load matched professors"""
        with open(self.matched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        profs = {}
        for prof in data['matched']:
            profs[prof['professor_id']] = prof

        return profs

    def _load_publications_index(self) -> Dict:
        """Load publications index"""
        with open(self.pubs_index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def merge_profile(self, prof_id: str, dry_run: bool = False, verbose: bool = False) -> Dict:
        """Merge Scopus data into a single professor profile"""

        profile_file = self.profiles_path / f"{prof_id}.json"

        if not profile_file.exists():
            print(f"❌ Profile not found: {prof_id}")
            return None

        # Load current profile
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing: {profile['nome']} ({prof_id})")
            print(f"{'='*60}")

        # Load Scopus author data
        author_file = self.raw_path / f"{prof_id}_author.json"
        if not author_file.exists():
            print(f"  ⚠️  No Scopus author data found")
            return None

        with open(author_file, 'r', encoding='utf-8') as f:
            scopus_author = json.load(f)

        # Load Scopus publications
        pubs_file = self.raw_path / f"{prof_id}_pubs.json"
        if not pubs_file.exists():
            print(f"  ⚠️  No Scopus publications found")
            return None

        with open(pubs_file, 'r', encoding='utf-8') as f:
            scopus_pubs = json.load(f)

        # Count Lattes publications to remove
        lattes_count = len(profile.get('publicacoes', []))

        if verbose:
            print(f"  Current Lattes publications: {lattes_count}")
            print(f"  Scopus publications: {len(scopus_pubs)}")

        # Update Scopus IDs section
        scopus_id = self.matched_profs[prof_id]['scopus_author_id']
        orcid = self.matched_profs[prof_id].get('orcid')

        profile['scopus_ids'] = {
            "author_id": scopus_id,
            "eid": scopus_author.get('eid'),
            "orcid": orcid
        }

        # Update metrics from Scopus
        profile['metrics'] = {
            "h_index": scopus_author.get('h_index', 0),
            "citacoes": scopus_author.get('total_citacoes', 0),
            "cited_by_count": scopus_author.get('cited_by_count', 0),
            "artigos": scopus_author.get('total_documentos', 0),
            "coauthor_count": scopus_author.get('coauthor_count', 0),
            "publication_range": scopus_author.get('intervalo_publicacao', []),
            "ultima_atualizacao": datetime.now().isoformat().split('T')[0],
            "data_source": "scopus"
        }

        # Add Scopus metadata
        subject_areas = []
        if scopus_author.get('classificacao_assuntos'):
            # Get top 5 subject areas
            sorted_areas = sorted(
                scopus_author['classificacao_assuntos'],
                key=lambda x: x.get('num_documentos', 0),
                reverse=True
            )[:5]

            # Map subject group IDs to names (simplified)
            for area in sorted_areas:
                subject_areas.append({
                    "id": area.get('subject_group_id'),
                    "document_count": area.get('num_documentos')
                })

        affiliation_current = None
        if scopus_author.get('afiliacoes_atuais'):
            aff = scopus_author['afiliacoes_atuais'][0]
            affiliation_current = {
                "name": aff.get('nome'),
                "city": aff.get('cidade'),
                "country": aff.get('pais')
            }

        profile['scopus_metadata'] = {
            "subject_areas": subject_areas,
            "affiliation_current": affiliation_current,
            "affiliation_history": scopus_author.get('afiliacoes_historicas', [])[:5],  # Top 5
            "link_scopus": scopus_author.get('link_scopus')
        }

        # Update Scopus link in links section
        if not profile['links'].get('scopus'):
            profile['links']['scopus'] = f"https://www.scopus.com/authid/detail.uri?authorId={scopus_id}"

        # REMOVE ALL Lattes publications
        # Replace with Scopus publication references
        new_publications = []

        for pub in scopus_pubs:
            eid = pub.get('eid')
            if not eid:
                continue

            # Find position of this author
            author_ids = pub.get('author_ids', [])
            if isinstance(author_ids, str):
                author_ids = author_ids.split(';')

            author_position = None
            for i, aid in enumerate(author_ids):
                if aid.strip() == scopus_id:
                    author_position = i + 1
                    break

            new_publications.append({
                "publication_id": eid,
                "author_position": author_position,
                "is_corresponding_author": False  # Could be enhanced
            })

        profile['publicacoes'] = new_publications

        if verbose:
            print(f"  ✓ Removed {lattes_count} Lattes publications")
            print(f"  ✓ Added {len(new_publications)} Scopus publication references")
            print(f"  ✓ Updated metrics: h-index={profile['metrics']['h_index']}, citations={profile['metrics']['citacoes']}")

        # Update statistics
        self.stats['profiles_processed'] += 1
        self.stats['profiles_updated'] += 1
        self.stats['lattes_pubs_removed'] += lattes_count
        self.stats['scopus_pubs_added'] += len(new_publications)
        self.stats['metrics_updated'] += 1

        # Save profile
        if not dry_run:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)

            if verbose:
                print(f"  ✓ Profile saved")

        return profile

    def merge_all_profiles(self, dry_run: bool = False, verbose: bool = False):
        """Merge Scopus data into all professor profiles"""

        print(f"\n{'='*60}")
        print("MERGING SCOPUS DATA INTO PROFILES")
        print(f"{'='*60}\n")

        if dry_run:
            print("⚠️  DRY RUN MODE - No files will be modified\n")

        for prof_id in self.matched_profs.keys():
            self.merge_profile(prof_id, dry_run=dry_run, verbose=verbose)

        print(f"\n{'='*60}")
        print("MERGE COMPLETE")
        print(f"{'='*60}")
        print(f"Profiles processed: {self.stats['profiles_processed']}")
        print(f"Profiles updated: {self.stats['profiles_updated']}")
        print(f"Lattes publications removed: {self.stats['lattes_pubs_removed']}")
        print(f"Scopus publication references added: {self.stats['scopus_pubs_added']}")
        print(f"Metrics updated: {self.stats['metrics_updated']}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Merge Scopus data into professor profiles"
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without saving changes')
    parser.add_argument('--professor', type=str,
                       help='Only process a specific professor')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print detailed processing information')

    args = parser.parse_args()

    # Find base path
    base_path = Path(__file__).parent.parent

    # Initialize merger
    merger = ProfileMerger(base_path)

    # Process profiles
    if args.professor:
        merger.merge_profile(args.professor, dry_run=args.dry_run, verbose=True)
    else:
        merger.merge_all_profiles(dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
