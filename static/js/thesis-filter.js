/**
 * Thesis Filter - Client-side filtering for thesis list page
 */
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('search-input');
  const yearFilter = document.getElementById('year-filter');
  const courseFilter = document.getElementById('course-filter');
  const areaFilter = document.getElementById('area-filter');
  const advisorFilter = document.getElementById('advisor-filter');
  const clearButton = document.getElementById('clear-filters');
  const resultsCount = document.getElementById('results-count');
  const container = document.getElementById('thesis-container');
  const noResults = document.getElementById('no-results');
  const cards = container.querySelectorAll('.thesis-card');

  // Normalize text for search (remove accents, lowercase)
  function normalizeText(text) {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  // Read URL query parameters and set filter values
  function applyUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);

    const advisor = urlParams.get('advisor');
    const year = urlParams.get('year');
    const course = urlParams.get('course');
    const area = urlParams.get('area');
    const search = urlParams.get('q');

    if (advisor && advisorFilter) {
      advisorFilter.value = advisor;
    }
    if (year && yearFilter) {
      yearFilter.value = year;
    }
    if (course && courseFilter) {
      courseFilter.value = course;
    }
    if (area && areaFilter) {
      areaFilter.value = area;
    }
    if (search && searchInput) {
      searchInput.value = search;
    }
  }

  function filterTheses() {
    const searchTerm = normalizeText(searchInput.value);
    const yearValue = yearFilter.value;
    const courseValue = courseFilter.value;
    const areaValue = areaFilter.value;
    const advisorValue = advisorFilter.value;

    let visibleCount = 0;

    cards.forEach(card => {
      const title = card.dataset.title || '';
      const author = card.dataset.author || '';
      const keywords = card.dataset.keywords || '';
      const year = card.dataset.year || '';
      const course = card.dataset.course || '';
      const area = card.dataset.area || '';
      const advisors = card.dataset.advisors || '';

      // Search matches title, author, or keywords
      const searchText = normalizeText(title + ' ' + author + ' ' + keywords);
      const matchesSearch = !searchTerm || searchText.includes(searchTerm);

      // Filter matches
      const matchesYear = !yearValue || year === yearValue;
      const matchesCourse = !courseValue || course === courseValue;
      const matchesArea = !areaValue || area === areaValue;
      const matchesAdvisor = !advisorValue || advisors.includes(advisorValue);

      if (matchesSearch && matchesYear && matchesCourse && matchesArea && matchesAdvisor) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    resultsCount.textContent = visibleCount;

    if (visibleCount === 0) {
      container.classList.add('hidden');
      noResults.classList.remove('hidden');
    } else {
      container.classList.remove('hidden');
      noResults.classList.add('hidden');
    }

    // Update URL without reloading (optional - for shareable links)
    updateUrl();
  }

  function updateUrl() {
    const params = new URLSearchParams();

    if (searchInput.value) params.set('q', searchInput.value);
    if (yearFilter.value) params.set('year', yearFilter.value);
    if (courseFilter.value) params.set('course', courseFilter.value);
    if (areaFilter.value) params.set('area', areaFilter.value);
    if (advisorFilter.value) params.set('advisor', advisorFilter.value);

    const newUrl = params.toString()
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;

    window.history.replaceState({}, '', newUrl);
  }

  function clearFilters() {
    searchInput.value = '';
    yearFilter.value = '';
    courseFilter.value = '';
    areaFilter.value = '';
    advisorFilter.value = '';
    filterTheses();
  }

  // Event listeners
  searchInput.addEventListener('input', filterTheses);
  yearFilter.addEventListener('change', filterTheses);
  courseFilter.addEventListener('change', filterTheses);
  areaFilter.addEventListener('change', filterTheses);
  advisorFilter.addEventListener('change', filterTheses);
  clearButton.addEventListener('click', clearFilters);

  // Apply URL parameters on page load
  applyUrlParams();

  // Initial filter
  filterTheses();
});
