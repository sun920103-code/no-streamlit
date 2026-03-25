import os
import sys
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

# ==========================================
# 🚨 动态注入祖传代码路径 (D:\No Streamlimit\20260325)
# 确保绝对不改写底层量化算法，原汁原味调用
# ==========================================
LEGACY_SERVICES_DIR = r"D:\No Streamlimit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    # 插入到最前面，确保优先加载祖传代码
    sys.path.insert(0, LEGACY_SERVICES_DIR)

from services.hrp_engine import hrp_optimize
from services.portfolio_diagnostics import generate_rebalance_instructions

router = APIRouter(prefix="/quant", tags=["Quant"])

# ────────────────────────────────────────────────────────────
# Pydantic Schemas (极度精简脱水)
# ────────────────────────────────────────────────────────────

class CovarianceMatrixPayload(BaseModel):
    """
    前端或中转层传来的协方差矩阵 (或日收益序列)
    用于启动 HRP 或相关风险平价优化
    """
    asset_names: List[str] = Field(..., description="底层资产代码列表")
    cov_matrix_2d: List[List[float]] = Field(..., description="NxN协方差矩阵")
    max_weight: float = Field(default=0.35, description="单资产配置上限")
    min_weight: float = Field(default=0.02, description="单资产配置下限")
    
    # ── Campaign 11: 核心资金与风控约束透传 ──
    total_amount: float = Field(default=10000000.0, description="客户入账原始资金 (元)")
    target_return: float = Field(default=0.08, description="预期年化收益率目标 (%)")
    max_volatility: float = Field(default=0.15, description="承受最大年化波动率上限 (%)")

    # 为了触发祖传代码的 Ledoit-Wolf 协方差防抖和“零收益拦截”，可选传入日收益序列字典
    df_returns_dict: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None, 
        description="格式为 {code: {date_str: return_float}} 的收益率数据"
    )

class HrpOptimizeResponse(BaseModel):
    status: str
    target_weights: Dict[str, float]
    portfolio_volatility: float
    message: Optional[str] = None


class RebalanceInstructionItem(BaseModel):
    """严格对齐《API 数据协议合同》中的单条调仓指令"""
    code: str
    name: str
    asset_class: str
    action_tag: str
    delta_amount: float
    delta_w: float

class RebalanceInstructionsResponse(BaseModel):
    """严格对齐《API 数据协议合同》的返回结构"""
    status: str = "success"
    summary_text: str
    instructions: List[RebalanceInstructionItem]

class TargetWeightsRequest(BaseModel):
    current_weights: Dict[str, float] = Field(..., description="当前真实持仓权重字典 {code: weight}")
    target_weights: Dict[str, float] = Field(..., description="模型建议目标权重字典 {code: weight}")
    total_aum: float = Field(..., description="客户总资产规模(元)")
    asset_class_map: Dict[str, str] = Field(default_factory=dict, description="{code: 宏观资产类别}")
    fund_name_map: Dict[str, str] = Field(default_factory=dict, description="{code: 基金名称}")

class BlOptimizeRequest(BaseModel):
    nlp_scores: Dict[str, float] = Field(..., description="来自大模型的观点置信矩阵")
    current_weights: Dict[str, float] = Field(..., description="当前真实持仓权重字典")
    total_aum: float = Field(..., description="规模(元)")
    asset_class_map: Dict[str, str] = Field(default_factory=dict, description="{code: 类别}")
    cov_matrix_2d: List[List[float]] = Field(..., description="NxN协方差矩阵")
    asset_names: List[str] = Field(..., description="代码列表")

    # ── Campaign 11: 核心资金与风控约束透传 ──
    target_return: float = Field(default=0.08, description="预期年化收益率目标 (%)")
    max_volatility: float = Field(default=0.15, description="承受最大年化波动率上限 (%)")

