
from __future__ import annotations
from modules.logging_config import get_plugin_logger
logger = get_plugin_logger()

class Base_URLS_Single_Tone:
    _instances = {}
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #         cls._instance._initialized = False
    #     return cls._instance
    
    def __init__(self):
        if self._initialized:
            try:
                ### 데이터베이스에서 데이터 로드가 우선순위임 : 
                ### 향후 server => ws 로 받으면 DB 저장
                ### DB 에서 로드 후 적요할 것임.
                self.apply_db_data_to_attributes()
            except Exception as e:
                logger.error(f"Error loading database data: {e}")
            return
        # 여기에 초기화 코드 작성
        self._initialized = True


    ###  필요 메소드
    def apply_data_to_attributes(self, data:list[dict]):
        try:
            self.save_db_data(data)
            self.set_db_data_to_attributes(data)
        except Exception as e:
            logger.error(f"Error applying data to attributes: {e}")


    def apply_db_data_to_attributes(self):
        db_datas = self.load_db_data()
        if db_datas:
            self.set_db_data_to_attributes(db_datas)

    def load_db_data(self) -> list[dict]:
        return []
    
    def save_db_data(self, data:list[dict]):
        try:
            pass
        except Exception as e:
            logger.error(f"Error saving database data: {e}")

    
    def set_db_data_to_attributes(self, data:list[dict]):
        try:
            for item in data:
                setattr(self, item['key'], item['value'])
        except Exception as e:
            logger.error(f"Error setting database data to attributes: {e}")

        
    def get(self, attrName:str):
        """ attrName 에 해당하는 WS_URL 값을 반환 """
        try:
            return getattr (self, attrName)
        except Exception as e:
            logger.error ( f' : get : {e}')
            return None
