#!/usr/bin/env python3
"""Render G1–G10 finding figures from dc-dev SQLite databases into assets/diagrams/."""
import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HOMEPAGE = os.path.dirname(HERE)
OUT_SVG = os.path.join(HOMEPAGE, "assets", "diagrams")
OUT_THUMB = os.path.join(HOMEPAGE, "assets", "diagrams_thumb")

DC_DEV = os.path.expanduser("~/Desktop/dc-dev")
EARLY_DB = os.path.join(DC_DEV, "IO", "tracking_history.db")
LATE_DB = os.path.join(DC_DEV, "tracking_history.db")

WARM = "#e8a23d"
INK = "#1a1a1a"
MUTED = "#555555"
GREY = "#6e6e6e"
LIGHT_GREY = "#9a9a9a"
BG = "#ffffff"

VERSION_LINES = [
    ("2026-02-12", "DB fix"),
    ("2026-02-25", "V5"),
    ("2026-03-02", "V6"),
    ("2026-03-03", "V6.5"),
]

PERSONALITY_KEYS = [
    "responsiveness",
    "energy",
    "exploration",
    "sociability",
    "memory",
    "brightness_global",
]


def _style():
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
    })


def _save(name, fig):
    os.makedirs(OUT_SVG, exist_ok=True)
    os.makedirs(OUT_THUMB, exist_ok=True)
    svg = os.path.join(OUT_SVG, name + ".svg")
    png = os.path.join(OUT_THUMB, name + ".png")
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png, dpi=120, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(f"  {name}")


