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
            w.start()
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
