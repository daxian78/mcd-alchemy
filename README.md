# 麦门炼金术 · McD Alchemy

> 把每一块钱和每一分积分都花在刀刃上：进门之前算一笔，出门之后算一笔。
> 基于麦当劳官方 MCP（mcd-order）的麦当劳消费决策副驾驶 —— 点餐 · 积分 · 优惠券，全链路算账。

![麦门炼金术](docs/assets/banner.png)

**对话即分析 · 每日简报主动找你 · 在线 demo 可玩** —— 一个开源的麦当劳个人消费 Copilot。

## 两个反直觉的发现

**发现一：积分抽奖，最差也是赚的？**

> 截至 2026-10-09 的公开奖池：积分抽奖 **24 积分/次**，奖池中价值最低的奖品是 **30 积分**——
> 也就是说，**抽一次最差净赚 6 积分**，其余 9 项奖品全是真实优惠券（立减券、5 折券）。
> （按当前公开奖池推断，官方未公示概率，实际以活动页为准。）

**发现二：用积分换巨无霸套餐，账面竟然不省？**

> 同一顿巨无霸午餐（2026-10-09 上海某门店实测菜单）：
>
> | 买单方式 | 你付出的 | 折算成本 | 结论 |
> |---|---|---|---|
> | 单点（堡 25.5 + 薯条 13.5 + 可乐 9.5） | 48.5 元 | 48.5 元 | 最贵，不用动脑 |
> | 官方三件套 | 36.5 元 | 36.5 元 | 省 12 元，无脑选 |
> | 800 积分换「21.9 元巨无霸可乐组合」券 | 800 分 + 21.9 元 | ≈ 43.8 元* | 账面不省，只是积分的"保本出口" |
>
> \* 折算口径：按积分标尺 0.0274 元/分（21.9 元 ÷ 800 分），800 分 ≈ 21.9 元等值。
> 积分真正的最优出口是小额定向券：50 分换 6.9 元派券，价值率 0.138 元/分，是巨无霸组合的 **5 倍**。

这些结论都能用 MCP 实时数据复现——本项目把"算账"过程工具化了。

## 它能做什么（五大模块）

| 模块 | 解决什么问题 | 背后的 MCP 工具 |
|---|---|---|
| 🍔 点餐算账器 | 单点 / 套餐 / 随心配 / 积分券，四种买单同口径比价 | `query-nearby-stores` + `query-meals` + `calculate-price` |
| ⏰ 过期积分预警 | 每月 silently 清零的积分，到期前给你"最优消耗路径" | `query-my-account` + `mall-points-products` |
| 🎰 抽奖保底分析器 | 抽奖前先算：保底值多少、期望区间多少、值不值得抽 | `query-lottery-info`（+确认后 `draw-lottery`） |
| 📊 积分性价比榜 | 商城商品统一折算"元/分"标尺，跨类目排出真值榜 | `mall-points-products` |
| 📅 活动领券联动 | 今日/明日活动 + 可领券一键收好 | `campaign-calendar` + `available-coupons` |

## 三种打开方式

| 端 | 形态 | 适合谁 |
|---|---|---|
| 💬 **对话端** | 在 WorkBuddy / Cursor 等 MCP Client 装载 Skill，随问随算 | 想交互式分析的人 |
| ⏰ **自动简报端** | GitHub Actions 每日 08:00 自动跑 Skill 逻辑，「今日麦麦情报」（活动+积分过期倒计时+抽奖保底速算+天气钩子）推送到**企微/钉钉/飞书/Telegram 群机器人** | 想每天被动接收、零操作的人 |
| 🌐 **在线演示端** | GitHub Pages 交互 demo（含可玩的抽奖模拟器），无需 Token 无需登录 | 围观者（链接发布后更新） |

自动化端是本项目的灵魂：**从"你问它才答"升级为"它每天主动找你"**。你的 Token 存在你自己仓库的 Secrets 里，不经过任何第三方服务器。配置指南见 [`automation/README.md`](./automation/README.md)，5 分钟配完。

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

把 [`skills/mcd-alchemy/SKILL.md`](./skills/mcd-alchemy/SKILL.md) 放入你的 Skill 目录（WorkBuddy：`.workbuddy/skills/` 或用户级 `~/.workbuddy/skills/`）。

**第 4 步：开聊**

```
这顿巨无霸怎么买最划算？
我的麦当劳积分快过期了吗？怎么花最值？
现在抽奖划算吗？帮我算算保底。
给我出今天的麦麦情报简报。
```

## WorkBuddy 用户？三步零代码复刻

本项目在 **WorkBuddy**（腾讯，本次大赛官方合作伙伴）中开发与验证。用 WorkBuddy 的话，
**不需要 GitHub Actions、不需要配任何 Secrets**：连接器 + Skill + 内置自动化三步搞定，
每天 08:00 的「今日麦麦情报」直接出现在会话里。完整步骤见 [`workbuddy-setup.md`](./workbuddy-setup.md)。

## 设计原则

1. **消耗型操作三重确认**——抽奖/兑换/下单前，先展示"花多少、换什么"，你点头才执行。
2. **统一价值标尺**——现金、积分、券全部折算到"元/分"口径再比较，杜绝积分错觉。
3. **证据标注**——实时数据标注时间戳；推算结论标注前提与局限；算不了就直说。
4. **不诱导消费**——该说"攒着别花"的时候直说，积分不是花得越多越聪明。

## 目标用户

- 每一个觉得麦当劳"价格玄学"的普通消费者
- 会员积分躺在账户里等过期的大多数人
- 喜欢用 MCP / Agent 折腾个人自动化工具链的开发者
- 羊毛党：想把每一分积分花出最大价值的人

## 文件结构

```
mcd-alchemy/
├── README.md                        # 本文件
├── CONTEST_DECLARATION.md           # 参赛声明（官方模板，未改动）
├── MCP_INTEGRATION.md               # MCP 工具集成与调用流程
├── mcp-config.example.json          # 脱敏 MCP 配置（环境变量占位符）
├── skills/mcd-alchemy/SKILL.md      # Skill 主体（五大模块分析框架）
├── workbuddy-setup.md               # WorkBuddy 用户零代码复刻指南
├── demo/index.html                  # 交互演示页（GitHub Pages 托管）
├── automation/                      # 每日简报自动化（Actions + 多平台 webhook）
│   ├── daily-brief.mjs              # 主脚本：MCP 数据采集 + Open-Meteo 天气 + 四通道推送
│   ├── README.md                    # 配置指南（Secrets / webhook 教程）
│   └── .env.example                 # 本地调试环境变量模板
├── docs/
│   ├── assets/banner.png            # 项目 banner
│   └── data-snapshots/              # 接口数据快照（可复现）
└── .github/workflows/
    ├── daily-brief.yml              # 定时任务：北京时间每日 08:00
    └── pages.yml                    # demo 页自动部署 GitHub Pages
```

## 注意事项

- 本项目为参赛作品，由个人独立开发，**非麦当劳官方产品**；餐品、积分、活动信息以麦当劳官方渠道实时结果为准。
- 麦当劳 MCP 限流 600 次/分钟/Token，批量查询请稍作间隔。
- 抽奖期望、积分标尺折算等结论为按公开数据的推断，官方未公示概率与标尺口径。
- 请妥善保管你的 MCP Token，不要提交到任何公开仓库（本项目配置文件仅含环境变量占位符）。

## License

MIT
