# UX Audit and Redesign Recommendations

This document captures the LUMEN UX audit performed on the ModelAtlas repository. The audit reviewed the README, CLI usage, and overall onboarding flow.

## 🔍 UX Audit Summary
ModelAtlas combines CLI commands, data tooling, and a conceptual React dashboard. The README explains how to launch the enrichment trace and CLI search commands, and describes the architecture of the system. However, the absence of the actual dashboard code and some inconsistent documentation make the entry experience slightly confusing. The CLI itself exposes an `init` command for creating a `.env` and a `trace` command for running the enrichment pipeline.

## 💡 UX Insights & Redesigns
- **README / Onboarding**
  - Clarify the Quick Start instructions. Include a direct note if the dashboard is forthcoming or where it lives.
  - Provide a single "Run the demo" command block that chains environment setup and enrichment.
- **CLI Flow**
  - Group related options under a "Trace Options" header in the help text.
  - Show explicit output path examples. Clarify if `atlas search` is an alias or official subcommand.
- **Visual Hierarchy**
  - Add subheadings such as "📦 Components" and "🛠️ Toolchain" to separate conceptual sections.
  - Move the `dashboards/` reference into a future work section or add the missing directory.
- **Input Anxiety & Validation**
  - Provide clearer messaging when `tasks.yml` is missing and after running `atlas init`.
- **Consistency / Terminology**
  - Use a single CLI name across docs and help text.

## 🎨 Visual Layering Suggestions
- Use a consistent typographic scale in README headers.
- Add subtle accent colors in CLI output with Rich for status feedback.
- When the dashboard is implemented, consider a neutral dark theme with accent color highlights.

## 📱 Responsiveness Matrix
| Viewport | Behavior |
| -------- | -------- |
| **≤768px** | CLI usage unchanged; future dashboard should collapse side navigation and show cards in a single column. |
| **≥769px** | Dashboard uses a multi-column grid with charts on the right and filters on the left. |

## 🧪 Suggested A/B Test Variants (Optional)
1. **Error Messaging**
   - Variant A: current short error message.
   - Variant B: detailed guidance suggesting `atlas init` or specifying `--tasks-yml`.
2. **Dashboard Color Scheme**
   - Variant A: dark background with neon accent.
   - Variant B: light background with soft gradient.

## ♿ Accessibility Review
- Provide alt text for diagrams and charts in README.
- Ensure future React dashboard components maintain a minimum 4.5:1 contrast ratio.
- Support keyboard navigation for search and filter controls.

## 📎 Design Tokens / Tailwind Snippets
```css
:root {
  --color-bg: #0f172a;        /* slate-900 */
  --color-accent: #4f46e5;    /* indigo-600 */
  --color-muted: #94a3b8;     /* slate-400 */
  --radius-base: 8px;
  --shadow-card: 0 2px 4px rgba(0,0,0,0.1);
}

.card {
  background-color: var(--color-bg);
  border-radius: var(--radius-base);
  box-shadow: var(--shadow-card);
  padding: 1rem;
  color: #fff;
}
```
