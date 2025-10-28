from modules.common_import import *

from plugin_main.websocket.handlers.base_handlers import (
    Base_WSMessageHandler, Base_WSMessageHandler_V2, Base_WSMessageHandler_No_Thread
)

class Mixin_UsersHandler:

    def on_message_handle(self, msg:dict):
        self.msg = copy.deepcopy(msg)
        if not self.check_is_available(msg):
            return 
        self._parse_message(msg)
        try: 
            match self._main_type:
                case 'init':
                    if self._sub_type == 'response' and self._action == 'init':
                        self._handle_init()
                ### 밑에 case 는 reserver 상태임:
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case _:
                    logger.info(f"UsersHandler : handle : {self.action} 처리 안함")
                    return
            
        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())

    def _handle_init(self):
        """ init 처리 """
        INFO.ALL_USER = self._message
        INFO.MBO_사용자 = self._get_mbo_users()
        INFO.USER_MAP_ID_TO_USER = {user['id']: user for user in INFO.ALL_USER}
        INFO.USER_MAP_NAME_TO_USER = {user['user_성명']: user for user in INFO.ALL_USER}
        # if INFO._get_is_app_admin():
        #     Utils.generate_QMsg_Information(
        #         None, 
        #         title='사용자 초기화', 
        #         text='사용자 초기화 WS 수신 완료', 
        #         autoClose= 1000)

        self.event_bus.publish(
            self.event_name, 
            self._action
        )

    def _get_mbo_users(self):
        if INFO.ALL_USER:
            MBO_사용자 = [{'id': user['id'], 'user_성명': user['user_성명'], 'MBO_표시명_부서': user['MBO_표시명_부서']} 
                            for user in INFO.ALL_USER if user['MBO_표시명_부서'] and user['is_active']]
            sorted_data = sorted(
                MBO_사용자,
                key=lambda x: (0 if x["MBO_표시명_부서"] == "비정규" else 1, x["MBO_표시명_부서"], x["user_성명"])
            )
            return sorted_data
        return []



    def _handle_update(self):
        """ update 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._update_users(user_obj)
        elif isinstance( user_obj, list):
            for user_dict in user_obj:
                self._update_users(user_dict)

    def _handle_delete(self):
        """ delete 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._delete_users(user_obj)
        elif isinstance(user_obj, list):
            for user_dict in user_obj:
                self._delete_users(user_dict)

    def _handle_create(self):
        """ create 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._create_users(user_obj)
        elif isinstance( user_obj, list):
            for user_dict in user_obj: 
                self._create_users(  user_dict)


    def _create_users(self, user_dict:dict):
        INFO.ALL_USER.append(user_dict)



    def _update_users(self,  user_dict:dict):
        for idx, userObj in enumerate(INFO.ALL_USER):
            if userObj.get('id') == user_dict.get('id'):
                userObj.update(user_dict)

    def _delete_users(self, user_dict:dict):
        del_idx:Optional[int] = None
        for idx, userObj in enumerate(INFO.ALL_USER):
            if userObj.get('id') == user_dict.get('id'):
                del_idx = idx
                break
        if del_idx is not None:
            del INFO.ALL_USER[del_idx]

class UsersHandler_V2(Mixin_UsersHandler, Base_WSMessageHandler_V2):
    pass
 

class UsersHandler_No_Thread(Mixin_UsersHandler, Base_WSMessageHandler_No_Thread):
    pass

class UsersHandler(Base_WSMessageHandler):
    

    def handle(self, msg: Union[dict,list, None]):
        """ users message 처리 by action
            action : init, update, delete, create, ... 그외는 필요시
        """
        self.msg = copy.deepcopy(msg)

        try: 
            self.action = msg.get('action')
            self.event_name = f"{self.url}"
            match self.action:
                case 'init':
                    self._handle_init()
                case 'create':
                    self._handle_create()
                case 'update':
                    self._handle_update()
                case 'delete':
                    self._handle_delete()
                case _:
                    logger.info(f"UsersHandler : handle : {self.action} 처리 안함")
                    return
            
            ### 처리 완료 이벤트 발송 : 받는 곳은 UPDATE된 INFO.APP_권한 으로 처리함
            logger.info(f" : handle : {self.event_name} PUB 완료 : { len(INFO.ALL_USER)}")
            self.event_bus.publish(
                self.event_name, 
                True
            )

        except Exception as e:
            logger.error(f"AppAuthorityHandler : handle : {e}")
            logger.error(traceback.format_exc())
    
    def _handle_init(self):
        """ init 처리 """
        INFO.ALL_USER = self.msg.get('message')
        INFO.MBO_사용자 = self._get_mbo_users()
        INFO.USER_MAP_ID_TO_USER = {user['id']: user for user in INFO.ALL_USER}
        INFO.USER_MAP_NAME_TO_USER = {user['user_성명']: user for user in INFO.ALL_USER}
        if INFO._get_is_app_admin():
            Utils.generate_QMsg_Information(
                None, 
                title='사용자 초기화', 
                text='사용자 초기화 WS 수신 완료', 
                autoClose= 1000)

    def _get_mbo_users(self):
        if INFO.ALL_USER:
            MBO_사용자 = [{'id': user['id'], 'user_성명': user['user_성명'], 'MBO_표시명_부서': user['MBO_표시명_부서']} 
                            for user in INFO.ALL_USER if user['MBO_표시명_부서'] and user['is_active']]
            sorted_data = sorted(
                MBO_사용자,
                key=lambda x: (0 if x["MBO_표시명_부서"] == "비정규" else 1, x["MBO_표시명_부서"], x["user_성명"])
            )
            return sorted_data
        return []



    def _handle_update(self):
        """ update 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._update_users(user_obj)
        elif isinstance( user_obj, list):
            for user_dict in user_obj:
                self._update_users(user_dict)
    
    def _handle_delete(self):
        """ delete 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._delete_users(user_obj)
        elif isinstance(user_obj, list):
            for user_dict in user_obj:
                self._delete_users(user_dict)

    def _handle_create(self):
        """ create 처리 """
        user_obj = self.msg.get('message')
        if isinstance(user_obj, dict):
            self._create_users(user_obj)
        elif isinstance( user_obj, list):
            for user_dict in user_obj: 
                self._create_users(  user_dict)


    def _create_users(self, user_dict:dict):
        INFO.ALL_USER.append(user_dict)


   
    def _update_users(self,  user_dict:dict):
        for idx, userObj in enumerate(INFO.ALL_USER):
            if userObj.get('id') == user_dict.get('id'):
                userObj.update(user_dict)

    def _delete_users(self, user_dict:dict):
        del_idx:Optional[int] = None
        for idx, userObj in enumerate(INFO.ALL_USER):
            if userObj.get('id') == user_dict.get('id'):
                del_idx = idx
                break
        if del_idx is not None:
            del INFO.ALL_USER[del_idx]