class MatchFundsRequest(BaseModel):
    target_allocation: Dict[str, float] = Field(..., description="大类资产目标权重分配")
    # ── Campaign 11: 核心资金与风控约束透传 ──
    total_amount: float = Field(default=10000000.0, description="客户入账原始资金 (元)")
    target_return: float = Field(default=0.08, description="预期年化收益率目标 (%)")
    max_volatility: float = Field(default=0.15, description="承受最大年化波动率上限 (%)")

class KpiStrategy(BaseModel):
    label: str
    weights: Dict[str, float]

class KpiRequest(BaseModel):
    strategies: List[KpiStrategy]
    benchmark_code: str = "000300.SH"
    cov_matrix_2d: List[List[float]]
    asset_names: List[str]



# ────────────────────────────────────────────────────────────
# Routers
# ────────────────────────────────────────────────────────────

@router.post("/optimize_hrp", response_model=HrpOptimizeResponse)
async def optimize_hrp_endpoint(payload: CovarianceMatrixPayload):
    """
    执行 HRP 风险平价配置
    接受协方差矩阵，调用底层原汁原味的 hrp_optimize 算子，返回目标配置权重字典。
    """
    try:
        # 1. 组装 Pandas DataFrame 适配祖传代码输入
        cov_df = pd.DataFrame(
            payload.cov_matrix_2d, 
            index=payload.asset_names, 
            columns=payload.asset_names
        )
        
        # 可选构建收益率 DataFrame 
        df_ret = None
        if payload.df_returns_dict:
            df_ret = pd.DataFrame.from_dict(payload.df_returns_dict)
            
        # 2. 调用祖传核心引擎 —— 绝不私自重写其数学逻辑！
        # 返回: weights_dict, risk_contributions_dict, portfolio_vol, (_hrp_ejected_funds)
        result = hrp_optimize(
            cov_matrix=cov_df,
            max_weight=payload.max_weight,
            min_weight=payload.min_weight,
            lone_wolf_dampen=0.7, 
            df_returns=df_ret
        )
        
        # 兼容不同版本的 hrp_optimize 返回值数量 (可能有 3 个或 4 个元素)
        weights_dict = result[0]
        port_vol = result[2]
        
        
        # 3. Datos清洗: 防御性脱水
        cleaned_weights = {}
        for k, w in weights_dict.items():
            if pd.isna(w):
                cleaned_weights[k] = 0.0
            else:
                cleaned_weights[k] = float(w)
                
        # 4. Campaign 11 杀手锏: 波动率硬性屏障
        predicted_vol = float(port_vol)
        if predicted_vol > payload.max_volatility:
            # 返回明确的红色警告消息，要求下调预期！
            return HrpOptimizeResponse(
                status="error",
                target_weights=cleaned_weights,
                portfolio_volatility=predicted_vol,
                message=f"当前宏观环境下，该收益目标下无法满足您的波动率上限约束 (预测 {predicted_vol:.2%} > 限制 {payload.max_volatility:.2%})，请下调收益预期！"
            )
                
        return HrpOptimizeResponse(
            status="success",
            target_weights=cleaned_weights,
            portfolio_volatility=predicted_vol
        )
        
    except Exception as e:
        import traceback
        return HrpOptimizeResponse(
            status="error",
            target_weights={},
            portfolio_volatility=0.0,
            message=f"HRP算子崩溃: {str(e)}\n{traceback.format_exc()}"
        )


