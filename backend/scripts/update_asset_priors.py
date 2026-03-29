"""
update_asset_priors.py — 从 Wind API 更新八大类资产波动率先验和相关矩阵
===============================================================================
定时任务: 每周五下午 4 点执行 (Windows Task Scheduler)
也可手动运行: python scripts/update_asset_priors.py

管线:
  1. 从 product_mapping 加载 146 只基金池
  2. 从 Wind API 下载每只基金近 3 年的复权净值 (nav_adj)
  3. 按 8 大类资产分组，计算每类的等权日收益率序列
  4. 从 8 条日收益率序列中提取:
     - 各类年化波动率 (DEFAULT_VOLS)
     - 各类年化收益率 (DEFAULT_RETURNS)
     - 8×8 相关矩阵 (CORRELATION_MATRIX)
  5. 序列化为 JSON 保存到 backend/data/asset_priors.json
  6. factor_risk_parity.py 启动时自动加载该文件
"""

import os
import sys
import json
import traceback
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ── 路径 ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
LEGACY_DIR = r"D:\No Streamlit\20260325"
DATA_DIR = os.path.join(BACKEND_DIR, "data")

sys.path.insert(0, BACKEND_DIR)
sys.path.append(LEGACY_DIR)

OUTPUT_FILE = os.path.join(DATA_DIR, "asset_priors.json")

# 8 大类资产 (与 factor_loadings.ASSET_CLASSES 完全对齐)
ASSET_CLASSES = ["大盘核心", "科技成长", "红利防守", "纯债固收", "混合债券", "短债理财", "黄金商品", "海外QDII"]


def load_fund_pool() -> dict:
    """
    从 product_mapping 加载 146 只基金池, 按 8 大类分组。
    返回: {"大盘核心": ["code1.OF", "code2.OF", ...], ...}
    """
    import importlib.util
    pm_path = os.path.join(LEGACY_DIR, "services", "product_mapping.py")
    if not os.path.exists(pm_path):
        pm_path = os.path.join(BACKEND_DIR, "services", "product_mapping.py")
    
    spec = importlib.util.spec_from_file_location("pm", pm_path)
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    
    TPM = pm.TRUST_PRODUCT_MAPPING
    pool_by_class = {}
    for ac_name in ASSET_CLASSES:
        if ac_name not in TPM:
            print(f"⚠️ 资产类别 '{ac_name}' 不在 product_mapping 中")
            continue
        codes = []
        for cat_name, items in TPM[ac_name].items():
            for item in items:
                if len(item) >= 2:
                    codes.append(item[0])
        pool_by_class[ac_name] = codes
    return pool_by_class


def fetch_nav_data(all_codes: list, years: int = 3) -> pd.DataFrame:
    """
    从 Wind API 批量下载复权净值。
    返回 DataFrame: index=日期, columns=基金代码, values=nav_adj
    """
    try:
        from WindPy import w
        if not w.isconnected():
            w.start()
    except ImportError:
        raise RuntimeError("WindPy 未安装或无法加载")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365 * years + 30)).strftime("%Y-%m-%d")
    
    print(f"📡 从 Wind 下载 {len(all_codes)} 只基金的复权净值...")
    print(f"   区间: {start_date} → {end_date}")
    
    # Wind API 单次最大支持约 50 只基金的 wsd, 分批下载
    batch_size = 40
    all_nav = pd.DataFrame()
    
    for i in range(0, len(all_codes), batch_size):
        batch = all_codes[i:i + batch_size]
        batch_str = ','.join(batch)
        print(f"   批次 {i // batch_size + 1}: {len(batch)} 只 ({batch[0]} ~ {batch[-1]})")
        
        res = w.wsd(batch_str, "nav_adj", start_date, end_date, "")
        if res.ErrorCode != 0:
            print(f"   ❌ Wind API 错误: ErrorCode={res.ErrorCode}")
            continue
        
        if len(batch) == 1:
            df_batch = pd.DataFrame({batch[0]: res.Data[0]}, index=pd.to_datetime(res.Times))
        else:
            df_batch = pd.DataFrame(dict(zip(batch, res.Data)), index=pd.to_datetime(res.Times))
        
        if all_nav.empty:
            all_nav = df_batch
        else:
            all_nav = all_nav.join(df_batch, how='outer')
    
    all_nav.sort_index(inplace=True)
    all_nav.ffill(inplace=True)
    
    print(f"✅ 数据下载完成: {all_nav.shape[0]} 个交易日, {all_nav.shape[1]} 只基金")
    return all_nav


