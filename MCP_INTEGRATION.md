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
| `query-my-account` | 积分账户详情 | 读取可用积分、本月/下月将过期积分（模块一输入） |
| `mall-points-products` | 积分商城商品列表 | 性价比榜与过期消耗推荐的商品池（模块一/三） |
| `query-lottery-info` | 积分抽奖活动信息 | 奖池、单次成本、服务端资源决策（模块二输入） |
| `draw-lottery` | 执行积分抽奖 | 仅在用户明确确认消耗后调用（模块二动作） |
| `campaign-calendar` | 营销活动日历 | 每日活动简报、热点预告（模块四） |
| `available-coupons` | 可领券列表 | 领券前的清单展示（模块四） |
| `auto-bind-coupons` | 一键领券 | 用户确认后批量领券（模块四动作） |
| `query-my-coupons` | 我的优惠券 | 领券结果核对（模块四） |

## 核心调用流程

```
模块一（过期预警）
query-my-account ──┬─ currentMouthExpirePoint = 0 → 输出"账户健康"
                   └─ > 0 → mall-points-products
                              → 计算 积分价值率 = price / point
                              → 筛选 point ≤ 过期分值 → 输出消耗建议表

模块二（抽奖分析）
query-lottery-info ──┬─ drawPoint + prizes[] + drawDecision
                     ├─ 保底分析：min(奖品折算价值) − drawPoint
                     └─ 用户确认消耗 → draw-lottery

模块三（性价比榜）
mall-points-products → 全量在售(status=2) → 价值率排序 → Top 10

模块四（活动联动）
now-time-info → campaign-calendar(±2天) → available-coupons
             → 用户确认 → auto-bind-coupons → query-my-coupons
```

## 业务价值

1. **把"会过期的资产"变成可决策对象**：官方渠道只展示余额，不主动做"过期前最优消耗"决策，本 Skill 补上这一层。
2. **抽奖从"凭感觉"到"算保底"**：用公开奖池与单次成本做保底/期望区间分析，输出可解释的决策建议。
3. **统一价值标尺**：商城商品用"元/分"统一折算，跨类目可比，杜绝"积分错觉消费"。
4. **真实消耗类操作全部二次确认**：Skill 层强制护栏，符合个人资产工具的审慎原则。

## 兼容性说明

- 本 Skill 在 WorkBuddy（官方合作伙伴）中开发与验证，兼容任意支持 Streamable HTTP 的 MCP Client（Cursor / Cherry Studio / Trae / VSCode 等）。
- 推荐模型：具备工具调用能力的对话模型即可，无额外依赖。
