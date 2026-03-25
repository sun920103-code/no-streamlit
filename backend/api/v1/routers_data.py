"""
Data API — 外部数据同步 (Wind, 等等)
"""
import os
import json
import uuid
import subprocess
from typing import List
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# 存储全局轮询任务状态 (内存中)
_tasks_status = {}

class SyncClientPortfolioRequest(BaseModel):
    fund_codes: List[str]

def run_sync_script(task_id: str, fund_codes: List[str]):
    """执行实际的 Python 子进程同步（隔离 C++ Windpy dll）"""
    _tasks_status[task_id] = {"status": "processing", "message": "正在连接 Wind 终端并拉取底层数据...", "result": None}
    
    codes_str = ",".join(fund_codes)
    
    # 确定输出路径: backend/data/sync_<task_id>.csv
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(backend_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_csv = os.path.join(data_dir, f"sync_{task_id}.csv")
    
    script_path = os.path.join(backend_dir, "scripts", "sync_client_holdings.py")
    
    logger.info(f"Task {task_id} - Spawning subprocess: python {script_path} <codes> {out_csv}")
    
    try:
        env = os.environ.copy()
        # 确保能 import services.wind_fetcher
        backend_parent = os.path.dirname(backend_dir)  # d:\No Streamlimit\ (Because services is likely in backend or root)
        
        # Original script had: sys.path.insert(0, _ROOT), and _ROOT was the level above scripts.
        # Wait, if script is in backend/scripts, then _ROOT is backend. We should just append 'backend' to PYTHONPATH.
        env['PYTHONPATH'] = backend_dir + os.pathsep + env.get('PYTHONPATH', '')
        
        process = subprocess.run(
            ["python", script_path, codes_str, out_csv],
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env
        )
        
        # 解析输出里包含的 JSON
        result_payload = {}
        out_text = process.stdout
        
        if "__CLIENT_SYNC_RESULT_START__" in out_text and "__CLIENT_SYNC_RESULT_END__" in out_text:
            try:
                start_idx = out_text.find("__CLIENT_SYNC_RESULT_START__") + len("__CLIENT_SYNC_RESULT_START__")
                end_idx = out_text.find("__CLIENT_SYNC_RESULT_END__")
                json_str = out_text[start_idx:end_idx].strip()
                result_payload = json.loads(json_str)
            except Exception as e:
                logger.error(f"Task {task_id} JSON 解析失败: {e}")
                
        if process.returncode == 0 and result_payload.get("status") == "success":
            # Strict API Contract mapping
            api_data = {
                "status": "success",
                "data": {
                    "funds_matched": result_payload.get("n_funds", 0),
                    "funds_total": result_payload.get("n_funds", 0),
                    "prices_days": result_payload.get("n_days", 0),
                    "total_stocks_count": result_payload.get("n_holdings", 0),
                    "unique_stocks_count": result_payload.get("n_underlying", 0)
                }
            }
            _tasks_status[task_id] = {
                "status": "success",
                "message": "Wind 数据拉取成功！",
                "result": api_data
            }
        else:
            logger.error(f"Task {task_id} sync failed! Stdout:\n{process.stdout}\nStderr:\n{process.stderr}")
            error_detail = result_payload.get("detail", "底层进程发生异常或 WindPy 连接超时。")
            _tasks_status[task_id] = {
                "status": "error",
                "message": f"拉取失败: {error_detail}",
                "result": None
            }
            
    except Exception as e:
        logger.exception(f"System error in run_sync_script for task {task_id}")
        _tasks_status[task_id] = {
            "status": "error",
            "message": f"系统调用异常: {str(e)}",
            "result": None
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
        "message": "数据拉取请求已受理，进入后台执行"
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
    将这作为前端的核心配置边界展台数据。
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
                             "category": f"{ac_name} - {cat_name}"
                         })
                         
        # 对列表进行去重，确保干净
        seen = set()
        unique_pool = []
        for p in pool:
            if p["code"] not in seen:
                seen.add(p["code"])
                unique_pool.append(p)
                
        return {
            "status": "success",
            "count": len(unique_pool),
            "pool": unique_pool
        }
    except Exception as e:
        logger.error(f"Failed to load core fund pool: {e}")
        raise HTTPException(status_code=500, detail="无法读取底层白盒产品映射矩阵")
