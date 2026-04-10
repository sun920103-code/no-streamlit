#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tushare_fetcher.py — Tushare Pro 数据适配层

作为 Wind API 的备用数据源, 提供基金 NAV、基金元数据、A 股日线行情。
所有接口设计为与 sync_client_holdings.py 中的 Wind 返回格式兼容。

Tushare Pro Token: 由环境变量 TUSHARE_TOKEN 或直接硬编码。
"""
import os
import logging
import time
import pandas as pd
from datetime import datetime, timedelta

# Tushare Pro Token
TUSHARE_TOKEN = os.environ.get(
    "TUSHARE_TOKEN",
    "609eaf15dc1e4e7dbb77d491fbf16cfe7e7ef70d466b470426e80efa"
)

_ts_api = None


def _get_api():
    """懒加载 Tushare Pro API 实例。"""
    global _ts_api
    if _ts_api is None:
        try:
            import tushare as ts
            ts.set_token(TUSHARE_TOKEN)
            _ts_api = ts.pro_api()
            logging.info("[Tushare] Pro API 初始化成功")
        except ImportError:
            logging.error("[Tushare] tushare 未安装, 请执行: pip install tushare")
            raise
        except Exception as e:
            logging.error(f"[Tushare] API 初始化失败: {e}")
            raise
    return _ts_api


def _is_etf_code(wind_code: str) -> bool:
    """判断是否为场内 ETF 代码 (上交所 .SH 或深交所 .SZ)。"""
    c = str(wind_code).strip().upper()
    return c.endswith('.SH') or c.endswith('.SZ')


def _wind_code_to_ts_code(wind_code: str) -> str:
    """
    Wind 基金代码 → Tushare 基金代码。
    ETF (场内基金): 保留 .SH / .SZ 后缀
    开放式基金: 统一加 .OF 后缀
    例: '510300.SH' → '510300.SH',  '000979.OF' → '000979.OF',  '000979' → '000979.OF'
    """
    c = str(wind_code).strip()
    if _is_etf_code(c):
        return c  # ETF 保持原样
    bare = c.split('.')[0].zfill(6)
    return f"{bare}.OF"


def _wind_stock_to_ts_code(wind_code: str) -> str:
    """
    Wind 股票/指数代码 → Tushare 代码
    例: '600519.SH' → '600519.SH',  '000001.SZ' → '000001.SZ'
    港股: '00700.HK' → '00700.HK'
    """
    return str(wind_code).strip()


# ═══════════════════════════════════════════
# 1. 基金复权净值 (替代 w.wsd nav_adj)
# ═══════════════════════════════════════════

def fetch_fund_nav(codes: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    批量获取基金复权净值, 返回与 Wind w.wsd 兼容的 DataFrame。
    自动识别 ETF (.SH/.SZ) 和开放式基金 (.OF), 分别使用:
      - ETF: fund_daily API (收盘价 close)
      - 开放式基金: fund_nav API (复权净值 adj_nav)

    :param codes: 基金代码列表 (支持 Wind 格式如 '510300.SH' 或裸码 '000979')
    :param start_date: 开始日期 'YYYY-MM-DD'
    :param end_date: 结束日期 'YYYY-MM-DD'
    :return: DataFrame, index=日期, columns=原始代码, values=复权净值/收盘价
    """
    api = _get_api()
    all_dfs = {}
    start_ts = start_date.replace('-', '')
    end_ts = end_date.replace('-', '')

    for code in codes:
        ts_code = _wind_code_to_ts_code(code)
        col_key = code  # 保留原始代码作为列名
        try:
            # 统一使用 fund_nav 获取复权净值 (支持 ETF 和 场外基金)
            df = api.fund_nav(
                ts_code=ts_code,
                start_date=start_ts,
                end_date=end_ts,
                fields='nav_date,adj_nav'
            )
            if df is not None and not df.empty:
                df['nav_date'] = pd.to_datetime(df['nav_date'])
                df = df.sort_values('nav_date').drop_duplicates(subset='nav_date', keep='last')
                df = df.set_index('nav_date')
                all_dfs[col_key] = df['adj_nav'].astype(float)
                logging.info(f"  [Tushare] {ts_code} 复权净值(adj_nav)获取成功: {len(df)} 天")
            else:
                logging.warning(f"  [Tushare] {ts_code} NAV 为空")
            
            time.sleep(0.12)  # Tushare 频率限制: 每分钟200次
        except Exception as e:
            logging.warning(f"  [Tushare] {code} NAV/价格 异常: {e}")
            time.sleep(0.5)

    if not all_dfs:
        return pd.DataFrame()

    result = pd.DataFrame(all_dfs)
    result.index = pd.to_datetime(result.index)
    result = result[result.index.notna()]
    result = result.sort_index()
    return result


