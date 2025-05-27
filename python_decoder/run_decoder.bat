@echo off
echo ========================================
echo  Cimbar Decoder - 彩色图形矩阵条形码解码器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否已安装
python -c "import cv2, mss, PIL" >nul 2>&1
if errorlevel 1 (
    echo 首次运行，正在安装依赖包...
    echo.
    pip install -r requirements.txt
    echo.
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查cimbar.exe是否存在
if not exist "cimbar.exe" (
    if not exist "..\build\Release\cimbar.exe" (
        if not exist "..\build\cimbar.exe" (
            echo 警告: 未找到cimbar.exe
            echo 请确保已编译libcimbar项目
            echo.
        )
    )
)

REM 启动解码器
echo 正在启动Cimbar解码器...
python cimbar_decoder.py

if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)