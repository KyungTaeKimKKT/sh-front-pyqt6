import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image

NUM_CLASSES = 10
IMG_SIZE = 64
CNN_MODEL_PATH = "/home/kkt/development/python/PyQt6/sh_app/modules/ai/hi_rtsp/cnn_digit_gray_model.pth"

class SimpleCNN(nn.Module):
    def __init__(self, _type:str="gray", num_classes=NUM_CLASSES):
        super(SimpleCNN, self).__init__()
        self._type = _type

        if self._type == "rgb":
            in_channels = 3
        elif self._type == "gray":
            in_channels = 1
        else:
            raise ValueError(f"Invalid image type: {self._type}")

        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * (IMG_SIZE // 8) * (IMG_SIZE // 8), 256),
            nn.ReLU(),
            nn.Dropout(0.5),   #### 25-8-26 추가
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

class CNN_Analyzer:
    def __init__(self, cnn_model_path:str=CNN_MODEL_PATH, is_debug:bool=False):
        self.is_debug = is_debug
        self.is_Run = True
        self.cnn_model_path = cnn_model_path

        # CNN 모델 로드
        self.cnn = self.load_cnn_model(cnn_model_path)
        self.cnn.eval()  # 평가 모드

    def load_cnn_model(self, path):
        # 예시: DigitCNN은 사용자 정의 모델 클래스
        model = SimpleCNN(num_classes=10, _type="gray")  # 0~9
        model.load_state_dict(torch.load(path, map_location='cpu'))
        return model