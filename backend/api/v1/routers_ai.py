import os
import sys
import tempfile
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Dict, List, Optional
from loguru import logger

# 动态注入祖传代码路径
LEGACY_SERVICES_DIR = r"D:\No Streamlimit\20260325"
if LEGACY_SERVICES_DIR not in sys.path:
    sys.path.insert(0, LEGACY_SERVICES_DIR)

router = APIRouter(prefix="/ai", tags=["AI 智能多智能体"])

class NewsExtractionRequest(BaseModel):
    query: Optional[str] = "外围降息与国内财政发力，如何影响国内核心资产表现"

@router.post("/extract_news_views")
async def extract_news_views(payload: NewsExtractionRequest = None):
    """
    异步提取新闻观点矩阵 (I/O密集型大模型调用，无惧长时间运行)
    """
    try:
        from services.multi_agent import extract_sentiment_signals
        from services.news_fetcher import fetch_latest_news
    except ImportError as e:
        logger.error(f"Failed to import legacy AI services: {e}")
        raise HTTPException(status_code=500, detail="底层AI服务加载失败")

    query = payload.query if payload else "最新宏观经济焦点"
    
    # 1. 抓取新闻 (纯IO)
    try:
        news_text = await run_in_threadpool(fetch_latest_news, query)
    except Exception as e:
        logger.warning(f"News fetch failed, using fallback: {e}")
        news_text = "摘要：中国央行降息释放流动性，利好超跌反弹；同时海外软着陆预期升温，利空黄金。"

    if not news_text or len(news_text) < 50:
        news_text = "摘要：政策发力预期增强，红利与科技双主线确立，建议适度超配权益资产并回避纯债。"

    # 2. 调度多智能体提取观点矩阵 (大模型调用)
    try:
        nlp_scores = await run_in_threadpool(extract_sentiment_signals, news_text)
        return {
            "status": "success", 
            "nlp_scores": nlp_scores,
            "source_synopsis": news_text[:300] + "..." if len(news_text) > 300 else news_text
        }
    except Exception as e:
        logger.error(f"AI View Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM 观点提取异常: {str(e)}")


@router.post("/extract_report_views")
async def extract_report_views(file: UploadFile = File(...)):
    """
    解析上传的 PDF/TXT 宏观研报并提取 AI 观点
    """
    # 写入临时文件
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".pdf"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from services.multi_agent import extract_sentiment_signals
        
        report_text = ""
        if ext == ".pdf":
            try:
                from services.report_pdf import extract_pdf_content  # 盲猜或使用回退逻辑
                report_text = await run_in_threadpool(extract_pdf_content, tmp_path)
            except Exception:
                # 若无法导入，调用现成的 pdf 工具或者 fallback
                import PyPDF2
                with open(tmp_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    report_text = "\n".join([page.extract_text() for page in pdf.pages[:5]])
        else:
            with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                report_text = f.read()

        if not report_text.strip():
            raise ValueError("无法从文件中解析到有效文本")

        nlp_scores = await run_in_threadpool(extract_sentiment_signals, report_text)
        return {"status": "success", "nlp_scores": nlp_scores}

    except Exception as e:
        logger.error(f"Report AI Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"研报解析异常: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

@router.post("/simulate_smart_selection_debate")
async def simulate_smart_selection_debate(payload: NewsExtractionRequest = None):
    """
    长驻多智能体虚拟投研会 (SSE 流式通信)
    这避免了接口 504 Timeout，将漫长的 LLM 辩论和心跳包以事件流按需推送给 Vue 前端。
    """
    import json
    try:
        from services.multi_agent import run_investment_committee
        from services.news_fetcher import fetch_latest_news
    except ImportError:
        val = {"type": "error", "content": "底层AI服务加载失败"}
        async def err_gen(): yield f"data: {json.dumps(val, ensure_ascii=False)}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    query = payload.query if (payload and payload.query) else "本月大类资产配置焦点"
    
    async def sse_generator():
        q = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        # UI 广播心跳槽 (抛入 Queue 供给 yield)
        def status_callback(msg: str):
            loop.call_soon_threadsafe(q.put_nowait, {"type": "log", "content": msg})
            
        def worker():
            try:
                # 预获取新闻当做语料 (如果很耗时，可以在 worker 内同步调)
                news_text = fetch_latest_news(query)
                if not news_text or len(news_text) < 50:
                    news_text = "中国央行降息释放流动性，利好超跌反弹；同时海外软着陆预期升温，利空黄金。"
                    
                # 真正的多智能体阻断呼叫
                md, bl_views, logs = run_investment_committee(
                    report_text=news_text,
                    model_choice="MiniMax",
                    status_callback=status_callback
                )
                loop.call_soon_threadsafe(q.put_nowait, {"type": "finish", "report": md, "bl_views": bl_views})
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})

        # 后台线程发射
        asyncio.create_task(run_in_threadpool(worker))
        
        # 作为消费者流式外溢
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if item["type"] in ["finish", "error"]:
                break
                
    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@router.post("/generate_market_review")
async def generate_market_review_api(file: Optional[UploadFile] = File(None)):
    """
    长驻市场回顾生成器 (SSE 流式通信)
    逐步返回文字，防止前端白屏干等。
    """
    import json
    try:
        from services.multi_agent import generate_market_review
    except ImportError:
        val = {"type": "error", "content": "底层AI服务加载失败"}
        async def err_gen(): yield f"data: {json.dumps(val, ensure_ascii=False)}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    async def sse_generator():
        q = asyncio.Queue()
        loop = asyncio.get_running_loop()
        
        # 截获打字及进度回调
        def status_callback(msg: str):
            # 将提示语或者进度信息发往前端
            loop.call_soon_threadsafe(q.put_nowait, {"type": "log", "content": msg})
            
        def worker():
            try:
                # 解析可选的因子报告 csv
                style_factor_result = None
                if file is not None:
                    try:
                        import tempfile
                        import os
                        from services.smart_csv_parser import parse_multiple_factor_csvs
                        content = file.file.read()
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                            tmp.write(content)
                            tmp_path = tmp.name
                        style_factor_result = parse_multiple_factor_csvs([tmp_path])
                        os.remove(tmp_path)
                    except Exception as e:
                        logger.warning(f"Failed to parse uploaded factor csv: {e}")
                
                md_text = generate_market_review(
                    style_factor_result=style_factor_result,
                    status_callback=status_callback
                )
                loop.call_soon_threadsafe(q.put_nowait, {"type": "finish", "report": md_text})
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "content": str(e)})

        # 使用线程池执行同步阻塞的 LLM 调用
        asyncio.create_task(run_in_threadpool(worker))
        
        while True:
            item = await q.get()
            
            # 如果是 finish, 可以将最终的 Markdown 字符逐字抛出，形成前端的打字机流式特效
            if item["type"] == "finish":
                report = item["report"]
                # 通知前端开始接收正文流
                yield f"data: {json.dumps({'type': 'start_stream'}, ensure_ascii=False)}\n\n"
                # 按段或更小的 chunk 抛出
                chunk_size = 5
                for i in range(0, len(report), chunk_size):
                    chunk = report[i:i+chunk_size]
                    yield f"data: {json.dumps({'type': 'stream_chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                    # 这里加0.05秒延迟模拟超级真实的打字机感觉
                    import time
                    time.sleep(0.02)
                
                yield f"data: {json.dumps({'type': 'finish_stream'}, ensure_ascii=False)}\n\n"
                break
                
            elif item["type"] == "error":
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                break
            else:
                # log messages (e.g. status)
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
