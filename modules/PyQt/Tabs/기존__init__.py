# https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
from os.path import dirname, basename, isfile, join
import glob
import traceback
from modules.logging_config import get_plugin_logger

# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()


modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

# __all__ = [
#     "App설정_App설정",
#     "공지및요청사항_공지사항작성",
#     "일일업무_개인",
#     "일일업무_개인이력조회",
#     "일일업무_개인이력조회_전사_",
# ]