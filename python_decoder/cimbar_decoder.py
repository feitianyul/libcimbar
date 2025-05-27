#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cimbar Decoder - 彩色图形矩阵条形码解码器
支持监控多个显示器或应用窗口，实时解码cimbar码
"""

import os
import sys
import time
import threading
import subprocess
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mss
import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    import pygetwindow as gw
except ImportError:
    gw = None
    print("警告: pygetwindow未安装，窗口捕获功能将不可用")


class CimbarDecoder:
    """Cimbar解码器主类"""
    
    def __init__(self, cimbar_path="./cimbar"):
        self.cimbar_path = cimbar_path
        self.decoding = False
        self.capture_thread = None
        self.decode_thread = None
        self.output_dir = tempfile.mkdtemp(prefix="cimbar_decode_")
        self.decoded_files = set()
        self.last_decode_time = 0
        self.decode_interval = 0.5  # 解码间隔（秒）
        
    def check_cimbar_executable(self):
        """检查cimbar可执行文件是否存在"""
        if os.name == 'nt':
            cimbar_exe = self.cimbar_path + '.exe'
        else:
            cimbar_exe = self.cimbar_path
            
        if not os.path.exists(cimbar_exe):
            return False, f"找不到cimbar可执行文件: {cimbar_exe}"
        
        if not os.access(cimbar_exe, os.X_OK) and os.name != 'nt':
            return False, f"cimbar文件没有执行权限: {cimbar_exe}"
            
        return True, "cimbar可执行文件就绪"
    
    def decode_image(self, image_path):
        """调用cimbar解码图像"""
        try:
            # 构造命令
            if os.name == 'nt':
                cmd = [self.cimbar_path + '.exe']
            else:
                cmd = [self.cimbar_path]
                
            cmd.extend([image_path, '-o', self.output_dir, '--no-deskew'])
            
            # 执行解码
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 检查是否有新文件生成
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
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            if area < 10000:  # 过滤太小的区域
                continue
                
            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 检查宽高比（cimbar码应该接近正方形）
            aspect_ratio = w / h
            if 0.8 < aspect_ratio < 1.2:
                # 提取感兴趣区域
                roi = image[y:y+h, x:x+w]
                return True, roi, (x, y, w, h)
                
        return False, None, None


class CimbarDecoderGUI:
    """图形用户界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cimbar解码器 - 彩色图形矩阵条形码")
        self.root.geometry("800x600")
        
        self.decoder = CimbarDecoder()
        self.monitoring = False
        self.capture_source = None
        self.capture_thread = None
        self.current_frame = None
        self.preview_label = None
        
        self.setup_ui()
        self.check_dependencies()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 捕获源选择
        source_frame = ttk.LabelFrame(main_frame, text="捕获源选择", padding="10")
        source_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.source_var = tk.StringVar(value="monitor")
        ttk.Radiobutton(source_frame, text="监控显示器", 
                       variable=self.source_var, value="monitor",
                       command=self.update_source_options).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(source_frame, text="监控窗口", 
                       variable=self.source_var, value="window",
                       command=self.update_source_options).grid(row=0, column=1, padx=5)
        
        # 显示器/窗口选择
        self.source_combo = ttk.Combobox(source_frame, width=40)
        self.source_combo.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="开始监控", 
                                      command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(control_frame, text="选择输出目录", 
                  command=self.select_output_dir).grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="打开输出目录", 
                  command=self.open_output_dir).grid(row=0, column=2, padx=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="实时预览", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(preview_frame, text="等待开始监控...")
        self.preview_label.grid(row=0, column=0)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="解码日志", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, width=60)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # 初始化源选项
        self.update_source_options()
        
    def check_dependencies(self):
        """检查依赖项"""
        # 检查cimbar可执行文件
        success, message = self.decoder.check_cimbar_executable()
        if not success:
            self.log(f"错误: {message}")
            self.log("请确保已编译cimbar并将可执行文件放在正确位置")
            messagebox.showerror("依赖检查失败", message)
        else:
            self.log(f"✓ {message}")
            
        # 检查pygetwindow
        if gw is None:
            self.log("警告: pygetwindow未安装，窗口捕获功能不可用")
            
    def update_source_options(self):
        """更新捕获源选项"""
        if self.source_var.get() == "monitor":
            # 获取显示器列表
            with mss.mss() as sct:
                monitors = [f"显示器 {i} ({m['width']}x{m['height']})" 
                           for i, m in enumerate(sct.monitors[1:], 1)]
            self.source_combo['values'] = monitors
            if monitors:
                self.source_combo.current(0)
        else:
            # 获取窗口列表
            if gw is not None:
                windows = [w.title for w in gw.getAllWindows() if w.title]
                self.source_combo['values'] = windows
                if windows:
                    self.source_combo.current(0)
            else:
                self.source_combo['values'] = ["pygetwindow未安装"]
                self.source_combo.current(0)
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        # 检查是否选择了捕获源
        if not self.source_combo.get():
            messagebox.showwarning("警告", "请先选择捕获源")
            return
            
        self.monitoring = True
        self.start_button.config(text="停止监控")
        self.status_var.set("正在监控...")
        self.log(f"开始监控: {self.source_combo.get()}")
        
        # 启动捕获线程
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_button.config(text="开始监控")
        self.status_var.set("已停止")
        self.log("停止监控")
        
    def capture_loop(self):
        """捕获循环"""
        with mss.mss() as sct:
            while self.monitoring:
                try:
                    # 捕获屏幕
                    if self.source_var.get() == "monitor":
                        # 获取显示器索引
                        monitor_idx = self.source_combo.current() + 1
                        if 0 < monitor_idx < len(sct.monitors):
                            screenshot = sct.grab(sct.monitors[monitor_idx])
                            image = np.array(screenshot)
                            # 转换BGRA到BGR
                            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                        else:
                            self.log("错误: 无效的显示器索引")
                            break
                    else:
                        # 窗口捕获
                        if gw is None:
                            self.log("错误: 窗口捕获功能不可用")
                            break
                            
                        window_title = self.source_combo.get()
                        windows = gw.getWindowsWithTitle(window_title)
                        if windows:
                            window = windows[0]
                            region = {
                                'left': window.left,
                                'top': window.top,
                                'width': window.width,
                                'height': window.height
                            }
                            screenshot = sct.grab(region)
                            image = np.array(screenshot)
                            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                        else:
                            self.log(f"错误: 找不到窗口 '{window_title}'")
                            break
                    
                    # 更新预览
                    self.update_preview(image)
                    
                    # 查找并解码cimbar码
                    current_time = time.time()
                    if current_time - self.decoder.last_decode_time > self.decoder.decode_interval:
                        found, roi, bbox = self.decoder.find_cimbar_in_image(image)
                        if found:
                            # 保存ROI到临时文件
                            temp_path = os.path.join(tempfile.gettempdir(), "cimbar_temp.png")
                            cv2.imwrite(temp_path, roi)
                            
                            # 解码
                            success, message = self.decoder.decode_image(temp_path)
                            if success:
                                self.log(f"✓ {message}")
                            else:
                                self.log(f"✗ {message}")
                                
                            # 清理临时文件
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                                
                            self.decoder.last_decode_time = current_time
                    
                    # 控制帧率
                    time.sleep(0.033)  # 约30 FPS
                    
                except Exception as e:
                    self.log(f"捕获错误: {str(e)}")
                    break
                    
        # 清理
        self.root.after(0, self.stop_monitoring)
    
    def update_preview(self, image):
        """更新预览图像"""
        try:
            # 调整图像大小以适应预览区域
            height, width = image.shape[:2]
            max_width, max_height = 600, 400
            
            # 计算缩放比例
            scale = min(max_width/width, max_height/height, 1.0)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # 缩放图像
            resized = cv2.resize(image, (new_width, new_height))
            
            # 转换为RGB（OpenCV使用BGR）
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL图像
            pil_image = Image.fromarray(rgb_image)
            
            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image=pil_image)
            
            # 更新标签
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo  # 保持引用
            
        except Exception as e:
            self.log(f"预览更新错误: {str(e)}")
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.decoder.output_dir
        )
        if directory:
            self.decoder.output_dir = directory
            self.log(f"输出目录设置为: {directory}")
    
    def open_output_dir(self):
        """打开输出目录"""
        if os.path.exists(self.decoder.output_dir):
            if os.name == 'nt':
                os.startfile(self.decoder.output_dir)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', self.decoder.output_dir])
            else:
                self.log("不支持的操作系统")
        else:
            messagebox.showwarning("警告", "输出目录不存在")
    
    def log(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CimbarDecoderGUI()
    app.run()