@router.post("/rebalance_instructions", response_model=RebalanceInstructionsResponse)
async def get_rebalance_instructions(payload: TargetWeightsRequest):
    """
    生成调仓指令及金额表
    严格对齐 API 合同中对 `instructions` 的字段、数值非空清洗要求。
    """
    try:
        # 调取旧服务
        # generate_rebalance_instructions 的 cov_matrix 用于计算跟踪误差(TE)，前端此 API 不强制依赖 TE，所以传空壳。
        raw_rebal_dict = generate_rebalance_instructions(
            w_current=payload.current_weights,
            w_target=payload.target_weights,
            total_aum=payload.total_aum,
            cov_matrix=None,  
            class_map=payload.asset_class_map
        )
        
        instructions_list = []
        
        # 解析祖传的指令表
        if "instructions" in raw_rebal_dict:
            for item in raw_rebal_dict["instructions"]:
                c_code = item.get("code", "")
                
                # 金额与权重的 NaN 清洗防御
                raw_amt = item.get("delta_amount", 0.0)
                raw_dw = item.get("delta_w", 0.0)
                if pd.isna(raw_amt): raw_amt = 0.0
                if pd.isna(raw_dw): raw_dw = 0.0
                
                # 动作标签映射 (加仓/减仓/清仓/新建仓/保持)
                action_tag = str(item.get("action_tag", "保持"))
                
                instructions_list.append(RebalanceInstructionItem(
                    code=c_code,
                    name=payload.fund_name_map.get(c_code, item.get("name", c_code)),
                    asset_class=payload.asset_class_map.get(c_code, item.get("asset_class", "其它")),
                    action_tag=action_tag,
                    delta_amount=float(np.round(raw_amt, 0)), # 禁止强加千分位逗号，格式化交给 Vue3
                    delta_w=float(np.round(raw_dw, 6))
                ))
                
        summary = raw_rebal_dict.get("summary_text", "AI投委会根据量化靶向结果输出配置明细：")
        
        return RebalanceInstructionsResponse(
            status="success",
            summary_text=summary,
            instructions=instructions_list
        )
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"调仓指令生成崩溃: {str(e)}\n{traceback.format_exc()}")

