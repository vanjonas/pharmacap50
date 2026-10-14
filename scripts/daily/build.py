#!/usr/bin/env python3
"""PharmaCap 50 daily builder.
Usage: build.py RUN_DIR DATE(YYYY-MM-DD)
RUN_DIR must hold:
  rank.txt   lines "rank|name|ticker|market cap as shown ($1.040 T / $597.34 B)|price|change|country"
  prev.json  (optional) previous market/latest document as read from the artifact db
  out*.json  per-company {"TICKER": {"filing": {...}|null, "news": [...]}}
Writes RUN_DIR/market_latest.json, RUN_DIR/brief.json
"""
import json, sys, glob, os, datetime
run, date = sys.argv[1], sys.argv[2]
ZH = {"LLY":"礼来","JNJ":"强生","ABBV":"艾伯维","RO.SW":"罗氏","MRK":"默沙东","NVS":"诺华","AZN":"阿斯利康","AMGN":"安进",
"GILD":"吉利德","NVO":"诺和诺德","PFE":"辉瑞","VRTX":"福泰制药","BMY":"百时美施贵宝","CVS":"CVS 健康","SNY":"赛诺菲","GSK":"葛兰素史克",
"MRNA":"Moderna","2359.HK":"药明康德","REGN":"再生元","MRK.DE":"默克集团","4519.T":"中外制药","CSL.AX":"CSL","TAK":"武田药品",
"ARGX":"argenx","BAYN.DE":"拜耳","TEVA":"梯瓦制药","LONN.SW":"龙沙","GALD.SW":"高德美","600276.SS":"恒瑞医药","SUNPHARMA.NS":"太阳药业",
"UCB.VI":"优时比","RVMD":"Revolution Medicines","ONC":"百济神州","4578.T":"大冢控股","SDZ.SW":"山德士","BIIB":"渤健","RPRX":"Royalty Pharma",
"ZTS":"硕腾","068270.KS":"赛尔群","4568.T":"第一三共","ALNY":"Alnylam","WXXWY":"药明生物","WST":"西氏医药","4503.T":"安斯泰来",
"DIVISLAB.NS":"Divi's 实验室","LH":"徕博科","3692.HK":"翰森制药","ROIV":"Roivant","UTHR":"联合治疗","BNTX":"BioNTech","1177.HK":"中国生物制药",
"300760.SZ":"迈瑞医疗","GMAB":"Genmab","4502.T":"武田药品","NOVO-B.CO":"诺和诺德"}
def cap(s):
    s = s.replace("$","").replace(",","").strip()
    v, unit = s.split()[0], s.split()[1] if len(s.split())>1 else "B"
    return float(v) * {"T":1e12,"B":1e9,"M":1e6}[unit[0].upper()]
prev = {}
p = os.path.join(run,"prev.json")
if os.path.exists(p):
    pd = json.load(open(p))
    if pd.get("asOf") != date:
        prev = {r["ticker"]: r for r in pd.get("rows",[])}
    else:  # same-day rerun: keep the earlier comparison base
        prev = {r["ticker"]: {"rank":r.get("prevRank"),"capUSD":r.get("prevCapUSD")} for r in pd.get("rows",[])}
rows = []
for line in open(os.path.join(run,"rank.txt"), encoding="utf8"):
    f = [x.strip() for x in line.strip().split("|")]
    if len(f) < 7: continue
    t = f[2]; pr = prev.get(t, {})
    rows.append({"rank":int(f[0]),"name":f[1],"nameZh":ZH.get(t,""),"ticker":t,"country":f[6],
                 "capUSD":cap(f[3]),"price":f[4],"prevRank":pr.get("rank"),"prevCapUSD":pr.get("capUSD")})
rows.sort(key=lambda r: r["rank"])
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
json.dump({"asOf":date,"fetchedAt":now,"rows":rows,
  "source":"市值来自 companiesmarketcap.com 公开榜单（延迟报价）；财报与新闻取自各公司官网及监管披露页面，链接均指向原文。"},
  open(os.path.join(run,"market_latest.json"),"w"), ensure_ascii=False)
comp = {}
for fn in sorted(glob.glob(os.path.join(run,"out*.json"))):
    comp.update(json.load(open(fn)))
names = {r["ticker"]: (r["nameZh"] or r["name"]) for r in rows}
d0 = datetime.date.fromisoformat(date)
hl = []
for t, c in comp.items():
    items = ([("filing", c["filing"])] if c.get("filing") else []) + [("news", n) for n in c.get("news", [])]
    for kind, i in items:
        try: age = (d0 - datetime.date.fromisoformat(i.get("date","")[:10])).days
        except ValueError: continue
        if 0 <= age <= 2:
            hl.append({"ticker":t,"name":names.get(t,t),"kind":kind,**{k:i.get(k,"") for k in ("title","date","url","summary")}})
hl.sort(key=lambda x: (x["date"], x["kind"]=="filing"), reverse=True)
json.dump({"date":date,"generatedAt":now,"highlights":hl,"companies":comp},
  open(os.path.join(run,"brief.json"),"w"), ensure_ascii=False)
print(f"rows={len(rows)} companies={len(comp)} highlights={len(hl)} brief_bytes={os.path.getsize(os.path.join(run,'brief.json'))}")
