import platform
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def set_korean_font():
    system = platform.system()
    if system == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"  # Windows 기본 한글 폰트
    elif system == "Darwin":  # macOS
        plt.rcParams["font.family"] = "AppleGothic"
    else:  # Linux
        # 나눔고딕 설치돼 있다는 전제
        plt.rcParams["font.family"] = "NanumGothic"

    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 깨짐 방지