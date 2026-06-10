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

def find_figure_path(fig_id):
    """Return the relative SVG path for a figure id like 'G1' or 'A7.3b'."""
    diagrams_dir = os.path.join(HERE, "assets", "diagrams")
    if not os.path.isdir(diagrams_dir):
        return None
    for f in os.listdir(diagrams_dir):
        if f.startswith(fig_id + "_") and f.endswith(".svg"):
            return "assets/diagrams/" + f
    return None

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
        '<figure style="margin:10px 0 0; padding:0;">'
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
    return li_html + embed

def add_heading_ids(html):
    """Add id="..." to every <h1>/<h2>/h3>/<h4> based on its text content."""
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

# Hardcoded finding -> figure mapping for findings-g, where the "Show it" lines
# don't include the figure id in the same bullet (it lives in section F's table).
G_FINDING_FIGURES = {
    "finding-1":            "G1",
    "finding-2":            None,  # Finding 2 has no figure in the table
    "finding-3":            "G9",
    "finding-4":            "G6",
    "finding-5":            "G5",
    "finding-6":            "G7",
    "finding-7":            "G3",
    "finding-8":            "G4",
    "finding-9":            "G2",
    "finding-10":           "G10",
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

def process_file(src_path, out_name):
    with open(src_path) as f:
        md_text = f.read()
    html = render_md(md_text)
    html = rewrite_figure_refs(html)
    html = add_heading_ids(html)
    # Special: G-series + H-series use a known finding->figure mapping
    if out_name == "findings-g":
        html = inject_finding_figures(html, G_FINDING_FIGURES, "finding")
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
