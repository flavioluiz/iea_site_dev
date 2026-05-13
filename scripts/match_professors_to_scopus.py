#!/usr/bin/env python3
"""
Match EAM Professors to Scopus Author IDs

This script implements a 4-stage matching algorithm:
1. ORCID Match (100% confidence) - Exact ORCID matching
2. Name Match (90% confidence) - Normalized name comparison
3. LLM Fuzzy Match (70-95% confidence) - AI-assisted matching with research areas
4. Manual Review - For unmatched professors

Usage:
    python match_professors_to_scopus.py [--mode MODE] [--dry-run]

    --mode: orcid, name, llm, all (default: all)
    --dry-run: Don't save results, just print
    --verbose: Print detailed matching information
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unicodedata import normalize
import argparse

# Try to import OpenAI client for LLM matching
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  OpenAI library not installed. LLM matching will be disabled.")
    print("   Install with: pip install openai")


class ProfessorMatcher:
    """Matches EAM professors to Scopus author IDs"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.profiles_path = base_path / "data" / "professores" / "profiles"
        self.scripts_path = base_path / "scripts"

        # Load data
        self.professors = self._load_professors()
        self.ita_authors_orcid = self._load_json(self.scripts_path / "ita_authors_orcid.json")
        self.ita_authors_all = self._load_json(self.scripts_path / "ita_authors_all.json")

        # Results
        self.matched = []
        self.unmatched = []

    def _load_json(self, path: Path) -> List[Dict]:
        """Load JSON file"""
        if not path.exists():
            print(f"❌ File not found: {path}")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_professors(self) -> Dict[str, Dict]:
        """Load all professor profiles"""
        professors = {}
        for file in self.profiles_path.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                prof = json.load(f)
                professors[prof['id']] = prof
        return professors

    def _normalize_orcid(self, orcid: str) -> Optional[str]:
        """Extract clean ORCID from various formats

        Examples:
            "https://orcid.org/0000-0002-1617-9063" -> "0000-0002-1617-9063"
            "[0000-0002-1617-9063]" -> "0000-0002-1617-9063"
            "0000-0002-1617-9063" -> "0000-0002-1617-9063"
        """
        if not orcid:
            return None

        # Extract the ORCID pattern (0000-0000-0000-0000)
        match = re.search(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', orcid)
        if match:
            return match.group(0)
        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison

        - Remove accents
        - Lowercase
        - Remove extra spaces
        - Remove punctuation
        """
        if not name:
            return ""

        # Remove accents
        name = normalize('NFD', name).encode('ASCII', 'ignore').decode('utf-8')

        # Lowercase and remove extra spaces/punctuation
        name = re.sub(r'[^\w\s]', '', name.lower())
        name = ' '.join(name.split())

        return name

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score (0-1)

        Checks for:
        - Exact match after normalization
        - Surname match + initial match
        - Partial name matches
        """
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)

        if not n1 or not n2:
            return 0.0

        # Exact match
        if n1 == n2:
            return 1.0

        # Split into parts
        parts1 = n1.split()
        parts2 = n2.split()

        # Check if one is contained in the other
        if n1 in n2 or n2 in n1:
            return 0.9

        # Check surname match (usually last part)
        if parts1 and parts2 and parts1[-1] == parts2[-1]:
            score = 0.7
            # Bonus for first name initial match
            if parts1[0][0] == parts2[0][0]:
                score += 0.2
            return min(score, 1.0)

        # Count matching words
        matching_words = len(set(parts1) & set(parts2))
        total_words = max(len(parts1), len(parts2))

        if total_words > 0:
            return matching_words / total_words

        return 0.0

    def stage1_orcid_match(self, verbose: bool = False) -> List[Dict]:
        """Stage 1: ORCID matching (100% confidence)"""
        if verbose:
            print("\n" + "="*60)
            print("STAGE 1: ORCID MATCHING")
            print("="*60)

        matches = []

        # Create ORCID index for fast lookup
        orcid_index = {}
        for author in self.ita_authors_orcid:
            orcid = self._normalize_orcid(author.get('orcid', ''))
            if orcid:
                orcid_index[orcid] = author

        if verbose:
            print(f"Indexed {len(orcid_index)} authors with ORCID from ITA database")

        # Match professors
        for prof_id, prof in self.professors.items():
            prof_orcid = self._normalize_orcid(prof.get('links', {}).get('orcid', ''))

            if prof_orcid and prof_orcid in orcid_index:
                author = orcid_index[prof_orcid]
                match = {
                    "professor_id": prof_id,
                    "professor_name": prof['nome'],
                    "scopus_author_id": str(author['author_id']),
                    "orcid": prof_orcid,
                    "match_method": "orcid",
                    "confidence": 100,
                    "author_details": {
                        "name": f"{author.get('given_name', '')} {author.get('surname', '')}".strip(),
                        "document_count": author.get('document_count', 0),
                        "subject_areas": author.get('subject_areas', [])
                    }
                }
                matches.append(match)

                if verbose:
                    print(f"\n✓ MATCH: {prof['nome']}")
                    print(f"  ORCID: {prof_orcid}")
                    print(f"  Scopus ID: {author['author_id']}")
                    print(f"  Documents: {author.get('document_count', 0)}")

        if verbose:
            print(f"\n{'-'*60}")
            print(f"Stage 1 Results: {len(matches)} matches")
            print(f"{'-'*60}")

        return matches

    def stage2_name_match(self, already_matched: List[str], verbose: bool = False) -> List[Dict]:
        """Stage 2: Name matching (90% confidence)"""
        if verbose:
            print("\n" + "="*60)
            print("STAGE 2: NAME MATCHING")
            print("="*60)

        matches = []
        matched_professor_ids = set(already_matched)

        for prof_id, prof in self.professors.items():
            if prof_id in matched_professor_ids:
                continue

            prof_name = prof['nome']
            best_match = None
            best_score = 0.0

            # Try matching against all ITA authors
            for author in self.ita_authors_all:
                # Build author name variations
                author_full = f"{author.get('given_name', '')} {author.get('surname', '')}".strip()
                author_reversed = f"{author.get('surname', '')} {author.get('given_name', '')}".strip()
                author_initials = f"{author.get('initials', '')} {author.get('surname', '')}".strip()

                # Calculate similarities
                scores = [
                    self._name_similarity(prof_name, author_full),
                    self._name_similarity(prof_name, author_reversed),
                    self._name_similarity(prof_name, author_initials),
                ]

                max_score = max(scores)

                if max_score > best_score:
                    best_score = max_score
                    best_match = author

            # Only accept matches with high confidence (> 0.85)
            if best_match and best_score >= 0.85:
                match = {
                    "professor_id": prof_id,
                    "professor_name": prof_name,
                    "scopus_author_id": str(best_match['author_id']),
                    "orcid": self._normalize_orcid(best_match.get('orcid', '')),
                    "match_method": "name",
                    "confidence": int(best_score * 100),
                    "author_details": {
                        "name": f"{best_match.get('given_name', '')} {best_match.get('surname', '')}".strip(),
                        "document_count": best_match.get('document_count', 0),
                        "subject_areas": best_match.get('subject_areas', [])
                    }
                }
                matches.append(match)
                matched_professor_ids.add(prof_id)

                if verbose:
                    print(f"\n✓ MATCH: {prof_name}")
                    print(f"  Matched to: {match['author_details']['name']}")
                    print(f"  Confidence: {best_score:.0%}")
                    print(f"  Scopus ID: {best_match['author_id']}")
                    print(f"  Documents: {best_match.get('document_count', 0)}")

        if verbose:
            print(f"\n{'-'*60}")
            print(f"Stage 2 Results: {len(matches)} matches")
            print(f"{'-'*60}")

        return matches

    def stage3_llm_match(self, already_matched: List[str], verbose: bool = False) -> List[Dict]:
        """Stage 3: LLM-assisted fuzzy matching (70-95% confidence)"""
        if not HAS_OPENAI:
            if verbose:
                print("\n⚠️  Skipping Stage 3: OpenAI library not installed")
            return []

        if not os.getenv('SYNTHETIC_API_KEY'):
            if verbose:
                print("\n⚠️  Skipping Stage 3: SYNTHETIC_API_KEY not set")
            return []

        if verbose:
            print("\n" + "="*60)
            print("STAGE 3: LLM FUZZY MATCHING")
            print("="*60)

        matches = []
        matched_professor_ids = set(already_matched)

        # Initialize OpenAI client for Synthetic API
        client = OpenAI(
            api_key=os.getenv('SYNTHETIC_API_KEY'),
            base_url="https://api.synthetic.new/openai/v1"
        )

        for prof_id, prof in self.professors.items():
            if prof_id in matched_professor_ids:
                continue

            # Find candidate authors (top 5 by name similarity)
            candidates = []
            for author in self.ita_authors_all:
                author_name = f"{author.get('given_name', '')} {author.get('surname', '')}".strip()
                score = self._name_similarity(prof['nome'], author_name)

                if score > 0.3:  # Minimum threshold
                    candidates.append((author, score))

            # Sort by score and take top 5
            candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = candidates[:5]

            if not candidates:
                continue

            # Prepare LLM prompt
            prof_name = prof['nome']
            prof_research = prof.get('linhas_pesquisa', {}).get('pt', [])

            candidates_text = "\n".join([
                f"{i+1}. ID: {c[0]['author_id']} | Name: {c[0].get('given_name', '')} {c[0].get('surname', '')} | "
                f"Documents: {c[0].get('document_count', 0)} | "
                f"Areas: {', '.join(c[0].get('subject_areas', [])[:3])}"
                for i, (c, _) in enumerate(candidates)
            ])

            prompt = f"""You are matching a professor to their Scopus author profile.

Professor Information:
- Name: {prof_name}
- Research Lines: {', '.join(prof_research) if prof_research else 'Not specified'}

Candidate Scopus Authors:
{candidates_text}

Task: Identify which candidate is most likely the same person as the professor.
Consider:
- Name similarity (accounting for different name orders, initials, etc.)
- Research area alignment
- Document count (should be reasonable for a professor)

Respond with ONLY a JSON object in this format:
{{
    "match_id": <candidate number 1-5, or null if no good match>,
    "confidence": <0-100>,
    "reasoning": "<brief explanation>"
}}"""

            if verbose:
                print(f"\n🤖 Querying LLM for: {prof_name}")

            try:
                response = client.chat.completions.create(
                    model="hf:Qwen/Qwen3-235B-A22B-Instruct-2507",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=200
                )

                result_text = response.choices[0].message.content.strip()

                # Extract JSON from response (handle markdown code blocks)
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()

                result = json.loads(result_text)

                match_idx = result.get('match_id')
                confidence = result.get('confidence', 0)
                reasoning = result.get('reasoning', '')

                if match_idx and 1 <= match_idx <= len(candidates) and confidence >= 70:
                    author = candidates[match_idx - 1][0]

                    match = {
                        "professor_id": prof_id,
                        "professor_name": prof_name,
                        "scopus_author_id": str(author['author_id']),
                        "orcid": self._normalize_orcid(author.get('orcid', '')),
                        "match_method": "llm",
                        "confidence": confidence,
                        "llm_reasoning": reasoning,
                        "author_details": {
                            "name": f"{author.get('given_name', '')} {author.get('surname', '')}".strip(),
                            "document_count": author.get('document_count', 0),
                            "subject_areas": author.get('subject_areas', [])
                        }
                    }
                    matches.append(match)
                    matched_professor_ids.add(prof_id)

                    if verbose:
                        print(f"  ✓ MATCH: {match['author_details']['name']}")
                        print(f"  Confidence: {confidence}%")
                        print(f"  Reasoning: {reasoning}")
                else:
                    if verbose:
                        print(f"  ✗ No confident match (confidence: {confidence}%)")

            except Exception as e:
                if verbose:
                    print(f"  ❌ LLM query failed: {e}")
                continue

        if verbose:
            print(f"\n{'-'*60}")
            print(f"Stage 3 Results: {len(matches)} matches")
            print(f"{'-'*60}")

        return matches

    def stage4_manual_review(self, already_matched: List[str]) -> List[Dict]:
        """Stage 4: Generate manual review report for unmatched professors"""
        unmatched = []
        matched_professor_ids = set(already_matched)

        for prof_id, prof in self.professors.items():
            if prof_id in matched_professor_ids:
                continue

            # Find top 3 candidates by name similarity
            candidates = []
            for author in self.ita_authors_all:
                author_name = f"{author.get('given_name', '')} {author.get('surname', '')}".strip()
                score = self._name_similarity(prof['nome'], author_name)

                if score > 0.2:
                    subject_areas = author.get('subject_areas') or []
                    candidates.append({
                        "author_id": str(author['author_id']),
                        "name": author_name,
                        "confidence": int(score * 100),
                        "document_count": author.get('document_count', 0),
                        "subject_areas": subject_areas[:5] if subject_areas else [],
                        "orcid": self._normalize_orcid(author.get('orcid', ''))
                    })

            # Sort by confidence
            candidates.sort(key=lambda x: x['confidence'], reverse=True)
            candidates = candidates[:3]

            unmatched.append({
                "professor_id": prof_id,
                "professor_name": prof['nome'],
                "research_lines": prof.get('linhas_pesquisa', {}).get('pt', []),
                "candidates": candidates,
                "requires_manual_review": True
            })

        return unmatched

    def run_matching(self, mode: str = "all", verbose: bool = False) -> Dict:
        """Run the matching process"""
        matched_ids = []

        if mode in ["orcid", "all"]:
            orcid_matches = self.stage1_orcid_match(verbose=verbose)
            self.matched.extend(orcid_matches)
            matched_ids.extend([m['professor_id'] for m in orcid_matches])

        if mode in ["name", "all"]:
            name_matches = self.stage2_name_match(matched_ids, verbose=verbose)
            self.matched.extend(name_matches)
            matched_ids.extend([m['professor_id'] for m in name_matches])

        if mode in ["llm", "all"]:
            llm_matches = self.stage3_llm_match(matched_ids, verbose=verbose)
            self.matched.extend(llm_matches)
            matched_ids.extend([m['professor_id'] for m in llm_matches])

        # Always run stage 4 for remaining unmatched
        self.unmatched = self.stage4_manual_review(matched_ids)

        # Calculate statistics
        stats = {
            "total": len(self.professors),
            "matched": len(self.matched),
            "unmatched": len(self.unmatched),
            "orcid_matches": len([m for m in self.matched if m['match_method'] == 'orcid']),
            "name_matches": len([m for m in self.matched if m['match_method'] == 'name']),
            "llm_matches": len([m for m in self.matched if m['match_method'] == 'llm']),
            "coverage_pct": (len(self.matched) / len(self.professors) * 100) if self.professors else 0
        }

        return {
            "matched": self.matched,
            "unmatched": self.unmatched,
            "statistics": stats
        }

    def save_results(self, output_path: Path):
        """Save matching results to JSON"""
        results = {
            "matched": self.matched,
            "unmatched": self.unmatched,
            "statistics": {
                "total": len(self.professors),
                "matched": len(self.matched),
                "unmatched": len(self.unmatched),
                "orcid_matches": len([m for m in self.matched if m['match_method'] == 'orcid']),
                "name_matches": len([m for m in self.matched if m['match_method'] == 'name']),
                "llm_matches": len([m for m in self.matched if m['match_method'] == 'llm']),
                "coverage_pct": (len(self.matched) / len(self.professors) * 100) if self.professors else 0
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results


def print_summary(results: Dict):
    """Print summary of matching results"""
    stats = results['statistics']

    print("\n" + "="*60)
    print("MATCHING SUMMARY")
    print("="*60)
    print(f"\nTotal Professors: {stats['total']}")
    print(f"✓ Matched: {stats['matched']} ({stats['coverage_pct']:.1f}%)")
    print(f"✗ Unmatched: {stats['unmatched']}")
    print(f"\nMatching Breakdown:")
    print(f"  - ORCID matches: {stats['orcid_matches']}")
    print(f"  - Name matches: {stats['name_matches']}")
    print(f"  - LLM matches: {stats['llm_matches']}")

    if results['unmatched']:
        print(f"\n⚠️  MANUAL REVIEW REQUIRED for {len(results['unmatched'])} professors:")
        for u in results['unmatched']:
            print(f"\n  Professor: {u['professor_name']} (ID: {u['professor_id']})")
            print(f"  Research: {', '.join(u['research_lines'][:2]) if u['research_lines'] else 'N/A'}")
            if u['candidates']:
                print(f"  Top candidate: {u['candidates'][0]['name']} (Scopus: {u['candidates'][0]['author_id']}, {u['candidates'][0]['confidence']}% confidence)")
            else:
                print(f"  No candidates found")

    if stats['coverage_pct'] == 100:
        print("\n🎉 SUCCESS! All professors matched to Scopus IDs!")
    else:
        print(f"\n⚠️  Need to resolve {stats['unmatched']} unmatched professors before proceeding.")
        print("   Options:")
        print("   1. Review candidates above and manually assign Scopus IDs")
        print("   2. Use manual_scopus_entry.py to enter IDs")
        print("   3. Search Scopus manually for these professors")

    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Match EAM professors to Scopus author IDs")
    parser.add_argument('--mode', choices=['orcid', 'name', 'llm', 'all'], default='all',
                       help='Matching mode (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without saving results')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print detailed matching information')
    parser.add_argument('--output', '-o', default='matched_professors.json',
                       help='Output file path (default: matched_professors.json)')

    args = parser.parse_args()

    # Find base path (assume we're in scripts/ directory)
    base_path = Path(__file__).parent.parent

    # Initialize matcher
    matcher = ProfessorMatcher(base_path)

    print(f"Loaded {len(matcher.professors)} professors")
    print(f"ITA authors with ORCID: {len(matcher.ita_authors_orcid)}")
    print(f"ITA authors total: {len(matcher.ita_authors_all)}")

    # Run matching
    results = matcher.run_matching(mode=args.mode, verbose=args.verbose)

    # Save results
    if not args.dry_run:
        output_path = base_path / "scripts" / args.output
        matcher.save_results(output_path)
        print(f"\n💾 Results saved to: {output_path}")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
