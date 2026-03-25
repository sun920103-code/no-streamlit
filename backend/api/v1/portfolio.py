"""
组合管理 API — 配置查询、再平衡触发
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()


class PortfolioConfigResponse(BaseModel):
    total_capital_rmb: float
    target_annual_return: float
    min_liquidity_ratio: float
    max_single_asset_weight: float
    max_drawdown_limit: float
    asset_classes: list


class RebalanceRequest(BaseModel):
    risk_preference: str = "moderate"  # conservative / moderate / aggressive
    use_ai_views: bool = True
    custom_views: Optional[Dict[str, float]] = None


class RebalanceResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.get("/config", response_model=PortfolioConfigResponse)
async def get_portfolio_config():
    """获取当前组合配置参数"""
    from core.config import settings
    return PortfolioConfigResponse(
        total_capital_rmb=settings.total_capital_rmb,
        target_annual_return=settings.target_annual_return,
        min_liquidity_ratio=settings.min_liquidity_ratio,
        max_single_asset_weight=settings.max_single_asset_weight,
        max_drawdown_limit=settings.max_drawdown_limit,
        asset_classes=[
            "货币现金", "纯债固收", "混合债券", "短债理财",
            "固收增强", "量化对冲", "股票多头", "黄金商品",
        ],
    )


@router.post("/rebalance", response_model=RebalanceResponse)
async def trigger_rebalance(
    request: RebalanceRequest,
    background_tasks: BackgroundTasks,
):
    """
    触发组合再平衡计算 (异步)

    返回 task_id，前端可通过 WebSocket 或轮询获取进度。
    """
    import uuid
    task_id = str(uuid.uuid4())

    # TODO: Phase 2 — 对接 Celery 异步任务
    # background_tasks.add_task(run_rebalance, task_id, request)

    return RebalanceResponse(
        task_id=task_id,
        status="queued",
        message="再平衡任务已提交，请通过 /status/{task_id} 查询进度",
    )


@router.get("/status/{task_id}")
async def get_rebalance_status(task_id: str):
    """查询再平衡任务进度"""
    # TODO: Phase 2 — 从 Celery/Redis 获取实际状态
    return {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "任务排队中 (Celery 尚未对接)",
    }
