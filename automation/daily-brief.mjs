#!/usr/bin/env node
/**
 * 麦门炼金术 · 每日麦麦情报简报
 *
 * 数据源：
 *  - 麦当劳 MCP（mcd-order）：活动日历 / 积分账户 / 抽奖状态 —— 官方实时数据
 *  - Open-Meteo（https://open-meteo.com，免费开放、无需 key）：天气增强，非麦当劳能力
 *
 * 推送：企微 / 钉钉 / 飞书 / Telegram 群机器人，按环境变量自动启用，可多选。
 * 本地运行：cp .env.example .env，填好后 `node --env-file=.env daily-brief.mjs`
 */
import crypto from "node:crypto";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const MCP_URL = process.env.MCD_MCP_URL || "https://mcp.mcd.cn";
const TOKEN = process.env.MCD_MCP_TOKEN;

/* ---------------- 工具函数 ---------------- */

const beijingDate = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai" }).format(new Date()); // yyyy-MM-dd
const beijingWeekday = () =>
  new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", weekday: "long" }).format(new Date());
const md = (s) => String(s ?? "").replace(/\n{3,}/g, "\n\n");

async function withMCP(fn) {
  if (!TOKEN) throw new Error("缺少 MCD_MCP_TOKEN 环境变量");
  const client = new Client({ name: "mcd-alchemy", version: "1.0.0" });
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL), {
    requestInit: { headers: { Authorization: `Bearer ${TOKEN}` } },
  });
  await client.connect(transport);
  try {
    return await fn(client);
  } finally {
    await client.close().catch(() => {});
  }
}

/** 调用 MCP 工具并尽量解析 JSON 结果；失败不抛出，返回 { error } */
async function callTool(client, name, args = {}) {
  try {
    const res = await client.callTool({ name, arguments: args });
    const text = (res.content || []).map((c) => c.text || "").join("\n");
    const start = text.indexOf("{");
    if (start >= 0) {
      try {
        return JSON.parse(text.slice(start));
      } catch {
        /* 非 JSON，走 raw */
      }
    }
    return { raw: text };
  } catch (e) {
    return { error: String(e?.message || e) };
  }
}

/* ---------------- 数据采集 ---------------- */

async function getPoints(client) {
  const j = await callTool(client, "query-my-account");
  const d = j?.data;
  if (!d) return null;
  return {
    available: Number(d.availablePoint || 0),
    expireThisMonth: Number(d.currentMouthExpirePoint || 0),
    expireNextMonth: Number(d.nextMouthExpirePoint || 0),
  };
}

async function getLottery(client) {
  const j = await callTool(client, "query-lottery-info");
  const d = j?.data;
  if (!d || !d.activityName) return null;
  // 保底推断：找积分类奖品，取名称中的最小分值
  const pointPrizes = (d.prizes || [])
    .map((p) => p.name)
    .map((n) => ({ name: n, pt: (n.match(/(\d+)\s*积分/) || [])[1] }))
    .filter((x) => x.pt)
    .map((x) => ({ ...x, pt: Number(x.pt) }));
  const floor = pointPrizes.length ? Math.min(...pointPrizes.map((x) => x.pt)) : null;
  const drawPoint = Number(d.drawPoint || 0);
  return {
    name: d.activityName,
    status: d.activityStatusText,
    drawPoint,
    prizeCount: (d.prizes || []).length,
    floor,
    floorNet: floor != null ? floor - drawPoint : null,
  };
}

/** 从 campaign-calendar 的 markdown 返回中抽取今日/明日活动标题 */
function parseCalendar(raw) {
  const out = { today: [], tomorrow: [] };
  try {
    const sections = String(raw).split(/####\s*/).slice(1);
    for (const sec of sections) {
      const titles = [...sec.matchAll(/\*\*活动标题\*\*：(.+)/g)].map((m) =>
        m[1].replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu, "").trim()
      );
      if (/今日/.test(sec.split("\n")[0])) out.today.push(...titles);
      if (/明日/.test(sec.split("\n")[0])) out.tomorrow.push(...titles);
    }
  } catch {
    /* 解析失败走兜底文案 */
  }
  out.today = out.today.slice(0, 4);
  out.tomorrow = out.tomorrow.slice(0, 3);
  return out;
}

async function getWeather() {
  const lat = process.env.WEATHER_LAT;
  const lon = process.env.WEATHER_LON;
  if (!lat || !lon) return null;
  try {
    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
      `&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia%2FShanghai&forecast_days=1`;
    const j = await (await fetch(url)).json();
    const d = j.daily;
    return {
      tmax: Math.round(d.temperature_2m_max[0]),
      tmin: Math.round(d.temperature_2m_min[0]),
      rain: Number(d.precipitation_sum[0] || 0),
    };
  } catch {
    return null;
  }
}

function weatherHook(w) {
  if (!w) return null;
  if (w.rain >= 1) return `今日降水 ${w.rain}mm —— 雨天排队劝退，麦乐送场景`;
  if (w.tmax >= 32) return `今日最高 ${w.tmax}°C —— 高温，雪冰/冰饮是主角`;
  if (w.tmax <= 5) return `今日最低 ${w.tmin}°C —— 冷天，热食 + 热咖啡优先`;
  return `今日 ${w.tmin}~${w.tmax}°C，降水 ${w.rain}mm —— 适合到店`;
}

