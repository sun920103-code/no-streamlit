import pandas as pd
from datetime import timedelta

df_nav = pd.read_csv('d:/No Streamlit/backend/data/sync_ca5783d8-9639-4cf6-b685-24cad9297ebb.csv', index_col=0)
df_nav_daily = df_nav.copy()
df_nav_daily.index = pd.to_datetime(df_nav_daily.index)

_summary_data = {}
_years = list(range(2020, 2026 + 1))

for code in df_nav_daily.columns:
    bare = str(code).split('.')[0].zfill(6)
    s = df_nav_daily[code].dropna()
    if s.empty: continue
    
    s_last_dt = s.index[-1]
    s_last_val = float(s.iloc[-1])
    s_dict = _summary_data.setdefault(bare, {})

    for yr in _years:
        yr_key = f"ret_{yr}"
        if yr_key not in s_dict:
            try:
                s_yr = s[s.index.year == yr]
                val_end = float(s_yr.iloc[-1]) if not s_yr.empty else None
                s_prev = s[s.index.year < yr]
                val_start = float(s_prev.iloc[-1]) if not s_prev.empty else None
                if val_end and val_start:
                    s_dict[yr_key] = (val_end / val_start) - 1.0
            except Exception as e:
                print(f"{bare} {yr_key} error: {e}")

    if 'ret_ytd' not in s_dict:
        try:
            s_prev = s[s.index.year < s_last_dt.year]
            if not s_prev.empty:
                s_dict['ret_ytd'] = (s_last_val / float(s_prev.iloc[-1])) - 1.0
        except Exception as e:
            print(f"{bare} ret_ytd error: {e}")

    print(f"Result for {bare}:", s_dict)
