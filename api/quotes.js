// GET /api/quotes —— 免费方案：从 Yahoo Finance 公开图表接口取分钟级报价，不需要 API Key。
// CDN 缓存 60 秒，所有访客共享同一次抓取，每分钟最多 50 次请求。
// 实时市值 = 每日市值快照 × 现价 / 昨收。快照在北京时间 07:17 生成，此时美、欧、亚市场都已收盘，
// 快照市值即对应各股票的昨收，因此这个比例在任何时段都成立。
import { readFile } from "node:fs/promises";
import path from "node:path";
import { toYahoo } from "./symbols.js";

const CHART = "https://query1.finance.yahoo.com/v8/finance/chart/";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

export async function fetchYahoo(symbol) {
  const r = await fetch(`${CHART}${encodeURIComponent(symbol)}?range=1d&interval=5m`, { headers: { "User-Agent": UA } });
  if (!r.ok) throw new Error(`${symbol} ${r.status}`);
  const meta = (await r.json())?.chart?.result?.[0]?.meta;
  if (!meta?.regularMarketPrice) throw new Error(`${symbol} no price`);
  return {
    price: meta.regularMarketPrice,
    prevClose: meta.chartPreviousClose ?? meta.previousClose,
    currency: meta.currency,
    ts: meta.regularMarketTime ? meta.regularMarketTime * 1000 : null,
  };
}

export async function buildQuotes(market, getQuote) {
  const settled = await Promise.allSettled(market.rows.map(r => getQuote(toYahoo(r.ticker))));
  const out = {};
  market.rows.forEach((r, i) => {
    const s = settled[i];
    if (s.status !== "fulfilled" || !s.value.prevClose) return;
    const q = s.value;
    const ratio = q.price / q.prevClose;
    if (!(ratio > 0.5 && ratio < 1.5)) return;          // 异常报价（拆股、错价）丢弃，页面回退到日更
    out[r.ticker] = {
      symbol: toYahoo(r.ticker), price: q.price, currency: q.currency,
      changePct: (ratio - 1) * 100, capUSD: r.capUSD * ratio, ts: q.ts,
    };
  });
  return out;
}

export default async function handler(req, res) {
  try {
    const market = JSON.parse(await readFile(path.join(process.cwd(), "public/data/market.json"), "utf8"));
    const quotes = await buildQuotes(market, fetchYahoo);
    res.setHeader("Cache-Control", "public, s-maxage=60, stale-while-revalidate=300");
    res.status(200).json({ updatedAt: new Date().toISOString(), source: "Yahoo Finance", quotes });
  } catch (e) {
    res.status(502).json({ error: String(e.message || e) });
  }
}
