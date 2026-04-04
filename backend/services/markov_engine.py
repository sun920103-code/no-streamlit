import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from typing import Dict, Any, List

class MarkovMacroEngine:
    """
    基于高斯隐马尔可夫模型 (Gaussian HMM) 的宏观经济/货币周期识别算子
    利用多维宏观指标序列(如 PMI, CPI, M2) 识别隐含的宏观状态，判断当前所处周期。
    """
    def __init__(self, n_components: int = 4, random_state: int = 42):
        self.n_components = n_components
        self.model = GaussianHMM(
            n_components=self.n_components,
            covariance_type="full",
            n_iter=1000,
            tol=1e-4,
            random_state=random_state
        )
        self.is_fitted = False
        self.feature_names = []

    def fit(self, df: pd.DataFrame) -> None:
        """
        训练马尔可夫模型
        :param df: 时间序列 DataFrame，列为宏观指标 (如 ['PMI', 'CPI', 'M2_Growth'])
        """
        self.feature_names = df.columns.tolist()
        data_matrix = df.values
        
        # 处理可能的缺失值或无穷值
        data_matrix = np.nan_to_num(data_matrix)
        
        self.model.fit(data_matrix)
        self.is_fitted = True

    def predict_current_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        预测最新的宏观状态及其概率分布
        """
        if not self.is_fitted:
            self.fit(df)

        data_matrix = df.values
        data_matrix = np.nan_to_num(data_matrix)
        
        # 得到最新的状态序列预测
        hidden_states = self.model.predict(data_matrix)
        current_state = hidden_states[-1]
        
        # 获取状态预测的平滑概率 (后验概率)
        probs = self.model.predict_proba(data_matrix)
        current_probs = probs[-1]

        # 计算各个维度的状态均值并进行排序，尝试进行周期语义的打标 (可选)
        # 这里为了简化，直接将状态 0,1,2... 映射。
        # 实际业务中，可以根据 PMI 均值最高映射为“过热”或“复苏”
        means = self.model.means_
        
        regime_labels = {
            state: f"Regime_{state}" for state in range(self.n_components)
        }
        
        # 将各维度的特征的均值带上标签
        state_features = {}
        for state in range(self.n_components):
            state_features[f"Regime_{state}"] = {
                feat: float(means[state][i]) for i, feat in enumerate(self.feature_names)
            }

        return {
            "current_regime": regime_labels[current_state],
            "current_state_id": int(current_state),
            "confidence": float(current_probs[current_state]),
            "state_probabilities": {
                regime_labels[i]: float(current_probs[i]) for i in range(self.n_components)
            },
            "transition_matrix": self.model.transmat_.tolist(),
            "state_characteristics": state_features
        }

def get_current_macro_regime_mock() -> Dict[str, Any]:
    """快捷的 Mock 测试调用，模拟 HMM 计算过程返回当前周期"""
    engine = MarkovMacroEngine(n_components=4)
    # Mock data
    dates = pd.date_range(end=pd.Timestamp.today(), periods=100, freq='M')
    mock_df = pd.DataFrame({
        "PMI": np.random.normal(50, 2, 100),
        "CPI_YoY": np.random.normal(2.0, 0.5, 100),
        "M2_Growth": np.random.normal(8.0, 1.0, 100),
        "Credit_Impulse": np.random.normal(0.5, 1.5, 100)
    }, index=dates)
    
    # 注入趋势模拟状态切换
    mock_df.iloc[-10:, 0] += 3  # PMI 上升
    mock_df.iloc[-10:, 1] += 1  # CPI 上升
    
    return engine.predict_current_regime(mock_df)

def get_current_macro_regime_live() -> Dict[str, Any]:
    """
    实盘调用的宏观体制识别引擎：
    1. 通过 tushare_fetcher 拉取真实宏观经济序列 (10年/120个月)
    2. 计算真实的滚动 Z-score 以消除绝对数值差异
    3. 调用 HMM 隐马尔可夫模型进行训练和推断
    """
    import sys
    import os
    
    # 动态载入 tushare_fetcher
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        
    try:
        from tushare_fetcher import fetch_macro_economic_indicators
    except ImportError as e:
        print(f"导入 tushare_fetcher 失败: {e}，回退使用 mock")
        return get_current_macro_regime_mock()
        
    # 拉取 120 个月 (10年) 数据
    df_macro = fetch_macro_economic_indicators(limit=120)
    
    if df_macro is None or df_macro.empty:
        print("Tushare 宏观数据为空，回退使用 mock")
        return get_current_macro_regime_mock()
        
    # 前向后向填充缺失值
    df_macro.ffill(inplace=True)
    df_macro.bfill(inplace=True)
    
    # 执行 Z-Score 规范化：使用过去均值和标准差 (即标准化时序)
    # 确保列包含: PMI, CPI_YoY, M2_Growth, Credit_Impulse
    required_cols = ['PMI', 'CPI_YoY', 'M2_Growth', 'Credit_Impulse']
    for col in required_cols:
        if col not in df_macro.columns:
            df_macro[col] = 0.0
            
    df_zscore = df_macro.copy()
    
    # 获取最新的绝对指标值，用于返回展示
    latest_absolute_values = {col: float(df_macro[col].iloc[-1]) for col in required_cols}
    latest_zscores = {}
    
    import warnings
    # 忽略计算标准差时的 RuntimeWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for col in required_cols:
            mean_val = df_macro[col].mean()
            std_val = df_macro[col].std()
            if std_val > 1e-6:
                df_zscore[col] = (df_macro[col] - mean_val) / std_val
            else:
                df_zscore[col] = 0.0
            latest_zscores[col] = float(df_zscore[col].iloc[-1])
            
    # 只使用这四根因子的 Z-Score 来喂给 HMM 引擎
    engine = MarkovMacroEngine(n_components=4)
    # HMM 会根据 4 维空间自动无监督聚类
    result = engine.predict_current_regime(df_zscore[required_cols])
    
    # 进行四象限业务语义打标 (简化的启发式映射)
    # 根据这一类别的平均 PMI 和 CPI 来推测
    state_id = result["current_state_id"]
    state_char = result["state_characteristics"][f"Regime_{state_id}"]
    
    z_pmi = state_char.get("PMI", 0.0)
    z_cpi = state_char.get("CPI_YoY", 0.0)
    
    if z_pmi >= 0 and z_cpi < 0:
        bussiness_regime = "recovery"
    elif z_pmi >= 0 and z_cpi >= 0:
        bussiness_regime = "overheat"
    elif z_pmi < 0 and z_cpi >= 0:
        bussiness_regime = "stagflation"
    else:
        bussiness_regime = "deflation"
        
    result["current_regime"] = bussiness_regime
    result["latest_zscores"] = latest_zscores
    result["latest_absolute_values"] = latest_absolute_values
    
    return result

