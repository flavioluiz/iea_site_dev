#!/usr/bin/env python3
"""
Fetch Scopus Data for All Matched Professors

This script fetches author data and publications from Scopus for all matched professors.
Implements delay between requests (2s default), progress tracking, and resume capability.

Usage:
    python fetch_scopus_all_professors.py [--matched-only] [--resume] [--dry-run]

    --matched-only: Only fetch for matched professors (default)
    --resume: Resume from last successful fetch
    --dry-run: Don't fetch data, just print what would be fetched
    --force: Overwrite existing data
    --delay: Seconds between requests (default: 2.0)
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add parent directory to path to import get_scopus functions
sys.path.insert(0, str(Path(__file__).parent))

import pybliometrics
pybliometrics.init(keys=['e8917d664a72244e7ed90ce9e5ecc082'], inst_tokens=[None])

from get_scopus import get_author_data, get_publications_data


class ScopusFetcher:
    """Fetches Scopus data for multiple professors with configurable delay"""

    def __init__(self, base_path: Path, rate_limit_per_hour: int = 1800):
        self.base_path = base_path
        self.scripts_path = base_path / "scripts"
        self.data_path = base_path / "data" / "scopus"
        self.raw_path = self.data_path / "raw"
        self.logs_path = base_path / "logs"

        # Ensure output directories exist before any read/write operations.
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Rate limiting - default 2 seconds between requests
        self.rate_limit = rate_limit_per_hour
        self.min_delay = 2.0  # seconds between requests (fixed)
        self.last_request_time = 0

        # Progress tracking
        self.metadata_file = self.data_path / "fetch_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load or create fetch metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "last_run": None,
            "last_successful_run": None,
            "completed": [],
            "failed": [],
            "total_requests": 0,
            "last_request_time": None
        }

    def _save_metadata(self):
        """Save fetch metadata"""
        self.metadata["last_run"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _rate_limit_wait(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            print(f"  ⏳ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _exponential_backoff(self, attempt: int, max_wait: int = 60):
        """Calculate exponential backoff delay"""
        wait = min(2 ** attempt, max_wait)
        print(f"  ⏳ Backoff: waiting {wait}s before retry...")
        time.sleep(wait)

    def fetch_professor_data(self, prof_id: str, scopus_id: str, prof_name: str,
                           max_retries: int = 3, fetch_abstracts: bool = True,
                           force: bool = False) -> bool:
        """Fetch data for a single professor with retry logic"""

        print(f"\n{'='*60}")
        print(f"Fetching: {prof_name} (ID: {prof_id})")
        print(f"Scopus Author ID: {scopus_id}")
        print(f"{'='*60}")

        author_file = self.raw_path / f"{prof_id}_author.json"
        pubs_file = self.raw_path / f"{prof_id}_pubs.json"

        # Check if already exists (skip unless forcing)
        if not force and author_file.exists() and pubs_file.exists():
            print(f"  ⚠️  Data already exists. Use --force to overwrite.")
            return True

        for attempt in range(max_retries):
            try:
                # Fetch author data
                print(f"\n  📥 Fetching author data... (attempt {attempt + 1}/{max_retries})")
                self._rate_limit_wait()

                au, author_data = get_author_data(scopus_id)
                self.metadata["total_requests"] += 1

                # Save author data
                with open(author_file, 'w', encoding='utf-8') as f:
                    json.dump(author_data, f, ensure_ascii=False, indent=2)

                print(f"     ✓ Author data saved")
                print(f"       H-index: {author_data.get('h_index', 'N/A')}")
                print(f"       Documents: {author_data.get('total_documentos', 'N/A')}")
                print(f"       Citations: {author_data.get('total_citacoes', 'N/A')}")

                # Fetch publications
                print(f"\n  📥 Fetching publications...")
                self._rate_limit_wait()

                pubs = get_publications_data(au, fetch_abstract=fetch_abstracts)
                self.metadata["total_requests"] += 1

                # Save publications
                with open(pubs_file, 'w', encoding='utf-8') as f:
                    json.dump(pubs, f, ensure_ascii=False, indent=2)

                print(f"     ✓ Publications saved: {len(pubs)} documents")

                # Log to separate file
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "professor_id": prof_id,
                    "professor_name": prof_name,
                    "scopus_id": scopus_id,
                    "documents_fetched": len(pubs),
                    "h_index": author_data.get('h_index'),
                    "status": "success"
                }

                log_file = self.logs_path / f"fetch_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

                return True

            except Exception as e:
                error_msg = str(e)
                print(f"     ❌ Error: {error_msg}")

                if attempt < max_retries - 1:
                    # Check if it's a rate limit error (429)
                    if "429" in error_msg or "Throttling" in error_msg:
                        print(f"     Rate limit hit. Increasing backoff...")
                        self._exponential_backoff(attempt + 3)  # Extra delay for rate limits
                    else:
                        self._exponential_backoff(attempt)
                else:
                    # Final attempt failed
                    print(f"     ❌ Failed after {max_retries} attempts")

                    # Log error
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "professor_id": prof_id,
                        "professor_name": prof_name,
                        "scopus_id": scopus_id,
                        "status": "failed",
                        "error": error_msg
                    }

                    log_file = self.logs_path / f"fetch_{datetime.now().strftime('%Y%m%d')}.jsonl"
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

                    return False

        return False

    def fetch_all(self, matched_file: Path, resume: bool = False,
                 force: bool = False, dry_run: bool = False,
                 fetch_abstracts: bool = True) -> Dict:
        """Fetch data for all matched professors"""

        # Load matched professors
        with open(matched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        matched = data['matched']
        total = len(matched)

        print(f"\n{'='*60}")
        print(f"SCOPUS DATA FETCH")
        print(f"{'='*60}")
        print(f"Total professors: {total}")
        print(f"Delay between requests: {self.min_delay:.1f}s")

        # Estimate time
        # Each professor = 2 requests (author + pubs)
        total_requests = total * 2
        estimated_minutes = (total_requests * self.min_delay) / 60

        print(f"Estimated requests: ~{total_requests}")
        print(f"Estimated time: ~{estimated_minutes:.0f} minutes")

        if resume and not force:
            completed_ids = set(self.metadata.get('completed', []))
            print(f"\nResuming: {len(completed_ids)} already completed")
        else:
            completed_ids = set()
            if resume and force:
                print("\nResuming with --force: previously completed professors will be fetched again")

        if dry_run:
            print("\n⚠️  DRY RUN MODE - No data will be fetched")

        print(f"{'='*60}\n")

        # Process each professor
        success_count = 0
        failed_count = 0
        skipped_count = 0

        start_time = time.time()

        for i, prof in enumerate(matched, 1):
            prof_id = prof['professor_id']
            prof_name = prof['professor_name']
            scopus_id = prof['scopus_author_id']

            # Skip if already completed and resuming
            if resume and prof_id in completed_ids:
                skipped_count += 1
                continue

            if dry_run:
                print(f"\n[{i}/{total}] Would fetch: {prof_name} (Scopus: {scopus_id})")
                continue

            # Fetch data
            success = self.fetch_professor_data(
                prof_id,
                scopus_id,
                prof_name,
                fetch_abstracts=fetch_abstracts,
                force=force
            )

            if success:
                success_count += 1
                if prof_id not in self.metadata['completed']:
                    self.metadata['completed'].append(prof_id)
                if prof_id in self.metadata.get('failed', []):
                    self.metadata['failed'].remove(prof_id)
            else:
                failed_count += 1
                if prof_id not in self.metadata.get('failed', []):
                    self.metadata['failed'].append(prof_id)

            # Save metadata after each professor
            self._save_metadata()

            # Progress update
            elapsed = time.time() - start_time
            rate = (i - skipped_count) / elapsed if elapsed > 0 else 0
            remaining = total - i
            eta_seconds = remaining / rate if rate > 0 else 0

            print(f"\n  Progress: {i}/{total} ({i/total*100:.1f}%)")
            print(f"  Success: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}")
            print(f"  Elapsed: {elapsed/60:.1f}min | ETA: {eta_seconds/60:.1f}min")

        # Final summary
        print(f"\n{'='*60}")
        print(f"FETCH COMPLETE")
        print(f"{'='*60}")
        print(f"Total processed: {i - skipped_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")
        print(f"Total requests: {self.metadata['total_requests']}")

        if not dry_run and failed_count == 0:
            self.metadata["last_successful_run"] = datetime.now().isoformat()
            self._save_metadata()

        if failed_count > 0:
            print(f"\n⚠️  {failed_count} professors failed to fetch:")
            for prof in matched:
                if prof['professor_id'] in self.metadata.get('failed', []):
                    print(f"  - {prof['professor_name']} (ID: {prof['professor_id']})")
            print(f"\nYou can retry failed professors with: --resume")

        print(f"{'='*60}\n")

        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Scopus data for all matched professors"
    )
    parser.add_argument('--matched-only', action='store_true', default=True,
                       help='Only fetch for matched professors (default: True)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last successful fetch')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print what would be fetched without actually fetching')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing data files')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay in seconds between requests (default: 2.0)')
    parser.add_argument('--no-abstracts', action='store_true',
                       help='Skip fetching abstracts (faster but less data)')

    args = parser.parse_args()

    # Find base path
    base_path = Path(__file__).parent.parent

    # Initialize fetcher
    fetcher = ScopusFetcher(base_path)
    fetcher.min_delay = args.delay  # Override default delay

    # Load matched professors
    matched_file = base_path / "scripts" / "matched_professors.json"

    if not matched_file.exists():
        print(f"❌ Error: matched_professors.json not found")
        print(f"   Run match_professors_to_scopus.py first")
        return 1

    # Fetch data
    try:
        results = fetcher.fetch_all(
            matched_file,
            resume=args.resume,
            force=args.force,
            dry_run=args.dry_run,
            fetch_abstracts=not args.no_abstracts
        )

        if results['failed'] > 0:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Fetch interrupted by user")
        print("Progress has been saved. Use --resume to continue.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
