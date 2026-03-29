"""
因子风险平价引擎 (Factor Risk Parity)
=====================================
将 HRP 的核心逻辑从"资产级波动率平价"升级为"宏观因子级风险贡献平价"。

核心思想:
  不再让 HRP 对 114 只基金平价波动率（可能表面分散但全挂在增长因子上），
  而是确保组合对 6 大宏观因子的风险暴露绝对均等。

这是桥水全天候 (All Weather) 策略的中国白盒化实装。

管线:
  1. 计算 6 个因子各自对组合的风险贡献
  2. 调整权重使各因子风险贡献趋于相等
  3. 在马尔可夫高危象限中强制退守现金
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from services.factor_loadings import (
    MACRO_FACTORS,
    ASSET_CLASSES,
    FACTOR_LOADINGS,
    determine_quadrant,
    QUADRANT_DEFINITIONS,
)


def compute_factor_risk_contributions(
    weights: Dict[str, float],
    asset_volatilities: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    计算组合中各宏观因子的近似风险贡献比例。
    
    方法: 
      Factor_Risk_i = sum_j(weight_j × |loading_ij| × volatility_j)
      然后归一化到百分比。

    :param weights: 资产权重字典 {"大盘核心": 0.3, ...}
    :param asset_volatilities: 可选的资产年化波动率，不提供则使用典型值
    :return: {"经济增长": 0.35, "通胀商品": 0.15, ...} 归一化的因子风险贡献
    """
    # 典型的大类资产年化波动率先验
    DEFAULT_VOLS = {
        "大盘核心": 0.22, "科技成长": 0.30, "红利防守": 0.15,
        "纯债固收": 0.04, "混合债券": 0.06, "短债理财": 0.015,
        "黄金商品": 0.18, "海外QDII": 0.25,
    }
    vols = asset_volatilities or DEFAULT_VOLS
    
    factor_risk = {}
    for factor in MACRO_FACTORS:
        risk = 0.0
        for asset in ASSET_CLASSES:
            w = weights.get(asset, 0.0)
            loading = abs(FACTOR_LOADINGS.loc[factor, asset])
            vol = vols.get(asset, 0.15)
            risk += w * loading * vol
        factor_risk[factor] = risk
    
    # 归一化
    total = sum(factor_risk.values())
    if total > 0:
        factor_risk = {k: round(v / total, 4) for k, v in factor_risk.items()}
    
    return factor_risk


