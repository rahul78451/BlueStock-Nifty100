/**
 * BlueStock Nifty 100 — Dashboard JavaScript
 * ============================================
 * Global search, navigation, utilities
 */

// ── Global Search ──
(function initSearch() {
    const input = document.getElementById('globalSearch');
    const dropdown = document.getElementById('searchDropdown');
    if (!input || !dropdown) return;

    let companies = [];
    let debounceTimer;

    // Pre-fetch company list
    fetch('/api/companies/?format=json&page_size=200')
        .then(r => r.json())
        .then(data => { companies = data.results || data; })
        .catch(() => {});

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const q = input.value.trim().toLowerCase();
            if (q.length < 1) {
                dropdown.classList.remove('visible');
                return;
            }

            const matches = companies.filter(c =>
                c.symbol.toLowerCase().includes(q) ||
                c.company_name.toLowerCase().includes(q)
            ).slice(0, 8);

            if (matches.length === 0) {
                dropdown.innerHTML = '<div style="padding:1rem;text-align:center;color:var(--text-muted);font-size:0.875rem;">No results found</div>';
            } else {
                dropdown.innerHTML = matches.map(c => `
                    <a href="/company/${c.symbol}/" class="search-item">
                        <span class="search-symbol">${c.symbol}</span>
                        <span class="search-name">${c.company_name}</span>
                        <span class="search-sector">${c.sector_name || ''}</span>
                    </a>
                `).join('');
            }
            dropdown.classList.add('visible');
        }, 200);
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-search')) {
            dropdown.classList.remove('visible');
        }
    });

    // Keyboard shortcut: / to focus search
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== input) {
            e.preventDefault();
            input.focus();
        }
        if (e.key === 'Escape') {
            dropdown.classList.remove('visible');
            input.blur();
        }
    });
})();

// ── Number Formatting Utility ──
function formatNumber(n, decimals = 0) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-IN', { maximumFractionDigits: decimals });
}

function formatCrores(n) {
    if (n == null) return '—';
    const num = Number(n);
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)}L Cr`;
    return `₹${formatNumber(num)} Cr`;
}
