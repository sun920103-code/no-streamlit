import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_wind_fund_profiles(fund_codes: list) -> dict:
    """
    Fetch comprehensive fund profiles from Wind API.
    Returns a dictionary mapping fund code to profile dict.
    """
    if not fund_codes:
        return {}
    
    unique_codes = list(set(fund_codes))
    result = {}
    
    try:
        from WindPy import w
        if not w.isconnected():
            return {code: _get_empty_profile(code) for code in unique_codes}
    except ImportError:
        print("[WindError] WindPy module not found.")
        return {code: _get_empty_profile(code) for code in unique_codes}

    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y%m%d")
    
    # ── 1. Fetch Basic Info ──
    basic_fields = "sec_name,fund_fundmanager,fund_setupdate,prt_fundnetasset_total"
    res_basic = w.wss(','.join(unique_codes), basic_fields, f"tradeDate={current_date_str}")
    
    if res_basic.ErrorCode != 0:
        print(f"[Wind API ERROR] Basic info failed: ErrorCode {res_basic.ErrorCode}")
        return {code: _get_empty_profile(code) for code in unique_codes}
        
    df_basic = pd.DataFrame(res_basic.Data).T
    df_basic.columns = ["sec_name", "fund_fundmanager", "fund_setupdate", "prt_fundnetasset_total"]
    df_basic.index = unique_codes

    # ── 2. Fetch Time Series for Performance Metrics ──
    start_3y = (current_date - timedelta(days=365 * 3 + 30)).strftime("%Y-%m-%d")
    end_date = current_date.strftime("%Y-%m-%d")
    
    res_ts = w.wsd(','.join(unique_codes), "nav_adj", start_3y, end_date, "")
    df_nav = pd.DataFrame()
    if res_ts.ErrorCode == 0:
        df_nav = pd.DataFrame(res_ts.Data).T
        df_nav.columns = unique_codes
        df_nav.index = pd.to_datetime(res_ts.Times)
        df_nav.dropna(how='all', inplace=True)
    else:
        print(f"[Wind API ERROR] TS info failed: ErrorCode {res_ts.ErrorCode}")

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
        row = df_basic.loc[code] if code in df_basic.index else None
        
        # Parse Performance
        navytd = nav1y = nav3y = vol = maxdd = sharpe = None
        
        if code in df_nav.columns and not df_nav.empty:
            fund_nav = df_nav[code].dropna()
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
            "name": fmt_str(row["sec_name"] if row is not None else "暂无"),
            "mgrname": fmt_str(row["fund_fundmanager"] if row is not None else "暂无"),
            "setupdate": fmt_date(row["fund_setupdate"] if row is not None else "暂无"),
            "scale": fmt_num(row["prt_fundnetasset_total"] / 1e8 if row is not None and not pd.isna(row["prt_fundnetasset_total"]) else None, 2, "亿"),
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


def compute_portfolio_metrics(allocations: list, period_years: int = 1) -> dict:
    """
    基于真实基金 NAV 时序数据计算组合级 KPI。
    
    :param allocations: [{"code": "000001.OF", "weight_pct": 10.5}, ...]
    :param period_years: 回溯年数 (1/3/5)
    :return: {"ann_vol_pct": 12.5, "max_drawdown_pct": -15.3, "ann_return_pct": 8.2, "sharpe": 0.65, "source": "wind"}
             如果 Wind 不可用则返回 {"source": "fallback"}
    """
    if not allocations:
        return {"source": "fallback"}
    
    codes = [a["code"] for a in allocations if a.get("weight_pct", 0) > 0.01]
    weights_map = {a["code"]: a["weight_pct"] / 100.0 for a in allocations if a.get("weight_pct", 0) > 0.01}
    
    if not codes:
        return {"source": "fallback"}
    
    try:
        from WindPy import w
        wind_available = w.isconnected()
    except ImportError:
        print("[WindError] WindPy not available for portfolio metrics.")
        wind_available = False
    
    # 拉取 NAV 时序
    current_date = datetime.now()
    start_date_str = (current_date - timedelta(days=365 * period_years + 30)).strftime("%Y-%m-%d")
    end_date_str = current_date.strftime("%Y-%m-%d")
    
    df_nav = None
    source_used = "fallback"

    if wind_available:
        res = w.wsd(','.join(codes), "nav_adj", start_date_str, end_date_str, "")
        if res.ErrorCode == 0:
            if len(codes) == 1:
                df_nav = pd.DataFrame({codes[0]: res.Data[0]}, index=pd.to_datetime(res.Times))
            else:
                df_nav = pd.DataFrame(dict(zip(codes, res.Data)), index=pd.to_datetime(res.Times))
            source_used = "wind"
            print(f"[智选] KPI 测算使用 Wind: 成功拉取 {len(codes)} 只基金的历史净值")
        else:
            print(f"[Wind API ERROR] Portfolio NAV fetch failed: {res.ErrorCode}")

    if df_nav is None or df_nav.empty:
        # ── Tushare 兜底 ──
        try:
            from scripts.tushare_fetcher import fetch_fund_nav
            print(f"[智选] Wind 净值拉取失败，启用 Tushare API 兜底抓取组合 KPI 所需净值: {len(codes)}只底仓...")
            df_nav = fetch_fund_nav(codes, start_date_str, end_date_str)
            if df_nav is not None and not df_nav.empty:
                source_used = "tushare"
        except Exception as e:
            print(f"[Tushare ERROR] 兜底获取净值失败: {e}")

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
    df_returns.dropna(how='any', inplace=True)
    
    if len(df_returns) < 30:
        return {"source": "fallback"}
    
    # 归一化权重 (仅保留有有效数据的基金)
    total_w = sum(weights_map.get(c, 0) for c in valid_codes)
    if total_w <= 0:
        return {"source": "fallback"}
    norm_weights = np.array([weights_map.get(c, 0) / total_w for c in valid_codes])
    
    # ── 组合日收益率序列 ──
    portfolio_returns = (df_returns[valid_codes].values @ norm_weights)
    
    # ── 年化波动率 (基于日收益率) ──
    daily_vol = np.std(portfolio_returns, ddof=1)
    ann_vol = daily_vol * np.sqrt(242)
    
    # ── 年化收益率 ──
    ann_ret = np.mean(portfolio_returns) * 242
    
    # ── 夏普比率 (无风险利率 2%) ──
    sharpe = (ann_ret - 0.02) / ann_vol if ann_vol > 1e-8 else 0
    
    # ── 最大回撤 (基于组合净值曲线) ──
    portfolio_nav = (1 + pd.Series(portfolio_returns)).cumprod()
    cummax = portfolio_nav.cummax()
    drawdowns = (portfolio_nav - cummax) / cummax
    max_dd = drawdowns.min()
    
    # 如果用的是 3 年数据，需要年化最大回撤
    # 最大回撤本身不年化，但如果 period > 1年，已经是整个区间的最大回撤
    
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

