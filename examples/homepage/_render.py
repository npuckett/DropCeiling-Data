#!/usr/bin/env python3
"""
Render the source markdown files in _source/ to HTML fragments in _rendered/.
The fragments are designed to be inlined into index.html (or sub-pages) at
build time, not as standalone pages. Headings get a stable id, relative
figure references are rewritten to point to ../assets/diagrams/.

Run from the homepage directory:  ../../../.venv/bin/python _render.py
"""
import os
import re
import sys
from markdown_it import MarkdownIt

HERE     = os.path.dirname(os.path.abspath(__file__))      # .../examples/homepage
PROJECT  = os.path.dirname(os.path.dirname(HERE))           # DropCeiling-Data
SOURCE   = os.path.join(PROJECT, "_source")
OUT      = os.path.join(HERE, "_rendered")

# Map figure IDs in the markdown text to actual SVG paths (relative to homepage/).
# Pattern: "G1" -> "../assets/diagrams/G1_personality_trajectories.svg"
def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def normalize_fig_id(fig_id):
    """Normalize unicode hyphens and spacing in catalog ids (e.g. C1‑bw → C1-bw)."""
    return fig_id.replace("‑", "-").replace("–", "-").strip()


FIG_ID_IN_HTML_RE = re.compile(
    r"<strong>([A-H](?:\d+(?:\.[0-9a-z]+)?(?:[‑\-]bw)?)|P\d+)</strong>",
    re.IGNORECASE,
)


def find_figure_path(fig_id):
    """Return the asset path for a figure id like 'G1', 'A7.3b', 'C1-bw', or 'P1'.
    Path is homepage-relative (assets/diagrams/... or assets/photos/...) because
    these fragments are fetched via JS and injected into index.html."""
    fig_id = normalize_fig_id(fig_id)

    # Photos (P1–P6)
    if re.match(r"^P\d+$", fig_id, re.IGNORECASE):
        photos_dir = os.path.join(HERE, "assets", "photos")
        if os.path.isdir(photos_dir):
            for f in sorted(os.listdir(photos_dir)):
                if f.startswith(fig_id.upper() + "_"):
                    return "assets/photos/" + f
        return None

    diagrams_dir = os.path.join(HERE, "assets", "diagrams")
    if not os.path.isdir(diagrams_dir):
        return None

    # Sub-figures like A7.3b → file prefix A7_3b_
    if re.search(r"\.\d", fig_id):
        sub = fig_id.replace(".", "_")
        for f in sorted(os.listdir(diagrams_dir)):
            if f.startswith(sub) and f.endswith(".svg"):
                return "assets/diagrams/" + f

    # Series prefix (C1-bw → C1_, then prefer _bw variant)
    m = re.match(r"^([A-Z]\d+)", fig_id, re.IGNORECASE)
    if not m:
        return None
    base = m.group(1).upper()
    matches = [
        f for f in os.listdir(diagrams_dir)
        if f.startswith(base + "_") and f.endswith(".svg")
    ]
    if not matches:
        return None
    want_bw = fig_id.endswith("-bw") or fig_id.endswith("bw")
    if want_bw:
        bw = [f for f in matches if "_bw" in f]
        if bw:
            return "assets/diagrams/" + sorted(bw)[0]
    non_bw = [f for f in matches if "_bw" not in f]
    if non_bw and not want_bw:
        return "assets/diagrams/" + sorted(non_bw)[0]
    return "assets/diagrams/" + sorted(matches)[0]


def make_figure_embed(fig_id, path, catalog_href="figures/index.html"):
    """HTML block for an inline figure embed."""
    return (
        '<figure>'
        '<a href="' + path + '" target="_blank" rel="noopener">'
        '<img src="' + path + '" alt="' + fig_id + '" loading="lazy">'
        '</a>'
        '<figcaption>'
        'Figure ' + fig_id + ' &mdash; '
        '<a href="' + catalog_href + '">view in catalog</a>'
        '</figcaption>'
        '</figure>'
    )

# Build the markdown-it parser with the options we need.
md = (
    MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": True})
    .enable("table")
    .enable("strikethrough")
)

# Post-render: rewrite figure references like "**G1**" near a "Show it:" line
# into inline image embeds. We do this by scanning the rendered HTML for
# patterns.
FIGURE_INLINE_RE = re.compile(
    r'<strong>([A-H](?:\d+(?:\.[0-9a-z]+)?))</strong>'
)

