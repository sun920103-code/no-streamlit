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
    sys.path.insert(0, LEGACY_SERVICES_DIR)

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
            if f.filename and f.size and f.size > 0:
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
        factor_scores_to_fund_views,
        ASSET_CLASSES_7,
        parse_weekly_report_pdf,
    )

    # ── 持仓代码标准化 ──
    if not portfolio_codes:
        # 从 backend/data 自动读取
        holdings = _load_client_holdings()
        if holdings:
            portfolio_codes = list(holdings.keys())
            log_fn(f"📂 自动加载持仓: {len(portfolio_codes)} 只基金")
        else:
            log_fn("⚠️ 未找到持仓数据，请先在诊断页面上传持仓 CSV")
            return {"error": "no_holdings"}

    bare_codes = [c.split(".")[0].zfill(6) for c in portfolio_codes]
    log_fn(f"📋 持仓基金: {len(bare_codes)} 只")

    # 加载 NAV
    nav_df = _load_client_nav()
    original_kpi = {}
    if nav_df is not None:
        # 原始持仓等权
        original_weights = {c: 1.0 / len(bare_codes) for c in bare_codes}
        original_kpi = _compute_kpi_from_nav(original_weights, nav_df)
        log_fn(f"📊 原始持仓 KPI 已计算 (Sharpe={original_kpi.get('sharpe', 0):.2f})")

    # ═══════════════════════════════════════════
    # Step 1: EDB → 宏观象限 → 因子调仓
    # ═══════════════════════════════════════════
    log_fn("🚀 Step 1/3: EDB 宏观数据下载 + 宏观象限定位...")

    step1_factors = {}
    step1_quadrant = {}
    step1_fund_views = {}
    step1_weights = {}

    try:
        from services.macro_data_collector import (
            fetch_macro_factors, fetch_valuation_factors,
            fetch_risk_momentum_factors, calculate_derived_factors,
            calculate_factor_scores,
        )
        from services.factor_loadings import determine_quadrant, QUADRANT_DEFINITIONS

        log_fn("📡 正在检索 EDB 宏观数据...")
        macro_data = fetch_macro_factors()
        val_data = fetch_valuation_factors()
        risk_data = fetch_risk_momentum_factors()
        derived = calculate_derived_factors(macro_data, val_data)
        scores = calculate_factor_scores(macro_data, val_data, risk_data, derived)

        log_fn(f"✅ EDB 数据下载完成 (市场状态: {scores.get('market_state', 'N/A')})")

        # 从 EDB 综合得分推导 6 因子得分
        # EDB composite_score → 6 因子一阶近似
        _composite = scores.get("composite_score", 0.5)
        _macro_t = scores.get("macro_total", 0)
        _val_t = scores.get("valuation_total", 0)
        _risk_t = scores.get("risk_total", 0)

        step1_factors = {
            "经济增长": round(float(_macro_t * 2), 3),
            "通胀商品": round(float(-_val_t * 1.5), 3),  # 高估值 → 通胀负
            "利率环境": round(float(_macro_t * 1.2), 3),
            "信用扩张": round(float((_composite - 0.5) * 2), 3),
            "海外环境": 0.0,
            "市场情绪": round(float((_composite - 0.5) * 3), 3),
        }
        step1_factors = _normalize_factor_keys(step1_factors)

        # 象限定位
        current_q = determine_quadrant(step1_factors)
        q_info = QUADRANT_DEFINITIONS[current_q]
        step1_quadrant = {
            "quadrant": current_q,
            "label": q_info["label"],
            "description": q_info["description"],
            "best_assets": q_info.get("best_assets", []),
            "worst_assets": q_info.get("worst_assets", []),
        }
        log_fn(f"🧭 宏观象限: {q_info['label']}")

        # 因子 → 大类资产 → 基金级映射
        asset_views = macro_factor_to_asset_views(step1_factors)
        step1_fund_views = factor_scores_to_fund_views(step1_factors, bare_codes)

        # 将基金级 view 转为权重
        step1_weights = _views_to_weights(step1_fund_views, bare_codes)

        log_fn("✅ Step 1 完成: 宏观象限调仓就绪")
    except Exception as e:
        logger.error(f"[Step 1] 异常: {traceback.format_exc()}")
        log_fn(f"⚠️ Step 1 异常 (降级跳过): {str(e)[:100]}")

    # ═══════════════════════════════════════════
    # Step 2: 新闻资讯 → LLM → 因子调仓
    # ═══════════════════════════════════════════
    log_fn("📰 Step 2/3: Tavily 搜索 + AI 新闻因子提取...")

    step2_factors = {}
    step2_fund_views = {}
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

            step2_fund_views = factor_scores_to_fund_views(step2_factors, bare_codes)
            step2_weights = _views_to_weights(step2_fund_views, bare_codes)

            log_fn("✅ Step 2 完成: 新闻资讯调仓就绪")
        else:
            log_fn("⚠️ 新闻因子提取无结果, 使用中性观点")
            step2_factors = {f: 0.0 for f in MACRO_FACTORS_6}
            step2_weights = {c: 1.0 / len(bare_codes) for c in bare_codes}
    except Exception as e:
        logger.error(f"[Step 2] 异常: {traceback.format_exc()}")
        log_fn(f"⚠️ Step 2 异常 (降级跳过): {str(e)[:100]}")
        step2_factors = {f: 0.0 for f in MACRO_FACTORS_6}
        step2_weights = {c: 1.0 / len(bare_codes) for c in bare_codes}

    # ═══════════════════════════════════════════
    # Step 3: 研报 → MOE 投委会 (可选)
    # ═══════════════════════════════════════════
    step3_factors = {}
    step3_fund_views = {}
    step3_weights = {}
    step3_debate_logs = []
    step3_moe_report = ""
    has_report = len(uploaded_reports) > 0

    if has_report:
        log_fn(f"📄 Step 3/3: {len(uploaded_reports)} 份研报 → AI MOE 投委会审议...")

        try:
            from services.multi_agent import run_investment_committee

            # 解析 PDF
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

                # 从 bl_views 提取因子得分
                if bl_views:
                    # bl_views = {资产类别: {view, confidence, sentiment_score}}
                    # 从 sentiment_score 反推因子得分
                    step3_factors = {f: 0.0 for f in MACRO_FACTORS_6}

                    # 方法1: 从 MOE 全局元数据获取 sensitivity_modifiers
                    try:
                        import services.multi_agent as _ma_mod
                        _moe_meta = getattr(_ma_mod, '_last_moe_metadata', None) or {}
                        _modifiers = _moe_meta.get("sensitivity_modifiers", {})
                        # sensitivity_modifiers 如果有非 1.0 的值, 说明因子有调整
                        for f in MACRO_FACTORS_6:
                            mod_val = _modifiers.get(f, 1.0)
                            # 将 modifier (0.5~1.5) 映射到 factor_score (-1~1)
                            step3_factors[f] = round((mod_val - 1.0) * 2.0, 3)
                    except Exception as e_meta:
                        logger.warning(f"[Step 3] 元数据读取失败: {e_meta}")

                    # 方法2 (兜底): 从 bl_views 的 sentiment_score 反推
                    # 识别资产得分并逆向推导因子
                    _asset_scores = {}
                    for cls, vdata in bl_views.items():
                        if isinstance(vdata, dict):
                            _asset_scores[cls] = vdata.get("sentiment_score", vdata.get("view", 0) * 5)

                    # 使用资产得分的加权平均作为综合因子信号
                    if _asset_scores:
                        avg_score = sum(_asset_scores.values()) / max(len(_asset_scores), 1)
                        for f in MACRO_FACTORS_6:
                            if step3_factors[f] == 0.0:
                                step3_factors[f] = round(avg_score * 0.3, 3)

                    step3_factors = _normalize_factor_keys(step3_factors)
                    step3_fund_views = factor_scores_to_fund_views(step3_factors, bare_codes)
                    step3_weights = _views_to_weights(step3_fund_views, bare_codes)

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

    # ═══════════════════════════════════════════
    # 并行输出: KPI + 表格 + 雷达 + 面板
    # ═══════════════════════════════════════════
    log_fn("📊 正在计算 KPI 看板 + 调仓表格...")

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

    # 调仓表格 (per-fund deltas)
    holdings_info = _load_client_holdings() or {}
    original_weights = {c: 1.0 / max(len(bare_codes), 1) for c in bare_codes}

    def _build_rebalance_table(new_weights, factor_views, step_name):
        table = []
        for code in bare_codes:
            fund_info = holdings_info.get(code, {})
            old_w = original_weights.get(code, 0)
            new_w = new_weights.get(code, old_w)
            delta_w = new_w - old_w
            delta_amount = delta_w * total_amount

            view_data = factor_views.get(code, {})
            reason = ""
            view_val = view_data.get("view", 0)
            if view_val > 0.01:
                reason = "看多增配"
            elif view_val < -0.01:
                reason = "看空减配"
            else:
                reason = "中性持有"

            table.append({
                "code": code,
                "name": fund_info.get("name", code),
                "old_weight": round(old_w * 100, 2),
                "new_weight": round(new_w * 100, 2),
                "delta_weight": round(delta_w * 100, 2),
                "delta_amount": round(delta_amount, 0),
                "reason": reason,
            })
        return table

    step1_table = _build_rebalance_table(step1_weights, step1_fund_views, "宏观象限")
    step2_table = _build_rebalance_table(step2_weights, step2_fund_views, "新闻资讯")
    step3_table = _build_rebalance_table(step3_weights, step3_fund_views, "研报") if has_report else []

    # 雷达图 + BL 得分数据
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

    # BL 资产得分表
    def _build_bl_scores(factors):
        asset_views = macro_factor_to_asset_views(factors)
        return [
            {"asset": k, "score": round(v, 4), "direction": "正向" if v > 0 else ("负向" if v < 0 else "中性")}
            for k, v in asset_views.items()
        ]

    bl_scores = {
        "macro": _build_bl_scores(step1_factors),
        "news": _build_bl_scores(step2_factors),
    }
    if has_report:
        bl_scores["report"] = _build_bl_scores(step3_factors)

    log_fn("✅ 全部调仓计算完成!")

    return {
        "kpi_dashboard": kpi_dashboard,
        "tables": {
            "macro": step1_table,
            "news": step2_table,
            "report": step3_table,
        },
        "radar": radar_data,
        "bl_scores": bl_scores,
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
    }


def _views_to_weights(fund_views: dict, codes: list) -> dict:
    """
    将 BL fund views (view, confidence) 转为目标权重。
    逻辑: 等权基线 + view 偏移, 然后归一化到 [0, 1]。
    """
    n = max(len(codes), 1)
    base_w = 1.0 / n
    raw = {}
    for code in codes:
        fv = fund_views.get(code, {})
        view = fv.get("view", 0.0)
        conf = fv.get("confidence", 0.5)
        # view ∈ [-0.1, 0.1] 大致, confidence ∈ [0, 1]
        # 偏移量 = view * confidence * 调节系数
        offset = view * conf * 5.0  # 放大到权重级别
        raw[code] = max(0.0, base_w + offset)

    # 归一化
    total = sum(raw.values())
    if total > 1e-8:
        return {k: v / total for k, v in raw.items()}
    return {c: base_w for c in codes}
