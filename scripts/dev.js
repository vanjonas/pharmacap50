// 本地预览：node scripts/dev.js（默认抓 Yahoo 真实行情；MOCK=1 用模拟行情）
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import handler, { buildQuotes } from "../api/quotes.js";
const root = path.resolve("public");
const types = { ".html": "text/html; charset=utf-8", ".json": "application/json" };
http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  if (url.pathname === "/api/quotes") {
    if (process.env.MOCK) {
      const market = JSON.parse(await readFile(path.join(root, "data/market.json"), "utf8"));
      const fake = async s => { const p = 50 + (s.length * 7) % 90; return { price: p * (1 + ((s.charCodeAt(0) * 37) % 70 - 35) / 1000), prevClose: p, currency: "USD" }; };
      res.setHeader("content-type", "application/json");
      return res.end(JSON.stringify({ updatedAt: new Date().toISOString(), plan: "mock", quotes: await buildQuotes(market, fake) }));
    }
    const shim = { status(c) { res.statusCode = c; return shim; }, setHeader: (k, v) => res.setHeader(k, v),
      json(o) { res.setHeader("content-type", "application/json"); res.end(JSON.stringify(o)); } };
    return handler(req, shim);
  }
  const f = path.join(root, url.pathname === "/" ? "index.html" : url.pathname);
  if (!f.startsWith(root)) { res.statusCode = 403; return res.end(); }
  try { res.setHeader("content-type", types[path.extname(f)] || "application/octet-stream"); res.end(await readFile(f)); }
  catch { res.statusCode = 404; res.end("not found"); }
}).listen(process.env.PORT || 3000, () => console.log("http://localhost:" + (process.env.PORT || 3000)));
