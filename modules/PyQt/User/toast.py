# from pyqttoast import Toast, ToastPreset
from PyQt6.QtGui import QPixmap

from .pyqttoast import Toast, ToastPreset

from enum import Enum
import traceback
from modules.logging_config import get_plugin_logger


# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class ToastIcon(Enum):
    SUCCESS = 1
    WARNING = 2
    ERROR = 3
    INFORMATION = 4
    CLOSE = 5

class User_Toast(Toast):
    """
    Toast 알림을 표시하는 클래스입니다.
    
    style 옵션:
    - SUCCESS: 성공 메시지 (녹색)
    - WARNING: 경고 메시지 (노란색)
    - ERROR: 오류 메시지 (빨간색)
    - INFORMATION: 정보 메시지 (파란색)
    - SUCCESS_DARK: 어두운 테마의 성공 메시지
    - WARNING_DARK: 어두운 테마의 경고 메시지
    - ERROR_DARK: 어두운 테마의 오류 메시지
    - INFORMATION_DARK: 어두운 테마의 정보 메시지
    """
    def __init__(self, parent, duration=2000, title:str='', text:str='', style:str='SUCCESS'):
        super().__init__(parent)
        self.title = title
        ### 😀😀😀 override : pyinstaller시 error 발생.
        # Apply stylesheet
        # self.setStyleSheet(open(self.__get_directory() + '/css/toast_notification.css').read()) ## 원본
        self.setStyleSheet("""
                #toast-drop-shadow-layer-1 {
                    background: rgba(0, 0, 0, 3);
                    border-radius: 8px;
                }

                #toast-drop-shadow-layer-2 {
                    background: rgba(0, 0, 0, 5);
                    border-radius: 8px;
                }

                #toast-drop-shadow-layer-3 {
                    background: rgba(0, 0, 0, 6);
                    border-radius: 8px;
                }

                #toast-drop-shadow-layer-4 {
                    background: rgba(0, 0, 0, 9);
                    border-radius: 8px;
                }

                #toast-drop-shadow-layer-5 {
                    background: rgba(0, 0, 0, 10);
                    border-radius: 8px;
                }

                #toast-close-button {
                    background: transparent;
                }

                #toast-icon-widget {
                    background: transparent;
                }


                """)

        self.setDuration(duration)
        self.setTitle(title)
        self.setText(text)
        self.applyPreset(eval(f"ToastPreset.{style}"))
        self.show()




    def _get_style_preset(self):
        pass
        # match self.style:
        #     case SUCCESS:
        #         return ToastPreset.SUCCESS
        #     case 


    ### 😀😀😀 override : pyinstaller시 error 발생.
    @staticmethod
    def __get_icon_from_enum(enum_icon: ToastIcon):
        """Get a QPixmap from a ToastIcon

        :param enum_icon: ToastIcon
        :return: pixmap of the ToastIcon
        """

        if enum_icon == ToastIcon.SUCCESS:
            return QPixmap(":/icons_toast/success.png")
        elif enum_icon == ToastIcon.WARNING:
            return QPixmap(":/icons_toast/warning.png")
        elif enum_icon == ToastIcon.ERROR:
            return QPixmap(":/icons_toast/error.png")
        elif enum_icon == ToastIcon.INFORMATION:
            return QPixmap(":/icons_toast/information.png")
        elif enum_icon == ToastIcon.CLOSE:
            return QPixmap(":/icons_toast/close.png")
        else:
            return None