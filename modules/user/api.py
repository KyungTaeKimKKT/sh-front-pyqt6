from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import requests, base64, json
import datetime

from modules.global_event_bus import event_bus
from modules.envs.global_bus_event_name import global_bus_event_name as GBus
# from modules.PyQt.User.loading import LoadingDialog
import modules.user.utils as utils

from info import Info_SW as INFO
# INFO = Info_SW()

from modules.PyQt.User.toast import User_Toast
import traceback
from modules.logging_config import get_plugin_logger
# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class Api_SH(QObject):
	"""
		API 통신 클래스
		중요 메소드:
			get_jwt() : login 정상이면 True, 그외면 False
			Send() : dataObj 유무로 , 그리고 id로 , post, patch 결정하여 send
			re_login() : 자동 login 경우는, ????
			set_refresh_token() : refresh token 설정
			set_access_token() : access token 설정
			get_refresh_token() : refresh token 반환
			get_access_token() : access token 반환
			regen_access_key() : access key 재발급
			getAPI_View() : get 요청 반환
			getlist() : get 요청 반환
			getObj() : get 요청 반환
			getObj_byURL() : get 요청 반환
	"""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.event_bus = event_bus
		self.event_bus_type = GBus.API_STATUS
		self._jwt_refresh_timer = None
		self.access_token = None
		self.refresh_token = None

	# def start_jwt_refresh_timer(self):
	# 	"""JWT 리프레시 주기적 타이머 시작"""
	# 	if self._jwt_refresh_timer is None:
	# 		self._jwt_refresh_timer = QTimer(self)
	# 		self._jwt_refresh_timer.timeout.connect(self._check_and_refresh_jwt)
	# 	self._jwt_refresh_timer.start(INFO.JWT_REFRESH_TIMER)

	def fetch_fastapi(self, url:str):
		"""
			fastapi 호출
		"""
		try:
			response = requests.get(INFO.URI_FASTAPI+url, headers=self._get_header())
			return response.ok, response.json()
		except Exception as e:
			logger.error(f"fastapi 호출 실패: {e}")
			return False, []

	def start_jwt_refresh_timer(self):
		"""JWT 리프레시 타이머 시작 - 만료 시간 기반 1회성 타이머"""
		if INFO.IS_DEV:
			logger.info(f" : start_jwt_refresh_timer : 토큰 갱신 타이머 시작")
		self._schedule_next_refresh()
	
	def _schedule_next_refresh(self):
		"""다음 리프레시 시점 계산 및 타이머 설정"""
		if self.access_token is None or self.refresh_token is None:
			logger.error(f"토큰이 없읍니다. 로그인 후 다시 시도해주세요.")
			# 토큰이 아직 없는 경우 (로그인 전)
			return
			
		self.refresh_exp_time = self.decoder_jwt_payload(token=self.refresh_token).get('exp')
		self.access_exp_time = self.decoder_jwt_payload(token=self.access_token).get('exp')

		# 액세스 토큰과 리프레시 토큰 만료 시간 확인
		access_remaining = self.get_expired_time_gap(self.access_exp_time)
		refresh_remaining = self.get_expired_time_gap(self.refresh_exp_time)
		
		# 갱신 시점 계산 (만료 시간보다 REFRESH_기준 초 전)
		access_refresh_at = max(0, access_remaining - INFO.REFRESH_기준)
		refresh_refresh_at = max(0, refresh_remaining - INFO.REFRESH_기준)
		
		# 더 빨리 만료되는 토큰 기준으로 타이머 설정
		next_refresh_ms = min(access_refresh_at, refresh_refresh_at) * 1000  # 밀리초 변환
		
		# 안전장치: 최소 1초, 최대 1시간으로 제한
		next_refresh_ms = max(1000, min(next_refresh_ms, 3600000))
		
		# 타이머 설정
		if self._jwt_refresh_timer is None:
			self._jwt_refresh_timer = QTimer(self)
			self._jwt_refresh_timer.setSingleShot(True)
			self._jwt_refresh_timer.timeout.connect(self._refresh_and_reschedule)
		else:
			self._jwt_refresh_timer.stop()
			
		self._jwt_refresh_timer.start(int(next_refresh_ms))
		if INFO.IS_DEV:
			logger.info(f" : _schedule_next_refresh : 다음 JWT 갱신 예정: {next_refresh_ms/1000:.1f}초 후")
		
	def _refresh_and_reschedule(self):
		"""토큰 갱신 후 다음 타이머 재설정"""
		refresh_needed = self.is_refresh_필요()
		if refresh_needed:
			if INFO.IS_DEV:
				logger.info(f"JWT 토큰 갱신 완료: {refresh_needed}")
		
		# 다음 갱신 일정 설정
		self._schedule_next_refresh()

	def stop_jwt_refresh_timer(self):
		"""JWT 리프레시 타이머 중지"""
		if self._jwt_refresh_timer and self._jwt_refresh_timer.isActive():
			self._jwt_refresh_timer.stop()
			
	def _check_and_refresh_jwt(self):
		"""타이머에 의해 호출되는 JWT 체크 및 리프레시 메서드"""
		refresh_needed = self.is_refresh_필요()
		if refresh_needed:
			if INFO.IS_DEV:
				logger.info(f"JWT 토큰 갱신: {refresh_needed}")

	def change_password_and_refresh_token(self, sendData:dict=None, url:str=None ) -> bool:
		"""
		비밀번호 변경 및 토큰 갱신을 처리하는 특수 메소드
		
		Args:
			data (dict): 비밀번호 변경 요청 데이터
			url (str): 비밀번호 변경 API 엔드포인트
		Returns:
			bool: 성공 여부
		"""
		try:
			url = url or INFO.URL_PASSWORD_CHANGE
			# 비밀번호 변경 요청 전송
			_isOk, _res = self.post(url, sendData)
			
			if _isOk:
				# 새 토큰 저장
				token_data = _res['tokens']
				if 'access' in token_data and 'refresh' in token_data:
					self.access_token = token_data['access']
					self.refresh_token = token_data['refresh']
					### local_db 업데이트
					from local_db.models import Login_User
					Login_User.objects.filter(user_id=INFO.USERID).update(
						refresh_token = self.refresh_token,
					)					
				return True
			else:
				return False
				
		except Exception as e:
			logger.error(f"비밀번호 변경 및 토큰 갱신 중 오류: {str(e)}")
			return False


	def get_jwt(self,login_info:dict):
		""" 실제로 login 하는 메서드, login이 정상이면 True, 그외면 False"""
		self.login_info = login_info
		response = requests.post(INFO.AUTH_URL, self.login_info)
		if response.ok:                
			res = response.json()
			return self.process_ok(res)
		else : 
			return False, {}

	def process_ok(self, res:dict):
		self.refresh_token = res['refresh']
		self.access_token = res['access']
		self.start_jwt_refresh_timer()
		if INFO.USERID == -1:		
			INFO._update_UserInfo(res['user_info'])
		return True, res
		
	def Send_bulk(self, url:str, added_url:str=None, detail:bool=True, dataObj:dict={}, sendData:dict={}, sendFiles=None  , **kwargs) ->tuple[bool, dict]:
		"""
			dataObj 유무로 , 그리고 id로 , post, patch 결정하여 send
		"""
		ID = dataObj.get('id', -1)
		if detail:
			url = f"{url}/{ID}/{added_url}/".replace('//', '/')
		else:
			url = f"{url}/{added_url}/".replace('//', '/')

		if ID > 0:
			return self.patch(url= url,
								data=sendData,
								files=sendFiles,
								**kwargs
								 )
		else:
			return self.post(url= url,
								data=sendData,
								files=sendFiles,
								**kwargs
								 )

	def Send( self, url, dataObj:dict, sendData:dict, sendFiles=None  , **kwargs) ->tuple[bool, dict]:
		"""
			dataObj 유무로 , 그리고 id로 , post, patch 결정하여 send
		"""
		if bool(dataObj):
			ID = dataObj.get('id', -1)
			if ID > 0:
				return self.patch(url= url+ str(ID) +'/',
								data=sendData,
								files=sendFiles,
								**kwargs
								 )
		
		return self.post(url= url,
								data=sendData,
								files=sendFiles,
								**kwargs
								 )

	def Send_json( self, url, dataObj:dict, sendData:dict, sendFiles=None  , headers={'Content-Type': 'application/json'}) ->tuple[bool, dict]:
		"""
			dataObj 유무로 , 그리고 id로 , post, patch 결정하여 send
		"""
		if bool(dataObj):
			ID = dataObj.get('id', -1)
			if ID > 0:
				return self.patch_json(url= url+ str(ID) +'/',
								data=sendData,
								headers=headers
								 )
		
		return self.post_json(url= url,
								data=sendData,
								headers=headers
								 )

	def Send_json_with_detail(self, url:str, added_url:str=None, detail:bool=True, dataObj:dict={}, sendData:dict={}, sendFiles=None  , **kwargs):
		"""
			25-9-1  신규, dataObj 유무로 , 그리고 id로 , post, patch 결정하여 send json
		"""
		kwargs.update({'headers':{'Content-Type': 'application/json'}})
		ID = dataObj.get('id', -1)
		if detail:
			url = f"{url}/{ID}/{added_url}/".replace('//', '/')
		else:
			url = f"{url}/{added_url}/".replace('//', '/')
		
		return self.patch_json(url= url, data=sendData ,**kwargs)
	
	def patch_json(self, url, data:dict, files=None, **kwargs):
		response = requests.patch(url=INFO.URI+url, json=data, files=files, headers=self._get_header(**kwargs) )
		return self.return_result(response)

	def post_json(self, url, data:dict, files=None, **kwargs):
		response = requests.post(url=INFO.URI+url, json=data, files=files, headers=self._get_header(**kwargs) )
		return self.return_result(response)

	def re_login(self):
		"""
			self.login_info를 통해서 재 login
		"""
		return self.get_jwt(login_info=self.login_info)
	
	def set_refresh_token(self, refresh_token:str):
		self.refresh_token = refresh_token
	
	def set_access_token(self, access_token:str):
		self.access_token = access_token

	def get_refresh_token(self) ->str:
		return self.refresh_token
	
	def get_access_token(self) ->str:
		return self.access_token
	
	def regen_access_key(self, refresh_token:str=None) ->bool:
		"""
			REFRESH_URL에 접속하여 access payload update함, 
			성공시 True, 실패시 False	
		"""
		self.refresh_token = refresh_token or self.refresh_token
		try: 
			response = requests.post(INFO.REFRESH_URL, {"refresh":self.refresh_token})
			if response.ok:
				res = response.json()
				self.access_token = res['access']
				self.access_exp_time = self.decoder_jwt_payload(token=self.access_token).get('exp')
				return True
			else:
				return False
		except:
			return False
		
	def getAPI_View(self, url:str):
		response = requests.get( INFO.URI+url, headers=self._get_header() )

		return ( response.ok,  response.json() )

	def getlist(self, url:str , **kwargs):		
		response = requests.get( INFO.URI+url, headers=self._get_header(), **kwargs)
		return self.return_result(response)
	
	def getObj(self, url:str, id:int):
		response = requests.get( INFO.URI+url+str(id) +'/', headers=self._get_header() )
		return self.return_result(response)
	
	def getObj_byURL(self, url:str, timeout:int=5):
		response = requests.get( INFO.URI+url, headers=self._get_header(), timeout=timeout )
		return self.return_result(response)
		
	def patch(self, url:str, data:dict, files=None, **kwargs):
		response = requests.patch(url=INFO.URI+url, data=data, files=files, headers=self._get_header(**kwargs) )
		return self.return_result(response)

	def post(self, url, data:dict, files=None, **kwargs):

		response = requests.post(url=INFO.URI+url, data=data, files=files, headers=self._get_header(**kwargs) )

		return self.return_result(response)
	
	def post_raw_return( self, url, data:dict, files=None ):
		return requests.post(url=INFO.URI+url, data=data, files=files, headers=self._get_header() )

	def delete(self, url:str):
		response = requests.delete(url=INFO.URI+url ,headers=self._get_header())
		if response.status_code ==  204 : return True
		else: return False


	def return_result(self, response:requests.Response):

		try:
		# 네트워크 상태 시그널 발생
			self.event_bus.publish(self.event_bus_type, response.ok)
			# self.parent.render_Network_status(response.ok)

			if response.ok:
				result_data = response.json()
				return True, result_data
			else:
				code = response.status_code
				error_message = f"{response.url} : {code} {INFO.STATUS_CODE.get(code)}"

				# 에러 정보를 포함한 시그널 발생
				try:
					result_data = response.json() if response.content else {}
				except:
					result_data = {}
					
				error_data = {
					"status_code": code,
					"message": error_message,
					"data": result_data
				}
				
				if isinstance(result_data, (dict, list)):
					return False, result_data
				return False, []
			
		except Exception as e:
			self.event_bus.publish(self.event_bus_type, False)
			error_msg = f"API 응답 처리 중 오류 발생: {str(e)}"
			logger.error(error_msg)
			logger.error(traceback.format_exc())
			self.event_bus.publish(self.event_bus_type, False)

			return False, []
	
	def _get_header(self, **kwargs) ->dict:
		default = {
					'Authorization'  : 'JWT '+ self.access_token
				}
		if 'headers' in kwargs:
			default.update ( kwargs['headers'])
		# logger.debug(f"default headers: {default}")
		return default

	def is_refresh_필요(self) -> list[str,str]:
		"""
			refresh가 필요하면 regen함.
			REFRESH_기준 = 1200.0 초 미만이면 해당 ['access','refresh'] return 
		"""		
		result = []
		if (sec_Access:=self.get_expired_time_gap(exp_time=self.access_exp_time)) < INFO.REFRESH_기준: 
			self.regen_access_key()
			result.append('access')
		# if (sec_Refresh:= self.get_expired_time_gap(exp_time=self.refresh_exp_time) ) < INFO.REFRESH_기준: 
		# 	self.re_login()
		# 	result.append('refresh')
		return result

	def decoder_jwt_payload(self, token:str=None) -> dict:
		"""
			각 payload를 decode하여 json file로 분리. 
			payload : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE5OTg3OTY5LCJpYXQiOjE3MTk5ODQzNjksImp0aSI6IjBjYzUzMmFjNjYzYzQwZjdiYjFjYjQ3OTA0NmJhMDExIiwidXNlcl9pZCI6MX0.OOJ11CdfgGO4tmKDYWjNtJcgmLN-AT-pHvDWXZJdcj4
			==>  {'token_type': 'access', 'exp': 1719987473, 'iat': 1719983873, 'jti': '193e6125d40c4ccb8dade245e40ea13a', 'user_id': 1}
		"""
		tokenSplit = token.split(".")[1]
		token_padding수정 = tokenSplit + '=' * (-len(tokenSplit) % 4)
		base64_decode_data = base64.b64decode(token_padding수정 )
		return json.loads(base64_decode_data.decode("utf-8"))
	
	# https://stackoverflow.com/questions/748491/how-do-i-create-a-datetime-in-python-from-milliseconds
	def get_expired_time_gap(self, exp_time:int=None) -> float:
		"""
			return  expire remaining time seconds
		"""
		dt = datetime.datetime.fromtimestamp(exp_time) #, tz=datetime.timezone.utc)
		return (dt- datetime.datetime.now()).total_seconds() 



class Api_SH_update(Api_SH):
	def getlist(self, url:str='') ->list:
		response = requests.get( INFO.URI + url )
		# utils.pprint(response.json())
		return response.json()
	

	def check_update(self, url:str, app_name:str, os:str, 종류:str, current_version:float):
		"""
		현재 버전 정보를 서버에 보내고 업데이트 필요 여부를 확인합니다.
		
		Args:
			app_name (str): 앱 이름
			os (str): 운영체제 코드
			current_version (float): 현재 버전
			
		Returns:
			Response: 서버 응답 객체
			- 200 OK: 업데이트 필요 (응답 본문에 최신 버전 정보)
			- 204 No Content: 업데이트 불필요
		"""
		url = f"{INFO.API_Update_Check_URL}"
		params = {
			"App_name": app_name,
			"OS": os,
			"종류": 종류,
			"버젼": str(current_version)
		}

		return requests.get ( INFO.URI+url, params=params)


# api= Api_SH(AUTH_URL)
# api.get_jwt()
# result = api.getlist(URI+ 'api/users/users/?page_size=0')