# A separate "Show it:" detector (we'll convert a line that says "Show it" followed
# by a figure id in bold into an inline image).
SHOW_IT_RE = re.compile(
    r'(<li>)?<strong>Show it:?</strong>\s*(?:—|-)?\s*<strong>([A-H](?:\d+(?:\.[0-9a-z]+)?))</strong>'
    r'(.*?)(?=</li>|<strong>|</ul>|$)',
    re.DOTALL
)

def slugify_heading(s):
    return slugify(s)

def render_md(md_text):
    """Render a single markdown file to HTML fragment."""
    # Add a "running" anchor id to every heading for in-page anchor linking.
    env = {}
    tokens = md.parse(md_text + "\n", env)
    for tok in tokens:
        if tok.type == "heading_open":
            level = int(tok.tag[1])  # 'h1' -> 1
            # peek next inline token
            # (we'll set id after we render to HTML)
    html = md.render(md_text, env)
    return html

def rewrite_figure_refs(html):
    """For each <strong>G1</strong> (or A1, H4, etc.) inside a 'Show it:' or
    'See it:' line, replace the strong with an inline <img> of the figure.
    Handles two patterns:
    - H-series: '**Show it:** **H1** — the description'
    - G-series: '**Show it:** ... description ... (Proposed figure **G1**.)'
    For G-series, the figure id appears in the SAME list item, separated by
    long descriptive text. We handle it with a per-paragraph rewrite.
    """
    # Process at the <li>...</li> level so we can grab the whole bullet point.
    out = []
    pos = 0
    li_re = re.compile(r'<li>(.*?)</li>', re.DOTALL)
    last_end = 0
    for m in li_re.finditer(html):
        out.append(html[last_end:m.start()])
        li_content = m.group(1)
        new_li = rewrite_li_with_figure(li_content)
        out.append('<li>' + new_li + '</li>')
        last_end = m.end()
    out.append(html[last_end:])
    return "".join(out)

def rewrite_li_with_figure(li_html):
    """If this list item contains 'Show it:' and a figure id, append the figure."""
    if 'Show it' not in li_html and 'See it' not in li_html:
        return li_html
    m = re.search(r'<strong>([A-H](?:\d+(?:\.[0-9a-z]+)?))</strong>', li_html)
    if not m:
        return li_html
    fig_id = m.group(1)
    path = find_figure_path(fig_id)
    if not path:
        return li_html
    # Replace the strong tag with a tiny inline link, and append the figure AFTER
    # the </strong>... part. To keep the bullet readable, we'll just add a
    # trailing figure block.
    embed = (
        '<div class="figure-block" style="margin:10px 0 0;">'
        + make_figure_embed(fig_id, path, "../figures/index.html")
        + '</div>'
    )
    return li_html + embed


def inject_carried_by_figures(html):
    """After each 'Carried by:' blockquote, embed referenced figures not already
    shown in the following move section (until the next h3)."""
    bq_re = re.compile(r"<blockquote>(.*?)</blockquote>", re.DOTALL)
    out = []
    pos = 0
    for m in bq_re.finditer(html):
        out.append(html[pos:m.start()])
        bq_inner = m.group(1)
        bq_full = m.group(0)
        if "Carried by" not in bq_inner:
            out.append(bq_full)
            pos = m.end()
            continue

        fig_ids = []
        for raw_id in FIG_ID_IN_HTML_RE.findall(bq_inner):
            nid = normalize_fig_id(raw_id)
            if nid not in fig_ids:
                fig_ids.append(nid)

        rest = html[m.end():]
        next_h3 = re.search(r"<h3", rest)
        lookahead = rest[:next_h3.start()] if next_h3 else rest[:3000]
        existing_paths = set(re.findall(r"(?:src|href)=\"([^\"]+)\"", lookahead))

        embeds = []
        for fid in fig_ids:
            path = find_figure_path(fid)
            if not path or path in existing_paths:
                continue
            embeds.append(make_figure_embed(fid, path))

        out.append(bq_full)
        if embeds:
            grid_class = "two-up" if len(embeds) == 2 else ""
            out.append(
                '<div class="figure-block ' + grid_class + '">'
                + "".join(embeds)
                + "</div>"
            )
        pos = m.end()
    out.append(html[pos:])
    return "".join(out)