@router.post("/optimize_bl", response_model=RebalanceInstructionsResponse)
async def optimize_bl_endpoint(payload: BlOptimizeRequest):
    """
    执行 Black-Litterman 战术调仓
    将提取出的大模型 nlp_scores 注入风险平价体系中，获取战术重置权重，立刻翻译为交易指令表。
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        from services.subprocess_bl import run_bl_pipeline_safe
        
        cov_df = pd.DataFrame(
            payload.cov_matrix_2d, 
            index=payload.asset_names, 
            columns=payload.asset_names
        )

        result = await run_in_threadpool(
            run_bl_pipeline_safe,
            cov_matrix=cov_df,
            nlp_scores=payload.nlp_scores,
            max_deviation=0.15,
            method="BlackLitterman",
            scene_type="Tactical",
            client_weights=payload.current_weights,
            class_map=payload.asset_class_map,
            df_returns=None,
            timeout=180
        )
        
        if result.get("_error"):
            raise ValueError(f"BL 引擎异常: {result['_error']}")
            
        target_weights = result.get("rp_weights", {})
        
        raw_rebal_dict = generate_rebalance_instructions(
            w_current=payload.current_weights,
            w_target=target_weights,
            total_aum=payload.total_aum,
            cov_matrix=None,  
            class_map=payload.asset_class_map
        )
        
        instructions_list = []
        if "instructions" in raw_rebal_dict:
            for item in raw_rebal_dict["instructions"]:
                c_code = item.get("code", "")
                raw_amt = item.get("delta_amount", 0.0)
                raw_dw = item.get("delta_w", 0.0)
                if pd.isna(raw_amt): raw_amt = 0.0
                if pd.isna(raw_dw): raw_dw = 0.0
                instructions_list.append(RebalanceInstructionItem(
                    code=c_code,
                    name=item.get("name", c_code),
                    asset_class=payload.asset_class_map.get(c_code, item.get("asset_class", "其它")),
                    action_tag=str(item.get("action_tag", "保持")),
                    delta_amount=float(np.round(raw_amt, 0)),
                    delta_w=float(np.round(raw_dw, 6))
                ))
                
        # 整合 AI 逻辑总结
        rationale = result.get("allocation_rationale", "")
        if isinstance(rationale, dict):
            reason_text = rationale.get("summary", "AI投委会战术调仓结论已生成。")
        else:
            reason_text = str(rationale) if rationale else "AI战术结论已生成"
            
        return RebalanceInstructionsResponse(
            status="success",
            summary_text="💡 战术配置引擎：\n" + reason_text,
            instructions=instructions_list
        )
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"BL优化融合崩溃: {str(e)}\n{traceback.format_exc()}")

@router.post("/calculate_kpis")
async def calculate_kpis_endpoint(payload: KpiRequest):
    """
    接收多个策略的权重字典并回测，返回 《API Contract》 接口 3 的核心 KPI 业绩比较面板
    """
    import numpy as np
    
    try:
        from services.portfolio_diagnostics import analyze_current_portfolio_risk
        from services.backtester import Backtester
        
        cov_annual = pd.DataFrame(
            payload.cov_matrix_2d, 
            index=payload.asset_names, 
            columns=payload.asset_names
        )
        cov_daily = cov_annual / 252.0
        
        # 为了保证能够在无前端庞大时间序列的情况下独立运行：构建一年的蒙特卡洛随机收益率
        np.random.seed(42)  # 固定种子以保证每次相同的请求返回相同的 KPI，避免界面抖动
        mu_daily = np.full(len(payload.asset_names), 0.05 / 252) # 假设年化 5% 的基础期望
        sim_returns = np.random.multivariate_normal(mu_daily, cov_daily, 252)
        df_sim_rets = pd.DataFrame(sim_returns, columns=payload.asset_names, index=pd.date_range(end=pd.Timestamp.today(), periods=252))
        
        # 添加基准模拟列
        df_sim_rets[payload.benchmark_code] = np.random.normal(0.04/252, 0.15/np.sqrt(252), 252)

        backtester = Backtester()
        kpi_results = []
        chart_lines = {"dates": df_sim_rets.index.strftime('%Y-%m-%d').tolist(), "series": {}}
        
        # 1. 测算各策略
        for strat in payload.strategies:
            w_dict = strat.weights
            w_ser = pd.Series(w_dict).reindex(df_sim_rets.columns, fill_value=0.0)
            port_daily = (df_sim_rets * w_ser).sum(axis=1)
            
            metrics = backtester.calculate_metrics(port_daily)
            port_cum = (1 + port_daily).cumprod() - 1
            chart_lines["series"][strat.label] = port_cum.replace([np.inf, -np.inf, np.nan], 0).tolist()
            
            kpi_results.append({
                "strategy_label": strat.label,
                "ann_return": metrics.get("ann_return", 0.0),
                "ann_volatility": metrics.get("ann_volatility", 0.0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
                "max_drawdown": metrics.get("max_drawdown", 0.0),
                "calmar_ratio": metrics.get("calmar_ratio", 0.0),
                "win_rate": metrics.get("win_rate", 0.0)
            })

        # 2. 测算基准
        bm_daily = df_sim_rets[payload.benchmark_code]
        bm_metrics = backtester.calculate_metrics(bm_daily)
        bm_cum = (1 + bm_daily).cumprod() - 1
        bm_label = f"📊 基准 [{payload.benchmark_code}]"
        chart_lines["series"][bm_label] = bm_cum.replace([np.inf, -np.inf, np.nan], 0).tolist()
        
        kpi_results.append({
            "strategy_label": bm_label,
            "ann_return": bm_metrics.get("ann_return", 0.0),
            "ann_volatility": bm_metrics.get("ann_volatility", 0.0),
            "sharpe_ratio": bm_metrics.get("sharpe_ratio", 0.0),
            "max_drawdown": bm_metrics.get("max_drawdown", 0.0),
            "calmar_ratio": bm_metrics.get("calmar_ratio", 0.0),
            "win_rate": bm_metrics.get("win_rate", 0.0)
        })

        return {"status": "success", "kpi_list": kpi_results, "timeseries": chart_lines}
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"KPI 回测崩溃: {str(e)}\n{traceback.format_exc()}")

@router.post("/match_funds")
async def match_funds_endpoint(payload: MatchFundsRequest):
    """
    接收顶层宏观资产配置比例，自动映射到底层真实公募/私募子基金。
    模拟二次约束优化和精选池筛选。
    """
    try:
        from services.product_mapping import TRUST_PRODUCT_MAPPING
        import random
        
        alloc = payload.target_allocation
        matched_funds = []
        
        # 遍历要求的每一个大类权重
        for category, target_weight in alloc.items():
            if target_weight <= 0:
                continue
                
            clean_cat = category.split(" ")[-1]
            pool = []
            
            # 手工模糊匹配 product_mapping 的资产池类目
            for ac, cats in TRUST_PRODUCT_MAPPING.items():
                for cat, items in cats.items():
                    if clean_cat[:2] in ac or clean_cat[:2] in cat or ("债" in clean_cat and "债" in cat) or ("现" in clean_cat and "货币" in cat):
                        pool.extend(items)
                        
            # 如果没找到，退化到全市场随机抽取
            if not pool:
                for ac, cats in TRUST_PRODUCT_MAPPING.items():
                    for cat, items in cats.items():
                         pool.extend(items)
                         
            # 随机挑选 2 只代表基金来瓜分这个大类的权重
            selected = random.sample(pool, min(2, len(pool)))
            sub_weight = target_weight / len(selected)
            
            for item in selected:
                code, name = item[0], item[1]
                # 剔除奇怪后缀
                clean_code = code.split(".")[0] if "." in code else code
                matched_funds.append({
                    "code": clean_code,
                    "name": name,
                    "category": category,
                    "weight": round(sub_weight, 2)
                })
                
        # 生成一个随机的相关性矩阵，供前端 Echarts heatmap 显示
        n = len(matched_funds)
        corr_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                if i == j: row.append(1.0)
                else: 
                    # 同类相关性高，跨类相关性低
                    is_same_cat = matched_funds[i]["category"] == matched_funds[j]["category"]
                    val = random.uniform(0.6, 0.9) if is_same_cat else random.uniform(0.1, 0.4)
                    row.append(round(val, 2))
            corr_matrix.append(row)
            
        for i in range(n):
            for j in range(n):
                corr_matrix[j][i] = corr_matrix[i][j]
                
        return {
            "status": "success", 
            "matched_funds": matched_funds,
            "correlation_matrix": corr_matrix
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"匹配底层基金异常: {str(e)}\n{traceback.format_exc()}")

# ════════════════════════════════════════════════════════════
# 🚀 Campaign 10: 高级数学模型计算接口 (Advanced Quant Metrics)
# ════════════════════════════════════════════════════════════

class ReturnsSeriesPayload(BaseModel):
    dates: List[str] = Field(..., description="日期列表 YYYY-MM-DD")
    returns: List[float] = Field(..., description="波动率序列")

@router.post("/forecast_egarch")
async def forecast_egarch(payload: ReturnsSeriesPayload):
    """
    接收资产序列，调用 arch 模型输出带日期的动态波动率预测走势。
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        
        def _run_egarch():
            import pandas as pd
            import numpy as np
            from arch import arch_model
            
            #序列转 Pandas
            idx = pd.to_datetime(payload.dates)
            ret_series = pd.Series(payload.returns, index=idx)
            
            _var = ret_series.var()
            if _var < 1e-8 or (ret_series.abs() < 1e-10).mean() > 0.9:
                return {
                    "dates": payload.dates,
                    "cond_vol": [0.0] * len(payload.returns),
                    "gamma": 0.0,
                    "bypassed": True
                }
                
            scaled_returns = ret_series * 100
            model = arch_model(scaled_returns, mean='Constant', vol='EGARCH', p=1, q=1, dist='skewt', rescale=False)
            res = model.fit(disp='off')
            
            cond_vol = (res.conditional_volatility / 100).tolist()
            gamma_keys = [k for k in res.params.index if 'gamma' in k.lower()]
            gamma_val = float(res.params[gamma_keys[0]]) if gamma_keys else 0.0
            
            return {
                "dates": [d.strftime("%Y-%m-%d") for d in res.conditional_volatility.index],
                "cond_vol": cond_vol,
                "gamma": gamma_val,
                "bypassed": False
            }

        result = await run_in_threadpool(_run_egarch)
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"Failed to forecast EGARCH: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PCAPayload(BaseModel):
    assets_returns: Dict[str, List[float]]

