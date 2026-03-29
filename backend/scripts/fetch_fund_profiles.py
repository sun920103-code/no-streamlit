"""
智选平台 — Wind 基金深度资料下载脚本
=====================================
从 Wind API 批量下载 114 只核心精选基金的深度资料，
输出结构化 JSON 供前端表格展示。

已验证可用 Wind WSS 字段:
  基本信息: sec_name, fund_setupdate, fund_mgrcomp, fund_investtype,
            fund_fundmanager, fund_custodianbank, fund_benchmark,
            fund_fundscale, fund_risklevel, fund_investobject
  费率信息: fund_managementfeeratio, fund_custodianfeeratio
  风险指标: risk_downside (最大回撤, 需 startDate/endDate)

使用方式:
    python fetch_fund_profiles.py            # 批量下载全部 114 只
    python fetch_fund_profiles.py 000011.OF  # 单只测试
"""

import os
import sys
import json
import time
from datetime import datetime

# ── Wind DLL 路径配置 ──
WIND_DLL_PATH = r"D:\Wind\x64"
WIND_BIN_PATH = r"D:\Wind\bin"


def _init_wind():
    """安全初始化 Wind COM 连接。"""
    original_cwd = os.getcwd()
    try:
        if hasattr(os, 'add_dll_directory'):
            if os.path.exists(WIND_DLL_PATH):
                os.add_dll_directory(WIND_DLL_PATH)
            if os.path.exists(WIND_BIN_PATH):
                os.add_dll_directory(WIND_BIN_PATH)
        if os.path.exists(WIND_DLL_PATH):
            os.chdir(WIND_DLL_PATH)
            os.environ['PATH'] = WIND_DLL_PATH + ';' + WIND_BIN_PATH + ';' + os.environ.get('PATH', '')
        from WindPy import w
        os.chdir(original_cwd)
    except Exception as e:
        os.chdir(original_cwd)
        raise e

    status = w.start()
    if status.ErrorCode != 0:
        raise RuntimeError(f"Wind 启动失败: ErrorCode={status.ErrorCode}")
    print(f"✅ Wind API 连接成功")
    return w


def _safe_val(val):
    """安全处理 Wind 返回值。"""
    if val is None:
        return None
    if hasattr(val, 'strftime'):
        return val.strftime("%Y-%m-%d")
    s = str(val)
    if s in ('nan', 'None', 'NaT', ''):
        return None
    if isinstance(val, float):
        return round(val, 4)
    return val


def fetch_single_fund_profile(w, fund_code: str) -> dict:
    """
    下载单只基金的完整深度资料 (仅使用已验证可用的字段)。
    基金名称/代码从 product_mapping 114 基金库获取, Wind 仅补充深度数据。
    """
    result = {"code": fund_code}

    # ═══ 1. 基本信息 (已验证OK的字段组合) ═══
    basic_fields = (
        "sec_name,fund_setupdate,fund_mgrcomp,fund_investtype,"
        "fund_fundmanager,fund_custodianbank,fund_benchmark,"
        "fund_fundscale,fund_risklevel,fund_investobject"
    )
    basic_labels = [
        "基金名称", "成立日期", "基金管理人", "投资类型",
        "基金经理", "托管人", "业绩比较基准",
        "基金规模(元)", "风险等级", "投资目标",
    ]

    try:
        data = w.wss(fund_code, basic_fields)
        if data and data.ErrorCode == 0 and data.Data:
            basic = {}
            for i, label in enumerate(basic_labels):
                if i < len(data.Data):
                    basic[label] = _safe_val(data.Data[i][0])
            # 规模转亿元
            if basic.get("基金规模(元)") and isinstance(basic["基金规模(元)"], (int, float)):
                basic["基金规模(亿元)"] = round(basic["基金规模(元)"] / 1e8, 2)
                del basic["基金规模(元)"]
            result["基本信息"] = basic
        else:
            ec = data.ErrorCode if data else 'None'
            print(f"  ⚠️ 基本信息: ErrorCode={ec}")
            result["基本信息"] = {}
    except Exception as e:
        print(f"  ❌ 基本信息异常: {e}")
        result["基本信息"] = {}

    # ═══ 2. 费率信息 ═══
    try:
        data = w.wss(fund_code, "fund_managementfeeratio,fund_custodianfeeratio")
        if data and data.ErrorCode == 0 and data.Data:
            result["费率信息"] = {
                "管理费率(%)": _safe_val(data.Data[0][0]),
                "托管费率(%)": _safe_val(data.Data[1][0]) if len(data.Data) > 1 else None,
            }
        else:
            result["费率信息"] = {}
    except Exception as e:
        result["费率信息"] = {}

    # ═══ 3. 风险指标 (5年最大回撤) ═══
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = str(int(end_date[:4]) - 5) + end_date[4:]
        data = w.wss(fund_code, "risk_downside",
                     f"riskFreeRate=1;startDate={start_date};endDate={end_date};period=1")
        if data and data.ErrorCode == 0 and data.Data:
            dd_val = data.Data[0][0]
            result["风险指标"] = {
                "近5年最大回撤(%)": round(float(dd_val), 2) if dd_val and str(dd_val) != 'nan' else None,
            }
        else:
            result["风险指标"] = {}
    except Exception as e:
        result["风险指标"] = {}

    return result


