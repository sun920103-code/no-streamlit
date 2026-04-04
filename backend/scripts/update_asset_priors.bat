@echo off
REM ── 每月1日上午9点自动更新资产先验参数 ──
REM 由 Windows Task Scheduler 调用
REM 脚本内置30天新鲜度检查，重复执行不会浪费 Wind 额度
REM 如需强制更新: python scripts\update_asset_priors.py --force

cd /d "D:\No Streamlit\backend"
python scripts\update_asset_priors.py >> data\update_asset_priors.log 2>&1
