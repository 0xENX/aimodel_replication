// thereplacemind.com: the site is static (assets in _site); this Worker runs only for /book/* and /stats.
// It counts the downloads of the book files, one number per file, with no data about the visitors
// (no IP, no cookie). The numbers are visible only at /stats?k=<STATS_KEY>, a secret set in the Cloudflare dashboard.
import { DurableObject } from "cloudflare:workers";

const FILES = new Set([
  "The_ReplaceMind_IT.pdf", "The_ReplaceMind_IT.epub",
  "The_ReplaceMind_EN.pdf", "The_ReplaceMind_EN.epub",
]);

// search engines, link previews and scripts download the files too: they are counted apart, not as readers
const ROBOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|headless|curl|wget|python|java\/|go-http|okhttp|axios|node-fetch/i;

export class Downloads extends DurableObject {
  async hit(name) {
    const day = new Date().toISOString().slice(0, 10);
    const total = ((await this.ctx.storage.get(name)) || 0) + 1;
    const daily = ((await this.ctx.storage.get(day + "|" + name)) || 0) + 1;
    await this.ctx.storage.put({ [name]: total, [day + "|" + name]: daily });
  }
  async robot(name) {
    const key = "robot|" + name;
    await this.ctx.storage.put(key, ((await this.ctx.storage.get(key)) || 0) + 1);
  }
  async all() {
    return Object.fromEntries(await this.ctx.storage.list());
  }
}

const counter = env => env.DOWNLOADS.get(env.DOWNLOADS.idFromName("book"));

// a PDF viewer may ask for the same file in pieces (Range): only the first piece counts
function isNewDownload(request) {
  if (request.method !== "GET") return false;
  const range = request.headers.get("Range");
  return !range || /^bytes=0-/.test(range);
}

function statsPage(data) {
  const files = [...FILES];
  const days = [...new Set(Object.keys(data).filter(k => /^\d{4}-\d{2}-\d{2}\|/.test(k)).map(k => k.split("|")[0]))].sort().reverse();
  const cell = v => `<td>${v || 0}</td>`;
  const head = `<tr><th></th>${files.map(f => `<th>${f.replace("The_ReplaceMind_", "")}</th>`).join("")}<th>Total</th></tr>`;
  const total = `<tr><th>Total</th>${files.map(f => cell(data[f])).join("")}${cell(files.reduce((s, f) => s + (data[f] || 0), 0))}</tr>`;
  const rows = days.map(d => `<tr><th>${d}</th>${files.map(f => cell(data[d + "|" + f])).join("")}${cell(files.reduce((s, f) => s + (data[d + "|" + f] || 0), 0))}</tr>`).join("");
  const robots = `<tr class="robots"><th>Robots</th>${files.map(f => cell(data["robot|" + f])).join("")}${cell(files.reduce((s, f) => s + (data["robot|" + f] || 0), 0))}</tr>`;
  return `<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Downloads</title>
<style>body{font:15px system-ui,sans-serif;margin:30px;color:#1f1e1c;background:#f5f0e4}table{border-collapse:collapse}th,td{border:1px solid #d6ccb6;padding:6px 12px;text-align:right}th{background:#ece5d4}tr.robots{color:#8a8070;font-style:italic}</style>
<h1>Downloads of The ReplaceMind</h1><table>${head}${total}${rows}${robots}</table>
<p style="color:#8a8070">Total and days count readers only. Robots (search engines, link previews, scripts) are counted apart, since this change.</p>`;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/stats") {
      if (!env.STATS_KEY || url.searchParams.get("k") !== env.STATS_KEY) return new Response("Not found", { status: 404 });
      return new Response(statsPage(await counter(env).all()), { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
    }
    const response = await env.ASSETS.fetch(request);
    if (url.pathname.startsWith("/book/")) {
      const name = decodeURIComponent(url.pathname.slice("/book/".length));
      if (response.ok && FILES.has(name) && isNewDownload(request)) {
        const robot = ROBOT.test(request.headers.get("User-Agent") || "robot");
        ctx.waitUntil((robot ? counter(env).robot(name) : counter(env).hit(name)).catch(() => {}));
      }
    }
    return response;
  },
};
