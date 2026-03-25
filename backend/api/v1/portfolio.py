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


@router.post("/rebalance")
async def trigger_rebalance(
    request: RebalanceRequest,
    background_tasks: BackgroundTasks,
):
    """
    触发组合再平衡计算 (模拟返回 API Contract Interface 2)
    """
    # TODO: Phase 2 — 真实对接 Celery 异步任务
    return {
        "status": "success",
        "summary_text": "客户持仓与基准相比差异巨大，重点加配宏观高景气品种...",
        "instructions": [
            {
               "code": "000979.OF",
               "name": "核心资产精选混合",
               "asset_class": "大盘价值",
               "action_tag": "加仓", 
               "delta_amount": 10500,  
               "delta_w": 0.025
            },
            {
               "code": "002657.OF",
               "name": "新能源主题",
               "asset_class": "高成长",
               "action_tag": "清仓", 
               "delta_amount": -50000,
               "delta_w": -0.150
            }
        ]
    }


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
