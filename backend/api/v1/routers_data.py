"""
Data API — 外部数据同步 (Wind, 等等) + 持仓诊断预警
"""
import os
import sys
import json
import uuid
import subprocess
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.append(LEGACY_SERVICES_DIR)

router = APIRouter()

# 存储全局轮询任务状态 (内存中)
_tasks_status: Dict[str, Any] = {}

# ─── 市场行情 5 分钟缓存 ───
_market_quotes_cache: list = []
_market_quotes_ts: Optional[datetime] = None
_MARKET_CACHE_SECONDS = 300  # 5 分钟

MARKET_INDICES = [
    {"code": "000001.SH", "name": "上证指数", "en": "SSE Composite"},
    {"code": "000300.SH", "name": "沪深300", "en": "CSI 300"},
    {"code": "399001.SZ", "name": "深证成指", "en": "SZSE Comp"},
    {"code": "399006.SZ", "name": "创业板指", "en": "ChiNext"},
    {"code": "000905.SH", "name": "中证500", "en": "CSI 500"},
    {"code": "000852.SH", "name": "中证1000", "en": "CSI 1000"},
    {"code": "HSI.HI",    "name": "恒生指数", "en": "Hang Seng"},
]

# ─── Wind 直连单例 — 专属线程 (COM 线程安全) ───
import threading
import queue as _queue

class _WindMarketDaemon:
    """Wind COM 必须在同一线程调用 start() 和所有 API。使用专属守护线程。"""
    def __init__(self):
        self._q = _queue.Queue()
        self._w = None
        self._ready = threading.Event()
        self._error = None
        t = threading.Thread(target=self._run, daemon=True, name="WindMarketThread")
        t.start()
        self._ready.wait(timeout=30)

    def _run(self):
        try:
            wind_dll_path = r"D:\Wind\x64"
            wind_bin_path = r"D:\Wind\bin"
            original_cwd = os.getcwd()
            try:
                if hasattr(os, 'add_dll_directory'):
                    if os.path.exists(wind_dll_path):
                        os.add_dll_directory(wind_dll_path)
                    if os.path.exists(wind_bin_path):
                        os.add_dll_directory(wind_bin_path)
                if os.path.exists(wind_dll_path):
                    os.chdir(wind_dll_path)
                    os.environ['PATH'] = wind_dll_path + ';' + wind_bin_path + ';' + os.environ.get('PATH', '')
                from WindPy import w
                os.chdir(original_cwd)
            except Exception as e:
                os.chdir(original_cwd)
                raise e

            status = w.start()
            if status.ErrorCode != 0:
                logger.error(f"Wind Market 启动失败: ErrorCode={status.ErrorCode}")
                self._error = f"ErrorCode={status.ErrorCode}"
                self._ready.set()
                return

            self._w = w
            logger.info("✅ Wind Market daemon 连接成功")
            self._ready.set()

            while True:
                try:
                    item = self._q.get(timeout=1.0)
                except _queue.Empty:
                    continue
                if item is None:
                    break
                method_name, args, kwargs, result_q = item
                try:
                    method = getattr(self._w, method_name)
                    result = method(*args, **kwargs)
                    result_q.put(('ok', result))
                except Exception as e:
                    result_q.put(('error', e))
        except ImportError:
            logger.warning("WindPy 未安装")
            self._error = "ImportError"
            self._ready.set()
        except Exception as e:
            logger.error(f"Wind Market daemon 异常: {e}")
            self._error = str(e)
            self._ready.set()

    def _call(self, method_name, *args, **kwargs):
        if self._w is None:
            return None
        result_q = _queue.Queue()
        self._q.put((method_name, args, kwargs, result_q))
        try:
            status, result = result_q.get(timeout=30)
            if status == 'error':
                raise result
            return result
        except _queue.Empty:
            logger.error(f"Wind {method_name} 超时 (30s)")
            return None

    def wss(self, *args, **kwargs):
        return self._call('wss', *args, **kwargs)

    def wsd(self, *args, **kwargs):
        return self._call('wsd', *args, **kwargs)

    def wsq(self, *args, **kwargs):
        return self._call('wsq', *args, **kwargs)

    @property
    def is_connected(self):
        return self._w is not None and self._error is None


