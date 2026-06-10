/* DropCeiling — Data loader
   Fetches the three web_data JSONs at page load and caches on window.DROPCEILING_DATA.
   Falls back gracefully if a fetch fails (charts show a "data unavailable" message). */

(function () {
  "use strict";
  var DATA = { meta: null, daily: null, hourly: null };

  function fetchJSON(url) {
    return fetch(url, { cache: "force-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status + " for " + url);
        return r.json();
      });
  }

  function loadAll(baseURL) {
    baseURL = baseURL || "";
    return Promise.all([
      fetchJSON(baseURL + "web_data/meta.json").then(function (j) { DATA.meta = j; return j; }),
      fetchJSON(baseURL + "web_data/daily.json").then(function (j) { DATA.daily = j; return j; }),
      fetchJSON(baseURL + "web_data/hourly.json").then(function (j) { DATA.hourly = j; return j; }),
    ]).then(function () { return DATA; });
  }

  // Expose
  window.DROPCEILING_DATA = DATA;
  window.DC_loadData = loadAll;
})();
