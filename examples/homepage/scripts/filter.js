/* DropCeiling — Figure catalog filter
   Filters figure cards by search query + series. Vanilla DOM, no framework.
   Port of p5-phone's catalog-filters pattern. */

(function () {
  "use strict";

  var FIGURE_CATALOG = [
    // [id, series, title, description, thumb (relative to examples/homepage/)]
    // A-series
    ["A0",  "A", "Master overview", "Pipeline + three nested loops + the point-light output (greyscale).", "assets/diagrams/A0_master_overview.svg"],
    ["A1",  "A", "Top-level pipeline", "3 processes × 2 channels (tracker → controller → panels; OSC + SQLite; WebSocket viewer + meta-tuner).", "assets/diagrams/A1_pipeline.svg"],
    ["A2",  "A", "Three nested loops", "Reaction ⊂ anticipation ⊂ self-tuning — the conceptual core of the system.", "assets/diagrams/A2_nested_loops.svg"],
    ["A3",  "A", "Mode state machine", "IDLE / FLOW / AWARE / ENGAGED / CROWD with stickiness and dwell transitions.", "assets/diagrams/A3_mode_state_machine.svg"],
    ["A4",  "A", "Modulation chain", "Mode base × personality × time-of-day × proximity → light.", "assets/diagrams/A4_modulation_chain.svg"],
    ["A5",  "A", "Trend windows", "1 / 5 / 30 / 60-min windows → activity_anticipation, flow_momentum, energy_level.", "assets/diagrams/A5_trend_windows.svg"],
    ["A6",  "A", "Aggression as a regulated tank", "Inflow / outflow / hourly cap — the attention-seeking state.", "assets/diagrams/A6_aggression_tank.svg"],
    ["A7",  "A", "Self-tuning feedback loop", "PUSH / RESIST / META — each node expanded in A7.1–A7.7.", "assets/diagrams/A7_self_tuning_feedback.svg"],
    ["A7-bw","A", "Self-tuning loop (greyscale)", "The same loop in greyscale + warm accent, for the ACADIA submission.", "assets/diagrams/A7_self_tuning_feedback_bw.svg"],
    ["A8",  "A", "Interaction-budget mechanism", "Refill / spend / throttle — what keeps adaptation deliberate.", "assets/diagrams/A8_budget_mechanism.svg"],
    ["A9",  "A", "Self-analysis mirror", "Light → records own state → reads back → varies (anti-repetition).", "assets/diagrams/A9_self_analysis_mirror.svg"],
    ["A10", "A", "Real-time ingestion", "2× RTSP → batched YOLO → ArUco → OSC :7000 → controller → Art-Net.", "assets/diagrams/A10_ingestion.svg"],
    ["A11", "A", "Web interface — two planes", "WebSocket immediate plane + nightly static-JSON trends plane.", "assets/diagrams/A11_web_two_planes.svg"],
    // A7.x exploded
    ["A7.1","A7.x", "PUSH — what the tuner senses", "Live presence + trends → behavior_status + engagement score.", "assets/diagrams/A7_1_push_signal.svg"],
    ["A7.2","A7.x", "TUNER — SmartAutoTuner.update()", "Full tuner cycle: gate → restore budget → score → gradient sample → deltas → curiosity → RESIST → apply.", "assets/diagrams/A7_2_tuner_pipeline.svg"],
    ["A7.3","A7.x", "RESIST — the friction stack", "4-stage friction: mean-reversion → step clamp → budget → value clamp.", "assets/diagrams/A7_3_resist_forces.svg"],
    ["A7.3b","A7.x", "RESIST worked example", "A +0.050 nudge to 'energy' whittled to +0.012 (ample budget) or +0.006 (throttled).", "assets/diagrams/A7_3b_resist_worked_example.svg"],
    ["A7.4","A7.x", "Meta-parameters state", "12-value state with ranges / floors / caps + slider/behaviour sync.", "assets/diagrams/A7_4_metaparams_state.svg"],
    ["A7.5","A7.x", "behavior_adjustments row", "The row logged each tuner cycle (old/new, deltas, budget before/after/cost).", "assets/diagrams/A7_5_adjustments_record.svg"],
    ["A7.6","A7.x", "Light output", "Meta-params → modulation chain → Art-Net DMX.", "assets/diagrams/A7_6_light_output.svg"],
    ["A7.7","A7.x", "Meta-review pipeline", "3×/day: read 8h → diagnose → compute → write overrides → log.", "assets/diagrams/A7_7_metareview_pipeline.svg"],
    // B-series
    ["B1", "B", "Tiered DB funnel", "Raw 48h → hourly (∞) → daily (∞), with audit / learnings tables.", "assets/diagrams/B1_db_funnel.svg"],
    ["B2", "B", "Concentric nested loops", "Filled-rings alternate to A2.", "assets/diagrams/B2_nested_loops.svg"],
    ["B3", "B", "Installation plan, to scale", "4 panel units + 2 cameras + ArUco markers, in centimetres.", "assets/diagrams/B3_spatial_plan.svg"],
    // C-series
    ["C1",     "C", "The funnel (full colour)", "Whole system → ~9-value light state → 12 DMX bytes.", "assets/diagrams/C1_funnel_to_12.svg"],
    ["C1-bw",  "C", "The funnel (greyscale)", "The collapse to twelve — the strongest single idea.", "assets/diagrams/C1_funnel_to_12_bw.svg"],
    ["C2",     "C", "The pinch point", "The ~9 scalars on PointLight that the renderer reads each frame.", "assets/diagrams/C2_light_state_pinch.svg"],
    ["C3",     "C", "Per-panel math", "get_panel_brightness() runs ×12 each frame.", "assets/diagrams/C3_per_panel_math.svg"],
    ["C4",     "C", "The 12 panels / DMX map", "4 units × 3 panels → channels 0–11 → Art-Net frame → fixtures.", "assets/diagrams/C4_panel_dmx_map.svg"],
    ["C5",     "C", "One frame (~30 Hz)", "The actors and call order — proving the funnel re-runs every frame.", "assets/diagrams/C5_per_frame_sequence.svg"],
    // D-series
    ["D1", "D", "Run totals (54 days, log-scale)", "Estimated run totals: ~15M events, ~3.1M flow updates, ~1M visitors.", "assets/diagrams/D1_run_totals.svg"],
    ["D2", "D", "Fast vs slow evaluations", "Tens of thousands of fast adjustments/day, governed by a handful of slow reviews.", "assets/diagrams/D2_eval_cadence.svg"],
    // E-series
    ["E1", "E", "Gesture plate (8 motion glyphs)", "Nod, lean, sway, orbit, settle, breathe, sweep, focus — with real centimetre amplitudes + dwell phase.", "assets/diagrams/E1_gesture_plate.svg"],
    ["E3", "E", "Personality drift (radar)", "6-axis radar: neutral start vs as-deployed after 54 days.", "assets/diagrams/E3_personality_radar.svg"],
    ["E4", "E", "One day in the life", "24-hour activity (people/hr) with rush-hour peak + a mode lane (idle/flow/aware/engaged).", "assets/diagrams/E4_daily_rhythm.svg"],
    // F-series
    ["F1", "F", "Software vs data timeline", "Capture volume over the version milestones (V2 → V6.5c).", "assets/diagrams/F1_software_data_timeline.svg"],
    ["F2", "F", "The calibration artifact", "Active-zone share: the impossible ~97% pre-fix plateau collapsing to ~1–12%.", "assets/diagrams/F2_calibration_artifact.svg"],
    ["F3", "F", "Tiered retention recovered the lost week", "Raw 48h → hourly → daily report — how Feb 3–9 survived.", "assets/diagrams/F3_report_recovery.svg"],
    // G-series
    ["G1",  "G", "Punctuated personality", "19 daily snapshots of 5 meta-parameters; version steps as warm rules.", "assets/diagrams/G1_personality_trajectories.svg"],
    ["G2",  "G", "The breathing street", "Diverging flow-by-hour: 08:00 inhales / 16:00 exhales (10.4M directional events).", "assets/diagrams/G2_breathing_street.svg"],
    ["G3",  "G", "The fleeting 758 + twelve bonds", "Log-scale episode-duration histogram with the dwell-phase boundaries.", "assets/diagrams/G3_engagement_episodes.svg"],
    ["G4",  "G", "Loneliest at 4 AM", "Aggression (warm) vs people (grey) over 24h, in opposite phase.", "assets/diagrams/G4_loneliest_hour.svg"],
    ["G5",  "G", "Solitary → social", "Two ranked gesture bars (V5 / V6.5); 'welcome' highlighted in the warm accent.", "assets/diagrams/G5_gesture_economy.svg"],
    ["G6",  "G", "Restructured waiting", "Mode-time bars (V5 / V6.5); idle redistributed to flow/aware.", "assets/diagrams/G6_mode_budget.svg"],
    ["G7",  "G", "The brightness ladder", "Average DMX brightness by mode (idle 30 → crowd 388, cap 600).", "assets/diagrams/G7_brightness_ladder.svg"],
    ["G8",  "G", "The desire line misses the alcove", "Z-occupancy histogram with active / passive zone bands; peak at z 350–400 cm.", "assets/diagrams/G8_desire_line.svg"],
    ["G9",  "G", "Two friction regimes", "Budget level + %-depleted, cliff at the V5 update.", "assets/diagrams/G9_friction_regimes.svg"],
    ["G10", "G", "The diary", "Verbatim strategy_summary excerpts (Day 1, first self-review, V5, V6) anchored on the energy trajectory.", "assets/diagrams/G10_diary.svg"],
    // H-series
    ["H1",  "H", "Tuner behaviour depends on regime", "4×12 heatmap: mean per-cycle Δparam split by activity regime.", "assets/diagrams/H1_regime_deltas.svg"],
    ["H2",  "H", "The first self-diagnosis", "Feb 13 10:23 — 8 of 12 parameters at 96.6% clamp, memory at 100%.", "assets/diagrams/H2_meta_review.svg"],
    ["H3",  "H", "Per-cycle aggression × day × hour", "The same data as G4 un-averaged; 4 AM dark band / 14:00 light band visible on every day.", "assets/diagrams/H3_aggression_heatmap.svg"],
    ["H4",  "H", "The 12-dial personality = 3 factors", "Daily net-change heatmap with 3 clusters boxed (outputs r=0.99, personality r=0.99, trade-offs r=−0.94).", "assets/diagrams/H4_param_clusters.svg"],
    ["H5",  "H", "Behavioural richness tripled (Mar 3)", "Shannon entropy of per-day mode distribution; the V6 step is a discontinuity.", "assets/diagrams/H5_mode_entropy.svg"],
    ["H6",  "H", "Where the 758 episodes happened", "3 days × 24 hours grid; Mar 16 17:00 is the hottest cell (56 episodes).", "assets/diagrams/H6_episode_grid.svg"],
    ["H7",  "H", "Spatial footprint of each mode", "Density of light (x, z) per mode in V6.5; engaged pulls forward 9 cm, crowd 14 cm.", "assets/diagrams/H7_mode_footprints.svg"],
    ["H8",  "H", "Motion vs posture", "Mean target (x, z) per gesture; sway / orbit / sweep at z=+20, the others at z=0.", "assets/diagrams/H8_gesture_spatial.svg"],
    ["H9",  "H", "The light took a week to come on", "48-day daily-mean brightness; first 5 days = 0 DMX, V6 deployment = the cliff.", "assets/diagrams/H9_brightness_timeline.svg"],
    ["H10", "H", "Per-param step distribution, by regime", "8 small multiples of std and mean per cycle; std grows in RUSH.", "assets/diagrams/H10_step_distribution.svg"],
  ];

  function init() {
    var catalogSel = document.querySelector("[data-catalog]");
    if (!catalogSel) return;
    var searchInput = catalogSel.querySelector("[data-catalog-search]");
    var seriesSel = catalogSel.querySelector("[data-catalog-series]");
    var gridSel = catalogSel.querySelector("[data-catalog-grid]");
    var statusSel = catalogSel.querySelector("[data-catalog-status]");
    // Optional data-catalog-base="../../assets/diagrams/" lets a sub-page
    // override the prefix; default is "assets/diagrams/" (works from the
    // homepage root). Use the pre-rendered PNG thumbnails for the catalog
    // cards (cleaner text rendering, no foreignObject issues) — they live
    // alongside the SVGs in assets/diagrams_thumb/.
    var svgPrefix = catalogSel.getAttribute("data-catalog-base") || "assets/diagrams/";
    var thumbPrefix = svgPrefix.replace(/\/diagrams\/$/, "/diagrams_thumb/");
    var useThumbs = catalogSel.getAttribute("data-catalog-thumb") !== "false";

    // Render all cards
    function render(filter) {
      filter = filter || function () { return true; };
      gridSel.innerHTML = "";
      var shown = 0;
      FIGURE_CATALOG.forEach(function (entry) {
        if (!filter(entry)) return;
        var id = entry[0], series = entry[1], title = entry[2], desc = entry[3], thumb = entry[4];
        var card = document.createElement("article");
        card.className = "figure-card";
        // The thumb field can be either an SVG or a PNG path. If it already
        // has an extension, use it as-is; otherwise derive the PNG thumb
        // (replacing the .svg with .png) and the SVG link from the base name.
        var baseName;
        var thumbExt;
        if (/\.svg$/i.test(thumb)) {
          baseName = thumb.replace(/^.*\//, "").replace(/\.svg$/i, "");
          thumbExt = ".png";
        } else {
          baseName = thumb.replace(/^.*\//, "").replace(/\.\w+$/, "");
          thumbExt = thumb.replace(/^[^.]*\.(\w+)$/, ".$1");
        }
        var thumbImg = useThumbs
          ? (thumbPrefix + baseName + thumbExt).replace(/\.svg$/i, ".png")
          : (svgPrefix + baseName + ".svg");
        // The link to the full file (for "view in catalog" / "open in new tab").
        // For figures whose thumb points to a PNG, link to the PNG too.
        var fullLink;
        if (/\.svg$/i.test(thumb)) {
          fullLink = svgPrefix + baseName + ".svg";
        } else {
          fullLink = thumbPrefix + baseName + thumbExt;
        }
        card.innerHTML =
          '<a class="figure-thumb" href="' + fullLink + '" target="_blank" rel="noopener" title="Open ' + id + ' at full size">' +
          '<img src="' + thumbImg + '" alt="' + id + ' — ' + title + '" loading="lazy">' +
          '</a>' +
          '<span class="figure-id">' + id + ' · ' + series + '</span>' +
          '<h4>' + title + '</h4>' +
          '<p>' + desc + '</p>';
        gridSel.appendChild(card);
        shown++;
      });
      if (statusSel) statusSel.textContent = "Showing " + shown + " of " + FIGURE_CATALOG.length + " figures.";
    }
    function currentFilter() {
      var q = (searchInput && searchInput.value || "").toLowerCase().trim();
      var s = (seriesSel && seriesSel.value || "").trim();
      return function (entry) {
        if (s && entry[1] !== s) return false;
        if (q) {
          var hay = (entry[0] + " " + entry[1] + " " + entry[2] + " " + entry[3]).toLowerCase();
          if (hay.indexOf(q) === -1) return false;
        }
        return true;
      };
    }
    if (searchInput) searchInput.addEventListener("input", function () { render(currentFilter()); });
    if (seriesSel) seriesSel.addEventListener("change", function () { render(currentFilter()); });
    render(currentFilter());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
