// Tags excluded from display and top-tags chart (infrastructure noise)
const TAG_BLOCKLIST = new Set([
  'region:us', 'transformers', 'endpoints_compatible',
  'autotrain_compatible', 'safetensors', 'pytorch', 'tf', 'jax',
  'latest',  // Ollama version tag, not semantic
]);

// Exclude models that are routing aliases, not distinct models
const NAME_BLOCKLIST_PREFIX = ['~'];

function modelApp() {
  return {
    models: [],
    filtered: [],
    corpusAsr: null,         // loaded from corpus_asr.json
    asrSortDir: 'desc',      // 'asc' | 'desc'
    search: '',
    licenseFilter: 'all',
    typeFilter: 'all',
    sortBy: 'trust_score',
    sourceFilter: 'all',
    loadError: false,
    safeStr(v) { return (v != null && typeof v === 'string') ? v : ''; },

    async init() {
      try {
        const resp = await fetch('./models_enriched.json');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        this.models = Array.isArray(data) ? data.filter(m => m != null && typeof m === 'object') : [];
      } catch (err) {
        console.error('Failed to load model data:', err);
        this.loadError = true;
      }

      try {
        const resp = await fetch('./corpus_asr.json');
        if (resp.ok) this.corpusAsr = await resp.json();
      } catch (err) {
        console.warn('corpus_asr.json not available:', err);
      }

      this.applyFilters();

      // Watch reactive properties and re-filter on change
      this.$watch('search', () => this.applyFilters());
      this.$watch('licenseFilter', () => this.applyFilters());
      this.$watch('typeFilter', () => this.applyFilters());
      this.$watch('sortBy', () => this.applyFilters());
      this.$watch('sourceFilter', () => this.applyFilters());

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
      const avg = this.models.reduce((s, m) => s + (parseFloat(m.trust_score) || 0), 0) / this.models.length;
      return avg.toFixed(2);
    },

    get corpusModelCount() {
      return this.corpusAsr ? this.corpusAsr.model_count : 0;
    },

    get corpusAvgAsr() {
      if (!this.corpusAsr || !this.corpusAsr.models.length) return '—';
      const avg = this.corpusAsr.models.reduce((s, m) => s + (m.asr_pct || 0), 0) / this.corpusAsr.models.length;
      return avg.toFixed(1) + '%';
    },

    get sortedCorpusModels() {
      if (!this.corpusAsr) return [];
      return [...this.corpusAsr.models].sort((a, b) =>
        this.asrSortDir === 'desc' ? b.asr_pct - a.asr_pct : a.asr_pct - b.asr_pct
      );
    },

    asrTierClass(asr) {
      if (asr >= 70) return 'asr-tier--high';
      if (asr >= 40) return 'asr-tier--mid';
      return 'asr-tier--low';
    },

    // ── Filtering ─────────────────────────────────────────────
    applyFilters() {
      let result = this.models.filter(m => !NAME_BLOCKLIST_PREFIX.some(p => this.safeStr(m.name).startsWith(p)));

      if (this.search.trim()) {
        const q = this.search.trim().toLowerCase();
        result = result.filter(m =>
          this.safeStr(m.name).toLowerCase().includes(q) ||
          this.safeStr(m.description).toLowerCase().includes(q) ||
          (Array.isArray(m.tags) ? m.tags : []).some(t => typeof t === 'string' && t.toLowerCase().includes(q))
        );
      }

      if (this.sourceFilter !== 'all') {
        result = result.filter(m => this.sourceKey(m) === this.sourceFilter);
      }

      if (this.typeFilter !== 'all') {
        result = result.filter(m => this.modelType(m) === this.typeFilter);
      }

      if (this.licenseFilter !== 'all') {
        if (this.licenseFilter === 'none') {
          result = result.filter(m => !this.safeStr(m.license));
        } else if (this.licenseFilter === 'other') {
          const common = ['apache-2.0', 'mit'];
          result = result.filter(m => {
            const license = this.safeStr(m.license);
            return license && !common.includes(license.toLowerCase());
          });
        } else {
          result = result.filter(m => this.safeStr(m.license).toLowerCase().trim() === this.licenseFilter);
        }
      }

      result.sort((a, b) => {
        if (this.sortBy === 'name') return this.safeStr(a.name).localeCompare(this.safeStr(b.name));
        if (this.sortBy === 'trust_score') return (parseFloat(b.trust_score) || 0) - (parseFloat(a.trust_score) || 0);
        if (this.sortBy === 'downloads') {
          return (b.pull_count ?? b.downloads ?? 0) - (a.pull_count ?? a.downloads ?? 0);
        }
        if (this.sortBy === 'last_updated') {
          const da = new Date(a.last_updated || 0), db = new Date(b.last_updated || 0);
          const ta = isNaN(da) ? 0 : da.getTime(), tb = isNaN(db) ? 0 : db.getTime();
          return tb - ta;
        }
        return 0;
      });

      this.filtered = result;
    },

    // ── Row helpers ───────────────────────────────────────────
    topTags(model) {
      return (Array.isArray(model.tags) ? model.tags : [])
        .filter(t => typeof t === 'string' && !TAG_BLOCKLIST.has(t) && !t.includes('•'))
        .slice(0, 4);
    },

    sourceKey(model) {
      const src = this.safeStr(model.source).toLowerCase();
      if (src === 'huggingface' || src === 'hf') return 'hf';
      if (src === 'ollama_cloud') return 'ollama_cloud';
      if (src === 'openrouter') return 'openrouter';
      if (src === 'ollama') return 'ollama';
      // fallback: namespaced names (org/repo) are HF
      return this.safeStr(model.name).includes('/') ? 'hf' : 'ollama';
    },

    sourceLabel(model) {
      const k = this.sourceKey(model);
      if (k === 'hf') return 'HF';
      if (k === 'ollama_cloud') return 'Ollama Cloud';
      if (k === 'openrouter') return 'OpenRouter';
      return 'Ollama';
    },

    sourceBadgeClass(model) {
      const k = this.sourceKey(model);
      if (k === 'hf') return 'source--hf';
      if (k === 'ollama_cloud') return 'source--ollama-cloud';
      if (k === 'openrouter') return 'source--openrouter';
      return 'source--ollama';
    },

    modelType(model) {
      const arch = this.safeStr(model.architecture).toLowerCase();
      const tags = (Array.isArray(model.tags) ? model.tags : []).map(t => (typeof t === 'string' ? t : '').toLowerCase());
      const name = this.safeStr(model.name).toLowerCase();

      const hasTag = (...needles) => needles.some(n => tags.some(t => t.includes(n)));
      const archHas = (...needles) => needles.some(n => arch.includes(n));
      const nameHas = (...needles) => needles.some(n => name.includes(n));

      if (hasTag('text-to-image', 'image-generation', 'diffusers', 'stable-diffusion', 'text-to-video'))
        return 'image-gen';
      if (hasTag('automatic-speech-recognition', 'text-to-speech', 'audio-classification') || archHas('audio') || nameHas('whisper', 'tts', 'speech'))
        return 'audio';
      if (hasTag('feature-extraction', 'sentence-similarity', 'text-embeddings-inference', 'sentence-transformers') || nameHas('embed', 'reranker', 'contriever', 'bge', 'nomic-embed', 'mxbai-embed', 'e5-', 'minilm', 'bert', 'roberta', 'deberta'))
        return 'embedding';
      if (hasTag('code', 'coding') || nameHas('code', 'coder', 'deepcoder', 'devstral', 'starcoder', 'codestral'))
        return 'code';
      if (archHas('image', 'video', 'vision') || hasTag('vision', 'image-classification', 'zero-shot-image-classification', 'object-detection', 'vqa') || nameHas('llava', 'vision', 'vl:', 'vl-', '-vl', 'minicpm-v', 'cogvlm', 'bakllava', 'moondream'))
        return 'vision';
      if (archHas('text->text') || hasTag('text-generation', 'text-generation-inference', 'conversational', 'chat', 'instruct') || nameHas('llama', 'mistral', 'gemma', 'qwen', 'phi', 'falcon', 'dolphin', 'command', 'deepseek', 'orca', 'vicuna', 'wizard', 'hermes', 'solar', 'yi', 'mixtral', 'granite', 'lfm', 'nexus', 'nous', 'stablelm', 'starling', 'zephyr', 'notus', 'notux', 'minimax', 'gpt-oss', 'reflection', 'xwin', 'everythinglm', 'deepscaler', 'r1-', 'megadolphin', 'openhermes', 'samantha'))
        return 'text-llm';
      return 'other';
    },

    formatPopularity(model) {
      const n = model.pull_count ?? model.downloads ?? 0;
      if (!n) return '—';
      if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
      if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
      if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '') + 'K';
      return String(n);
    },

    descExcerpt(model) {
      const d = this.safeStr(model.description).trim();
      if (!d) return '—';
      return d.length > 130 ? d.slice(0, 130) + '…' : d;
    },

    formatDate(model) {
      const d = model.last_updated;
      if (!d) return '—';
      try {
        const date = new Date(d);
        if (isNaN(date)) return '—';
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
      } catch {
        return '—';
      }
    },

    modelUrl(model) {
      const modelName = this.safeStr(model.name);
      if (!modelName) return '#';
      const k = this.sourceKey(model);
      if (k === 'openrouter') return `https://openrouter.ai/models/${modelName}`;
      if (k === 'ollama_cloud') return `https://ollama.com/library/${modelName.split(':')[0]}`;
      if (k === 'hf') return `https://huggingface.co/${modelName}`;
      return `https://ollama.com/library/${modelName}`;
    },

    licenseBadgeClass(license) {
      const l = (typeof license === 'string' ? license : '').toLowerCase().trim();
      if (!l) return 'badge--none';
      if (l === 'apache-2.0') return 'badge--apache';
      if (l === 'mit') return 'badge--mit';
      return 'badge--other';
    },

    trustFilled(score) {
      const raw = parseFloat(score);
      return Number.isFinite(raw) ? Math.min(5, Math.max(0, Math.round(raw * 5))) : 0;
    },

    trustDots(score) {
      return '';
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
        const key = this.safeStr(m.license) || 'unlicensed';
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
        const raw = parseFloat(m.trust_score);
        const s = Number.isFinite(raw) ? Math.min(Math.max(raw, 0), 1) : 0;
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
        (Array.isArray(m.tags) ? m.tags : [])
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
