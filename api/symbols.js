// 展示用代码 → Yahoo Finance 代码。不在表里的直接用原代码（美股、ADR、大部分本地代码本身就和 Yahoo 一致）。
export const YAHOO = {
  "RO.SW": "ROG.SW",
  "UCB.VI": "UCB.BR",
  "WXXWY": "2269.HK",
};

export const toYahoo = t => YAHOO[t] || t;
