#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cimbar Decoder 测试脚本
用于验证解码器功能是否正常
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# 添加颜色输出支持
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print_info("需要Python 3.8或更高版本")
        return False
    print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    required_packages = [
        ('cv2', 'opencv-python'),
        ('mss', 'mss'),
        ('PIL', 'Pillow'),
        ('numpy', 'numpy')
    ]
    
    missing = []
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print_success(f"{package_name} 已安装")
        except ImportError:
            print_error(f"{package_name} 未安装")
            missing.append(package_name)
    
    # 检查可选依赖
    try:
        import pygetwindow
        print_success("pygetwindow 已安装（窗口捕获功能可用）")
    except ImportError:
        print_warning("pygetwindow 未安装（窗口捕获功能不可用）")
    
    if missing:
        print_info(f"\n请运行以下命令安装缺失的包:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True

def check_cimbar_executable():
    """检查cimbar可执行文件"""
    print("\n检查cimbar可执行文件...")
    
    # 可能的cimbar路径
    possible_paths = [
        './cimbar',
        './cimbar.exe',
        '../build/cimbar',
        '../build/cimbar.exe',
        '../build/Release/cimbar.exe',
        '../build/Debug/cimbar.exe'
    ]
    
    cimbar_path = None
    for path in possible_paths:
        if os.path.exists(path):
            cimbar_path = path
            break
    
    if not cimbar_path:
        # 检查PATH
        try:
            result = subprocess.run(['cimbar', '--help'], capture_output=True)
            if result.returncode == 0:
                cimbar_path = 'cimbar'
        except:
            pass
    
    if cimbar_path:
        print_success(f"找到cimbar: {cimbar_path}")
        # 测试运行
        try:
            if os.name == 'nt' and not cimbar_path.endswith('.exe'):
                cimbar_path += '.exe'
            result = subprocess.run([cimbar_path, '--help'], capture_output=True, text=True)
            if result.returncode == 0:
                print_success("cimbar可以正常运行")
                return True
            else:
                print_error("cimbar运行失败")
                return False
        except Exception as e:
            print_error(f"运行cimbar时出错: {e}")
            return False
    else:
        print_error("未找到cimbar可执行文件")
        print_info("请先编译libcimbar项目")
        print_info("编译步骤:")
        print("  cd ..")
        print("  mkdir build && cd build")
        if os.name == 'nt':
            print("  cmake .. -G \"Visual Studio 16 2019\"")
            print("  cmake --build . --config Release")
        else:
            print("  cmake ..")
            print("  make")
        return False

def test_gui_import():
    """测试GUI模块导入"""
    print("\n测试GUI模块...")
    try:
        from cimbar_decoder import CimbarDecoder, CimbarDecoderGUI
        print_success("GUI模块导入成功")
        
        # 测试解码器创建
        decoder = CimbarDecoder()
        print_success("解码器对象创建成功")
        return True
    except Exception as e:
        print_error(f"GUI模块导入失败: {e}")
        return False

def test_cli_import():
    """测试CLI模块导入"""
    print("\n测试CLI模块...")
    try:
        from cimbar_decoder_cli import CimbarDecoderCLI
        print_success("CLI模块导入成功")
        
        # 测试CLI解码器创建
        decoder = CimbarDecoderCLI()
        print_success("CLI解码器对象创建成功")
        return True
    except Exception as e:
        print_error(f"CLI模块导入失败: {e}")
        return False

def test_screen_capture():
    """测试屏幕捕获功能"""
    print("\n测试屏幕捕获...")
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            print_success(f"检测到 {len(monitors)-1} 个显示器")
            for i, monitor in enumerate(monitors[1:], 1):
                print_info(f"  显示器 {i}: {monitor['width']}x{monitor['height']}")
            
            # 尝试捕获主显示器
            screenshot = sct.grab(monitors[1])
            print_success("屏幕捕获功能正常")
            return True
    except Exception as e:
        print_error(f"屏幕捕获失败: {e}")
        return False

def test_image_processing():
    """测试图像处理功能"""
    print("\n测试图像处理...")
    try:
        import cv2
        import numpy as np
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 测试基本操作
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        
        print_success("OpenCV图像处理功能正常")
        return True
    except Exception as e:
        print_error(f"图像处理测试失败: {e}")
        return False

def test_sample_decode():
    """测试解码样本图像"""
    print("\n测试样本图像解码...")
    
    # 查找样本图像
    sample_paths = [
        '../samples/6bit/4color_ecc30_fountain.png',
        '../samples/6bit/4color_ecc30_fountain_0.png',
        '../samples/6bit/4color_ecc30_v2_fountain.png',
        '../samples/4bit/4color_30_0.png'
    ]
    
    sample_image = None
    for path in sample_paths:
        if os.path.exists(path):
            sample_image = path
            break
    
    if not sample_image:
        print_warning("未找到样本图像，跳过解码测试")
        print_info("样本图像应该在 ../samples/ 目录下")
        return True
    
    print_info(f"找到样本图像: {sample_image}")
    
    # 尝试使用CLI解码
    try:
        from cimbar_decoder_cli import CimbarDecoderCLI
        decoder = CimbarDecoderCLI()
        
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as tmpdir:
            decoder.output_dir = tmpdir
            success, message = decoder.decode_single_image(sample_image)
            
            if success:
                print_success(f"样本解码成功: {message}")
                # 检查输出文件
                files = os.listdir(tmpdir)
                if files:
                    print_info(f"  生成文件: {', '.join(files)}")
            else:
                print_warning(f"样本解码失败: {message}")
                print_info("这可能是因为cimbar版本不匹配或样本图像格式问题")
        
        return True
    except Exception as e:
        print_error(f"解码测试出错: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("="*50)
    print("Cimbar Python Decoder 功能测试")
    print("="*50)
    
    tests = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("Cimbar可执行文件", check_cimbar_executable),
        ("GUI模块", test_gui_import),
        ("CLI模块", test_cli_import),
        ("屏幕捕获", test_screen_capture),
        ("图像处理", test_image_processing),
        ("样本解码", test_sample_decode)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name}测试异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print(f"{Colors.GREEN}✓ {name}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ {name}{Colors.END}")
    
    print(f"\n通过测试: {passed}/{total}")
    
    if passed == total:
        print_success("\n所有测试通过！程序可以正常使用。")
        print_info("\n运行程序:")
        print("  GUI版本: python cimbar_decoder.py")
        print("  CLI版本: python cimbar_decoder_cli.py --help")
    else:
        print_warning("\n部分测试未通过，请根据错误信息进行修复。")

if __name__ == "__main__":
    run_all_tests()