def _connect(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _merged_hourly():
    """Union hourly_stats from both DBs; on overlap prefer higher total_events."""
    best = {}
    for path in (EARLY_DB, LATE_DB):
        conn = _connect(path)
        for date, hour, ltr, rtl, people, events in conn.execute(
            "SELECT date, hour, left_to_right, right_to_left, unique_people, total_events "
            "FROM hourly_stats"
        ):
            key = (date, hour)
            row = (ltr or 0, rtl or 0, people or 0, events or 0)
            if key not in best or row[3] > best[key][3]:
                best[key] = row
        conn.close()
    return best


def _daily_learnings():
    rows = []
    for path in (EARLY_DB, LATE_DB):
        conn = _connect(path)
        for date, opt, summary in conn.execute(
            "SELECT date, optimal_values_json, strategy_summary "
            "FROM autotune_daily_learnings ORDER BY date"
        ):
            rows.append((date, opt, summary))
        conn.close()
    seen = {}
    for date, opt, summary in rows:
        seen[date] = (opt, summary)
    return sorted(seen.items())


def render_g1():
    learnings = _daily_learnings()
    dates, series = [], {k: [] for k in PERSONALITY_KEYS}
    for date, (opt_json, _) in learnings:
        if not opt_json or opt_json.strip() in ("{}", "null"):
            continue
        try:
            opt = json.loads(opt_json)
        except json.JSONDecodeError:
            continue
        if not opt:
            continue
        dates.append(datetime.strptime(date, "%Y-%m-%d"))
        for k in PERSONALITY_KEYS:
            v = opt.get(k)
            if k == "brightness_global" and v is not None:
                v = v / 3.0  # scale to ~0–1 for chart
            series[k].append(v)
    if not dates:
        raise RuntimeError("G1: no autotune_daily_learnings data")

    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    styles = [
        (INK, "-"),
        (GREY, "-"),
        (LIGHT_GREY, "--"),
        ("#404040", "-."),
        ("#808080", ":"),
        (WARM, "-"),
    ]
    for i, k in enumerate(PERSONALITY_KEYS):
        ys = series[k]
        if not ys or all(v is None for v in ys):
            continue
        color, ls = styles[i % len(styles)]
        ax.plot(dates[:len(ys)], ys, label=k.replace("_", " "), color=color, ls=ls, lw=1.9)

    for dstr, label in VERSION_LINES:
        d = datetime.strptime(dstr, "%Y-%m-%d")
        if dates[0] <= d <= dates[-1]:
            ax.axvline(d, color=LIGHT_GREY, lw=0.8, ls=":", zorder=0)
            ax.text(d, ax.get_ylim()[1], label, fontsize=7, color=MUTED, ha="center", va="bottom")

    ax.set_title("Personality trajectories — daily optimal values (Feb 12 – Mar 2)", fontsize=10, pad=10)
    ax.set_ylabel("Parameter value (brightness scaled ÷3)")
    ax.legend(loc="upper left", fontsize=7, frameon=False, ncol=2)
    ax.grid(True, axis="y", color="#e8e8e8", lw=0.6)
    fig.text(
        0.08, 0.02,
        "Daily optimal-value snapshots (autotune_daily_learnings). Record ends Mar 2: "
        "the V6 tuner stopped writing this table.",
        fontsize=8, color=MUTED,
    )
    _save("G1_personality_trajectories", fig)


def render_g2():
    hourly = _merged_hourly()
  # measured days: skip early estimated Jan window with bad calibration
    by_hour = defaultdict(lambda: [0, 0])
    for (date, hour), (ltr, rtl, _people, events) in hourly.items():
        if date < "2026-02-13":
            continue
        by_hour[hour][0] += rtl
        by_hour[hour][1] += ltr
    hours = list(range(24))
    into = [by_hour[h][0] for h in hours]
    home = [by_hour[h][1] for h in hours]

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    y = np.arange(24)
    ax.barh(y, [-v for v in into], color=GREY, height=0.72, label="Into district (RTL)")
    ax.barh(y, home, color=WARM, height=0.72, label="Homeward (LTR)")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{h:02d}:00" for h in hours])
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel("Directional flow events (aggregated measured days, Feb 13 – Mar 17)")
    ax.set_title("The breathing street — flow by hour", fontsize=10, pad=10)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    fig.text(0.08, 0.02, "10.4M+ directional events across measured days.", fontsize=8, color=MUTED)
    _save("G2_breathing_street", fig)


def render_g3():
    conn = _connect(LATE_DB)
    rows = conn.execute(
        "SELECT timestamp, active_count FROM light_behavior "
        "WHERE datetime >= '2026-03-15' ORDER BY timestamp"
    ).fetchall()
    conn.close()

    episodes = []
    in_ep, start = False, None
    for ts, ac in rows:
        if ac and ac > 0:
            if not in_ep:
                start = ts
                in_ep = True
        elif in_ep:
            episodes.append(ts - start)
            in_ep = False
    if in_ep and start:
        episodes.append(rows[-1][0] - start)

    durations = np.array(episodes)
    bonds = durations >= 30

    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    bins = np.logspace(-1, 3, 40)
    ax.hist(durations, bins=bins, color=GREY, edgecolor=INK, linewidth=0.4, alpha=0.85)
    for boundary, label in [(3, "notice 3s"), (30, "bond 30s")]:
        ax.axvline(boundary, color=WARM, lw=1.2, ls="--")
        ax.text(boundary, ax.get_ylim()[1] * 0.92, label, fontsize=7, color=WARM, ha="left")

    bond_idx = np.where(bonds)[0]
    if len(bond_idx):
        ytop = ax.get_ylim()[1]
        for d in durations[bonds]:
            ax.plot(d, ytop * 0.75, "o", color=WARM, ms=5, markeredgecolor=INK, markeredgewidth=0.5)

    ax.set_xscale("log")
    ax.set_xlabel("Episode duration (seconds)")
    ax.set_ylabel("Count")
    ax.set_title(
        f"Engagement episodes — {len(durations)} total, {bonds.sum()} bond-phase (≥30s)",
        fontsize=10, pad=10,
    )
    fig.text(0.08, 0.02, "V6.5 window (Mar 15–17) from light_behavior active_count runs.", fontsize=8, color=MUTED)
    _save("G3_engagement_episodes", fig)


def render_g4():
    agg_by_hour = defaultdict(list)
    for path in (EARLY_DB, LATE_DB):
        conn = _connect(path)
        for dt, agg in conn.execute(
            "SELECT datetime, aggression_level FROM behavior_adjustments "
            "WHERE aggression_level IS NOT NULL"
        ):
            try:
                h = int(dt[11:13])
            except (TypeError, ValueError):
                continue
            agg_by_hour[h].append(agg)
        conn.close()

    people_by_hour = defaultdict(list)
    for (_, hour), (_ltr, _rtl, people, _) in _merged_hourly().items():
        if people:
            people_by_hour[hour].append(people)

    hours = list(range(24))
    agg_m = [np.mean(agg_by_hour[h]) if agg_by_hour[h] else 0 for h in hours]
    ppl_m = [np.mean(people_by_hour[h]) if people_by_hour[h] else 0 for h in hours]

    fig, ax1 = plt.subplots(figsize=(9.5, 4.0))
    ax2 = ax1.twinx()
    ax1.plot(hours, agg_m, color=WARM, lw=2, label="Aggression (tuner)")
    ax2.plot(hours, ppl_m, color=GREY, lw=1.9, ls="--", label="People / hour")
    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Mean aggression level", color=WARM)
    ax2.set_ylabel("Mean people per hour", color=GREY)
    ax1.set_xticks(hours)
    ax1.set_xticklabels([f"{h:02d}" for h in hours], fontsize=7)
    ax1.set_title("Loneliest at 4 AM — aggression vs traffic", fontsize=10, pad=10)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8, frameon=False)
    fig.text(0.08, 0.02, "217K tuning cycles · opposite phase by design.", fontsize=8, color=MUTED)
    _save("G4_loneliest_hour", fig)