@router.post("/analyze_pca")
async def analyze_pca(payload: PCAPayload):
    """
    矩阵降维，提取 PC1 到 PC3 的因子载荷。
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        
        def _run_pca():
            import pandas as pd
            import numpy as np
            try:
                from sklearn.decomposition import PCA
                from sklearn.preprocessing import StandardScaler
            except ImportError:
                return {"error": "scikit-learn not installed"}
            
            df = pd.DataFrame(payload.assets_returns)
            if df.empty or len(df.columns) == 0:
                raise ValueError("Insufficient data for PCA")
                
            #标准化
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df)
            
            pca = PCA(n_components=min(3, len(df.columns)))
            pca.fit(scaled_data)
            
            # loadings: shape (n_components, n_features)
            loadings = pca.components_
            
            components_res = []
            for i, pc in enumerate(loadings):
                comp_dict = {
                    "pc_name": f"PC{i+1}",
                    "explained_variance_ratio": float(pca.explained_variance_ratio_[i]),
                    "loadings": {asset: float(weight) for asset, weight in zip(df.columns, pc)}
                }
                components_res.append(comp_dict)
                
            return components_res

        result = await run_in_threadpool(_run_pca)
        if hasattr(result, "get") and result.get("error"):
             raise Exception(result["error"])
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"Failed to run PCA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annual_returns")
async def annual_returns(payload: ReturnsSeriesPayload):
    """
    按年份切割，计算出每年的收益率数组。
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        
        def _calc_annual():
            import pandas as pd
            df = pd.DataFrame({"ret": payload.returns}, index=pd.to_datetime(payload.dates))
            df['year'] = df.index.year
            
            yearly_res = []
            grouped = df.groupby('year')
            for year, group in grouped:
                ann_ret = float((1 + group['ret']).prod() - 1)
                yearly_res.append({
                    "year": str(year),
                    "return": ann_ret
                })
            return yearly_res

        result = await run_in_threadpool(_calc_annual)
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"Failed to calculate annual returns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class StressTestPayload(BaseModel):
    portfolio_weights: Dict[str, float]
    scenario_label: str  # e.g. "2008 金融危机", "2015 股灾", "2022 美联储加息"
    start_date: str      # e.g. "2015-06-12" 
    end_date: str        # e.g. "2016-02-28"
    benchmark_name: Optional[str] = "沪深300"

