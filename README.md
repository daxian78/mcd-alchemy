# 麦门积分炼金术 · McD Points Alchemy

> 把麦当劳积分当资产管：不浪费每一分，不乱抽每一次。
> 基于麦当劳官方 MCP（mcd-order）的积分分析与决策 Skill。

![demo](docs/demo.gif) <!-- TODO: 演示 GIF，发布前替换 -->

## 一个反直觉的发现

> 截至 2026-10-09 的公开奖池：积分抽奖 **24 积分/次**，奖池中价值最低的奖品是 **30 积分**——
> 也就是说，**抽一次最差也能净赚 6 积分**，其余奖品全是真实优惠券（立减券、5 折券）。
> （按当前公开奖池推断，官方未公示概率，实际以活动页为准。）

这个发现就是本项目的起点：**既然积分能被"算"，那就把它工具化。**

## 它能做什么

| 模块 | 解决什么问题 | 背后的 MCP 工具 |
|---|---|---|
| ⏰ 过期积分预警 | 每月 silently 清零的积分，到期前给你"最优消耗路径" | `query-my-account` + `mall-points-products` |
| 🎰 抽奖保底分析器 | 抽奖前先算：保底值多少、期望区间多少、值不值得抽 | `query-lottery-info`（+确认后 `draw-lottery`） |
| 📊 积分性价比榜 | 商城商品统一折算"元/分"标尺，跨类目排出真值榜 | `mall-points-products` |
| 📅 活动领券联动 | 今日/明日活动 + 可领券一键收好 | `campaign-calendar` + `available-coupons` |

**在线演示（无需 Token）**：打开 [`demo/index.html`](./demo/index.html)，全部基于 2026-10-09 真实接口数据。

## 快速开始（3 分钟）

**第 1 步：申请麦当劳 MCP Token**

访问 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) → 手机号登录 → 控制台 → 激活 MCP Token。

**第 2 步：把麦当劳 MCP 接入你的 AI 客户端**

以 WorkBuddy 为例（Cursor / Cherry Studio / Trae 同理）：
左侧【专家·技能·连接器】→【连接器】→【自定义连接器】→【配置 MCP】→ 粘贴下方 JSON（**替换 Token**）→ 保存并启用。

```json
{
  "mcpServers": {
    "mcd-order": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer 你的MCP_TOKEN"
      }
    }
  }
}
```

**第 3 步：装载本 Skill**

把 [`skills/mcd-points-alchemy/SKILL.md`](./skills/mcd-points-alchemy/SKILL.md) 放入你的 Skill 目录（WorkBuddy：`.workbuddy/skills/` 或用户级 `~/.workbuddy/skills/`）。

**第 4 步：开聊**

```
我的麦当劳积分快过期了吗？怎么花最值？
现在抽奖划算吗？帮我算算保底。
给我出今天的麦麦情报简报。
```

## 设计原则

1. **消耗型操作三重确认**——抽奖/兑换/下单前，先展示"花多少、换什么"，你点头才执行。
2. **证据标注**——实时数据标注时间戳；推算结论（如抽奖期望）标注前提与局限；算不了就直说。
3. **不诱导消费**——该说"攒着别花"的时候直说，积分不是花得越多越聪明。

## 目标用户

- 麦当劳会员里"积分躺在账户里等过期"的大多数人
- 喜欢用 MCP / Agent 折腾个人自动化工具链的开发者
- 羊毛党：想把每一分积分花出最大价值的人

## 文件结构

```
mcd-points-alchemy/
├── README.md                        # 本文件
├── CONTEST_DECLARATION.md           # 参赛声明（官方模板，未改动）
├── MCP_INTEGRATION.md               # MCP 工具集成与调用流程
├── mcp-config.example.json          # 脱敏 MCP 配置（环境变量占位符）
├── skills/mcd-points-alchemy/SKILL.md   # Skill 主体（分析框架）
├── demo/index.html                  # 交互演示页（内置真实数据快照）
└── docs/
    ├── data-snapshots/              # 接口数据快照（可复现）
    └── demo.gif                     # 演示动图
```

## 注意事项

- 本项目为参赛作品，由个人独立开发，**非麦当劳官方产品**；餐品、积分、活动信息以麦当劳官方渠道实时结果为准。
- 麦当劳 MCP 限流 600 次/分钟/Token，批量查询请稍作间隔。
- 抽奖期望类结论为按公开奖池的推断，官方未公示概率。
- 请妥善保管你的 MCP Token，不要提交到任何公开仓库（本项目配置文件仅含环境变量占位符）。

## License

MIT
