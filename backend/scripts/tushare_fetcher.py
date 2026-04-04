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


def _wind_code_to_ts_code(wind_code: str) -> str:
    """
    Wind 基金代码 → Tushare 基金代码
    例: '000979.OF' → '000979.OF',  '000979' → '000979.OF'
    """
    c = str(wind_code).strip()
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

    :param codes: 基金代码列表 (bare code, 如 ['000979', '001203'])
    :param start_date: 开始日期 'YYYY-MM-DD'
    :param end_date: 结束日期 'YYYY-MM-DD'
    :return: DataFrame, index=日期, columns=bare_code, values=复权净值
    """
    api = _get_api()
    all_dfs = {}
    start_ts = start_date.replace('-', '')
    end_ts = end_date.replace('-', '')

    for code in codes:
        ts_code = _wind_code_to_ts_code(code)
        bare = code.split('.')[0].zfill(6)
        try:
            # Tushare fund_nav: 返回 ann_date, nav, accum_nav, adj_nav
            df = api.fund_nav(
                ts_code=ts_code,
                start_date=start_ts,
                end_date=end_ts,
                fields='ann_date,adj_nav'
            )
            if df is not None and not df.empty:
                df['ann_date'] = pd.to_datetime(df['ann_date'])
                df = df.sort_values('ann_date').drop_duplicates(subset='ann_date', keep='last')
                df = df.set_index('ann_date')
                all_dfs[bare] = df['adj_nav'].astype(float)
                logging.info(f"  [Tushare] {bare} NAV 获取成功: {len(df)} 天")
            else:
                logging.warning(f"  [Tushare] {bare} NAV 为空")
            time.sleep(0.12)  # Tushare 频率限制: 每分钟200次
        except Exception as e:
            logging.warning(f"  [Tushare] {bare} NAV 异常: {e}")
            time.sleep(0.5)

    if not all_dfs:
        return pd.DataFrame()

    result = pd.DataFrame(all_dfs)
    result.index = pd.to_datetime(result.index)
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
            if df is not None and not df.empty:
                row = df.iloc[0]
                rows.append({
                    'code': bare,
                    'SEC_NAME': row.get('name', bare),
                    'FUND_TYPE': row.get('fund_type', ''),
                    'FUND_INVESTTYPE': row.get('fund_type', ''),  # Tushare fund_type ≈ Wind investtype
                    'FUND_CORP_FUNDMANAGEMENTCOMPANY': row.get('management', ''),
                    'FUND_FUNDMANAGER': row.get('manager', ''),
                    'FUND_FUNDMANAGER_STARTDATE': row.get('found_date', ''),
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
