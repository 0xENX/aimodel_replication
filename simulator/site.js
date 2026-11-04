// Settings and header shared by the home page and the book page (needs i18n.js first).
// paypal: the donation button made in PayPal (public ids); button can be one id, or { it: "...", en: "..." } for a
// button written in each language; empty = the donation box and buttons stay hidden.
// amazon: the ASIN of each edition; empty = "coming soon on Amazon" stays, an ASIN = a buy button.
// amazonStore: Kindle books can only be bought in the store of one's own country, so the buy links go to the store
// of the visitor's country (from /where, answered by the Worker); countries not listed, and the site run without the
// Worker, use the store of the site language.
// price: the Kindle price in each store, shown as launch price; a store not listed shows no price.
window.SITE = {
  book: { it: "book/The_ReplaceMind_IT.pdf", en: "book/The_ReplaceMind_EN.pdf" },
  amazon: { it: "B0HPL9WNB7", en: "B0HPL8SMR4" },
  amazonStore: {
    it: "amazon.it", en: "amazon.com",
    country: { US: "amazon.com", IT: "amazon.it", SM: "amazon.it", VA: "amazon.it", DE: "amazon.de", AT: "amazon.de",
      FR: "amazon.fr", ES: "amazon.es", NL: "amazon.nl", GB: "amazon.co.uk", IE: "amazon.co.uk", CA: "amazon.ca",
      AU: "amazon.com.au", JP: "amazon.co.jp", IN: "amazon.in", BR: "amazon.com.br", MX: "amazon.com.mx" },
  },
  price: { "amazon.com": "$2.99", "amazon.it": "2,99 €" },
  // trailer: the YouTube id of the book trailer; empty = the trailer boxes stay hidden. The player loads only on click.
  trailer: "gmr-jVeoI0Y",
  paypal: { clientId: "BAAkPVaCyuQ1CL-nZDnU34lPq1uQ-OXe5KyMP6_clgCzmX62UHhxlVOhMlWnipwJ_XdMeU-7SkNUsUhbpA", button: { it: "9V4SVW6LCJYXQ", en: "AZA93J9H9625N" } },
};

// Language flags, mobile menu, links that keep the language, donation buttons
window.siteChrome = function () {
  const lang = window.LANG;
  document.querySelectorAll("a[href*='.html']").forEach(a => {
    const href = a.getAttribute("href");
    if (/^(https?:|mailto:)/.test(href)) return;
    const u = new URL(href, location.href); u.searchParams.set("lang", lang); a.href = u.toString();
  });
  const FLAGS = {
    it: ['<svg viewBox="0 0 3 2" width="22" height="15" aria-hidden="true"><rect width="1" height="2" fill="#009246"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ce2b37"/></svg>', "Italiano"],
    en: ['<svg viewBox="0 0 60 30" width="22" height="15" aria-hidden="true"><clipPath id="ukh"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath><rect width="60" height="30" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#ukh)" stroke="#C8102E" stroke-width="4"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/></svg>', "English"],
  };
  const flags = document.getElementById("flags");
  ["it", "en"].forEach(l => {
    const b = document.createElement("button"); b.type = "button"; b.className = "flag" + (l === lang ? " on" : ""); b.innerHTML = FLAGS[l][0];
    b.title = FLAGS[l][1]; b.setAttribute("aria-label", FLAGS[l][1]); b.setAttribute("aria-pressed", l === lang ? "true" : "false");
    b.onclick = () => {
      if (l === lang) return;
      try { localStorage.setItem("tlf-lang", l); } catch (e) { /* ignore */ }
      const u = new URL(location.href); u.searchParams.set("lang", l); location.href = u.toString();
    };
    flags.appendChild(b);
  });
  const menu = document.getElementById("menu"), nav = document.getElementById("nav");
  menu.onclick = () => { const o = nav.classList.toggle("open"); menu.setAttribute("aria-expanded", o ? "true" : "false"); };
  nav.querySelectorAll("a").forEach(a => a.addEventListener("click", () => { nav.classList.remove("open"); menu.setAttribute("aria-expanded", "false"); }));
  // trailer: a still with a play button; YouTube (no-cookie domain) is contacted only when the reader presses play
  if (SITE.trailer) {
    document.querySelectorAll(".js-trailer-section").forEach(s => { s.hidden = false; });
    document.querySelectorAll(".js-trailer").forEach(box => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "trailer-play";
      b.setAttribute("aria-label", L("Play the book trailer (YouTube)", "Guarda il trailer del libro (YouTube)"));
      b.innerHTML = '<img src="img/trailer.jpg" alt="" width="1280" height="720" loading="lazy"><span class="trailer-icon" aria-hidden="true"></span>' +
        '<span class="trailer-note">' + L("Plays on YouTube", "Si apre con YouTube") + "</span>";
      b.onclick = () => {
        const f = document.createElement("iframe");
        f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(SITE.trailer) + "?autoplay=1&rel=0&hl=" + lang +
          (lang === "it" ? "&cc_lang_pref=it&cc_load_policy=1" : "");
        f.title = L("The ReplaceMind, book trailer", "The ReplaceMind, trailer del libro");
        f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen"; f.allowFullscreen = true;
        b.replaceWith(f);
      };
      box.appendChild(b);
    });
  }
  // Amazon: each edition with its ASIN gets a buy button with the launch price; the "coming soon" lines change once
  // the page's own edition is on sale
  const amazon = SITE.amazon || {};
  document.querySelectorAll("[data-amazon]").forEach(el => {
    if (!amazon[el.dataset.amazon]) return;
    const a = amazonLink(el.dataset.amazon, "btn dark");
    a.innerHTML = L("Buy on Amazon", "Acquista su Amazon") + ' <span aria-hidden="true">→</span>';
    el.replaceWith(a);
    a.after(priceTag(el.dataset.amazon));
  });
  if (amazon[lang]) {
    document.querySelectorAll(".js-amazon-title").forEach(el => { el.textContent = L("Now on Amazon", "Ora su Amazon"); });
    document.querySelectorAll(".js-amazon-text").forEach(el => {
      el.textContent = L("37 chapters, the conclusions, the notes, the references and the appendix with all the relationships of the model. The book is on Amazon, in Italian and English. The simulators on this site stay free.",
        "37 capitoli, le conclusioni, le note, la bibliografia e l’appendice con tutte le relazioni del modello. Il libro è su Amazon, in italiano e in inglese. I simulatori di questo sito restano gratuiti.");
    });
    // home: cover, price and buy button of the site-language edition, right under the title
    document.querySelectorAll(".js-amazon-line").forEach(el => {
      el.before(bookBuy());
      el.textContent = L("Kindle edition · Italian and English", "Edizione Kindle · in italiano e in inglese");
    });
  }
  // donations: buttons lead to the box on the book page, where PayPal opens on top of the site
  const button = SITE.paypal && (typeof SITE.paypal.button === "string" ? SITE.paypal.button : (SITE.paypal.button[lang] || SITE.paypal.button.it));
  if (button) {
    document.querySelectorAll(".js-donate").forEach(d => {
      const u = new URL("libro.html", location.href); u.searchParams.set("lang", lang); u.hash = "donate"; d.href = u.toString(); d.hidden = false;
    });
    document.querySelectorAll(".js-donate-section").forEach(d => { d.hidden = false; });
    const box = document.getElementById("paypal-donate");
    if (box) {
      const s = document.createElement("script");
      s.src = "https://www.paypal.com/sdk/js?client-id=" + encodeURIComponent(SITE.paypal.clientId) +
        "&components=hosted-buttons&disable-funding=venmo&currency=EUR&locale=" + (lang === "it" ? "it_IT" : "en_GB");
      s.onload = () => paypal.HostedButtons({ hostedButtonId: button }).render("#paypal-donate");
      s.onerror = () => { box.textContent = L("PayPal could not be loaded. Please try again later.", "Non è stato possibile caricare PayPal. Riprova più tardi."); };
      document.body.appendChild(s);
    }
  }
};

