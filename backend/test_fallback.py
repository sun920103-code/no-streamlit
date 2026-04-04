import pandas as pd
from datetime import timedelta

df_nav = pd.read_csv('d:/No Streamlit/backend/data/sync_2b7a0ed8-1325-426a-8557-e0d6064b1b8c.csv', index_col=0)
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

    print(f"Testing {bare}, last dt: {s_last_dt}, last val: {s_last_val}")

    for yr in _years:
        yr_key = f"ret_{yr}"
        if yr_key not in s_dict:
            try:
                s_yr = s[s.index.year == yr]
                if not s_yr.empty:
                    val_end = float(s_yr.iloc[-1])
                    s_prev = s[s.index.year < yr]
                    if not s_prev.empty:
                        val_start = float(s_prev.iloc[-1])
                        s_dict[yr_key] = (val_end / val_start) - 1.0
                    else:
                        print(f"  {bare} ret_{yr} failed: s_prev is empty")
            except Exception as e:
                print(f"  {bare} ret_{yr} Exception:", e)

    if 'ret_ytd' not in s_dict:
        try:
            s_prev = s[s.index.year < s_last_dt.year]
            if not s_prev.empty:
                s_dict['ret_ytd'] = (s_last_val / float(s_prev.iloc[-1])) - 1.0
            else:
                print(f"  {bare} ret_ytd failed: s_prev is empty")
        except Exception as e:
            print(f"  {bare} ret_ytd Exception:", e)

    _cycle_map = [(182, 'ret_6m'), (365, 'ret_1y'), (1095, 'ret_3y'), (1826, 'ret_5y')]
    for days, key in _cycle_map:
        if key not in s_dict:
            try:
                ago_dt = s_last_dt - timedelta(days=days)
                past_vals = s[:ago_dt.strftime('%Y-%m-%d')]
                if not past_vals.empty:
                    s_dict[key] = (s_last_val / float(past_vals.iloc[-1])) - 1.0
                else:
                    print(f"  {bare} {key} failed: past_vals is empty for ago_dt {ago_dt}")
            except Exception as e:
                print(f"  {bare} {key} Exception:", e)

    print(f"Result for {bare}:", s_dict)
    break  # just test one
