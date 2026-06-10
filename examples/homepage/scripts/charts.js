/* DropCeiling — Charts (vanilla SVG, no dependencies)
   Three small reusable chart functions for the #data section:
   - renderHourlyStrip(sel, hourlyData)  : 1063 hour mini-strip, last 28 days
   - renderDailyTotals(sel, dailyData)   : 48-day daily-people bar chart
   - renderFlowBalance(sel, dailyData)   : 48-day flow balance diverging chart
*/

(function () {
  "use strict";

  var INK = "#1a1a1a";
  var GREY = "#9a9a9a";
  var MID = "#6e6e6e";
  var FAINT = "#d9d9d9";
  var WARM = "#e8a23d";
  var WARM_DARK = "#c47f1d";
  var LINE = "#d8dad4";

  function el(tag, attrs, children) {
    var n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (children) children.forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function text(x, y, str, opts) {
    opts = opts || {};
    var t = el("text", {
      x: x, y: y,
      "font-size": opts.size || 10,
      "font-family": "-apple-system, BlinkMacSystemFont, sans-serif",
      fill: opts.color || MID,
      "text-anchor": opts.anchor || "start",
      "font-weight": opts.weight || 400,
    });
    t.textContent = str;
    return t;
  }
  function clear(sel) {
    var node = typeof sel === "string" ? document.querySelector(sel) : sel;
    if (!node) return null;
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  // ---- renderHourlyStrip: 1063-hour mini-strip (or last N days) ----
  function renderHourlyStrip(sel, hourlyData, opts) {
    opts = opts || {};
    var node = clear(sel);
    if (!node) return;
    if (!hourlyData || !hourlyData.length) {
      node.appendChild(text(0, 20, "hourly data unavailable", { color: MID }));
      return;
    }
    var W = opts.width || Math.max(640, node.clientWidth || 640);
    var H = opts.height || 120;
    var padL = 36, padR = 8, padT = 16, padB = 22;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var data = hourlyData;
    var maxEvents = 0;
    for (var i = 0; i < data.length; i++) if (data[i].events > maxEvents) maxEvents = data[i].events;
    if (maxEvents === 0) maxEvents = 1;
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });
    // y-axis labels
    svg.appendChild(text(padL - 6, padT + 4, "events", { anchor: "end", size: 8 }));
    svg.appendChild(text(padL - 6, padT + innerH, "0", { anchor: "end", size: 8 }));
    svg.appendChild(text(padL - 6, padT + 8, Math.round(maxEvents / 1000) + "K", { anchor: "end", size: 8 }));
    // x-axis: 48 day ticks (every 7 days = ~7 ticks)
    var days = data.length / 24;
    var tickEvery = Math.max(1, Math.round(days / 8));
    for (var h = 0; h < data.length; h += 24 * tickEvery) {
      var x = padL + (h / data.length) * innerW;
      svg.appendChild(el("line", { x1: x, y1: padT + innerH, x2: x, y2: padT + innerH + 3, stroke: GREY, "stroke-width": 0.5 }));
      svg.appendChild(text(x, padT + innerH + 14, data[h].date.slice(5), { anchor: "middle", size: 8 }));
    }
    // bars
    var barW = innerW / data.length;
    for (var j = 0; j < data.length; j++) {
      var e = data[j].events || 0;
      var bh = (e / maxEvents) * innerH;
      var bx = padL + (j / data.length) * innerW;
      var by = padT + innerH - bh;
      var c = (data[j].est === 1) ? GREY : (data[j].src === "report" ? WARM_DARK : INK);
      svg.appendChild(el("rect", { x: bx, y: by, width: Math.max(0.5, barW - 0.3), height: bh, fill: c, opacity: 0.85 }));
    }
    // x-axis line
    svg.appendChild(el("line", { x1: padL, y1: padT + innerH, x2: padL + innerW, y2: padT + innerH, stroke: INK, "stroke-width": 0.5 }));
    node.appendChild(svg);
    // legend
    var legend = el("div", { style: "display:flex; gap:14px; margin-top:8px; font-size:0.82rem; color:" + MID });
    legend.innerHTML = '<span style="display:inline-block; width:10px; height:10px; background:' + INK + '; margin-right:4px; vertical-align:middle"></span>measured &nbsp; ' +
                       '<span style="display:inline-block; width:10px; height:10px; background:' + GREY + '; margin-right:4px; vertical-align:middle"></span>estimated &nbsp; ' +
                       '<span style="display:inline-block; width:10px; height:10px; background:' + WARM_DARK + '; margin-right:4px; vertical-align:middle"></span>report-recovered';
    node.appendChild(legend);
  }

  // ---- renderDailyTotals: 48 daily-people bars ----
  function renderDailyTotals(sel, dailyData, opts) {
    opts = opts || {};
    var node = clear(sel);
    if (!node) return;
    if (!dailyData || !dailyData.length) {
      node.appendChild(text(0, 20, "daily data unavailable", { color: MID }));
      return;
    }
    var W = opts.width || Math.max(640, node.clientWidth || 640);
    var H = opts.height || 180;
    var padL = 36, padR = 8, padT = 18, padB = 24;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var max = 0;
    for (var i = 0; i < dailyData.length; i++) if (dailyData[i].people_sum > max) max = dailyData[i].people_sum;
    if (max === 0) max = 1;
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });
    svg.appendChild(text(padL - 6, padT + 4, "people", { anchor: "end", size: 8 }));
    svg.appendChild(text(padL - 6, padT + innerH, "0", { anchor: "end", size: 8 }));
    svg.appendChild(text(padL - 6, padT + 8, Math.round(max / 1000) + "K", { anchor: "end", size: 8 }));
    // x ticks: ~8
    var tickEvery = Math.max(1, Math.round(dailyData.length / 8));
    for (var d = 0; d < dailyData.length; d += tickEvery) {
      var x = padL + (d / dailyData.length) * innerW;
      svg.appendChild(el("line", { x1: x, y1: padT + innerH, x2: x, y2: padT + innerH + 3, stroke: GREY, "stroke-width": 0.5 }));
      svg.appendChild(text(x, padT + innerH + 14, dailyData[d].date.slice(5), { anchor: "middle", size: 8 }));
    }
    var barW = innerW / dailyData.length;
    for (var k = 0; k < dailyData.length; k++) {
      var p = dailyData[k].people_sum || 0;
      var bh = (p / max) * innerH;
      var bx = padL + (k / dailyData.length) * innerW;
      var by = padT + innerH - bh;
      svg.appendChild(el("rect", { x: bx, y: by, width: Math.max(0.5, barW - 0.5), height: bh, fill: WARM, "fill-opacity": 0.85, stroke: INK, "stroke-width": 0.3 }));
    }
    svg.appendChild(el("line", { x1: padL, y1: padT + innerH, x2: padL + innerW, y2: padT + innerH, stroke: INK, "stroke-width": 0.5 }));
    node.appendChild(svg);
  }

  // ---- renderFlowBalance: diverging horizontal bars, by hour of day ----
  function renderFlowBalance(sel, hourlyData, opts) {
    opts = opts || {};
    var node = clear(sel);
    if (!node) return;
    if (!hourlyData || !hourlyData.length) {
      node.appendChild(text(0, 20, "hourly data unavailable", { color: MID }));
      return;
    }
    // Aggregate ltr/rtl by hour-of-day (across all days).
    var hourLTR = new Array(24).fill(0);
    var hourRTL = new Array(24).fill(0);
    for (var i = 0; i < hourlyData.length; i++) {
      hourLTR[hourlyData[i].hour] += (hourlyData[i].ltr || 0);
      hourRTL[hourlyData[i].hour] += (hourlyData[i].rtl || 0);
    }
    var maxV = 0;
    for (var h = 0; h < 24; h++) {
      if (hourLTR[h] > maxV) maxV = hourLTR[h];
      if (hourRTL[h] > maxV) maxV = hourRTL[h];
    }
    var W = opts.width || Math.max(640, node.clientWidth || 640);
    var H = opts.height || 360;
    var padL = 50, padR = 50, padT = 18, padB = 22;
    var innerW = W - padL - padR, innerH = H - padT - padB;
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: "100%", height: H });
    svg.appendChild(text(padL - 6, padT + 4, "rtl", { anchor: "end", size: 8 }));
    svg.appendChild(text(padL + innerW + 6, padT + 4, "ltr", { anchor: "start", size: 8 }));
    svg.appendChild(text(padL + innerW / 2, padT + 12, "0", { anchor: "middle", size: 8, color: INK }));
    svg.appendChild(el("line", { x1: padL + innerW / 2, y1: padT + 14, x2: padL + innerW / 2, y2: padT + innerH, stroke: INK, "stroke-width": 0.5 }));
    var rowH = innerH / 24;
    var barH = Math.min(10, rowH - 2);
    for (var hh = 0; hh < 24; hh++) {
      var y = padT + hh * rowH + (rowH - barH) / 2;
      var wRTL = (hourRTL[hh] / maxV) * (innerW / 2);
      var wLTR = (hourLTR[hh] / maxV) * (innerW / 2);
      svg.appendChild(el("rect", { x: padL + innerW / 2 - wRTL, y: y, width: wRTL, height: barH, fill: GREY, stroke: INK, "stroke-width": 0.3 }));
      svg.appendChild(el("rect", { x: padL + innerW / 2, y: y, width: wLTR, height: barH, fill: WARM, stroke: INK, "stroke-width": 0.3 }));
      svg.appendChild(text(padL - 6, y + barH / 2 + 3, hh.toString().padStart(2, "0") + ":00", { anchor: "end", size: 8 }));
    }
    node.appendChild(svg);
  }

  window.DC_charts = {
    renderHourlyStrip: renderHourlyStrip,
    renderDailyTotals: renderDailyTotals,
    renderFlowBalance: renderFlowBalance,
  };
})();