# ═══════════════════════════════════════════
# 2. 基金元数据 (替代 w.wss sec_name, fund_type 等)
# ═══════════════════════════════════════════

def fetch_fund_metadata(codes: list) -> pd.DataFrame:
    """
    批量获取基金元数据, 返回与 Wind w.wss 兼容的 DataFrame。

    :param codes: 基金代码列表 (bare code)
    :return: DataFrame, index=bare_code,
             columns=['SEC_NAME', 'FUND_TYPE', 'FUND_INVESTTYPE',
                      'FUND_CORP_FUNDMANAGEMENTCOMPANY',
                      'FUND_FUNDMANAGER', 'FUND_FUNDMANAGER_STARTDATE']
    """
    api = _get_api()
    rows = []

    for code in codes:
        ts_code = _wind_code_to_ts_code(code)
        bare = code.split('.')[0].zfill(6)
        try:
            # fund_basic: 基金基本信息
            df = api.fund_basic(ts_code=ts_code,
                                fields='ts_code,name,fund_type,management,manager,found_date')
            
            mgr_name = '暂无'
            mgr_start = ''
            
            # 追加拉取 fund_manager 获取真实的经理变更日期
            try:
                mgr_df = api.fund_manager(ts_code=ts_code)
                if mgr_df is not None and not mgr_df.empty:
                    # 找到目前仍在任的经理(end_date 为 NaN 或空字符串)
                    active_mgr = mgr_df[mgr_df['end_date'].isna() | (mgr_df['end_date'] == '')]
                    if not active_mgr.empty:
                        mgr_name = ",".join(active_mgr['name'].dropna().tolist())
                        mgr_start = active_mgr['begin_date'].dropna().max()  # 取最近上任的一个人的时间
                time.sleep(0.12)
            except Exception as e:
                pass

            if df is not None and not df.empty:
                row = df.iloc[0]
                if mgr_name == '暂无': mgr_name = row.get('manager', '')
                if mgr_start == '': mgr_start = row.get('found_date', '')
                
                rows.append({
                    'code': bare,
                    'SEC_NAME': row.get('name', bare),
                    'FUND_TYPE': row.get('fund_type', ''),
                    'FUND_INVESTTYPE': row.get('fund_type', ''),  # Tushare fund_type ≈ Wind investtype
                    'FUND_CORP_FUNDMANAGEMENTCOMPANY': row.get('management', ''),
                    'FUND_FUNDMANAGER': mgr_name,
                    'FUND_FUNDMANAGER_STARTDATE': mgr_start,
                    'FUND_FUNDMANAGER_TOTALFUNDNO': '',
                })
            else:
                rows.append({'code': bare, 'SEC_NAME': bare})
            time.sleep(0.12)
        except Exception as e:
            logging.warning(f"  [Tushare] {bare} 元数据异常: {e}")
            rows.append({'code': bare, 'SEC_NAME': bare})
            time.sleep(0.5)

    if not rows:
        return pd.DataFrame()

    df_meta = pd.DataFrame(rows)
    df_meta = df_meta.set_index('code')
    # 统一列名大写 (与 Wind wss 对齐)
    df_meta.columns = [c.upper() for c in df_meta.columns]
    return df_meta


# ═══════════════════════════════════════════
# 3. A 股日涨跌幅 (替代 w.wss pct_chg / w.wsd pct_chg)
# ═══════════════════════════════════════════

