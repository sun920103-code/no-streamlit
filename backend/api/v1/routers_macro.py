import os
import sys
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlimit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.insert(0, LEGACY_SERVICES_DIR)

router = APIRouter(prefix="/macro", tags=["宏观经济基座"])

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
            calculate_factor_scores
        )
        
        # 1. 抓取三组基础数据
        macro_data = await run_in_threadpool(fetch_macro_factors)
        val_data = await run_in_threadpool(fetch_valuation_factors)
        risk_data = await run_in_threadpool(fetch_risk_momentum_factors)
        
        # 2. 计算衍生指标
        derived = await run_in_threadpool(calculate_derived_factors, macro_data, val_data)
        
        # 3. 计算最终得分
        scores = await run_in_threadpool(calculate_factor_scores, macro_data, val_data, risk_data, derived)
        
        if not scores:
            scores = {
                "composite_score": 0.5, 
                "market_state": "Recovery", 
                "macro_total": 0.4, 
                "valuation_total": 0.3, 
                "risk_total": 0.3,
                "factor_analysis": {"details": "使用默认基座兜底"}
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