def fetch_batch_profiles(w, fund_codes: list) -> list:
    """批量下载多只基金的深度资料。"""
    profiles = []
    total = len(fund_codes)
    for i, code in enumerate(fund_codes):
        print(f"[{i+1}/{total}] 正在下载 {code} ...")
        try:
            profile = fetch_single_fund_profile(w, code)
            profiles.append(profile)
        except Exception as e:
            print(f"  ❌ {code} 下载失败: {e}")
            profiles.append({"code": code, "error": str(e)})
        # 防 Wind API 限流
        if i < total - 1:
            time.sleep(0.2)
    return profiles


def get_114_fund_codes():
    """从 product_mapping 获取 114 只核心基金代码 + 名称。"""
    legacy_dir = r"D:\No Streamlit\20260325"
    if legacy_dir not in sys.path:
        sys.path.insert(0, legacy_dir)

    try:
        from services.product_mapping import TRUST_PRODUCT_MAPPING
        pool = []
        seen = set()
        for ac_name, sub_cats in TRUST_PRODUCT_MAPPING.items():
            for cat_name, items in sub_cats.items():
                for item in items:
                    if len(item) >= 2 and item[0] not in seen:
                        seen.add(item[0])
                        pool.append({"code": item[0], "name": item[1], "category": ac_name})
        print(f"📋 从 product_mapping 114 基金库读取到 {len(pool)} 只基金")
        return pool
    except Exception as e:
        print(f"❌ 无法读取 product_mapping: {e}")
        return []


def main():
    """主入口：下载基金深度资料并保存为 JSON。"""
    if len(sys.argv) > 1:
        fund_codes = [sys.argv[1]]
        print(f"🔬 测试模式: 下载 {fund_codes[0]} 的深度资料")
        pool_info = None
    else:
        pool = get_114_fund_codes()
        if not pool:
            print("❌ 未获取到基金代码，退出")
            return
        fund_codes = [p["code"] for p in pool]
        pool_info = {p["code"]: p for p in pool}
        print(f"📦 批量模式: 下载 {len(fund_codes)} 只基金深度资料")

    w = _init_wind()

    try:
        profiles = fetch_batch_profiles(w, fund_codes)

        # 合并 114 基金库的名称和类别信息
        if pool_info:
            for p in profiles:
                code = p.get("code", "")
                if code in pool_info:
                    p["库内名称"] = pool_info[code]["name"]
                    p["资产大类"] = pool_info[code]["category"]

        # 保存结果
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "zx_fund_profiles.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n{'='*60}")
        print(f"✅ 深度资料下载完成!")
        print(f"   总计: {len(profiles)} 只基金")
        print(f"   输出: {output_path}")
        print(f"{'='*60}")

        # 摘要
        if profiles:
            sample = profiles[0]
            print(f"\n📊 数据字段摘要 (以 {sample.get('code', '?')} 为例):")
            for section, data in sample.items():
                if isinstance(data, dict):
                    non_null = sum(1 for v in data.values() if v is not None)
                    total_f = len(data)
                    print(f"  [{section}] {non_null}/{total_f} 个字段有数据")
                    for k, v in data.items():
                        status = "✅" if v is not None else "❌"
                        display_val = str(v)[:50] if v is not None else "N/A"
                        print(f"    {status} {k}: {display_val}")

    finally:
        try:
            w.stop()
            print("🔌 Wind 连接已关闭")
        except Exception:
            pass


if __name__ == "__main__":
    main()