def fetch_stock_pct_chg(stock_codes: list, start_date: str = None, end_date: str = None) -> dict:
    """
    获取 A 股个股的名称 + 涨跌幅 + 7天逐日涨跌幅。

    :param stock_codes: Wind 格式股票代码列表 (如 ['600519.SH', '000001.SZ'])
    :param start_date: 7天行情开始日期 YYYYMMDD
    :param end_date: 7天行情结束日期 YYYYMMDD
    :return: {stock_code: {'name': ..., 'pct_chg': ..., 'max_drop_7d': ..., 'daily_pcts': [...]}}
    """
    api = _get_api()
    result = {}

    if end_date is None:
        end_date = datetime.today().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.today() - timedelta(days=10)).strftime('%Y%m%d')

    for stk_code in stock_codes:
        ts_code = _wind_stock_to_ts_code(stk_code)
        try:
            # 判断是否为港股 (Tushare 港股用 hk_daily)
            if '.HK' in ts_code.upper():
                # 港股: 暂不支持, 返回空
                result[stk_code] = {
                    'name': stk_code, 'pct_chg': 0.0,
                    'max_drop_7d': 0.0, 'drop_date': '', 'daily_pcts': []
                }
                continue

            # A 股日线
            df = api.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='trade_date,close,pct_chg'
            )

            if df is not None and not df.empty:
                df = df.sort_values('trade_date')
                pct_list = df['pct_chg'].tolist()
                latest_pct = float(df.iloc[-1]['pct_chg']) if not df.empty else 0.0
                min_pct = float(df['pct_chg'].min())
                min_idx = df['pct_chg'].idxmin()
                drop_date = str(df.loc[min_idx, 'trade_date']) if min_idx is not None else ''

                # 获取股票名称
                stock_name = stk_code
                try:
                    info = api.namechange(ts_code=ts_code, fields='ts_code,name')
                    if info is not None and not info.empty:
                        stock_name = info.iloc[0]['name']
                except Exception:
                    pass

                result[stk_code] = {
                    'name': stock_name,
                    'pct_chg': latest_pct,
                    'max_drop_7d': min_pct,
                    'drop_date': drop_date,
                    'daily_pcts': pct_list,
                }
            else:
                result[stk_code] = {
                    'name': stk_code, 'pct_chg': 0.0,
                    'max_drop_7d': 0.0, 'drop_date': '', 'daily_pcts': []
                }
            time.sleep(0.12)
        except Exception as e:
            logging.warning(f"  [Tushare] {stk_code} 涨跌幅异常: {e}")
            result[stk_code] = {
                'name': stk_code, 'pct_chg': 0.0,
                'max_drop_7d': 0.0, 'drop_date': '', 'daily_pcts': []
            }
            time.sleep(0.5)

    return result


# ═══════════════════════════════════════════
# 4. 宽基指数日线 (替代 w.wsd close for benchmarks)
# ═══════════════════════════════════════════

