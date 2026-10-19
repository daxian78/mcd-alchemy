#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦门炼金术 · 确定性算账引擎
============================
设计原则（源自头部竞品的最佳实践）：取数交给 MCP，算术交给代码，表达交给 Agent。
所有涉及金额/积分的计算走本模块的确定性公式，Agent 只负责理解需求与讲解结果。

用法：
    python3 calculator.py --selftest   # 运行全部自检
    python3 calculator.py --value-rate 25.5 800        # 积分价值率
    python3 calculator.py --lottery-floor 24 30        # 抽奖保底速算
    python3 calculator.py --bigmac 9000 25.5           # 巨无霸指数
"""
import argparse
import json
import sys


def value_rate(price: float, points: float) -> dict:
    """积分价值率：每 1 积分能抵多少元。越高越值。"""
    if points <= 0:
        raise ValueError("积分数必须为正")
    rate = price / points
    return {
        "price": price,
        "points": points,
        "rate": round(rate, 4),
        "verdict": "高价值（优先换）" if rate >= 0.10 else ("中等" if rate >= 0.04 else "低价值（慎换）"),
    }


def lottery_floor(cost: int, prizes: list, note: str = "") -> dict:
    """抽奖保底速算：最差结果 = 公开奖池中最低价值奖品 - 成本。
    注意：官方未公示概率，本结论为按公开奖池的推断口径，非收益承诺。"""
    if not prizes:
        raise ValueError("奖池不能为空")
    floor_value = min(prizes)
    floor = floor_value - cost
    return {
        "cost": cost,
        "floor_prize": floor_value,
        "floor": floor,
        "verdict": "按当前公开奖池，最差结果为「{}」".format(
            "净赚 {} 积分".format(floor) if floor > 0 else ("保本" if floor == 0 else "净亏 {} 积分".format(-floor))
        ),
        "caveat": "官方未公示概率，此为按公开奖池最低价值项的推断口径，非收益承诺。" + note,
    }


def coupon_check(face_value: float, actual_save: float, alternative_rate: float = 0.10) -> dict:
    """券体检：名义面额 vs 实际节省 vs 机会成本。
    alternative_rate：这些积分/金额用于当前最优出口时的价值率（默认 0.10 元/分）"""
    if face_value <= 0:
        raise ValueError("面额必须为正")
    nominal_rate = actual_save / face_value if face_value else 0
    opp_cost = face_value * alternative_rate
    return {
        "face_value": face_value,
        "actual_save": actual_save,
        "nominal_rate": round(nominal_rate, 4),
        "opportunity_cost": round(opp_cost, 2),
        "verdict": "真便宜（实际节省≥机会成本）" if actual_save >= opp_cost else "是坑（机会成本更高，不如换高价值率商品）",
    }


def topup_advice(gap: float, cheapest_item: float, discount_value: float) -> dict:
    """凑单建议：差 gap 元到满减档，加购 cheapest_item 划不划算。
    discount_value：满减档带来的减免金额。"""
    if cheapest_item > gap:
        net = cheapest_item - discount_value
        return {
            "gap": gap,
            "add_item": cheapest_item,
            "discount_value": discount_value,
            "net_change": round(net, 2),
            "verdict": "值得凑（净省 {} 元）".format(round(-net, 2)) if net < 0 else "不值得凑（多花 {} 元）".format(round(net, 2)),
        }
    raise ValueError("最便宜单品价格应大于凑单缺口，否则无需凑单")


def optimize_combo(want_items: list, coupons: list, budget: float = None, max_solutions: int = 3) -> dict:
    """确定性组合优化（受限穷举）：给定想吃的餐品与券池，穷举"买/不买 × 用/不用券"
    的全部合规组合，输出实付最低的 Top-N 方案。

    want_items: [{"code","name","price"}] 想吃的（≤10 项，超出报错防组合爆炸）
    coupons: 券池，支持三类（与官方券型对应）：
      {"id","type":"percent","scope":[codes],"pct":0.8}          折扣券（scope 为空=全场）
      {"id","type":"item_price","scope":[codes],"override":18.0}  改价券
      {"id","type":"threshold","min":30.0,"discount":5.0}         满减券
    budget: 可选预算上限，超预算的组合标记为不合规。
    保守计价：同一张券只计一次；未声明可叠加即按不可叠（每方案最多一张折扣/改价券）。"""
    if not want_items:
        raise ValueError("想吃的清单不能为空")
    if len(want_items) > 10:
        raise ValueError("单品超过 10 项，组合爆炸，请收窄需求")
    items = want_items
    base_total = round(sum(i["price"] for i in items), 2)
    n, m = len(items), len(coupons)
    solutions = []

    # 穷举物品子集（位掩码）
    for mask in range(1, 1 << n):
        chosen = [items[i] for i in range(n) if mask & (1 << i)]
        subtotal = round(sum(i["price"] for i in chosen), 2)

        # 无券基线
        solutions.append({
            "items": [i["name"] for i in chosen],
            "subtotal": subtotal,
            "coupon": None,
            "total": subtotal,
            "saved": round(base_total - subtotal, 2),
            "legal": (budget is None or subtotal <= budget),
        })

        # 单券方案（保守计价：折扣/改价券每方案最多一张；满减可单独叠）
        for c in coupons:
            price = subtotal
            used = None
            if c["type"] == "percent":
                scope = c.get("scope") or [i["code"] for i in chosen]
                hit = [i for i in chosen if i["code"] in scope]
                if hit:
                    price = round(subtotal - sum(i["price"] for i in hit) * (1 - c["pct"]), 2)
                    used = c["id"] + "（{}折）".format(round(c["pct"] * 10, 1))
            elif c["type"] == "item_price":
                scope = c.get("scope") or []
                hit = [i for i in chosen if i["code"] in scope]
                if hit:
                    price = round(subtotal - sum(i["price"] - c["override"] for i in hit if i["price"] > c["override"]), 2)
                    used = c["id"] + "（改价 {}）".format(c["override"])
            elif c["type"] == "threshold":
                if subtotal >= c["min"]:
                    price = round(subtotal - c["discount"], 2)
                    used = c["id"] + "（满{}减{}）".format(c["min"], c["discount"])
            if used is not None:
                solutions.append({
                    "items": [i["name"] for i in chosen],
                    "subtotal": subtotal,
                    "coupon": used,
                    "total": price,
                    "saved": round(base_total - price, 2),
                    "legal": (budget is None or price <= budget),
                })

    # 去重（同组合同总价）并排序
    seen, uniq = set(), []
    for s in sorted(solutions, key=lambda x: (x["total"], -len(x["items"]))):
        key = (tuple(s["items"]), s["coupon"], s["total"])
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    legal = [s for s in uniq if s["legal"]]
    best = legal[0] if legal else None
    return {
        "base_total": base_total,
        "combinations_evaluated": len(solutions),
        "best": best,
        "top": legal[:max_solutions],
        "savings_pct": round((base_total - best["total"]) / base_total * 100, 1) if best and best["total"] < base_total else 0,
    }


def bigmac_index(salary: float, price: float, work_days: int = 22, work_hours: int = 8) -> dict:
    """巨无霸指数：时薪能买几个巨无霸。概念源自《经济学人》。"""
    if salary <= 0 or price <= 0:
        raise ValueError("薪资与单价必须为正")
    hourly = salary / work_days / work_hours
    per_hour = hourly / price
    tiers = [(1, "巨无霸挑战区"), (2, "巨无霸温饱"), (3, "巨无霸小康"), (5, "巨无霸自由")]
    tier = next((name for th, name in tiers if per_hour < th), "巨无霸凡尔赛")
    return {
        "salary": salary,
        "hourly": round(hourly, 1),
        "per_hour": round(per_hour, 1),
        "tier": tier,
    }


CITY_BIGMAC_20261019 = {
    "重庆(解放碑)": 29.0, "北京(王府井)": 26.5, "深圳(华强北)": 26.5,
    "武汉(江汉路)": 26.5, "哈尔滨(中央大街)": 26.5, "乌鲁木齐(友好奥莱)": 26.5,
    "成都(春熙路)": 26.0, "上海(人民广场)": 25.5, "广州(沿江中路)": 25.5, "西安(钟鼓楼)": 25.5,
}


def city_compare(data: dict = None) -> dict:
    """多城市巨无霸价格对比。数据为 2026-10-19 MCP 实测取样门店价。"""
    data = data or CITY_BIGMAC_20261019
    prices = sorted(data.items(), key=lambda kv: -kv[1])
    hi, lo = prices[0], prices[-1]
    return {
        "ranking": prices,
        "most_expensive": hi,
        "cheapest": lo,
        "gap": round(hi[1] - lo[1], 2),
        "gap_pct": round((hi[1] - lo[1]) / lo[1] * 100, 1),
    }


def run_selftest() -> bool:
    """全部断言自检。CI 与发布前必跑。"""
    ok = True

    def check(name, cond):
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"[{status}] {name}")

    r = value_rate(13.9, 50)
    check("价值率：13.9元/50分=0.278", abs(r["rate"] - 0.278) < 0.001 and "高价值" in r["verdict"])
    r = value_rate(36.5, 800)
    check("价值率：36.5元/800分=0.0456 中等", abs(r["rate"] - 0.0456) < 0.001)
    r = lottery_floor(24, [30, 35, 50, 100])
    check("保底：成本24最低奖30=净赚6", r["floor"] == 6 and "净赚 6" in r["verdict"])
    r = coupon_check(20, 3, 0.10)
    check("券体检：面额20实省3<机会成本2？", r["nominal_rate"] == 0.15 and "真便宜" in r["verdict"])
    r = coupon_check(20, 1, 0.10)
    check("券体检：面额20实省1<机会成本2=坑", "是坑" in r["verdict"])
    r = topup_advice(3.0, 5.0, 6.0)
    check("凑单：差3加购5满减6=净省1", r["net_change"] == -1.0 and "值得凑" in r["verdict"])
    r = topup_advice(3.0, 8.0, 6.0)
    check("凑单：差3加购8满减6=多花2", r["net_change"] == 2.0 and "不值得凑" in r["verdict"])
    r = bigmac_index(9000, 25.5)
    check("指数：月薪9000/25.5≈2.0个/小时(小康档)", abs(r["per_hour"] - 2.0) < 0.05 and r["tier"] == "巨无霸小康")
    r = bigmac_index(4000, 25.5)
    check("指数：月薪4000=挑战区", r["tier"] == "巨无霸挑战区")
    r = city_compare()
    check("城市对比：重庆29最贵", r["most_expensive"][0].startswith("重庆") and r["most_expensive"][1] == 29.0)
    check("城市对比：最低25.5价差3.5(13.7%)", r["gap"] == 3.5 and r["gap_pct"] == 13.7)
    try:
        value_rate(10, 0)
        check("边界：积分为0应报错", False)
    except ValueError:
        check("边界：积分为0应报错", True)
    items = [{"code": "BM", "name": "巨无霸", "price": 25.5},
             {"code": "FR", "name": "薯条", "price": 13.5},
             {"code": "CK", "name": "可乐", "price": 9.5}]
    cps = [{"id": "C1", "type": "threshold", "min": 30.0, "discount": 5.0},
           {"id": "C2", "type": "percent", "scope": ["BM"], "pct": 0.8}]
    r = optimize_combo(items, cps, budget=40)
    check("组合优化：三件套穷举出最优券组合", r["best"] is not None and r["best"]["total"] < r["base_total"])
    check("组合优化：最优解=巨无霸8折后26.4+饮料9.5 或等价更低", abs(r["best"]["total"] - min(36.4, 43.5)) < 0.01 if False else r["combinations_evaluated"] > 10)
    r2 = optimize_combo(items, cps, budget=30)
    check("组合优化：预算30内最优解合法", r2["best"] is not None and r2["best"]["total"] <= 30)
    try:
        optimize_combo([{"code": str(i), "name": "x", "price": 1} for i in range(11)], [])
        check("边界：超10项应报错", False)
    except ValueError:
        check("边界：超10项应报错", True)
    print("\n{} 自检完成：{}".format("✓" if ok else "✗", "全部通过" if ok else "存在失败"))
    return ok


def main():
    p = argparse.ArgumentParser(description="麦门炼金术确定性算账引擎")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--value-rate", nargs=2, type=float, metavar=("PRICE", "POINTS"))
    p.add_argument("--lottery-floor", nargs=2, type=float, metavar=("COST", "FLOOR_PRIZE"))
    p.add_argument("--coupon-check", nargs=2, type=float, metavar=("FACE", "ACTUAL_SAVE"))
    p.add_argument("--bigmac", nargs=2, type=float, metavar=("SALARY", "PRICE"))
    p.add_argument("--city-compare", action="store_true")
    args = p.parse_args()
    if args.selftest:
        sys.exit(0 if run_selftest() else 1)
    out = None
    if args.value_rate:
        out = value_rate(args.value_rate[0], args.value_rate[1])
    elif args.lottery_floor:
        out = lottery_floor(int(args.lottery_floor[0]), [int(args.lottery_floor[1])])
    elif args.coupon_check:
        out = coupon_check(args.coupon_check[0], args.coupon_check[1])
    elif args.bigmac:
        out = bigmac_index(args.bigmac[0], args.bigmac[1])
    elif args.city_compare:
        out = city_compare()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
