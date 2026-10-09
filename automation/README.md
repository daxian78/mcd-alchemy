# 每日麦麦情报 · 自动化简报配置指南

每天北京时间 08:00，GitHub Actions 自动调用麦当劳 MCP 生成简报，推送到你选的群机器人。
你是唯一的数据主人：MCP Token 和 webhook 都存在你自己的仓库 Secrets 里，不经过任何第三方服务器。

## 它每天会告诉你什么

- 🌤️ **天气钩子**（可选）：高温推冰饮、雨天推麦乐送（数据来自 Open-Meteo 免费开放 API，无需注册）
- 🎁 **今日/明日活动**：麦当劳 MCP `campaign-calendar` 实时查询
- ⏰ **积分健康**：可用积分 + 过期倒计时警告（`query-my-account`）
- 🎰 **抽奖保底速算**：当日奖池下的"最差结果"推断（`query-lottery-info`）

## 配置步骤（约 5 分钟）

### 第 1 步：Fork 或使用本仓库

Fork 后在你自己的仓库操作（也可以直接在本地 clone 运行，见文末）。

### 第 2 步：配置 Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret，按需添加：

| Secret | 必填 | 说明 |
|---|---|---|
| `MCD_MCP_TOKEN` | ✅ | [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请的 MCP Token |
| `WECOM_WEBHOOK` | 任选 | 企业微信群机器人地址：群设置 → 群机器人 → 添加机器人 → 复制 webhook |
| `DINGTALK_WEBHOOK` + `DINGTALK_SECRET` | 任选 | 钉钉群机器人（安全设置建议选"加签"） |
| `FEISHU_WEBHOOK` | 任选 | 飞书群机器人 webhook |
| `TG_BOT_TOKEN` + `TG_CHAT_ID` | 任选 | Telegram Bot（Actions 服务器在海外，无需代理） |

配几个发几个，一个都不配则运行时打印到日志。

### 第 3 步：配置天气位置（可选）

Settings → Secrets and variables → Actions → **Variables** 页签 → New repository variable：

| Variable | 示例 |
|---|---|
| `WEATHER_LAT` | `31.2304`（纬度） |
| `WEATHER_LON` | `121.4737`（经度） |

### 第 4 步：试跑一次

仓库 → Actions → daily-brief → Run workflow。绿了就是通了，去群里看消息。

之后每天北京时间 08:00 自动运行（GitHub Actions 的 cron 有约 5-15 分钟的正常浮动）。

## 本地运行（不想用 Actions 也行）

```bash
cd automation
cp .env.example .env   # 填入你的 Token / webhook
npm install
node --env-file=.env daily-brief.mjs
```

配合 crontab / launchd 定时即可。**`.env` 已被 .gitignore 忽略，永远不会被提交。**

## 隐私与安全说明

- 你的 MCP Token 只存在 GitHub Secrets（加密）或本地 `.env`（未提交）中
- 简报中的积分数据来自你自己的账户，推送到你自己配置的群
- 本项目代码不含任何硬编码凭证（参赛声明中"信息安全声明"条款的落实）