_wind_market_daemon = None
_wind_market_init_lock = threading.Lock()

def _get_wind_direct():
    """获取 Wind Market daemon 单例。"""
    global _wind_market_daemon
    if _wind_market_daemon is not None and _wind_market_daemon.is_connected:
        return _wind_market_daemon
    with _wind_market_init_lock:
        if _wind_market_daemon is not None and _wind_market_daemon.is_connected:
            return _wind_market_daemon
        try:
            _wind_market_daemon = _WindMarketDaemon()
            if _wind_market_daemon.is_connected:
                return _wind_market_daemon
            else:
                logger.error(f"Wind Market daemon 启动失败: {_wind_market_daemon._error}")
                return None
        except Exception as e:
            logger.error(f"Wind Market 初始化异常: {e}")
            return None


@router.get("/market_quotes")
async def get_market_quotes():
    """
    获取 7 大宽基指数实时行情 (5 分钟缓存)。
    由于 WSD 历史额度容易耗尽 (-40522017)，改为使用 w.wsq 实时快照接口 (不耗历史额度)。
    """
    global _market_quotes_cache, _market_quotes_ts

    now = datetime.now()
    if _market_quotes_ts and (now - _market_quotes_ts).total_seconds() < _MARKET_CACHE_SECONDS:
        return {"status": "success", "quotes": _market_quotes_cache, "cached": True,
                "updated_at": _market_quotes_ts.strftime("%H:%M:%S")}

    w = _get_wind_direct()
    if w is None:
        if _market_quotes_cache:
            return {"status": "success", "quotes": _market_quotes_cache, "cached": True,
                    "updated_at": (_market_quotes_ts or now).strftime("%H:%M:%S"),
                    "warning": "Wind 未连接，使用缓存数据"}
        return {"status": "error", "quotes": [], "message": "Wind API 未连接"}

    try:
        codes_list = [idx["code"] for idx in MARKET_INDICES]
        codes_str = ",".join(codes_list)
        logger.info(f"📡 正在从 Wind 拉取市场行情 (wsq): {len(codes_list)} 个指数...")

        # wsq 接口不耗费 wsd 历史配额, 返回 [rt_last, rt_pct_chg]
        data = w.wsq(codes_str, "rt_last,rt_pct_chg")

        if data is None:
            logger.warning("Wind wsq 返回 None (可能超时)")
            if _market_quotes_cache:
                return {"status": "success", "quotes": _market_quotes_cache, "cached": True,
                        "updated_at": (_market_quotes_ts or now).strftime("%H:%M:%S")}
            return {"status": "error", "quotes": [], "message": "Wind wsq 超时"}

        quotes = []
        if data.ErrorCode == 0 and data.Data:
            logger.info(f"📡 Wind wsq 返回成功数据: rt_last={data.Data[0][:3]}...")

            for j, idx in enumerate(MARKET_INDICES):
                close_val = None
                pct_val = None

                try:
                    # wsq 返回各列数据 (第0列为 rt_last, 第1列为 rt_pct_chg)
                    val_last = data.Data[0][j] if j < len(data.Data[0]) else None
                    val_pct = data.Data[1][j] if len(data.Data) > 1 and j < len(data.Data[1]) else None

                    if val_last is not None and str(val_last) not in ('nan', 'None', ''):
                        close_val = float(val_last)

                    if val_pct is not None and str(val_pct) not in ('nan', 'None', ''):
                        # Wind wsq rt_pct_chg 直接返回 百分比数值 (0.015表示涨幅 1.5%)
                        # 而我们的 UI 期望直接展示 1.5，需要乘以 100
                        pct_val = float(val_pct) * 100.0

                except Exception as e:
                    logger.warning(f"解析 {idx['code']} 行情异常: {e}")

                quotes.append({
                    "code": idx["code"],
                    "name": idx["name"],
                    "en": idx["en"],
                    "close": round(close_val, 2) if close_val is not None else None,
                    "pct_chg": round(pct_val, 2) if pct_val is not None else None,
                })

            _market_quotes_cache = quotes
            _market_quotes_ts = now
            n_valid = sum(1 for q in quotes if q["close"] is not None)
            logger.info(f"✅ 市场行情更新: {n_valid}/{len(quotes)} 个指数有有效数据")
            return {"status": "success", "quotes": quotes, "cached": False,
                    "updated_at": now.strftime("%H:%M:%S")}
        else:
            logger.warning(f"Wind WSQ 市场行情失败: ErrorCode={data.ErrorCode}")
            # 如果 wsq 因为配额或其他原因彻底死掉 (-40522017) 则明确提示 UI
            msg = f"ErrorCode={data.ErrorCode}"
            if data.ErrorCode == -40522017:
                msg = "行情配额已耗尽(ErrorCode=-40522017)"

            if _market_quotes_cache:
                return {"status": "success", "quotes": _market_quotes_cache, "cached": True,
                        "updated_at": (_market_quotes_ts or now).strftime("%H:%M:%S"), "warning": msg}
            return {"status": "error", "quotes": [], "message": msg}

    except Exception as e:
        logger.error(f"市场行情获取异常: {e}")
        return {"status": "error", "quotes": _market_quotes_cache or [],
                "message": str(e)}

