/**
 * Lab Card Expand/Collapse and Filtering Functionality
 */

// Toggle lab card expansion
function toggleLabCard(button) {
  const card = button.closest('.lab-card');
  const preview = card.querySelector('.lab-preview');
  const details = card.querySelector('.lab-details');
  const expandIcon = card.querySelector('.expand-icon');
  const btnText = card.querySelector('.btn-text');

  const isExpanded = !details.classList.contains('hidden');

  if (isExpanded) {
    // Collapse
    details.classList.add('hidden');
    preview.classList.remove('hidden');
    if (expandIcon) expandIcon.classList.remove('rotate-180');
  } else {
    // Expand
    details.classList.remove('hidden');
    preview.classList.add('hidden');
    if (expandIcon) expandIcon.classList.add('rotate-180');
  }
}

// Lab filtering functionality
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('lab-search');
  const areaFilter = document.getElementById('lab-area-filter');
  const clearBtn = document.getElementById('clear-lab-filters');
  const resultsCount = document.getElementById('lab-results-count');
  const noResults = document.getElementById('no-lab-results');
  const areaSections = document.querySelectorAll('.lab-area-section');
  const cards = document.querySelectorAll('.lab-card');

  if (!searchInput || !areaFilter) return;

  function filterLabs() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const selectedArea = areaFilter.value;
    let visibleCount = 0;
    const visibleAreas = new Set();

    cards.forEach(card => {
      const name = card.dataset.name || '';
      const sigla = card.dataset.sigla || '';
      const area = card.dataset.area || '';

      const matchesSearch = !searchTerm ||
                           name.includes(searchTerm) ||
                           sigla.includes(searchTerm);
      const matchesArea = !selectedArea || area === selectedArea;

      if (matchesSearch && matchesArea) {
        card.style.display = '';
        visibleCount++;
        visibleAreas.add(area);
      } else {
        card.style.display = 'none';
      }
    });

    // Show/hide area sections based on visible cards
    areaSections.forEach(section => {
      const sectionArea = section.dataset.area;
      if (visibleAreas.has(sectionArea)) {
        section.style.display = '';
      } else {
        section.style.display = 'none';
      }
    });

    // Update results count
    resultsCount.textContent = visibleCount;

    // Show/hide no results message
    if (noResults) {
      noResults.classList.toggle('hidden', visibleCount > 0);
    }
  }

  function clearFilters() {
    searchInput.value = '';
    areaFilter.value = '';
    filterLabs();
  }

  // Event listeners
  searchInput.addEventListener('input', filterLabs);
  areaFilter.addEventListener('change', filterLabs);

  if (clearBtn) {
    clearBtn.addEventListener('click', clearFilters);
  }

  // Expand all labs in a section when clicking section header (optional feature)
  areaSections.forEach(section => {
    const header = section.querySelector('h2');
    if (header) {
      header.style.cursor = 'pointer';
      header.title = 'Click to expand/collapse all';

      header.addEventListener('dblclick', function() {
        const sectionCards = section.querySelectorAll('.lab-card');
        const allExpanded = Array.from(sectionCards).every(card =>
          !card.querySelector('.lab-details').classList.contains('hidden')
        );

        sectionCards.forEach(card => {
          const details = card.querySelector('.lab-details');
          const preview = card.querySelector('.lab-preview');
          const expandIcon = card.querySelector('.expand-icon');

          if (allExpanded) {
            // Collapse all
            details.classList.add('hidden');
            preview.classList.remove('hidden');
            if (expandIcon) expandIcon.classList.remove('rotate-180');
          } else {
            // Expand all
            details.classList.remove('hidden');
            preview.classList.add('hidden');
            if (expandIcon) expandIcon.classList.add('rotate-180');
          }
        });
      });
    }
  });
});