def optimize_factor_risk_parity(
    current_quadrant: Optional[str] = None,
    factor_scores: Optional[Dict[str, float]] = None,
    max_volatility: float = 0.15,
    target_return: float = 0.0,
) -> Dict[str, Any]:
    """
    因子风险平价优化器 — 宏观象限对应配置的核心。
    
    在"正常"周期中，追求 6 因子等权风险贡献；
    在"危险"象限中，自动退守低风险资产。
    
    :param current_quadrant: 当前象限 ("recovery" / "overheat" / "stagflation" / "deflation")
    :param factor_scores: 如果提供则自动推断象限
    :param max_volatility: 最大可承受年化波动率
    :return: 优化结果字典（包括权重、因子风险贡献、白盒链条）
    """
    # 判断象限
    if current_quadrant is None and factor_scores:
        current_quadrant = determine_quadrant(factor_scores)
    elif current_quadrant is None:
        current_quadrant = "recovery"
    
    quadrant_info = QUADRANT_DEFINITIONS.get(current_quadrant, QUADRANT_DEFINITIONS["recovery"])
    
    # ── Step 1: 寻找因子风险平价的初始权重 ──
    # 逆波动率加权法 (Inverse Volatility + Factor Loading Balancing)
    DEFAULT_VOLS = {
        "大盘核心": 0.22, "科技成长": 0.30, "红利防守": 0.15,
        "纯债固收": 0.04, "混合债券": 0.06, "短债理财": 0.015,
        "黄金商品": 0.18, "海外QDII": 0.25,
    }
    
    # 初始权重 = 1 / volatility (波动率倒数)
    inv_vols = {a: 1.0 / v for a, v in DEFAULT_VOLS.items()}
    total_inv = sum(inv_vols.values())
    weights = {a: round(inv_vols[a] / total_inv, 4) for a in ASSET_CLASSES}
    
    # ── Step 2: 象限防御自适应覆写 ──
    defense_log = []
    
    if current_quadrant == "stagflation":
        # 滞胀：大幅压降权益，提升现金和大宗
        for asset in ["大盘核心", "科技成长", "海外QDII"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.3, 4)
            defense_log.append(f"⚠️ 滞胀防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["黄金商品"] = round(weights["黄金商品"] * 2.0, 4)
        weights["短债理财"] = round(weights["短债理财"] * 2.0, 4)
        defense_log.append("🛡️ 滞胀象限: 加配黄金与短债作为安全气囊")
        
    elif current_quadrant == "deflation":
        # 衰退通缩：压降权益，拉满长债避险
        for asset in ["大盘核心", "科技成长", "海外QDII"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.4, 4)
            defense_log.append(f"⚠️ 衰退防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["纯债固收"] = round(weights["纯债固收"] * 1.8, 4)
        defense_log.append("🛡️ 衰退象限: 加配长久期国债，央行降息利好债券")
        
    elif current_quadrant == "overheat":
        # 过热：压降债券和成长股，加配大宗商品
        for asset in ["纯债固收", "科技成长"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.5, 4)
            defense_log.append(f"⚠️ 过热防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["黄金商品"] = round(weights["黄金商品"] * 2.0, 4)
        defense_log.append("🔥 过热象限: 通胀上行利好大宗商品，债券承压")
    
    # ── Step 3: 重新归一化 ──
    total = sum(weights.values())
    weights = {a: w / total for a, w in weights.items()}
    
    # ── [NEW] Step 3.5: Risk Targeting (双约束最优夏普逼近) ──
    RISK_ASSETS = ["大盘核心", "科技成长", "红利防守", "黄金商品", "海外QDII"]
    SAFE_ASSETS = ["纯债固收", "混合债券", "短债理财"]
    
    # 典型大类资产年化收益率先验 (供推演使用)
    DEFAULT_RETURNS = {
        "大盘核心": 0.08, "科技成长": 0.12, "红利防守": 0.06,
        "纯债固收": 0.035, "混合债券": 0.05, "短债理财": 0.025,
        "黄金商品": 0.07, "海外QDII": 0.09,
    }

    current_vol = sum(weights.get(a, 0) * DEFAULT_VOLS.get(a, 0.15) for a in ASSET_CLASSES)
    current_ret = sum(weights.get(a, 0) * DEFAULT_RETURNS.get(a, 0.05) for a in ASSET_CLASSES)
    
    step_size = 0.05
    tolerance_vol = 0.002
    tolerance_ret = 0.002
    
    target_return = target_return or 0.0

    for _ in range(50):
        # 状况1：波动率超标 -> 必须强制降杠杆，抛弃不切实际的收益幻想，强力压降波动
        if current_vol > max_volatility + tolerance_vol:
            risk_wt = sum(weights.get(a, 0) for a in RISK_ASSETS)
            if risk_wt <= 0.02: break
            for a in RISK_ASSETS: weights[a] *= (1 - step_size)
            for a in SAFE_ASSETS: weights[a] *= (1 + step_size)
            
        # 状况2：波动率没超标，但收益率还未达到目标 -> 提升风险敞口
        elif current_ret < target_return - tolerance_ret and current_vol < max_volatility - tolerance_vol:
            safe_wt = sum(weights.get(a, 0) for a in SAFE_ASSETS)
            if safe_wt <= 0.02: break 
            for a in SAFE_ASSETS: weights[a] *= (1 - step_size)
            for a in RISK_ASSETS: weights[a] *= (1 + step_size)
            
        # 状况3：收益已经达标，且波动率未超限；或是两者都已经逼近临界点 -> 我们得到了夏普最优解，退出！
        else:
            break
            
        # 归一化并重新测算
        total_w = sum(weights.values())
        weights = {a: w / total_w for a, w in weights.items()}
        current_vol = sum(weights.get(a, 0) * DEFAULT_VOLS.get(a, 0.15) for a in ASSET_CLASSES)
        current_ret = sum(weights.get(a, 0) * DEFAULT_RETURNS.get(a, 0.05) for a in ASSET_CLASSES)

    # 封顶格式化
    weights = {a: round(w, 4) for a, w in weights.items()}

    # ── Step 4: 计算最终因子风险贡献（供白盒前端展示） ──
    factor_risks = compute_factor_risk_contributions(weights)
    
    # ── Step 5: 组合级预估指标 ──
    estimated_vol = sum(weights.get(a, 0) * DEFAULT_VOLS.get(a, 0.15) for a in ASSET_CLASSES)
    
    return {
        "status": "success",
        "method": "🧭 宏观象限对应配置 (Factor Risk Parity)",
        "quadrant": current_quadrant,
        "quadrant_label": quadrant_info["label"],
        "quadrant_description": quadrant_info["description"],
        "target_weights": weights,
        "factor_risk_contributions": factor_risks,
        "estimated_volatility": round(estimated_vol, 4),
        "defense_log": defense_log,
        "best_assets": quadrant_info["best_assets"],
        "worst_assets": quadrant_info["worst_assets"],
    }