def fetch_index_daily(index_codes: dict, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取多个指数的日收盘价。

    :param index_codes: {Wind代码: 名称} 如 {'000300.SH': '沪深300'}
    :param start_date: 'YYYY-MM-DD'
    :param end_date: 'YYYY-MM-DD'
    :return: DataFrame, index=日期, columns=Wind代码, values=收盘价
    """
    api = _get_api()
    all_series = {}
    start_ts = start_date.replace('-', '')
    end_ts = end_date.replace('-', '')

    for wind_code, name in index_codes.items():
        ts_code = _wind_stock_to_ts_code(wind_code)
        try:
            if '.HK' in ts_code.upper() or 'HSI' in ts_code.upper():
                logging.warning(f"  [Tushare] 港股指数 {ts_code} 暂不支持, 跳过")
                continue

            df = api.index_daily(
                ts_code=ts_code,
                start_date=start_ts,
                end_date=end_ts,
                fields='trade_date,close'
            )
            if df is not None and not df.empty:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date').set_index('trade_date')
                all_series[wind_code] = df['close'].astype(float)
                logging.info(f"  [Tushare] {name}({wind_code}) 指数日线: {len(df)} 天")
            time.sleep(0.12)
        except Exception as e:
            logging.warning(f"  [Tushare] {wind_code} 指数日线异常: {e}")
            time.sleep(0.5)

    if not all_series:
        return pd.DataFrame()

    result = pd.DataFrame(all_series)
    result.index = pd.to_datetime(result.index)
    return result.sort_index()


# ═══════════════════════════════════════════
# 5. 宏观经济指标 (月度频次)
# ═══════════════════════════════════════════

def fetch_macro_economic_indicators(limit: int = 150) -> pd.DataFrame:
    """
    通过 Tushare 获取核心宏观经济指标：PMI, CPI_YoY, M2_Growth, Credit_Impulse (M1-M2差)
    带有一天内有效的文件缓存，以保护 API 配额。
    
    :param limit: 获取的月数
    :return: DataFrame, index 包含 'PMI', 'CPI_YoY', 'M2_Growth', 'Credit_Impulse', index 是月份 'YYYYMM'
    """
    import json
    
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "macro_indicators_cache.json")
    
    # 尝试加载缓存
    if os.path.exists(cache_file):
        try:
            mt = os.path.getmtime(cache_file)
            if time.time() - mt < 86400:  # 缓存 24 小时
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_content = json.load(f)
                    df = pd.DataFrame(cache_content)
                    if not df.empty:
                        df.index = pd.to_datetime(df.index)
                        return df
        except Exception as e:
            logging.warning(f"[Tushare] 读取宏观缓存失败: {e}")
            
    api = _get_api()
    
    try:
        logging.info("[Tushare] 正在拉取宏观指标: PMI...")
        df_pmi = api.cn_pmi(limit=limit)
        # 兼容 Tushare 大小写返回
        month_col = 'MONTH' if 'MONTH' in df_pmi.columns else 'month'
        pmi_col = 'PMI010000' if 'PMI010000' in df_pmi.columns else 'pmi'
        df_pmi = df_pmi[[month_col, pmi_col]].set_index(month_col)
        df_pmi.columns = ['PMI']
        time.sleep(0.5)
        
        logging.info("[Tushare] 正在拉取宏观指标: CPI...")
        df_cpi = api.cn_cpi(limit=limit)
        df_cpi = df_cpi[['month', 'nt_yoy']].set_index('month')
        df_cpi.columns = ['CPI_YoY']
        time.sleep(0.5)
        
        logging.info("[Tushare] 正在拉取宏观指标: M2...")
        df_m = api.cn_m(limit=limit)
        df_m = df_m[['month', 'm2_yoy', 'm1_yoy']].set_index('month')
        df_m['Credit_Impulse'] = df_m['m1_yoy'] - df_m['m2_yoy']  # 用 M1-M2 增速剪刀差作为流动性/信用脉冲替代
        df_m = df_m[['m2_yoy', 'Credit_Impulse']]
        df_m.columns = ['M2_Growth', 'Credit_Impulse']
        
        # ── 美国 10 年期国债收益率 (海外环境因子) ──
        df_us10y = None
        try:
            logging.info("[Tushare] 正在拉取海外指标: US 10Y Treasury Yield...")
            # 拉取近 10 年日频数据
            us_start = (datetime.today() - timedelta(days=365 * 10 + 60)).strftime('%Y%m%d')
            us_end = datetime.today().strftime('%Y%m%d')
            df_us_raw = api.us_tycr(start_date=us_start, end_date=us_end, fields='date,y10')
            time.sleep(0.5)
            if df_us_raw is not None and not df_us_raw.empty:
                df_us_raw['date'] = pd.to_datetime(df_us_raw['date'])
                df_us_raw = df_us_raw.dropna(subset=['y10']).sort_values('date').set_index('date')
                df_us_raw['y10'] = pd.to_numeric(df_us_raw['y10'], errors='coerce')
                # 重采样为月末, 与 PMI/CPI/M2 月频对齐
                df_us10y = df_us_raw['y10'].resample('ME').last().dropna()
                df_us10y = df_us10y.to_frame(name='US10Y')
                # 将 index 对齐到月初 (与其他 Tushare 宏观指标一致)
                df_us10y.index = df_us10y.index.to_period('M').to_timestamp()
                logging.info(f"  [Tushare] US 10Y 收益率获取成功: {len(df_us10y)} 个月")
            else:
                logging.warning("  [Tushare] US 10Y 收益率数据为空")
        except Exception as e_us:
            logging.warning(f"  [Tushare] US 10Y 收益率拉取异常(非致命): {e_us}")
        
        # 将所有指标合并
        merge_list = [df_pmi, df_cpi, df_m]
        if df_us10y is not None and not df_us10y.empty:
            merge_list.append(df_us10y)
        df_macro = pd.concat(merge_list, axis=1)
        df_macro.index = pd.to_datetime(df_macro.index, format='%Y%m', errors='coerce')
        df_macro = df_macro.sort_index()
        
        # 保存缓存 (将 index 转换为字符串)
        try:
            cache_save = df_macro.copy()
            cache_save.index = cache_save.index.strftime('%Y-%m-%d')
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_save.to_dict(), f, indent=2)
        except Exception as e:
            logging.warning(f"[Tushare] 保存宏观缓存失败: {e}")
            
        return df_macro
        
    except Exception as e:
        logging.error(f"[Tushare] 拉取宏观指标异常: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════
# 6. 基金重仓股穿透 (替代 w.wset fundholdings)
# ═══════════════════════════════════════════

def fetch_fund_portfolio(fund_codes: list, rpt_date: str = None) -> dict:
    """
    获取基金十大重仓股 (替代 Wind w.wset("fundholdings")).

    :param fund_codes: 基金代码列表 (bare code 如 ['000979', '519702'])
    :param rpt_date: 报告期 YYYYMMDD, 如 '20251231'. 为 None 时自动推算最新季末.
    :return: {
        'holdings_map':  {fund_code: [(stock_code, stock_name), ...]},
        'holdings_ratio': {fund_code: {stock_code: ratio_pct}},
        'report_date': 实际使用的报告期
    }
    """
    api = _get_api()

    # 自动推算最新报告期 (往前推 2 个季度确保披露)
    if rpt_date is None:
        today = datetime.today()
        candidates = []
        dt = today
        for _ in range(4):
            m = dt.month
            q = (m - 1) // 3
            if q == 0:
                rd = f"{dt.year - 1}1231"
            elif q == 1:
                rd = f"{dt.year}0331"
            elif q == 2:
                rd = f"{dt.year}0630"
            else:
                rd = f"{dt.year}0930"
            if rd not in candidates:
                candidates.append(rd)
            dt = datetime.strptime(rd, "%Y%m%d") - timedelta(days=1)
    else:
        candidates = [rpt_date]

    holdings_map = {}
    holdings_ratio = {}
    actual_rpt_date = candidates[0] if candidates else ''

    for code in fund_codes:
        ts_code = _wind_code_to_ts_code(code)
        bare = code.split('.')[0].zfill(6)
        found = False

        for rd in candidates:
            if found:
                break
            try:
                # fund_portfolio: 基金持仓明细
                df = api.fund_portfolio(
                    ts_code=ts_code,
                    ann_date=rd,
                    fields='ts_code,ann_date,end_date,symbol,mkv,stk_mkv_ratio'
                )
                # 如果 ann_date 匹配不到, 尝试 end_date 参数
                if df is None or df.empty:
                    df = api.fund_portfolio(
                        ts_code=ts_code,
                        end_date=rd,
                        fields='ts_code,ann_date,end_date,symbol,mkv,stk_mkv_ratio'
                    )

                if df is not None and not df.empty:
                    # ★ 关键: fund_portfolio 返回所有历史季度的持仓
                    # 必须先过滤到最新一期 (end_date 最大值)
                    if 'end_date' not in df.columns:
                        # 请求时未包含 end_date，重新请求
                        df = api.fund_portfolio(
                            ts_code=ts_code,
                            end_date=rd,
                            fields='ts_code,ann_date,end_date,symbol,mkv,stk_mkv_ratio'
                        )
                    if df is not None and not df.empty and 'end_date' in df.columns:
                        latest_period = df['end_date'].max()
                        df = df[df['end_date'] == latest_period]

                    # stk_mkv_ratio 和 mkv 转数字
                    if 'mkv' in df.columns:
                        df['mkv'] = pd.to_numeric(df['mkv'], errors='coerce')
                    if 'stk_mkv_ratio' in df.columns:
                        df['stk_mkv_ratio'] = pd.to_numeric(df['stk_mkv_ratio'], errors='coerce')

                    # 按持仓市值降序, 取 top 10
                    df = df.sort_values('mkv', ascending=False).head(10)

                    stk_list = []
                    ratio_dict = {}
                    seen_codes = set()
                    for _, row in df.iterrows():
                        stk_symbol = str(row.get('symbol', '')).strip()
                        if not stk_symbol:
                            continue
                        # Tushare symbol 已带后缀 (如 601899.SH), 直接使用
                        stk_wind = stk_symbol

                        # 去重
                        if stk_wind in seen_codes:
                            continue
                        seen_codes.add(stk_wind)

                        stk_list.append((stk_wind, ''))
                        ratio = row.get('stk_mkv_ratio')
                        if ratio is not None and str(ratio) != 'nan':
                            try:
                                # Tushare stk_mkv_ratio 已经是百分比 (10.36 = 10.36%)
                                ratio_dict[stk_wind] = round(float(ratio), 2)
                            except (ValueError, TypeError):
                                pass

                    if stk_list:
                        holdings_map[bare] = stk_list
                        holdings_ratio[bare] = ratio_dict
                        actual_rpt_date = rd
                        found = True
                        logging.info(f"  [Tushare] {bare} 重仓股: {len(stk_list)} 只 (报告期={rd})")

                time.sleep(0.25)  # fund_portfolio 频率限制较严
            except Exception as e:
                logging.warning(f"  [Tushare] {bare} 重仓穿透异常 (rd={rd}): {e}")
                time.sleep(0.5)

        if not found:
            logging.warning(f"  [Tushare] {bare} 所有报告期均无重仓数据")

    return {
        'holdings_map': holdings_map,
        'holdings_ratio': holdings_ratio,
        'report_date': actual_rpt_date,
    }


# ═══════════════════════════════════════════
# 7. 实时指数行情 (替代 w.wsq rt_last,rt_pct_chg)
# ═══════════════════════════════════════════

def fetch_realtime_index(index_codes: list) -> list:
    """
    获取指数实时行情 (替代 Wind w.wsq).
    使用 Tushare rt_idx_k 接口。

    :param index_codes: 指数代码列表 (Wind 格式如 ['000001.SH', '000300.SH'])
    :return: [{'code': '000001.SH', 'close': 3200.5, 'pct_chg': 1.23, 'pre_close': 3161.6}, ...]
    """
    api = _get_api()
    results = []

    # 批量获取: rt_idx_k 支持逗号分隔多个代码
    # 过滤掉非 A 股指数 (如 HSI.HI)
    a_codes = [c for c in index_codes if c.endswith('.SH') or c.endswith('.SZ')]
    hk_codes = [c for c in index_codes if c not in a_codes]

    if a_codes:
        try:
            codes_str = ','.join(a_codes)
            df = api.rt_idx_k(ts_code=codes_str, fields='ts_code,name,close,pre_close')
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    ts_code = str(row.get('ts_code', '')).strip()
                    close = row.get('close')
                    pre_close = row.get('pre_close')
                    pct = None
                    if close is not None and pre_close is not None and pre_close != 0:
                        try:
                            pct = round((float(close) / float(pre_close) - 1.0) * 100, 2)
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass
                    results.append({
                        'code': ts_code,
                        'close': round(float(close), 2) if close is not None else None,
                        'pct_chg': pct,
                        'pre_close': round(float(pre_close), 2) if pre_close is not None else None,
                    })
                logging.info(f"  [Tushare] rt_idx_k 实时行情: {len(results)} 个指数")
        except Exception as e:
            logging.warning(f"  [Tushare] rt_idx_k 异常: {e}")

    # 港股指数暂用空占位
    for hk in hk_codes:
        results.append({
            'code': hk,
            'close': None,
            'pct_chg': None,
            'pre_close': None,
        })

    return results


