# scan_modules.py
import os
import importlib
import traceback
from modules.logging_config import get_plugin_logger



# 인자 없이 호출하면 자동으로 현재 모듈 이름(파일 이름)을 사용
logger = get_plugin_logger()

def get_all_modules(base_path, base_package):
    modules = []
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                # base_path의 상위 디렉토리부터 상대 경로 계산
                rel_dir = os.path.relpath(root, os.path.dirname(base_path))
                
                # 모듈 경로에서 base_path와 동일한 이름 부분 제거
                if rel_dir.startswith(os.path.basename(base_path)):
                    rel_dir = rel_dir[len(os.path.basename(base_path))+1:]
                
                # 경로 구성
                if rel_dir == os.path.basename(base_path) or rel_dir == '.':
                    module_path = file[:-3]
                else:
                    module_path = os.path.join(rel_dir, file[:-3]).replace(os.sep, '.')
                
                # base_package가 비어있지 않은 경우에만 앞에 추가
                if base_package:
                    full_module_path = f"{base_package}.{module_path}"
                else:
                    full_module_path = module_path
                    
                modules.append(full_module_path)
    
    return modules

if __name__ == "__main__":
    modules = get_all_modules("modules", "modules")


    for module in modules:
        if 'copy' in module:
            continue
        print(f'"{module}",')

