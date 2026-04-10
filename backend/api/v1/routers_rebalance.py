"""
routers_rebalance.py — 一键配置调仓 SSE 编排端点
=================================================
将 3 步调仓管线 (宏观象限 → 新闻资讯 → 研报MOE) 串行编排，
通过 SSE 实时推送进度日志，最终返回聚合结果。
"""

import os
import sys
import json
import asyncio
import traceback
import tempfile
from typing import Dict, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.append(LEGACY_SERVICES_DIR)

router = APIRouter(prefix="/rebalance", tags=["一键配置调仓"])

# 标准化 6 因子键名 (防止映射断裂)
MACRO_FACTORS_6 = ["经济增长", "通胀商品", "利率环境", "信用扩张", "海外环境", "市场情绪"]


def _normalize_factor_keys(raw: dict) -> dict:
    """确保因子键名统一为中文 6 因子, 防止映射断裂。"""
    _EN_TO_CN = {
        "growth_factor": "经济增长", "inflation_factor": "通胀商品",
        "rate_factor": "利率环境", "credit_factor": "信用扩张",
        "overseas_factor": "海外环境", "sentiment_factor": "市场情绪",
    }
    result = {}
    for k, v in raw.items():
        cn_key = _EN_TO_CN.get(k, k)
        if cn_key in MACRO_FACTORS_6:
            try:
                result[cn_key] = float(v) if not isinstance(v, dict) else float(v.get("score", 0))
            except (ValueError, TypeError):
                result[cn_key] = 0.0
    # 补全缺失因子
    for f in MACRO_FACTORS_6:
        if f not in result:
            result[f] = 0.0
    return result


# ── 8 大资产类别常量 (与 legacy sensitivity matrix 列对齐) ──
ASSET_CLASSES_8 = ["大盘核心", "科技成长", "红利防守", "纯债固收", "混合债券", "短债理财", "黄金商品", "海外QDII"]