def _gesture_shares(conn, start, end):
    rows = conn.execute(
        "SELECT gesture_type, COUNT(*) FROM light_behavior "
        "WHERE datetime >= ? AND datetime < ? AND gesture_type IS NOT NULL AND gesture_type != '' "
        "GROUP BY gesture_type",
        (start, end),
    ).fetchall()
    total = sum(c for _, c in rows)
    if not total:
        return {}
    return {g: c / total for g, c in rows}


def render_g5():
    early = _connect(EARLY_DB)
    late = _connect(LATE_DB)
    v5 = _gesture_shares(early, "2026-02-23", "2026-02-26")
    v65 = _gesture_shares(late, "2026-03-15", "2026-03-18")
    early.close()
    late.close()

    gestures = sorted(set(v5) | set(v65), key=lambda g: v65.get(g, 0), reverse=True)[:8]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=True)
    for ax, data, title in [
        (axes[0], v5, "V5 era (Feb 23–25)"),
        (axes[1], v65, "V6.5 era (Mar 15–17)"),
    ]:
        vals = [data.get(g, 0) * 100 for g in gestures]
        colors = [WARM if g == "welcome" else GREY for g in gestures]
        ax.barh(gestures, vals, color=colors, edgecolor=INK, linewidth=0.5)
        ax.set_xlabel("Share of gesture ticks (%)")
        ax.set_title(title, fontsize=9)
        ax.invert_yaxis()
    fig.suptitle("Gesture economy — solitary → social", fontsize=10, y=1.02)
    _save("G5_gesture_economy", fig)


def _mode_shares(conn, start, end):
    rows = conn.execute(
        "SELECT mode, COUNT(*) FROM light_behavior "
        "WHERE datetime >= ? AND datetime < ? GROUP BY mode",
        (start, end),
    ).fetchall()
    total = sum(c for _, c in rows)
    return {m: c / total for m, c in rows} if total else {}


def render_g6():
    early = _connect(EARLY_DB)
    late = _connect(LATE_DB)
    v5 = _mode_shares(early, "2026-02-23", "2026-02-26")
    v65 = _mode_shares(late, "2026-03-15", "2026-03-18")
    early.close()
    late.close()

    modes = ["idle", "flow", "aware", "engaged", "crowd"]
    x = np.arange(len(modes))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    ax.bar(x - w / 2, [v5.get(m, 0) * 100 for m in modes], w, label="V5 (Feb 23–25)", color=GREY, edgecolor=INK, linewidth=0.5)
    ax.bar(x + w / 2, [v65.get(m, 0) * 100 for m in modes], w, label="V6.5 (Mar 15–17)", color=WARM, edgecolor=INK, linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(modes)
    ax.set_ylabel("% of light_behavior ticks")
    ax.set_title("Mode time-budget — restructured waiting", fontsize=10, pad=10)
    ax.legend(frameon=False, fontsize=8)
    _save("G6_mode_budget", fig)


def render_g7():
    conn = _connect(LATE_DB)
    rows = conn.execute(
        "SELECT mode, AVG(brightness) FROM light_behavior "
        "WHERE datetime >= '2026-03-15' GROUP BY mode"
    ).fetchall()
    conn.close()
    order = ["idle", "flow", "aware", "engaged", "crowd"]
    vals = {m: v for m, v in rows}
    modes = [m for m in order if m in vals]
    br = [vals[m] for m in modes]

    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    bars = ax.bar(modes, br, color=[WARM if i == len(modes) - 1 else GREY for i in range(len(modes))],
                    edgecolor=INK, linewidth=0.6)
    for bar, v in zip(bars, br):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 8, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_ylabel("Mean DMX brightness")
    ax.set_title("Brightness ladder by mode (V6.5 era)", fontsize=10, pad=10)
    ax.set_ylim(0, max(br) * 1.15)
    _save("G7_brightness_ladder", fig)


def render_g8():
    conn = _connect(LATE_DB)
    zs = [z for (z,) in conn.execute(
        "SELECT z FROM tracking_events WHERE z > 50 AND z < 900"
    )]
    conn.close()
    zs = np.array(zs)

    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.hist(zs, bins=60, range=(50, 700), color=GREY, edgecolor=INK, linewidth=0.3, alpha=0.85)
    ax.axvspan(78, 283, color=WARM, alpha=0.14, label="Active zone (z < 283 cm)")
    ax.axvline(350, color=WARM, lw=1, ls="--")
    ax.axvline(400, color=WARM, lw=1, ls="--")
    ax.set_xlabel("Depth z (cm) — pedestrian positions")
    ax.set_ylabel("Count")
    ax.set_title("Desire line vs alcove — Z occupancy (Mar-era positions)", fontsize=10, pad=10)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    pct_active = (zs < 283).sum() / len(zs) * 100
    fig.text(
        0.08, 0.02,
        f"Peak band 350–400 cm · only {pct_active:.1f}% in active zone · n={len(zs):,}",
        fontsize=8, color=MUTED,
    )
    _save("G8_desire_line", fig)


def render_g9():
    def era_stats(path, start, end):
        conn = _connect(path)
        budgets, depleted = [], 0
        for adj_json, dt in conn.execute(
            "SELECT adjustments_json, datetime FROM behavior_adjustments "
            "WHERE datetime >= ? AND datetime < ? AND adjustments_json IS NOT NULL",
            (start, end),
        ):
            try:
                j = json.loads(adj_json)
            except json.JSONDecodeError:
                continue
            b = j.get("budget_before")
            a = j.get("budget_after")
            if b is None:
                continue
            budgets.append(b)
            if a is not None and a < 5:
                depleted += 1
        conn.close()
        n = len(budgets)
        return (np.mean(budgets) if budgets else 0, depleted / n * 100 if n else 0, n)

    v4_avg, v4_pct, v4_n = era_stats(EARLY_DB, "2026-02-13", "2026-02-24")
    v5_avg, v5_pct, v5_n = era_stats(EARLY_DB, "2026-02-25", "2026-03-03")

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.0))
    for ax, avg, pct, title, n in [
        (axes[0], v4_avg, v4_pct, "V4 era (Feb 13–23)", v4_n),
        (axes[1], v5_avg, v5_pct, "V5 era (Feb 25 – Mar 2)", v5_n),
    ]:
        ax.bar(["Mean budget", "% depleted"], [avg, pct], color=[GREY, WARM], edgecolor=INK, linewidth=0.5)
        ax.set_title(f"{title} · n={n:,}", fontsize=9)
        ax.set_ylim(0, max(avg, pct, 1) * 1.2)
    fig.suptitle("Friction regimes — starved vs never-binding", fontsize=10, y=1.02)
    _save("G9_friction_regimes", fig)


