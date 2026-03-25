"""
全局配置管理 — 从环境变量和 .env 文件加载
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置 (优先读取环境变量, 其次 .env 文件)"""

    # ── 应用 ──
    app_name: str = "FOF 量化投资决策平台"
    debug: bool = False
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── 组合 ──
    total_capital_rmb: float = 4_400_000_000  # 44亿
    target_annual_return: float = 0.059       # 5.9%

    # ── 风控约束 ──
    min_liquidity_ratio: float = 0.15
    max_single_asset_weight: float = 0.20
    max_drawdown_limit: float = 0.02

    # ── API Keys ──
    llm_provider: str = "moonshot"
    llm_api_key: str = ""
    zhipu_api_key: str = ""
    deepseek_api_key: str = ""
    tavily_api_key: str = ""

    # ── Wind ──
    wind_enabled: bool = True

    # ── Risk Parity ──
    rp_min_weight: float = 0.02
    rp_max_weight: float = 0.40
    nlp_max_tilt: float = 0.10

    # ── Celery ──
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── 路径 ──
    raw_data_path: str = "data/raw/"
    db_path: str = "data/database/fof_data.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
