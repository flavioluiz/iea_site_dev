/**
 * Publications Filter
 * Client-side filtering for publications on professor profile pages
 */

document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('pub-search');
  const yearFilter = document.getElementById('pub-year-filter');
  const typeFilter = document.getElementById('pub-type-filter');
  const publicationsList = document.getElementById('publications-list');
  const pubCount = document.getElementById('pub-count');
  const noResults = document.getElementById('no-results');

  if (!publicationsList) return; // Exit if not on a page with publications

  const publications = Array.from(publicationsList.querySelectorAll('.publication-card'));

  // Populate year filter with unique years from publications
  const years = [...new Set(publications.map(p => p.dataset.year))]
    .filter(y => y && y !== 'undefined')
    .sort()
    .reverse();

  years.forEach(year => {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    yearFilter.appendChild(option);
  });

  /**
   * Filter publications based on current filter values
   */
  function filterPublications() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const selectedYear = yearFilter.value;
    const selectedType = typeFilter.value;

    let visibleCount = 0;

    publications.forEach(pub => {
      // Get publication data
      const titleElement = pub.querySelector('h3');
      const authorsElement = pub.querySelector('.text-gray-600');

      const title = titleElement ? titleElement.textContent.toLowerCase() : '';
      const authors = authorsElement ? authorsElement.textContent.toLowerCase() : '';
      const year = pub.dataset.year || '';
      const type = pub.dataset.type || '';

      // Check if publication matches all filters
      const matchesSearch = !searchTerm ||
        title.includes(searchTerm) ||
        authors.includes(searchTerm);

      const matchesYear = !selectedYear || year === selectedYear;
      const matchesType = !selectedType || type === selectedType;

      // Show/hide publication
      if (matchesSearch && matchesYear && matchesType) {
        pub.style.display = 'block';
        visibleCount++;
      } else {
        pub.style.display = 'none';
      }
    });

    // Update count
    if (pubCount) {
      pubCount.textContent = visibleCount;
    }

    // Show/hide no results message
    if (noResults) {
      if (visibleCount === 0) {
        noResults.classList.remove('hidden');
        publicationsList.classList.add('hidden');
      } else {
        noResults.classList.add('hidden');
        publicationsList.classList.remove('hidden');
      }
    }
  }

  // Add event listeners
  if (searchInput) {
    searchInput.addEventListener('input', filterPublications);
  }

  if (yearFilter) {
    yearFilter.addEventListener('change', filterPublications);
  }

  if (typeFilter) {
    typeFilter.addEventListener('change', filterPublications);
  }

  // Initial filter (in case URL has parameters)
  filterPublications();
});
