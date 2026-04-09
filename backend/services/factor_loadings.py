"""
宏观因子载荷矩阵 (Factor Loadings Matrix)
==========================================
将祖传代码 bl_view_generator.py 中的专家校准矩阵移植到新 FastAPI 后端，
并新增四象限宏观体制映射。

核心设计:
  - 6 大宏观因子 × 8 大类资产的敏感度矩阵 (Factor Loadings)
  - 基于桥水全天候框架的四象限体制映射 (Macro Quadrant)
  - 体制条件下的因子乘数调控 (Regime Modifiers)
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional

# ────────────────────────────────────────────────────────────
# 6 大宏观因子定义 (与祖传 multi_agent.py MACRO_FACTORS_6 完全对齐)
# ────────────────────────────────────────────────────────────
MACRO_FACTORS = [
    "经济增长",       # growth_factor
    "通胀商品",       # inflation_factor
    "利率环境",       # rate_factor
    "信用扩张",       # credit_factor
    "海外环境",       # overseas_factor
    "市场情绪",       # sentiment_factor
]

# ────────────────────────────────────────────────────────────
# 8 大类资产定义 (与祖传 product_mapping.py ASSET_CLASSES_8 对齐)
# ────────────────────────────────────────────────────────────
ASSET_CLASSES = [
    "大盘核心", "科技成长", "红利防守",
    "纯债固收", "混合债券", "短债理财",
    "黄金商品", "海外QDII",
]

# ────────────────────────────────────────────────────────────
# 🔒 专家校准因子载荷矩阵 v2.0
# (移植自 bl_view_generator.py FACTOR_SENSITIVITY_MATRIX_DEFAULT)
#
# 行 (Index): 6 个宏观因子
# 列 (Columns): 8 个大类资产
# 值域: [-1.0, 1.0]
# ────────────────────────────────────────────────────────────
FACTOR_LOADINGS = pd.DataFrame(
    {
        #                    经济增长  通胀商品  利率环境  信用扩张  海外环境  市场情绪
        "大盘核心": [0.80, 0.10, 0.50, 0.50, 0.20, 0.60],
        "科技成长": [0.60, -0.10, 0.70, 0.40, 0.30, 0.80],
        "红利防守": [0.15, 0.20, 0.20, 0.30, 0.10, 0.20],
        "纯债固收": [-0.40, -0.30, 0.80, -0.30, 0.10, -0.30],
        "混合债券": [-0.10, -0.20, 0.60, 0.80, 0.05, -0.10],
        "短债理财": [-0.05, -0.10, 0.30, 0.10, 0.00, -0.05],
        "黄金商品": [-0.05, 0.80, 0.30, 0.10, 0.30, 0.00],
        "海外QDII": [0.30, -0.10, 0.20, 0.00, 0.80, 0.40],
    },
    index=MACRO_FACTORS,
)


# ════════════════════════════════════════════════════════════
# 桥水全天候四象限体制 (All Weather Macro Quadrants)
# ════════════════════════════════════════════════════════════

QUADRANT_DEFINITIONS = {
    "recovery": {
        "label": "复苏期",
        "description": "经济增长上升 + 通胀下降 (最利好股票和信用债)",
        "growth": "rising",
        "inflation": "falling",
        "best_assets": ["大盘核心", "科技成长", "混合债券"],
        "worst_assets": ["黄金商品"],
        "factor_modifiers": {
            "经济增长": 1.3,
            "通胀商品": 0.6,
            "利率环境": 1.1,
            "信用扩张": 1.2,
            "海外环境": 1.0,
            "市场情绪": 1.2,
        },
    },
    "overheat": {
        "label": "景气高位期",
        "description": "经济增长上升 + 通胀上升（利好大宗商品，关注估值风险）",
        "growth": "rising",
        "inflation": "rising",
        "best_assets": ["黄金商品"],
        "worst_assets": ["纯债固收", "科技成长"],
        "factor_modifiers": {
            "经济增长": 0.8,
            "通胀商品": 1.5,
            "利率环境": 0.5,    # 加息预期打压利率敏感型
            "信用扩张": 0.7,
            "海外环境": 0.9,
            "市场情绪": 0.6,    # 景气高位期情绪失灵
        },
    },
    "stagflation": {
        "label": "谨慎观望期",
        "description": "经济增长放缓 + 通胀偏高（优选抗通胀资产，均衡防守）",
        "growth": "falling",
        "inflation": "rising",
        "best_assets": ["黄金商品", "短债理财"],
        "worst_assets": ["大盘核心", "科技成长", "纯债固收"],
        "factor_modifiers": {
            "经济增长": 0.4,
            "通胀商品": 1.4,
            "利率环境": 0.3,
            "信用扩张": 0.4,
            "海外环境": 0.6,
            "市场情绪": 0.3,
        },
    },
    "deflation": {
        "label": "等待复苏期",
        "description": "经济增长放缓 + 通胀回落（利好债券配置，权益谨慎）",
        "growth": "falling",
        "inflation": "falling",
        "best_assets": ["纯债固收", "短债理财"],
        "worst_assets": ["大盘核心", "科技成长", "黄金商品"],
        "factor_modifiers": {
            "经济增长": 0.4,
            "通胀商品": 0.5,
            "利率环境": 1.5,   # 央行降息利好债券
            "信用扩张": 0.6,
            "海外环境": 0.7,
            "市场情绪": 0.4,
        },
    },
}


def determine_quadrant(factor_scores: Dict[str, float]) -> str:
    """
    根据宏观因子得分判断当前所处的桥水四象限。
    
    :param factor_scores: {"经济增长": 0.6, "通胀商品": -0.3, ...}
    :return: quadrant key — "recovery", "overheat", "stagflation", "deflation"
    """
    growth = factor_scores.get("经济增长", 0.0)
    inflation = factor_scores.get("通胀商品", 0.0)

    if growth >= 0 and inflation < 0:
        return "recovery"
    elif growth >= 0 and inflation >= 0:
        return "overheat"
    elif growth < 0 and inflation >= 0:
        return "stagflation"
    else:
        return "deflation"


def get_regime_modifiers(quadrant: str) -> Dict[str, float]:
    """获取指定象限的因子乘数调控向量"""
    regime = QUADRANT_DEFINITIONS.get(quadrant, QUADRANT_DEFINITIONS["recovery"])
    return regime["factor_modifiers"]


def factor_scores_to_asset_expected_returns(
    factor_scores: Dict[str, float],
    apply_regime: bool = True,
) -> Dict[str, float]:
    """
    核心传导函数：宏观因子得分 → 大类资产预期收益率
    
    数学: Expected_Returns = Factor_Scores × Factor_Loadings × Regime_Modifiers
    
    :param factor_scores: AI 委员会输出的 6 因子得分 (range: [-1, 1])
    :param apply_regime: 是否自动识别象限并施加调控乘数
    :return: 8 大类资产的标准化预期收益信号 (tanh 归一化至 [-1, 1])
    """
    # Step 1: 构建因子得分向量
    factor_vector = np.array([
        float(factor_scores.get(f, 0.0)) for f in MACRO_FACTORS
    ])
    
    # Step 2: 如果开启象限调控，施加体制乘数
    matrix = FACTOR_LOADINGS.copy()
    quadrant = None
    if apply_regime:
        quadrant = determine_quadrant(factor_scores)
        modifiers = get_regime_modifiers(quadrant)
        modifier_vector = np.array([modifiers.get(f, 1.0) for f in MACRO_FACTORS])
        # 按行广播
        for i in range(len(MACRO_FACTORS)):
            matrix.iloc[i, :] = matrix.iloc[i, :] * modifier_vector[i]
    
    # Step 3: 矩阵乘法 (1×6) @ (6×8) = (1×8)
    raw_scores = factor_vector @ matrix.values
    
    # Step 4: tanh 归一化
    normalized = np.tanh(raw_scores)
    
    result = {
        asset: round(float(score), 4)
        for asset, score in zip(ASSET_CLASSES, normalized)
    }
    
    return result
