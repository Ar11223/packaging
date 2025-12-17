import sys
import os
import subprocess
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QRadioButton, 
                             QCheckBox, QTextEdit, QFileDialog, QComboBox, QSlider, 
                             QMessageBox, QDialog, QFrame, QButtonGroup, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, pyqtProperty, QPropertyAnimation, QRect, QPoint
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QCursor, QIcon, QPainter, QBrush, QPen, QPolygon

# ===========================
# 依赖库检查
# ===========================
try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ===========================
# 全局样式表 (深度定制 - 紧凑商务风)
# ===========================
STYLESHEET = """
    /* 全局设定 */
    QMainWindow { background-color: #f0f0f0; }
    QWidget { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; color: #333; }

    /* 卡片容器 */
    QFrame#Card {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e8e8e8; /* 更柔和的边框 */
    }

    /* 标题 */
    QLabel#CardTitle {
        font-weight: bold;
        font-size: 14px;
        color: #3f4f60; /* 柔和的标题颜色 */
        padding-bottom: 5px;
    }

    /* 输入框 */
    QLineEdit {
        border: 1px solid #e0e0e0; /* 柔和的边框 */
        border-radius: 6px;
        padding: 8px 10px;
        background-color: #ffffff; /* 保持白色背景 */
    }
    QLineEdit:focus {
        border: 1px solid #4a90e2; /* 与主色调一致 */
        background-color: #fff;
    }

    /* 通用按钮 (浏览/选择) */
    QPushButton#GhostBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0e0e0, stop:1 #d0d0d0);
        border: 1px solid #c0c0c0;
        border-radius: 6px;
        color: #333;
        padding: 7px 12px;
        font-weight: 500;
    }
    QPushButton#GhostBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d0d0d0, stop:1 #c0c0c0);
        border-color: #b0b0b0;
        color: #222;
    }

    /* 编译器选择器 */
    QRadioButton#CompilerBtn {
        background-color: #f8f8f8;
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        padding: 10px 15px;
        color: #555;
        font-weight: bold;
        text-align: left;
    }
    QRadioButton#CompilerBtn::indicator { width: 0; height: 0; }
    QRadioButton#CompilerBtn:checked {
        background-color: #e8f0fe;
        border: 1px solid #4a90e2;
        color: #4a90e2;
    }
    QRadioButton#CompilerBtn:hover {
        border-color: #b0d0f0;
    }

    /* 环境选择 (Tab 样式) */
    QRadioButton#TabBtn {
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 20px;
        color: #909399;
        font-weight: 500;
    }
    QRadioButton#TabBtn::indicator { width: 0; height: 0; }
    QRadioButton#TabBtn:checked {
        color: #303133;
        border-bottom: 2px solid #4a90e2; /* 与PrimaryBtn主色调保持一致 */
        font-weight: bold;
    }

    /* 分段控制器 (Segmented Control) */
    QFrame#SegmentedControlFrame {
        border: 1px solid #dcdcdc; /* 整体边框 */
        border-radius: 8px; /* 整体圆角 */
        background-color: #f8f8f8; /* 整体背景 */
        padding: 0px; /* 内部无填充 */
    }

    QRadioButton#SegmentedControlBtn {
        background-color: transparent; /* 默认透明背景 */
        border: none; /* 移除默认边框 */
        padding: 8px 20px;
        color: #555;
        font-weight: 500;
        min-width: 100px; /* 最小宽度 */
    }
    QRadioButton#SegmentedControlBtn::indicator {
        width: 0;
        height: 0;
    }
    QRadioButton#SegmentedControlBtn:hover {
        color: #3a80d2;
    }
    QRadioButton#SegmentedControlBtn:checked {
        background-color: #4a90e2; /* 选中背景色 */
        color: white; /* 选中字体颜色 */
        border-radius: 7px; /* 内部圆角，比Frame小1px */
        font-weight: bold;
    }
    /* 针对分段控制器中的第一个和最后一个按钮的特殊处理 */
    QRadioButton#SegmentedControlBtn:first-of-type {
        border-top-left-radius: 7px;
        border-bottom-left-radius: 7px;
    }
    QRadioButton#SegmentedControlBtn:last-of-type {
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
    }

    /* 立即打包大按钮 */
    QPushButton#PrimaryBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4a90e2, stop:1 #6aafff);
        border: none;
        border-radius: 8px;
        color: white;
        font-size: 16px;
        font-weight: bold;
        padding: 12px;
    }
    QPushButton#PrimaryBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a9ff2, stop:1 #7ac0ff); }
    QPushButton#PrimaryBtn:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a80d2, stop:1 #5aa0ef); }
    QPushButton#PrimaryBtn:disabled { background-color: #bdc3c7; }

    /* 成功按钮 */
    QPushButton#SuccessBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
        border: none;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        padding: 8px 20px;
    }
    QPushButton#SuccessBtn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3ede81, stop:1 #32be70); }

    /* 滑动开关 (Toggle Switch) */
    /* 底部日志 */
    QTextEdit#LogArea {
        background-color: #333333; /* 稍亮的深色背景，与整体更协调 */
        color: #e0e0e0;
        border: none;
        border-radius: 0;
        font-family: Consolas, "Courier New", monospace;
        font-size: 12px;
        padding: 12px;
    }
    
    /* 计时器 */
    QLabel#Timer {
        font-size: 24px;
        font-weight: 300;
        color: #4a90e2; /* 与主色调一致 */
        font-family: "Segoe UI Light";
    }
    /* 下拉选择框 */
    QComboBox {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 8px 10px;
        background-color: #ffffff;
        selection-background-color: #e0e0e0;
    }
    QComboBox:focus {
        border: 1px solid #4a90e2;
    }
    QComboBox::drop-down {
        border: none;
        background-color: transparent;
        width: 20px;
    }
    QComboBox::down-arrow {
        image: url(none); /* 隐藏默认箭头 */
    }

    /* 滑块 */
    QSlider::groove:horizontal {
        height: 6px;
        background: #e0e0e0;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #4a90e2;
        width: 16px;
        height: 16px;
        border-radius: 8px;
        margin: -5px 0;
    }
    QSlider::handle:horizontal:hover {
        background: #6aafff;
    }
    QSlider::add-page:horizontal {
        background: #c0c0c0;
    }
    QSlider::sub-page:horizontal {
        background: #4a90e2;
    }
"""

