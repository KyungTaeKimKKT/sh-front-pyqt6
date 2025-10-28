from __future__ import annotations
from modules.envs.base_urls_single_tone import Base_URLS_Single_Tone
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

from collections import deque

class GlobalData_SingleTone( Base_URLS_Single_Tone ):

    server_db_status = deque(maxlen=300)


    def set( self, attrName:str, value:any) -> None:
        try:
            setattr (self, attrName, value )
        except Exception as e:
            logger.error(f"set error:{str(e)}")\
            
    def append_server_db_status(self, data:dict):
        self.server_db_status.append(data)


GlobalData = GlobalData_SingleTone()

    

