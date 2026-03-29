@echo off
REM ── 每周五下午4点自动更新资产先验参数 ──
REM 由 Windows Task Scheduler 调用

cd /d "D:\No Streamlit\backend"
python scripts\update_asset_priors.py >> data\update_asset_priors.log 2>&1
