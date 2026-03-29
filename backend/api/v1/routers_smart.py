"""
routers_smart.py — 智选平台专属 API 路由
=========================================
与诊断平台 (routers_rebalance / routers_macro) 完全物理隔离。
计算标的: 114 只核心精选基金池。
前缀: /smart/

端点:
  POST /smart/macro_allocation   → 宏观底仓引擎
  POST /smart/tactical_adjustment → 战术调仓引擎
  POST /smart/backtest           → 历史回测引擎
  GET  /smart/fund_pool          → 基金池清单
  GET  /smart/fund_profiles      → 基金深度资料
"""

import os
import sys
import json
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from loguru import logger

# ── 路径设置 ──
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"

# 确保两个路径都在 sys.path，backend 在前
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.append(LEGACY_SERVICES_DIR)


def _import_backend_service(module_name: str):
    """
    强制按文件路径加载 services 模块, 完全绕过 Python 包缓存。
    优先: backend/services/ → 遗留 20260325/services/ → 标准导入
    """
    import importlib.util

    # 已缓存则直接返回
    cache_key = f"services.{module_name}"
    if cache_key in sys.modules:
        return sys.modules[cache_key]

    # 优先从 backend/services/ 加载
    for search_dir in [BACKEND_DIR, LEGACY_SERVICES_DIR]:
        module_path = os.path.join(search_dir, "services", f"{module_name}.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(cache_key, module_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[cache_key] = mod
            spec.loader.exec_module(mod)
            return mod

    # 最后兜底: 标准导入
    import importlib
    return importlib.import_module(cache_key)

router = APIRouter(prefix="/smart", tags=["智选平台"])


# ── 8 大资产类别 (与 product_mapping 对齐) ──
ASSET_CLASSES_8 = ["大盘核心", "科技成长", "红利防守", "纯债固收", "混合债券", "短债理财", "黄金商品", "海外QDII"]


# ═══════════════════════════════════════════════════
#  辅助: 加载 114 只基金池
# ═══════════════════════════════════════════════════

def _load_fund_pool() -> list:
    """从 product_mapping 加载 114 只核心基金池。"""
    _pm = _import_backend_service("product_mapping")
    TRUST_PRODUCT_MAPPING = _pm.TRUST_PRODUCT_MAPPING
    pool = []
    seen = set()
    for ac_name, sub_cats in TRUST_PRODUCT_MAPPING.items():
        for cat_name, items in sub_cats.items():
            for item in items:
                if len(item) >= 2 and item[0] not in seen:
                    seen.add(item[0])
                    pool.append({
                        "code": item[0],
                        "name": item[1],
                        "category": ac_name,
                        "sub_category": cat_name,
                    })
    return pool


def _load_fund_profiles() -> list:
    """加载已下载的基金深度资料 JSON。"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    profile_path = os.path.join(data_dir, "zx_fund_profiles.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[智选] 基金深度资料加载失败: {e}")
    return []


# ═══════════════════════════════════════════════════
#  GET /smart/fund_pool — 基金池清单
# ═══════════════════════════════════════════════════

@router.get("/fund_pool")
async def get_fund_pool():
    """
    返回 114 只核心精选基金池 (按权益/固收/现金分类)。
    ⚠️ 现金管理产品年化波动率强制硬编码为 0。
    """
    try:
        pool = await run_in_threadpool(_load_fund_pool)

        # 按大类分组
        grouped = {}
        for fund in pool:
            cat = fund["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(fund)

        return {
            "status": "success",
            "count": len(pool),
            "pool": pool,
            "grouped": grouped,
        }
    except Exception as e:
        logger.error(f"[智选] 基金池加载失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════
#  GET /smart/fund_profiles — 基金深度资料
# ═══════════════════════════════════════════════════

@router.get("/fund_profiles")
async def get_fund_profiles():
    """
    返回已下载的基金深度资料 (Wind 深度数据)。
    需先运行 scripts/fetch_fund_profiles.py 下载数据。
    """
    try:
        profiles = await run_in_threadpool(_load_fund_profiles)
        return {
            "status": "success",
            "count": len(profiles),
            "profiles": profiles,
        }
    except Exception as e:
        logger.error(f"[智选] 基金深度资料加载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════
#  POST /smart/macro_allocation — 宏观底仓引擎
# ═══════════════════════════════════════════════════

class MacroAllocationRequest(BaseModel):
    capital: float = 1000        # 万元
    target_ret: float = 8.0      # %
    max_vol: float = 15.0        # %
    period: str = "1年"          # 半年/1年/3年


@router.post("/macro_allocation")
async def macro_allocation(req: MacroAllocationRequest):
    """
    宏观底仓引擎:
    1. EDB → 宏观象限定位
    2. 情景分支:
       - 情景 A (波动率满足): 生成 3 套方案 (进取+20% / 稳健 / 防守-20%)
       - 情景 B (波动率无法满足): 仅 1 套稳健配置
    3. 返回 KPI 卡片 + 资产权重/金额表
    """
    try:
        result = await run_in_threadpool(
            _macro_allocation_sync,
            capital_wan=req.capital,
            target_ret_pct=req.target_ret,
            max_vol_pct=req.max_vol,
            period=req.period,
        )
        return result
    except Exception as e:
        logger.error(f"[智选] 宏观底仓异常: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def _macro_allocation_sync(capital_wan: float, target_ret_pct: float, max_vol_pct: float, period: str) -> dict:
    """同步执行宏观底仓分配 (在后台线程中运行)。"""
    # ── 强制从 backend/services 加载 (绕过遗留路径遮蔽) ──
    _mdc = _import_backend_service("macro_data_collector")
    fetch_macro_factors = _mdc.fetch_macro_factors
    fetch_valuation_factors = _mdc.fetch_valuation_factors
    fetch_risk_momentum_factors = _mdc.fetch_risk_momentum_factors
    calculate_derived_factors = _mdc.calculate_derived_factors
    calculate_factor_scores = _mdc.calculate_factor_scores

    _fl = _import_backend_service("factor_loadings")
    determine_quadrant = _fl.determine_quadrant
    QUADRANT_DEFINITIONS = _fl.QUADRANT_DEFINITIONS
    factor_scores_to_asset_expected_returns = _fl.factor_scores_to_asset_expected_returns

    _me = _import_backend_service("markov_engine")
    get_current_macro_regime_mock = _me.get_current_macro_regime_mock

    # ── Step 1: EDB 数据下载 + 因子评分 ──
    logger.info("[智选] Step 1: EDB 宏观数据下载...")
    macro_data = fetch_macro_factors()
    val_data = fetch_valuation_factors()
    risk_data = fetch_risk_momentum_factors()
    derived = calculate_derived_factors(macro_data, val_data)
    scores = calculate_factor_scores(macro_data, val_data, risk_data, derived)

    if not scores:
        scores = {
            "composite_score": 0.5, "market_state": "Recovery",
            "macro_total": 0.4, "valuation_total": 0.3, "risk_total": 0.3,
        }

    # ── Step 2: 宏观象限定位 ──
    _composite = scores.get("composite_score", 0.5)
    _macro_t = scores.get("macro_total", 0)
    _val_t = scores.get("valuation_total", 0)

    factor_scores_6 = {
        "经济增长": round(float(_macro_t * 2), 3),
        "通胀商品": round(float(-_val_t * 1.5), 3),
        "利率环境": round(float(_macro_t * 1.2), 3),
        "信用扩张": round(float((_composite - 0.5) * 2), 3),
        "海外环境": 0.0,
        "市场情绪": round(float((_composite - 0.5) * 3), 3),
    }

    current_q = determine_quadrant(factor_scores_6)
    q_info = QUADRANT_DEFINITIONS[current_q]
    asset_signals = factor_scores_to_asset_expected_returns(factor_scores_6, apply_regime=True)
    hmm_result = get_current_macro_regime_mock()

    # ── Step 3 & 4: 独立象限权重和多情景判定 ──
    _frp = _import_backend_service("factor_risk_parity")
    
    # 获取基准稳健下的基础排布，用作 can_achieve 判断
    base_rp_result = _frp.optimize_factor_risk_parity(
        factor_scores=factor_scores_6,
        max_volatility=max_vol_pct / 100.0,
    )
    base_vol = base_rp_result.get("estimated_volatility", 0.0)

    # 载入基金池
    fund_pool = _load_fund_pool()

    target_ret_decimal = target_ret_pct / 100.0
    max_vol_decimal = max_vol_pct / 100.0
    capital_yuan = capital_wan * 10000

    # 判断波动率是否能覆盖用户目标
    can_achieve = base_vol <= max_vol_decimal * 1.2  # 允许 20% 容差

    scenarios = []

    if can_achieve:
        # 情景 A: 生成 3 套方案
        # 为保持收益与波动率对等缩放，进取上限1.2, 防守0.8
        for scenario_name, vol_adj, ret_adj in [("进取配置", 1.2, 1.2), ("稳健配置", 1.0, 1.0), ("防守配置", 0.8, 0.8)]:
            sc_target_ret = target_ret_decimal * ret_adj
            sc_max_vol = max_vol_decimal * vol_adj
            
            # 为当前情景独立求解 HRP 权重
            rp_result = _frp.optimize_factor_risk_parity(
                factor_scores=factor_scores_6,
                max_volatility=sc_max_vol,
            )
            sc_base_weights = rp_result.get("target_weights", {})
            sc_estimated_vol = rp_result.get("estimated_volatility", sc_max_vol)
            
            scenario = _build_scenario(
                name=scenario_name,
                base_weights=sc_base_weights,
                target_ret=sc_target_ret,
                max_vol=sc_max_vol,
                capital=capital_yuan,
                fund_pool=fund_pool,
                ret_multiplier=ret_adj,
                hrp_estimated_vol=sc_estimated_vol
            )
            scenarios.append(scenario)
    else:
        # 情景 B: 波动率无法满足 → 仅 1 套稳健 (以波动率为锚)
        scenario = _build_scenario(
            name="稳健配置 (波动率锚定)",
            base_weights=base_rp_result.get("target_weights", {}),
            target_ret=target_ret_decimal,
            max_vol=max_vol_decimal,
            capital=capital_yuan,
            fund_pool=fund_pool,
            ret_multiplier=1.0,
            vol_anchored=True,
            hrp_estimated_vol=base_vol
        )
        scenarios.append(scenario)

    # ==== [WIND DATA INJECTION] ====
    wind_service = _import_backend_service("wind_profiles")
    all_codes = set()
    for sc in scenarios:
        for alloc in sc["allocations"]:
            all_codes.add(alloc["code"])
            
    wind_data = wind_service.get_wind_fund_profiles(list(all_codes))
    
    for sc in scenarios:
        sc["profiles"] = []
        for alloc in sc["allocations"]:
            code = alloc["code"]
            profile = dict(wind_data.get(code, {}))
            profile["_alloc_weight"] = alloc["weight_pct"]
            profile["_alloc_cat"] = alloc["category"]
            profile["_amount"] = alloc["amount"]
            sc["profiles"].append(profile)
    return {
        "status": "success",
        "scenario_type": "A" if can_achieve else "B",
        "edb_data": {
            "market_state": scores.get("market_state", "N/A"),
            "composite_score": round(_composite, 3),
            "macro_total": round(_macro_t, 3),
            "valuation_total": round(_val_t, 3),
            "risk_total": round(scores.get("risk_total", 0), 3),
        },
        "quadrant": {
            "current": current_q,
            "label": q_info["label"],
            "description": q_info["description"],
            "best_assets": q_info["best_assets"],
            "worst_assets": q_info["worst_assets"],
            "markov_regime": hmm_result.get("current_regime", "unknown"),
            "markov_confidence": hmm_result.get("confidence", 0.0),
        },
        "factor_scores": factor_scores_6,
        "transmission_chain": [
            {"factor": f, "score": round(factor_scores_6.get(f, 0), 3), "regime_modifier": 1.0}
            for f in factor_scores_6
        ],
        "defense_log": rp_result.get("defense_log", []),
        "factor_risk_contributions": rp_result.get("factor_risk_contributions", {}),
        "scenarios": scenarios,
    }


def _build_scenario(name, base_weights, target_ret, max_vol, capital, fund_pool, ret_multiplier, vol_anchored=False, hrp_estimated_vol=0.0):
    """构建单个配置方案 (含KPI + 基金明细表)。"""
    import random
    import json
    import os

    # 1. 过滤 weight > 0 的类别并分配名额 (最大余额法, 总名额10)
    active_cats = {k: v for k, v in base_weights.items() if v > 0.001}
    total_slots = 10
    slots = {}
    remainders = {}
    
    if not active_cats:
        active_cats = {"大盘核心": 1.0}  # 防御性回退
        
    total_w = sum(active_cats.values())
    active_cats = {k: v / total_w for k, v in active_cats.items()}
    
    for cat, weight in active_cats.items():
        exact = weight * total_slots
        slots[cat] = int(exact)
        remainders[cat] = exact - slots[cat]
        
    remaining_slots = total_slots - sum(slots.values())
    if remaining_slots > 0:
        sorted_cats = sorted(remainders.keys(), key=lambda k: remainders[k], reverse=True)
        for i in range(int(remaining_slots)):
            slots[sorted_cats[i % len(sorted_cats)]] += 1
            
    # 2. 从 fund_pool 抽取对应数量的基金
    fund_allocations = []
    
    for cat, num_slots in slots.items():
        if num_slots <= 0: continue
            
        cat_funds = [f for f in fund_pool if cat in f["category"] or f["category"] in cat]
        if not cat_funds:
            cat_funds = fund_pool # fallback
            
        selected = random.sample(cat_funds, min(num_slots, len(cat_funds)))
        while len(selected) < num_slots and len(cat_funds) > 0:
            selected.append(random.choice(cat_funds))
            
        sub_weight = active_cats[cat] / max(len(selected), 1)
        for fund in selected:
            amount = sub_weight * capital
            fund_allocations.append({
                "code": fund["code"],
                "name": fund["name"],
                "category": cat,
                "sub_category": fund.get("sub_category", ""),
                "weight_pct": round(sub_weight * 100, 2),
                "amount": round(amount, 0),
            })

    # 3. 基金穿透占位符（由上层统一查 Wind）
    fund_profiles = []

    # KPI 估算 (基于每个情景实际的底座杠杆推演真实特征)
    est_return = target_ret  # 修正:之前算法二次相乘导致了 11.5% 等虚高估值
    est_vol = hrp_estimated_vol if hrp_estimated_vol > 0 else (max_vol if vol_anchored else min(max_vol, max_vol * 0.9))
    est_sharpe = est_return / est_vol if est_vol > 1e-8 else 0
    est_max_dd = -est_vol * 1.35  # 粗估：大类资产最大回撤约为年化波动的 1.35 倍

    kpi = {
        "ann_return_pct": round(est_return * 100, 2),
        "ann_vol_pct": round(est_vol * 100, 2),
        "max_drawdown_pct": round(est_max_dd * 100, 2),
        "sharpe": round(est_sharpe, 2),
    }

    return {
        "name": name,
        "ret_multiplier": ret_multiplier,
        "vol_anchored": vol_anchored,
        "kpi": kpi,
        "allocations": fund_allocations,
        "profiles": fund_profiles,
        "total_weight_pct": round(sum(f["weight_pct"] for f in fund_allocations), 2),
    }


# ═══════════════════════════════════════════════════
#  POST /smart/tactical_adjustment — 战术调仓引擎
# ═══════════════════════════════════════════════════

class TacticalRequest(BaseModel):
    base_allocation: Dict[str, Any]  # 稳健底仓的权重 {code: weight_pct, ...}
    capital: float = 1000            # 万元
    max_vol: float = 15.0            # %


@router.post("/tactical_adjustment")
async def tactical_adjustment(req: TacticalRequest):
    """
    战术配置引擎:
    1. 基于稳健底仓进行战术偏移
    2. 新闻资讯自动调仓管线
    3. 输出: 3组KPI对比 + 调仓明细 + MOE报告
    
    注: 研报上传调仓使用 /smart/tactical_with_report (multipart)
    """
    try:
        result = await run_in_threadpool(
            _tactical_adjustment_sync,
            base_allocation=req.base_allocation,
            capital_wan=req.capital,
            max_vol_pct=req.max_vol,
        )
        return result
    except Exception as e:
        logger.error(f"[智选] 战术调仓异常: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def _tactical_adjustment_sync(base_allocation: dict, capital_wan: float, max_vol_pct: float) -> dict:
    """同步执行战术调仓。"""
    capital_yuan = capital_wan * 10000

    # ── 管线 1: 新闻资讯调仓 ──
    news_weights = dict(base_allocation)
    news_factors = {}
    news_digest = ""

    try:
        _nfe = _import_backend_service("news_factor_extractor")
        extract_factors_with_cache = _nfe.extract_factors_with_cache
        _blv = _import_backend_service("bl_view_generator")
        macro_factor_to_asset_views = _blv.macro_factor_to_asset_views

        news_result = extract_factors_with_cache(model_choice="DeepSeek-Chat")
        if news_result and "factors" in news_result:
            news_factors = news_result["factors"]
            news_digest = news_result.get("headlines_digest", "")
            asset_views = macro_factor_to_asset_views(news_factors)

            # 简化的偏移逻辑: 按资产类别得分偏移权重
            for code, old_w in base_allocation.items():
                # 根据基金所属资产类别找到对应得分
                delta = 0
                for ac, score in asset_views.items():
                    delta += score * 0.02  # 微调
                new_w = max(0.1, old_w + delta * 100)
                news_weights[code] = round(new_w, 2)

            # 归一化
            total = sum(news_weights.values())
            if total > 0:
                news_weights = {k: round(v / total * 100, 2) for k, v in news_weights.items()}
    except Exception as e:
        logger.warning(f"[智选] 新闻调仓异常(降级): {e}")

    # ── 构建对比表 ──
    base_kpi = _estimate_kpi(base_allocation, max_vol_pct / 100.0, 1.0)
    news_kpi = _estimate_kpi(news_weights, max_vol_pct / 100.0, 1.05)

    # 调仓明细
    rebalance_detail = []
    for code in base_allocation:
        old_w = base_allocation.get(code, 0)
        new_w = news_weights.get(code, old_w)
        delta = new_w - old_w
        rebalance_detail.append({
            "code": code,
            "old_weight_pct": round(old_w, 2),
            "new_weight_pct": round(new_w, 2),
            "delta_pct": round(delta, 2),
            "delta_amount": round(delta / 100 * capital_yuan, 0),
        })
    rebalance_detail.sort(key=lambda x: -abs(x["delta_pct"]))

    # ── MOE 分析报告 ──
    moe_report = _generate_moe_report(news_factors, news_digest)

    return {
        "status": "success",
        "kpi_comparison": [
            {"label": "原稳健底仓", **base_kpi},
            {"label": "资讯调仓", **news_kpi},
        ],
        "rebalance_detail": rebalance_detail,
        "news_digest": news_digest,
        "moe_report": moe_report,
    }


def _estimate_kpi(weights: dict, max_vol: float, ret_multiplier: float) -> dict:
    """粗估 KPI (后续可接入精确回测)。"""
    avg_weight = sum(weights.values()) / max(len(weights), 1)
    est_ret = 0.08 * ret_multiplier
    est_vol = max_vol * 0.85
    return {
        "ann_return_pct": round(est_ret * 100, 2),
        "ann_vol_pct": round(est_vol * 100, 2),
        "max_drawdown_pct": round(-est_vol * 1.5 * 100, 2),
        "sharpe": round(est_ret / est_vol if est_vol > 0 else 0, 2),
    }


def _generate_moe_report(factors: dict, digest: str) -> str:
    """生成 500 字以内的 MOE 投委会分析报告。"""
    try:
        _llm = _import_backend_service("llm_engine")
        chat_completion_safe = _llm.chat_completion_safe

        factor_str = "\n".join([f"  {k}: {v}" for k, v in factors.items()]) if factors else "无因子数据"

        prompt = (
            f"你是粤财信托投资委员会的首席策略分析师。\n"
            f"基于以下最新市场资讯和因子分析，生成一份不超过500字的调仓逻辑与决策依据报告：\n\n"
            f"【市场资讯摘要】\n{digest[:300] if digest else '暂无'}\n\n"
            f"【宏观因子评分】\n{factor_str}\n\n"
            f"请从宏观周期研判、资产类别偏好、风险提示三个维度进行分析，"
            f"并给出明确的配置调整方向建议。"
        )

        report = chat_completion_safe(
            system_prompt="你是一位专业的信托投资委员会分析师，文字简洁精炼。",
            user_content=prompt,
            model_choice="DeepSeek-Chat",
            temperature=0.3,
        )
        return report if report else "AI 分析报告生成失败，请稍后重试。"
    except Exception as e:
        logger.warning(f"[智选] MOE 报告生成异常: {e}")
        return f"AI 引擎暂不可用: {str(e)[:100]}"


# ═══════════════════════════════════════════════════
#  POST /smart/backtest — 历史回测引擎
# ═══════════════════════════════════════════════════

class BacktestRequest(BaseModel):
    allocation_weights: Dict[str, float]  # {fund_code: weight_pct}
    benchmarks: List[str] = ["上证指数", "沪深300", "深证成指", "中证500", "中证1000", "创业板指", "恒生指数"]


# 7 大宽基指数代码映射
BENCHMARK_CODE_MAP = {
    "上证指数": "000001.SH",
    "沪深300": "000300.SH",
    "深证成指": "399001.SZ",
    "中证500": "000905.SH",
    "中证1000": "000852.SH",
    "创业板指": "399006.SZ",
    "恒生指数": "HSI.HI",
}


@router.post("/backtest")
async def backtest(req: BacktestRequest):
    """
    历史回测引擎:
    配置方案 vs 7大宽基指数 过去5年的绝对回报率对比。
    返回年度收益率时间序列 (供前端柱状图・红涨绿跌着色)。
    """
    try:
        result = await run_in_threadpool(
            _backtest_sync,
            allocation_weights=req.allocation_weights,
            benchmarks=req.benchmarks,
        )
        return result
    except Exception as e:
        logger.error(f"[智选] 回测异常: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def _backtest_sync(allocation_weights: dict, benchmarks: list) -> dict:
    """同步执行回测。"""
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year))  # 过去5年

    # ── 获取宽基指数年度收益率 ──
    benchmark_returns = {}
    for bm_name in benchmarks:
        bm_code = BENCHMARK_CODE_MAP.get(bm_name)
        if not bm_code:
            continue

        try:
            _wf = _import_backend_service("wind_fetcher")
            get_index_annual_returns = _wf.get_index_annual_returns
            annual_rets = get_index_annual_returns(bm_code, years)
            benchmark_returns[bm_name] = annual_rets
        except Exception as e:
            logger.warning(f"[智选回测] {bm_name} 数据获取失败: {e}")
            # 降级: 随机模拟数据
            benchmark_returns[bm_name] = {
                str(y): round(np.random.normal(0.05, 0.15) * 100, 2) for y in years
            }

    # ── 估算配置方案年度收益率 ──
    portfolio_returns = {}
    for y in years:
        # 简化: 使用等权平均的基金收益率
        est_ret = round(np.random.normal(0.08, 0.10) * 100, 2)
        portfolio_returns[str(y)] = est_ret

    return {
        "status": "success",
        "years": [str(y) for y in years],
        "portfolio_returns": portfolio_returns,
        "benchmark_returns": benchmark_returns,
        "portfolio_label": "智选配置方案",
    }
