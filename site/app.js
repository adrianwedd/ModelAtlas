// Tags excluded from display and top-tags chart (infrastructure noise)
const TAG_BLOCKLIST = new Set([
  'region:us', 'transformers', 'endpoints_compatible',
  'autotrain_compatible', 'safetensors', 'pytorch', 'tf', 'jax',
]);

function modelApp() {
  return {
    models: [],
    filtered: [],
    search: '',
    licenseFilter: 'all',
    sortBy: 'trust_score',

    async init() {
      try {
        const resp = await fetch('./models_enriched.json');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        this.models = await resp.json();
      } catch (err) {
        console.error('Failed to load model data:', err);
      }
      this.applyFilters();

      // Watch reactive properties and re-filter on change
      this.$watch('search', () => this.applyFilters());
      this.$watch('licenseFilter', () => this.applyFilters());
      this.$watch('sortBy', () => this.applyFilters());

      // Init charts after DOM renders
      this.$nextTick(() => this.initCharts());
    },

    // ── Computed ─────────────────────────────────────────────
    get licensedPct() {
      if (!this.models.length) return 0;
      const n = this.models.filter(m => m.license).length;
      return Math.round(n / this.models.length * 100);
    },

    get avgTrust() {
      if (!this.models.length) return '—';
      const avg = this.models.reduce((s, m) => s + (m.trust_score || 0), 0) / this.models.length;
      return avg.toFixed(2);
    },

    // ── Filtering ─────────────────────────────────────────────
    applyFilters() {
      let result = [...this.models];

      if (this.search.trim()) {
        const q = this.search.trim().toLowerCase();
        result = result.filter(m =>
          m.name.toLowerCase().includes(q) ||
          (m.tags || []).some(t => typeof t === 'string' && t.toLowerCase().includes(q))
        );
      }

      if (this.licenseFilter !== 'all') {
        if (this.licenseFilter === 'none') {
          result = result.filter(m => !m.license);
        } else if (this.licenseFilter === 'other') {
          result = result.filter(m => m.license && !['apache-2.0', 'mit'].includes(m.license));
        } else {
          result = result.filter(m => (m.license || '').toLowerCase() === this.licenseFilter);
        }
      }

      result.sort((a, b) => {
        if (this.sortBy === 'name') return a.name.localeCompare(b.name);
        if (this.sortBy === 'trust_score') return (b.trust_score || 0) - (a.trust_score || 0);
        if (this.sortBy === 'last_updated') {
          return (b.last_updated || '').localeCompare(a.last_updated || '');
        }
        return 0;
      });

      this.filtered = result;
    },

    // ── Row helpers ───────────────────────────────────────────
    topTags(model) {
      return (model.tags || [])
        .filter(t => typeof t === 'string' && !TAG_BLOCKLIST.has(t))
        .slice(0, 3);
    },

    modelUrl(model) {
      // HF models always have namespace/repo format (e.g. "bert-base/uncased")
      // Ollama native models never have a slash (e.g. "llama3", "mistral")
      if (model.name.includes('/')) {
        return `https://huggingface.co/${model.name}`;
      }
      return `https://ollama.com/library/${model.name}`;
    },

    licenseBadgeClass(license) {
      if (!license) return 'badge--none';
      const l = license.toLowerCase();
      if (l === 'apache-2.0') return 'badge--apache';
      if (l === 'mit') return 'badge--mit';
      return 'badge--other';
    },

    trustDots(score) {
      const filled = Math.round((score || 0) * 5);
      let html = '';
      for (let i = 0; i < 5; i++) {
        html += `<span class="${i < filled ? 'dot--filled' : 'dot--empty'}">●</span>`;
      }
      return html;
    },

    // ── Charts ────────────────────────────────────────────────
    initCharts() {
      this.initLicenseChart();
      this.initTrustChart();
      this.initTagsChart();
    },

    initLicenseChart() {
      const counts = {};
      this.models.forEach(m => {
        const key = m.license || 'unlicensed';
        counts[key] = (counts[key] || 0) + 1;
      });
      const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
      const ctx = document.getElementById('licenseChart');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: sorted.map(e => e[0]),
          datasets: [{
            data: sorted.map(e => e[1]),
            backgroundColor: ['#3fb950', '#58a6ff', '#d29922', '#a371f7', '#f85149', '#484f58'],
            borderColor: '#161b22',
            borderWidth: 2,
          }]
        },
        options: {
          plugins: {
            legend: { labels: { color: '#7d8590', font: { size: 11 } } }
          }
        }
      });
    },

    initTrustChart() {
      const labels = ['0–0.2', '0.2–0.4', '0.4–0.6', '0.6–0.8', '0.8–1.0'];
      const buckets = [0, 0, 0, 0, 0];
      this.models.forEach(m => {
        const s = m.trust_score || 0;
        const idx = Math.min(Math.floor(s * 5), 4);
        buckets[idx]++;
      });
      const ctx = document.getElementById('trustChart');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            data: buckets,
            backgroundColor: ['#f85149', '#d29922', '#d29922', '#3fb950', '#3fb950'],
            borderRadius: 4,
          }]
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#7d8590', font: { size: 10 } }, grid: { color: '#30363d' } },
            y: { ticks: { color: '#7d8590', font: { size: 10 } }, grid: { color: '#30363d' } }
          }
        }
      });
    },

    initTagsChart() {
      const counts = {};
      this.models.forEach(m => {
        (m.tags || [])
          .filter(t => typeof t === 'string' && !TAG_BLOCKLIST.has(t))
          .forEach(t => { counts[t] = (counts[t] || 0) + 1; });
      });
      const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
      const ctx = document.getElementById('tagsChart');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: top.map(e => e[0]),
          datasets: [{
            data: top.map(e => e[1]),
            backgroundColor: '#58a6ff',
            borderRadius: 4,
          }]
        },
        options: {
          indexAxis: 'y',
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#7d8590', font: { size: 10 } }, grid: { color: '#30363d' } },
            y: { ticks: { color: '#e6edf3', font: { size: 10, family: 'monospace' } }, grid: { display: false } }
          }
        }
      });
    }
  };
}
