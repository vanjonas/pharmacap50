// 用伪造的报价测试 buildQuotes，不需要网络
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
import { buildQuotes } from "../api/quotes.js";
const market = JSON.parse(await readFile(new URL("../public/data/market.json", import.meta.url), "utf8"));
const asked = [];
const fake = async s => {
  asked.push(s);
  if (s === "BNTX") throw new Error("429");                 // 单只失败不影响其他
  if (s === "PFE") return { price: 50, prevClose: 25 };     // 异常比例被丢弃
  if (s === "ROG.SW") throw new Error("404");               // 第一个候选失败 → 用下一个
  return { price: 101, prevClose: 100, currency: s.endsWith(".T") ? "JPY" : "USD" };
};
const q = await buildQuotes(market, fake);
assert.ok(asked.includes("ROG.SW") && asked.includes("2269.HK") && asked.includes("UCB.BR"));
assert.ok(Math.abs(q.LLY.capUSD - market.rows[0].capUSD * 1.01) < 1);
assert.ok(Math.abs(q.LLY.changePct - 1) < 1e-9);
assert.equal(q.BNTX, undefined);
assert.equal(q.PFE, undefined);
assert.equal(q["RO.SW"].symbol, "RO.SW");
assert.equal(Object.keys(q).length, 48);
console.log("ok: 48/50 合并正确，失败和异常报价已回退到日更");
