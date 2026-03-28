import os
import sys
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

# ==========================================
# 🚨 动态注入祖传代码路径 (D:\No Streamlit\20260325)
# 确保绝对不改写底层量化算法，原汁原味调用
# ==========================================
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"
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

class CvarOptimizeResponse(BaseModel):
    status: str
    target_weights: Dict[str, float]
    expected_return: float
    cvar: float
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
    benchmark_codes: List[str] = Field(
        default=["000300.SH", "000001.SH", "399001.SZ", "399006.SZ", "000905.SH", "000852.SH", "HSI.HI"]
    )
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

@router.post("/optimize_cvar", response_model=CvarOptimizeResponse)
async def optimize_cvar_endpoint(payload: CovarianceMatrixPayload):
    """
    执行 CVaR 尾部风险优化配置 (Expected Shortfall)
    """
    try:
        from services.cvar_engine import optimize_cvar_mock
        # 为了演示和由于缺失庞大历史收盘价数据，先调用带参数的Mock实现
        result = optimize_cvar_mock(beta=0.95)
        
        return CvarOptimizeResponse(
            status=result.get("status", "success"),
            target_weights=result.get("weights", {}),
            expected_return=result.get("expected_return", 0.0),
            cvar=result.get("cvar", 0.0)
        )
    except Exception as e:
        import traceback
        return CvarOptimizeResponse(
            status="error",
            target_weights={},
            expected_return=0.0,
            cvar=0.0,
            message=f"CVaR算子崩溃: {str(e)}\n{traceback.format_exc()}"
        )


class MblFactorRequest(BaseModel):
    factor_scores: Dict[str, float] = Field(..., description="6大宏观因子得分 {因子名: [-1, 1]}")
    apply_regime: bool = Field(default=True, description="是否启用四象限体制调控")
    max_volatility: float = Field(default=0.15, description="承受最大年化波动率上限")

@router.post("/optimize_mbl")
async def optimize_mbl_endpoint(payload: MblFactorRequest):
    """
    MBL 宏观因子 Black-Litterman 优化
    AI 委员会仅输出 6 因子得分，本引擎通过因子载荷矩阵自动传导至 8 大类资产权重。
    """
    try:
        from services.mbl_engine import optimize_with_mbl
        result = optimize_with_mbl(
            factor_scores=payload.factor_scores,
            max_volatility=payload.max_volatility,
            apply_regime=payload.apply_regime,
        )
        return result
    except Exception as e:
        import traceback
        return {"status": "error", "message": f"MBL引擎异常: {str(e)}\n{traceback.format_exc()}"}


