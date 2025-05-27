#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cimbar Decoder CLI - 命令行版彩色图形矩阵条形码解码器
"""

import os
import sys
import time
import argparse
import subprocess
import tempfile
from pathlib import Path
import mss
import cv2
import numpy as np

try:
    import pygetwindow as gw
except ImportError:
    gw = None


class CimbarDecoderCLI:
    """命令行版Cimbar解码器"""
    
    def __init__(self, cimbar_path="./cimbar", output_dir=None):
        self.cimbar_path = cimbar_path
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="cimbar_decode_")
        self.decoded_files = set()
        self.frame_count = 0
        self.decode_count = 0
        
    def check_cimbar_executable(self):
        """检查cimbar可执行文件"""
        if os.name == 'nt':
            cimbar_exe = self.cimbar_path + '.exe'
        else:
            cimbar_exe = self.cimbar_path
            
        if not os.path.exists(cimbar_exe):
            return False, f"找不到cimbar可执行文件: {cimbar_exe}"
        
        if not os.access(cimbar_exe, os.X_OK) and os.name != 'nt':
            return False, f"cimbar文件没有执行权限: {cimbar_exe}"
            
        return True, "cimbar可执行文件就绪"
    
    def decode_image(self, image_path, verbose=False):
        """解码图像"""
        try:
            # 构造命令
            if os.name == 'nt':
                cmd = [self.cimbar_path + '.exe']
            else:
                cmd = [self.cimbar_path]
                
            cmd.extend([image_path, '-o', self.output_dir, '--no-deskew'])
            
            if verbose:
                print(f"执行命令: {' '.join(cmd)}")
            
            # 执行解码
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 检查新文件
                current_files = set(os.listdir(self.output_dir))
                new_files = current_files - self.decoded_files
                self.decoded_files = current_files
                
                if new_files:
                    return True, f"成功解码，新文件: {', '.join(new_files)}"
                else:
                    return True, "解码成功（等待更多数据）"
            else:
                return False, f"解码失败: {result.stderr}"
                
        except Exception as e:
            return False, f"解码错误: {str(e)}"
    
    def find_cimbar_in_image(self, image):
        """在图像中查找cimbar码"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 应用自适应阈值
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 筛选可能的cimbar码区域
        candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 10000:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            if 0.8 < aspect_ratio < 1.2:
                roi = image[y:y+h, x:x+w]
                candidates.append((roi, (x, y, w, h), area))
        
        # 返回最大的候选区域
        if candidates:
            candidates.sort(key=lambda x: x[2], reverse=True)
            return True, candidates[0][0], candidates[0][1]
            
        return False, None, None
    
    def monitor_screen(self, monitor_index=1, duration=None, interval=0.5, verbose=False):
        """监控屏幕并解码"""
        print(f"开始监控显示器 {monitor_index}")
        print(f"输出目录: {self.output_dir}")
        print("按 Ctrl+C 停止监控\n")
        
        start_time = time.time()
        last_decode_time = 0
        
        with mss.mss() as sct:
            if monitor_index >= len(sct.monitors):
                print(f"错误: 显示器索引 {monitor_index} 无效")
                return
                
            monitor = sct.monitors[monitor_index]
            print(f"监控区域: {monitor['width']}x{monitor['height']}")
            
            try:
                while True:
                    # 检查是否超时
                    if duration and (time.time() - start_time) > duration:
                        print("\n监控时间已到")
                        break
                    
                    # 捕获屏幕
                    screenshot = sct.grab(monitor)
                    image = np.array(screenshot)
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    
                    self.frame_count += 1
                    
                    # 控制解码频率
                    current_time = time.time()
                    if current_time - last_decode_time < interval:
                        continue
                    
                    # 查找并解码
                    found, roi, bbox = self.find_cimbar_in_image(image)
                    if found:
                        # 保存到临时文件
                        temp_path = os.path.join(tempfile.gettempdir(), "cimbar_temp.png")
                        cv2.imwrite(temp_path, roi)
                        
                        # 解码
                        success, message = self.decode_image(temp_path, verbose)
                        if success:
                            self.decode_count += 1
                            print(f"[{time.strftime('%H:%M:%S')}] ✓ {message}")
                        elif verbose:
                            print(f"[{time.strftime('%H:%M:%S')}] ✗ {message}")
                        
                        # 清理临时文件
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
                        last_decode_time = current_time
                    
                    # 显示统计信息
                    if self.frame_count % 30 == 0:
                        elapsed = time.time() - start_time
                        fps = self.frame_count / elapsed
                        print(f"\r帧数: {self.frame_count}, 解码次数: {self.decode_count}, FPS: {fps:.1f}", end="")
                    
                    time.sleep(0.033)  # 约30 FPS
                    
            except KeyboardInterrupt:
                print("\n\n用户中断")
            
        # 显示统计
        elapsed = time.time() - start_time
        print(f"\n\n监控统计:")
        print(f"  总时长: {elapsed:.1f}秒")
        print(f"  处理帧数: {self.frame_count}")
        print(f"  解码次数: {self.decode_count}")
        print(f"  平均FPS: {self.frame_count/elapsed:.1f}")
        print(f"\n解码文件保存在: {self.output_dir}")
    
    def monitor_window(self, window_title, duration=None, interval=0.5, verbose=False):
        """监控特定窗口并解码"""
        if gw is None:
            print("错误: pygetwindow未安装，无法使用窗口监控功能")
            print("请运行: pip install pygetwindow")
            return
            
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            print(f"错误: 找不到窗口 '{window_title}'")
            print("\n可用窗口:")
            for w in gw.getAllWindows():
                if w.title:
                    print(f"  - {w.title}")
            return
            
        window = windows[0]
        print(f"开始监控窗口: {window.title}")
        print(f"窗口位置: ({window.left}, {window.top})")
        print(f"窗口大小: {window.width}x{window.height}")
        print(f"输出目录: {self.output_dir}")
        print("按 Ctrl+C 停止监控\n")
        
        # 使用屏幕监控的逻辑，但限定在窗口区域
        start_time = time.time()
        last_decode_time = 0
        
        with mss.mss() as sct:
            try:
                while True:
                    # 检查是否超时
                    if duration and (time.time() - start_time) > duration:
                        print("\n监控时间已到")
                        break
                    
                    # 更新窗口位置（窗口可能被移动）
                    window = gw.getWindowsWithTitle(window_title)[0]
                    region = {
                        'left': window.left,
                        'top': window.top,
                        'width': window.width,
                        'height': window.height
                    }
                    
                    # 捕获窗口
                    screenshot = sct.grab(region)
                    image = np.array(screenshot)
                    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    
                    self.frame_count += 1
                    
                    # 后续处理与monitor_screen相同
                    current_time = time.time()
                    if current_time - last_decode_time < interval:
                        continue
                    
                    found, roi, bbox = self.find_cimbar_in_image(image)
                    if found:
                        temp_path = os.path.join(tempfile.gettempdir(), "cimbar_temp.png")
                        cv2.imwrite(temp_path, roi)
                        
                        success, message = self.decode_image(temp_path, verbose)
                        if success:
                            self.decode_count += 1
                            print(f"[{time.strftime('%H:%M:%S')}] ✓ {message}")
                        elif verbose:
                            print(f"[{time.strftime('%H:%M:%S')}] ✗ {message}")
                        
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
                        last_decode_time = current_time
                    
                    if self.frame_count % 30 == 0:
                        elapsed = time.time() - start_time
                        fps = self.frame_count / elapsed
                        print(f"\r帧数: {self.frame_count}, 解码次数: {self.decode_count}, FPS: {fps:.1f}", end="")
                    
                    time.sleep(0.033)
                    
            except KeyboardInterrupt:
                print("\n\n用户中断")
            
        # 显示统计
        elapsed = time.time() - start_time
        print(f"\n\n监控统计:")
        print(f"  总时长: {elapsed:.1f}秒")
        print(f"  处理帧数: {self.frame_count}")
        print(f"  解码次数: {self.decode_count}")
        print(f"  平均FPS: {self.frame_count/elapsed:.1f}")
        print(f"\n解码文件保存在: {self.output_dir}")
    
    def decode_single_image(self, image_path, verbose=False):
        """解码单个图像文件"""
        if not os.path.exists(image_path):
            print(f"错误: 文件不存在 {image_path}")
            return
            
        print(f"解码图像: {image_path}")
        print(f"输出目录: {self.output_dir}")
        
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            print("错误: 无法读取图像")
            return
            
        # 查找cimbar码
        found, roi, bbox = self.find_cimbar_in_image(image)
        if not found:
            # 尝试直接解码整个图像
            print("未检测到明显的cimbar码区域，尝试解码整个图像...")
            success, message = self.decode_image(image_path, verbose)
        else:
            # 保存ROI并解码
            temp_path = os.path.join(tempfile.gettempdir(), "cimbar_roi.png")
            cv2.imwrite(temp_path, roi)
            success, message = self.decode_image(temp_path, verbose)
            try:
                os.remove(temp_path)
            except:
                pass
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")


