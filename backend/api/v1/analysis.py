"""
分析计算 API — 宏观分析、风格归因、压力测试
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional

router = APIRouter()


class MacroRegimeResponse(BaseModel):
    regime: str
    confidence: float
    indicators: Dict[str, float]
    description: str


class StyleAnalysisRequest(BaseModel):
    fund_codes: List[str]
    lookback_days: int = 252


@router.get("/macro/regime", response_model=MacroRegimeResponse)
async def get_macro_regime():
    """
    获取当前宏观经济体制判断

    基于 EDB 指标 Z-score 映射宏观周期阶段。
    """
    # TODO: Phase 2 — 对接 macro_data_collector + EDB
    return MacroRegimeResponse(
        regime="recovery",
        confidence=0.72,
        indicators={
            "PMI": 50.2,
            "CPI_YoY": 0.8,
            "M2_Growth": 7.1,
            "Credit_Impulse": 1.3,
        },
        description="当前处于复苏阶段，制造业 PMI 重返荣枯线上方",
    )


@router.get("/whitebox/bl-views")
async def get_bl_views():
    """
    量化决策白盒 — Black-Litterman 观点矩阵

    展示 AI 生成的资产观点及其置信度。
    """
    # TODO: Phase 2 — 对接 bl_view_generator
    return {
        "views": [
            {"asset": "股票多头", "expected_return": 0.08, "confidence": 0.6},
            {"asset": "纯债固收", "expected_return": 0.035, "confidence": 0.85},
            {"asset": "黄金商品", "expected_return": 0.05, "confidence": 0.5},
        ],
        "method": "Black-Litterman + Bayesian Shrinkage",
        "data_source": "AI + EDB Z-scores",
    }


@router.post("/style-analysis")
async def run_style_analysis(request: StyleAnalysisRequest):
    """运行基金风格归因分析 (RBSA)"""
    # TODO: Phase 2 — 对接 rbsa_style_analyzer
    return {
        "status": "not_implemented",
        "message": "风格归因引擎将在 Phase 2 对接",
    }


@router.get("/stress-test")
async def run_stress_test():
    """运行压力测试场景"""
    # TODO: Phase 2 — 对接 stress_testing
    return {
        "scenarios": [
            {"name": "2020 新冠冲击", "portfolio_impact": -0.018},
            {"name": "2022 债市调整", "portfolio_impact": -0.012},
            {"name": "利率上行100bp", "portfolio_impact": -0.008},
        ],
        "status": "mock_data",
    }