def render_g10():
    learnings = _daily_learnings()
    dates, energy, quotes = [], [], []
    for date, (opt_json, summary) in learnings:
        if not opt_json or opt_json.strip() in ("{}", "null"):
            continue
        try:
            opt = json.loads(opt_json)
        except json.JSONDecodeError:
            continue
        if not opt or "energy" not in opt:
            continue
        dates.append(datetime.strptime(date, "%Y-%m-%d"))
        energy.append(opt["energy"])
        quotes.append((date, summary or ""))

    if not dates:
        raise RuntimeError("G10: no trajectory data")

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    ax.plot(dates, energy, color=INK, lw=2, marker="o", ms=4, markerfacecolor=WARM, markeredgecolor=INK)
    for dstr, label in VERSION_LINES[:3]:
        d = datetime.strptime(dstr, "%Y-%m-%d")
        if dates[0] <= d <= dates[-1]:
            ax.axvline(d, color=LIGHT_GREY, lw=0.8, ls=":")

    # Diary excerpts — pick first review + a few strategy lines
    excerpt_dates = ["2026-02-12", "2026-02-13", "2026-02-25", "2026-03-02"]
    y = 0.95
    for date in excerpt_dates:
        for d, summary in quotes:
            if d == date and summary:
                text = summary[:120] + ("…" if len(summary) > 120 else "")
                fig.text(0.08, y, f"{date}: {text}", fontsize=7, color=MUTED, wrap=True)
                y -= 0.08
                break

    ax.set_title("The diary — strategy summaries on the energy trajectory", fontsize=10, pad=10)
    ax.set_ylabel("Energy (optimal value)")
    ax.grid(True, axis="y", color="#e8e8e8", lw=0.6)
    _save("G10_diary", fig)


def main():
    if not os.path.isdir(DC_DEV):
        raise SystemExit(f"dc-dev not found at {DC_DEV}")
    _style()
    print("Rendering G-series figures from:")
    print(f"  early: {EARLY_DB}")
    print(f"  late:  {LATE_DB}")
    render_g1()
    render_g2()
    render_g3()
    render_g4()
    render_g5()
    render_g6()
    render_g7()
    render_g8()
    render_g9()
    render_g10()
    print("done.")


if __name__ == "__main__":
    main()
