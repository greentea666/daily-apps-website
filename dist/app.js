const filters = document.querySelectorAll('[data-filter]');
filters.forEach(button => button.addEventListener('click', () => {
  const category = button.dataset.filter;
  filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  let count = 0;
  document.querySelectorAll('[data-category]').forEach(card => {
    const visible = category === 'all' || card.dataset.category === category;
    card.classList.toggle('hidden', !visible);
    if (visible) count++;
  });
  document.querySelector('#filter-status').textContent = `已顯示 ${count} 個項目`;
}));