MINGW_DIR_NAME = "mingw64"

# ===========================
# 逻辑核心
# ===========================
class IconProcessor:
    @staticmethod
    def create_shaped_icon(image_path, shape='rounded', size=256, zoom=1.0):
        if not HAS_PILLOW: return None
        try:
            img = Image.open(image_path).convert("RGBA")
            orig_w, orig_h = img.size
            base_scale = max(size / orig_w, size / orig_h)
            final_scale = base_scale * zoom
            new_w, new_h = int(orig_w * final_scale), int(orig_h * final_scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            background = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            paste_x = (size - new_w) // 2; paste_y = (size - new_h) // 2
            background.paste(img, (paste_x, paste_y)); img = background 
            mask = Image.new('L', (size, size), 0); draw = ImageDraw.Draw(mask)
            if shape == 'square': draw.rectangle((0, 0, size, size), fill=255)
            elif shape == 'circle': draw.ellipse((0, 0, size, size), fill=255)
            elif shape == 'rounded': r = int(size * 0.18); draw.rounded_rectangle((0, 0, size, size), radius=r, fill=255)
            elif shape == 'heart':
                scale_heart = 0.9; offset_x = size * (1 - scale_heart) / 2; offset_y = size * (1 - scale_heart) / 2; s = size * scale_heart
                draw.polygon([(size/2, s*0.95+offset_y),(s*0.05+offset_x, s*0.4+offset_y),(s*0.25+offset_x, s*0.1+offset_y),(size/2, s*0.3+offset_y),(s*0.75+offset_x, s*0.1+offset_y),(s*0.95+offset_x, s*0.4+offset_y)], fill=255)
            output = Image.new('RGBA', (size, size), (0, 0, 0, 0)); output.paste(img, (0, 0), mask=mask)
            return output
        except: return None

class EnvManager:
    def __init__(self): self.python_path = sys.executable
    def set_python_path(self, path): 
        if os.path.exists(path): self.python_path = path; return True
        return False
    def install_package(self, pkg, signal):
        cmd = [self.python_path, "-m", "pip", "install", pkg]
        signal.emit(f"安装依赖: {' '.join(cmd)}\n")
        try: subprocess.check_call(cmd); return True
        except: return False

class BaseTool:
    def __init__(self, env): self.env = env
    def check_installed(self):
        try: subprocess.check_call([self.env.python_path, "-c", f"import {self.module_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return True
        except: return False
    def find_upx(self):
        base = os.path.dirname(os.path.abspath(__file__)); tools = os.path.join(base, "tools")
        if not os.path.exists(tools): return None
        for r, d, f in os.walk(tools):
            if "upx.exe" in f: return r
        return None

class PyInstallerTool(BaseTool):
    def __init__(self, env): self.env = env; self.name = "PyInstaller"; self.module_name = "PyInstaller"
    def get_cmd(self, target, out, nocon, icon, upx):
        if not os.path.exists(out): os.makedirs(out)
        cmd = [self.env.python_path, "-m", "PyInstaller", "-F", target, "--distpath", out, "--specpath", out, "--workpath", os.path.join(out, "build_temp")]
        if nocon: cmd.append("-w")
        if icon: cmd.extend(["--icon", icon])
        if upx:
            u = self.find_upx()
            if u: cmd.extend(["--upx-dir", u])
            else: cmd.append("--noupx")
        else: cmd.append("--noupx")
        return cmd, None

class NuitkaTool(BaseTool):
    def __init__(self, env): self.env = env; self.name = "Nuitka"; self.module_name = "nuitka"
    def get_cmd(self, target, out, nocon, icon, upx):
        # 1. 定位 MinGW
        base = os.path.dirname(os.path.abspath(__file__))
        mingw = os.path.join(base, "tools", MINGW_DIR_NAME, "mingw64", "bin")
        if not os.path.exists(mingw): 
            mingw = os.path.join(base, "tools", MINGW_DIR_NAME, "bin")
        
        # 2. 注入环境变量
        env = os.environ.copy()
        if os.path.exists(mingw): 
            env["PATH"] = mingw + os.pathsep + env["PATH"]
            
        # 3. 准备输出
        if not os.path.exists(out): os.makedirs(out)
        
        # 4. 构建命令 (修复版)
        cmd = [
            self.env.python_path, 
            "-m", "nuitka", 
            "--standalone", 
            "--onefile", 
            
            # --- 修复核心: 启用 PyQt6 插件 ---
            "--enable-plugin=pyqt6", 
            "--include-qt-plugins=sensible,styles,platforms", 
            
            "--assume-yes-for-downloads", 
            "--remove-output", 
            f"--output-dir={out}", 
            target
        ]

        # --- 修复核心: 强制 MinGW ---
        cmd.append("--mingw64")

        # 控制台
        if nocon: 
            cmd.append("--windows-console-mode=disable")
        
        # 图标
        if icon: 
            cmd.append(f"--windows-icon-from-ico={icon}")
            
        # UPX
        if upx:
            u = self.find_upx()
            if u: 
                cmd.append("--enable-plugin=upx")
                env["PATH"] = u + os.pathsep + env["PATH"]
            else: 
                cmd.append("--disable-plugin=upx")
        else: 
            cmd.append("--disable-plugin=upx")
            
        return cmd, env

class WorkerSignals(QObject): log = pyqtSignal(str); finished = pyqtSignal(bool)
class ToolRunner(QObject):
    def __init__(self, cmd, env): super().__init__(); self.cmd = cmd; self.env = env; self.signals = WorkerSignals()
    def run(self):
        try:
            si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, startupinfo=si, env=self.env)
            for l in p.stdout: self.signals.log.emit(l)
            p.wait()
            self.signals.finished.emit(p.returncode == 0)
        except Exception as e: self.signals.log.emit(str(e)); self.signals.finished.emit(False)

# ===========================
# UI 组件
# ===========================
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15); shadow.setColor(QColor(0, 0, 0, 10)); shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class ToggleSwitch(QWidget):
    def __init__(self, parent=None, w=50, h=28):
        super().__init__(parent)
        self._w, self._h = w, h
        self.setFixedSize(w, h)

        self._on = False                       # 开关状态
        self._margin = 2                       # 滑块与背景边缘间距
        self._thumb_radius = (h - 2 * self._margin) // 2
        self._track_radius = h // 2

        # 颜色可自定义
        self._track_off_color = "#c5c5c5"
        self._track_on_color  = "#1890FF" # 调整为蓝色
        self._thumb_color     = "#ffffff"

        # 动画
        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(120)

    # -------------- 属性：滑块 x 坐标 --------------
    def get_thumb_x(self):
        return self._thumb_x if hasattr(self, "_thumb_x") else self._margin

    def set_thumb_x(self, x):
        self._thumb_x = x
        self.update()

    thumb_x = pyqtProperty(int, get_thumb_x, set_thumb_x)

    # -------------- 尺寸、绘制 --------------
    def paintEvent(self, _):
        from PyQt6.QtGui import QPainter, QBrush, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 画轨道
        track_color = self._track_on_color if self._on else self._track_off_color
        p.setBrush(QBrush(QColor(track_color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self._w, self._h, self._track_radius, self._track_radius)

        # 画滑块
        p.setBrush(QBrush(QColor(self._thumb_color)))
        p.drawEllipse(self.get_thumb_x(), self._margin,
                      self._thumb_radius * 2, self._thumb_radius * 2)

    # -------------- 鼠标交互 --------------
    def mousePressEvent(self, e):
        self._start_x = e.position().x()
        self._anim.stop()

    def mouseReleaseEvent(self, e):
        # 轻点切换 / 拖动过半切换
        if abs(e.position().x() - self._start_x) < 5:          # 点击
            self.toggle()
        else:                                                    # 拖动
            mid = self._w / 2
            self.set_on(e.position().x() > mid)

    def toggle(self):
        self.set_on(not self._on)

    def set_on(self, on: bool):
        if self._on == on:
            return
        self._on = on
        self._anim.setStartValue(self.get_thumb_x())
        end = self._w - self._thumb_radius * 2 - self._margin if on else self._margin
        self._anim.setEndValue(end)
        self._anim.start()
        self.toggled.emit(on)

    # -------------- 信号 --------------
    toggled = pyqtSignal(bool)


# ===========================
# 图标制作弹窗
# ===========================
class IconDialog(QDialog):
    def __init__(self, parent, callback, default_dir):
        super().__init__(parent)
        self.setWindowTitle("图标工作台")
        self.setFixedSize(650, 400)
        self.callback = callback; self.default_dir = default_dir; self.img_path = None; self.zoom = 1.0
        # self.setStyleSheet("background-color: #f0f0f0;") # 移除此行，让其继承全局样式
        layout = QHBoxLayout(self)
        self.lbl_prev = QLabel("暂无图片"); self.lbl_prev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prev.setStyleSheet("background: #ffffff; border-radius: 8px; border: 1px solid #e8e8e8; color: #999; font-size: 13px;")
        layout.addWidget(self.lbl_prev, 5)
        ctrl = QVBoxLayout()
        btn_open = QPushButton("打开图片"); btn_open.clicked.connect(self.load); btn_open.setObjectName("GhostBtn")
        ctrl.addWidget(btn_open)
        ctrl.addWidget(QLabel("形状:"))
        self.cmb = QComboBox(objectName="IconShapeComboBox"); self.cmb.addItems(["圆角", "方", "圆", "心"]); self.cmb.currentIndexChanged.connect(self.refresh)
        ctrl.addWidget(self.cmb)
        ctrl.addWidget(QLabel("缩放:"))
        self.sld = QSlider(Qt.Orientation.Horizontal, objectName="IconZoomSlider"); self.sld.setRange(50,200); self.sld.setValue(100); self.sld.valueChanged.connect(self.slide)
        ctrl.addWidget(self.sld)
        ctrl.addStretch()
        btn_ok = QPushButton("✅ 生成并使用"); btn_ok.setObjectName("SuccessBtn"); btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor)); btn_ok.clicked.connect(self.apply)
        ctrl.addWidget(btn_ok)
        layout.addLayout(ctrl, 3)

    def load(self):
        p, _ = QFileDialog.getOpenFileName(self, "Img", "", "*.png *.jpg"); 
        if p: self.img_path = p; self.refresh()
    def slide(self): self.zoom = self.sld.value()/100.0; self.refresh()
    def refresh(self):
        if not self.img_path: return
        map_s = ["rounded", "square", "circle", "heart"]
        current_shape_str = map_s[self.cmb.currentIndex()]
        self.cur = IconProcessor.create_shaped_icon(self.img_path, current_shape_str, 256, self.zoom)

        if self.cur:
            # 1. 将PIL Image转换为QImage
            qimage = QImage(self.cur.convert("RGBA").tobytes("raw", "RGBA"),
                            self.cur.size[0], self.cur.size[1],
                            QImage.Format.Format_RGBA8888)
            
            # 2. 从QImage创建QPixmap (原始大小 256x256)
            original_pixmap = QPixmap.fromImage(qimage)
            
            # 3. 在original_pixmap上绘制形状轮廓
            painter = QPainter(original_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 添加一个通用的虚线边框作为“小框”
            painter.setPen(QPen(QColor(100, 100, 100, 150), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(0, 0, 256, 256) # 绘制一个围绕整个 256x256 画布的矩形

            # 设置画笔：半透明蓝色实线边框 (用于特定形状轮廓)
            painter.setPen(QPen(QColor(74, 144, 226, 200), 4, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush) # 无填充
            
            # 定义绘制区域（相对于256x256的pixmap）
            rect = QRect(0, 0, 256, 256)
            
            if current_shape_str == 'square':
                painter.drawRect(rect)
            elif current_shape_str == 'circle':
                painter.drawEllipse(rect)
            elif current_shape_str == 'rounded':
                radius = int(256 * 0.18)
                painter.drawRoundedRect(rect, radius, radius)
            elif current_shape_str == 'heart':
                scale_heart = 0.9
                offset_x = 256 * (1 - scale_heart) / 2
                offset_y = 256 * (1 - scale_heart) / 2
                s = 256 * scale_heart

                points = [
                    (256/2, s*0.95+offset_y),
                    (s*0.05+offset_x, s*0.4+offset_y),
                    (s*0.25+offset_x, s*0.1+offset_y),
                    (256/2, s*0.3+offset_y),
                    (s*0.75+offset_x, s*0.1+offset_y),
                    (s*0.95+offset_x, s*0.4+offset_y)
                ]
                
                q_points = [QPoint(int(p[0]), int(p[1])) for p in points]
                painter.drawPolygon(QPolygon(q_points))
            
            painter.end() # 结束绘制
            
            # 4. 缩放并设置给lbl_prev
            self.lbl_prev.setPixmap(original_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_prev.setText("")
    def apply(self):
        if hasattr(self, 'cur'):
            d = self.default_dir or os.getcwd(); p = os.path.join(d, "icon.ico")
            self.cur.save(p, format='ICO', sizes=[(256,256),(128,128),(48,48),(16,16)])
            self.callback(p); self.accept()

# ===========================
# 主界面
# ===========================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Packer Pro")
        self.resize(800, 680)
        self.env_mgr = EnvManager()
        
        # 自动加载 name.png 图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "name.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.start_ts = 0
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 1. 入口文件
        card_file = QFrame(objectName="Card")
        l_file = QVBoxLayout(card_file)
        l_file.setContentsMargins(10, 10, 10, 10)
        l_file.addWidget(QLabel("入口文件", objectName="CardTitle"))
        h_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setPlaceholderText("选择主程序 .py 文件")
        self.txt_file.setReadOnly(True)
        btn_file = QPushButton("选择文件", objectName="GhostBtn"); btn_file.clicked.connect(self.sel_file)
        h_file.addWidget(self.txt_file); h_file.addWidget(btn_file)
        l_file.addLayout(h_file)
        layout.addWidget(card_file)

        # 2. 环境
        card_env = QFrame(objectName="Card")
        l_env = QVBoxLayout(card_env)
        l_env.setContentsMargins(10, 10, 10, 10)
        l_env.addWidget(QLabel("编译环境", objectName="CardTitle"))
        
        # 分段控制器布局
        self.bg_env_selection = QButtonGroup(self) # 创建一个QButtonGroup来管理单选按钮
        
        segmented_frame = QFrame(objectName="SegmentedControlFrame")
        segmented_layout = QHBoxLayout(segmented_frame)
        segmented_layout.setContentsMargins(1, 1, 1, 1) # 调整内边距以适应边框
        segmented_layout.setSpacing(0) # 确保按钮之间没有间距

        self.rb_auto = QRadioButton("自动检测", objectName="SegmentedControlBtn")
        self.rb_auto.setChecked(True)
        self.rb_auto.toggled.connect(self.detect_env)
        self.bg_env_selection.addButton(self.rb_auto)

        self.rb_man = QRadioButton("手动指定", objectName="SegmentedControlBtn")
        self.rb_man.toggled.connect(self.man_env)
        self.bg_env_selection.addButton(self.rb_man)

        segmented_layout.addWidget(self.rb_auto, 1) # 设置拉伸系数为1
        segmented_layout.addWidget(self.rb_man, 1) # 设置拉伸系数为1
        # 移除 segmented_layout.addStretch() 因为按钮会均匀填充可用空间

        l_env.addWidget(segmented_frame) # 将分段控制器框架添加到环境卡片布局中

        # 路径显示框
        bg_path = QFrame()
        bg_path.setStyleSheet("background: #f8f9fa; border-radius: 6px; padding: 8px;")
        
        l_path = QHBoxLayout(bg_path)
        l_path.setContentsMargins(5, 0, 5, 0) # 保持与原设计一致的内边距

        self.lbl_env = QLabel(f"{self.env_mgr.python_path}")
        self.lbl_env.setStyleSheet("color: #606266; font-family: Consolas; font-size: 12px;")
        
        l_path.addWidget(self.lbl_env)
        l_path.addStretch()

        l_env.addWidget(bg_path) # 添加路径框到环境卡片布局中 (确保只添加一次)
        layout.addWidget(card_env)

        # 3. 资源
        card_res = QFrame(objectName="Card")
        l_res = QVBoxLayout(card_res)
        l_res.setContentsMargins(10, 10, 10, 10)
        l_res.addWidget(QLabel("资源与输出", objectName="CardTitle"))
        h_out = QHBoxLayout()
        lbl_out = QLabel("输出位置:"); lbl_out.setFixedWidth(70)
        self.txt_out = QLineEdit(); self.txt_out.setPlaceholderText("默认 dist_output")
        btn_out = QPushButton("选择目录", objectName="GhostBtn"); btn_out.clicked.connect(self.sel_out)
        h_out.addWidget(lbl_out); h_out.addWidget(self.txt_out); h_out.addWidget(btn_out)
        l_res.addLayout(h_out)
        h_icon = QHBoxLayout()
        lbl_icon = QLabel("应用图标:"); lbl_icon.setFixedWidth(70)
        self.txt_icon = QLineEdit(); self.txt_icon.setPlaceholderText("可选")
        btn_make = QPushButton("制作", objectName="GhostBtn"); btn_make.clicked.connect(self.make_icon)
        btn_sel = QPushButton("选择", objectName="GhostBtn"); btn_sel.clicked.connect(self.sel_icon)
        h_icon.addWidget(lbl_icon); h_icon.addWidget(self.txt_icon); h_icon.addWidget(btn_make); h_icon.addWidget(btn_sel)
        l_res.addLayout(h_icon)
        layout.addWidget(card_res)

        # 4. 选项
        card_opt = QFrame(objectName="Card")
        l_opt = QVBoxLayout(card_opt)
        l_opt.setContentsMargins(10, 10, 10, 10)
        l_opt.addWidget(QLabel("构建选项", objectName="CardTitle"))
        
        h_opt_main = QHBoxLayout()
        v_compiler = QVBoxLayout()
        self.bg_comp = QButtonGroup()
        self.rb_nuitka = QRadioButton("Nuitka 编译器", objectName="CompilerBtn"); self.rb_nuitka.setChecked(True)
        self.rb_pyi = QRadioButton("PyInstaller 打包器", objectName="CompilerBtn")
        self.bg_comp.addButton(self.rb_nuitka); self.bg_comp.addButton(self.rb_pyi)

        # 左侧布局: PyInstaller 和 隐藏控制台
        v_left_column = QVBoxLayout()
        v_left_column.addWidget(self.rb_pyi)
        
        h_nocon = QHBoxLayout()
        self.chk_nocon = ToggleSwitch(self, w=38, h=22); self.chk_nocon.set_on(True)
        self.lbl_nocon = QLabel("隐藏控制台")
        h_nocon.addWidget(self.chk_nocon); h_nocon.addWidget(self.lbl_nocon); h_nocon.addStretch()
        v_left_column.addLayout(h_nocon)
        v_left_column.addStretch() # 确保左侧内容向上对齐

        # 右侧布局: Nuitka 和 UPX 压缩
        v_right_column = QVBoxLayout()
        v_right_column.addWidget(self.rb_nuitka)

        h_upx = QHBoxLayout()
        self.chk_upx = ToggleSwitch(self, w=38, h=22); self.chk_upx.set_on(True)
        self.lbl_upx = QLabel("UPX 压缩")
        h_upx.addWidget(self.chk_upx); h_upx.addWidget(self.lbl_upx); h_upx.addStretch()
        v_right_column.addLayout(h_upx)
        v_right_column.addStretch() # 确保右侧内容向上对齐

        h_opt_main.addLayout(v_left_column)
        h_opt_main.addLayout(v_right_column)
        l_opt.addLayout(h_opt_main)
        layout.addWidget(card_opt)

        layout.addStretch()

        # 5. 操作区
        h_action = QHBoxLayout()
        self.lbl_timer = QLabel("00:00", objectName="Timer"); self.lbl_timer.setVisible(False)
        self.btn_run = QPushButton("立即打包", objectName="PrimaryBtn")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(15); shadow.setColor(QColor(41, 128, 185, 60)); shadow.setOffset(0, 4)
        self.btn_run.setGraphicsEffect(shadow)
        self.btn_run.clicked.connect(self.start)
        h_action.addWidget(self.lbl_timer)
        h_action.addStretch()
        h_action.addWidget(self.btn_run)
        layout.addLayout(h_action)

        # 6. 日志
        self.txt_log = QTextEdit(objectName="LogArea"); self.txt_log.setPlaceholderText("Ready..."); self.txt_log.setFixedHeight(100); self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log)
        self.sig_log = pyqtSignal(str)

    # 逻辑部分
    def sel_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "File", "", "*.py")
        if f:
            self.txt_file.setText(f)
            if not self.txt_out.text(): self.txt_out.setText(os.path.join(os.path.dirname(f), "dist_output"))
            if self.rb_auto.isChecked(): self.detect_env()
    def sel_out(self):
        d = QFileDialog.getExistingDirectory(self, "Dir"); 
        if d: self.txt_out.setText(d)
    def sel_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "Icon", "", "*.ico"); 
        if f: self.txt_icon.setText(f)
    def make_icon(self):
        if not HAS_PILLOW: return QMessageBox.warning(self, "Tips", "Install Pillow first.")
        IconDialog(self, lambda p: self.txt_icon.setText(p), self.txt_out.text() or os.getcwd()).exec()
    def detect_env(self):
        if not self.rb_auto.isChecked(): return
        base = os.path.dirname(self.txt_file.text()) if self.txt_file.text() else os.getcwd()
        found = False
        for d in ["venv", ".venv", "env"]:
            p = os.path.join(base, d)
            if os.path.exists(p):
                exe = os.path.join(p, "Scripts", "python.exe") if os.name=='nt' else os.path.join(p, "bin", "python")
                if os.path.exists(exe): self.env_mgr.set_python_path(exe); self.lbl_env.setText(f"自动检测: {exe}"); found=True; break
        if not found: self.env_mgr.set_python_path(sys.executable); self.lbl_env.setText(f"系统全局: {sys.executable}")
    def man_env(self):
        if not self.rb_man.isChecked(): return
        f, _ = QFileDialog.getOpenFileName(self, "Python Exe", "", "*.exe")
        if f: self.env_mgr.set_python_path(f); self.lbl_env.setText(f"手动: {f}")
        else: self.rb_auto.setChecked(True)
    def tick(self):
        s = int(time.time() - self.start_ts)
        self.lbl_timer.setText(f"{s//60:02d}:{s%60:02d}")
    def append_log(self, t): self.txt_log.append(t.strip()); self.txt_log.verticalScrollBar().setValue(100000)
    sig_log_bridge = pyqtSignal(str)
    def start(self):
        tgt = self.txt_file.text(); 
        if not tgt: return QMessageBox.warning(self, "!", "请选择入口文件")
        self.btn_run.setEnabled(False); self.btn_run.setText("打包构建中..."); self.txt_log.clear()
        self.start_ts = time.time(); self.lbl_timer.setVisible(True); self.timer.start(1000)
        threading.Thread(target=self.worker, daemon=True).start()
    def worker(self):
        self.sig_log_bridge.connect(self.append_log)
        try:
            tgt = self.txt_file.text(); out = self.txt_out.text(); icon = self.txt_icon.text(); nocon = self.chk_nocon._on; upx = self.chk_upx._on
            tool = PyInstallerTool(self.env_mgr) if self.rb_pyi.isChecked() else NuitkaTool(self.env_mgr)
            if not tool.check_installed():
                self.sig_log_bridge.emit(f"安装依赖 {tool.name}..."); self.env_mgr.install_package(tool.module_name, self.sig_log_bridge)
            cmd, env = tool.get_cmd(tgt, out, nocon, icon, upx)
            self.sig_log_bridge.emit(f"Run: {' '.join(cmd)}\n")
            runner = ToolRunner(cmd, env); runner.signals.log.connect(self.sig_log_bridge.emit); runner.signals.finished.connect(self.done); runner.run()
        except Exception as e: self.sig_log_bridge.emit(str(e)); self.done(False)
    def done(self, s):
        self.timer.stop(); self.btn_run.setEnabled(True); self.btn_run.setText("立即打包")
        if s: QMessageBox.information(self, "OK", "Success!"); os.startfile(self.txt_out.text())
        else: QMessageBox.critical(self, "Err", "Failed.")
        try: self.sig_log_bridge.disconnect() 
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # 显式设置应用程序的默认字体，以避免某些环境下字体大小为0
    default_font = QFont("Segoe UI", 9)  # 设置一个合理的默认字体和大小
    app.setFont(default_font)
    
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())