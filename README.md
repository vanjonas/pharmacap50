# PharmaCap 50

全球医药公司市值前 50：分钟级行情 + 每天北京时间 08:00 的财报 / 官网新闻晨报。

## 结构

| 路径 | 作用 |
|---|---|
| `public/index.html` | 前端页面，每 60 秒请求一次 `/api/quotes`，每 30 分钟重读每日数据 |
| `public/data/market.json` | 每日市值快照（排名名单、日更市值、前一日对比） |
| `public/data/brief.json` | 每日晨报：50 家公司最新财报、官网新闻、48 小时内要点 |
| `api/quotes.js` | Vercel 函数：从 Yahoo Finance 公开接口取 50 家报价（免费、无需 Key），CDN 缓存 60 秒，所有访客共享一次抓取 |
| `api/symbols.js` | 展示代码 → Yahoo 代码映射 |

每日数据由 Claude 定时任务在 07:17 抓取并提交到本仓库的 `public/data/`，提交后 Vercel 自动重新部署。

## 部署（Vercel）

1. 在 Vercel 导入本仓库，Framework 选 **Other**，不需要构建命令，输出目录 `public`。
2. 不需要任何环境变量。部署完成后访问首页，右上角显示「实时行情 N/50」即为正常。

中国大陆访问 `*.vercel.app` 不稳定，建议绑定自己的域名。

## 本地预览

```bash
MOCK=1 node scripts/dev.js        # 模拟行情
node scripts/dev.js               # 真实 Yahoo 行情
npm test                          # 离线测试报价合并逻辑
```

## 说明

- 实时市值 = 每日市值快照 × 现价 / 昨收。快照在北京时间 07:17 生成，各市场都已收盘，所以这个比例全天成立，汇率按当日快照固定。
- Yahoo 的这个接口是公开但非官方的，没有服务协议保障；某只股票取不到报价时页面自动显示日更市值并标“日更”。如果以后要商用或更稳定，换成付费数据商只需改 `api/quotes.js`。
