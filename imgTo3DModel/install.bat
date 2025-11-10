@echo off
echo 图片转3D模型系统 - 一键安装
echo ================================

REM 检查Python是否安装
echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 请访问 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

REM 显示Python版本
python --version

REM 创建虚拟环境
echo 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装PyTorch (CUDA版本)
echo 安装PyTorch (支持CUDA)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

REM 安装项目依赖
echo 安装项目依赖...
pip install -r app\requirements.txt

REM 创建必要目录
echo 创建必要目录...
if not exist "models" mkdir models
if not exist "output" mkdir output
if not exist "input" mkdir input

REM 下载TripoSR模型
echo 下载TripoSR模型...
if not exist "models\TripoSR" (
    echo 正在从Hugging Face下载模型，请稍候...
    python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='stabilityai/TripoSR', local_dir='models/TripoSR', local_dir_use_symlinks=False)"
    if %errorlevel% neq 0 (
        echo 模型下载失败，请检查网络连接
        pause
        exit /b 1
    )
)

REM 复制TripoSR源码
echo 设置TripoSR源码...
if not exist "src\tsr" (
    if exist "..\TripoSR\tsr" (
        xcopy "..\TripoSR\tsr" "src\tsr" /E /I /Y
    ) else (
        echo 警告: 未找到TripoSR源码，请确保已克隆TripoSR仓库
    )
)

echo.
echo ================================
echo 安装完成！
echo ================================
echo.
echo 现在可以运行 start.bat 启动应用
echo.
pause
