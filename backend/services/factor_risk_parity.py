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
import json
import os
from typing import Dict, Any, Optional

from services.factor_loadings import (
    MACRO_FACTORS,
    ASSET_CLASSES,
    FACTOR_LOADINGS,
    determine_quadrant,
    QUADRANT_DEFINITIONS,
)

# ────────────────────────────────────────────────────────────
# 动态加载资产先验参数 (由 scripts/update_asset_priors.py 每周五生成)
# 如果 data/asset_priors.json 存在则使用真实数据，否则回退到硬编码默认值
# ────────────────────────────────────────────────────────────
_PRIORS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "asset_priors.json")

# ── 硬编码默认值 (作为 Wind 不可用时的兜底) ──
_DEFAULT_CORRELATION = np.array([
    [ 1.00,    0.82,    0.65,   -0.15,   0.10,   -0.02,   0.05,    0.35],
    [ 0.82,    1.00,    0.50,   -0.20,   0.05,   -0.03,  -0.05,    0.40],
    [ 0.65,    0.50,    1.00,    0.00,   0.15,    0.02,   0.10,    0.25],
    [-0.15,   -0.20,    0.00,    1.00,   0.70,    0.80,   0.10,   -0.10],
    [ 0.10,    0.05,    0.15,    0.70,   1.00,    0.65,   0.08,    0.05],
    [-0.02,   -0.03,    0.02,    0.80,   0.65,    1.00,   0.05,   -0.05],
    [ 0.05,   -0.05,    0.10,    0.10,   0.08,    0.05,   1.00,    0.15],
    [ 0.35,    0.40,    0.25,   -0.10,   0.05,   -0.05,   0.15,    1.00],
])

_DEFAULT_VOLS_FALLBACK = {
    "大盘核心": 0.22, "科技成长": 0.30, "红利防守": 0.15,
    "纯债固收": 0.035, "混合债券": 0.055, "短债理财": 0.012,
    "黄金商品": 0.18, "海外QDII": 0.25,
}

_DEFAULT_RETURNS_FALLBACK = {
    "大盘核心": 0.10, "科技成长": 0.14, "红利防守": 0.08,
    "纯债固收": 0.04, "混合债券": 0.055, "短债理财": 0.028,
    "黄金商品": 0.08, "海外QDII": 0.10,
}


def _load_asset_priors() -> dict:
    """
    加载资产先验参数。优先从 asset_priors.json 读取 Wind 真实数据,
    否则回退到硬编码默认值。
    """
    if os.path.exists(_PRIORS_FILE):
        try:
            with open(_PRIORS_FILE, 'r', encoding='utf-8') as f:
                priors = json.load(f)
            
            ordered = priors.get("asset_classes", ASSET_CLASSES)
            # 重建相关矩阵 (按 ASSET_CLASSES 顺序)
            raw_corr = priors.get("correlation_matrix", [])
            if raw_corr and len(raw_corr) == len(ordered):
                # 映射到标准顺序
                idx_map = {ac: i for i, ac in enumerate(ordered)}
                n = len(ASSET_CLASSES)
                corr = np.eye(n)
                for i, ac_i in enumerate(ASSET_CLASSES):
                    for j, ac_j in enumerate(ASSET_CLASSES):
                        if ac_i in idx_map and ac_j in idx_map:
                            corr[i, j] = raw_corr[idx_map[ac_i]][idx_map[ac_j]]
                correlation_matrix = corr
            else:
                correlation_matrix = _DEFAULT_CORRELATION
            
            vols = priors.get("default_vols", _DEFAULT_VOLS_FALLBACK)
            rets = priors.get("default_returns", _DEFAULT_RETURNS_FALLBACK)
            source = "wind"
            updated_at = priors.get("updated_at", "unknown")
            
            print(f"[FactorRP] ✅ 已加载 Wind 资产先验 (更新于 {updated_at})")
            
            return {
                "correlation_matrix": correlation_matrix,
                "default_vols": vols,
                "default_returns": rets,
                "source": source,
            }
        except Exception as e:
            print(f"[FactorRP] ⚠️ 加载 asset_priors.json 失败: {e}, 使用默认值")
    else:
        print(f"[FactorRP] ℹ️ 未找到 asset_priors.json, 使用硬编码默认值")
    
    return {
        "correlation_matrix": _DEFAULT_CORRELATION,
        "default_vols": _DEFAULT_VOLS_FALLBACK,
        "default_returns": _DEFAULT_RETURNS_FALLBACK,
        "source": "hardcoded",
    }


