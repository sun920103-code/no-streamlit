"""
Celery 异步任务配置

Redis 作为 broker 和 result backend。
重计算任务（BL 模型、HRP 优化）在独立 worker 中执行，
崩溃不影响 FastAPI 主进程。
"""
from celery import Celery
from core.config import settings

celery_app = Celery(
    "fof_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=600,       # 单任务最大 10 分钟
    task_soft_time_limit=540,  # 9 分钟软超时
    worker_max_tasks_per_child=50,  # 防内存泄漏，每50任务重启 worker
)


@celery_app.task(bind=True, name="tasks.rebalance")
def run_rebalance_task(self, task_id: str, params: dict):
    """
    异步执行组合再平衡

    Phase 2 实现:
    1. 获取最新市场数据
    2. 运行 BL 模型生成观点
    3. HRP/Risk Parity 优化
    4. 合规检查
    5. 返回建议权重
    """
    self.update_state(state="PROGRESS", meta={"step": "初始化", "progress": 0})

    # TODO: 对接 services/ 模块
    result = {
        "task_id": task_id,
        "weights": {},
        "status": "not_implemented",
    }

    return result
