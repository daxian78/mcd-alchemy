# WorkBuddy 用户一键复刻指南

> 本项目在 WorkBuddy（腾讯）中开发与验证。WorkBuddy 是麦当劳程序员创意开发大赛的官方合作伙伴。
> 用 WorkBuddy 的话，**不需要 GitHub Actions、不需要配任何 Secrets**——连接器 + Skill + 内置自动化三步搞定全套能力。

## 第 1 步：接入麦当劳 MCP 连接器

左侧边栏【专家·技能·连接器】→【连接器】→ 右上角【自定义连接器】→【配置 MCP】，粘贴以下 JSON
（先去 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请 Token，替换 `你的MCP_TOKEN`）：

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

保存后回到【自定义连接器】，将 `mcd-order`【启用】。

## 第 2 步：安装 Skill

把 [`skills/mcd-alchemy/SKILL.md`](./skills/mcd-alchemy/SKILL.md) 放入：

- 用户级（推荐，全项目可用）：`~/.workbuddy/skills/mcd-alchemy/SKILL.md`
- 或项目级：`{你的工作区}/.workbuddy/skills/mcd-alchemy/SKILL.md`

## 第 3 步：创建「每日麦麦情报」自动化（灵魂功能）

WorkBuddy 对话框输入自然语言即可创建，例如：

> 每天早上 8 点，帮我生成一份「麦门炼金术·今日情报」：调用麦当劳 MCP 查询今日和明日活动、
> 我的积分账户（含过期警告）、抽奖状态并做保底速算（最低积分类奖品分值减去单次成本），
> 以简报形式输出，数据标注时间，推断结论标注口径。

或者使用精确配置：

- **类型**：重复执行（recurring）
- **规则**：每天 08:00（`FREQ=DAILY;BYHOUR=8;BYMINUTE=0`）
- **提示词**（可直接粘贴）：

```text
生成「麦门炼金术·今日情报」简报。步骤：
1. 调用连接器 mcd-order 的 campaign-calendar（specifiedDate=今天），提取今日与明日活动标题（各最多4条）；
2. 调用 query-my-account，输出可用积分；若"本月将过期积分">0，加 ⚠️ 过期警告并提示"小额定向券是积分最优出口"；
3. 调用 query-lottery-info，输出单次抽奖成本与奖池数量，并做保底速算：找出名称含"积分"的最低奖品分值，减去单次成本，标注"按公开奖池推断，官方未公示概率"；
4. 以 🍟 麦门炼金术·今日情报 为标题输出，数据标注日期，结尾注明"非官方，仅供参考"。
```

## 第 4 步：开聊（对话端能力）

```
这顿巨无霸怎么买最划算？单点还是套餐？
我的积分快过期了吗？怎么花最值？
现在抽奖划算吗？帮我算算保底。
```

## 与 GitHub Actions 路径的对比

| | WorkBuddy 路径 | GitHub Actions 路径（`automation/`） |
|---|---|---|
| 配置成本 | 对话里说一句话 | 配置 Secrets + Fork 仓库 |
| 运行环境 | WorkBuddy 云端 | GitHub 免费额度 |
| 推送目标 | WorkBuddy 会话内（可搭配企业微信连接器推群） | 企微/钉钉/飞书/TG 群机器人 |
| 适合谁 | WorkBuddy 用户（推荐） | 开发者 / 非 WorkBuddy 用户 |

两条路径完全等价，核心逻辑同源（见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)）。

## 安全提醒

- MCP Token 只保存在你自己的 WorkBuddy 连接器配置中，不要粘贴给他人、不要提交到公开仓库
- 自动化中的查询均为只读操作；任何消耗积分/下单的操作，Skill 内置护栏会要求你二次确认