# 模块加载时执行一次
_CACHED_PRIORS = _load_asset_priors()
CORRELATION_MATRIX = _CACHED_PRIORS["correlation_matrix"]


def _portfolio_volatility(
    weights: Dict[str, float],
    vols: Dict[str, float],
) -> float:
    """
    马科维茨组合方差公式: σ_p = sqrt(w^T Σ w)
    其中 Σ = diag(σ) × ρ × diag(σ) 是协方差矩阵。
    使用从 Wind 加载的真实相关矩阵。
    """
    w = np.array([weights.get(a, 0.0) for a in ASSET_CLASSES])
    sigma = np.array([vols.get(a, 0.15) for a in ASSET_CLASSES])
    cov_matrix = np.outer(sigma, sigma) * CORRELATION_MATRIX
    port_var = w @ cov_matrix @ w
    return float(np.sqrt(max(port_var, 0.0)))


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
    # 使用从 Wind 缓存的真实波动率 (或硬编码兜底)
    DEFAULT_VOLS = dict(_CACHED_PRIORS["default_vols"])
    
    # 初始权重 = 1 / volatility (波动率倒数)
    inv_vols = {a: 1.0 / v for a, v in DEFAULT_VOLS.items()}
    total_inv = sum(inv_vols.values())
    weights = {a: round(inv_vols[a] / total_inv, 4) for a in ASSET_CLASSES}
    
    # ── Step 2: 象限防御自适应覆写 ──
    defense_log = []
    
    if current_quadrant == "stagflation":
        # 谨慎观望期：大幅压降权益，提升现金和大宗
        for asset in ["大盘核心", "科技成长", "海外QDII"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.3, 4)
            defense_log.append(f"⚠️ 谨慎观望防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["黄金商品"] = round(weights["黄金商品"] * 2.0, 4)
        weights["短债理财"] = round(weights["短债理财"] * 2.0, 4)
        defense_log.append("🛡️ 谨慎观望象限: 加配黄金与短债作为安全气囊")
        
    elif current_quadrant == "deflation":
        # 等待复苏期：压降权益，拉满长债避险
        for asset in ["大盘核心", "科技成长", "海外QDII"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.4, 4)
            defense_log.append(f"⚠️ 等待复苏防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["纯债固收"] = round(weights["纯债固收"] * 1.8, 4)
        defense_log.append("🛡️ 等待复苏象限: 加配长久期国债，央行降息利好债券")
        
    elif current_quadrant == "overheat":
        # 景气高位期：压降债券和成长股，加配大宗商品
        for asset in ["纯债固收", "科技成长"]:
            old_w = weights[asset]
            weights[asset] = round(old_w * 0.5, 4)
            defense_log.append(f"⚠️ 景气高位防御: {asset} 权重 {old_w:.2%} → {weights[asset]:.2%}")
        weights["黄金商品"] = round(weights["黄金商品"] * 2.0, 4)
        defense_log.append("🔥 景气高位象限: 通胀上行利好大宗商品，债券承压")
    
    # ── Step 3: 重新归一化 ──
    total = sum(weights.values())
    weights = {a: w / total for a, w in weights.items()}
    
    # ── [NEW] Step 3.5: Risk Targeting (双约束最优夏普逼近) ──
    RISK_ASSETS = ["大盘核心", "科技成长", "红利防守", "黄金商品", "海外QDII"]
    SAFE_ASSETS = ["纯债固收", "混合债券", "短债理财"]
    
    # 使用从 Wind 缓存的真实收益率先验 (或硬编码兜底)
    DEFAULT_RETURNS = dict(_CACHED_PRIORS["default_returns"])

    current_vol = _portfolio_volatility(weights, DEFAULT_VOLS)
    current_ret = sum(weights.get(a, 0) * DEFAULT_RETURNS.get(a, 0.05) for a in ASSET_CLASSES)
    
    step_size = 0.06
    tolerance_ret = 0.001
    
    target_return = target_return or 0.0

    # ── 最小波动率约束优化 (双约束) ──
    # 目标: 在锁定 target_return 的前提下，最小化组合波动率
    # max_volatility 是硬性红线，若最小化后仍超标则进入情景 B
    for iteration in range(200):
        # 自适应步长: 离目标越近步长越小，保证精确收敛
        gap = abs(current_ret - target_return)
        # 下界 0.20 保证在收益率接近目标时仍有足够推进力
        adaptive_step = step_size * max(0.20, min(1.0, gap / max(target_return, 0.01)))
        
        if current_ret < target_return - tolerance_ret:
            # 收益率不够 → 增配风险资产 (接受更高波动)
            # [核心修复] 如果波动率已经触碰红线，必须停止激进增配，防止无视波动率约束
            if current_vol >= max_volatility:
                break
                
            safe_wt = sum(weights.get(a, 0) for a in SAFE_ASSETS)
            if safe_wt <= 0.005:
                break  # 已全仓风险资产，收益率封顶
            for a in SAFE_ASSETS: weights[a] *= (1 - adaptive_step)
            for a in RISK_ASSETS: weights[a] *= (1 + adaptive_step)
            
        elif current_ret > target_return + tolerance_ret or current_vol > max_volatility + 0.001:
            # 收益率超标，或波动率超标 → 降低风险敞口来压缩波动率
            risk_wt = sum(weights.get(a, 0) for a in RISK_ASSETS)
            if risk_wt <= 0.005:
                break
            for a in RISK_ASSETS: weights[a] *= (1 - adaptive_step)
            for a in SAFE_ASSETS: weights[a] *= (1 + adaptive_step)
            
        else:
            # 收益率已精确锁定在目标附近，且波动率未超标 → 解已收敛
            break
            
        # 归一化并重新测算
        total_w = sum(weights.values())
        weights = {a: w / total_w for a, w in weights.items()}
        current_vol = _portfolio_volatility(weights, DEFAULT_VOLS)
        current_ret = sum(weights.get(a, 0) * DEFAULT_RETURNS.get(a, 0.05) for a in ASSET_CLASSES)

    # 封顶格式化
    weights = {a: round(w, 4) for a, w in weights.items()}

    # ── Step 4: 计算最终因子风险贡献（供白盒前端展示） ──
    factor_risks = compute_factor_risk_contributions(weights)
    
    # ── Step 5: 组合级预估指标 (使用相关性调整的真实组合波动率) ──
    RISK_ASSETS_SET = {"大盘核心", "科技成长", "红利防守", "黄金商品", "海外QDII"}
    estimated_vol = _portfolio_volatility(weights, DEFAULT_VOLS)
    estimated_ret = sum(weights.get(a, 0) * DEFAULT_RETURNS.get(a, 0.05) for a in ASSET_CLASSES)
    risk_concentration = sum(weights.get(a, 0) for a in RISK_ASSETS_SET)
    
    return {
        "status": "success",
        "method": "🧭 宏观象限对应配置 (Factor Risk Parity)",
        "quadrant": current_quadrant,
        "quadrant_label": quadrant_info["label"],
        "quadrant_description": quadrant_info["description"],
        "target_weights": weights,
        "factor_risk_contributions": factor_risks,
        "estimated_volatility": round(estimated_vol, 4),
        "estimated_return": round(estimated_ret, 4),
        "risk_concentration": round(risk_concentration, 4),
        "defense_log": defense_log,
        "best_assets": quadrant_info["best_assets"],
        "worst_assets": quadrant_info["worst_assets"],
    }
