#!/usr/bin/env python3
"""生成定投模拟器的数据文件 data.json。
优先使用 FRED 日度数据(SP500 / NASDAQ100 / DEXCHUS),拿不到时回退到 GitHub 上的 datasets 镜像。
用法: python3 gen.py [输出路径]
"""
import csv, io, json, sys, urllib.parse, urllib.request, datetime as dt

OUT = sys.argv[1] if len(sys.argv) > 1 else "data.json"
SHILLER = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"
FX_GH = "https://raw.githubusercontent.com/datasets/exchange-rates/main/data/daily.csv"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        return r.read().decode("utf-8")

def yahoo(symbol):
    """Yahoo Finance 日收盘 [(yyyymmdd, close)],失败返回 None。"""
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol)
           + f"?period1=0&period2={int(dt.datetime.now().timestamp())}&interval=1d&events=history")
    try:
        res = json.loads(get(url, 30))["chart"]["result"][0]
        ts, cl = res["timestamp"], res["indicators"]["quote"][0]["close"]
    except Exception as e:
        print(f"Yahoo {symbol} 不可用: {e}", file=sys.stderr)
        return None
    out = {}
    for t, c in zip(ts, cl):
        if c:
            out[int(dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y%m%d"))] = c
    return sorted(out.items()) or None

def fred(series):
    """返回 [(yyyymmdd, value)],失败返回 None。"""
    try:
        rows = list(csv.reader(io.StringIO(get(FRED.format(series), 20))))
    except Exception as e:
        print(f"FRED {series} 不可用: {e}", file=sys.stderr)
        return None
    out = []
    for r in rows[1:]:
        if len(r) < 2 or r[1] in ("", "."):
            continue
        out.append((int(r[0].replace("-", "")), float(r[1])))
    return out or None

def ymd(s):
    return int(s.replace("-", ""))

notes, sources = [], []

# ---------- 标普500 ----------
sh = list(csv.DictReader(io.StringIO(get(SHILLER))))
monthly, divy = [], []
for r in sh:
    y, m = int(r["Date"][:4]), int(r["Date"][5:7])
    p, d = float(r["SP500"]), float(r["Dividend"])
    if p <= 0:
        continue
    monthly.append((y * 10000 + m * 100 + 15, p))   # Shiller 是月均价,放在月中
    if d > 0:
        divy.append((y * 100 + m, round(d / p, 5)))
last_div = divy[-1][0]
spx_daily = yahoo("^GSPC")
if spx_daily:
    sources.append("标普500:Yahoo Finance 日收盘")
else:
    spx_daily = fred("SP500")
    if spx_daily:
        sources.append("标普500:FRED 日收盘(近10年)")
if spx_daily:
    start = spx_daily[0][0]
    spx = [x for x in monthly if x[0] < start] + spx_daily
    daily_from = start
    sources.append("标普500:日收盘之前的时段用 Shiller 月度均价")
else:
    spx, daily_from = monthly, None
    sources.append("标普500:Shiller 月度序列(datasets/s-and-p-500)")
spx = [x for x in spx if x[0] >= 19280101]
spx_last = spx[-1][0]
notes.append(f"标普500股息率在 {last_div // 100}-{last_div % 100:02d} 之后按 1.3% 估算")

# ---------- 纳指100 ----------
ndx_daily = yahoo("^NDX")
ndx_src = "Yahoo Finance"
if not ndx_daily:
    ndx_daily, ndx_src = fred("NASDAQ100"), "FRED"
if ndx_daily:
    ndx = {"d": [x[0] for x in ndx_daily], "p": [x[1] for x in ndx_daily],
           "dailyFrom": ndx_daily[0][0], "divy": [], "divyDefault": 0.007}
    sources.append(f"纳指100:{ndx_src} 日收盘(1985-10 起)")
    notes.append("纳指100股息率按 0.7% 估算")
else:
    ndx = None
    notes.append("纳指100:今天没拿到数据源,暂不可用")

# ---------- 美元/人民币 ----------
fx = fred("DEXCHUS")
if fx:
    sources.append("美元兑人民币:FRED DEXCHUS 日度")
else:
    fx = [(ymd(r["Date"]), float(r["Exchange rate"])) for r in csv.DictReader(io.StringIO(get(FX_GH)))
          if r["Country"] == "China" and r["Exchange rate"]]
    sources.append("美元兑人民币:美联储 H.10 日度(datasets/exchange-rates 镜像)")

data = {
    "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "sources": sources,
    "notes": notes,
    "spx": {"d": [x[0] for x in spx], "p": [round(x[1], 2) for x in spx], "dailyFrom": daily_from,
            "divy": divy, "divyDefault": 0.013},
    "ndx": ndx,
    "fx": {"d": [x[0] for x in fx], "v": [x[1] for x in fx]},
}
with open(OUT, "w") as f:
    json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
print(f"写入 {OUT}: 标普 {len(spx)} 点(至 {spx_last}),纳指 {len(ndx['d']) if ndx else 0} 点,汇率 {len(fx)} 点(至 {fx[-1][0]})")
