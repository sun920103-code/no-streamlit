"""
import_nav_to_sqlite.py — 将 backend/data/ 中已有的 sync_*.csv 和 client_benchmarks.csv
导入到 SQLite 净值蓄水池中，为未来的增量更新打基础。

用法: python scripts/import_nav_to_sqlite.py
效果: 在 backend/data/ 下生成 fund_nav_cache.db（约 5-10MB）

这是一个只读脚本，不会修改或删除任何现有文件。
"""
import os
import sys
import glob
import sqlite3
import pandas as pd
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "fund_nav_cache.db")


def init_db(conn):
    """创建表结构"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_nav (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            nav_adj REAL,
            PRIMARY KEY (code, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_index (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            close REAL,
            PRIMARY KEY (code, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nav_code ON daily_nav(code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nav_date ON daily_nav(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_idx_code ON daily_index(code)")
    conn.commit()


def import_sync_csvs(conn):
    """从 sync_*.csv 文件中导入基金净值"""
    csv_files = glob.glob(os.path.join(DATA_DIR, "sync_*.csv"))
    # 只取 nav csv（不含 _meta.csv）
    nav_csvs = [f for f in csv_files if "_meta" not in f]

    if not nav_csvs:
        print("⚠️ 未找到 sync_*.csv 文件")
        return 0

    print(f"📂 发现 {len(nav_csvs)} 个 sync_*.csv 文件")

    # 找最大的那个（数据最全）作为主要来源，其余作为补充
    nav_csvs.sort(key=lambda f: os.path.getsize(f), reverse=True)

    total_inserted = 0
    all_codes = set()

    for i, csv_path in enumerate(nav_csvs):
        fname = os.path.basename(csv_path)
        fsize = os.path.getsize(csv_path) / 1024
        try:
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if df.empty:
                continue

            # 列名就是基金代码（bare code，6位）
            for code in df.columns:
                series = df[code].dropna()
                if len(series) == 0:
                    continue

                rows = []
                for dt, val in series.items():
                    try:
                        date_str = dt.strftime("%Y-%m-%d")
                        nav_val = float(val)
                        if nav_val > 0:
                            rows.append((str(code).strip(), date_str, nav_val))
                    except (ValueError, TypeError):
                        continue

                if rows:
                    conn.executemany(
                        "INSERT OR IGNORE INTO daily_nav (code, date, nav_adj) VALUES (?, ?, ?)",
                        rows
                    )
                    total_inserted += len(rows)
                    all_codes.add(str(code).strip())

            conn.commit()
            if i < 3 or i == len(nav_csvs) - 1:
                print(f"  ✅ [{i+1}/{len(nav_csvs)}] {fname} ({fsize:.0f}KB): {len(df.columns)} 只基金, {len(df)} 天")

        except Exception as e:
            print(f"  ⚠️ {fname} 读取失败: {e}")

    return total_inserted, all_codes


def import_benchmarks(conn):
    """从 client_benchmarks.csv 导入基准指数"""
    bm_path = os.path.join(DATA_DIR, "client_benchmarks.csv")
    if not os.path.exists(bm_path):
        print("⚠️ 未找到 client_benchmarks.csv")
        return 0

    try:
        df = pd.read_csv(bm_path, index_col=0, parse_dates=True)
        total = 0
        for code in df.columns:
            series = df[code].dropna()
            rows = []
            for dt, val in series.items():
                try:
                    rows.append((str(code).strip(), dt.strftime("%Y-%m-%d"), float(val)))
                except (ValueError, TypeError):
                    continue
            if rows:
                conn.executemany(
                    "INSERT OR IGNORE INTO daily_index (code, date, close) VALUES (?, ?, ?)",
                    rows
                )
                total += len(rows)
        conn.commit()
        print(f"  ✅ 基准指数: {len(df.columns)} 个指数, {len(df)} 天, {total} 条记录")
        return total
    except Exception as e:
        print(f"  ⚠️ 基准指数导入失败: {e}")
        return 0


def main():
    print("=" * 60)
    print("  净值蓄水池初始化 — 从现有 CSV 导入到 SQLite")
    print("=" * 60)
    print(f"  数据目录: {DATA_DIR}")
    print(f"  数据库路径: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # 导入基金净值
    print("📊 [1/2] 导入基金净值...")
    nav_result = import_sync_csvs(conn)
    if isinstance(nav_result, tuple):
        nav_count, nav_codes = nav_result
    else:
        nav_count, nav_codes = nav_result, set()

    # 导入基准指数
    print("\n📊 [2/2] 导入基准指数...")
    idx_count = import_benchmarks(conn)

    # 写入元数据
    conn.execute(
        "INSERT OR REPLACE INTO sync_meta (key, value) VALUES (?, ?)",
        ("last_import", datetime.now().isoformat())
    )
    conn.execute(
        "INSERT OR REPLACE INTO sync_meta (key, value) VALUES (?, ?)",
        ("fund_count", str(len(nav_codes)))
    )
    conn.commit()

    # 统计
    nav_total = conn.execute("SELECT COUNT(*) FROM daily_nav").fetchone()[0]
    idx_total = conn.execute("SELECT COUNT(*) FROM daily_index").fetchone()[0]
    nav_codes_count = conn.execute("SELECT COUNT(DISTINCT code) FROM daily_nav").fetchone()[0]
    idx_codes_count = conn.execute("SELECT COUNT(DISTINCT code) FROM daily_index").fetchone()[0]

    # 日期范围
    nav_min = conn.execute("SELECT MIN(date) FROM daily_nav").fetchone()[0]
    nav_max = conn.execute("SELECT MAX(date) FROM daily_nav").fetchone()[0]

    conn.close()

    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)

    print()
    print("=" * 60)
    print("  ✅ 净值蓄水池初始化完成!")
    print("=" * 60)
    print(f"  基金净值: {nav_codes_count} 只基金, {nav_total:,} 条记录")
    print(f"  基准指数: {idx_codes_count} 个指数, {idx_total:,} 条记录")
    print(f"  日期范围: {nav_min} → {nav_max}")
    print(f"  数据库大小: {db_size:.1f} MB")
    print(f"  文件位置: {DB_PATH}")
    print()
    print("  下一步: 等 Wind 额度恢复后，每天只需增量拉取 1 天数据即可。")
    print("=" * 60)


if __name__ == "__main__":
    main()