class SyncClientPortfolioRequest(BaseModel):
    fund_codes: List[str]


# ═══════════════════════════════════════════════════
# 辅助函数 — 从 Wind sync 输出文件中提取诊断数据
# ═══════════════════════════════════════════════════

def _get_data_dir(task_id: str) -> str:
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(backend_dir, "data")


def _compute_fund_summary(task_id: str, fund_codes: List[str]) -> Dict:
    """
    从 Wind sync 输出中读取 client_fund_summary.json + client_nav_meta.csv,
    返回 NordicFinance 表格所需的增强数据：月收益率、年化波动率、状态 badge。
    """
    data_dir = _get_data_dir(task_id)
    summary_path = os.path.join(data_dir, "client_fund_summary.json")
    meta_path = os.path.join(data_dir, f"sync_{task_id}_meta.csv")
    nav_path = os.path.join(data_dir, f"sync_{task_id}.csv")

    # 读取综合分析表
    summary_data = {}
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_data = json.load(f)
        except Exception as e:
            logger.warning(f"读取 fund_summary.json 失败: {e}")

    # 读取元数据
    meta_df = None
    if os.path.exists(meta_path):
        for enc in ["utf-8-sig", "gbk", "utf-8", "gb2312"]:
            try:
                meta_df = pd.read_csv(meta_path, index_col=0, encoding=enc)
                meta_df.columns = [c.lower() for c in meta_df.columns]
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

    # 读取净值计算月收益率
    monthly_returns = {}
    if os.path.exists(nav_path):
        try:
            nav_df = pd.read_csv(nav_path, index_col=0, parse_dates=True)
            for col in nav_df.columns:
                series = nav_df[col].dropna()
                if len(series) >= 20:
                    last = series.iloc[-1]
                    one_month_ago_idx = max(0, len(series) - 22)
                    prev = series.iloc[one_month_ago_idx]
                    if prev > 0:
                        monthly_returns[col] = float(round((last / prev - 1) * 100, 2))
        except Exception as e:
            logger.warning(f"计算月收益率失败: {e}")

    # 构建每只基金的增强数据
    # --- 计算基金经理变更标记 ---
    mgr_changed_set = set()
    if meta_df is not None:
        twelve_months_ago = datetime.today() - timedelta(days=365)
        for idx, row in meta_df.iterrows():
            mgr_start = str(row.get("fund_fundmanager_startdate", "")).strip()
            if mgr_start and mgr_start not in ("nan", "None", "NaT", ""):
                try:
                    start_dt = pd.to_datetime(mgr_start)
                    if start_dt >= twelve_months_ago:
                        mgr_changed_set.add(str(idx).split(".")[0].zfill(6))
                except Exception:
                    pass

    # --- 调用 RBSA 风格漂移检测 ---
    drift_set = set()  # codes with style drift
    try:
        from services.rbsa_style_analyzer import analyze_portfolio_styles
        rbsa = analyze_portfolio_styles(fund_codes, lookback_short=60, lookback_long=180)
        for alert in rbsa.get("drift_alerts", []):
            fc = str(alert.get("fund_code", "")).split(".")[0].zfill(6)
            drift_set.add(fc)
    except ImportError:
        logger.info("RBSA 不可用，跳过风格漂移检测")
    except Exception as e:
        logger.warning(f"RBSA 风格漂移检测异常(非致命): {e}")

    enhanced = {}
    for code in fund_codes:
        bare = str(code).split(".")[0].zfill(6)
        sd = summary_data.get(bare, {})
        fund_name = ""
        if meta_df is not None and bare in meta_df.index:
            fund_name = str(meta_df.loc[bare].get("sec_name", ""))

        monthly_pl = monthly_returns.get(bare, sd.get("ret_ytd", None))
        if monthly_pl is None:
            monthly_pl = 0.0
        elif isinstance(monthly_pl, float) and abs(monthly_pl) < 0.001:
            monthly_pl = round(sd.get("ret_ytd", 0) * 100, 2) if sd.get("ret_ytd") else 0.0

        vol_3y = sd.get("vol_3y", None)
        volatility = round(vol_3y * 100, 1) if vol_3y else 0.0

        # YTD 和 1Y 收益率 — 直接从 Wind WSS 下载的 client_fund_summary.json 中取
        _ret_ytd_raw = sd.get("ret_ytd", None)
        ret_ytd = round(_ret_ytd_raw * 100, 2) if _ret_ytd_raw is not None else None
        _ret_1y_raw = sd.get("ret_1y", None)
        ret_1y = round(_ret_1y_raw * 100, 2) if _ret_1y_raw is not None else None

        # 状态 badge 逻辑
        if monthly_pl > 2:
            status = "OUTPERFORM"
        elif monthly_pl > 0:
            status = "ACTIVE"
        elif monthly_pl > -1:
            status = "STABLE"
        elif volatility > 20:
            status = "VOLATILITY"
        else:
            status = "HOLDING"

        enhanced[bare] = {
            "name": fund_name if fund_name and fund_name != "nan" else "",
            "monthly_pl": float(round(monthly_pl, 2)),
            "volatility": float(volatility),
            "status": status,
            "ret_ytd": float(ret_ytd) if ret_ytd is not None else None,
            "ret_1y": float(ret_1y) if ret_1y is not None else None,
            "style_drifted": bare in drift_set,
            "mgr_changed": bare in mgr_changed_set,
        }

    return enhanced


