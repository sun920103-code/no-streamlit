import os
import sys
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.append(LEGACY_SERVICES_DIR)

router = APIRouter(prefix="/macro", tags=["宏观经济基座"])

@router.get("/debug")
def debug_import():
    try:
        from services.markov_engine import get_current_macro_regime_live
        return {"status": "ok", "module": str(get_current_macro_regime_live)}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc(), "sys_path": sys.path}

@router.post("/fetch_edb_data")
async def fetch_edb_data():
    """
    一键式宏观及流动性、估值、风险阵列 EDB 检索与清洗
    """
    try:
        from services.macro_data_collector import (
            fetch_macro_factors, 
            fetch_valuation_factors, 
            fetch_risk_momentum_factors, 
            calculate_derived_factors, 
            calculate_factor_scores,
            _check_wind
        )
        
        # [优化] 如果 Wind 彻底挂了，别再循环去测算浪费时间，直接使用 Tushare 兜底引擎！
        is_wind_alive = await run_in_threadpool(_check_wind)
        scores = None

        if is_wind_alive:
            # 1. 抓取三组基础数据
            macro_data = await run_in_threadpool(fetch_macro_factors)
            val_data = await run_in_threadpool(fetch_valuation_factors)
            risk_data = await run_in_threadpool(fetch_risk_momentum_factors)
            
            # 2. 计算衍生指标
            derived = await run_in_threadpool(calculate_derived_factors, macro_data, val_data)
            
            # 3. 计算最终得分
            scores = await run_in_threadpool(calculate_factor_scores, macro_data, val_data, risk_data, derived)
            
            # 如果得出所有都是 0，视为无效数据
            if isinstance(scores, dict) and scores.get("macro_total") == 0.0 and scores.get("valuation_total") == 0.0 and scores.get("risk_total") == 0.0:
                scores = None
                
        # 4. 判断是否需要兜底 (Wind断线，或者分数全为 0)
        if not scores:
            try:
                from services.markov_engine import get_current_macro_regime_live
                import math
                hmm = await run_in_threadpool(get_current_macro_regime_live)
                z = hmm.get("latest_zscores", {})
                
                # Tushare Z-scores -> -1 到 1 之间的强度映射
                pmi_score = math.tanh(z.get("PMI", 0) / 2.0)
                m2_score = math.tanh(z.get("M2_Growth", 0) / 2.0)
                cpi_score = math.tanh(z.get("CPI_YoY", 0) / 2.0)
                credit_score = math.tanh(z.get("Credit_Impulse", 0) / 2.0)
                
                macro_tot = (pmi_score + m2_score + credit_score) / 3.0
                val_tot = -cpi_score / 2.0
                risk_tot = (pmi_score - cpi_score) / 2.0
                
                comp = (macro_tot + val_tot + risk_tot) / 3.0
                state_map = {"recovery": "Recovery", "overheat": "Overheat", "stagflation": "Stagflation", "deflation": "Deflation"}
                m_state = state_map.get(hmm.get("current_regime", "recovery"), "Recovery")
                
                scores = {
                    "composite_score": round(comp, 3),
                    "market_state": m_state.upper(),
                    "macro_total": round(macro_tot, 3),
                    "valuation_total": round(val_tot, 3),
                    "risk_total": round(risk_tot, 3),
                    "factor_analysis": {"details": "Wind API脱机，Tushare Engine 已横向接管底层宏观数据"}
                }
                logger.info(f"[EDB] Wind不可用，已成功调用Tushare生成兜底宏观矩阵: {scores}")
            except Exception as fe:
                import traceback
                logger.warning(f"[EDB] Tushare 兜底发生异常: {fe}\n{traceback.format_exc()}")
                scores = {
                    "composite_score": 0.0, 
                    "market_state": "UNKNOWN", 
                    "macro_total": 0.0, 
                    "valuation_total": 0.0, 
                    "risk_total": 0.0,
                    "factor_analysis": {"details": "全部数据源断开连接"}
                }
            
        return {
            "status": "success",
            "data": scores
        }
    except Exception as e:
        logger.error(f"EDB 数据检索失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

class AssetAllocRequest(BaseModel):
    debate_views: Dict[str, Any]

@router.post("/calculate_asset_allocation")
async def calculate_asset_allocation(payload: AssetAllocRequest):
    """
    接收虚投研会的多空结论，自上而下推导大类资产配置靶向比例。
    """
    # 提取多空情绪 (这里简化运用 heuristics 融合系统默认测算逻辑)
    views = payload.debate_views
    
    # 根据 LLM 的 views 进行偏移：看多权益则提高 equity，看多固收则提高 bond
    eq_w = 40.0
    bd_w = 45.0
    cs_w = 15.0
    
    for asset, score in views.items():
        if isinstance(score, dict):
            view_val = score.get("view", 0)
        else:
            view_val = float(score)
            
        if "权益" in asset or "股票" in asset or "市值" in asset:
            eq_w += view_val * 20
            bd_w -= view_val * 10
            cs_w -= view_val * 10
        elif "债" in asset:
            bd_w += view_val * 20
            eq_w -= view_val * 10
            cs_w -= view_val * 10
            
    # 归一化并细分大类
    tot = max(eq_w + bd_w + cs_w, 1.0)
    eq_w, bd_w, cs_w = eq_w/tot, bd_w/tot, cs_w/tot
    
    allocations = {
        "📊 大盘价值": round(eq_w * 0.4 * 100, 2),
        "🚀 科技成长": round(eq_w * 0.3 * 100, 2),
        "🛡️ 红利低波": round(eq_w * 0.3 * 100, 2),
        "🏦 纯债基底": round(bd_w * 0.7 * 100, 2),
        "🔀 宏观对冲": round(bd_w * 0.3 * 100, 2),
        "💵 现金管理": round(cs_w * 100, 2)
    }
    
    return {
        "status": "success",
        "target_allocation": allocations
    }


class QuadrantRequest(BaseModel):
    factor_scores: Dict[str, Any] = {}


@router.post("/quadrant")
async def get_macro_quadrant(payload: QuadrantRequest = None):
    """
    🧭 宏观四象限可视化数据 (桥水全天候)

    返回当前所处象限、四象限定义以及因子传导链条，
    供前端绘制宏观雷达十字坐标与象限高亮。
    """
    try:
        from services.factor_loadings import (
            determine_quadrant,
            QUADRANT_DEFINITIONS,
            factor_scores_to_asset_expected_returns,
        )
        from services.markov_engine import get_current_macro_regime_live

        # 马尔可夫状态概率 (真实拉取)
        hmm_result = await run_in_threadpool(get_current_macro_regime_live)
        z = hmm_result.get("latest_zscores", {})

        # 如果前端传入了因子得分，直接使用；否则从马尔可夫引擎推断
        if payload and payload.factor_scores:
            scores = {k: float(v) for k, v in payload.factor_scores.items() if isinstance(v, (int, float))}
        else:
            # 用真实马尔可夫状态推导的最新 Z-score 代替默认数值
            import math
            scores = {
                "经济增长": round(math.tanh(z.get("PMI", 0) / 2.0), 3),
                "通胀商品": round(math.tanh(z.get("CPI_YoY", 0) / 2.0), 3),
                "利率环境": round(math.tanh(-z.get("Credit_Impulse", 0) / 2.0), 3),
                "信用扩张": round(math.tanh(z.get("Credit_Impulse", 0) / 2.0), 3),
                "海外环境": round(math.tanh(-z.get("US10Y", 0) / 2.0), 3),
                "市场情绪": round(math.tanh(z.get("M2_Growth", 0) / 3.0), 3),
            }

        current_q = determine_quadrant(scores)
        q_info = QUADRANT_DEFINITIONS[current_q]
        asset_signals = factor_scores_to_asset_expected_returns(scores, apply_regime=True)

        return {
            "status": "success",
            "current_quadrant": current_q,
            "quadrant_label": q_info["label"],
            "quadrant_description": q_info["description"],
            "growth_axis": scores.get("经济增长", 0.0),
            "inflation_axis": scores.get("通胀商品", 0.0),
            "best_assets": q_info["best_assets"],
            "worst_assets": q_info["worst_assets"],
            "asset_signals": asset_signals,
            "all_quadrants": {
                k: {"label": v["label"], "description": v["description"]}
                for k, v in QUADRANT_DEFINITIONS.items()
            },
            "markov_regime": hmm_result.get("current_regime", "unknown"),
            "markov_confidence": hmm_result.get("confidence", 0.0),
        }
    except Exception as e:
        import traceback
        logger.error(f"四象限推断失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

