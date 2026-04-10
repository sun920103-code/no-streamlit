"""
wind_profiles.py — 基金资料与组合KPI计算服务
==============================================
数据源: Tushare Pro (唯一数据源)
已移除 Wind API 依赖 (2026-04-08 Phase 1 迁移)
"""
import os
import importlib.util
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def _load_tushare_fetcher():
    """使用绝对路径加载 tushare_fetcher 模块，避免 sys.path 污染。"""
    ts_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts", "tushare_fetcher.py"
    )
    spec = importlib.util.spec_from_file_location("tushare_fetcher", ts_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_wind_fund_profiles(fund_codes: list) -> dict:
    """
    获取基金概况资料 (元数据 + NAV 绩效指标)。
    数据源: Tushare Pro。函数名保留 'wind' 前缀以保持调用端兼容。

    Returns a dictionary mapping fund code to profile dict.
    """
    if not fund_codes:
        return {}

    unique_codes = list(set(fund_codes))
    result = {}

    current_date = datetime.now()
    start_3y = (current_date - timedelta(days=365 * 3 + 30)).strftime("%Y-%m-%d")
    end_date = current_date.strftime("%Y-%m-%d")

    # ── 1. 元数据 (Tushare fund_basic) ──
    df_meta = pd.DataFrame()
    try:
        ts = _load_tushare_fetcher()
        df_meta = ts.fetch_fund_metadata(unique_codes)
        if df_meta is not None and not df_meta.empty:
            print(f"[基金资料] Tushare 元数据获取成功: {len(df_meta)} 只基金")
        else:
            df_meta = pd.DataFrame()
    except Exception as e:
        print(f"[基金资料] Tushare 元数据异常: {e}")

    # ── 2. NAV 时序 (Tushare fund_nav — 主路径) ──
    df_nav = pd.DataFrame()
    try:
        ts = _load_tushare_fetcher()
        df_nav = ts.fetch_fund_nav(unique_codes, start_3y, end_date)
        if df_nav is not None and not df_nav.empty:
            df_nav.dropna(how='all', inplace=True)
            print(f"[基金资料] Tushare NAV 获取成功: {len(df_nav.columns)} 列, {len(df_nav)} 行")
        else:
            df_nav = pd.DataFrame()
    except Exception as e:
        print(f"[基金资料] Tushare NAV 异常: {e}")

    # [2026-04-10] Wind API 已永久移除, 纯 Tushare 路径

    # Format helpers
    def fmt_num(val, decimals=2, suffix=""):
        if pd.isna(val) or val is None:
            return "暂无"
        try:
            return f"{round(float(val), decimals)}{suffix}"
        except:
            return "暂无"

    def fmt_date(val):
        if pd.isna(val) or val is None:
            return "暂无"
        if isinstance(val, str):
            return val.split(" ")[0]
        if hasattr(val, 'strftime'):
            return val.strftime("%Y-%m-%d")
        return str(val)

    def fmt_str(val):
        if pd.isna(val) or val is None or str(val).strip() == "":
            return "暂无"
        return str(val).replace('\r', '').replace('\n', ' ')

    for code in unique_codes:
        bare = code.split('.')[0].zfill(6)

        # 从元数据获取基金信息
        sec_name = "暂无"
        mgr_name = "暂无"
        setup_date = "暂无"
        scale_str = "暂无"

        if not df_meta.empty and bare in df_meta.index:
            meta_row = df_meta.loc[bare]
            sec_name = fmt_str(meta_row.get("SEC_NAME", "暂无"))
            mgr_name = fmt_str(meta_row.get("FUND_FUNDMANAGER", "暂无"))
            setup_date = fmt_str(meta_row.get("FUND_FUNDMANAGER_STARTDATE", "暂无"))

        # Wind 增强: 覆盖缺失字段 (基金规模/成立日期/基金经理)
        if code in wind_basic:
            wb = wind_basic[code]
            if sec_name == "暂无":
                sec_name = fmt_str(wb.get("sec_name", "暂无"))
            if mgr_name == "暂无":
                mgr_name = fmt_str(wb.get("fund_fundmanager", "暂无"))
            if setup_date == "暂无":
                setup_date = fmt_date(wb.get("fund_setupdate", "暂无"))
            scale_val = wb.get("prt_fundnetasset_total")
            if scale_val is not None and not pd.isna(scale_val):
                scale_str = fmt_num(float(scale_val) / 1e8, 2, "亿")

        # Parse Performance from NAV
        navytd = nav1y = nav3y = vol = maxdd = sharpe = None

        # NAV 列名匹配: 尝试原始代码和 bare code
        nav_col = None
        if not df_nav.empty:
            if code in df_nav.columns:
                nav_col = code
            elif bare in df_nav.columns:
                nav_col = bare

        if nav_col and not df_nav.empty:
            fund_nav = df_nav[nav_col].dropna()
            # 过滤掉非法的日期 (NaT) 以防止 last_date.year 返回 float
            fund_nav = fund_nav[fund_nav.index.notna()]
            
            if len(fund_nav) > 0:
                last_val = fund_nav.iloc[-1]
                last_date = fund_nav.index[-1]

                # YTD
                ytd_start_date = pd.Timestamp(year=last_date.year - 1, month=12, day=31)
                before_ytd = fund_nav[fund_nav.index <= ytd_start_date]
                if len(before_ytd) > 0:
                    ytd_val = before_ytd.iloc[-1]
                    if ytd_val > 0: navytd = (last_val / ytd_val - 1) * 100

                # 1Y
                date_1y = last_date - pd.DateOffset(years=1)
                before_1y = fund_nav[fund_nav.index <= date_1y]
                if len(before_1y) > 0:
                    val_1y = before_1y.iloc[-1]
                    if val_1y > 0: nav1y = (last_val / val_1y - 1) * 100

                # 3Y
                date_3y = last_date - pd.DateOffset(years=3)
                before_3y = fund_nav[fund_nav.index <= date_3y]
                if len(before_3y) > 0:
                    val_3y = before_3y.iloc[-1]
                    if val_3y > 0: nav3y = (last_val / val_3y - 1) * 100

                # Volatility & Sharpe
                if len(fund_nav) > 20:
                    rets = fund_nav.pct_change().dropna()
                    daily_vol = rets.std()
                    annual_vol = daily_vol * np.sqrt(242)
                    vol = annual_vol * 100

                    annual_ret = rets.mean() * 242
                    if annual_vol > 0:
                        sharpe = (annual_ret - 0.02) / annual_vol

                # Max Drawdown
                cummax = fund_nav.cummax()
                drawdowns = (fund_nav - cummax) / cummax
                maxdd = drawdowns.min() * 100

        result[code] = {
            "code": code,
            "name": sec_name,
            "mgrname": mgr_name,
            "setupdate": setup_date,
            "scale": scale_str,
            "navytd": fmt_num(navytd, 2, "%"),
            "nav1y": fmt_num(nav1y, 2, "%"),
            "nav3y": fmt_num(nav3y, 2, "%"),
            "volatility": fmt_num(vol, 2, "%"),
            "maxdrawdown": fmt_num(maxdd, 2, "%"),
            "sharpe": fmt_num(sharpe, 2, "")
        }

    return result


def _get_empty_profile(code):
    return {
        "code": code,
        "name": "暂无",
        "mgrname": "暂无",
        "setupdate": "暂无",
        "scale": "暂无",
        "navytd": "暂无",
        "nav1y": "暂无",
        "nav3y": "暂无",
        "volatility": "暂无",
        "maxdrawdown": "暂无",
        "sharpe": "暂无"
    }


def compute_portfolio_metrics(allocations: list, period_years: float = 1.0, cached_nav_df: pd.DataFrame = None) -> dict:
    """
    基于真实基金 NAV 时序数据计算组合级 KPI。
    数据源: Tushare Pro (唯一) 或预缓存 DataFrame。

    :param allocations: [{"code": "000001.OF", "weight_pct": 10.5}, ...]
    :param period_years: 回溯年数 (1/3/5)
    :param cached_nav_df: 可选的预先拉取好的 NAV DataFrame
    :return: {"ann_vol_pct": 12.5, "max_drawdown_pct": -15.3, "ann_return_pct": 8.2, "sharpe": 0.65, "source": "tushare"}
    """
    if not allocations:
        return {"source": "fallback"}

    codes = [a["code"] for a in allocations if a.get("weight_pct", 0) > 0.01]
    weights_map = {a["code"]: a["weight_pct"] / 100.0 for a in allocations if a.get("weight_pct", 0) > 0.01}

    if not codes:
        return {"source": "fallback"}

    # 拉取 NAV 时序
    current_date = datetime.now()
    start_date_str = (current_date - timedelta(days=365 * period_years + 30)).strftime("%Y-%m-%d")
    end_date_str = current_date.strftime("%Y-%m-%d")

    df_nav = None
    source_used = "fallback"

    # 1. 优先使用预缓存数据
    if cached_nav_df is not None and not cached_nav_df.empty:
        avail_codes = [c for c in codes if c in cached_nav_df.columns]
        if avail_codes:
            df_nav = cached_nav_df[avail_codes].copy()
            source_used = "cached"

    # 2. Tushare 拉取
    if df_nav is None or df_nav.empty:
        try:
            ts = _load_tushare_fetcher()
            print(f"[组合KPI] Tushare 拉取 {len(codes)} 只基金 NAV ({start_date_str} ~ {end_date_str})...")
            df_nav = ts.fetch_fund_nav(codes, start_date_str, end_date_str)
            if df_nav is not None and not df_nav.empty:
                source_used = "tushare"
                print(f"[组合KPI] Tushare 成功: {len(df_nav.columns)} 列, {len(df_nav)} 行")
            else:
                print(f"[组合KPI] Tushare 返回空 DataFrame")
        except Exception as e:
            print(f"[组合KPI] Tushare 异常: {e}\n{traceback.format_exc()}")

    if df_nav is None or df_nav.empty:
        return {"source": "fallback"}

    df_nav.dropna(how='all', inplace=True)
    df_nav.ffill(inplace=True)

    # 至少需要 60 个交易日的数据
    valid_codes = [c for c in codes if c in df_nav.columns and df_nav[c].notna().sum() > 60]
    if not valid_codes:
        return {"source": "fallback"}

    # 计算各基金日收益率
    df_returns = df_nav[valid_codes].pct_change().dropna(how='all')

    if len(df_returns) < 30:
        return {"source": "fallback"}

    # 获取归一化目标权重
    base_weights = np.array([weights_map.get(c, 0) for c in valid_codes])

    # ── 组合日收益率序列 (动态剔除无数据基金并重加权) ──
    portfolio_returns = []
    for date, row_series in df_returns.iterrows():
        row_arr = row_series.values
        valid_mask = ~np.isnan(row_arr)
        if not valid_mask.any():
            portfolio_returns.append(0.0)
            continue

        w_valid = base_weights[valid_mask]
        w_sum = w_valid.sum()
        if w_sum > 1e-8:
            daily_ret = np.dot(row_arr[valid_mask], w_valid / w_sum)
            portfolio_returns.append(daily_ret)
        else:
            portfolio_returns.append(0.0)

    portfolio_returns = np.array(portfolio_returns)
    if len(portfolio_returns) > 0 and portfolio_returns[0] == 0.0:
        portfolio_returns = portfolio_returns[1:]

    # ── 年化波动率 ──
    daily_vol = np.std(portfolio_returns, ddof=1)
    ann_vol = daily_vol * np.sqrt(242)

    # ── 累积净值曲线 ──
    portfolio_nav = (1 + pd.Series(portfolio_returns)).cumprod()

    # ── 真实复合年化收益率 (CAGR) ──
    trading_days = len(portfolio_returns)
    total_return = portfolio_nav.iloc[-1] - 1.0
    if trading_days > 0:
        ann_ret = (1 + total_return) ** (242 / trading_days) - 1.0
    else:
        ann_ret = 0.0

    # ── 夏普比率 (无风险利率 2%) ──
    sharpe = (ann_ret - 0.02) / ann_vol if ann_vol > 1e-8 else 0

    # ── 最大回撤 ──
    portfolio_nav = (1 + pd.Series(portfolio_returns)).cumprod()
    cummax = portfolio_nav.cummax()
    drawdowns = (portfolio_nav - cummax) / cummax
    max_dd = drawdowns.min()

    return {
        "ann_return_pct": round(float(ann_ret * 100), 2),
        "ann_vol_pct": round(float(ann_vol * 100), 2),
        "max_drawdown_pct": round(float(max_dd * 100), 2),
        "sharpe": round(float(sharpe), 2),
        "data_points": len(df_returns),
        "valid_funds": len(valid_codes),
        "total_funds": len(codes),
        "source": source_used,
    }
