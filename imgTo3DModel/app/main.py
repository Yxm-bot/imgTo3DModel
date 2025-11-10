#!/usr/bin/env python3
"""
图片转3D模型系统 - 简化版主应用程序
基于TripoSR模型实现单张图片转3D模型功能
"""

import os
import sys
import time
import tempfile
import logging
import argparse
import shutil
from pathlib import Path
from datetime import datetime

import gradio as gr
import numpy as np
import torch
from PIL import Image
import rembg
from tqdm import tqdm

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入TripoSR相关模块
try:
    from tsr.system import TSR
    from tsr.utils import remove_background, resize_foreground, to_gradio_3d_orientation
    TRIPOSR_AVAILABLE = True
except ImportError:
    print("警告: 无法导入TripoSR模块，请确保已正确安装")
    TRIPOSR_AVAILABLE = False

# 配置日志
def setup_logging():
    """设置日志记录"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ImageTo3DModel:
    """图片转3D模型系统"""
    
    def __init__(self, model_path=None, device=None):
        """初始化模型"""
        self.model_path = model_path or "models/TripoSR"
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.rembg_session = None
        
        logger.info(f"使用设备: {self.device}")
        
        # 初始化模型
        self._load_model()
        
        # 初始化背景移除会话
        self.rembg_session = rembg.new_session()
    
    def _load_model(self):
        """加载TripoSR模型"""
        if not TRIPOSR_AVAILABLE:
            logger.error("TripoSR模块不可用")
            return False
            
        try:
            logger.info("正在加载TripoSR模型...")
            self.model = TSR.from_pretrained(
                self.model_path,
                config_name="config.yaml",
                weight_name="model.ckpt",
            )
            
            # 设置块大小以平衡速度和内存使用
            self.model.renderer.set_chunk_size(8192)
            self.model.to(self.device)
            
            logger.info("模型加载成功")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    def preprocess_image(self, image, do_remove_background=True, foreground_ratio=0.85):
        """预处理输入图像"""
        def fill_background(image):
            image = np.array(image).astype(np.float32) / 255.0
            image = image[:, :, :3] * image[:, :, 3:4] + (1 - image[:, :, 3:4]) * 0.5
            image = Image.fromarray((image * 255.0).astype(np.uint8))
            return image

        if do_remove_background:
            image = image.convert("RGB")
            image = remove_background(image, self.rembg_session)
            image = resize_foreground(image, foreground_ratio)
            image = fill_background(image)
        else:
            image = image
            if image.mode == "RGBA":
                image = fill_background(image)
        return image
    
    def generate_3d_model(self, image, mc_resolution=256, formats=["obj", "glb"]):
        """生成3D模型"""
        if self.model is None:
            raise ValueError("模型未加载")
            
        logger.info("开始生成3D模型...")
        
        with torch.no_grad():
            scene_codes = self.model([image], device=self.device)
        
        logger.info("提取网格...")
        mesh = self.model.extract_mesh(scene_codes, True, resolution=mc_resolution)[0]
        mesh = to_gradio_3d_orientation(mesh)
        
        # 创建输出目录
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 保存模型文件
        output_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for format in formats:
            filename = f"model_{timestamp}.{format}"
            output_path = output_dir / filename
            mesh.export(str(output_path))
            output_files.append(str(output_path))
            logger.info(f"已保存{format.upper()}格式模型: {output_path}")
        
        logger.info("3D模型生成完成")
        return output_files

# 全局模型实例
model_instance = None

def load_model():
    """加载模型（全局函数）"""
    global model_instance
    if model_instance is None:
        model_instance = ImageTo3DModel()
    return model_instance

def check_input_image(input_image):
    """检查输入图像"""
    if input_image is None:
        raise gr.Error("未上传图片!")
    return True

def preprocess_image(input_image, do_remove_background, foreground_ratio):
    """预处理图像（Gradio接口）"""
    model = load_model()
    processed_image = model.preprocess_image(
        input_image, 
        do_remove_background, 
        foreground_ratio
    )
    return processed_image

def generate_3d_model(processed_image, mc_resolution):
    """生成3D模型（Gradio接口）"""
    model = load_model()
    output_files = model.generate_3d_model(processed_image, mc_resolution, ["obj", "glb"])
    return output_files[0], output_files[1]  # obj_path, glb_path

def create_ui():
    """创建Gradio用户界面"""
    with gr.Blocks(title="图片转3D模型系统", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 图片转3D模型系统
            
            本系统基于[TripoSR](https://github.com/VAST-AI-Research/TripoSR)模型，能够从单张图片快速生成高质量的3D模型。
            
            **使用提示:**
            1. 上传一张包含角色或物体的图片
            2. 调整参数以获得最佳效果
            3. 点击"生成3D模型"按钮
            4. 下载生成的3D模型文件
            """
        )
        
        with gr.Row(variant="panel"):
            with gr.Column():
                with gr.Row():
                    input_image = gr.Image(
                        label="输入图片",
                        image_mode="RGBA",
                        sources="upload",
                        type="pil",
                        elem_id="content_image",
                    )
                    processed_image = gr.Image(label="处理后图片", interactive=False)
                
                with gr.Row():
                    with gr.Group():
                        do_remove_background = gr.Checkbox(
                            label="移除背景", value=True
                        )
                        foreground_ratio = gr.Slider(
                            label="前景比例",
                            minimum=0.5,
                            maximum=1.0,
                            value=0.85,
                            step=0.05,
                        )
                        mc_resolution = gr.Slider(
                            label="网格分辨率",
                            minimum=64,
                            maximum=512,
                            value=256,
                            step=32,
                            info="值越高模型越精细，但消耗更多资源"
                        )
                
                with gr.Row():
                    submit = gr.Button("生成3D模型", elem_id="generate", variant="primary")
            
            with gr.Column():
                with gr.Tab("OBJ格式"):
                    output_model_obj = gr.File(
                        label="3D模型 (OBJ格式)",
                        interactive=False,
                    )
                    gr.Markdown("OBJ格式可在大多数3D软件中打开")
                
                with gr.Tab("GLB格式"):
                    output_model_glb = gr.File(
                        label="3D模型 (GLB格式)",
                        interactive=False,
                    )
                    gr.Markdown("GLB格式适合Web展示和移动应用")
        
        # 事件处理
        submit.click(
            fn=check_input_image, 
            inputs=[input_image]
        ).success(
            fn=preprocess_image,
            inputs=[input_image, do_remove_background, foreground_ratio],
            outputs=[processed_image],
        ).success(
            fn=generate_3d_model,
            inputs=[processed_image, mc_resolution],
            outputs=[output_model_obj, output_model_glb],
        )
    
    return interface

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="图片转3D模型系统")
    parser.add_argument('--port', type=int, default=7860, help='服务器端口')
    parser.add_argument("--share", action='store_true', help="创建公共分享链接")
    
    args = parser.parse_args()
    
    # 创建UI
    interface = create_ui()
    
    # 启动服务器
    logger.info(f"启动Web服务器，端口: {args.port}")
    interface.launch(
        share=args.share,
        server_name="0.0.0.0", 
        server_port=args.port,
        inbrowser=True  # 自动打开浏览器
    )

if __name__ == "__main__":
    main()