def add_heading_ids(html):
    """Add id="..." to every <h1>/<h2>/h3>/h4> based on its text content."""
    def repl(m):
        tag = m.group(1)
        attrs = m.group(2) or ""
        inner = m.group(3)
        # Extract text only
        text = re.sub(r"<[^>]+>", "", inner)
        hid = slugify_heading(text)
        if 'id=' in attrs:
            return m.group(0)
        return "<" + tag + attrs + ' id="' + hid + '">' + inner + "</" + tag + ">"
    return re.sub(r"<(h[1-4])([^>]*)>(.*?)</\1>", repl, html, flags=re.DOTALL)

def rewrite_legacy_paths(html):
    """Rewrite old dc-dev paths to the new homepage-relative paths.
    - diagrams/assets/P*  -> ../assets/photos/P*
    - diagrams/png/A*     -> ../assets/diagrams/A* (then strip the .png/.jpg/.jpeg -> .svg if available)
    - diagrams/*.svg      -> ../assets/diagrams/*.svg
    For png -> svg, look for the SVG equivalent.
    """
    def png_to_svg(p):
        # If the path looks like .../diagrams/png/A0_master_overview.png,
        # try to find A0_master_overview.svg in assets/diagrams/
        m = re.search(r"diagrams/png/([A-Za-z0-9_\.\-]+)\.png$", p)
        if not m: return p
        stem = m.group(1)
        svg_path = os.path.join(HERE, "assets", "diagrams", stem + ".svg")
        if os.path.exists(svg_path):
            return "assets/diagrams/" + stem + ".svg"
        return p

    # diagrams/assets/P*.{jpg,png} -> assets/photos/P*.{jpg,png}
    html = re.sub(r'(?:src|href)="diagrams/assets/([^"]+)"',
                  lambda m: m.group(0).replace("diagrams/assets/", "assets/photos/"),
                  html)
    # diagrams/png/A*.png -> assets/diagrams/A*.svg (if svg exists)
    html = re.sub(r'((?:src|href))="diagrams/png/([^"]+)"',
                  lambda m: m.group(1) + '="' + png_to_svg("diagrams/png/" + m.group(2)) + '"',
                  html)
    # diagrams/*.svg -> assets/diagrams/*.svg
    html = re.sub(r'(?:src|href)="diagrams/([^"]+\.svg)"',
                  lambda m: m.group(0).replace("diagrams/", "assets/diagrams/"),
                  html)
    return html

# Hardcoded finding -> figure mapping for findings-g, where the "Show it" lines
# don't include the figure id in the same bullet (it lives in section F's table).
G_FINDING_FIGURES = {
    "finding-1":            "G1",
    "finding-2":            "G10",  # diary + first self-diagnosis (text-as-figure)
    "finding-3":            "G9",
    "finding-4":            "G6",
    "finding-5":            "G5",
    "finding-6":            "G7",
    "finding-7":            "G3",
    "finding-8":            "G4",
    "finding-9":            "G2",
    "finding-10":           None,  # Tuesday/Friday — no G-series figure
    "finding-11":           "G8",
}

H_FINDING_FIGURES = {
    "finding-h1": "H1", "finding-h2": "H2", "finding-h3": "H3",
    "finding-h4": "H4", "finding-h5": "H5", "finding-h6": "H6",
    "finding-h7": "H7", "finding-h8": "H8", "finding-h9": "H9",
    "finding-h10": "H10",
}

def inject_finding_figures(html, mapping, heading_id_prefix):
    """Walk through the HTML, find each finding's heading, then insert the
    appropriate figure block just before the next finding heading (or the
    end of the section). Mapping keys are PREFIX-IDs that match the START of
    the heading id (e.g. 'finding-1' matches 'finding-1-personality-change...')."""
    fig_id_to_path = {}
    for fid in mapping.values():
        if fid:
            p = find_figure_path(fid)
            if p: fig_id_to_path[fid] = p
    # Match any <h3 id="...finding-N..."> (where N matches a mapping key)
    keys = sorted(mapping.keys(), key=lambda k: -len(k))
    pattern = r'(<h3 id="(' + '|'.join(re.escape(k) for k in keys) + r')-[^"]+"[^>]*>.*?</h3>)'
    parts = re.split(pattern, html, flags=re.DOTALL)
    # parts: [pre, h3_full, h3_id, post, h3_full, h3_id, post, ...]
    out = [parts[0]]
    i = 1
    while i + 1 < len(parts):
        h3 = parts[i]
        short_id = parts[i + 1]
        post = parts[i + 2] if i + 2 < len(parts) else ""
        fig_id = mapping.get(short_id)
        if fig_id and fig_id in fig_id_to_path:
            path = fig_id_to_path[fig_id]
            embed = (
                '<figure style="margin:18px 0; padding:0;">'
                '<a href="' + path + '" target="_blank" rel="noopener">'
                '<img src="' + path + '" alt="' + fig_id + '" loading="lazy" '
                'style="display:block; max-width:100%; height:auto; '
                'background:#fff; border:1px solid var(--line); border-radius:6px; padding:8px;">'
                '</a>'
                '<figcaption style="text-align:center; color:var(--muted); font-size:0.88rem; margin-top:6px;">'
                'Figure ' + fig_id + ' &mdash; <a href="../figures/index.html" style="color:var(--ink);">view in catalog</a>'
                '</figcaption>'
                '</figure>'
            )
            out.append(h3 + embed + post)
        else:
            out.append(h3 + post)
        i += 3
    return "".join(out)

