from __future__ import annotations
from modules.envs.base_urls_single_tone import Base_URLS_Single_Tone
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from modules.envs.api_urls import API_URLS

class FastAPI_URLS(API_URLS):

    @classmethod
    def get_URL(cls, name: str) -> str:
        base_url = getattr(cls, name, None)
        if base_url:
            return f"fastapi/{base_url}"
        raise AttributeError(f"{name} not found in API_URLS")
    

    def __getattr__(self, name):
        # 기존 API_URLS에 정의된 속성만 처리
        if hasattr(API_URLS, name):
            base_value = getattr(super(), name)
            return f"fastapi/{base_value.lstrip('/')}"
        raise AttributeError(f"{name} not found in FastAPI_URLS")
    




fastapi_urls = FastAPI_URLS()