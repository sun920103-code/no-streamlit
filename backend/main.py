"""
FOF 量化投资决策平台 — FastAPI 后端入口
"""
import sys
import os

# 将 backend 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.v1 import portfolio, analysis, report
from core.config import settings

# ── 日志配置 ──
logger.add(
    "logs/backend_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    encoding="utf-8",
)

# ── 创建 FastAPI 应用 ──
app = FastAPI(
    title="FOF 量化投资决策平台",
    description="广东省属信托自有资金 FOF 系统 — FastAPI 后端 API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS 中间件 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["组合管理"])
app.include_router(analysis.router,  prefix="/api/v1/analysis",  tags=["分析计算"])
app.include_router(report.router,    prefix="/api/v1/report",    tags=["报告生成"])


# ── 健康检查 ──
@app.get("/api/health", tags=["系统"])
async def health_check():
    """系统健康检查"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "platform": "FOF 量化投资决策平台",
        "engine": "FastAPI",
    }


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FOF 量化平台后端启动成功")
    logger.info(f"📊 总资金规模: {settings.total_capital_rmb / 1e8:.0f} 亿元")
    logger.info(f"🎯 目标年化收益: {settings.target_annual_return * 100:.1f}%")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