G_SERIES_IDS = [
    "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10",
]


def inject_section_f_gallery(html):
    """After section F heading, embed a catalog grid of all G-series figures."""
    h2_id = "f-new-figures-worth-building-in-house-style"
    m = re.search(
        r'(<h2 id="' + re.escape(h2_id) + r'"[^>]*>.*?</h2>)',
        html,
        flags=re.DOTALL,
    )
    if not m:
        return html
    cards = []
    for gid in G_SERIES_IDS:
        path = find_figure_path(gid)
        if not path:
            continue
        cards.append(
            '<a class="figure-thumb" href="' + path + '" target="_blank" rel="noopener" '
            'title="Figure ' + gid + '">'
            '<img src="' + path + '" alt="' + gid + '" loading="lazy">'
            '</a>'
        )
    if not cards:
        return html
    gallery = (
        '<div class="figure-grid g-series-catalog" style="margin:20px 0 28px;">'
        + "".join(cards)
        + '<p style="grid-column:1/-1;color:var(--muted);font-size:0.9rem;margin:0;">'
        'All ten G-series figures (rendered from dc-dev run data). '
        '<a href="figures/index.html">Open the full catalog</a></p>'
        '</div>'
    )
    return html[:m.end()] + gallery + html[m.end():]


def process_file(src_path, out_name):
    with open(src_path) as f:
        md_text = f.read()
    html = render_md(md_text)
    html = rewrite_figure_refs(html)
    html = add_heading_ids(html)
    html = rewrite_legacy_paths(html)
    # Story: embed figures named in "Carried by:" blockquotes
    if out_name == "story":
        html = inject_carried_by_figures(html)
    # Special: G-series + H-series use a known finding->figure mapping
    if out_name == "findings-g":
        html = inject_finding_figures(html, G_FINDING_FIGURES, "finding")
        html = inject_section_f_gallery(html)
    elif out_name == "findings-h":
        html = inject_finding_figures(html, H_FINDING_FIGURES, "finding-h")
    out_path = os.path.join(OUT, out_name + ".html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"  rendered {out_name}.html ({len(html):,} bytes)")
    return out_path

def main():
    if not os.path.isdir(SOURCE):
        print("ERROR: _source/ not found at", SOURCE, file=sys.stderr); sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    print(f"Source: {SOURCE}")
    print(f"Output: {OUT}")
    print()

    # Map source files to output names
    files = [
        ("DROPCEILING_STORY.md",                "story"),
        ("DROPCEILING_FINDINGS.md",             "findings-g"),
        ("DROPCEILING_FINDINGS_H.md",           "findings-h"),
        ("ACADIA_2026_SOFTWARE_REPORT.md",      "software-report"),
        ("ACADIA_2026_DIAGRAM_GUIDE.md",        "diagram-guide"),
        ("ACADIA_2026_DIAGRAMS_RENDERABLE.md",  "diagrams-renderable"),
        ("ACADIA_2026_REFERENCES.md",           "references"),
        ("TEI_2027_PICTORIAL_PLAN.md",          "tei-pictorial-plan"),
    ]
    for fname, out in files:
        src = os.path.join(SOURCE, fname)
        if os.path.exists(src):
            process_file(src, out)
        else:
            print(f"  SKIP {fname} (not found)")

    # analysis/ subdir
    analysis_files = [
        ("DATA_TIMELINE_AND_MERGE.md", "data-timeline"),
        ("WEB_DEPLOYMENT_PLAN.md",     "web-deployment-plan"),
    ]
    for fname, out in analysis_files:
        src = os.path.join(SOURCE, "analysis", fname)
        if os.path.exists(src):
            process_file(src, out)
        else:
            print(f"  SKIP analysis/{fname} (not found)")

    print()
    print("done.")

if __name__ == "__main__":
    main()
