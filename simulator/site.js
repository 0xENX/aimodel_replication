// Settings and header shared by the home page and the book page (needs i18n.js first).
// paypal: the donation button made in PayPal (public ids); button can be one id, or { it: "...", en: "..." } for a
// button written in each language; empty = the donation box and buttons stay hidden.
// amazon: the ASIN of each edition; empty = "coming soon on Amazon" stays, an ASIN = a buy button.
// amazonStore: Kindle books can only be bought in the store of one's own country, so the buy links go to the store
// of the visitor's country (from /where, answered by the Worker); countries not listed, and the site run without the
// Worker, use the store of the site language.
// price: the Kindle price in each store; a store not listed shows no price.
// free: the KDP free days (midnight Pacific Time to midnight); in between the book shows as free in every store, the
// price comes back by itself when they end; only the editions listed in "editions". Empty = no free days.
window.SITE = {
  book: { it: "book/The_ReplaceMind_IT.pdf", en: "book/The_ReplaceMind_EN.pdf" },
  amazon: { it: "B0HPL9WNB7", en: "B0HPL8SMR4" },
  amazonStore: {
    it: "amazon.it", en: "amazon.com",
    country: { US: "amazon.com", IT: "amazon.it", SM: "amazon.it", VA: "amazon.it", DE: "amazon.de", AT: "amazon.de",
      FR: "amazon.fr", ES: "amazon.es", NL: "amazon.nl", GB: "amazon.co.uk", IE: "amazon.co.uk", CA: "amazon.ca",
      AU: "amazon.com.au", JP: "amazon.co.jp", IN: "amazon.in", BR: "amazon.com.br", MX: "amazon.com.mx" },
  },
  price: { "amazon.com": "$5.99" },
  free: { editions: ["en"], from: "2026-11-07T08:00:00Z", to: "2026-11-12T08:00:00Z", until: { en: "Nov 11", it: "11 novembre" } },
  // more: the other books of Marc Molften, shown in the home next to The ReplaceMind (Kindle ASIN, cover, texts)
  more: [
    { asin: "B0HRNQMWR1", title: "The Fake AI Boom That Is Breaking the World", img: "img/cover-fake-ai-boom.jpg",
      price: { "amazon.com": "$3.99" },   // Kindle price per store, as SITE.price, e.g. { "amazon.com": "$4.99", "amazon.it": "4,99 €" }; empty = no price
      kind: { en: "The new book · Essay", it: "Il nuovo libro · Saggio · in inglese" },
      text: { en: "Every day you read that artificial intelligence is making the economy grow. This book looks at where that money really comes from, and what happens when the boom breaks. Not a book about your job: a book about what comes after.",
              it: "Ogni giorno si legge che l’intelligenza artificiale fa crescere l’economia. Questo libro guarda da dove arrivano davvero quei soldi, e cosa succede quando il boom si rompe. Non è un libro sul tuo lavoro: è un libro su quello che viene dopo." } },
  ],
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
    const a = buyLabel(amazonLink(el.dataset.amazon, "btn dark"), el.dataset.amazon);
    el.replaceWith(a);
    a.after(priceTag(el.dataset.amazon));
  });
  if (amazon[lang]) {
    document.querySelectorAll(".js-amazon-title").forEach(el => { el.textContent = L("Now on Amazon", "Ora su Amazon"); });
    document.querySelectorAll(".js-amazon-text").forEach(el => {
      el.textContent = L("37 chapters, the conclusions, the notes, the references and the appendix with all the relationships of the model. The book is on Amazon, in Italian and English. The simulators on this site stay free.",
        "37 capitoli, le conclusioni, le note, la bibliografia e l’appendice con tutte le relazioni del modello. Il libro è su Amazon, in italiano e in inglese. I simulatori di questo sito restano gratuiti.");
    });
    // home: cover, price and buy button of the site-language edition, right under the title (before the
    // description, so that it is seen without scrolling also on short screens)
    document.querySelectorAll(".js-amazon-line").forEach(el => {
      const lead = el.closest(".hero") && el.closest(".hero").querySelector("p.lead");
      const row = document.createElement("div");
      row.className = "hero-books";
      row.append(bookBuy(), ...(SITE.more || []).map(moreBuy));   // The ReplaceMind, then the other books, side by side
      (lead || el).before(row);
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
  const links = [], prices = [], words = [], morePrices = [];
  const url = ed => "https://www." + store + "/dp/" + (SITE.amazon[ed] || ed);   // an edition of this book, or any ASIN
  const fr = SITE.free, now = Date.now();
  const days = !!fr && now >= Date.parse(fr.from) && now < Date.parse(fr.to);
  const free = ed => days && fr.editions.includes(ed);
  const until = days ? fr.until[window.LANG] || fr.until.en : "";
  const draw = () => {
    links.forEach(([a, ed]) => { a.href = url(ed); });
    prices.forEach(([b, hide, ed]) => { const p = free(ed) ? L("FREE", "GRATIS") : SITE.price[store]; b.textContent = p || ""; hide.hidden = !p; });
    words.forEach(([el, normal, gratis, ed]) => { el.innerHTML = free(ed) ? gratis : normal; });
    morePrices.forEach(([b, hide, map]) => { const p = (map || {})[store]; b.textContent = p || ""; hide.hidden = !p; });
  };
  // a text that changes during the free days
  const word = (el, ed, normal, gratis) => { words.push([el, normal, gratis, ed]); return el; };
  const arrow = ' <span aria-hidden="true">→</span>';
  window.buyLabel = (el, ed) => word(el, ed, L("Buy on Amazon", "Acquista su Amazon") + arrow, L("Get it free on Amazon", "Scaricalo gratis su Amazon") + arrow);
  window.amazonLink = (ed, cls) => {
    const a = document.createElement("a");
    a.className = cls; a.target = "_blank"; a.rel = "noopener"; a.href = url(ed);
    links.push([a, ed]);
    return a;
  };
  // the launch price as a tag next to the buy buttons, linked to the edition on Amazon; hidden where the price is unknown
  window.priceTag = ed => {
    const t = amazonLink(ed, "price-tag");
    t.innerHTML = "<small></small><b></b>";
    word(t.querySelector("small"), ed, L("Kindle price", "Prezzo Kindle"), L("Kindle · until " + until, "Kindle · fino all’" + until));
    prices.push([t.querySelector("b"), t, ed]); draw();
    return t;
  };
  // cover, price and button of the edition in the site language, all one link: the home hero and the simulators
  window.bookBuy = () => {
    const ed = window.LANG === "it" ? "it" : "en";
    const box = amazonLink(ed, "book-buy");
    box.innerHTML = '<img src="img/cover-' + ed + '.jpg" alt="" width="64" height="102"><span class="txt"><small>' +
      L("The book · Kindle edition", "Il libro · edizione Kindle") + "</small><b>The ReplaceMind</b><span class=\"pr\">" +
      "<i></i> <b></b></span><span class=\"go\"></span></span>";
    word(box.querySelector(".pr i"), ed, L("Kindle price", "Prezzo Kindle"), L("Until " + until, "Fino all’" + until));
    buyLabel(box.querySelector(".go"), ed);
    prices.push([box.querySelector(".pr b"), box.querySelector(".pr"), ed]); draw();
    return box;
  };
  // another book of the author, next to The ReplaceMind in the home: cover, title and a link to Amazon
  window.moreBuy = b => {
    const box = amazonLink(b.asin, "book-buy more");
    box.innerHTML = '<img src="' + b.img + '" alt="" width="64" height="96"><span class="txt"><small></small><b></b>' +
      '<span class="pr"><i>' + L("Kindle price", "Prezzo Kindle") + '</i> <b></b></span>' +
      '<span class="go">' + L("Buy on Amazon", "Acquista su Amazon") + ' <span aria-hidden="true">→</span></span></span>';
    box.querySelector("small").textContent = b.kind[window.LANG] || b.kind.en;
    box.querySelector("b").textContent = b.title;
    box.title = b.text[window.LANG] || b.text.en;
    morePrices.push([box.querySelector(".pr b"), box.querySelector(".pr"), b.price]); draw();
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