def _compute_alerts(task_id: str, fund_codes: List[str]) -> Dict:
    """
    从 Wind sync 输出中提取三大预警：
    1. 基金经理变更 (12个月内)
    2. 重仓股连续下跌 (近3交易日连跌>10%)
    3. 风格漂移预警 (RBSA — 如可用)
    """
    data_dir = _get_data_dir(task_id)
    meta_path = os.path.join(data_dir, f"sync_{task_id}_meta.csv")
    xray_path = os.path.join(data_dir, "client_xray.json")

    mgr_alerts = []
    crash_alerts = []
    drift_alerts = []

    # ── Rule B: 基金经理变更 (12个月内) ──
    if os.path.exists(meta_path):
        try:
            meta_df = None
            for enc in ["utf-8-sig", "gbk", "utf-8", "gb2312"]:
                try:
                    meta_df = pd.read_csv(meta_path, index_col=0, encoding=enc)
                    meta_df.columns = [c.lower() for c in meta_df.columns]
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if meta_df is not None:
                twelve_months_ago = datetime.today() - timedelta(days=365)
                six_months_ago = datetime.today() - timedelta(days=180)
                three_months_ago = datetime.today() - timedelta(days=90)

                for code, row in meta_df.iterrows():
                    mgr_name = str(row.get("fund_fundmanager", "")).strip()
                    mgr_start = str(row.get("fund_fundmanager_startdate", "")).strip()
                    fund_name = str(row.get("sec_name", code)).strip()

                    if mgr_start and mgr_start not in ("nan", "None", "NaT", ""):
                        try:
                            start_dt = pd.to_datetime(mgr_start)
                            if start_dt >= twelve_months_ago:
                                days_since = (datetime.today() - start_dt).days
                                if start_dt >= three_months_ago:
                                    severity = "critical"
                                    severity_label = "🔴 高风险"
                                elif start_dt >= six_months_ago:
                                    severity = "warning"
                                    severity_label = "🟠 中风险"
                                else:
                                    severity = "notice"
                                    severity_label = "🟡 关注"

                                mgr_alerts.append({
                                    "fund": str(code).split(".")[0].zfill(6),
                                    "fund_name": fund_name,
                                    "manager": mgr_name,
                                    "start_date": start_dt.strftime("%Y-%m-%d"),
                                    "days_since_change": days_since,
                                    "severity": severity,
                                    "severity_label": severity_label,
                                })
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"经理变更预警计算异常: {e}")

    # ── Rule A: 重仓股连续三个交易日跌幅超过 10% ──
    if os.path.exists(xray_path):
        try:
            with open(xray_path, "r", encoding="utf-8") as f:
                xray = json.load(f)

            holdings_map = xray.get("holdings_map", {})
            underlying_pct = xray.get("underlying_pct", {})

            for fund_code, stk_list in holdings_map.items():
                for stk_info in stk_list:
                    stk_code = stk_info[0] if isinstance(stk_info, (list, tuple)) else stk_info
                    stk_name = stk_info[1] if isinstance(stk_info, (list, tuple)) and len(stk_info) > 1 else ""
                    info = underlying_pct.get(stk_code, {})
                    real_name = info.get("name", stk_name or stk_code)
                    daily_pcts = info.get("daily_pcts", [])

                    # 触发条件: 连续 3 个交易日每日跌幅均超过 10%
                    consecutive_drops = 0
                    max_consecutive = 0
                    for pct in daily_pcts:
                        if pct is not None and pct <= -10.0:
                            consecutive_drops += 1
                            max_consecutive = max(max_consecutive, consecutive_drops)
                        else:
                            consecutive_drops = 0

                    if max_consecutive >= 3:
                        crash_alerts.append({
                            "fund": fund_code,
                            "stock": real_name,
                            "stock_code": stk_code,
                            "consecutive_days": max_consecutive,
                            "daily_pcts": [round(p, 2) for p in daily_pcts if p is not None],
                        })
        except Exception as e:
            logger.warning(f"重仓股暴跌预警计算异常: {e}")

    # ── Rule C: 风格漂移预警 (RBSA) ──
    try:
        from services.rbsa_style_analyzer import detect_style_drift
        nav_path = os.path.join(data_dir, f"sync_{task_id}.csv")
        if os.path.exists(nav_path):
            nav_df = pd.read_csv(nav_path, index_col=0, parse_dates=True)
            for col in nav_df.columns:
                series = nav_df[col].dropna()
                if len(series) >= 252:  # 需要至少1年数据
                    try:
                        drift_result = detect_style_drift(series)
                        if drift_result and drift_result.get("drifted"):
                            drift_alerts.append({
                                "fund": col,
                                "message": drift_result.get("message", "风格漂移"),
                                "from_style": drift_result.get("from_style", ""),
                                "to_style": drift_result.get("to_style", ""),
                            })
                    except Exception:
                        pass  # 单只基金漂移检测失败不影响整体
    except ImportError:
        logger.info("rbsa_style_analyzer 不可用，跳过风格漂移检测")
    except Exception as e:
        logger.warning(f"风格漂移预警异常: {e}")

    return {
        "manager_alerts": mgr_alerts,
        "crash_alerts": crash_alerts,
        "drift_alerts": drift_alerts,
        "total_alerts": len(mgr_alerts) + len(crash_alerts) + len(drift_alerts),
    }


