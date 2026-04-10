#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户持仓同步脚本 — 纯 Tushare Pro 数据源。

用法: python scripts/sync_client_holdings.py <codes_comma_sep> <output_csv_path>
输出: JSON 到 stdout (供 Streamlit 解析)

扩展数据:
  - 基金净值 (2020-01-01 至今)
  - 基金元数据 (名称/类型/投资类型/管理公司)
  - 基金经理变更信息 (现任经理 + 任职起始日)
  - 十大重仓股穿透 + 底层资产昨日涨跌幅
"""
import sys
import os
import json
import logging
import time
import glob

# Since this script was moved to backend/scripts, but the services are still in 20260325/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_OLD_SERVICES_ROOT = os.path.join(_PROJECT_ROOT, "20260325")
sys.path.insert(0, _OLD_SERVICES_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)

BATCH_SIZE = 5
MAX_SYNC_FILES_KEEP = 3  # 保留最新的 N 份 sync 文件, 自动清理旧文件


def _cleanup_old_sync_files(data_dir: str):
    """清理旧的 sync_*.csv 文件, 只保留最新的 MAX_SYNC_FILES_KEEP 份。"""
    try:
        # 找所有 sync_*.csv (不含 meta)
        nav_files = sorted(
            glob.glob(os.path.join(data_dir, "sync_*.csv")),
            key=os.path.getmtime, reverse=True
        )
        nav_only = [f for f in nav_files if '_meta' not in f]

        if len(nav_only) <= MAX_SYNC_FILES_KEEP:
            return

        to_delete = nav_only[MAX_SYNC_FILES_KEEP:]
        for f in to_delete:
            try:
                os.remove(f)
                # 同时删除对应的 _meta.csv
                meta_f = f.replace('.csv', '_meta.csv')
                if os.path.exists(meta_f):
                    os.remove(meta_f)
                logging.info(f"  🗑️ 清理旧 sync 文件: {os.path.basename(f)}")
            except Exception as e:
                logging.warning(f"  ⚠️ 清理失败 {os.path.basename(f)}: {e}")

        logging.info(f"  ✅ 已清理 {len(to_delete)} 份旧 sync 文件, 保留最新 {MAX_SYNC_FILES_KEEP} 份")
    except Exception as e:
        logging.warning(f"  ⚠️ sync 文件清理异常 (非致命): {e}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python sync_client_holdings.py <codes_comma_sep> <output_csv_path>")
        sys.exit(1)

    codes_str = sys.argv[1]
    output_path = sys.argv[2]
    codes = [c.strip() for c in codes_str.split(',') if c.strip()]

    if not codes:
        _emit_result({"status": "error", "detail": "未提供有效的基金代码"})
        sys.exit(1)

    try:
        import pandas as pd
        from datetime import datetime, timedelta

        tushare_used = False

        # [2026-04-10] Wind API 已永久移除, 纯 Tushare 模式
        wind_available = False
        w = None

        logging.info(f"🔄 纯 Tushare 模式, 开始处理 {len(codes)} 只基金...")

        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = '2020-01-01'
        out_dir = os.path.dirname(output_path)
        os.makedirs(out_dir, exist_ok=True)

        # 自动清理旧 sync 文件 (仅保留最新 3 份)
        _cleanup_old_sync_files(out_dir)

        # ══════════════════════════════════════════
        # 1. 下载复权净值 (Tushare 主路径)
        # ══════════════════════════════════════════
        all_nav_dfs = []
        failed_codes = []

        logging.info("📡 Tushare 主路径: 下载复权净值...")
        print("__TUSHARE_STARTED__", flush=True)
        try:
            from tushare_fetcher import fetch_fund_nav
            bare_codes = [c.split('.')[0].zfill(6) for c in codes]
            df_ts_nav = fetch_fund_nav(bare_codes, start_date, end_date)
            if df_ts_nav is not None and not df_ts_nav.empty:
                all_nav_dfs.append(df_ts_nav)
                tushare_used = True
                logging.info(f"  ✅ Tushare NAV: {len(df_ts_nav.columns)} 只基金, {len(df_ts_nav)} 天")
            else:
                logging.warning("  ⚠️ Tushare NAV 返回空")
        except Exception as e_ts:
            logging.warning(f"  ⚠️ Tushare NAV 异常: {e_ts}")

        if not all_nav_dfs:
            raise RuntimeError("Tushare 无法获取任何净值数据")
        df_nav = pd.concat(all_nav_dfs, axis=1)
        df_nav = df_nav.loc[:, ~df_nav.columns.duplicated(keep='first')]

        # 清理全 NaN 的列
        df_nav = df_nav.dropna(how='all', axis=1)
        if df_nav.empty:
            raise RuntimeError("所有数据源均无法获取有效 NAV 数据 (所有列全 NaN)")
        success_codes = list(df_nav.columns)

        # ══════════════════════════════════════════
        # ══════════════════════════════════════════
        # 2. 基金元数据 (Tushare 主路径)
        # ══════════════════════════════════════════
        def _ensure_of_suffix(code):
            c = str(code).strip()
            if '.' not in c:
                return c + '.OF'
            return c
        _wss_codes = [_ensure_of_suffix(c) for c in success_codes]

        # ── Tushare 主路径 ──
        df_meta = pd.DataFrame()
        try:
            from tushare_fetcher import fetch_fund_metadata
            df_ts_meta = fetch_fund_metadata(success_codes)
            if df_ts_meta is not None and not df_ts_meta.empty:
                df_meta = df_ts_meta
                tushare_used = True
                logging.info(f"  ✅ Tushare 元数据: {len(df_meta)} 只基金")
        except Exception as e_ts:
            logging.warning(f"  ⚠️ Tushare 元数据异常: {e_ts}")

        # ── Wind 可选增强: 补充完整字段 (经理信息/基金分类) ──
        _FULL_FIELDS = ("sec_name,fund_type,fund_investtype,fund_corp_fundmanagementcompany,"
                        "fund_fundmanager,fund_fundmanager_startdate,"
                        "fund_fundmanager_totalfundno")
        if wind_available:
            # 识别 Tushare 缺失或名称为空的基金
            _meta_missing = []
            for c in success_codes:
                if df_meta.empty or c not in df_meta.index:
                    _meta_missing.append(c)
                elif 'SEC_NAME' in df_meta.columns:
                    name_val = df_meta.loc[c, 'SEC_NAME']
                    if pd.isna(name_val) or str(name_val).strip() in ('', 'nan', 'None'):
                        _meta_missing.append(c)

            if _meta_missing:
                logging.info(f"🔄 Wind 增强元数据: {len(_meta_missing)} 只基金...")
                _missing_wss = [_ensure_of_suffix(c) for c in _meta_missing]
                all_meta_dfs = []
                for batch_i in range(0, len(_missing_wss), BATCH_SIZE):
                    batch = _missing_wss[batch_i:batch_i + BATCH_SIZE]
                    try:
                        meta_data = w.wss(','.join(batch), _FULL_FIELDS)
                        if meta_data.ErrorCode == 0:
                            df_mb = pd.DataFrame(meta_data.Data, index=meta_data.Fields, columns=meta_data.Codes).T
                            all_meta_dfs.append(df_mb)
                        time.sleep(0.3)
                    except Exception as e:
                        logging.warning(f"  ⚠️ Wind 增强元数据异常: {e}")

                if all_meta_dfs:
                    df_wind_meta = pd.concat(all_meta_dfs)
                    df_wind_meta.index = [str(c).split('.')[0].zfill(6) for c in df_wind_meta.index]
                    df_wind_meta.columns = [str(col).upper() for col in df_wind_meta.columns]
                    if df_meta.empty:
                        df_meta = df_wind_meta
                    else:
                        for idx in df_wind_meta.index:
                            if idx not in df_meta.index:
                                df_meta = pd.concat([df_meta, df_wind_meta.loc[[idx]]])
                            else:
                                for col in df_wind_meta.columns:
                                    existing = df_meta.loc[idx, col] if col in df_meta.columns else None
                                    if existing is None or pd.isna(existing) or str(existing).strip() in ('', 'nan'):
                                        if col not in df_meta.columns:
                                            df_meta[col] = pd.NA
                                        df_meta.loc[idx, col] = df_wind_meta.loc[idx, col]
                    logging.info(f"  ✅ Wind 增强元数据完成: {len(df_wind_meta)} 只")

        # 归一化
        if not df_meta.empty:
            df_meta.index = [str(c).split('.')[0].zfill(6) for c in df_meta.index]
            df_meta.columns = [str(col).upper() for col in df_meta.columns]

        # ══════════════════════════════════════════
        # 2.5 持仓综合分析表 — 全部直取 Wind API
        # ══════════════════════════════════════════
        logging.info("⭐ 拉取持仓综合分析表数据 (逐年回报/评级/排名)...")
        _summary_data = {}  # {code: {year: ret, ...}}

        # ── 2.5a 逐日历年基金收益率 — WSS 直接下载 (100% 对齐 Wind 终端) ──
        # w.wss(codes, "return_y", f"annualized=0;tradeDate={yr}1231") → 精确年度回报
        _current_year = datetime.today().year
        _years = list(range(2020, _current_year + 1))
        _trade_date_today = datetime.today().strftime('%Y%m%d')
        # 三年前日期 (用于 vol / mdd)
        _three_yr_ago = (datetime.today() - timedelta(days=3*365)).strftime('%Y%m%d')

        # --- 逐年回报: 批量 WSS ---
        for yr in _years if wind_available else []:
            yr_end = f"{yr}1231" if yr < _current_year else _trade_date_today
            try:
                res = w.wss(','.join(_wss_codes), "return_y",
                            f"tradeDate={yr_end}")
                if res.ErrorCode == 0 and res.Data and res.Data[0]:
                    _n_valid_yr = 0
                    for j, code in enumerate(_wss_codes):
                        bare = str(code).split('.')[0].zfill(6)
                        val = res.Data[0][j] if j < len(res.Data[0]) else None
                        if val is not None and str(val) != 'nan':
                            _summary_data.setdefault(bare, {})[f"ret_{yr}"] = float(val) / 100.0
                            _n_valid_yr += 1
                    logging.info(f"  ✅ {yr} 年度回报 WSS 完成 (有效值: {_n_valid_yr}/{len(_wss_codes)})")
                else:
                    logging.warning(f"  ⚠️ {yr} return_y ErrorCode={res.ErrorCode}")
            except Exception as e:
                logging.warning(f"  ⚠️ {yr} return_y 异常: {e}")
            time.sleep(0.1)

        # Wind 终端对齐: 使用 T-1 (昨日) 作为 tradeDate
        # 原因: Wind WSS 的 return_Xy 在 T 日盘中/盘后如果净值未更新,
        #       会使用 T-2 的净值计算, 导致与 Wind 终端显示不一致。
        #       T-1 确保使用最近一个完整交易日的净值。
        _t1_date = (datetime.today() - timedelta(days=1)).strftime('%Y%m%d')

        if wind_available:
            try:
                res = w.wss(','.join(_wss_codes),
                            "return_6m,return_1y,return_3y,return_5y,return_ytd",
                            f"annualized=0;tradeDate={_t1_date}")
                if res.ErrorCode == 0 and res.Data:
                    _rf = [f.upper() for f in (res.Fields if hasattr(res, 'Fields') else [])]
                    _field_map = {
                        'RETURN_6M': 'ret_6m', 'RETURN_1Y': 'ret_1y',
                        'RETURN_3Y': 'ret_3y', 'RETURN_5Y': 'ret_5y',
                        'RETURN_YTD': 'ret_ytd',
                    }
                    for fi, f_name in enumerate(_rf):
                        key = _field_map.get(f_name)
                        if key and fi < len(res.Data):
                            for j, code in enumerate(_wss_codes):
                                bare = str(code).split('.')[0].zfill(6)
                                val = res.Data[fi][j] if j < len(res.Data[fi]) else None
                                if val is not None and str(val) != 'nan':
                                    _summary_data.setdefault(bare, {})[key] = float(val) / 100.0
                    logging.info("  ✅ 6M/1Y/3Y/5Y/YTD WSS 完成")
            except Exception as e:
                logging.warning(f"  ⚠️ 周期收益率 WSS 异常: {e}")

        # --- 近三年年化波动率 + 最大回撤: WSS risk_stdevyearly + risk_maxdownside ---
        # risk_stdevyearly 对全部 .OF / .SH 基金均有效 (已验证)
        # risk_maxdownside2 对 .OF 返回 NaN, 改用 risk_maxdownside (已验证)
        if wind_available:
            try:
                res = w.wss(','.join(_wss_codes),
                            "risk_stdevyearly,risk_maxdownside",
                            f"startDate={_three_yr_ago};endDate={_trade_date_today};period=2;returnType=1;")
                if res.ErrorCode == 0 and res.Data:
                    _flds = [f.upper() for f in (res.Fields if hasattr(res, 'Fields') else ['RISK_STDEVYEARLY', 'RISK_MAXDOWNSIDE'])]
                    for fi, f_name in enumerate(_flds):
                        if fi >= len(res.Data):
                            continue
                        for j, code in enumerate(_wss_codes):
                            bare = str(code).split('.')[0].zfill(6)
                            val = res.Data[fi][j] if j < len(res.Data[fi]) else None
                            if val is not None and str(val) != 'nan':
                                if 'STDEV' in f_name:
                                    _summary_data.setdefault(bare, {})['vol_3y'] = float(val) / 100.0
                                elif 'MAXDOWN' in f_name:
                                    _summary_data.setdefault(bare, {})['max_dd_3y'] = abs(float(val)) / 100.0
                    logging.info("  ✅ 年化波动率(三年期) + 最大回撤(三年期) WSS 完成")
            except Exception as e:
                logging.warning(f"  ⚠️ vol/mdd WSS 异常: {e}")

        # ── 2.5a-Fallback: 如果 Wind 取不到周期/年度回报, 使用 df_nav 本地计算兜底 ──
        if not df_nav.empty:
            logging.info("  🔄 检查本地区间收益率兜底...")
            df_nav_daily = df_nav.copy()
            df_nav_daily.index = pd.to_datetime(df_nav_daily.index)
            # 根据最后一个交易日基准进行倒推
            _last_dt_overall = df_nav_daily.index.max()
            
            for code in df_nav_daily.columns:
                bare = str(code).split('.')[0].zfill(6)
                s = df_nav_daily[code].dropna()
                if s.empty: continue
                
                s_last_dt = s.index[-1]
                s_last_val = float(s.iloc[-1])
                s_dict = _summary_data.setdefault(bare, {})
                
                # 年度 return_y 兜底 (2020 至今)
                for yr in _years:
                    yr_key = f"ret_{yr}"
                    if yr_key not in s_dict:
                        try:
                            # 提取当年的数据
                            s_yr = s[s.index.year == yr]
                            if not s_yr.empty:
                                val_end = float(s_yr.iloc[-1])
                                # 提取上一年及以前的最后一天
                                s_prev = s[s.index.year < yr]
                                if not s_prev.empty:
                                    val_start = float(s_prev.iloc[-1])
                                    s_dict[yr_key] = (val_end / val_start) - 1.0
                        except Exception as e:
                            logging.warning(f"  ⚠️ {bare} ret_{yr} 兜底异常: {e}")
                
                # YTD 兜底
                if 'ret_ytd' not in s_dict:
                    try:
                        s_prev = s[s.index.year < s_last_dt.year]
                        if not s_prev.empty:
                            s_dict['ret_ytd'] = (s_last_val / float(s_prev.iloc[-1])) - 1.0
                    except Exception as e:
                        logging.warning(f"  ⚠️ {bare} ret_ytd 兜底异常: {e}")
                
                # 周期回报兜底 (6M, 1Y, 3Y, 5Y)
                # 使用 timedelta 做粗略计算 (182, 365, 1095, 1826)
                _cycle_map = [(182, 'ret_6m'), (365, 'ret_1y'), (1095, 'ret_3y'), (1826, 'ret_5y')]
                for days, key in _cycle_map:
                    if key not in s_dict:
                        try:
                            ago_dt = s_last_dt - timedelta(days=days)
                            past_vals = s[:ago_dt.strftime('%Y-%m-%d')]
                            if not past_vals.empty:
                                s_dict[key] = (s_last_val / float(past_vals.iloc[-1])) - 1.0
                        except Exception as e:
                            logging.warning(f"  ⚠️ {bare} {key} 兜底异常: {e}")
                
                # 波动率与回撤兜底 (3年)
                if 'vol_3y' not in s_dict or 'max_dd_3y' not in s_dict:
                    try:
                        dt_3y = s_last_dt - timedelta(days=1095)
                        s_3y = s[dt_3y.strftime('%Y-%m-%d'):]
                        if len(s_3y) > 100:
                            if 'vol_3y' not in s_dict:
                                s_dict['vol_3y'] = float(s_3y.pct_change().std() * (252**0.5))
                            if 'max_dd_3y' not in s_dict:
                                s_dict['max_dd_3y'] = float(abs((s_3y / s_3y.cummax() - 1.0).min()))
                    except Exception as e:
                        logging.warning(f"  ⚠️ {bare} vol/mdd 兜底异常: {e}")

        # --- 诊断统计 ---
        _got_ret = sum(1 for c, v in _summary_data.items() if any(k.startswith("ret_") for k in v))
        _got_vol = sum(1 for c, v in _summary_data.items() if 'vol_3y' in v)
        _got_mdd = sum(1 for c, v in _summary_data.items() if 'max_dd_3y' in v)
        logging.info(f"  📊 综合分析表 (Wind+本地): {_got_ret} 只有收益数据, {_got_vol} 只有 vol, {_got_mdd} 只有 mdd")

        # ── 2.5-Final: 如果 Wind WSS + 本地 NAV 兜底后仍缺少数据, 强制重新用 df_nav 计算 ──
        if _got_ret == 0 and not df_nav.empty:
            logging.warning("⚠️ Wind WSS 返回全 NaN 且本地兜底未生效, 强制二次 NAV 计算...")
            _df_force = df_nav.copy()
            _df_force.index = pd.to_datetime(_df_force.index)
            for code in _df_force.columns:
                bare = str(code).split('.')[0].zfill(6)
                s = _df_force[code].dropna()
                if s.empty or len(s) < 20:
                    logging.warning(f"  ⚠️ {bare} NAV 数据不足 ({len(s)} 天), 跳过")
                    continue
                s_dict = _summary_data.setdefault(bare, {})
                s_last_dt = s.index[-1]
                s_last_val = float(s.iloc[-1])

                # YTD
                try:
                    s_prev_yr = s[s.index.year < s_last_dt.year]
                    if not s_prev_yr.empty:
                        s_dict['ret_ytd'] = (s_last_val / float(s_prev_yr.iloc[-1])) - 1.0
                except Exception:
                    pass

                # 1Y
                try:
                    ago_1y = s_last_dt - timedelta(days=365)
                    past_1y = s[:ago_1y.strftime('%Y-%m-%d')]
                    if not past_1y.empty:
                        s_dict['ret_1y'] = (s_last_val / float(past_1y.iloc[-1])) - 1.0
                except Exception:
                    pass

                # 6M
                try:
                    ago_6m = s_last_dt - timedelta(days=182)
                    past_6m = s[:ago_6m.strftime('%Y-%m-%d')]
                    if not past_6m.empty:
                        s_dict['ret_6m'] = (s_last_val / float(past_6m.iloc[-1])) - 1.0
                except Exception:
                    pass

                # 年度 ret
                for yr in _years:
                    yr_key = f"ret_{yr}"
                    if yr_key not in s_dict:
                        try:
                            s_yr = s[s.index.year == yr]
                            s_prev = s[s.index.year < yr]
                            if not s_yr.empty and not s_prev.empty:
                                s_dict[yr_key] = (float(s_yr.iloc[-1]) / float(s_prev.iloc[-1])) - 1.0
                        except Exception:
                            pass

                # Vol + MDD (三年)
                try:
                    dt_3y = s_last_dt - timedelta(days=1095)
                    s_3y = s[dt_3y.strftime('%Y-%m-%d'):]
                    if len(s_3y) > 60:
                        if 'vol_3y' not in s_dict:
                            s_dict['vol_3y'] = float(s_3y.pct_change().std() * (252**0.5))
                        if 'max_dd_3y' not in s_dict:
                            s_dict['max_dd_3y'] = float(abs((s_3y / s_3y.cummax() - 1.0).min()))
                except Exception:
                    pass

            _got_ret2 = sum(1 for c, v in _summary_data.items() if any(k.startswith("ret_") for k in v))
            _got_vol2 = sum(1 for c, v in _summary_data.items() if 'vol_3y' in v)
            logging.info(f"  📊 强制二次计算后: {_got_ret2} 只有收益数据, {_got_vol2} 只有 vol")

        # ── 2.5b 排名 / 基准代码 ──
        _RATING_FIELDS = (
            "fund_benchindexcode,"
            "periodreturnranking_y"
        )
        _trade_date = datetime.today().strftime('%Y%m%d')
        _rating_opts = f"tradeDate={_trade_date};fundType=1;"
        for batch_i in range(0, len(_wss_codes), BATCH_SIZE) if wind_available else []:
            batch = _wss_codes[batch_i:batch_i + BATCH_SIZE]
            try:
                logging.info(f"  ⏳ 排名批次 codes={batch[:2]}...")
                res = w.wss(','.join(batch), _RATING_FIELDS, _rating_opts)
                logging.info(f"  ↪ 排名 ErrorCode={res.ErrorCode}, Fields={getattr(res, 'Fields', [])}")
                if res.ErrorCode == 0 and res.Data:
                    for j, code in enumerate(batch):
                        bare = str(code).split('.')[0].zfill(6)
                        d = _summary_data.setdefault(bare, {})
                        # fund_benchmark_windcode
                        if len(res.Data) > 0 and res.Data[0][j]:
                            d['benchmark_code'] = str(res.Data[0][j])
                        # periodreturnranking_y → 直接存储 "425/952" 格式
                        if len(res.Data) > 1 and res.Data[1][j] is not None:
                            d['peer_ranking'] = str(res.Data[1][j])
                time.sleep(0.3)
            except Exception as e:
                logging.warning(f"  ⚠️ 排名批次异常: {e}")
        logging.info("  ✅ 排名/基准完成")

        # ── 2.5c 基准指数逐年回报 (Wind wss NAV_adj_return1 on benchmark) ──
        _bm_codes_set = set()
        for bare, d in _summary_data.items():
            bm = d.get('benchmark_code', '')
            _first = str(bm).split('*')[0].split('+')[0].strip()
            if '.' in _first and len(_first) < 20:
                _bm_codes_set.add(_first)
                d['benchmark_code_clean'] = _first
        _bm_codes_list = list(_bm_codes_set)

        _bm_annual = {}  # {bm_code: {year: ret}}
        _wsd_end = datetime.today().strftime('%Y%m%d')  # 基准行情截止日期
        if _bm_codes_list and wind_available:
            logging.info(f"📊 拉取 {len(_bm_codes_list)} 个基准指数逐年回报...")
            for bm_code in _bm_codes_list:
                try:
                    r = w.wsd(bm_code, "close", "2019-12-15", _wsd_end, "")
                    if r.ErrorCode == 0 and r.Data and r.Data[0] and r.Times:
                        # 找每年最后交易日 close
                        yr_end = {}
                        for i, t in enumerate(r.Times):
                            v = r.Data[0][i]
                            if v is not None:
                                yr_key = t.year if hasattr(t, 'year') else int(str(t)[:4])
                                yr_end[yr_key] = float(v)
                        for yr in _years:
                            if yr in yr_end and (yr - 1) in yr_end and yr_end[yr - 1] > 0:
                                _bm_annual.setdefault(bm_code, {})[yr] = yr_end[yr] / yr_end[yr - 1] - 1.0
                        logging.info(f"  ✅ 基准 {bm_code} 逐年回报完成")
                    else:
                        logging.warning(f"  ⚠️ 基准 {bm_code} close Err={r.ErrorCode}")
                except Exception as e:
                    logging.warning(f"  ⚠️ 基准 {bm_code} close 异常: {e}")
                time.sleep(0.1)
            logging.info("  ✅ 基准指数逐年回报完成")

        # 将基准逐年回报写入 _summary_data
        for bare, d in _summary_data.items():
            bm = d.get('benchmark_code_clean', '')
            if bm and bm in _bm_annual:
                for yr, ret in _bm_annual[bm].items():
                    d[f"bm_ret_{yr}"] = ret

        # ── 诊断日志 ──
        logging.info(f"  📊 _summary_data 共 {len(_summary_data)} 只基金")
        for _sk, _sv in list(_summary_data.items())[:2]:
            logging.info(f"    样本 {_sk}: {list(_sv.keys())}")
        # ── 保存为 JSON ──
        _summary_path = os.path.join(out_dir, 'client_fund_summary.json')
        with open(_summary_path, 'w', encoding='utf-8') as f:
            json.dump(_summary_data, f, ensure_ascii=False, indent=2)
        logging.info(f"  ✅ 持仓综合分析表数据已保存: {_summary_path}")


        # ══════════════════════════════════════════
        # 3. 穿透十大重仓 (Tushare 主路径 + Wind 增强)
        # ══════════════════════════════════════════
        logging.info("🔬 穿透十大重仓...")
        # 自动推算最新报告期 (上季末)
        today = datetime.today()
        _q = (today.month - 1) // 3
        if _q == 0:
            rpt_date = f"{today.year - 1}1231"
        else:
            rpt_date = f"{today.year}{_q * 3:02d}{[31,30,30,31][_q-1]:02d}"
        # 往前再推一期以确保数据已披露
        _rpt_dt = datetime.strptime(rpt_date, "%Y%m%d")
        if (today - _rpt_dt).days < 60:
            _rpt_dt = _rpt_dt - timedelta(days=90)
            _q2 = (_rpt_dt.month - 1) // 3
            if _q2 == 0:
                rpt_date = f"{_rpt_dt.year - 1}1231"
            else:
                rpt_date = f"{_rpt_dt.year}{_q2 * 3:02d}{[31,30,30,31][_q2-1]:02d}"

        logging.info(f"  报告期: {rpt_date}")
        holdings_map = {}   # {fund_code: [(stock_code, stock_name), ...]}
        holdings_ratio = {}  # {fund_code: {stock_code: hold_ratio}}

        # ── Tushare 主路径: fund_portfolio ──
        try:
            from tushare_fetcher import fetch_fund_portfolio
            ts_portfolio = fetch_fund_portfolio(success_codes, rpt_date)
            if ts_portfolio:
                holdings_map.update(ts_portfolio.get('holdings_map', {}))
                holdings_ratio.update(ts_portfolio.get('holdings_ratio', {}))
                if ts_portfolio.get('report_date'):
                    rpt_date = ts_portfolio['report_date']
                logging.info(f"  ✅ Tushare 重仓穿透: {len(holdings_map)} 只基金有数据")
                tushare_used = True
        except Exception as e_ts:
            logging.warning(f"  ⚠️ Tushare 重仓穿透异常: {e_ts}")

        # 构建报告期候选列表 (最新→递减)
        def _build_rpt_dates():
            """生成最近 3 个季末报告期"""
            _dates = []
            _dt = today
            for _ in range(4):  # 最多回溯 4 个季度
                _m = _dt.month
                _q = (_m - 1) // 3
                if _q == 0:
                    _rd = f"{_dt.year - 1}1231"
                elif _q == 1:
                    _rd = f"{_dt.year}0331"
                elif _q == 2:
                    _rd = f"{_dt.year}0630"
                else:
                    _rd = f"{_dt.year}0930"
                if _rd not in _dates:
                    _dates.append(_rd)
                _dt = datetime.strptime(_rd, "%Y%m%d") - timedelta(days=1)
            return _dates

        _rpt_candidates = _build_rpt_dates()
        logging.info(f"  报告期候选: {_rpt_candidates}")

        # ── Wind 可选增强: 补充 Tushare 缺失的基金持仓 ──
        _funds_missing_ts = [c for c in success_codes if c not in holdings_map]
        if _funds_missing_ts and wind_available:
            logging.info(f"🔄 Wind 增强: 补充 {len(_funds_missing_ts)} 只基金持仓穿透...")
            for fund_code in _funds_missing_ts:
                if fund_code in holdings_map:
                    continue
                _fc_wss = fund_code + '.OF' if '.' not in fund_code else fund_code
                _found = False

                try:
                    _all_params = []
                    for _rd in _rpt_candidates:
                        _dash = f"{_rd[:4]}-{_rd[4:6]}-{_rd[6:]}"
                        _all_params.append(
                            f"fundcode={_fc_wss};rptdate={_rd};"
                            f"field=wind_code,stock_name,proportion"
                        )
                        _all_params.append(
                            f"fundcode={_fc_wss};rptdate={_dash};"
                            f"field=wind_code,stock_name,proportion"
                        )

                    for _param in _all_params:
                        if _found:
                            break
                        res = w.wset("fundholdings", _param)
                        if res.ErrorCode == 0 and res.Data and res.Data[0]:
                            _codes = res.Data[0] if res.Data[0] else []
                            _names = res.Data[1] if len(res.Data) > 1 else [None] * len(_codes)
                            _ratios = res.Data[2] if len(res.Data) > 2 else [None] * len(_codes)
                            for i in range(min(10, len(_codes))):
                                stk_code = _codes[i]
                                stk_name = _names[i] if i < len(_names) else None
                                ratio = _ratios[i] if i < len(_ratios) else None
                                if stk_code and str(stk_code).strip():
                                    _sc = str(stk_code).strip()
                                    _sn = str(stk_name or '').strip()
                                    holdings_map.setdefault(fund_code, []).append((_sc, _sn))
                                    if ratio is not None:
                                        try:
                                            holdings_ratio.setdefault(fund_code, {})[_sc] = float(ratio)
                                        except (ValueError, TypeError):
                                            pass
                            if holdings_map.get(fund_code):
                                _found = True
                                _used_rd = _param.split('rptdate=')[1].split(';')[0]
                                logging.info(f"  ✅ Wind w.wset {fund_code}: {len(holdings_map[fund_code])} 只重仓股 (报告期={_used_rd})")
                    time.sleep(0.15)
                except Exception as e:
                    logging.warning(f"  ⚠️ Wind w.wset {fund_code} 异常: {e}")

        # ── 方法 A2: w.wsd(top10_stockwindcode) — 备用 API 端点 ──
        # 参考 MultiSourceFundDiagnosis: 不同的 Wind 字段, 可能在 w.wset 失败时可用
        _funds_missing_a2 = [c for c in success_codes if c not in holdings_map]
        if _funds_missing_a2 and wind_available:
            logging.info(f"  🔄 方法A2: 尝试 w.wsd(top10_stockwindcode) 对 {len(_funds_missing_a2)} 只基金...")
            for fund_code in _funds_missing_a2:
                _fc_wsd = fund_code + '.OF' if '.' not in fund_code else fund_code
                try:
                    res = w.wsd(
                        _fc_wsd,
                        "prt_topstockwindcode,prt_topstockname",
                        rpt_date, rpt_date, ""
                    )
                    if res is not None and res.ErrorCode == 0 and res.Data:
                        # wsd 返回单只基金多字段: Data[0]=codes, Data[1]=names
                        _raw_codes = res.Data[0] if res.Data[0] else []
                        _raw_names = res.Data[1] if len(res.Data) > 1 and res.Data[1] else []
                        if not isinstance(_raw_codes, list):
                            _raw_codes = [_raw_codes]
                        if not isinstance(_raw_names, list):
                            _raw_names = [_raw_names]
                        _added = 0
                        for i in range(len(_raw_codes)):
                            _sc = _raw_codes[i]
                            _sn = _raw_names[i] if i < len(_raw_names) else ''
                            if _sc and str(_sc).strip() and str(_sc).strip() not in ('None', 'nan', ''):
                                holdings_map.setdefault(fund_code, []).append(
                                    (str(_sc).strip(), str(_sn or '').strip())
                                )
                                _added += 1
                        if _added > 0:
                            logging.info(f"  ✅ w.wsd A2 {fund_code}: {_added} 只重仓股")
                    time.sleep(0.15)
                except Exception as e:
                    logging.warning(f"  ⚠️ w.wsd A2 {fund_code} 异常: {e}")

        # ── 方法 B 回退: w.wss(order=1..10) — 逐只查询 top10 ──
        _funds_missing = [c for c in success_codes if c not in holdings_map]
        if _funds_missing and wind_available:
            logging.info(f"  🔄 {len(_funds_missing)} 只基金仍无持仓数据，回退 w.wss(order=1..10)...")
            for order in range(1, 11):
                try:
                    for batch_i in range(0, len(_funds_missing), BATCH_SIZE):
                        batch = _funds_missing[batch_i:batch_i + BATCH_SIZE]
                        # w.wss 需要 .OF 后缀
                        batch_of = [c + '.OF' if '.' not in c else c for c in batch]
                        opts = f"rptDate={rpt_date};order={order}"
                        res = w.wss(','.join(batch_of), "prt_topstockwindcode,prt_topstockname", opts)
                        if res.ErrorCode == 0 and res.Data:
                            for j, code in enumerate(batch):
                                stk_code = res.Data[0][j] if res.Data[0][j] else None
                                stk_name = res.Data[1][j] if len(res.Data) > 1 and res.Data[1][j] else None
                                if stk_code and str(stk_code).strip():
                                    holdings_map.setdefault(code, []).append(
                                        (str(stk_code).strip(), str(stk_name or '').strip())
                                    )
                        time.sleep(0.15)
                except Exception as e:
                    logging.warning(f"  重仓 order={order} 异常: {e}")

        # ── 统计各方法命中情况 ──
        _n_with_holdings = sum(1 for c in success_codes if c in holdings_map)
        _n_without = len(success_codes) - _n_with_holdings
        logging.info(f"  📊 持仓穿透汇总: {_n_with_holdings}/{len(success_codes)} 只有重仓数据, {_n_without} 只无数据")

        # ══════════════════════════════════════════
        # 4. 汇总底层资产 → 拉取过去 7 天涨跌幅 (Tushare 主路径)
        # ══════════════════════════════════════════
        all_underlying = set()
        for fund_code, stk_list in holdings_map.items():
            for stk_code, _ in stk_list:
                all_underlying.add(stk_code)

        underlying_pct = {}
        _und_list = list(all_underlying)
        _7d_ago = (today - timedelta(days=10)).strftime('%Y%m%d')
        _today_str = today.strftime('%Y%m%d')

        # ── Tushare 主路径 ──
        if all_underlying:
            logging.info(f"📊 Tushare: 拉取 {len(all_underlying)} 只底层资产行情...")
            try:
                from tushare_fetcher import fetch_stock_pct_chg
                ts_stock_result = fetch_stock_pct_chg(_und_list, _7d_ago, _today_str)
                for stk, data in ts_stock_result.items():
                    if data.get('pct_chg', 0.0) != 0.0 or data.get('daily_pcts'):
                        underlying_pct[stk] = data
                logging.info(f"  ✅ Tushare 底层行情: {len(underlying_pct)}/{len(_und_list)} 只")
                tushare_used = True
            except Exception as e_ts:
                logging.warning(f"  ⚠️ Tushare 底层行情异常: {e_ts}")

        # ── Wind 可选增强: 补充 Tushare 缺失的底层股票 ──
        _stk_missing = [stk for stk in _und_list if stk not in underlying_pct]
        if _stk_missing and wind_available:
            logging.info(f"🔄 Wind 增强: 补充 {len(_stk_missing)} 只底层资产行情...")

            # ── Wind wss 获取名称+涨跌幅 ──
            for batch_i in range(0, len(_stk_missing), BATCH_SIZE * 2):
                batch = _stk_missing[batch_i:batch_i + BATCH_SIZE * 2]
                try:
                    res = w.wss(','.join(batch), "sec_name,pct_chg")
                    if res.ErrorCode == 0 and res.Data:
                        for j, stk in enumerate(batch):
                            _nm = res.Data[0][j] if res.Data[0][j] else stk
                            _pc = res.Data[1][j] if len(res.Data) > 1 and res.Data[1][j] is not None else 0.0
                            try:
                                _pc = float(_pc)
                            except (ValueError, TypeError):
                                _pc = 0.0
                            underlying_pct[stk] = {
                                'name': str(_nm), 'pct_chg': _pc,
                                'max_drop_7d': _pc, 'drop_date': '',
                            }
                    time.sleep(0.15)
                except Exception as e:
                    logging.warning(f"  Wind 底层行情 wss 异常: {e}")

            # ── Wind wsd 补充 7 天逐日涨跌幅 ──
            _drop_count = 0
            for stk in _stk_missing:
                try:
                    r7 = w.wsd(stk, "pct_chg", _7d_ago, _today_str, "")
                    if r7.ErrorCode == 0 and r7.Data and r7.Data[0]:
                        _pcts = r7.Data[0] if isinstance(r7.Data[0], list) else [r7.Data[0]]
                        _valid = [(i, float(p)) for i, p in enumerate(_pcts) if p is not None and str(p) != 'nan']
                        if _valid:
                            _mi, _mv = min(_valid, key=lambda x: x[1])
                            if stk in underlying_pct:
                                underlying_pct[stk]['max_drop_7d'] = _mv
                                underlying_pct[stk]['daily_pcts'] = [float(p) if p is not None and str(p) != 'nan' else None for p in _pcts]
                                if hasattr(r7, 'Times') and r7.Times and _mi < len(r7.Times):
                                    _d = r7.Times[_mi]
                                    underlying_pct[stk]['drop_date'] = _d.strftime('%Y-%m-%d') if hasattr(_d, 'strftime') else str(_d)
                                _drop_count += 1
                except Exception:
                    pass
                time.sleep(0.05)
            logging.info(f"  ✅ Wind 增强底层行情完成: {_drop_count} 只")

        # ══════════════════════════════════════════
        # 5. 保存所有数据
        # ══════════════════════════════════════════
        meta_path = output_path.replace('.csv', '_meta.csv')
        xray_path = os.path.join(out_dir, 'client_xray.json')

        # 先删除旧文件，防止新 nav 写入后旧 meta 残留导致代码不匹配
        # 注意: client_fund_summary.json 已在 section 2.5 保存，不在此处清理
        _old_files = [output_path, meta_path, xray_path]
        # 清理遗留的旧格式文件
        for _legacy in ['client_fund_ratings.csv', 'client_benchmark_nav.csv']:
            _old_files.append(os.path.join(out_dir, _legacy))
        for _old_f in _old_files:
            if os.path.exists(_old_f):
                os.remove(_old_f)
                logging.info(f"  🗑️ 已清除旧文件: {_old_f}")

        df_nav.to_csv(output_path, encoding='utf-8-sig')
        if not df_meta.empty:
            df_meta.to_csv(meta_path, encoding='utf-8-sig')
        else:
            logging.warning("⚠️ 元数据为空，client_nav_meta.csv 未生成")
            logging.warning("  ↳ 继续处理, 元数据缺失不阻塞流程")

        # ══════════════════════════════════════════
        # 6. 自动下载 7 大比较基准指数行情 (Tushare 主路径)
        # ══════════════════════════════════════════
        BENCHMARK_CODES = {
            '000300.SH': '沪深300',
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指',
            '000905.SH': '中证500',
            '000852.SH': '中证1000',
            'HSI.HI':    '恒生指数',
        }
        bm_path = os.path.join(out_dir, 'client_benchmarks.csv')
        bm_success = False

        # ── Tushare 主路径 ──
        try:
            logging.info(f"📊 Tushare: 下载 {len(BENCHMARK_CODES)} 个比较基准指数行情...")
            from tushare_fetcher import fetch_index_daily
            df_bm_ts = fetch_index_daily(BENCHMARK_CODES, start_date, end_date)
            if df_bm_ts is not None and not df_bm_ts.empty:
                df_bm_ts.index.name = 'Date'
                df_bm_ts.to_csv(bm_path, encoding='utf-8-sig')
                logging.info(f"  ✅ Tushare 基准行情: {bm_path} ({len(df_bm_ts)} 行 × {len(df_bm_ts.columns)} 列)")
                bm_success = True
                tushare_used = True
            else:
                logging.warning("  ⚠️ Tushare 基准行情返回空")
        except Exception as e_ts:
            logging.warning(f"  ⚠️ Tushare 基准行情异常: {e_ts}")

        # ── Wind 可选增强: 补充 Tushare 未获取到的基准 ──
        if not bm_success and wind_available:
            try:
                logging.info(f"🔄 Wind 增强: 补充基准指数行情...")
                bm_codes_str = ','.join(BENCHMARK_CODES.keys())
                bm_result = w.wsd(bm_codes_str, "close", start_date, end_date, "")
                if bm_result.ErrorCode == 0:
                    bm_codes_list = list(BENCHMARK_CODES.keys())
                    if len(bm_codes_list) == 1:
                        df_bm = pd.DataFrame({bm_codes_list[0]: bm_result.Data[0]}, index=bm_result.Times)
                    else:
                        df_bm = pd.DataFrame(bm_result.Data, index=bm_result.Codes, columns=bm_result.Times).T
                    df_bm.index = pd.to_datetime(df_bm.index)
                    df_bm.index.name = 'Date'
                    df_bm = df_bm.dropna(how='all')
                    _non_null_cols = [c for c in df_bm.columns if df_bm[c].notna().sum() > 10]
                    if len(df_bm) > 10 and len(_non_null_cols) > 0:
                        df_bm.to_csv(bm_path, encoding='utf-8-sig')
                        logging.info(f"  ✅ Wind 增强基准行情: {bm_path}")
                        bm_success = True
            except Exception as e_bm:
                logging.warning(f"  ⚠️ Wind 增强基准异常: {e_bm}")

        # 保存穿透数据为 JSON
        xray_data = {
            'holdings_map': {k: v for k, v in holdings_map.items()},
            'holdings_ratio': {k: v for k, v in holdings_ratio.items()},
            'underlying_pct': underlying_pct,
            'report_date': rpt_date,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        with open(xray_path, 'w', encoding='utf-8') as f:
            json.dump(xray_data, f, ensure_ascii=False, indent=2)

        logging.info(f"✅ 全部完成: {len(success_codes)} 只基金, "
                     f"{len(holdings_map)} 只有重仓数据, {len(underlying_pct)} 只底层资产")

        _emit_result({
            "status": "success",
            "n_funds": len(df_nav.columns),
            "n_days": len(df_nav),
            "n_failed": len(failed_codes),
            "failed_codes": failed_codes[:10],
            "n_holdings": sum(len(v) for v in holdings_map.values()),
            "n_underlying": len(underlying_pct),
            "tushare_used": tushare_used,
        })
        sys.exit(0)

    except Exception as e:
        import traceback
        _emit_result({
            "status": "error",
            "detail": str(e),
            "traceback": traceback.format_exc(),
        })
        sys.exit(1)


def _emit_result(result: dict):
    print("__CLIENT_SYNC_RESULT_START__")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("__CLIENT_SYNC_RESULT_END__")


if __name__ == "__main__":
    main()
