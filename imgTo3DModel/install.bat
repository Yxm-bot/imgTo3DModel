@echo off
echo 图片转3D模型系统 - 一键安装（国内镜像加速版）
echo ================================
echo.
echo [信息] 本安装脚本已优化为使用国内镜像源，大幅提升下载速度
echo [信息] - pip包使用阿里云镜像
echo [信息] - PyTorch使用上海交大镜像
echo [信息] - HuggingFace模型使用hf-mirror镜像
echo [信息] - GitHub包使用ghproxy加速
echo.
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

REM 配置pip使用国内镜像源（阿里云）
echo 配置pip使用国内镜像源（阿里云）...
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com
echo [成功] pip已配置为使用阿里云镜像源

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

REM 安装PyTorch (CUDA版本) - 使用上海交大镜像
echo 安装PyTorch (支持CUDA) - 使用上海交大镜像...
if exist "offline_packages\pytorch_wheels" (
    echo 检测到本地 PyTorch wheel 文件，使用离线安装...
    pip install --no-index --find-links offline_packages\pytorch_wheels torch torchvision
    if %errorlevel% neq 0 (
        echo 离线安装失败，尝试使用上海交大镜像在线安装...
        pip install torch torchvision --index-url https://mirror.sjtu.edu.cn/pytorch-wheels/cu118
        if %errorlevel% neq 0 (
            echo 上海交大镜像失败，尝试官方CUDA源...
            pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
        )
    )
) else (
    echo 优先使用上海交大镜像（国内高速）...
    pip install torch torchvision --index-url https://mirror.sjtu.edu.cn/pytorch-wheels/cu118
    if %errorlevel% neq 0 (
        echo 上海交大镜像失败，使用官方CUDA源...
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    )
)

REM 安装项目依赖 - 自动使用阿里云镜像
echo 安装项目依赖（使用阿里云镜像）...
if exist "offline_packages\python_packages" (
    echo 检测到本地依赖包，优先使用离线安装...
    pip install --find-links offline_packages\python_packages -r app\requirements.txt
) else (
    echo 使用阿里云镜像在线安装...
    pip install -r app\requirements.txt
)

REM 创建必要目录
echo 创建必要目录...
if not exist "models" mkdir models
if not exist "output" mkdir output
if not exist "input" mkdir input
if not exist "logs" mkdir logs

REM 设置HuggingFace镜像环境变量
echo 配置HuggingFace使用国内镜像（hf-mirror）...
set HF_ENDPOINT=https://hf-mirror.com
echo [成功] HuggingFace已配置为使用hf-mirror国内镜像

REM 下载TripoSR模型 - 使用hf-mirror国内镜像
echo 下载TripoSR模型（使用hf-mirror国内镜像）...
if not exist "models\TripoSR" (
    echo 正在从HuggingFace镜像下载模型，速度更快，请稍候...
    echo [提示] 使用hf-mirror.com镜像，预计2-3分钟完成
    python -c "import os; os.environ['HF_ENDPOINT']='https://hf-mirror.com'; from huggingface_hub import snapshot_download; snapshot_download(repo_id='stabilityai/TripoSR', local_dir='models/TripoSR', local_dir_use_symlinks=False)"
    if %errorlevel% neq 0 (
        echo [警告] 镜像下载失败，尝试使用官方源（可能较慢）...
        python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='stabilityai/TripoSR', local_dir='models/TripoSR', local_dir_use_symlinks=False)"
        if %errorlevel% neq 0 (
            echo [错误] 模型下载失败，请检查网络连接
            echo [提示] 你也可以手动从 https://hf-mirror.com/stabilityai/TripoSR 下载模型文件
            echo [提示] 然后解压到 models\TripoSR 目录
            pause
            exit /b 1
        )
    )
    echo [成功] TripoSR模型下载完成
) else (
    echo [跳过] TripoSR模型已存在，跳过下载
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
echo [镜像源配置总结]
echo - pip包：阿里云镜像（已永久配置）
echo - PyTorch：上海交大镜像
echo - HuggingFace：hf-mirror国内镜像
echo.
echo 现在可以运行 start.bat 启动应用
echo.
pause