# ═══════════════════════════════════════════════════
# Wind 同步主脚本 + 增强诊断数据
# ═══════════════════════════════════════════════════

def run_sync_script(task_id: str, fund_codes: List[str]):
    """执行实际的 Python 子进程同步（隔离 C++ Windpy dll），完成后自动计算增强诊断数据"""
    _tasks_status[task_id] = {"status": "processing", "message": "正在连接 Wind 终端并拉取底层数据...", "result": None}

    codes_str = ",".join(fund_codes)

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(backend_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_csv = os.path.join(data_dir, f"sync_{task_id}.csv")

    script_path = os.path.join(backend_dir, "scripts", "sync_client_holdings.py")

    logger.info(f"Task {task_id} - Spawning subprocess: {sys.executable} {script_path} <codes> {out_csv}")

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = backend_dir + os.pathsep + env.get("PYTHONPATH", "")

        process = subprocess.Popen(
            [sys.executable, script_path, codes_str, out_csv],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        out_lines = []
        result_payload = {}
        for line in iter(process.stdout.readline, ""):
            out_lines.append(line)
            if "__TUSHARE_STARTED__" in line:
                _tasks_status[task_id]["message"] = "Tushare 下载数据中..."

        process.stdout.close()
        returncode = process.wait()
        out_text = "".join(out_lines)

        # DEBUG: Save full subprocess output to a log file
        log_path = os.path.join(data_dir, f"sync_subprocess_{task_id}.log")
        try:
            with open(log_path, "w", encoding="utf-8") as _f:
                _f.write(out_text)
        except Exception as e:
            logger.error(f"无法保存子进程日志: {e}")

        if "__CLIENT_SYNC_RESULT_START__" in out_text and "__CLIENT_SYNC_RESULT_END__" in out_text:
            try:
                start_idx = out_text.find("__CLIENT_SYNC_RESULT_START__") + len("__CLIENT_SYNC_RESULT_START__")
                end_idx = out_text.find("__CLIENT_SYNC_RESULT_END__")
                json_str = out_text[start_idx:end_idx].strip()
                result_payload = json.loads(json_str)
            except Exception as e:
                logger.error(f"Task {task_id} JSON 解析失败: {e}")

        if returncode == 0 and result_payload.get("status") == "success":
            # ── 计算增强诊断数据 ──
            fund_summary = {}
            alerts = {"manager_alerts": [], "crash_alerts": [], "drift_alerts": [], "total_alerts": 0}
            try:
                fund_summary = _compute_fund_summary(task_id, fund_codes)
                alerts = _compute_alerts(task_id, fund_codes)
            except Exception as e:
                logger.warning(f"Task {task_id} 增强诊断数据计算异常(非致命): {e}\n{traceback.format_exc()}")

            api_data = {
                "status": "success",
                "data": {
                    "funds_matched": result_payload.get("n_funds", 0),
                    "funds_total": result_payload.get("n_funds", 0),
                    "prices_days": result_payload.get("n_days", 0),
                    "total_stocks_count": result_payload.get("n_holdings", 0),
                    "unique_stocks_count": result_payload.get("n_underlying", 0),
                    "fund_summary": fund_summary,
                    "alerts": alerts,
                },
            }
            is_ts = result_payload.get("tushare_used", False)
            msg = "⚡ Tushare 数据拉取成功！" if is_ts else "Wind 数据拉取成功！"

            _tasks_status[task_id] = {
                "status": "success",
                "message": msg,
                "result": api_data,
            }
        else:
            logger.error(f"Task {task_id} sync failed! Stdout:\n{out_text}")
            error_detail = result_payload.get("detail", "底层进程发生异常或 WindPy 连接超时。")
            _tasks_status[task_id] = {
                "status": "error",
                "message": f"底层数据拉取失败: {error_detail}",
                "result": None,
            }

    except Exception as e:
        logger.exception(f"System error in run_sync_script for task {task_id}")
        _tasks_status[task_id] = {
            "status": "error",
            "message": f"系统调用异常: {str(e)}",
            "result": None,
        }


@router.post("/sync_client_portfolio")
async def sync_client_portfolio(req: SyncClientPortfolioRequest, background_tasks: BackgroundTasks):
    """
    独立进程拉取客户组合 Wind 行情数据 (防 C++ 内存冲突)
    """
    if not req.fund_codes:
        raise HTTPException(status_code=400, detail="由于 CSV 文件未提供合格的代码列表，请求被拒绝。")

    task_id = str(uuid.uuid4())
    _tasks_status[task_id] = {"status": "pending", "message": "请求排队中..."}

    # 异步推入后台执行，立即响应
    background_tasks.add_task(run_sync_script, task_id, req.fund_codes)

    return {
        "status": "accepted",
        "task_id": task_id,
        "message": "数据拉取请求已受理，进入后台执行",
    }


@router.get("/sync_status/{task_id}")
async def get_sync_status(task_id: str):
    """轮询进度接口"""
    if task_id not in _tasks_status:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return _tasks_status[task_id]


# ── Campaign 12: 核心精选基金池白盒接口 ──
@router.get("/get_core_fund_pool")
async def get_core_fund_pool_endpoint():
    """
    完整下发 114 只精选核心基金池的代码、名称及宏观标签。
    """
    try:
        from services.product_mapping import TRUST_PRODUCT_MAPPING

        pool = []
        for ac_name, sub_cats in TRUST_PRODUCT_MAPPING.items():
            for cat_name, items in sub_cats.items():
                for item in items:
                    if len(item) >= 2:
                        pool.append({
                            "code": item[0],
                            "name": item[1],
                            "category": f"{ac_name} - {cat_name}",
                        })

        seen = set()
        unique_pool = []
        for p in pool:
            if p["code"] not in seen:
                seen.add(p["code"])
                unique_pool.append(p)

        return {
            "status": "success",
            "count": len(unique_pool),
            "pool": unique_pool,
        }
    except Exception as e:
        logger.error(f"Failed to load core fund pool: {e}")
        raise HTTPException(status_code=500, detail="无法读取底层白盒产品映射矩阵")


# ── Kimi 基金新闻搜索 + 月度回顾生成 ──

class FundNewsReviewRequest(BaseModel):
    fund_names: List[str]  # 基金名称列表


@router.post("/fund_news_review")
async def fund_news_review(req: FundNewsReviewRequest):
    """
    使用 Kimi (Moonshot API) 联网搜索每只基金的近期新闻,
    汇总生成投资组合表现月度回顾。
    """
    if not req.fund_names:
        raise HTTPException(status_code=400, detail="基金名称列表为空")

    today_str = datetime.today().strftime("%Y年%m月%d日")

    try:
        from services.llm_engine import chat_completion_safe

        # 构建搜索 prompt — 要求 Kimi 联网搜索
        fund_list_str = "、".join(req.fund_names[:20])  # 最多 20 只避免 prompt 过长

        system_prompt = (
            "你是一位专业的信托家族办公室投资顾问。请你根据用户提供的基金名称列表，"
            "通过联网搜索查找这些基金近一个月的市场新闻和重大事件。\n\n"
            "【重要规则】\n"
            "1. 你必须通过网络搜索获取真实新闻，禁止编造任何信息\n"
            "2. 对于每只基金，搜索关键词应包含基金名称+相关信托公司名称\n"
            "3. 如果某只基金确实没有搜索到相关新闻，标注为'近期无相关市场资讯'\n"
            "4. 如果所有基金都没有搜到新闻，直接输出'近一个月无上述持仓基金的市场资讯'\n"
            "5. 新闻需要涵盖：业绩表现、规模变动、分红公告、监管处罚、基金经理动态等\n\n"
            "【输出格式】\n"
            f"# 投资组合表现月度回顾（{today_str}）\n\n"
            "## 持仓基金近期市场资讯\n\n"
            "按照以下格式逐只基金输出：\n"
            "### 基金名称\n"
            "- 新闻标题1：摘要...\n"
            "- 新闻标题2：摘要...\n\n"
            "## 市场总结\n"
            "（对整体市场环境和持仓基金表现做一段简要总结）"
        )

        user_prompt = (
            f"请搜索以下基金的近一个月市场新闻并汇总：\n\n{fund_list_str}\n\n"
            f"今天日期是 {today_str}，请搜索最近一个月的新闻。"
        )

        result = chat_completion_safe(
            system_prompt=system_prompt,
            user_content=user_prompt,
            model_choice="Kimi",
            temperature=0.3,
            enable_web_search=True,
        )

        if not result or len(result.strip()) < 20:
            return {
                "status": "success",
                "review": f"# 投资组合表现月度回顾（{today_str}）\n\n近一个月无上述持仓基金的市场资讯",
                "source": "kimi_empty",
            }

        return {
            "status": "success",
            "review": result.strip(),
            "source": "kimi_web_search",
        }

    except ImportError:
        logger.warning("llm_engine 不可用")
        return {
            "status": "error",
            "review": f"# 投资组合表现月度回顾（{today_str}）\n\nAI 引擎不可用，无法生成市场回顾。",
            "source": "error",
        }
    except Exception as e:
        logger.error(f"Kimi 基金新闻搜索异常: {e}")
        return {
            "status": "error",
            "review": f"# 投资组合表现月度回顾（{today_str}）\n\n生成失败: {str(e)}",
            "source": "error",
        }