/* ---------------- 简报排版 ---------------- */

function buildBrief({ points, lottery, calendar, weatherLine, dateStr }) {
  const L = [];
  L.push(`## 🍟 麦门炼金术 · 今日情报`);
  L.push(`> ${dateStr} ${beijingWeekday()} · 数据来自麦当劳 MCP 实时查询`);
  if (weatherLine) L.push(`**🌤️ 天气**：${weatherLine}`);

  if (calendar) {
    const t = calendar.today.length ? calendar.today.map((x) => `- ${x}`).join("\n") : "- 今日无特别活动";
    L.push(`**🎁 今日活动**\n${t}`);
    if (calendar.tomorrow.length) L.push(`**📅 明日预告**\n${calendar.tomorrow.map((x) => `- ${x}`).join("\n")}`);
  }

  if (points) {
    let line = `**⏰ 积分**：可用 ${points.available} 分`;
    if (points.expireThisMonth > 0)
      line += `，⚠️ **${points.expireThisMonth} 分本月过期**（最优出口：小额定向券，价值率约为大额组合的 5 倍）`;
    else line += `，本月无过期，安心`;
    L.push(line);
  }

  if (lottery) {
    let line = `**🎰 抽奖**：${lottery.name}（${lottery.status}），${lottery.drawPoint} 积分/次，奖池 ${lottery.prizeCount} 项`;
    if (lottery.floorNet != null)
      line += `\n> 保底速算：最低奖品 ${lottery.floor} 积分 vs 成本 ${lottery.drawPoint} 积分 → 按公开奖池最差 ${
        lottery.floorNet >= 0 ? "+" : ""
      }${lottery.floorNet} 分（概率未公示，推断口径）`;
    L.push(line);
  }

  L.push(`---\n*i am lovin' it · mcd-alchemy 自动简报（非官方）*`);
  return md(L.join("\n\n"));
}

/* ---------------- 多通道推送 ---------------- */

async function postJSON(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${(await r.text()).slice(0, 200)}`);
}

function dingtalkSigned(base, secret) {
  if (!secret) return base;
  const ts = Date.now();
  const sign = encodeURIComponent(
    crypto.createHmac("sha256", secret).update(`${ts}\n${secret}`).digest("base64")
  );
  return `${base}&timestamp=${ts}&sign=${sign}`;
}

async function dispatch(brief) {
  const jobs = [];
  if (process.env.WECOM_WEBHOOK)
    jobs.push(["wecom", postJSON(process.env.WECOM_WEBHOOK, { msgtype: "markdown", markdown: { content: brief } })]);
  if (process.env.DINGTALK_WEBHOOK)
    jobs.push([
      "dingtalk",
      postJSON(dingtalkSigned(process.env.DINGTALK_WEBHOOK, process.env.DINGTALK_SECRET), {
        msgtype: "markdown",
        markdown: { title: "麦门炼金术 · 今日情报", text: brief },
      }),
    ]);
  if (process.env.FEISHU_WEBHOOK)
    jobs.push(["feishu", postJSON(process.env.FEISHU_WEBHOOK, { msg_type: "text", content: { text: brief } })]);
  if (process.env.TG_BOT_TOKEN && process.env.TG_CHAT_ID)
    jobs.push([
      "telegram",
      postJSON(`https://api.telegram.org/bot${process.env.TG_BOT_TOKEN}/sendMessage`, {
        chat_id: process.env.TG_CHAT_ID,
        text: brief,
        disable_web_page_preview: true,
      }),
    ]);

  if (!jobs.length) {
    console.log("未配置任何推送通道，以下为简报内容：\n");
    console.log(brief);
    console.log("\n提示：配置 WECOM_WEBHOOK / DINGTALK_WEBHOOK / FEISHU_WEBHOOK / TG_BOT_TOKEN+TG_CHAT_ID 即可自动推送，见 .env.example");
    return;
  }
  const results = await Promise.allSettled(jobs.map(([, p]) => p));
  results.forEach(([name], i) => {
    const r = results[i];
    console.log(`[${name}] ${r.status === "fulfilled" ? "推送成功" : `推送失败：${r.reason}`}`);
  });
}

/* ---------------- 主流程 ---------------- */

const dateStr = beijingDate();
const data = await withMCP(async (client) => {
  const [calendarRaw, points, lottery] = await Promise.all([
    callTool(client, "campaign-calendar", { specifiedDate: dateStr }),
    getPoints(client),
    getLottery(client),
  ]);
  return { points, lottery, calendar: calendarRaw.raw ? parseCalendar(calendarRaw.raw) : null };
});

const weather = await getWeather();
const brief = buildBrief({
  dateStr,
  points: data.points,
  lottery: data.lottery,
  calendar: data.calendar,
  weatherLine: weatherHook(weather),
});

await dispatch(brief);
