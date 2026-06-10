# examples/homepage/

The DropCeiling data & findings website. Single-page application, no build step.

## Structure

```
homepage/
├── index.html            # the main page (10 sections, all anchors)
├── figures/index.html    # the figure catalog sub-page
├── styles/main.css       # the single stylesheet
├── scripts/              # 4 vanilla-JS files (no dependencies)
│   ├── data.js
│   ├── charts.js
│   ├── nav.js
│   └── filter.js
├── _render.py            # dev-time: convert _source/*.md to _rendered/*.html
├── _rendered/            # dev-time output of _render.py
├── assets/
│   ├── diagrams/         # 58 SVGs
│   └── photos/           # P1–P6 + screenshots/
└── downloads/            # 3 .docx files
```

## How the site works

1. `index.html` loads.
2. The 4 scripts run in order: `data.js` (no-op until called), `charts.js` (defines
   `window.DC_charts`), `nav.js` (mobile drawer + scroll-spy), `filter.js` (figure
   catalog filter for the `#figures` section).
3. The inline `<script>` at the bottom of `index.html`:
   - `fetch()`s `_rendered/story.html`, `_rendered/findings-g.html`, and
     `_rendered/findings-h.html`, and injects them into the corresponding
     section placeholders.
   - `fetch()`s `web_data/{meta,daily,hourly}.json` and renders the 3 charts in
     the `#data` section.

## How to update the prose

The narrative .md files live in `../../_source/`. To regenerate the HTML:

```sh
cd examples/homepage
../../../.venv/bin/python _render.py
git add _rendered/
git commit -m "Re-render from _source"
```

The renderer reads each .md, converts to HTML with `markdown-it-py`, adds id
attributes to headings, and embeds inline figures where the source has
`**Show it:** **GX**` (or in the H-series: anywhere a `**G/H/A/B/C/D/E/F
[number]**` token appears in a `Show it:` bullet).

## Cache-busting

All script and CSS tags use `?v=20260610` query strings. Bump the version
when the file content changes to force a refresh.
