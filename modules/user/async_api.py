from PyQt6.QtCore import QThread, pyqtSignal, QObject

import asyncio
import aiohttp

from config import Config as APP
from info import Info_SW as INFO
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Async_API_SH(QObject):
    signal_Process = pyqtSignal(int, int)
    signal_Finished = pyqtSignal(dict)
    signal_Response = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.headers = self.__get_header()

    def __get_header(self) -> dict:
        return APP.API._get_header()


    async def fetch(self, url):
        async with aiohttp.ClientSession(
            base_url= INFO.URI,
            headers=self.__get_header()
        ) as session:
            async with session.get( url) as response:
                if response.ok: # 요청 성공
                    _json = await response.json()
 # await 주의
                    return (True, _json)
                else: # 요청 실패
       
                    return (False, {})

    def Get(self, url):
        return asyncio.run( self.fetch(url))
    
    async def post ( self, url, data) ->None:

        async with aiohttp.ClientSession(
            base_url= INFO.URI,
            headers=self.__get_header()
        ) as session:
            try:
                # url이 '/'로 시작하는지 확인하고 수정
                if url.startswith('http'):
                    # url이 절대 경로인 경우 base_url 없이 직접 사용
                    full_url = url
                else:
                    # url이 상대 경로인 경우 '/'로 시작하는지 확인
                    if not url.startswith('/'):
                        url = '/' + url
                    full_url = url  # base_url이 이미 설정되어 있으므로 상대 경로만 사용
                async with session.post(url=full_url, json=data) as response:

                    if response.status == 200:  # 요청 성공
                        sendData = await response.json()

                        self.signal_Response.emit(sendData)
                        return (True, sendData)
                    else:  # 요청 실패
                        error_text = await response.text()

                        self.signal_Response.emit(None)
                        return (False, None)
            except Exception as e:

                import traceback
                traceback.print_exc()
                self.signal_Response.emit(None)
                return (False, None)



            # data 대신 json 파라미터 사용
            async with session.post( url=url, data=form_data) as response:

                if response.status == 200: # 요청 성공
                    sendData = await response.json()

                    self.signal_Response.emit(sendData )
                    return (True, sendData)
                else: # 요청 실패
  
                    self.signal_Response.emit(None)
                    return (False, None)
    
    async def post_getContents(self, url, data) -> None:
        async with aiohttp.ClientSession(
            base_url= INFO.URI,
            headers=self.__get_header()
        ) as session:
            async with session.post( url=url, data=data) as response:
                if response.ok: # 요청 성공
                    header = response.headers
                    empty_bytes = b''
                    result = empty_bytes
                    Total_cnt = int( header.get('Content-Length') )
                    count = 0
                    prevProgress = 0
                    buf_size = 128
                    while True:
                        progress =  int( count*buf_size / Total_cnt * 100 )

                        if not prevProgress == progress:
                            prevProgress = progress
                            self.signal_Process.emit( progress , Total_cnt )

                        chunk = await response.content.read(buf_size)
                        if chunk == empty_bytes:
                            break
                        result += chunk
                        count +=1
                    # 😀TypeError: a bytes-like object is required, not 'StreamReader'
                    # content = response.content
                    self.signal_Finished.emit({
                        'headers' :header,
                        'contents' : result,
                    })
                    # return (header, result)
                    # _json = await response.json()
                    # # print('결과:', _json ) # await 주의
                    # return _json
                else: # 요청 실패
  
                    self.signal_Finished({
                        'headers' : None,
                        'contents' : None,
                    })
    
    def Post_getContents(self, url, data):
        asyncio.run ( self.post_getContents(url, data ))

    def Post(self, url, data):
        return asyncio.run ( self.post(url, data) )