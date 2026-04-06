import os
import sys
import tempfile
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict, List, Any
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.append(LEGACY_SERVICES_DIR)

router = APIRouter(prefix="/export", tags=["报表生成"])

class ExportPdfRequest(BaseModel):
    diagnose_state: Dict[str, Any]

@router.post("/generate_diagnose_pdf")
async def generate_diagnose_pdf(payload: ExportPdfRequest):
    """
    接收前端收集好的 Diagnoses 结果状态，投递给后厨原始的 PDF 生成器，以文件响应流形式返回。
    """
    try:
        from services.report_pdf import generate_pdf_report
    except ImportError as e:
        logger.error(f"Failed to load PDF generator: {e}")
        raise HTTPException(status_code=500, detail="PDF 报告生成引擎加载失败")

    # The payload MUST mimic the original Streamlit st.session_state structure exactly
    # otherwise the PDF engine would crash because it uses `state.get('df_holdings_val')` etc.
    state = payload.diagnose_state

    # 异步生成 PDF 的字节数组 (防止 CPU intensive 画图操作导致 Uvicorn 堵塞)
    try:
        pdf_bytes = await run_in_threadpool(generate_pdf_report, state)
    except Exception as e:
        logger.error(f"Generate PDF error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PDF 图形渲染异常: {str(e)}")
        
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="生成的 PDF 流为空白")

    # 创建一个临时文件来存放 PDF
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    
    # 使用 FileResponse 返还给前端供浏览器拦截下载
    return FileResponse(
        path=tmp.name, 
        filename="智能分析诊断战报.pdf", 
        media_type="application/pdf",
        background=None  # Can use background tasks to delete the file later if necessary
    )

@router.post("/generate_diagnose_docx")
async def generate_diagnose_docx(payload: ExportPdfRequest):
    """
    Campaign 13: 提取动态 Word (DOCX) 底稿
    接收相同的诊断状态对象，投递给 Python-docx 引擎生成报告。
    """
    try:
        from services.report_word import generate_docx_report
    except ImportError as e:
        logger.error(f"Failed to load DOCX generator: {e}")
        raise HTTPException(status_code=500, detail="Word 报告生成引擎加载失败")

    state = payload.diagnose_state

    # 异步生成 DOCX 的字节数组
    try:
        docx_bytes = await run_in_threadpool(generate_docx_report, state)
    except Exception as e:
        import traceback
        logger.error(f"Generate DOCX error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Word 文档渲染异常: {str(e)}")
        
    if not docx_bytes:
        raise HTTPException(status_code=500, detail="生成的 Word 流为空白")

    # 创建一个临时文件来存放 docx
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.write(docx_bytes)
    tmp.close()
    
    return FileResponse(
        path=tmp.name, 
        filename="智能诊断底稿.docx", 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=None
    )
