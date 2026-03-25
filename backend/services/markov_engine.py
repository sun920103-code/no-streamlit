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