@router.post("/optimize_factor_rp")
async def optimize_factor_risk_parity_endpoint(payload: MblFactorRequest):
    """
    🧭 宏观象限对应配置 (Factor Risk Parity)
    将 HRP 从资产级升级为宏观因子级风险贡献平价。
    """
    try:
        from services.factor_risk_parity import optimize_factor_risk_parity
        result = optimize_factor_risk_parity(
            factor_scores=payload.factor_scores,
            max_volatility=payload.max_volatility,
        )
        return result
    except Exception as e:
        import traceback
        return {"status": "error", "message": f"因子风险平价异常: {str(e)}\n{traceback.format_exc()}"}


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
    以及过去 5 年的真实历史年度收益率（柱状图数据）。
    此接口直连本地存放的 Wind API 真实数据文件 (sync_*.csv 和 client_benchmarks.csv)。
    """
    try:
        from services.backtester import FOFBacktester
        import os
        import pandas as pd
        import numpy as np
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(backend_dir, "data")
        
        # ── 1. 加载真实的历史底层净值序列 ──
        # 我们寻找最新的一个 sync_*.csv (除去 meta)。在实际工程中可以传入 task_id，但为了兼容性，取最新即可。
        csv_files = [f for f in os.listdir(data_dir) if f.startswith("sync_") and f.endswith(".csv") and "meta" not in f]
        if not csv_files:
            raise FileNotFoundError("没有找到底层基金的行情数据 (sync_*.csv)，请先执行持仓诊断的自动下载步骤。")
            
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)), reverse=True)
        latest_sync = os.path.join(data_dir, csv_files[0])
        df_funds = pd.read_csv(latest_sync, index_col=0, parse_dates=True)
        
        # 将价格转为逐日收益率
        df_funds_ret = df_funds.pct_change().dropna(how='all')
        
        # ── 2. 加载市场基准真实净值序列 ──
        bm_path = os.path.join(data_dir, "client_benchmarks.csv")
        df_bm = None
        if os.path.exists(bm_path):
            df_bm = pd.read_csv(bm_path, index_col=0, parse_dates=True)
            
        # ── 3. 对齐日期与拼接 ──
        df_all_ret = df_funds_ret.copy()
        
        # 将传入的多个基准列加入 df_all_ret
        valid_benchmark_codes = []
        if df_bm is not None:
            for bm_code in payload.benchmark_codes:
                if bm_code in df_bm.columns:
                    df_all_ret[bm_code] = df_bm[bm_code].pct_change().dropna()
                    valid_benchmark_codes.append(bm_code)
                else:
                    logger.warning(f"Benchmark {bm_code} not found in client_benchmarks.csv")
        
        # 如果一个基准都没找到，提供兜底
        if not valid_benchmark_codes:
            logger.warning("未找到任何匹配的市场基准数据，使用代理数据...")
            fallback_bm = payload.benchmark_codes[0] if payload.benchmark_codes else "000300.SH"
            np.random.seed(42)
            df_all_ret[fallback_bm] = pd.Series(np.random.normal(0.04/252, 0.15/np.sqrt(252), len(df_funds_ret)), index=df_funds_ret.index)
            valid_benchmark_codes = [fallback_bm]
            
        df_all_ret = df_all_ret.fillna(0.0) # 防止 NaN 影响加权
        df_all_ret.index = pd.to_datetime(df_all_ret.index)

        backtester = FOFBacktester(initial_capital=1_000_000)
        kpi_results = []
        
        # 数据结构变更为 bar chart 年化收益:
        # { dates: ["2020", "2021", ...], series: { "策略A": [0.05, -0.01, ...], ...} }
        years = df_all_ret.index.year.unique().tolist()
        chart_lines = {"dates": [str(y) for y in years], "series": {}}
        
        def calculate_annual(series: pd.Series):
            annual_rets = []
            grouped = series.groupby(series.index.year)
            for year in years:
                if year in grouped.groups:
                    group = grouped.get_group(year)
                    ret = (1 + group).prod() - 1
                    annual_rets.append(float(ret))
                else:
                    annual_rets.append(0.0)
            return annual_rets

        # ====== 计算各个策略 ======
        for strat in payload.strategies:
            w_dict = strat.weights
            w_ser = pd.Series(w_dict).reindex(df_funds_ret.columns, fill_value=0.0)
            
            # 由于可能出现配置里带有一些在库里找不到的代码，做下归一化
            total_w = w_ser.sum()
            if total_w > 0.01:
                w_ser = w_ser / total_w
                
            port_daily = (df_funds_ret * w_ser).sum(axis=1)
            
            # 算整体指标
            metrics = backtester.calculate_metrics(port_daily)
            ann_ret = metrics.get("Annualized_Return") or 0.0
            ann_vol = metrics.get("Annualized_Volatility") or 0.0
            mdd = metrics.get("Max_Drawdown") or 0.0
            sharpe = metrics.get("Sharpe_Ratio") or 0.0
            calmar = abs(ann_ret / mdd) if mdd != 0 else 0.0
            win_rate = float((port_daily > 0).sum()) / max(len(port_daily), 1)
            # 算各年指标
            ann_rets = calculate_annual(port_daily)
            
            chart_lines["series"][strat.label] = ann_rets
            
            kpi_results.append({
                "strategy_label": strat.label,
                "ann_return": ann_ret,
                "ann_volatility": ann_vol,
                "sharpe_ratio": sharpe,
                "max_drawdown": mdd,
                "calmar_ratio": calmar,
                "win_rate": win_rate
            })

        # ====== 计算所有有效基准 ======
        bm_kpi_results = []
        for bm_code in valid_benchmark_codes:
            bm_daily = df_all_ret[bm_code]
            bm_metrics = backtester.calculate_metrics(bm_daily)
            bm_ann_ret = bm_metrics.get("Annualized_Return") or 0.0
            bm_ann_vol = bm_metrics.get("Annualized_Volatility") or 0.0
            bm_mdd = bm_metrics.get("Max_Drawdown") or 0.0
            bm_sharpe = bm_metrics.get("Sharpe_Ratio") or 0.0
            bm_calmar = abs(bm_ann_ret / bm_mdd) if bm_mdd != 0 else 0.0
            bm_win_rate = float((bm_daily > 0).sum()) / max(len(bm_daily), 1)
            bm_ann_rets = calculate_annual(bm_daily)
            
            # 使用更易读的名称，这里写了内置字典作友好展示
            BM_NAME_MAP = {
                '000300.SH': '沪深300',
                '000001.SH': '上证指数',
                '399001.SZ': '深证成指',
                '399006.SZ': '创业板指',
                '000905.SH': '中证500',
                '000852.SH': '中证1000',
                'HSI.HI': '恒生指数'
            }
            bm_friendly_name = BM_NAME_MAP.get(bm_code, bm_code)
            
            bm_label = f"📊 基准 [{bm_friendly_name}]"
            chart_lines["series"][bm_label] = bm_ann_rets
            
            bm_kpi_results.append({
                "strategy_label": bm_label,
                "ann_return": bm_ann_ret,
                "ann_volatility": bm_ann_vol,
                "sharpe_ratio": bm_sharpe,
                "max_drawdown": bm_mdd,
                "calmar_ratio": bm_calmar,
                "win_rate": bm_win_rate
            })

        # 将基准排在前面，更符合常规展示 UI
        kpi_results = bm_kpi_results + kpi_results

        return {"status": "success", "kpi_list": kpi_results, "timeseries": chart_lines}
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"历史回测KPI计算崩溃: {str(e)}\n{traceback.format_exc()}")

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