def _load_client_meta() -> Optional[pd.DataFrame]:
    """从 backend/data/ 加载最新的 sync_*_meta.csv (基金元数据)。"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    if not os.path.exists(data_dir):
        return None
    metas = [f for f in os.listdir(data_dir) if f.startswith("sync_") and f.endswith("_meta.csv")]
    if not metas:
        return None
    metas.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
    path = os.path.join(data_dir, metas[0])
    try:
        df = pd.read_csv(path, index_col=0, encoding="utf-8-sig", dtype=str)
        df.columns = [c.upper() for c in df.columns]
        df.index = [str(idx).split(".")[0].zfill(6) for idx in df.index]
        logger.info(f"[Rebalance] 加载基金元数据: {path} ({len(df)} 只)")
        return df
    except Exception as e:
        logger.error(f"[Rebalance] 元数据加载失败: {e}")
        return None


def _build_class_map(bare_codes: list) -> dict:
    """
    构建 {fund_code: asset_class} 映射。
    使用 meta CSV 中的 SEC_NAME + FUND_INVESTTYPE 关键字启发式匹配,
    与 legacy portfolio_diagnostics.map_client_funds_to_factors 逻辑一致。
    """
    meta_df = _load_client_meta()
    class_map = {}
    for code in bare_codes:
        name = ""
        inv_type = ""
        if meta_df is not None and code in meta_df.index:
            row = meta_df.loc[code]
            name = str(row.get("SEC_NAME", ""))
            inv_type = str(row.get("FUND_INVESTTYPE", ""))
        cmb = f"{name} {inv_type}".lower()

        if 'qdii' in cmb or '海外' in cmb or '全球' in cmb or '标普' in cmb or '纳斯达克' in cmb or '恒生' in cmb or '纳指' in cmb:
            ac = "海外QDII"
        elif '黄金' in cmb or '大宗商品' in cmb or '豆粕' in cmb or '能源' in cmb or '商品型' in cmb or '有色' in cmb or '白银' in cmb:
            ac = "黄金商品"
        elif '纯债' in cmb or '利率债' in cmb or '国债' in cmb or '政金债' in cmb or '中长期纯债' in cmb:
            ac = "纯债固收"
        elif '货币' in cmb or '理财' in cmb or '短债' in cmb:
            ac = "短债理财"
        elif '信用' in cmb or '企业债' in cmb or '公司债' in cmb or '可转债' in cmb or '产业债' in cmb or '一级基金' in cmb:
            ac = "混合债券"
        elif '偏债' in cmb or '二级债' in cmb or '短期纯债' in cmb:
            ac = "混合债券"
        elif '红利' in cmb or '低波' in cmb or '高股息' in cmb:
            ac = "红利防守"
        elif '科创' in cmb or '创业板' in cmb or '中证1000' in cmb or '科技' in cmb:
            ac = "科技成长"
        elif '股票' in cmb or '偏股' in cmb or '灵活配置' in cmb or '沪深' in cmb or '中证' in cmb or '混合型' in cmb or '指数型' in cmb or '被动' in cmb or '白酒' in cmb or '医药' in cmb or '新能源' in cmb or '军工' in cmb or '银行' in cmb:
            ac = "大盘核心"
        elif '偏债混合' in cmb:
            ac = "混合债券"
        elif '灵活配置' in cmb or '混合' in cmb:
            ac = "大盘核心"
        else:
            ac = "大盘核心"
        class_map[code] = ac
    logger.info(f"[Rebalance] class_map 构建完成: {len(class_map)} 只 → {dict(pd.Series(list(class_map.values())).value_counts())}")
    return class_map


PROXY_MAPPING = {
    "海外QDII": ["大盘核心", "科技成长"],
    "科技成长": ["大盘核心", "红利防守"],
    "黄金商品": ["纯债固收", "短债理财"], # 视作避险替代
    "大盘核心": ["红利防守", "科技成长"],
    "红利防守": ["大盘核心", "纯债固收"],
    "混合债券": ["纯债固收", "大盘核心"],
    "纯债固收": ["短债理财", "混合债券"],
    "短债理财": ["纯债固收", "混合债券"]
}

def _fold_views(views: dict, class_map: dict) -> dict:
    """
    当宏观/新闻引擎产生了针对某资产类别(如'海外QDII')的看多/看空观点，
    但客户的持仓池 (class_map) 中压根没有这份额资产时，
    把该观点平移/降维折叠 (Fold) 给持仓里的第一替补资产。
    这样避免因子信号因为「目标资产缺失」而被白白抛弃。
    """
    available_classes = set(class_map.values())
    folded_views = {}
    
    for asset_class, score in views.items():
        if abs(score) < 0.001:
            continue
            
        if asset_class in available_classes:
            folded_views[asset_class] = folded_views.get(asset_class, 0.0) + score
        else:
            # 在池中无法映射！进行寻找替补的遍历
            found_proxy = False
            proxies = PROXY_MAPPING.get(asset_class, ["大盘核心"])
            for proxy in proxies:
                if proxy in available_classes:
                    # 将观点折叠传递，施加一点损耗系数 (0.8) 代表不完全匹配
                    logger.info(f"🔄 [观点折叠] 目标资产 [{asset_class}] 不在持仓中, 信号 {score} 已折叠转移给 [{proxy}]")
                    folded_views[proxy] = folded_views.get(proxy, 0.0) + score * 0.8
                    found_proxy = True
                    break
                    
            if not found_proxy:
                # 实在找不到替补 (比如持仓全空)，强行给大盘核心 (若存在)
                if "大盘核心" in available_classes:
                    logger.info(f"🔄 [观点折叠] 目标资产 [{asset_class}] 找不到精准替补, 强制降维给 [大盘核心]")
                    folded_views["大盘核心"] = folded_views.get("大盘核心", 0.0) + score * 0.5
                else:
                    logger.warning(f"⚠️ [观点折叠] 目标资产 [{asset_class}] 无法找到任何可承接的资产! 信号流失。")
    
    return folded_views

def _asset_views_to_fund_weights(
    asset_views: dict,
    bare_codes: list,
    class_map: dict,
    amplifier: float = 1.5,
    base_weights: dict = None,
) -> dict:
    """
    将资产类别级得分通过 class_map 广播到基金级权重。
    逻辑:
      1. asset_views = {asset_class: score}  (score ∈ [-1, 1])
      2. 每只基金获得其所属 asset_class 的 score
      3. 将 score 转为年化超额预期 view = score * 0.15
      4. 基线权重 (original_weights 或等权) + view * confidence * amplifier → 目标权重
      5. 归一化到 sum=1
    """
    n = max(len(bare_codes), 1)
    raw = {}
    for code in bare_codes:
        # ✅ 基于原始持仓做偏离 (而非等权)
        base_w = base_weights.get(code, 1.0 / n) if base_weights else 1.0 / n
        ac = class_map.get(code, "大盘核心")
        score = asset_views.get(ac, 0.0)
        view = score * 0.15
        confidence = min(0.90, 0.5 + abs(score) * 0.35)
        offset = view * confidence * amplifier
        raw[code] = max(0.001, base_w + offset)
    total = sum(raw.values())
    if total > 1e-8:
        return {k: v / total for k, v in raw.items()}
    return {c: (base_weights.get(c, 1.0/n) if base_weights else 1.0/n) for c in bare_codes}


def _compute_kpi_from_nav(weights: dict, nav_df: pd.DataFrame) -> dict:
    """
    从历史 NAV DataFrame 计算 KPI (年化收益/波动/最大回撤/夏普/卡玛)。
    weights: {fund_code: weight}
    nav_df: index=date, columns=fund_codes, values=NAV
    """
    # 对齐: 只保留有 NAV 数据的基金
    common_codes = [c for c in weights if c in nav_df.columns]
    if not common_codes:
        return {"ann_return": 0, "ann_vol": 0, "max_dd": 0, "sharpe": 0, "calmar": 0}

    w_arr = np.array([weights.get(c, 0) for c in common_codes])
    w_sum = w_arr.sum()
    if w_sum > 0:
        w_arr = w_arr / w_sum  # 归一化

    nav_sub = nav_df[common_codes].dropna(how="all").ffill().dropna()
    if len(nav_sub) < 20:
        return {"ann_return": 0, "ann_vol": 0, "max_dd": 0, "sharpe": 0, "calmar": 0}

    # 日收益率
    rets = nav_sub.pct_change().dropna()
    port_ret = (rets * w_arr).sum(axis=1)

    ann_return = float(port_ret.mean() * 252)
    ann_vol = float(port_ret.std() * np.sqrt(252))

    # 最大回撤 (3 年)
    cum = (1 + port_ret).cumprod()
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = float(drawdown.min())

    sharpe = ann_return / ann_vol if ann_vol > 1e-8 else 0
    calmar = ann_return / abs(max_dd) if abs(max_dd) > 1e-8 else 0

    return {
        "ann_return": round(ann_return, 4),
        "ann_vol": round(ann_vol, 4),
        "max_dd": round(max_dd, 4),
        "sharpe": round(sharpe, 2),
        "calmar": round(calmar, 2),
    }


def _load_client_nav() -> Optional[pd.DataFrame]:
    """从 backend/data/ 加载最近的客户持仓 NAV 数据。"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    # 找最近的 sync_*.csv
    if not os.path.exists(data_dir):
        return None
    csvs = [f for f in os.listdir(data_dir) if f.startswith("sync_") and f.endswith(".csv") and "_meta" not in f]
    if not csvs:
        return None
    # 取最新的
    csvs.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
    path = os.path.join(data_dir, csvs[0])
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df = df[df.index.notnull()]
        # 列名统一去掉后缀 .OF 等
        df.columns = [c.split(".")[0].zfill(6) for c in df.columns]
        logger.info(f"[Rebalance] 加载客户 NAV: {path} ({len(df)} 天 × {len(df.columns)} 基金)")
        return df
    except Exception as e:
        logger.error(f"[Rebalance] NAV 加载失败: {e}")
        return None


