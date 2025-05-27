# Cimbar Python Decoder - 彩色图形矩阵条形码解码器

这是一个基于Python的桌面应用程序，用于监控显示器或应用窗口，实时解码libcimbar彩色图形矩阵条形码。

## 功能特点

- 🖥️ **多显示器支持**：可以选择监控任意显示器
- 🪟 **窗口捕获**：支持监控特定应用程序窗口
- 🔄 **实时解码**：自动检测并解码屏幕中的cimbar码
- 👀 **实时预览**：显示当前捕获的画面
- 📁 **文件管理**：自动保存解码后的文件
- 🎨 **友好界面**：简洁易用的图形界面

## 系统要求

- Python 3.8 或更高版本
- 已编译的cimbar可执行文件
- Windows/Linux/macOS（窗口捕获功能仅支持Windows）

## 安装步骤

### 1. 安装Python依赖

```bash
cd python_decoder
pip install -r requirements.txt
```

### 2. 准备cimbar可执行文件

确保已经编译了libcimbar项目，并且`cimbar`（或`cimbar.exe`）可执行文件位于以下位置之一：
- 当前目录
- 父目录的build文件夹
- PATH环境变量中

编译libcimbar的方法请参考主项目的README文档。

## 使用方法

### 启动程序

```bash
python cimbar_decoder.py
```

或者使用提供的启动脚本：
- Windows: 双击 `run_decoder.bat`
- Linux/Mac: 运行 `./run_decoder.sh`

### 操作步骤

1. **选择捕获源**
   - 选择"监控显示器"或"监控窗口"
   - 从下拉列表中选择具体的显示器或窗口

2. **开始监控**
   - 点击"开始监控"按钮
   - 程序将开始实时捕获并显示预览

3. **解码过程**
   - 当检测到cimbar码时，程序会自动解码
   - 解码状态会显示在日志区域
   - 成功解码的文件会保存到输出目录

4. **查看结果**
   - 点击"打开输出目录"查看解码后的文件
   - 或点击"选择输出目录"更改保存位置

## 配置选项

### 修改cimbar路径

如果cimbar可执行文件不在默认位置，可以在创建`CimbarDecoder`实例时指定路径：

```python
decoder = CimbarDecoder(cimbar_path="/path/to/cimbar")
```

### 调整解码参数

可以修改以下参数来优化解码性能：

- `decode_interval`: 解码间隔时间（默认0.5秒）
- 图像处理参数（在`find_cimbar_in_image`方法中）

## 故障排除

### 常见问题

1. **"找不到cimbar可执行文件"**
   - 确保已编译libcimbar项目
   - 检查cimbar路径是否正确
   - Windows用户确保文件名为`cimbar.exe`

2. **"窗口捕获功能不可用"**
   - 安装pygetwindow: `pip install pygetwindow`
   - 注意：此功能仅在Windows上可用

3. **解码失败**
   - 确保cimbar码清晰可见
   - 调整显示器亮度和对比度
   - 尝试调整解码间隔时间

4. **预览画面卡顿**
   - 降低捕获分辨率
   - 关闭其他占用资源的程序

### 调试模式

如需查看详细的调试信息，可以修改代码启用调试输出：

```python
# 在decode_image方法中添加
print(f"执行命令: {' '.join(cmd)}")
print(f"输出: {result.stdout}")
print(f"错误: {result.stderr}")
```

## 开发说明

### 项目结构

```
python_decoder/
├── cimbar_decoder.py    # 主程序
├── requirements.txt     # Python依赖
├── README.md           # 本文档
├── run_decoder.bat     # Windows启动脚本
└── run_decoder.sh      # Linux/Mac启动脚本
```

### 扩展功能

可以通过继承`CimbarDecoder`类来添加新功能：

```python
class CustomDecoder(CimbarDecoder):
    def decode_image(self, image_path):
        # 添加自定义解码逻辑
        result = super().decode_image(image_path)
        # 处理结果
        return result
```

## 许可证

本项目遵循与libcimbar相同的许可证。

## 贡献

欢迎提交Issue和Pull Request！

## 相关链接

- [libcimbar主项目](https://github.com/sz3/libcimbar)
- [OpenCV文档](https://docs.opencv.org/)
- [Python MSS文档](https://python-mss.readthedocs.io/)