// 展示用代码 → Yahoo Finance 代码候选（按顺序尝试，前一个取不到就用下一个）。
// 不在表里的直接用原代码（美股、ADR、大部分本地代码本身就和 Yahoo 一致）。
export const YAHOO = {
  "RO.SW": ["ROG.SW", "RO.SW", "RHHBY"],
  "UCB.VI": ["UCB.BR", "UCBJY"],
  "WXXWY": ["2269.HK", "WXXWY"],
};

export const toYahoo = t => YAHOO[t] || [t];
