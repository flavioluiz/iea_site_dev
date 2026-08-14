#!/usr/bin/env python3
"""
Generate statistics JSON from publication database.
Run this script whenever the Scopus data is updated.

Usage:
    python3 generate_statistics.py
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_publications():
    """Load all publications from data directory."""
    data_dir = Path(__file__).parent.parent / "data" / "publications" / "by_eid"
    publications = []

    if not data_dir.exists():
        print(f"Error: Directory not found: {data_dir}")
        return []

    print(f"Loading publications from: {data_dir}")

    for pub_file in data_dir.glob("*.json"):
        try:
            with open(pub_file, 'r', encoding='utf-8') as f:
                pub_data = json.load(f)
                publications.append(pub_data)
        except Exception as e:
            print(f"Error loading {pub_file.name}: {e}")

    print(f"Loaded {len(publications)} publications")
    return publications

def calculate_statistics(publications):
    """Calculate all statistics from publications."""
    stats = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "total_publications": len(publications)
        },
        "totals": {
            "articles": 0,
            "citations": 0
        },
        "by_year": {},
        "by_type": defaultdict(int),
        "recent_years": [],
        "top_cited": []
    }

    # Counters by year
    articles_by_year = defaultdict(int)
    citations_by_year = defaultdict(int)

    # Process each publication
    for pub in publications:
        year = pub.get('year')

        # Convert year to int if it's a string
        if isinstance(year, str):
            try:
                year = int(year)
            except (ValueError, TypeError):
                continue

        if not year or not isinstance(year, int):
            continue

        # Count articles by year
        articles_by_year[year] += 1
        stats['totals']['articles'] += 1

        # Count citations
        citations = pub.get('scopus', {}).get('citations', 0)
        if isinstance(citations, int):
            citations_by_year[year] += citations
            stats['totals']['citations'] += citations
        elif isinstance(citations, str):
            try:
                citations = int(citations)
                citations_by_year[year] += citations
                stats['totals']['citations'] += citations
            except (ValueError, TypeError):
                pass

        # Count by type
        pub_type = pub.get('type', 'article')
        stats['by_type'][pub_type] += 1

    # Build by_year structure
    all_years = sorted(set(list(articles_by_year.keys()) + list(citations_by_year.keys())))

    for year in all_years:
        stats['by_year'][str(year)] = {
            "articles": articles_by_year.get(year, 0),
            "citations": citations_by_year.get(year, 0)
        }

    # Get recent years (last 10 years with data)
    current_year = datetime.now().year
    recent_years = [y for y in all_years if y >= current_year - 10 and y <= current_year]
    recent_years.sort()

    # Calculate cumulative citations
    cumulative_citations = 0
    stats['recent_years'] = []
    for year in recent_years:
        cumulative_citations += citations_by_year.get(year, 0)
        stats['recent_years'].append({
            "year": year,
            "articles": articles_by_year.get(year, 0),
            "citations": citations_by_year.get(year, 0),
            "citations_cumulative": cumulative_citations
        })

    # Get top cited publications by different time periods
    current_year = datetime.now().year
    periods = {
        'all': None,  # All time
        '10y': current_year - 10,
        '5y': current_year - 5,
        '2y': current_year - 2
    }

    stats['top_cited_by_period'] = {}

    for period_key, year_threshold in periods.items():
        pubs_with_citations = []
        for pub in publications:
            year = pub.get('year')
            if isinstance(year, str):
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    continue

            # Filter by year if threshold is set
            if year_threshold is not None and (not isinstance(year, int) or year < year_threshold):
                continue

            citations = pub.get('scopus', {}).get('citations', 0)
            if isinstance(citations, int) and citations > 0:
                pubs_with_citations.append({
                    "eid": pub.get('eid', ''),
                    "doi": pub.get('doi', ''),
                    "title": pub.get('title', 'Untitled'),
                    "year": pub.get('year', 0),
                    "citations": citations,
                    "authors": [a.get('name', '') for a in pub.get('authors', [])[:3]],
                    "eam_coauthors": pub.get('eam_coauthors', [])
                })

        pubs_with_citations.sort(key=lambda x: x['citations'], reverse=True)
        stats['top_cited_by_period'][period_key] = pubs_with_citations[:10]

    # Keep the old 'top_cited' for backwards compatibility (all time)
    stats['top_cited'] = stats['top_cited_by_period']['all']

    # Convert by_type defaultdict to regular dict
    stats['by_type'] = dict(stats['by_type'])

    return stats

def calculate_professor_statistics(publications):
    """Calculate per-professor statistics."""
    professor_stats = defaultdict(lambda: {
        "articles": 0,
        "citations": 0,
        "h_index_calculated": 0
    })

    for pub in publications:
        citations = pub.get('scopus', {}).get('citations', 0)
        if not isinstance(citations, int):
            citations = 0

        eam_coauthors = pub.get('eam_coauthors', [])
        for prof_id in eam_coauthors:
            professor_stats[prof_id]["articles"] += 1
            professor_stats[prof_id]["citations"] += citations

    # Calculate h-index for each professor
    for prof_id, stats_data in professor_stats.items():
        # Get all publications for this professor with citations
        prof_pubs_citations = []
        for pub in publications:
            if prof_id in pub.get('eam_coauthors', []):
                citations = pub.get('scopus', {}).get('citations', 0)
                if isinstance(citations, int):
                    prof_pubs_citations.append(citations)

        # Sort citations in descending order
        prof_pubs_citations.sort(reverse=True)

        # Calculate h-index
        h_index = 0
        for i, citations in enumerate(prof_pubs_citations, 1):
            if citations >= i:
                h_index = i
            else:
                break

        stats_data["h_index_calculated"] = h_index

    return dict(professor_stats)

def count_cnpq_fellows():
    """Count CNPq research fellows from professor profiles."""
    profiles_dir = Path(__file__).parent.parent / "data" / "professores" / "profiles"

    cnpq_fellows = {
        "total": 0,
        "by_level": {}
    }

    if not profiles_dir.exists():
        print(f"Warning: Profiles directory not found: {profiles_dir}")
        return cnpq_fellows

    for profile_file in profiles_dir.glob("*.json"):
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile = json.load(f)

            bolsista_cnpq = profile.get('bolsista_cnpq', 'Não')

            # Count if is CNPq fellow (not "Não")
            if bolsista_cnpq != 'Não' and bolsista_cnpq:
                cnpq_fellows["total"] += 1

                # Extract level if present
                if bolsista_cnpq.startswith("Sim - "):
                    level = bolsista_cnpq.replace("Sim - ", "").strip()
                    cnpq_fellows["by_level"][level] = cnpq_fellows["by_level"].get(level, 0) + 1
                else:
                    cnpq_fellows["by_level"]["Sem nível especificado"] = cnpq_fellows["by_level"].get("Sem nível especificado", 0) + 1
        except Exception as e:
            print(f"Error reading profile {profile_file.name}: {e}")

    return cnpq_fellows

def calculate_theses_statistics():
    """Calculate statistics from theses and dissertations."""
    theses_file = Path(__file__).parent.parent / "data" / "tesesdigitais_eam.json"

    theses_stats = {
        "total": 0,
        "by_course": {},
        "by_year": {},
        "by_area": {},
        "recent_years": [],
        "top_advisors": []
    }

    if not theses_file.exists():
        print(f"Warning: Theses file not found: {theses_file}")
        return theses_stats

    try:
        with open(theses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        theses = data.get('theses', [])
        theses_stats['total'] = len(theses)

        # Counters
        advisors_count = defaultdict(int)

        for thesis in theses:
            fields = thesis.get('fields', {})

            # Count by course type
            course = fields.get('course', 'Unknown')
            theses_stats['by_course'][course] = theses_stats['by_course'].get(course, 0) + 1

            # Count by year
            year = fields.get('year')
            if year:
                try:
                    year = int(year)
                    theses_stats['by_year'][str(year)] = theses_stats['by_year'].get(str(year), 0) + 1
                except (ValueError, TypeError):
                    pass

            # Count by area
            area = fields.get('area_concentration', 'Não especificada')
            theses_stats['by_area'][area] = theses_stats['by_area'].get(area, 0) + 1

            # Count advisors
            advisors = fields.get('advisors', [])
            if isinstance(advisors, list):
                for advisor in advisors:
                    if advisor:
                        advisors_count[advisor] += 1
            elif advisors:
                advisors_count[advisors] += 1

            # Also count co-advisors
            co_advisors = fields.get('co_advisors', [])
            if isinstance(co_advisors, list):
                for co_advisor in co_advisors:
                    if co_advisor:
                        advisors_count[co_advisor] += 1
            elif co_advisors:
                advisors_count[co_advisors] += 1

        # Get recent years (last 10 years)
        current_year = datetime.now().year
        all_years = sorted([int(y) for y in theses_stats['by_year'].keys()])
        recent_years = [y for y in all_years if y >= current_year - 10 and y <= current_year]

        theses_stats['recent_years'] = []
        for year in recent_years:
            theses_stats['recent_years'].append({
                "year": year,
                "total": theses_stats['by_year'].get(str(year), 0),
                "mestrado": sum(1 for t in theses if t.get('fields', {}).get('year') == str(year) and t.get('fields', {}).get('course') == 'Mestrado Acadêmico'),
                "doutorado": sum(1 for t in theses if t.get('fields', {}).get('year') == str(year) and t.get('fields', {}).get('course') == 'Doutorado')
            })

        # Get top advisors
        top_advisors = sorted(advisors_count.items(), key=lambda x: x[1], reverse=True)[:10]
        theses_stats['top_advisors'] = [
            {"name": advisor, "count": count}
            for advisor, count in top_advisors
        ]

    except Exception as e:
        print(f"Error loading theses data: {e}")

    return theses_stats

def main():
    """Main function."""
    print("=" * 60)
    print("Generating Program Statistics")
    print("=" * 60)
    print()

    # Load publications
    publications = load_publications()

    if not publications:
        print("No publications found. Exiting.")
        return

    # Calculate statistics
    print("\nCalculating statistics...")
    stats = calculate_statistics(publications)

    print("\nCalculating professor statistics...")
    professor_stats = calculate_professor_statistics(publications)
    stats['professors'] = professor_stats

    print("\nCounting CNPq research fellows...")
    cnpq_fellows = count_cnpq_fellows()
    stats['cnpq_fellows'] = cnpq_fellows

    print("\nCalculating theses and dissertations statistics...")
    theses_stats = calculate_theses_statistics()
    stats['theses'] = theses_stats

    # Save to JSON
    output_file = Path(__file__).parent.parent / "data" / "statistics.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\nStatistics saved to: {output_file}")
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Total publications: {stats['totals']['articles']}")
    print(f"Total citations: {stats['totals']['citations']}")

    if stats['by_year']:
        years = [int(y) for y in stats['by_year'].keys()]
        print(f"Years covered: {min(years)} - {max(years)}")
    else:
        print("Years covered: No data")

    print(f"Recent years (last 10): {len(stats['recent_years'])}")
    print(f"Publication types: {len(stats['by_type'])}")
    print(f"Professors with publications: {len(professor_stats)}")
    print(f"CNPq Research Fellows: {cnpq_fellows['total']}")
    if cnpq_fellows['by_level']:
        print("  By level:")
        for level, count in sorted(cnpq_fellows['by_level'].items()):
            print(f"    - {level}: {count}")
    print()

    # Show theses statistics
    print("Theses and Dissertations:")
    print(f"  Total: {theses_stats['total']}")
    if theses_stats['by_course']:
        for course, count in theses_stats['by_course'].items():
            print(f"    - {course}: {count}")
    if theses_stats['top_advisors']:
        print("  Top 5 Advisors:")
        for i, advisor_data in enumerate(theses_stats['top_advisors'][:5], 1):
            print(f"    {i}. {advisor_data['name']}: {advisor_data['count']} theses")
    print()

    # Show recent years data
    if stats['recent_years']:
        print("Recent years publications:")
        for year_data in stats['recent_years'][-5:]:
            print(f"  {year_data['year']}: {year_data['articles']} articles, {year_data['citations']} citations")
        print()

    # Show top cited
    if stats['top_cited']:
        print("Top 5 most cited publications:")
        for i, pub in enumerate(stats['top_cited'][:5], 1):
            print(f"  {i}. [{pub['year']}] {pub['title'][:60]}... ({pub['citations']} citations)")
        print()

    print("Done!")

if __name__ == "__main__":
    main()
