import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

try:
    from pypfopt import expected_returns, risk_models
    from pypfopt.efficient_frontier import EfficientCVaR
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False


def optimize_cvar(
    historical_returns: pd.DataFrame, 
    beta: float = 0.95,
    target_return: Optional[float] = None
) -> Dict[str, Any]:
    """
    使用 Conditional Value at Risk (CVaR / Expected Shortfall)进行由于厚尾风险的组合优化。
    :param historical_returns: 资产历史收益率序列 DataFrame，index为日期，columns为资产代码
    :param beta: CVaR 的分位数置信区间（如 0.95 或 0.99）
    :param target_return: 可选的目标收益限制，如果没有则直接最小化CVaR
    :return: 包含权重信息和预估CVaR的字典
    """
    if not PYPFOPT_AVAILABLE:
        raise ImportError("PyPortfolioOpt is required for CVaR optimization. Please install it.")

    # 计算历史预期收益 (几何平均或简单平均)
    mu = expected_returns.mean_historical_return(historical_returns, returns_data=True)
    
    # 初始化 Efficient CVaR 优化器
    # pyportfolioopt 的 EfficientCVaR 需要历史收益序列而不单是协方差矩阵
    ec = EfficientCVaR(mu, historical_returns, beta=beta)
    
    try:
        if target_return is not None:
            # 在满足目标收益的基础上，最小化 CVaR 风险
            ec.efficient_return(target_return)
        else:
            # 全面追求绝对抗风险能力，直接最小化 CVaR
            ec.min_cvar()
            
        weights = dict(ec.clean_weights())
        
        # 计算组合的 CVaR 等效值
        port_return, port_cvar = ec.portfolio_performance()
        
        return {
            "status": "success",
            "weights": {str(k): float(v) for k, v in weights.items() if float(v) > 0},
            "expected_return": float(port_return),
            "cvar": float(port_cvar),
            "beta": float(beta)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CVaR 优化过程失败: {str(e)}"
        }

def optimize_cvar_mock(beta: float=0.95) -> Dict[str, Any]:
    """提供给API层的 Mock 数据实现，防止因为缺少历史数据无法展示"""
    return {
        "status": "success",
        "weights": {
            "110011": 0.40,
            "000001": 0.35,
            "005918": 0.25
        },
        "expected_return": 0.082,
        "cvar": 0.045, # 95% 情况下极端月损失的平均
        "beta": beta,
        "method": "EfficientCVaR Opt"
    }