def main():
    parser = argparse.ArgumentParser(
        description="Cimbar Decoder CLI - 彩色图形矩阵条形码解码器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  监控主显示器:
    %(prog)s --monitor 1
    
  监控特定窗口:
    %(prog)s --window "Chrome"
    
  解码图像文件:
    %(prog)s --image sample.png
    
  设置输出目录:
    %(prog)s --monitor 1 --output ./decoded
        """
    )
    
    # 模式选择
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-m', '--monitor', type=int, metavar='INDEX',
                           help='监控显示器（1=主显示器，2=第二显示器...）')
    mode_group.add_argument('-w', '--window', type=str, metavar='TITLE',
                           help='监控特定窗口标题')
    mode_group.add_argument('-i', '--image', type=str, metavar='PATH',
                           help='解码单个图像文件')
    
    # 其他参数
    parser.add_argument('-o', '--output', type=str, metavar='DIR',
                       help='输出目录（默认：临时目录）')
    parser.add_argument('-c', '--cimbar', type=str, default='./cimbar',
                       help='cimbar可执行文件路径（默认：./cimbar）')
    parser.add_argument('-t', '--time', type=int, metavar='SECONDS',
                       help='监控时长（秒），不指定则持续监控')
    parser.add_argument('-r', '--rate', type=float, default=0.5,
                       help='解码间隔（秒）（默认：0.5）')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='显示详细信息')
    parser.add_argument('--list-windows', action='store_true',
                       help='列出所有可用窗口')
    
    args = parser.parse_args()
    
    # 列出窗口
    if args.list_windows:
        if gw is None:
            print("错误: pygetwindow未安装")
            return 1
        print("可用窗口:")
        for w in gw.getAllWindows():
            if w.title:
                print(f"  {w.title}")
        return 0
    
    # 创建解码器
    decoder = CimbarDecoderCLI(cimbar_path=args.cimbar, output_dir=args.output)
    
    # 检查cimbar
    success, message = decoder.check_cimbar_executable()
    if not success:
        print(f"错误: {message}")
        return 1
    
    if args.verbose:
        print(f"✓ {message}")
    
    # 执行相应模式
    try:
        if args.monitor:
            decoder.monitor_screen(args.monitor, args.time, args.rate, args.verbose)
        elif args.window:
            decoder.monitor_window(args.window, args.time, args.rate, args.verbose)
        elif args.image:
            decoder.decode_single_image(args.image, args.verbose)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())