// Buy links in the store of the visitor's country. Links are drawn at once with the store of the site language and
// moved to the visitor's store when /where answers (kept for the session, so it is asked once).
(function () {
  let store = SITE.amazonStore[window.LANG] || "amazon.com";
  const links = [], prices = [];
  const url = ed => "https://www." + store + "/dp/" + SITE.amazon[ed];
  const draw = () => {
    links.forEach(([a, ed]) => { a.href = url(ed); });
    const price = SITE.price[store];
    prices.forEach(([b, hide]) => { b.textContent = price || ""; hide.hidden = !price; });
  };
  window.amazonLink = (ed, cls) => {
    const a = document.createElement("a");
    a.className = cls; a.target = "_blank"; a.rel = "noopener"; a.href = url(ed);
    links.push([a, ed]);
    return a;
  };
  // the launch price as a tag next to the buy buttons, linked to the edition on Amazon; hidden where the price is unknown
  window.priceTag = ed => {
    const t = amazonLink(ed, "price-tag");
    t.innerHTML = "<small>" + L("Launch price · Kindle", "Prezzo di lancio · Kindle") + "</small><b></b>";
    prices.push([t.querySelector("b"), t]); draw();
    return t;
  };
  // cover, price and button of the edition in the site language, all one link: the home hero and the simulators
  window.bookBuy = () => {
    const ed = window.LANG === "it" ? "it" : "en";
    const box = amazonLink(ed, "book-buy");
    box.innerHTML = '<img src="img/cover-' + ed + '.jpg" alt="" width="64" height="102"><span class="txt"><small>' +
      L("The book · Kindle edition", "Il libro · edizione Kindle") + "</small><b>The ReplaceMind</b><span class=\"pr\">" +
      L("Launch price", "Prezzo di lancio") + " <b></b></span><span class=\"go\">" +
      L("Buy on Amazon", "Acquista su Amazon") + ' <span aria-hidden="true">→</span></span></span>';
    prices.push([box.querySelector(".pr b"), box.querySelector(".pr")]); draw();
    return box;
  };
  const use = c => { const s = SITE.amazonStore.country[c]; if (s) { store = s; draw(); } };
  let country = null;
  try { country = sessionStorage.getItem("tlf-country"); } catch (e) { /* storage blocked: ask again */ }
  if (country) use(country);
  else fetch("/where").then(r => (r.ok ? r.json() : null)).then(j => {
    if (!j || !j.country) return;
    try { sessionStorage.setItem("tlf-country", j.country); } catch (e) { /* ignore */ }
    use(j.country);
  }).catch(() => { /* site without the Worker: the store of the site language stays */ });
})();
