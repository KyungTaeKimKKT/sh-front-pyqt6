from __future__ import annotations
from typing import Optional, Union
import json
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

def handle_api_response(msg:dict) -> tuple[ bool,Optional[dict], Optional[list|dict]]:
    """
    api_response 분석 함수
    event_bus 의 fetch 에서 받은 api_response 를 분석하여 반환하는 함수
    tuple[
    bool ==> is_ok
    Optional[dict] ==> pagination 정보
    Optional[list|dict]]  ==>  api_datas 
    """
    logger.info(f"handle_api_response: {json.dumps(msg)[:700]}")
    is_Pagenation = msg.get('is_Pagenation')
    is_ok = msg.get('is_ok')
    results = msg.get('results')
    pagination = None
    api_datas = None

    if is_ok:
        if is_Pagenation:
            if isinstance(results, dict):
                api_datas = results.pop('results')
                pagination = results
            else:
                api_datas = results
                pagination = None

        else:
            api_datas = results
            pagination = None

    else:  
        logger.error(f"handle_api_response: {msg}")

    return is_ok, pagination, api_datas