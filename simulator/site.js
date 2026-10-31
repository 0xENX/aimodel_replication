// Settings and header shared by the home page and the book page (needs i18n.js first).
// paypal: the donation button made in PayPal (public ids); button can be one id, or { it: "...", en: "..." } for a
// button written in each language; empty = the donation box and buttons stay hidden.
// amazon: the ASIN of each edition; empty = "coming soon on Amazon" stays, an ASIN = a buy button.
// amazonStore: the store each site language links to (Kindle books can only be bought in the store of one's own
// country, so the Italian site sends both editions to Amazon.it and the English site to Amazon.com).
// price: the Kindle price in the store of each site language, shown as launch price; empty = no price line.
window.SITE = {
  book: { it: "book/The_ReplaceMind_IT.pdf", en: "book/The_ReplaceMind_EN.pdf" },
  amazon: { it: "B0HPL9WNB7", en: "B0HPL8SMR4" },
  amazonStore: { it: "https://www.amazon.it/dp/", en: "https://www.amazon.com/dp/" },
  price: { it: "2,99 €", en: "$2.99" },
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
  // Amazon: each edition with its ASIN gets a buy button in the store of the site language; the "coming soon" lines
  // change once the page's own edition is on sale
  const amazon = SITE.amazon || {};
  const store = (SITE.amazonStore || {})[lang] || "https://www.amazon.com/dp/";
  const price = (SITE.price || {})[lang];
  // the launch price as a tag next to the buy buttons, linked to the edition on Amazon
  const priceTag = href => {
    const t = document.createElement("a");
    t.className = "price-tag"; t.href = href; t.target = "_blank"; t.rel = "noopener";
    t.innerHTML = "<small>" + L("Launch price · Kindle", "Prezzo di lancio · Kindle") + "</small><b>" + price + "</b>";
    return t;
  };
  document.querySelectorAll("[data-amazon]").forEach(el => {
    const asin = amazon[el.dataset.amazon];
    if (!asin) return;
    const url = store + asin;
    const a = document.createElement("a");
    a.className = "btn dark"; a.href = url; a.target = "_blank"; a.rel = "noopener";
    a.innerHTML = L("Buy on Amazon", "Acquista su Amazon") + ' <span aria-hidden="true">→</span>';
    el.replaceWith(a);
    if (price) a.after(priceTag(url));
  });
  if (amazon[lang]) {
    document.querySelectorAll(".js-amazon-title").forEach(el => { el.textContent = L("Now on Amazon", "Ora su Amazon"); });
    document.querySelectorAll(".js-amazon-text").forEach(el => {
      el.textContent = L("37 chapters, the conclusions, the notes, the references and the appendix with all the relationships of the model. The book is on Amazon, in Italian and English. The simulators on this site stay free.",
        "37 capitoli, le conclusioni, le note, la bibliografia e l’appendice con tutte le relazioni del modello. Il libro è su Amazon, in italiano e in inglese. I simulatori di questo sito restano gratuiti.");
    });
    document.querySelectorAll(".js-amazon-line").forEach(el => {
      el.innerHTML = '<a href="' + store + amazon[lang] + '" target="_blank" rel="noopener">' + L("Now on Amazon", "Ora su Amazon") + "</a> · " + L("Italian and English", "in italiano e in inglese");
      if (price) el.before(priceTag(store + amazon[lang]));
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
