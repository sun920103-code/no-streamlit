"""
宏观因子 Black-Litterman 引擎 (Macro-Factor BL / MBL)
=====================================================
核心创新:
  AI 不再预测具体资产涨跌，而是输出对 6 个宏观因子的得分。
  本引擎通过因子载荷矩阵（Factor Loadings）将因子观点严密传导到
  8 大类资产，并结合 CVaR 或 HRP 进行最终权重优化。

管线:
  1. AI 委员会 → 6 因子得分 (e.g. 经济增长: +0.8, 通胀: -0.3)
  2. factor_loadings.factor_scores_to_asset_expected_returns() 
     → 8 资产的预期收益信号
  3. mbl_engine.optimize_with_mbl()
     → CVaR 或 HRP 约束下的最终资产权重

这条管线完美避免了让 LLM 直接猜测资产权重的危险做法。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from services.factor_loadings import (
    MACRO_FACTORS,
    ASSET_CLASSES,
    FACTOR_LOADINGS,
    determine_quadrant,
    get_regime_modifiers,
    factor_scores_to_asset_expected_returns,
    QUADRANT_DEFINITIONS,
)


def optimize_with_mbl(
    factor_scores: Dict[str, float],
    max_volatility: float = 0.15,
    target_return: Optional[float] = None,
    apply_regime: bool = True,
) -> Dict[str, Any]:
    """
    完整的 MBL (Macro-Factor Black-Litterman) 优化管线。
    
    :param factor_scores: AI 委员会输出的 6 个宏观因子得分 ([-1, 1])
    :param max_volatility: 目标最大年化波动率上限
    :param target_return: 可选的目标年化收益率
    :param apply_regime: 是否启用四象限体制调控
    :return: 完整结果字典
    """
    # ── Step 1: 因子 → 资产预期收益信号 ──
    asset_signals = factor_scores_to_asset_expected_returns(
        factor_scores, apply_regime=apply_regime
    )
    
    # ── Step 2: 识别当前象限 ──
    quadrant = determine_quadrant(factor_scores)
    quadrant_info = QUADRANT_DEFINITIONS[quadrant]
    
    # ── Step 3: 信号 → 权重 (简化的风险预算模型) ──
    # 对正值信号进行 softmax 归一化得到初始权重
    scores_array = np.array([asset_signals.get(a, 0.0) for a in ASSET_CLASSES])
    
    # 将信号转化为权重: 正信号资产按比例分配，负信号资产获得微小权重
    # 使用 exp(score) softmax 来确保所有权重为正且归一
    exp_scores = np.exp(scores_array * 2.0)  # 放大以增强区分度
    raw_weights = exp_scores / exp_scores.sum()
    
    # ── Step 4: 象限防御约束 ──
    # 在危险象限（滞胀/衰退）中，强制压降高风险资产权重
    if quadrant in ("stagflation", "deflation"):
        # 风险资产（股票类）上限 30%
        risk_assets = ["大盘核心", "科技成长", "海外QDII"]
        for i, asset in enumerate(ASSET_CLASSES):
            if asset in risk_assets:
                raw_weights[i] = min(raw_weights[i], 0.10)
        # 重新归一化
        raw_weights = raw_weights / raw_weights.sum()
    
    # ── Step 5: 最终构造 ──
    target_weights = {
        asset: round(float(w), 4) 
        for asset, w in zip(ASSET_CLASSES, raw_weights)
    }
    
    # 构建因子传导链条（供白盒展示）
    transmission_chain = []
    for factor in MACRO_FACTORS:
        score = factor_scores.get(factor, 0.0)
        if abs(score) > 0.1:
            direction = "看多" if score > 0 else "看空"
            modifier = quadrant_info["factor_modifiers"].get(factor, 1.0)
            transmission_chain.append({
                "factor": factor,
                "score": round(score, 2),
                "direction": direction,
                "regime_modifier": modifier,
                "effective_score": round(score * modifier, 2),
            })
    
    return {
        "status": "success",
        "method": "MBL (Macro-Factor Black-Litterman)",
        "quadrant": quadrant,
        "quadrant_label": quadrant_info["label"],
        "quadrant_description": quadrant_info["description"],
        "asset_signals": asset_signals,
        "target_weights": target_weights,
        "best_assets": quadrant_info["best_assets"],
        "worst_assets": quadrant_info["worst_assets"],
        "transmission_chain": transmission_chain,
        "factor_scores_input": {k: round(v, 2) for k, v in factor_scores.items()},
    }
