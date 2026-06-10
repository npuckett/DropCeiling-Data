/* DropCeiling — Nav (mobile drawer + scroll-spy)
   Direct port of p5-phone's navigation.js pattern. */

(function () {
  "use strict";

  function init() {
    var body = document.body;
    var menuBtn = document.querySelector(".menu-button");
    var backdrop = document.querySelector(".backdrop");
    var sidebarLinks = document.querySelectorAll(".sidebar-nav a[href^='#']");

    if (menuBtn) {
      menuBtn.addEventListener("click", function () {
        body.classList.toggle("menu-open");
      });
    }
    if (backdrop) {
      backdrop.addEventListener("click", function () {
        body.classList.remove("menu-open");
      });
    }
    sidebarLinks.forEach(function (a) {
      a.addEventListener("click", function () {
        body.classList.remove("menu-open");
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") body.classList.remove("menu-open");
    });

    // Scroll-spy: highlight the matching sidebar link as you scroll.
    var sections = document.querySelectorAll(".content-section[id], section[id]");
    var navLinks = document.querySelectorAll(".sidebar-nav a[href^='#']");
    if (!("IntersectionObserver" in window) || sections.length === 0) return;

    function setActive(id) {
      navLinks.forEach(function (a) {
        var href = a.getAttribute("href");
        if (href === "#" + id) a.classList.add("active");
        else a.classList.remove("active");
      });
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    }, { rootMargin: "-30% 0px -60% 0px", threshold: 0 });
    sections.forEach(function (s) { observer.observe(s); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
