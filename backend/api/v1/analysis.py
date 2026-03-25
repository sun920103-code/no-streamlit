"""
分析计算 API — 宏观分析、风格归因、压力测试、持仓解析
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Optional
import re
import io

router = APIRouter()


@router.post("/parse-holdings")
async def parse_holdings(file: UploadFile = File(...)):
    """
    解析客户持仓 CSV 文件

    支持多编码（utf-8-sig / gbk / utf-8）和智能列识别。
    返回基金代码、名称、金额、占比。
    """
    import pandas as pd

    raw = await file.read()

    # 多编码容错读取
    df = None
    for enc in ['utf-8-sig', 'gbk', 'utf-8', 'gb2312', 'gb18030']:
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if df is None or df.empty:
        return {"status": "error", "message": "CSV 编码无法识别或内容为空"}

    # 智能列识别
    code_col = next((c for c in df.columns if any(k in c for k in ['代码', 'code', 'ticker', '编码'])), None)
    name_col = next((c for c in df.columns if any(k in c for k in ['名称', '简称', 'name'])), None)
    amt_col = next((c for c in df.columns if any(k in c for k in ['金额', '市值', '本金', '权重', 'amount'])), None)

    if not code_col:
        return {"status": "error", "message": '未找到基金代码列。CSV 必须包含标题含"代码"的列。'}
    if not amt_col:
        return {"status": "error", "message": '未找到金额列。CSV 必须包含标题含"金额"、"市值"或"本金"的列。'}

    unit_multiplier = 10000.0 if '万' in amt_col else 1.0
    holdings = []
    skipped = []
    total = 0.0

    for _, row in df.iterrows():
        raw_code = str(row[code_col]).strip()
        raw_name = str(row.get(name_col, '')).strip() if name_col else ''
        raw_amt = str(row[amt_col]).strip().replace(',', '').replace('%', '')

        if raw_code.lower() in ('nan', 'none', ''):
            continue
        if any(kw in raw_code for kw in ['合计', '总计']):
            continue

        clean_code = raw_code.split('.')[0].strip()
        if not re.match(r'^\d{4,6}$', clean_code):
            skipped.append(f"{raw_code} — 非有效基金代码")
            continue

        bare = clean_code.zfill(6)
        try:
            amt = float(raw_amt) * unit_multiplier
        except (ValueError, TypeError):
            amt = 0.0

        if amt > 0:
            name = raw_name if raw_name.lower() not in ('nan', 'none', '') else ''
            holdings.append({
                "code": bare,
                "name": name,
                "amount": round(amt, 2),
            })
            total += amt

    # 计算占比
    for h in holdings:
        h["proportion"] = round(h["amount"] / total, 4) if total > 0 else 0

    return {
        "status": "ok",
        "holdings": holdings,
        "total": round(total, 2),
        "count": len(holdings),
        "skipped": skipped,
    }


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
    """运行压力测试场景 (模拟返回 API Contract Interface 3 KPI)"""
    return {
      "kpi_list": [
        {
          "strategy_label": "📋 客户持仓",
          "ann_return": 0.0520,
          "ann_volatility": 0.1250,
          "sharpe_ratio": 1.20,
          "max_drawdown": -0.1520,
          "calmar_ratio": 0.34,
          "win_rate": 0.550
        },
        {
          "strategy_label": "⚖️ HRP 配置 [沪深300基准]",
          "ann_return": 0.0810,
          "ann_volatility": 0.1010,
          "sharpe_ratio": 1.85,
          "max_drawdown": -0.0980,
          "calmar_ratio": 0.82,
          "win_rate": 0.612
        }
      ]
    }
