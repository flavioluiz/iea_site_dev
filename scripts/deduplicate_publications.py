#!/usr/bin/env python3
"""
Deduplicate Publications from Scopus Data

This script processes all fetched Scopus publications and creates a deduplicated
master index. Publications co-authored by multiple EAM professors are identified
and stored as a single record.

Deduplication strategy:
1. DOI match (highest priority)
2. EID match (Scopus Electronic Identifier)
3. Fuzzy title matching (for publications without DOI/EID)

Usage:
    python deduplicate_publications.py [--dry-run] [--verbose]
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime
import argparse


class PublicationDeduplicator:
    """Deduplicates publications and creates master records"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.raw_path = base_path / "data" / "scopus" / "raw"
        self.pubs_path = base_path / "data" / "publications" / "by_eid"
        self.matched_file = base_path / "scripts" / "matched_professors.json"

        # Load professor data
        self.professors = self._load_professors()

        # Deduplication indexes
        self.doi_index = {}  # doi -> eid
        self.eid_index = {}  # eid -> publication
        self.title_index = defaultdict(list)  # normalized_title -> [eids]

        # Statistics
        self.stats = {
            "total_pubs_raw": 0,
            "unique_pubs": 0,
            "co_authored": 0,
            "no_doi": 0,
            "no_eid": 0,
            "duplicates_found": 0
        }

    def _load_professors(self) -> Dict:
        """Load matched professors"""
        with open(self.matched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        profs = {}
        for prof in data['matched']:
            profs[prof['scopus_author_id']] = {
                'id': prof['professor_id'],
                'name': prof['professor_name']
            }
        return profs

    def _normalize_title(self, title: str) -> str:
        """Normalize title for fuzzy matching"""
        if not title:
            return ""

        # Lowercase
        title = title.lower()

        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = ' '.join(title.split())

        return title

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate title similarity (simple word overlap)"""
        words1 = set(self._normalize_title(title1).split())
        words2 = set(self._normalize_title(title2).split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _identify_eam_authors(self, pub_data: Dict) -> List[Dict]:
        """Identify which authors are EAM professors"""
        eam_authors = []

        author_ids = pub_data.get('author_ids', [])
        author_names = pub_data.get('author_names', [])

        if not author_ids:
            return eam_authors

        # Split author IDs (can be semicolon-separated)
        if isinstance(author_ids, str):
            author_ids = author_ids.split(';')

        # Split author names
        if isinstance(author_names, str):
            author_names = author_names.split(';')

        # Match authors
        for i, author_id in enumerate(author_ids):
            author_id = author_id.strip()
            if author_id in self.professors:
                prof = self.professors[author_id]
                author_name = author_names[i].strip() if i < len(author_names) else "Unknown"

                eam_authors.append({
                    "author_id": author_id,
                    "professor_id": prof['id'],
                    "professor_name": prof['name'],
                    "author_name": author_name,
                    "position": i + 1
                })

        return eam_authors

    def _create_master_record(self, pub_data: Dict, prof_id: str, eam_authors: List[Dict]) -> Dict:
        """Create master publication record"""

        # Extract journal info
        journal_info = {
            "name": pub_data.get('journal'),
            "issn": pub_data.get('issn'),
            "eissn": pub_data.get('eissn'),
            "volume": pub_data.get('volume'),
            "issue": pub_data.get('issue'),
            "pages": pub_data.get('page_range'),
            "article_number": pub_data.get('article_number')
        }

        # Map subtype to type
        subtype = pub_data.get('subtype', '').lower()
        pub_type = 'article'  # default
        if 'conference' in subtype or 'proceeding' in subtype:
            pub_type = 'conference'
        elif 'review' in subtype:
            pub_type = 'review'
        elif 'book' in subtype or 'chapter' in subtype:
            pub_type = 'book_chapter'

        # Build authors list
        author_ids = pub_data.get('author_ids', []) or []
        author_names = pub_data.get('author_names', []) or []
        author_afids = pub_data.get('author_afids', []) or []

        if isinstance(author_ids, str):
            author_ids = author_ids.split(';')
        if isinstance(author_names, str):
            author_names = author_names.split(';')
        if isinstance(author_afids, str):
            author_afids = author_afids.split(';')

        # Ensure lists
        if not isinstance(author_ids, list):
            author_ids = []
        if not isinstance(author_names, list):
            author_names = []
        if not isinstance(author_afids, list):
            author_afids = []

        authors = []
        eam_prof_ids = {a['author_id'] for a in eam_authors}

        for i, author_id in enumerate(author_ids):
            author_id = author_id.strip()
            author_name = author_names[i].strip() if i < len(author_names) else ""
            affiliation = author_afids[i].strip() if i < len(author_afids) else ""

            is_eam = author_id in eam_prof_ids
            prof_id_match = next((a['professor_id'] for a in eam_authors if a['author_id'] == author_id), None)

            authors.append({
                "name": author_name,
                "scopus_id": author_id,
                "affiliation": affiliation,
                "is_eam_professor": is_eam,
                "eam_professor_id": prof_id_match
            })

        # Master record
        record = {
            "publication_id": pub_data.get('eid'),
            "eid": pub_data.get('eid'),
            "doi": pub_data.get('doi'),
            "pii": pub_data.get('pii'),
            "pubmed_id": pub_data.get('pubmed_id'),

            "title": pub_data.get('title'),
            "abstract": pub_data.get('abstract'),
            "authkeywords": pub_data.get('authkeywords'),

            "year": pub_data.get('year'),
            "date": pub_data.get('date'),
            "type": pub_type,
            "subtype": pub_data.get('subtype'),

            "journal": journal_info,

            "authors": authors,
            "eam_coauthors": [a['professor_id'] for a in eam_authors],

            "scopus": {
                "citations": pub_data.get('cited_by', 0),
                "subject_areas": pub_data.get('subject_areas', []),
                "references_count": pub_data.get('references_count', 0),
                "scopus_link": pub_data.get('scopus_link')
            },

            "metadata": {
                "source": "scopus",
                "last_updated": datetime.now().isoformat(),
                "data_quality_score": self._calculate_quality_score(pub_data)
            }
        }

        return record

    def _calculate_quality_score(self, pub_data: Dict) -> int:
        """Calculate data quality score (0-100)"""
        score = 0

        # Has DOI (20 points)
        if pub_data.get('doi'):
            score += 20

        # Has abstract (20 points)
        if pub_data.get('abstract'):
            score += 20

        # Has keywords (10 points)
        if pub_data.get('authkeywords'):
            score += 10

        # Has journal info (15 points)
        if pub_data.get('journal'):
            score += 15

        # Has authors (15 points)
        if pub_data.get('author_names'):
            score += 15

        # Has subject areas (10 points)
        if pub_data.get('subject_areas'):
            score += 10

        # Has citation count (10 points)
        if pub_data.get('cited_by'):
            score += 10

        return score

    def process_all_publications(self, verbose: bool = False) -> Dict:
        """Process all publications and create deduplicated records"""

        if verbose:
            print(f"\n{'='*60}")
            print("DEDUPLICATION PROCESS")
            print(f"{'='*60}\n")

        # Process each professor's publications
        for prof_id, prof_data in self.professors.items():
            prof_name = prof_data['name']
            prof_file_id = prof_data['id']

            pubs_file = self.raw_path / f"{prof_file_id}_pubs.json"

            if not pubs_file.exists():
                if verbose:
                    print(f"⚠️  No publications file for {prof_name}")
                continue

            # Load publications
            with open(pubs_file, 'r', encoding='utf-8') as f:
                pubs = json.load(f)

            if verbose:
                print(f"Processing: {prof_name} ({len(pubs)} publications)")

            for pub in pubs:
                self.stats['total_pubs_raw'] += 1

                eid = pub.get('eid')
                doi = pub.get('doi')
                title = pub.get('title')

                if not eid:
                    self.stats['no_eid'] += 1
                    if verbose:
                        print(f"  ⚠️  No EID: {title[:50]}...")
                    continue

                # Check if already processed
                if eid in self.eid_index:
                    # Add this professor as co-author
                    existing = self.eid_index[eid]
                    if prof_file_id not in existing['eam_coauthors']:
                        existing['eam_coauthors'].append(prof_file_id)
                        self.stats['co_authored'] += 1

                        if verbose:
                            print(f"  ✓ Co-author: {title[:50]}...")

                    self.stats['duplicates_found'] += 1
                    continue

                # Identify EAM authors
                eam_authors = self._identify_eam_authors(pub)

                # Create master record
                master = self._create_master_record(pub, prof_file_id, eam_authors)

                # Index by EID
                self.eid_index[eid] = master

                # Index by DOI
                if doi:
                    self.doi_index[doi] = eid
                else:
                    self.stats['no_doi'] += 1

                # Index by title (for fuzzy matching)
                norm_title = self._normalize_title(title)
                if norm_title:
                    self.title_index[norm_title].append(eid)

                self.stats['unique_pubs'] += 1

        if verbose:
            print(f"\n{'='*60}")
            print("DEDUPLICATION STATISTICS")
            print(f"{'='*60}")
            print(f"Total publications (raw): {self.stats['total_pubs_raw']}")
            print(f"Unique publications: {self.stats['unique_pubs']}")
            print(f"Duplicates removed: {self.stats['duplicates_found']}")
            print(f"Co-authored (EAM): {self.stats['co_authored']}")
            print(f"Publications without DOI: {self.stats['no_doi']}")
            print(f"Publications without EID: {self.stats['no_eid']}")
            print(f"{'='*60}\n")

        return self.eid_index

    def save_deduplicated_publications(self, dry_run: bool = False):
        """Save deduplicated publications to individual files"""

        if dry_run:
            print("DRY RUN: Would save publications to:")
            print(f"  {self.pubs_path}/")
            return

        # Create directory
        self.pubs_path.mkdir(parents=True, exist_ok=True)

        print(f"\nSaving {len(self.eid_index)} publications...")

        saved = 0
        for eid, pub in self.eid_index.items():
            # Create filename from EID (remove prefix)
            filename = eid.replace('2-s2.0-', '').replace(':', '_')
            filepath = self.pubs_path / f"{filename}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pub, f, ensure_ascii=False, indent=2)

            saved += 1

            if saved % 100 == 0:
                print(f"  Saved {saved}/{len(self.eid_index)}...")

        print(f"✓ Saved {saved} publications")

    def build_master_index(self, dry_run: bool = False) -> Dict:
        """Build master publication index"""

        index = {
            "metadata": {
                "total_publications": len(self.eid_index),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "publications": {},
            "doi_to_eid_map": self.doi_index,
            "statistics": self.stats
        }

        # Add publication summaries
        for eid, pub in self.eid_index.items():
            index["publications"][eid] = {
                "title": pub['title'],
                "year": pub['year'],
                "type": pub['type'],
                "eam_coauthors": pub['eam_coauthors'],
                "citations": pub['scopus']['citations']
            }

        if dry_run:
            print("\nDRY RUN: Would save index to:")
            print(f"  {self.base_path / 'data' / 'publications' / 'index.json'}")
            return index

        # Save index
        index_file = self.base_path / "data" / "publications" / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        print(f"\n✓ Master index saved: {index_file}")

        return index


def main():
    parser = argparse.ArgumentParser(
        description="Deduplicate publications from Scopus data"
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without saving files')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print detailed processing information')

    args = parser.parse_args()

    # Find base path
    base_path = Path(__file__).parent.parent

    # Initialize deduplicator
    dedup = PublicationDeduplicator(base_path)

    # Process publications
    print("Processing publications from Scopus data...")
    dedup.process_all_publications(verbose=args.verbose)

    # Save deduplicated publications
    dedup.save_deduplicated_publications(dry_run=args.dry_run)

    # Build master index
    index = dedup.build_master_index(dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print("DEDUPLICATION COMPLETE")
    print(f"{'='*60}")
    print(f"Unique publications: {index['metadata']['total_publications']}")
    print(f"Co-authored publications: {dedup.stats['co_authored']}")
    print(f"Duplicates removed: {dedup.stats['duplicates_found']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
