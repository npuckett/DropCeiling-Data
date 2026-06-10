# DropCeiling — Data & Findings

An open record of a 54-day adaptive AR installation: 12 LED panels in a Toronto storefront window that respond to pedestrians, with the run data, diagrams, and findings all in one place.

**The live installation is at [thedropceiling.com](https://thedropceiling.com).** This repository holds the data, the figures, and the analysis.

---

## What's here

| | |
|---|---|
| **Story** | The distilled narrative — what the project is, the seven narrative moves, the canonical figure set. |
| **Findings** | Two independent readings of the run data. **G-series** (11 findings) covers what the system did; **H-series** (10 findings) covers how the tuner actually behaved. |
| **Architecture** | The whole system, from cameras to DMX: meta-parameters, the three nested control loops, the interaction budget, the output funnel. |
| **Figures** | All 58 rendered diagrams (A–H series) with a filterable catalog. |
| **Data** | The 48-day run as 1,063 hourly rows + 48 daily rows + run metadata. Download as JSON, with provenance flags preserved. |
| **Publications** | ACADIA 2026 (submitted), TEI 2027 (planned), interactive engine (planned). |

## Quick links

- **Live installation:** [thedropceiling.com](https://thedropceiling.com)
- **Source code & runtime:** [github.com/npuckett/dc-dev](https://github.com/npuckett/dc-dev)
- **Hardware / project home:** [github.com/npuckett/Drop-Ceiling](https://github.com/npuckett/Drop-Ceiling)

## The numbers

From the verified merged run database (`analysis/merged_run.db`):

- **48 days** of continuous data (Jan 29 – Mar 17, 2026)
- **23.3 million** tracking events
- **12 panels**, **2 cameras**, **30 Hz** light update
- **12 meta-parameters** (6 personality + 6 output multipliers)
- **5 behaviour modes** (idle, flow, aware, engaged, crowd)
- **1,063 hours** of hourly aggregates — [browse the data](https://npuckett.github.io/DropCeiling-Data/examples/homepage/#data)

## File layout

```
DropCeiling-Data/
├── examples/homepage/        the website (p5-phone-style, single index.html)
│   ├── index.html
│   ├── styles/main.css
│   ├── scripts/              data.js, charts.js, nav.js, filter.js
│   ├── assets/diagrams/      58 SVGs (A–H series)
│   ├── assets/photos/        P1–P6 + screenshots/
│   └── downloads/            3 .docx files (ACADIA submission, abstract, field notes)
├── web_data/                 3 static JSONs (hourly, daily, meta) — the data the site fetches
├── _source/                  the source markdown files the site renders from
├── .github/workflows/        GitHub Pages deploy workflow
└── README.md                 (this file)
```

## Credits

- **Nick Puckett** — design, runtime, analysis
- **Joshua Pothen** — design collaborator
- The full system was developed with AI coding agents working against a shared 3D model of the site.

## License

MIT — see [LICENSE](LICENSE).
