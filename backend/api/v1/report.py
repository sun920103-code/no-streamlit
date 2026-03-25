"""
报告生成 API — 市场回顾、投资建议报告
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class MarketReviewRequest(BaseModel):
    period: str = "weekly"  # daily / weekly / monthly


class ReportGenerateRequest(BaseModel):
    report_type: str = "full"  # full / summary / risk
    format: str = "markdown"   # markdown / docx / pdf


@router.post("/market-review")
async def generate_market_review(request: MarketReviewRequest):
    """
    生成市场回顾

    调用 LLM 生成中文市场回顾报告。
    """
    # TODO: Phase 2 — 对接 multi_agent.generate_market_review
    return {
        "period": request.period,
        "status": "not_implemented",
        "message": "市场回顾生成引擎将在 Phase 2 对接",
        "preview": "本周市场整体呈现震荡格局，A股主要指数涨跌互现...",
    }


@router.post("/generate")
async def generate_report(request: ReportGenerateRequest):
    """生成完整投资报告"""
    # TODO: Phase 2 — 对接 report_word / report_pdf
    return {
        "report_type": request.report_type,
        "format": request.format,
        "status": "not_implemented",
        "message": "报告生成引擎将在 Phase 2 对接",
    }


@router.get("/templates")
async def list_report_templates():
    """列出可用的报告模板"""
    return {
        "templates": [
            {"id": "full", "name": "完整投资报告", "description": "包含市场回顾、配置建议、风险分析"},
            {"id": "summary", "name": "简要概览", "description": "一页纸投资概览"},
            {"id": "risk", "name": "风险报告", "description": "压力测试 + 回撤分析"},
        ]
    }
