from PyQt6.QtCore import *
import pygame
import traceback
from modules.logging_config import get_plugin_logger




# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

class PlaySound(QThread):
    def __init__(self, path):
        super().__init__()
        pygame.mixer.init()
        self.is_Run = True
        self.sound = pygame.mixer.Sound(path)

    def run(self):
        self.sound.play(-1)

    def stop(self):
        # self.is_Run = False
        self.sound.stop()

    def resume(self):
        self.sound.play(-1)
    

    def change_resume(self, path):
        self.stop()
        self.sound = pygame.mixer.Sound(path)
        self.resume()


