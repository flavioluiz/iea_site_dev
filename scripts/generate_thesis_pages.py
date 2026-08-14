#!/usr/bin/env python3
"""
Generate thesis pages and data structures from tesesdigitais_eam.json.

This script processes the large thesis database and creates:
1. Individual thesis JSON files in data/teses/by_id/
2. A lightweight index for search (data/teses/index.json)
3. A professor-to-thesis mapping (data/teses/by_professor.json)
4. Statistics file (data/teses/statistics.json)
5. Content markdown files for Hugo pages

Interactive mode allows manual verification and correction of advisor matches.
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TESES_DATA_DIR = DATA_DIR / "teses"
CONTENT_DIR = BASE_DIR / "content" / "teses"
PROFESSORS_DIR = DATA_DIR / "professores" / "profiles"
MANUAL_MATCHES_FILE = DATA_DIR / "teses" / "manual_matches.json"

# Common Brazilian last names that require stricter matching
COMMON_LAST_NAMES = {
    'silva', 'santos', 'oliveira', 'souza', 'rodrigues', 'ferreira', 'alves',
    'pereira', 'lima', 'gomes', 'costa', 'ribeiro', 'martins', 'carvalho',
    'almeida', 'lopes', 'soares', 'fernandes', 'vieira', 'barbosa', 'rocha',
    'dias', 'nascimento', 'andrade', 'moreira', 'nunes', 'marques', 'machado',
    'mendes', 'freitas', 'cardoso', 'ramos', 'goncalves', 'santana', 'teixeira',
    'neto', 'junior', 'filho', 'sobrinho'
}

# Common first names to exclude from matching
COMMON_FIRST_NAMES = {
    'jose', 'joao', 'maria', 'antonio', 'pedro', 'rodrigo', 'carlos',
    'paulo', 'luis', 'luiz', 'marcos', 'marcelo', 'andre', 'rafael',
    'fernando', 'roberto', 'sergio', 'gilberto', 'amauri'
}

# Prepositions to ignore
PREPOSITIONS = {'de', 'da', 'do', 'dos', 'das', 'e'}


def normalize_name(name: str) -> str:
    """Normalize a name for comparison by removing accents, lowercasing, etc."""
    if not name:
        return ""
    normalized = unicodedata.normalize('NFKD', name)
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = normalized.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def name_to_slug(name: str) -> str:
    """Convert a name to a slug format."""
    slug = normalize_name(name)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug


def get_name_parts(name: str) -> dict:
    """Extract meaningful parts from a name."""
    parts = normalize_name(name).split()
    if not parts:
        return {'first': '', 'last': '', 'all': set(), 'full': ''}

    return {
        'first': parts[0],
        'last': parts[-1],
        'second_to_last': parts[-2] if len(parts) > 1 else '',
        'all': set(parts),
        'full': ' '.join(parts)
    }


def load_professors():
    """Load all professors and create structured data for matching."""
    professors = {}
    professor_names = {}

    if not PROFESSORS_DIR.exists():
        print(f"Warning: Professors directory not found: {PROFESSORS_DIR}")
        return professors, professor_names

    for prof_file in PROFESSORS_DIR.glob("*.json"):
        with open(prof_file, 'r', encoding='utf-8') as f:
            prof = json.load(f)

        prof_id = prof.get('id') or prof.get('slug') or prof_file.stem
        professors[prof_id] = prof

        full_name = prof.get('nome', '')
        if full_name:
            professor_names[prof_id] = {
                'full_name': full_name,
                'normalized': normalize_name(full_name),
                'parts': get_name_parts(full_name),
                'destaque': normalize_name(prof.get('nome_destaque', ''))
            }

    return professors, professor_names


def calculate_name_similarity(advisor_parts: dict, prof_data: dict) -> float:
    """
    Calculate similarity score between advisor name and professor name.
    Returns a score between 0 and 1, where 1 is a perfect match.
    """
    prof_parts = prof_data['parts']

    # Exact full name match
    if advisor_parts['full'] == prof_parts['full']:
        return 1.0

    # Check if advisor name is contained in professor name or vice versa
    if advisor_parts['full'] in prof_data['normalized'] or prof_data['normalized'] in advisor_parts['full']:
        common_parts = advisor_parts['all'] & prof_parts['all']
        meaningful = common_parts - COMMON_LAST_NAMES - PREPOSITIONS - COMMON_FIRST_NAMES
        if len(meaningful) >= 1:
            return 0.95

    # First name MUST match for any further checks
    if advisor_parts['first'] != prof_parts['first']:
        return 0.0

    # First name + last name match (last name must be distinctive)
    if advisor_parts['last'] == prof_parts['last']:
        if advisor_parts['last'] not in COMMON_LAST_NAMES and advisor_parts['last'] not in COMMON_FIRST_NAMES:
            return 0.9
        common_parts = advisor_parts['all'] & prof_parts['all']
        meaningful = common_parts - COMMON_LAST_NAMES - PREPOSITIONS - COMMON_FIRST_NAMES
        if len(meaningful) >= 1:
            return 0.85

    # First name + second-to-last name match
    if (advisor_parts['second_to_last'] and
        advisor_parts['second_to_last'] == prof_parts['last'] and
        advisor_parts['second_to_last'] not in COMMON_LAST_NAMES and
        advisor_parts['second_to_last'] not in COMMON_FIRST_NAMES):
        return 0.85

    # Check nome_destaque (ignore if it's just the first name)
    if prof_data['destaque']:
        destaque_normalized = normalize_name(prof_data['destaque'])
        if (destaque_normalized != prof_parts['first'] and
            destaque_normalized not in COMMON_FIRST_NAMES and
            destaque_normalized not in COMMON_LAST_NAMES):
            destaque_parts = set(destaque_normalized.split())
            advisor_distinctive = advisor_parts['all'] - PREPOSITIONS - COMMON_LAST_NAMES - COMMON_FIRST_NAMES
            if destaque_parts & advisor_distinctive:
                return 0.85

    # Count matching name parts
    common_parts = advisor_parts['all'] & prof_parts['all']
    meaningful_common = common_parts - COMMON_LAST_NAMES - PREPOSITIONS - COMMON_FIRST_NAMES

    if len(meaningful_common) >= 2:
        return 0.8

    return 0.0


def auto_match_advisor(advisor_name: str, professor_names: dict, threshold: float = 0.7) -> tuple[str | None, float]:
    """
    Try to automatically match an advisor name to a professor ID.
    Returns (professor_id, score) or (None, 0.0) if no match.
    """
    if not advisor_name:
        return None, 0.0

    advisor_parts = get_name_parts(advisor_name)
    best_match = None
    best_score = 0.0

    for prof_id, prof_data in professor_names.items():
        score = calculate_name_similarity(advisor_parts, prof_data)
        if score > best_score:
            best_score = score
            best_match = prof_id

    if best_score >= threshold:
        return best_match, best_score

    return None, 0.0


def load_manual_matches() -> dict:
    """Load manually verified matches from file."""
    if MANUAL_MATCHES_FILE.exists():
        with open(MANUAL_MATCHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_manual_matches(matches: dict):
    """Save manually verified matches to file."""
    MANUAL_MATCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANUAL_MATCHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)


def extract_all_advisors(theses: list) -> dict:
    """Extract all unique advisor names from theses with their thesis count."""
    advisor_counts = defaultdict(lambda: {'count': 0, 'as_advisor': 0, 'as_coadvisor': 0})

    for thesis in theses:
        fields = thesis.get('fields', {})
        advisors = fields.get('advisors', [])

        # First advisor is main advisor, rest are co-advisors
        for i, advisor in enumerate(advisors):
            if advisor:
                advisor_counts[advisor]['count'] += 1
                if i == 0:
                    advisor_counts[advisor]['as_advisor'] += 1
                else:
                    advisor_counts[advisor]['as_coadvisor'] += 1

    return dict(advisor_counts)


def interactive_matching(advisors: dict, professor_names: dict, professors: dict, manual_matches: dict) -> dict:
    """
    Interactive session for verifying and correcting advisor matches.
    Returns the final mapping of advisor_name -> professor_id (or None).
    """
    # Build initial matches (manual overrides auto)
    matches = {}
    auto_matches = {}

    for advisor_name in advisors:
        if advisor_name in manual_matches:
            matches[advisor_name] = manual_matches[advisor_name]
        else:
            prof_id, score = auto_match_advisor(advisor_name, professor_names)
            auto_matches[advisor_name] = (prof_id, score)
            matches[advisor_name] = prof_id

    # Sort advisors by count (most theses first)
    sorted_advisors = sorted(advisors.items(), key=lambda x: -x[1]['count'])

    # Create professor list for selection
    prof_list = sorted(professors.keys())
    prof_by_num = {i+1: pid for i, pid in enumerate(prof_list)}

    while True:
        # Display current state
        print("\n" + "="*80)
        print("ADVISOR MATCHING - Interactive Verification")
        print("="*80)
        print(f"\nTotal unique advisors: {len(advisors)}")
        print(f"Matched to current professors: {sum(1 for v in matches.values() if v)}")
        print(f"Unmatched (external/retired): {sum(1 for v in matches.values() if not v)}")
        print("\n" + "-"*80)
        print(f"{'#':<4} {'Advisor Name':<40} {'Match':<30} {'Theses':<8}")
        print("-"*80)

        for i, (advisor_name, stats) in enumerate(sorted_advisors, 1):
            match = matches.get(advisor_name)
            if match:
                prof_name = professors[match].get('nome', match)[:28]
                match_str = f"→ {prof_name}"
                # Mark if it was manual or auto
                if advisor_name in manual_matches:
                    match_str += " [M]"
                elif auto_matches.get(advisor_name, (None, 0))[1] >= 0.9:
                    match_str += " [A]"
                else:
                    match_str += " [a]"
            else:
                match_str = "(unmatched)"

            count_str = f"{stats['count']} ({stats['as_advisor']}+{stats['as_coadvisor']})"
            print(f"{i:<4} {advisor_name[:38]:<40} {match_str:<30} {count_str:<8}")

        print("-"*80)
        print("\nLegend: [M]=manual, [A]=auto (high confidence), [a]=auto (low confidence)")
        print("\nCommands:")
        print("  <number>  - Edit match for advisor #number")
        print("  f <text>  - Find/filter advisors by name (e.g., 'f silva')")
        print("  p         - Show PROFESSOR view (professors with their matched advisors)")
        print("  u         - Show professors with NO supervisions (potential missing matches)")
        print("  s         - Save current matches and continue to generation")
        print("  q         - Quit without generating (matches are saved)")
        print("  ?         - Show professor list")

        cmd = input("\nEnter command: ").strip()

        cmd_lower = cmd.lower()

        if cmd_lower == 's':
            # Save and continue
            save_manual_matches(matches)
            print("\nMatches saved. Continuing to thesis generation...")
            return matches

        elif cmd_lower == 'q':
            save_manual_matches(matches)
            print("\nMatches saved. Exiting without generation.")
            sys.exit(0)

        elif cmd_lower.startswith('f '):
            # Find/filter advisors by name
            search_term = normalize_name(cmd[2:])
            if not search_term:
                print("Please provide a search term. Example: f silva")
                continue

            print(f"\n--- Searching for '{cmd[2:]}' ---")
            found = []
            for i, (advisor_name, stats) in enumerate(sorted_advisors, 1):
                if search_term in normalize_name(advisor_name):
                    match = matches.get(advisor_name)
                    if match:
                        prof_name = professors[match].get('nome', match)
                        match_str = f"→ {prof_name}"
                    else:
                        match_str = "(unmatched)"
                    found.append((i, advisor_name, match_str, stats))

            if found:
                print(f"\nFound {len(found)} advisors matching '{cmd[2:]}':\n")
                print(f"{'#':<4} {'Advisor Name':<40} {'Match':<30} {'Theses':<8}")
                print("-"*80)
                for idx, name, match_str, stats in found:
                    count_str = f"{stats['count']} ({stats['as_advisor']}+{stats['as_coadvisor']})"
                    print(f"{idx:<4} {name[:38]:<40} {match_str[:28]:<30} {count_str:<8}")
                print("-"*80)
                print("\nUse the # to edit a match (e.g., type '42' to edit advisor #42)")
            else:
                print(f"No advisors found matching '{cmd[2:]}'")

            input("\nPress Enter to continue...")

        elif cmd_lower == 'p':
            # Show professor view - all professors with their matched advisors
            print("\n" + "="*90)
            print("PROFESSOR VIEW - Professors with their matched advisor names")
            print("="*90)

            # Build reverse mapping: professor_id -> list of matched advisor names
            prof_to_advisors = defaultdict(list)
            for advisor_name, prof_id in matches.items():
                if prof_id:
                    stats = advisors[advisor_name]
                    prof_to_advisors[prof_id].append({
                        'name': advisor_name,
                        'count': stats['count'],
                        'as_advisor': stats['as_advisor'],
                        'as_coadvisor': stats['as_coadvisor']
                    })

            # Sort professors by total thesis count
            prof_with_counts = []
            for prof_id in professors:
                advisor_list = prof_to_advisors.get(prof_id, [])
                total_theses = sum(a['count'] for a in advisor_list)
                total_as_advisor = sum(a['as_advisor'] for a in advisor_list)
                total_as_coadvisor = sum(a['as_coadvisor'] for a in advisor_list)
                prof_with_counts.append((prof_id, advisor_list, total_theses, total_as_advisor, total_as_coadvisor))

            prof_with_counts.sort(key=lambda x: -x[2])  # Sort by total theses descending

            print(f"\n{'#':<4} {'Professor':<35} {'Theses':<12} {'Matched Advisor Names'}")
            print("-"*90)

            for i, (prof_id, advisor_list, total, as_adv, as_coadv) in enumerate(prof_with_counts, 1):
                prof_name = professors[prof_id].get('nome', prof_id)[:33]
                count_str = f"{total} ({as_adv}+{as_coadv})" if total > 0 else "0"

                if advisor_list:
                    # Show first advisor name, indicate if there are more
                    names = [a['name'] for a in advisor_list]
                    if len(names) == 1:
                        names_str = names[0][:30]
                    else:
                        names_str = f"{names[0][:20]}... (+{len(names)-1} more)"
                else:
                    names_str = "(no matches)"

                print(f"{i:<4} {prof_name:<35} {count_str:<12} {names_str}")

            print("-"*90)
            print(f"\nProfessors with supervisions: {sum(1 for p in prof_with_counts if p[2] > 0)}/{len(professors)}")
            print(f"Professors without supervisions: {sum(1 for p in prof_with_counts if p[2] == 0)}")

            # Option to view details of a professor
            while True:
                choice = input("\nEnter professor # for details, or press Enter to go back: ").strip()
                if not choice:
                    break
                if choice.isdigit():
                    pnum = int(choice)
                    if 1 <= pnum <= len(prof_with_counts):
                        prof_id, advisor_list, total, as_adv, as_coadv = prof_with_counts[pnum-1]
                        prof_name = professors[prof_id].get('nome', prof_id)
                        print(f"\n--- {prof_name} ---")
                        print(f"Total theses: {total} (as advisor: {as_adv}, as co-advisor: {as_coadv})")
                        if advisor_list:
                            print("\nMatched advisor names:")
                            for a in sorted(advisor_list, key=lambda x: -x['count']):
                                print(f"  - {a['name']} ({a['count']} theses: {a['as_advisor']} adv + {a['as_coadvisor']} coadv)")
                        else:
                            print("\nNo advisor names matched to this professor.")
                            print("This could mean:")
                            print("  - Professor recently joined the program")
                            print("  - Advisor names in database don't match (check spelling variations)")
                    else:
                        print(f"Invalid number. Use 1-{len(prof_with_counts)}")

        elif cmd_lower == 'u':
            # Show professors with NO supervisions
            print("\n" + "="*70)
            print("PROFESSORS WITHOUT SUPERVISIONS")
            print("="*70)

            # Build reverse mapping
            prof_to_advisors = defaultdict(list)
            for advisor_name, prof_id in matches.items():
                if prof_id:
                    prof_to_advisors[prof_id].append(advisor_name)

            unmatched_profs = []
            for prof_id in professors:
                if prof_id not in prof_to_advisors:
                    prof_name = professors[prof_id].get('nome', prof_id)
                    unmatched_profs.append((prof_id, prof_name))

            if unmatched_profs:
                print(f"\nFound {len(unmatched_profs)} professors with no matched supervisions:\n")
                for i, (prof_id, prof_name) in enumerate(sorted(unmatched_profs, key=lambda x: x[1]), 1):
                    print(f"  {i:>3}. {prof_name}")

                print("\n" + "-"*70)
                print("These professors have no advisor names matched to them.")
                print("Possible reasons:")
                print("  - Recently joined the program (no thesis students yet)")
                print("  - Name variations in the database (check for spelling differences)")
                print("  - External advisors with similar names taking precedence")
                print("\nTo fix: search for their name variations in the advisor list (main view)")
            else:
                print("\nAll professors have at least one matched supervision!")

            input("\nPress Enter to continue...")

        elif cmd_lower == '?':
            # Show professor list
            print("\n" + "="*60)
            print("PROFESSORS IN THE PROGRAM")
            print("="*60)
            for num, prof_id in prof_by_num.items():
                prof_name = professors[prof_id].get('nome', prof_id)
                print(f"  {num:>3}. {prof_name}")
            print("="*60)
            input("\nPress Enter to continue...")

        elif cmd_lower.isdigit():
            num = int(cmd)
            if 1 <= num <= len(sorted_advisors):
                advisor_name = sorted_advisors[num-1][0]
                stats = sorted_advisors[num-1][1]
                current_match = matches.get(advisor_name)

                print(f"\n--- Editing: {advisor_name} ---")
                print(f"Theses: {stats['count']} (as advisor: {stats['as_advisor']}, as co-advisor: {stats['as_coadvisor']})")
                if current_match:
                    print(f"Current match: {professors[current_match].get('nome', current_match)}")
                else:
                    print("Current match: (none)")

                # Show auto-match suggestion if different from current
                auto_prof, auto_score = auto_match_advisor(advisor_name, professor_names)
                if auto_prof and auto_prof != current_match:
                    print(f"Auto-suggestion: {professors[auto_prof].get('nome', auto_prof)} (score: {auto_score:.2f})")

                print("\nOptions:")
                print("  <number>  - Match to professor #number (use '?' to see list)")
                print("  0         - Mark as unmatched (external/retired advisor)")
                print("  a         - Accept auto-suggestion")
                print("  k         - Keep current match")
                print("  ?         - Show professor list")

                while True:
                    choice = input("Choice: ").strip().lower()

                    if choice == 'k':
                        break
                    elif choice == '?':
                        print("\nProfessors:")
                        for num, prof_id in prof_by_num.items():
                            prof_name = professors[prof_id].get('nome', prof_id)
                            print(f"  {num:>3}. {prof_name}")
                    elif choice == '0':
                        matches[advisor_name] = None
                        manual_matches[advisor_name] = None
                        print(f"Marked as unmatched.")
                        break
                    elif choice == 'a' and auto_prof:
                        matches[advisor_name] = auto_prof
                        manual_matches[advisor_name] = auto_prof
                        print(f"Matched to: {professors[auto_prof].get('nome', auto_prof)}")
                        break
                    elif choice.isdigit():
                        pnum = int(choice)
                        if pnum in prof_by_num:
                            prof_id = prof_by_num[pnum]
                            matches[advisor_name] = prof_id
                            manual_matches[advisor_name] = prof_id
                            print(f"Matched to: {professors[prof_id].get('nome', prof_id)}")
                            break
                        else:
                            print(f"Invalid professor number. Use 1-{len(prof_list)} or '?' to see list.")
                    else:
                        print("Invalid choice.")
            else:
                print(f"Invalid number. Use 1-{len(sorted_advisors)}.")
        else:
            print("Invalid command. Use a number, 's', 'q', or '?'.")


def create_lightweight_index_entry(thesis: dict) -> dict:
    """Create a lightweight index entry for search purposes."""
    fields = thesis.get('fields', {})

    return {
        'id': thesis.get('num_tese', ''),
        't': fields.get('title', '')[:200],
        'a': fields.get('author', ''),
        'y': fields.get('year', ''),
        'c': 'M' if 'Mestrado' in fields.get('course', '') else 'D',
        'ar': fields.get('area_concentration', ''),
        'ad': fields.get('advisors', [])[:3],
        'kw': fields.get('subjects', [])[:5],
    }


def create_individual_thesis_file(thesis: dict, advisor_mapping: dict) -> dict:
    """Create a complete individual thesis data file."""
    fields = thesis.get('fields', {})

    advisors_with_ids = []
    for advisor in fields.get('advisors', []):
        prof_id = advisor_mapping.get(advisor)
        advisors_with_ids.append({
            'name': advisor,
            'professor_id': prof_id
        })

    return {
        'num_tese': thesis.get('num_tese', ''),
        'title': fields.get('title', ''),
        'author': fields.get('author', ''),
        'year': fields.get('year', ''),
        'course': fields.get('course', ''),
        'area_concentration': fields.get('area_concentration', ''),
        'advisors': advisors_with_ids,
        'abstract': fields.get('abstract', ''),
        'subjects': fields.get('subjects', []),
        'defense_date': fields.get('defense_date', ''),
        'url': thesis.get('url', ''),
        'pdf_url': fields.get('pdf_url', '')
    }


def create_thesis_markdown(thesis: dict, lang: str) -> str:
    """Create markdown content for a thesis page."""
    fields = thesis.get('fields', {})
    num_tese = thesis.get('num_tese', '')
    title = fields.get('title', '')

    # Escape quotes in title for YAML
    title_escaped = title.replace('"', '\\"')

    if lang == 'pt':
        content = f'''---
title: "{title_escaped}"
type: "teses"
layout: "single"
thesis_id: "{num_tese}"
---
'''
    else:
        content = f'''---
title: "{title_escaped}"
type: "teses"
layout: "single"
thesis_id: "{num_tese}"
---
'''
    return content


def generate_thesis_pages(theses: list, advisor_mapping: dict, metadata: dict = None):
    """Generate all thesis-related files."""
    # Create directories
    TESES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (TESES_DATA_DIR / "by_id").mkdir(exist_ok=True)
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Build indexes
    index_entries = []
    by_professor = defaultdict(lambda: {
        'as_advisor': [],
        'as_coadvisor': [],
        'mestrado_count': 0,
        'doutorado_count': 0
    })

    stats = {
        'total': 0,
        'mestrado': 0,
        'doutorado': 0,
        'by_year': defaultdict(int),
        'by_area': defaultdict(int),
    }
    if metadata and metadata.get('generated_at'):
        stats['last_updated'] = metadata['generated_at']

    print("Processing theses...")
    for i, thesis in enumerate(theses, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(theses)} theses...")

        num_tese = thesis.get('num_tese', '')
        if not num_tese:
            continue

        fields = thesis.get('fields', {})

        # Create individual thesis data file
        thesis_data = create_individual_thesis_file(thesis, advisor_mapping)
        with open(TESES_DATA_DIR / "by_id" / f"{num_tese}.json", 'w', encoding='utf-8') as f:
            json.dump(thesis_data, f, ensure_ascii=False, indent=2)

        # Add to lightweight index
        index_entries.append(create_lightweight_index_entry(thesis))

        # Update professor mapping
        advisors = fields.get('advisors', [])
        is_mestrado = 'Mestrado' in fields.get('course', '')

        for j, advisor in enumerate(advisors):
            prof_id = advisor_mapping.get(advisor)
            if prof_id:
                if j == 0:
                    by_professor[prof_id]['as_advisor'].append(num_tese)
                    if is_mestrado:
                        by_professor[prof_id]['mestrado_count'] += 1
                    else:
                        by_professor[prof_id]['doutorado_count'] += 1
                else:
                    by_professor[prof_id]['as_coadvisor'].append(num_tese)

        # Update statistics
        stats['total'] += 1
        if is_mestrado:
            stats['mestrado'] += 1
        else:
            stats['doutorado'] += 1

        year = fields.get('year', 'Unknown')
        stats['by_year'][year] += 1

        area = fields.get('area_concentration', 'Unknown')
        stats['by_area'][area] += 1

        # Create content markdown files
        thesis_content_dir = CONTENT_DIR / num_tese
        thesis_content_dir.mkdir(exist_ok=True)

        for lang in ['pt', 'en']:
            md_content = create_thesis_markdown(thesis, lang)
            with open(thesis_content_dir / f"index.{lang}.md", 'w', encoding='utf-8') as f:
                f.write(md_content)

    # Save lightweight index
    print("Saving lightweight index...")
    with open(TESES_DATA_DIR / "index.json", 'w', encoding='utf-8') as f:
        json.dump(index_entries, f, ensure_ascii=False, separators=(',', ':'))

    index_size = (TESES_DATA_DIR / "index.json").stat().st_size / 1024
    print(f"  Index size: {index_size:.1f} KB")

    # Save professor mapping
    print("Saving professor mapping...")
    with open(TESES_DATA_DIR / "by_professor.json", 'w', encoding='utf-8') as f:
        json.dump(dict(by_professor), f, ensure_ascii=False, indent=2)

    # Save statistics
    print("Computing statistics...")
    stats['by_year'] = dict(stats['by_year'])
    stats['by_area'] = dict(stats['by_area'])
    with open(TESES_DATA_DIR / "statistics.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Create index content pages
    print("Creating index content pages...")
    for lang in ['pt', 'en']:
        index_file = CONTENT_DIR / f"_index.{lang}.md"
        if lang == 'pt':
            content = '''---
title: "Teses e Dissertações"
type: "teses"
layout: "list"
---
'''
        else:
            content = '''---
title: "Theses and Dissertations"
type: "teses"
layout: "list"
---
'''
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)

    return stats


def main():
    # Check for non-interactive mode
    non_interactive = '--no-interactive' in sys.argv or '-y' in sys.argv

    # Load thesis data
    print("Loading thesis data...")
    thesis_file = DATA_DIR / "tesesdigitais_eam.json"
    if not thesis_file.exists():
        print(f"Error: Thesis data file not found: {thesis_file}")
        sys.exit(1)

    with open(thesis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both formats: direct array or object with 'theses' key
    if isinstance(data, list):
        theses = data
    elif isinstance(data, dict) and 'theses' in data:
        theses = data['theses']
    else:
        print("Error: Unexpected JSON format")
        sys.exit(1)

    print(f"Loaded {len(theses)} theses")

    # Load professors
    print("Loading professors...")
    professors, professor_names = load_professors()
    print(f"Loaded {len(professors)} professors")

    # Extract all advisors
    print("Extracting advisors from thesis database...")
    advisors = extract_all_advisors(theses)
    print(f"Found {len(advisors)} unique advisors")

    # Load manual matches
    manual_matches = load_manual_matches()
    if manual_matches:
        print(f"Loaded {len(manual_matches)} manual matches from previous session")

    # Create output directories
    print("Creating output directories...")
    TESES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (TESES_DATA_DIR / "by_id").mkdir(exist_ok=True)

    # Interactive or automatic matching
    if non_interactive:
        print("\nRunning in non-interactive mode...")
        # Use manual matches + auto matches
        advisor_mapping = {}
        for advisor_name in advisors:
            if advisor_name in manual_matches:
                advisor_mapping[advisor_name] = manual_matches[advisor_name]
            else:
                prof_id, score = auto_match_advisor(advisor_name, professor_names)
                advisor_mapping[advisor_name] = prof_id

        matched = sum(1 for v in advisor_mapping.values() if v)
        print(f"Matched {matched}/{len(advisors)} advisors to professors")
    else:
        # Interactive matching
        advisor_mapping = interactive_matching(advisors, professor_names, professors, manual_matches)

    # Generate thesis pages
    stats = generate_thesis_pages(theses, advisor_mapping, data.get('metadata', {}))

    # Summary
    matched_count = sum(1 for v in advisor_mapping.values() if v)
    print(f"""
Summary:
  Total theses: {stats['total']}
  Mestrado: {stats['mestrado']}
  Doutorado: {stats['doutorado']}
  Advisors matched to current faculty: {matched_count}
  Advisors not matched (retired/external): {len(advisors) - matched_count}

Files created:
  - {TESES_DATA_DIR / 'index.json'}
  - {TESES_DATA_DIR / 'by_professor.json'}
  - {TESES_DATA_DIR / 'statistics.json'}
  - {TESES_DATA_DIR / 'manual_matches.json'}
  - {len(theses)} individual thesis files in {TESES_DATA_DIR / 'by_id'}
  - {len(theses)} content pages in {CONTENT_DIR}

Done!
""")


if __name__ == "__main__":
    main()
