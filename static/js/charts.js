/**
 * BlueStock Nifty 100 — Chart.js Configuration
 * ===============================================
 * Shared chart defaults and helper functions
 */

// ── Global Chart.js Defaults ──
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17, 24, 39, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600' };
Chart.defaults.scale.grid = { color: 'rgba(255, 255, 255, 0.04)' };

/**
 * Create a standard chart with premium dark-mode styling.
 */
function createChart(canvasId, type, labels, datasets, extraOpts = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    // Destroy if exists
    const existing = Chart.getChart(ctx);
    if (existing) existing.destroy();

    const opts = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
            legend: {
                display: datasets.length > 1,
                position: 'top',
                align: 'end',
            },
        },
        scales: {},
        ...extraOpts,
    };

    // Add scales for non-radar/pie/doughnut charts
    if (!['radar', 'pie', 'doughnut', 'polarArea'].includes(type)) {
        const isHorizontal = extraOpts.indexAxis === 'y';
        const valueAxis = isHorizontal ? 'x' : 'y';
        const categoryAxis = isHorizontal ? 'y' : 'x';

        opts.scales[categoryAxis] = {
            ticks: { maxTicksLimit: 12 },
            ...(extraOpts.scales?.[categoryAxis] || {}),
        };

        opts.scales[valueAxis] = {
            beginAtZero: type === 'bar',
            ticks: {
                callback: function(v) {
                    if (typeof v === 'number' && Math.abs(v) >= 10000) {
                        return (v / 1000).toFixed(0) + 'K';
                    }
                    return v;
                }
            },
            ...(extraOpts.scales?.[valueAxis] || {}),
        };
    }

    return new Chart(ctx, { type, data: { labels, datasets }, options: opts });
}

/**
 * Create a radar chart for growth analysis.
 */
function createRadarChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const existing = Chart.getChart(ctx);
    if (existing) existing.destroy();

    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels,
            datasets: datasets.map(d => ({
                ...d,
                borderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255,255,255,0.06)' },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                    pointLabels: { color: '#94a3b8', font: { size: 13 } },
                    ticks: { display: false },
                }
            },
            plugins: {
                legend: { position: 'bottom' },
            }
        }
    });
}

/**
 * Render the health distribution doughnut chart on the main dashboard.
 */
function renderHealthDistChart(distribution) {
    const colorMap = {
        'EXCELLENT': '#10b981',
        'GOOD': '#22c55e',
        'AVERAGE': '#f59e0b',
        'WEAK': '#f97316',
        'POOR': '#ef4444',
    };
    const labels = distribution.map(d => d.health_label__label_name);
    const data = distribution.map(d => d.count);
    const colors = labels.map(l => colorMap[l] || '#6366f1');

    const ctx = document.getElementById('healthDistChart');
    if (!ctx) return;

    const existing = Chart.getChart(ctx);
    if (existing) existing.destroy();

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.map(c => c + 'cc'),
                borderColor: colors,
                borderWidth: 2,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 20 },
                },
            },
            onClick: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const activeElement = activeElements[0];
                    const labelIndex = activeElement.index;
                    const ratingLabel = labels[labelIndex];
                    const ratingColor = colors[labelIndex];
                    if (typeof openHealthLabelModal === 'function') {
                        openHealthLabelModal(ratingLabel, ratingColor);
                    }
                }
            }
        }
    });
}

/**
 * Render the sector performance horizontal bar chart on the main dashboard.
 */
function renderSectorPerfChart(sectors) {
    const sorted = sectors.sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0)).slice(0, 12);
    createChart('sectorPerfChart', 'line',
        sorted.map(s => s.sector_name),
        [{
            label: 'Avg Score',
            data: sorted.map(s => s.avg_score ? parseFloat(Number(s.avg_score).toFixed(1)) : 0),
            backgroundColor: '#818cf833',
            borderColor: '#818cf8',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: sorted.map(s => s.color_hex || '#6366f1'),
            pointRadius: 4,
        }],
        { indexAxis: 'y' }
    );
}

// ── Global Chart Expansion Modal ──────────────────────────────────────────────
// We clone the chart into a fresh canvas appended to <body> to completely avoid
// CSS stacking-context issues (backdrop-filter / transform on parent glass cards
// trap position:fixed children, making them invisible or clipped).
// ─────────────────────────────────────────────────────────────────────────────

let _modalOverlay = null;
let _modalChart   = null;

function _buildModalOverlay() {
    if (_modalOverlay) return;

    // Backdrop
    const overlay = document.createElement('div');
    overlay.id = 'chartModalOverlay';
    overlay.style.cssText = `
        position: fixed; inset: 0; z-index: 99999;
        background: rgba(0,0,0,0.85);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex; align-items: center; justify-content: center;
        opacity: 0; transition: opacity 0.25s;
        pointer-events: none;
    `;

    // Modal box
    const box = document.createElement('div');
    box.id = 'chartModalBox';
    box.style.cssText = `
        position: relative;
        width: 88vw; height: 82vh;
        background: #111827;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        box-shadow: 0 25px 60px rgba(0,0,0,0.7);
        display: flex; flex-direction: column;
        padding: 2rem;
    `;

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.id = 'chartModalClose';
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        position: absolute; top: 1rem; right: 1.25rem;
        background: rgba(255,255,255,0.1); border: none; color: #fff;
        width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem;
        cursor: pointer; display: flex; align-items: center; justify-content: center;
        transition: background 0.2s; z-index: 1;
    `;
    closeBtn.onmouseenter = () => closeBtn.style.background = 'rgba(255,255,255,0.22)';
    closeBtn.onmouseleave = () => closeBtn.style.background = 'rgba(255,255,255,0.1)';
    closeBtn.onclick = _closeModal;

    // Canvas wrapper
    const canvasWrap = document.createElement('div');
    canvasWrap.style.cssText = 'flex:1; position:relative; min-height:0;';
    const canvas = document.createElement('canvas');
    canvas.id = 'chartModalCanvas';
    canvasWrap.appendChild(canvas);

    box.appendChild(closeBtn);
    box.appendChild(canvasWrap);
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    _modalOverlay = overlay;

    // Close on backdrop click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) _closeModal();
    });
}

function _openModal(srcCanvas) {
    _buildModalOverlay();

    const srcChart = Chart.getChart(srcCanvas);
    if (!srcChart) return;

    // Destroy previous modal chart
    if (_modalChart) { _modalChart.destroy(); _modalChart = null; }

    // Show overlay
    _modalOverlay.style.pointerEvents = 'auto';
    _modalOverlay.style.opacity = '1';

    // Clone chart config deeply
    const srcConfig = srcChart.config;
    const newCanvas = document.getElementById('chartModalCanvas');

    // Small delay to let the overlay render first
    setTimeout(() => {
        _modalChart = new Chart(newCanvas, {
            type: srcConfig.type,
            data: JSON.parse(JSON.stringify(srcConfig.data)),
            options: {
                ...JSON.parse(JSON.stringify(srcConfig.options || {})),
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400 },
            }
        });
    }, 50);
}

function _closeModal() {
    if (!_modalOverlay) return;
    _modalOverlay.style.opacity = '0';
    _modalOverlay.style.pointerEvents = 'none';
    if (_modalChart) {
        setTimeout(() => { if (_modalChart) { _modalChart.destroy(); _modalChart = null; } }, 280);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Click any canvas inside a chart-container to expand
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'CANVAS' && e.target.closest('.chart-container')) {
            if (e.target.id === 'healthDistChart') return; // Skip default expansion
            _openModal(e.target);
        }
    });

    // ESC to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') _closeModal();
    });
});
