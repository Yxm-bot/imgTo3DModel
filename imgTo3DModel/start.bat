@echo off
echo 图片转3D模型系统 - 启动
echo ========================

REM 检查是否已安装
if not exist "venv" (
    echo 错误: 未找到虚拟环境，请先运行 install.bat 进行安装
    pause
    exit /b 1
)

if not exist "models\TripoSR" (
    echo 错误: 未找到模型文件，请先运行 install.bat 进行安装
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate

REM 启动应用
echo 启动图片转3D模型系统...
echo 浏览器将自动打开，如果没有请手动访问 http://localhost:7860
echo.
python app\main.py

pause
