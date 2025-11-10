"""
TripoSR模块包装器
用于导入TripoSR相关功能
"""

import os
import sys
from pathlib import Path

# 添加TripoSR路径到系统路径
triposr_path = None

# 尝试找到TripoSR路径
possible_paths = [
    Path(__file__).parent.parent.parent / "TripoSR",  # 项目根目录下的TripoSR
    Path(__file__).parent.parent / "TripoSR",         # 项目目录下的TripoSR
    Path("models/TripoSR"),                           # 模型目录下的TripoSR
]

for path in possible_paths:
    if path.exists() and (path / "tsr").exists():
        triposr_path = str(path)
        break

if triposr_path and triposr_path not in sys.path:
    sys.path.insert(0, triposr_path)

# 导入TripoSR模块
try:
    from tsr.system import TSR
    from tsr.utils import remove_background, resize_foreground, to_gradio_3d_orientation
    from tsr.bake_texture import bake_texture
    TRIPOSR_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入TripoSR模块: {e}")
    TRIPOSR_AVAILABLE = False
    
    # 创建占位符类以避免导入错误
    class TSR:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            raise ImportError("TripoSR模块不可用，请检查安装")
    
    def remove_background(*args, **kwargs):
        raise ImportError("TripoSR模块不可用，请检查安装")
    
    def resize_foreground(*args, **kwargs):
        raise ImportError("TripoSR模块不可用，请检查安装")
    
    def to_gradio_3d_orientation(*args, **kwargs):
        raise ImportError("TripoSR模块不可用，请检查安装")
    
    def bake_texture(*args, **kwargs):
        raise ImportError("TripoSR模块不可用，请检查安装")
