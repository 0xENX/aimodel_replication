// Language of the site: English or Italian. Shared by the Job Simulator and the Economy Model.
// The choice comes from ?lang=, then from the last choice saved in this browser, then from the browser language.
// Static texts are translated by matching their exact English HTML; dynamic texts use L(english, italian).
(function () {
  const params = new URLSearchParams(location.search);
  let lang = params.get("lang");
  if (lang !== "it" && lang !== "en") {
    try { lang = localStorage.getItem("tlf-lang"); } catch (e) { lang = null; }
  }
  if (lang !== "it" && lang !== "en") lang = (navigator.language || "en").toLowerCase().startsWith("it") ? "it" : "en";
  try { localStorage.setItem("tlf-lang", lang); } catch (e) { /* storage blocked: the URL still carries the choice */ }
  document.documentElement.lang = lang;

  window.LANG = lang;
  window.L = (en, it) => (lang === "it" ? it : en);

  const FLAG_IT = '<svg viewBox="0 0 3 2" width="22" height="15" aria-hidden="true"><rect width="1" height="2" fill="#009246"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ce2b37"/></svg>';
  const FLAG_EN = '<svg viewBox="0 0 60 30" width="22" height="15" aria-hidden="true"><clipPath id="ukc"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath><rect width="60" height="30" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#ukc)" stroke="#C8102E" stroke-width="4"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/></svg>';

  function go(l) {
    try { localStorage.setItem("tlf-lang", l); } catch (e) { /* ignore */ }
    const u = new URL(location.href); u.searchParams.set("lang", l); location.href = u.toString();
  }

  // Top bar: page links keep the language, flags at the right
  window.i18nNav = function () {
    const bar = document.querySelector(".topnav .in");
    if (!bar) return;
    const NAMES = { "simulator.html": L("Job Simulator", "Simulatore"), "model.html": L("Economy Model", "Modello economico"), "social.html": L("Social Risk", "Rischio sociale") };
    bar.querySelectorAll("a[href$='.html']").forEach(a => {
      const page = a.getAttribute("href");
      if (NAMES[page]) a.textContent = NAMES[page];
      const u = new URL(page, location.href); u.searchParams.set("lang", lang); a.href = u.toString();
    });
    const flags = document.createElement("span"); flags.className = "flags";
    [["it", FLAG_IT, "Italiano"], ["en", FLAG_EN, "English"]].forEach(([l, svg, name]) => {
      const b = document.createElement("button"); b.type = "button"; b.innerHTML = svg; b.title = name; b.setAttribute("aria-label", name);
      b.className = "flag" + (l === lang ? " on" : ""); b.setAttribute("aria-pressed", l === lang ? "true" : "false");
      b.onclick = () => { if (l !== lang) go(l); };
      flags.appendChild(b);
    });
    bar.appendChild(flags);
  };

  // Static texts: replace the exact English HTML with the Italian one
  window.i18nApply = function (dict, selector) {
    if (lang !== "it") return [];
    const missing = [];
    document.querySelectorAll(selector).forEach(el => {
      const key = el.innerHTML.trim().replace(/\s+/g, " ");
      if (!key) return;
      if (dict[key] !== undefined) el.innerHTML = dict[key];
      else if (!el.children.length || el.matches("li, p, .sub, .keys span, label, th")) missing.push(key);
    });
    if (dict.__title) document.title = dict.__title;
    return missing;
  };
})();
