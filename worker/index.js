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
  // "reset" deletes nothing: it stores today's numbers as the starting point, and the table shows what comes after
  async rebase() {
    const now = Object.fromEntries(await this.ctx.storage.list());
    delete now.baseline;
    now.since = new Date().toISOString();
    await this.ctx.storage.put("baseline", now);
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
  // numbers since the last "reset": the stored starting point is subtracted, nothing is deleted
  const base = data.baseline || {};
  const v = k => Math.max(0, (data[k] || 0) - (base[k] || 0));
  const days = [...new Set(Object.keys(data).filter(k => /^\d{4}-\d{2}-\d{2}\|/.test(k) && v(k) > 0).map(k => k.split("|")[0]))].sort().reverse();
  const cell = n => `<td>${n}</td>`;
  const line = (label, key, cls = "") => `<tr${cls}><th>${label}</th>${files.map(f => cell(v(key(f)))).join("")}${cell(files.reduce((s, f) => s + v(key(f)), 0))}</tr>`;
  const head = `<tr><th></th>${files.map(f => `<th>${f.replace("The_ReplaceMind_", "")}</th>`).join("")}<th>Total</th></tr>`;
  const since = base.since ? `Counting since ${base.since.slice(0, 16).replace("T", " ")} UTC. ` : "";
  return `<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Downloads</title>
<style>body{font:15px system-ui,sans-serif;margin:30px;color:#1f1e1c;background:#f5f0e4}table{border-collapse:collapse}th,td{border:1px solid #d6ccb6;padding:6px 12px;text-align:right}th{background:#ece5d4}tr.robots{color:#8a8070;font-style:italic}</style>
<h1>Downloads of The ReplaceMind</h1><table>${head}${line("Total", f => f)}${days.map(d => line(d, f => d + "|" + f)).join("")}${line("Robots", f => "robot|" + f, ' class="robots"')}</table>
<p style="color:#8a8070">${since}Total and days count readers only. Robots (search engines, link previews, scripts) are counted apart.</p>
<form method="post" onsubmit="return confirm('Start counting again from zero? The numbers so far are kept, only no longer shown.')"><button style="font:inherit;padding:6px 14px;margin-top:10px;cursor:pointer">Reset counters</button></form>`;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/stats") {
      if (!env.STATS_KEY || url.searchParams.get("k") !== env.STATS_KEY) return new Response("Not found", { status: 404 });
      // the button posts back to the same address (key included); after the reset, back to the table
      if (request.method === "POST") {
        await counter(env).rebase();
        return Response.redirect(url.toString(), 303);
      }
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
