# MCP_INTEGRATION — 麦当劳 MCP 集成说明

本文说明本项目实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值。

## 使用的 MCP Server

| 项目 | 值 |
|---|---|
| Server 名称 | 麦当劳中国 MCP Server（`mcd-mcp` / `mcd-order`） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | `Authorization: Bearer <MCP Token>`（Token 从 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请） |
| 限流 | 600 次/分钟/Token |

脱敏配置见 [`mcp-config.example.json`](./mcp-config.example.json)（仅环境变量占位符）。

## 工具清单与用途

| Tool | 用途 | 本项目中的角色 |
|---|---|---|
| `now-time-info` | 当前时间 | 锚定"今天"，活动窗口与过期判断的基准 |
| `query-nearby-stores` | 附近门店查询 | 点餐算账的入口（到店自提/得来速），获取 storeCode/beCode |
| `query-meals` | 门店实时菜单 | 单品/套餐/随心配现价与划线价（模块一核心数据） |
| `calculate-price` | 商品价格计算 | 买单路径复核（含优惠券组合后的应付价） |
| `query-store-coupons` | 门店可用券列表 | 点餐代理下单前的优惠检查 |
| `create-order` | 创建订单 | 点餐代理终步：建单返回支付链接（支付由用户完成，仅确认后调用） |
| `query-order` / `cancel-order` | 订单查询/取消 | 下单后跟踪进度、用户反悔时取消 |
| `query-my-account` | 积分账户详情 | 读取可用积分、本月/下月将过期积分（模块二输入） |
| `mall-points-products` | 积分商城商品列表 | 性价比榜与过期消耗推荐的商品池（模块二/四） |
| `query-lottery-info` | 积分抽奖活动信息 | 奖池、单次成本、服务端资源决策（模块三输入） |
| `draw-lottery` | 执行积分抽奖 | 仅在用户明确确认消耗后调用（模块三动作） |
| `campaign-calendar` | 营销活动日历 | 每日活动简报、热点预告（模块五） |
| `available-coupons` | 可领券列表 | 领券前的清单展示（模块五） |
| `auto-bind-coupons` | 一键领券 | 用户确认后批量领券（模块五动作） |
| `query-my-coupons` | 我的优惠券 | 领券结果核对（模块五） |

## 核心调用流程

```
模块〇（模式路由）
用户意图 → 点餐代理(点餐/饿了/任何时段) | 巨无霸指数(工资/购买力) | 会员管家(积分/抽奖/活动)

模块一（点餐代理·全天候全自主点餐，深夜档绰号"夜航员"）
now-time-info(时段) → query-nearby-stores(营业中/宵夜/24h门店) → query-meals(预算档位组合)
   → 随心配1+1优先 + query-store-coupons 优惠检查 → calculate-price 复核
   → 方案对比表(≤3套) → 用户确认 → create-order(支付链接) → query-order 跟踪

模块二（巨无霸指数）
query-meals(巨无霸实时价) → 月薪÷22÷8=时薪 → 时薪÷单价=巨无霸时薪 → 万物换算

模块三（过期预警）
query-my-account ──┬─ currentMouthExpirePoint = 0 → 输出"账户健康"
                   └─ > 0 → mall-points-products
                              → 计算 积分价值率 = price / point
                              → 筛选 point ≤ 过期分值 → 输出消耗建议表

模块四（抽奖分析）
query-lottery-info ──┬─ drawPoint + prizes[] + drawDecision
                     ├─ 保底分析：min(奖品折算价值) − drawPoint
                     └─ 用户确认消耗 → draw-lottery

模块五（性价比榜）
mall-points-products → 全量在售(status=2) → 价值率排序 → Top 10

模块六（活动联动）
now-time-info → campaign-calendar(±2天) → available-coupons
             → 用户确认 → auto-bind-coupons → query-my-coupons
```

## 业务价值

1. **点餐从"凭感觉"到"看对比表"**：单点/套餐/随心配/积分券四条路径同口径比价，"价格玄学"变成可计算的题。
2. **把"会过期的资产"变成可决策对象**：官方渠道只展示余额，不主动做"过期前最优消耗"决策，本 Skill 补上这一层。
3. **抽奖从"凭感觉"到"算保底"**：用公开奖池与单次成本做保底/期望区间分析，输出可解释的决策建议。
4. **统一价值标尺**：现金、积分、券全部折算"元/分"，跨形态可比，杜绝"积分错觉消费"。
5. **真实消耗类操作全部二次确认**：Skill 层强制护栏，符合个人资产工具的审慎原则。

## 自动化层（GitHub Actions 每日简报）

除对话式调用外，本项目包含一套自动化工作流（`automation/` + `.github/workflows/daily-brief.yml`）：

- 每日北京时间 08:00 由 GitHub Actions 触发，通过 MCP 官方 SDK（Streamable HTTP）调用
  `campaign-calendar` / `query-my-account` / `query-lottery-info` 三个工具生成「今日麦麦情报」
- 天气增强使用 [Open-Meteo](https://open-meteo.com) 免费 API（**非麦当劳能力**，仅作推荐钩子，已明确标注）
- 推送目标是用户自行配置的企微/钉钉/飞书/Telegram 群机器人 webhook，Token 全部存于用户仓库 Secrets

## 兼容性说明

- 本 Skill 在 WorkBuddy（官方合作伙伴）中开发与验证，兼容任意支持 Streamable HTTP 的 MCP Client（Cursor / Cherry Studio / Trae / VSCode 等）。
- 推荐模型：具备工具调用能力的对话模型即可，无额外依赖。