def _load_client_holdings() -> Optional[dict]:
    """从 backend/data/ 加载最近的客户持仓信息 (fund_summary)。"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    summary_path = os.path.join(data_dir, "client_fund_summary.json")
    if not os.path.exists(summary_path):
        return None
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[Rebalance] 持仓摘要加载失败: {e}")
        return None


@router.post("/run_full_pipeline")
async def run_full_pipeline(
    files: Optional[List[UploadFile]] = File(None),
    portfolio_codes_json: str = Form(default="[]"),
    total_amount: float = Form(default=10000000.0),
):
    """
    一键配置调仓 SSE 端点。

    三步串行:
      Step 1: EDB → 宏观象限 → 因子映射 → 基金调仓
      Step 2: Tavily 新闻 → LLM 因子提取 → 基金调仓
      Step 3: (可选) 研报 → MOE 投委会 → 基金调仓

    最后并行计算 KPI + 表格 + 雷达数据, 一次性推送结果。
    """
    # 预读取上传的研报文件
    uploaded_reports = []
    if files:
        for f in files:
            if f.filename and f.filename.strip():
                content = await f.read()
                if content and len(content) > 10:
                    uploaded_reports.append((f.filename, content))

    # 解析持仓代码
    try:
        portfolio_codes = json.loads(portfolio_codes_json)
    except Exception:
        portfolio_codes = []

    async def sse_generator():
        q = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _emit(msg_type: str, **kwargs):
            payload = {"type": msg_type, **kwargs}
            loop.call_soon_threadsafe(q.put_nowait, payload)

        def _log(msg: str):
            _emit("log", content=msg)

        def worker():
            try:
                result = _run_pipeline_sync(
                    portfolio_codes=portfolio_codes,
                    total_amount=total_amount,
                    uploaded_reports=uploaded_reports,
                    log_fn=_log,
                )
                _emit("finish", result=result)
            except Exception as e:
                logger.error(f"[Rebalance] 管线异常: {traceback.format_exc()}")
                _emit("error", content=str(e))

        # 后台线程
        asyncio.create_task(run_in_threadpool(worker))

        # 心跳 + 消费
        heartbeat_interval = 10  # 秒
        last_heartbeat = asyncio.get_event_loop().time()

        while True:
            try:
                item = await asyncio.wait_for(q.get(), timeout=heartbeat_interval)
                yield f"data: {json.dumps(item, ensure_ascii=False, default=str)}\n\n"
                if item["type"] in ("finish", "error"):
                    break
            except asyncio.TimeoutError:
                # 心跳
                yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


def _run_pipeline_sync(
    portfolio_codes: list,
    total_amount: float,
    uploaded_reports: list,
    log_fn,
):
    """同步执行三步调仓管线 (在后台线程中运行)。"""

    from services.bl_view_generator import (
        macro_factor_to_asset_views,
        parse_weekly_report_pdf,
    )

    # ── 持仓代码标准化 ──
    if not portfolio_codes:
        holdings = _load_client_holdings()
        if holdings:
            portfolio_codes = list(holdings.keys())
            log_fn(f"📂 自动加载持仓: {len(portfolio_codes)} 只基金")
        else:
            log_fn("⚠️ 未找到持仓数据，请先在诊断页面上传持仓 CSV")
            return {"error": "no_holdings"}

    bare_codes = [c.split(".")[0].zfill(6) for c in portfolio_codes]
    log_fn(f"📋 持仓基金: {len(bare_codes)} 只")

    # ── 构建 class_map (fund_code → asset_class) ──
    class_map = _build_class_map(bare_codes)
    _cm_summary = {}
    for c, ac in class_map.items():
        _cm_summary[ac] = _cm_summary.get(ac, 0) + 1
    log_fn(f"🗂️ 基金归类: {_cm_summary}")

    # ── 加载基金元数据 (名称) ──
    meta_df = _load_client_meta()
    fund_names = {}
    if meta_df is not None:
        for code in bare_codes:
            if code in meta_df.index:
                fund_names[code] = str(meta_df.loc[code].get("SEC_NAME", code))
            else:
                fund_names[code] = code
    else:
        fund_names = {c: c for c in bare_codes}

    # 加载 NAV
    nav_df = _load_client_nav()
    original_kpi = {}
    original_weights = {c: 1.0 / len(bare_codes) for c in bare_codes}
    if nav_df is not None:
        original_kpi = _compute_kpi_from_nav(original_weights, nav_df)
        log_fn(f"📊 原始持仓 KPI 已计算 (Sharpe={original_kpi.get('sharpe', 0):.2f})")

    # ═══════════════════════════════════════════
    # Step 1: EDB → 宏观象限 → 因子调仓
    # ═══════════════════════════════════════════
    log_fn("🚀 Step 1/3: EDB 宏观数据下载 + 宏观象限定位...")

    step1_factors = {}
    step1_quadrant = {}
    step1_asset_views = {}
    step1_weights = {}

    try:
        from services.markov_engine import get_current_macro_regime_live
        import math

        log_fn("📡 正在调用 Tushare 实盘数据测算宏观环境...")
        hmm_result = get_current_macro_regime_live()
        
        zscores = hmm_result.get("latest_zscores", {})
        z_pmi = zscores.get("PMI", 0.0)
        z_cpi = zscores.get("CPI_YoY", 0.0)
        z_credit = zscores.get("Credit_Impulse", 0.0)
        
        log_fn(f"✅ Tushare 数据测算完成 (Z-Scores PMI: {z_pmi:.2f}, CPI: {z_cpi:.2f})")

        # 将 Z-Score 映射到 [-1.0, 1.0] 的因子观点击分
        # 用 tanh 让极端值平滑收敛
        step1_factors = {
            "经济增长": round(math.tanh(z_pmi / 2.0), 3),
            "通胀商品": round(math.tanh(z_cpi / 2.0), 3),
            "信用扩张": round(math.tanh(z_credit / 2.0), 3),
            "利率环境": round(math.tanh(-z_credit / 2.0), 3), # 信用扩张时利率通常向下
            "海外环境": round(math.tanh(-zscores.get("US10Y", 0.0) / 2.0), 3),
            "市场情绪": round(math.tanh(z_pmi / 3.0), 3), # 经济好时情绪通常偏好
        }
        step1_factors = _normalize_factor_keys(step1_factors)

        # 象限定位 (直出)
        _q_label = hmm_result.get("current_regime", "recovery")
        _q_desc_map = {
            "overheat": "经济扩张+通胀上行，偏向商品/短久期",
            "recovery": "经济扩张+通胀温和，利好权益/信用",
            "stagflation": "经济放缓+通胀偏高，均衡防守为主",
            "deflation": "经济放缓+通胀回落，利好债券/防御"
        }
        _q_label_cn = {
            "overheat": "景气高位期",
            "recovery": "复苏期",
            "stagflation": "谨慎观望期",
            "deflation": "等待复苏期"
        }.get(_q_label, "复苏期")
        
        step1_quadrant = {"quadrant": _q_label_cn, "label": _q_label_cn, "description": _q_desc_map.get(_q_label, "")}
        log_fn(f"🧭 宏观象限探测: {_q_label_cn}")

        # 因子 → 资产类别级得分 (矩阵乘法)
        step1_asset_views = macro_factor_to_asset_views(step1_factors)
        step1_asset_views = _fold_views(step1_asset_views, class_map)
        
        # 资产类别得分 → 基金级权重 (以原持仓为基准偏移)
        step1_weights = _asset_views_to_fund_weights(
            step1_asset_views, 
            bare_codes, 
            class_map, 
            amplifier=1.5, 
            base_weights=original_weights
        )

        log_fn("✅ Step 1 完成: 宏观象限调仓就绪")
    except Exception as e:
        logger.error(f"[Step 1] 异常: {traceback.format_exc()}")
        log_fn(f"⚠️ Step 1 异常 (降级跳过): {str(e)[:100]}")
        step1_weights = dict(original_weights)

    # ═══════════════════════════════════════════
    # Step 2: 新闻资讯 → LLM → 因子调仓
    # ═══════════════════════════════════════════
    log_fn("📰 Step 2/3: Tavily 搜索 + AI 新闻因子提取...")

    step2_factors = {}
    step2_asset_views = {}
    step2_weights = {}
    step2_news_digest = ""

    try:
        from services.news_factor_extractor import extract_factors_with_cache

        log_fn("🔍 正在搜索最新市场新闻...")
        news_result = extract_factors_with_cache(model_choice="DeepSeek-Chat")

        if news_result and "factors" in news_result:
            step2_factors = _normalize_factor_keys(news_result["factors"])
            step2_news_digest = news_result.get("headlines_digest", "")
            log_fn(f"✅ 新闻因子提取完成: {step2_news_digest[:50]}...")

            step2_asset_views = macro_factor_to_asset_views(step2_factors)
            step2_asset_views = _fold_views(step2_asset_views, class_map)
            
            # --- BL Optimizer (传入 class_map 脱离 Streamlit 依赖) ---
            from services.bl_fusion import black_litterman_fusion
            
            # 准备协方差矩阵
            if nav_df is not None and not nav_df.empty:
                cov_matrix = nav_df.pct_change().dropna().cov()
            else:
                n_assets = len(bare_codes)
                cov_matrix = pd.DataFrame(
                    np.eye(n_assets) * (0.15 / np.sqrt(252))**2, 
                    index=bare_codes, columns=bare_codes
                )
            
            # 格式化符合 BL 函数要求的观点字典
            views_for_bl = {
                ac: {"view": val, "confidence": 0.8} 
                for ac, val in step2_asset_views.items()
            }
            
            bl_weights, _ = black_litterman_fusion(
                rp_weights=original_weights,      # ✅ 基于原始持仓, 避免叠加 step1 的偏移导致超调
                cov_matrix=cov_matrix,
                views=views_for_bl,
                df_returns=nav_df,
                orig_volatility=original_kpi.get('ann_vol', 0.0),  # ✅ 修正 key: ann_vol
                deviation_base=original_weights,
                fund_class_map=class_map,
            )
            step2_weights = bl_weights

            log_fn("✅ Step 2 完成: 新闻资讯调仓就绪 (Black-Litterman 优化)")
        else:
            log_fn("⚠️ 新闻因子提取无结果, 使用中性观点")
            step2_factors = {f: 0.0 for f in MACRO_FACTORS_6}
            step2_weights = dict(original_weights)
    except Exception as e:
        logger.error(f"[Step 2] 异常: {traceback.format_exc()}")
        log_fn(f"⚠️ Step 2 异常 (降级跳过): {str(e)[:100]}")
        step2_factors = {f: 0.0 for f in MACRO_FACTORS_6}
        step2_weights = dict(original_weights)

    # ═══════════════════════════════════════════
    # Step 3: 研报 → MOE 投委会 (可选)
    # ═══════════════════════════════════════════
    step3_factors = {}
    step3_asset_views = {}
    step3_weights = {}
    step3_debate_logs = []
    step3_moe_report = ""
    has_report = len(uploaded_reports) > 0

    if has_report:
        log_fn(f"📄 Step 3/3: {len(uploaded_reports)} 份研报 → AI MOE 投委会审议...")
        try:
            from services.multi_agent import run_investment_committee

            report_texts = []
            report_names = []
            for fname, content in uploaded_reports:
                ext = os.path.splitext(fname)[1].lower()
                if ext == ".pdf":
                    text = parse_weekly_report_pdf(content)
                else:
                    text = content.decode("utf-8", errors="ignore")
                if text and len(text.strip()) > 50:
                    report_texts.append(text)
                    report_names.append(fname)

            if report_texts:
                log_fn(f"📑 已解析 {len(report_texts)} 份研报, 启动 MOE 投委会...")

                def _moe_status(msg):
                    log_fn(f"  🤖 {msg}")

                md_report, bl_views, debate_logs = run_investment_committee(
                    report_text=report_texts[0],
                    model_choice="MiniMax",
                    status_callback=_moe_status,
                    report_texts_list=report_texts if len(report_texts) > 1 else None,
                    report_names_list=report_names if len(report_names) > 1 else None,
                )

                step3_moe_report = md_report
                step3_debate_logs = debate_logs

                if bl_views:
                    # ✅ 直接使用 MOE 投委会输出的 bl_views 作为 BL 观点
                    # bl_views 格式: {asset_class: {"view": float, "confidence": float}}
                    log_fn(f"📊 MOE 观点: {list(bl_views.keys())}")
                    
                    # 同时尝试构建因子得分 (供雷达图使用)
                    step3_factors = {f: 0.0 for f in MACRO_FACTORS_6}
                    try:
                        import services.multi_agent as _ma_mod
                        _moe_meta = getattr(_ma_mod, '_last_moe_metadata', None) or {}
                        logger.info(f"[Step 3 Radar Debug] _moe_meta keys: {list(_moe_meta.keys())}")
                        if "factor_scores" in _moe_meta:
                            _fs = _moe_meta["factor_scores"]
                            logger.info(f"[Step 3 Radar Debug] factor_scores from MOE: {_fs}")
                            for f in MACRO_FACTORS_6:
                                step3_factors[f] = _fs.get(f, 0.0)
                        else:
                            # fallback: 从 sensitivity_modifiers 反推
                            _modifiers = _moe_meta.get("sensitivity_modifiers", {})
                            logger.info(f"[Step 3 Radar Debug] No factor_scores, using sensitivity_modifiers: {_modifiers}")
                            for f in MACRO_FACTORS_6:
                                mod_val = _modifiers.get(f, 1.0)
                                step3_factors[f] = round((mod_val - 1.0) * 2.0, 3)
                    except Exception as e_fs:
                        logger.warning(f"[Step 3 Radar Debug] factor_scores extraction failed: {e_fs}")
                    
                    logger.info(f"[Step 3 Radar] step3_factors BEFORE normalize: {step3_factors}")
                    step3_factors = _normalize_factor_keys(step3_factors)
                    logger.info(f"[Step 3 Radar] step3_factors AFTER normalize: {step3_factors}")
                    log_fn(f"📊 研报因子雷达: {step3_factors}")

                    # 用 bl_views 构建资产类别级得分 (供调仓理由生成)
                    step3_asset_views = {}
                    for ac, vdata in bl_views.items():
                        if isinstance(vdata, dict):
                            step3_asset_views[ac] = vdata.get("view", 0.0)
                        else:
                            step3_asset_views[ac] = float(vdata) if vdata else 0.0
                    
                    # --- BL Optimizer (直接使用 MOE bl_views) ---
                    from services.bl_fusion import black_litterman_fusion
                    
                    if nav_df is not None and not nav_df.empty:
                        cov_matrix = nav_df.pct_change().dropna().cov()
                    else:
                        n_assets = len(bare_codes)
                        cov_matrix = pd.DataFrame(
                            np.eye(n_assets) * (0.15 / np.sqrt(252))**2, 
                            index=bare_codes, columns=bare_codes
                        )
                    
                    # ✅ 使用折叠后的 step3_asset_views 重建 views_for_bl
                    step3_asset_views = _fold_views(step3_asset_views, class_map)
                    views_for_bl = {}
                    for ac, val in step3_asset_views.items():
                        views_for_bl[ac] = {"view": val, "confidence": 0.8}
                    bl_weights, _ = black_litterman_fusion(
                        rp_weights=original_weights,       # ✅ 基于原始持仓
                        cov_matrix=cov_matrix,
                        views=views_for_bl,
                        df_returns=nav_df,
                        orig_volatility=original_kpi.get('ann_vol', 0.0),  # ✅ 修正 key
                        deviation_base=original_weights,
                        fund_class_map=class_map,
                    )
                    step3_weights = bl_weights

                log_fn("✅ Step 3 完成: 研报 MOE 调仓就绪")
            else:
                log_fn("⚠️ 研报解析无有效文本, 跳过 Step 3")
                has_report = False
        except Exception as e:
            logger.error(f"[Step 3] 异常: {traceback.format_exc()}")
            log_fn(f"⚠️ Step 3 异常 (降级跳过): {str(e)[:100]}")
            has_report = False
    else:
        log_fn("ℹ️ 未上传研报, 跳过 Step 3 (MOE 投委会)")

    if not has_report:
        step3_weights = dict(original_weights)

    # ═══════════════════════════════════════════
    # 并行输出: KPI + 表格 + 雷达 + 资产观点 + EGARCH + PCA
    # ═══════════════════════════════════════════
    log_fn("📊 正在计算 KPI 看板 + 调仓表格 + 图表数据...")

    # KPI 回测
    step1_kpi = _compute_kpi_from_nav(step1_weights, nav_df) if nav_df is not None else {}
    step2_kpi = _compute_kpi_from_nav(step2_weights, nav_df) if nav_df is not None else {}
    step3_kpi = _compute_kpi_from_nav(step3_weights, nav_df) if nav_df is not None and has_report else {}

    kpi_dashboard = [
        {"label": "原持仓", **original_kpi},
        {"label": "宏观象限调仓", **step1_kpi},
        {"label": "新闻资讯调仓", **step2_kpi},
    ]
    if has_report:
        kpi_dashboard.append({"label": "研报调仓", **step3_kpi})

    # ── 调仓明细表 (per-fund deltas with reasons) ──
    def _build_rebalance_table(new_weights, asset_views_dict, step_name):
        table = []
        for code in bare_codes:
            old_w = original_weights.get(code, 0)
            new_w = new_weights.get(code, old_w)
            delta_w = new_w - old_w
            delta_amount = delta_w * total_amount
            ac = class_map.get(code, "大盘核心")
            score = asset_views_dict.get(ac, 0.0)

            # 构建 ≤15 字调仓理由
            if abs(delta_w) < 0.005:
                reason = "观点中性，维持原仓"
            elif score > 0.1:
                reason = f"{ac}看多，增配"
            elif score < -0.1:
                reason = f"{ac}偏空，减配"
            elif delta_w > 0:
                reason = f"{ac}温和看多"
            else:
                reason = f"{ac}温和看空"

            table.append({
                "code": code,
                "name": fund_names.get(code, code),
                "asset_class": ac,
                "old_weight": round(old_w * 100, 2),
                "new_weight": round(new_w * 100, 2),
                "delta_weight": round(delta_w * 100, 2),
                "delta_amount": round(delta_amount, 0),
                "reason": reason,
            })
        # 按偏离幅度降序
        table.sort(key=lambda x: -abs(x["delta_weight"]))
        return table

    step1_table = _build_rebalance_table(step1_weights, step1_asset_views, "宏观象限")
    step2_table = _build_rebalance_table(step2_weights, step2_asset_views, "新闻资讯")
    step3_table = _build_rebalance_table(step3_weights, step3_asset_views, "研报") if has_report else []

    # ── 雷达图数据 ──
    def _build_radar_data(factors):
        return {
            "indicators": [{"name": f, "max": 1.0, "min": -1.0} for f in MACRO_FACTORS_6],
            "values": [round(factors.get(f, 0), 3) for f in MACRO_FACTORS_6],
        }

    radar_data = {
        "macro": _build_radar_data(step1_factors),
        "news": _build_radar_data(step2_factors),
    }
    if has_report:
        radar_data["report"] = _build_radar_data(step3_factors)

    # ── 大类资产观点 (超配/维持/低配) ──
    def _build_asset_view_table(asset_views_dict):
        items = []
        for ac in ASSET_CLASSES_8:
            score = asset_views_dict.get(ac, 0.0)
            if score > 0.1:
                direction = "超配"
                color = "red"
            elif score < -0.1:
                direction = "低配"
                color = "blue"
            else:
                direction = "维持"
                color = "gray"
            items.append({"asset": ac, "score": round(score, 4), "direction": direction, "color": color})
        return items

    asset_views_data = {
        "macro": _build_asset_view_table(step1_asset_views),
        "news": _build_asset_view_table(step2_asset_views),
    }
    if has_report:
        asset_views_data["report"] = _build_asset_view_table(step3_asset_views)

    # ── EGARCH 条件波动率计算 ──
    egarch_data = {}
    if nav_df is not None and len(nav_df) > 30:
        try:
            log_fn("📈 正在计算 EGARCH 条件波动率...")
            all_weight_sets = [
                ("baseline", "持仓底仓", original_weights),
                ("macro", "宏观调仓", step1_weights),
                ("news", "资讯调仓", step2_weights),
            ]
            if has_report:
                all_weight_sets.append(("report", "研报调仓", step3_weights))

            for key, label, w_dict in all_weight_sets:
                try:
                    common = [c for c in w_dict if c in nav_df.columns]
                    if not common or len(nav_df) < 30:
                        continue
                    w_arr = np.array([w_dict.get(c, 0) for c in common])
                    w_sum = w_arr.sum()
                    if w_sum > 0:
                        w_arr = w_arr / w_sum
                    rets = nav_df[common].pct_change().dropna()
                    port_ret = (rets * w_arr).sum(axis=1)

                    # EGARCH 拟合
                    from arch import arch_model
                    scaled = port_ret * 100
                    if scaled.var() < 1e-8:
                        egarch_data[key] = {"label": label, "bypassed": True, "reason": "波动率不足"}
                        continue

                    model = arch_model(scaled, mean='Constant', vol='EGARCH', p=1, o=1, q=1, dist='skewt', rescale=False)
                    res = model.fit(disp='off')
                    cond_vol = res.conditional_volatility / 100
                    # Filter out NaT values from index to prevent NaTType strftime error
                    cond_vol = cond_vol[cond_vol.index.notna()].dropna()
                    
                    gamma_keys = [k for k in res.params.index if 'gamma' in k.lower()]
                    gamma_val = float(res.params[gamma_keys[0]]) if gamma_keys else 0.0

                    egarch_data[key] = {
                        "label": label,
                        "bypassed": False,
                        "dates": [d.strftime("%Y-%m-%d") for d in cond_vol.index],
                        "values": [round(float(v), 6) for v in cond_vol.values],
                        "mean_vol": round(float(cond_vol.mean()), 6),
                        "gamma": round(gamma_val, 4),
                        "asymmetry": "负面冲击放大" if gamma_val < -0.03 else "冲击基本对称",
                    }
                except Exception as e_eg:
                    import traceback
                    egarch_data[key] = {"label": label, "bypassed": True, "reason": str(e_eg)[:60]}
                    log_fn(f"EGARCH Detail Error: {traceback.format_exc()}")
            log_fn(f"✅ EGARCH 计算完成 ({len(egarch_data)} 个配置)")
        except Exception as e_all:
            log_fn(f"⚠️ EGARCH 计算异常: {str(e_all)[:60]}")

    # ── PCA 风险温度计 ──
    pca_data = {}
    if nav_df is not None and len(nav_df) > 30:
        try:
            log_fn("🌡️ 正在计算 PCA 风险温度计...")
            from sklearn.decomposition import PCA
            rets = nav_df.pct_change().dropna()

            all_weight_sets_pca = [
                ("baseline", "持仓底仓", original_weights),
                ("macro", "宏观调仓", step1_weights),
                ("news", "资讯调仓", step2_weights),
            ]
            if has_report:
                all_weight_sets_pca.append(("report", "研报调仓", step3_weights))

            for key, label, w_dict in all_weight_sets_pca:
                try:
                    common = [c for c in w_dict if c in rets.columns]
                    if len(common) < 2:
                        continue
                    X = rets[common].values
                    # 加权标准化
                    w_arr = np.array([w_dict.get(c, 1.0 / len(common)) for c in common])
                    w_arr = w_arr / w_arr.sum()
                    X_weighted = X * np.sqrt(w_arr)
                    # 去除零方差列
                    valid_mask = X_weighted.std(axis=0) > 1e-10
                    X_clean = X_weighted[:, valid_mask]
                    if X_clean.shape[1] < 2:
                        continue
                    pca = PCA(n_components=1)
                    pca.fit(X_clean)
                    pc1_ratio = float(pca.explained_variance_ratio_[0]) * 100

                    if pc1_ratio < 40:
                        level, color, text = "green", "#10B981", "分散良好"
                    elif pc1_ratio < 60:
                        level, color, text = "yellow", "#F59E0B", "中度集中"
                    else:
                        level, color, text = "red", "#EF4444", "高度同质化"

                    pca_data[key] = {
                        "label": label,
                        "pc1_ratio": round(pc1_ratio, 1),
                        "level": level,
                        "color": color,
                        "text": text,
                        "loadings": [round(float(v), 4) for v in pca.components_[0][:min(len(common), 10)]],
                        "fund_names": [fund_names.get(c, c) for c in common[:10]],
                    }
                except Exception as e_pca:
                    logger.warning(f"[PCA] {key} 异常: {e_pca}")
            log_fn(f"✅ PCA 计算完成 ({len(pca_data)} 个配置)")
        except Exception as e_all:
            log_fn(f"⚠️ PCA 计算异常: {str(e_all)[:60]}")

    log_fn("✅ 全部调仓计算完成!")

    return {
        "kpi_dashboard": kpi_dashboard,
        "tables": {
            "macro": step1_table,
            "news": step2_table,
            "report": step3_table,
        },
        "radar": radar_data,
        "asset_views": asset_views_data,
        "egarch": egarch_data,
        "pca": pca_data,
        "quadrant": step1_quadrant,
        "news_digest": step2_news_digest,
        "has_report": has_report,
        "debate_logs": step3_debate_logs if has_report else [],
        "moe_report": step3_moe_report if has_report else "",
        "factor_scores": {
            "macro": step1_factors,
            "news": step2_factors,
            "report": step3_factors if has_report else {},
        },
        "class_map": class_map,
    }