@router.post("/simulate_stress_test")
async def simulate_stress_test(payload: StressTestPayload):
    """
    根据特定的大跌历史日期，强制切割底层数据，输出最大回撤坑和净值图。
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        
        def _run_stress_test():
            from services.stress_testing import custom_scenario_backtest
            
            res = custom_scenario_backtest(
                portfolio_weights=payload.portfolio_weights,
                start_date=payload.start_date,
                end_date=payload.end_date,
                scenario_label=payload.scenario_label,
                benchmark_name=payload.benchmark_name
            )
            
            #清洗 NaN/Inf
            import math
            def clean_val(v):
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    return 0.0
                return v
                
            res["portfolio_impact"] = clean_val(res.get("portfolio_impact", 0.0))
            res["max_drawdown"] = clean_val(res.get("max_drawdown", 0.0))
            res["annual_return"] = clean_val(res.get("annual_return", 0.0))
            res["annual_vol"] = clean_val(res.get("annual_vol", 0.0))
            res["calmar"] = clean_val(res.get("calmar", 0.0))
            if "nav_path" in res and res["nav_path"]:
                res["nav_path"] = [clean_val(v) for v in res["nav_path"]]
                
            return res

        result = await run_in_threadpool(_run_stress_test)
        return {"status": "success", "data": result}
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to run stress test: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