def compute_asset_class_returns(df_nav: pd.DataFrame, pool_by_class: dict) -> pd.DataFrame:
    """
    计算每个大类资产的等权日收益率序列。
    返回 DataFrame: index=日期, columns=8大类资产名
    """
    # 先算每只基金的日收益率
    df_returns = df_nav.pct_change().iloc[1:]  # 去掉第一行 NaN
    
    class_returns = {}
    for ac_name in ASSET_CLASSES:
        codes = pool_by_class.get(ac_name, [])
        valid_codes = [c for c in codes if c in df_returns.columns and df_returns[c].notna().sum() > 60]
        
        if not valid_codes:
            print(f"  ⚠️ {ac_name}: 无有效基金数据, 跳过")
            continue
        
        # 等权平均日收益率
        class_ret = df_returns[valid_codes].mean(axis=1)
        class_returns[ac_name] = class_ret
        print(f"  ✅ {ac_name}: {len(valid_codes)}/{len(codes)} 只基金有效")
    
    df_class = pd.DataFrame(class_returns)
    df_class.dropna(how='all', inplace=True)
    return df_class


def compute_priors(df_class_returns: pd.DataFrame) -> dict:
    """
    从 8 大类资产等权日收益率序列中，计算:
      - 各类年化波动率
      - 各类年化收益率
      - 8×8 相关矩阵
    """
    trading_days = 242
    
    # ── 年化波动率 ──
    daily_vols = df_class_returns.std(ddof=1)
    ann_vols = daily_vols * np.sqrt(trading_days)
    
    # ── 年化收益率 ──
    daily_means = df_class_returns.mean()
    ann_returns = daily_means * trading_days
    
    # ── 相关矩阵 ──
    corr_matrix = df_class_returns.corr()
    
    # 确保 8×8 顺序一致
    ordered_classes = [ac for ac in ASSET_CLASSES if ac in df_class_returns.columns]
    
    result = {
        "updated_at": datetime.now().isoformat(),
        "data_start": df_class_returns.index[0].strftime("%Y-%m-%d"),
        "data_end": df_class_returns.index[-1].strftime("%Y-%m-%d"),
        "trading_days": len(df_class_returns),
        "asset_classes": ordered_classes,
        "default_vols": {ac: round(float(ann_vols[ac]), 6) for ac in ordered_classes},
        "default_returns": {ac: round(float(ann_returns[ac]), 6) for ac in ordered_classes},
        "correlation_matrix": [
            [round(float(corr_matrix.loc[ac_i, ac_j]), 4) for ac_j in ordered_classes]
            for ac_i in ordered_classes
        ],
    }
    
    return result


def print_summary(priors: dict):
    """打印结果摘要。"""
    print("\n" + "=" * 70)
    print("📊 资产先验参数更新结果")
    print("=" * 70)
    print(f"  数据区间: {priors['data_start']} → {priors['data_end']}")
    print(f"  交易日数: {priors['trading_days']}")
    print(f"  更新时间: {priors['updated_at']}")
    
    print("\n  📈 年化收益率先验:")
    for ac in priors['asset_classes']:
        ret = priors['default_returns'][ac]
        print(f"    {ac:8s}: {ret * 100:7.2f}%")
    
    print("\n  📉 年化波动率先验:")
    for ac in priors['asset_classes']:
        vol = priors['default_vols'][ac]
        print(f"    {ac:8s}: {vol * 100:7.2f}%")
    
    print("\n  📊 相关矩阵:")
    acs = priors['asset_classes']
    header = "         " + "  ".join([f"{ac[:4]:>6s}" for ac in acs])
    print(header)
    for i, ac_i in enumerate(acs):
        row = f"  {ac_i:6s}  " + "  ".join([f"{priors['correlation_matrix'][i][j]:6.2f}" for j in range(len(acs))])
        print(row)
    
    print("=" * 70)


def main():
    print("🚀 开始更新八大类资产波动率先验和相关矩阵...")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 加载基金池
    pool_by_class = load_fund_pool()
    total_funds = sum(len(v) for v in pool_by_class.values())
    print(f"\n📋 基金池: {len(pool_by_class)} 大类, {total_funds} 只基金")
    for ac, codes in pool_by_class.items():
        print(f"  {ac}: {len(codes)} 只")
    
    # 2. 下载 NAV 数据
    all_codes = []
    for codes in pool_by_class.values():
        all_codes.extend(codes)
    all_codes = list(set(all_codes))  # 去重
    
    df_nav = fetch_nav_data(all_codes, years=3)
    
    # 3. 计算各类等权日收益率
    print("\n📊 计算大类资产等权日收益率...")
    df_class_returns = compute_asset_class_returns(df_nav, pool_by_class)
    
    # 4. 计算先验参数
    print("\n🧮 计算先验参数...")
    priors = compute_priors(df_class_returns)
    
    # 5. 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(priors, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已保存到: {OUTPUT_FILE}")
    
    # 6. 打印摘要
    print_summary(priors)
    
    return priors


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        traceback.print_exc()
        sys.exit(1)
