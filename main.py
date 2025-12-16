import sys
import os
import subprocess
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QLabel, QLineEdit, QPushButton, QRadioButton, 
                             QCheckBox, QTextEdit, QFileDialog, QComboBox, QSlider, 
                             QMessageBox, QDialog, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QLinearGradient, QGradient

# ===========================
# 依赖检查
# ===========================
try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ===========================
# 全局常量与样式表
# ===========================
MINGW_DIR_NAME = "mingw64"

# 商务简约风格 QSS
STYLESHEET = """
    /* 全局字体与背景 */
    QWidget {
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 13px;
        color: #2c3e50;
    }
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);
    }
    
    /* 分组框：去除边框，仅保留标题强调 */
    QGroupBox {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 24px;
        font-weight: bold;
        font-size: 14px;
        color: #34495e;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 10px;
        left: 10px;
        background-color: transparent; 
        color: #2c3e50;
    }

    /* 输入框：极简线条 */
    QLineEdit {
        border: 1px solid #ced4da;
        border-radius: 4px;
        padding: 6px 10px;
        background-color: #fcfcfc;
        selection-background-color: #3498db;
    }
    QLineEdit:focus {
        border: 1px solid #3498db;
        background-color: white;
    }
    QLineEdit:read-only {
        background-color: #f1f3f5;
        color: #868e96;
    }

    /* 普通按钮：白色微渐变，带阴影 */
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f1f3f5);
        border: 1px solid #ced4da;
        border-radius: 5px;
        padding: 6px 16px;
        color: #495057;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #f8f9fa;
        border-color: #adb5bd;
        color: #212529;
    }
    QPushButton:pressed {
        background-color: #e9ecef;
        padding-top: 7px; /* 按下位移感 */
        padding-left: 17px;
    }

    /* 主操作按钮（Primary）：深蓝渐变 */
    QPushButton#PrimaryBtn {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #2c3e50);
        border: none;
        color: white;
        font-weight: bold;
        font-size: 15px;
        border-radius: 6px;
    }
    QPushButton#PrimaryBtn:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #34495e);
    }
    QPushButton#PrimaryBtn:disabled {
        background-color: #bdc3c7;
        color: #f0f0f0;
    }

    /* 成功按钮（Success）：墨绿渐变 */
    QPushButton#SuccessBtn {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #27ae60, stop:1 #219150);
        border: none;
        color: white;
        font-weight: bold;
    }
    QPushButton#SuccessBtn:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2ecc71, stop:1 #27ae60);
    }

    /* 优雅的滑动条 */
    QSlider::groove:horizontal {
        border: 1px solid #e0e0e0;
        height: 6px; /* 轨道厚度 */
        background: #ecf0f1;
        margin: 2px 0;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: white;
        border: 1px solid #bdc3c7;
        width: 18px;
        height: 18px;
        margin: -7px 0; /* 居中 */
        border-radius: 9px; /* 圆形 */
    }
    QSlider::handle:horizontal:hover {
        border-color: #3498db;
        background: #f8f9fa;
    }
    QSlider::sub-page:horizontal {
        background: #3498db; /* 选中区域颜色 */
        border-radius: 3px;
    }

    /* 复选框与单选框 */
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
    }
    QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
        border: 1px solid #bdc3c7;
        background: white;
        border-radius: 3px; /* 复选框微圆角 */
    }
    QRadioButton::indicator:unchecked {
        border-radius: 8px; /* 单选框圆形 */
    }
    QCheckBox::indicator:checked {
        background-color: #3498db;
        border: 1px solid #3498db;
        image: url(none); /* 纯色风格，也可以用自定义图标 */
    }
    QRadioButton::indicator:checked {
        background-color: #3498db;
        border: 4px solid white; /* 同心圆效果 */
        outline: 1px solid #3498db;
    }

    /* 日志区域 */
    QTextEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        border: 1px solid #34495e;
        border-radius: 6px;
        font-family: Consolas, "Courier New", monospace;
        padding: 8px;
    }

    /* 计时器文字 */
    QLabel#TimerLabel {
        font-size: 24px;
        font-weight: 300; /* 细体更具现代感 */
        color: #e67e22;
        font-family: "Segoe UI Light", sans-serif;
    }
"""

# ===========================
# 1. 核心逻辑 (Icon & Tools)
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
            paste_x = (size - new_w) // 2
            paste_y = (size - new_h) // 2
            background.paste(img, (paste_x, paste_y))
            img = background 

            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)

            if shape == 'square':
                draw.rectangle((0, 0, size, size), fill=255)
            elif shape == 'circle':
                draw.ellipse((0, 0, size, size), fill=255)
            elif shape == 'rounded':
                r = int(size * 0.18)
                draw.rounded_rectangle((0, 0, size, size), radius=r, fill=255)
            elif shape == 'heart':
                scale_heart = 0.9 
                offset_x = size * (1 - scale_heart) / 2
                offset_y = size * (1 - scale_heart) / 2
                s = size * scale_heart
                draw.polygon([
                    (size/2, s * 0.95 + offset_y),
                    (s * 0.05 + offset_x, s * 0.4 + offset_y),
                    (s * 0.25 + offset_x, s * 0.1 + offset_y),
                    (size/2, s * 0.3 + offset_y),
                    (s * 0.75 + offset_x, s * 0.1 + offset_y),
                    (s * 0.95 + offset_x, s * 0.4 + offset_y)
                ], fill=255)

            output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            output.paste(img, (0, 0), mask=mask)
            return output
        except Exception as e:
            return None

class WorkerSignals(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)

class ToolRunner(QObject):
    def __init__(self, cmd, env):
        super().__init__()
        self.cmd = cmd
        self.env = env
        self.signals = WorkerSignals()

    def run(self):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                startupinfo=startupinfo, env=self.env
            )
            for line in process.stdout:
                self.signals.log.emit(line)
            process.wait()
            self.signals.finished.emit(process.returncode == 0)
        except Exception as e:
            self.signals.log.emit(f"Critical Error: {str(e)}\n")
            self.signals.finished.emit(False)

class EnvManager:
    def __init__(self):
        self.python_path = sys.executable

    def set_python_path(self, path):
        if os.path.exists(path):
            self.python_path = path
            return True
        return False
    
    def install_package(self, pkg_name, signal):
        cmd = [self.python_path, "-m", "pip", "install", pkg_name]
        signal.emit(f"安装依赖中: {' '.join(cmd)}\n")
        try:
            subprocess.check_call(cmd)
            return True
        except: return False

class BaseTool:
    def __init__(self, env_manager):
        self.env = env_manager
        self.name = "Base"
        self.module_name = "base"
    
    def check_installed(self):
        try:
            subprocess.check_call([self.env.python_path, "-c", f"import {self.module_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except: return False

    def find_upx_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tools_dir = os.path.join(base_dir, "tools")
        if not os.path.exists(tools_dir): return None
        for root, dirs, files in os.walk(tools_dir):
            if "upx.exe" in files: return root
        return None

class PyInstallerTool(BaseTool):
    def __init__(self, env_manager):
        super().__init__(env_manager)
        self.name = "PyInstaller"
        self.module_name = "PyInstaller"

    def get_build_info(self, target, out, nocon, icon, use_upx):
        if not os.path.exists(out): os.makedirs(out)
        cmd = [self.env.python_path, "-m", "PyInstaller", "-F", target, "--distpath", out, "--specpath", out, "--workpath", os.path.join(out, "build_temp")]
        if nocon: cmd.append("-w")
        if icon: cmd.extend(["--icon", icon])
        if use_upx:
            upx = self.find_upx_path()
            if upx: cmd.extend(["--upx-dir", upx])
            else: cmd.append("--noupx")
        else: cmd.append("--noupx")
        return cmd, None, None

class NuitkaTool(BaseTool):
    def __init__(self, env_manager):
        super().__init__(env_manager)
        self.name = "Nuitka"
        self.module_name = "nuitka"

    def get_build_info(self, target, out, nocon, icon, use_upx):
        base = os.path.dirname(os.path.abspath(__file__))
        mingw = os.path.join(base, "tools", MINGW_DIR_NAME, "mingw64", "bin")
        if not os.path.exists(mingw): 
            mingw_fallback = os.path.join(base, "tools", MINGW_DIR_NAME, "bin")
            if os.path.exists(mingw_fallback): mingw = mingw_fallback
        
        c_env = os.environ.copy()
        found_cc = False
        if os.path.exists(mingw) and os.path.exists(os.path.join(mingw, "gcc.exe")):
            c_env["PATH"] = mingw + os.pathsep + c_env["PATH"]
            found_cc = True
            
        if not os.path.exists(out): os.makedirs(out)
        cmd = [self.env.python_path, "-m", "nuitka", "--standalone", "--onefile", "--enable-plugin=tk-inter", "--assume-yes-for-downloads", "--remove-output", f"--output-dir={out}", target]
        if nocon: cmd.append("--windows-disable-console")
        if icon: cmd.append(f"--windows-icon-from-ico={icon}")
        
        upx_found = False
        if use_upx:
            upx = self.find_upx_path()
            if upx:
                cmd.append("--enable-plugin=upx")
                c_env["PATH"] = upx + os.pathsep + c_env["PATH"]
                upx_found = True
        if not upx_found: cmd.append("--disable-plugin=upx")

        return cmd, c_env, found_cc

# ===========================
# 2. 图标工作台 (QDialog)
# ===========================
class IconGeneratorDialog(QDialog):
    def __init__(self, parent, callback, default_save_dir="."):
        super().__init__(parent)
        self.setWindowTitle("图标工作台")
        self.setFixedSize(720, 480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # 白色背景
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        self.callback = callback
        self.default_save_dir = default_save_dir
        self.img_path = None
        self.zoom = 1.0
        
        if not HAS_PILLOW:
            layout = QVBoxLayout()
            layout.addWidget(QLabel("错误: 未安装 Pillow 库。请先 pip install Pillow"))
            self.setLayout(layout)
            return

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)

        # 左侧：预览区域 (带阴影卡片效果)
        preview_container = QWidget()
        preview_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px dashed #ced4da;
                border-radius: 8px;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_container.setLayout(preview_layout)
        
        self.preview_label = QLabel("请打开图片")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: none; color: #adb5bd; font-size: 14px;")
        
        preview_layout.addStretch()
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignmentFlag.AlignCenter)
        preview_layout.addStretch()
        
        # 右侧：控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)
        control_panel.setLayout(control_layout)

        # 1. 打开按钮
        btn_open = QPushButton("打开图片 (PNG/JPG)")
        btn_open.setFixedHeight(36)
        btn_open.clicked.connect(self.load_image)
        control_layout.addWidget(btn_open)

        # 2. 形状
        control_layout.addWidget(QLabel("形状裁切:"))
        self.combo_shape = QComboBox()
        self.combo_shape.addItems(["圆角方形 (Rounded)", "正方形 (Square)", "圆形 (Circle)", "心形 (Heart)"])
        self.combo_shape.currentIndexChanged.connect(self.update_preview)
        control_layout.addWidget(self.combo_shape)

        # 3. 缩放
        control_layout.addWidget(QLabel("缩放与位置:"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(50)
        self.slider.setMaximum(200)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.on_slider_change)
        control_layout.addWidget(self.slider)

        # 4. 选项
        self.chk_trans = QCheckBox("保留透明背景")
        self.chk_trans.setChecked(True)
        self.chk_trans.setEnabled(False)
        control_layout.addWidget(self.chk_trans)

        control_layout.addStretch()

        # 5. 底部按钮
        btn_export = QPushButton("仅导出 ICO")
        btn_export.clicked.connect(self.export_ico)
        control_layout.addWidget(btn_export)

        btn_apply = QPushButton("使用此图标")
        btn_apply.setObjectName("SuccessBtn") 
        btn_apply.setFixedHeight(40)
        btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_apply.clicked.connect(self.apply_icon)
        
        # 按钮阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        btn_apply.setGraphicsEffect(shadow)
        
        control_layout.addWidget(btn_apply)

        main_layout.addWidget(preview_container, 6)
        main_layout.addWidget(control_panel, 4)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.img_path = path
            self.slider.setValue(100)
            self.update_preview()

    def on_slider_change(self):
        self.zoom = self.slider.value() / 100.0
        self.update_preview()

    def get_shape_code(self):
        idx = self.combo_shape.currentIndex()
        return ["rounded", "square", "circle", "heart"][idx]

    def update_preview(self):
        if not self.img_path: return
        pil_img = IconProcessor.create_shaped_icon(self.img_path, self.get_shape_code(), 256, self.zoom)
        if pil_img:
            self.current_pil = pil_img
            im_data = pil_img.convert("RGBA").tobytes("raw", "RGBA")
            qim = QImage(im_data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qim)
            self.preview_label.setPixmap(pix.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.preview_label.setText("")

    def export_ico(self):
        if not hasattr(self, 'current_pil'): return
        path, _ = QFileDialog.getSaveFileName(self, "保存图标", "icon.ico", "Icon Files (*.ico)")
        if path:
            try:
                self.current_pil.save(path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                QMessageBox.information(self, "成功", "图标导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def apply_icon(self):
        if not hasattr(self, 'current_pil'): 
            QMessageBox.warning(self, "提示", "请先加载图片")
            return
        try:
            d = self.default_save_dir if self.default_save_dir else os.getcwd()
            if not os.path.exists(d): os.makedirs(d)
            save_path = os.path.join(d, "icon.ico")
            self.current_pil.save(save_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            self.callback(save_path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

# ===========================
# 3. 主窗口
# ===========================
class PackerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Packer Pro")
        self.resize(920, 780)
        self.env_manager = EnvManager()
        self.current_icon = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.start_time = 0
        self.is_running = False

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25) # 增加外边距
        main_layout.setSpacing(15) # 增加模块间距
        central_widget.setLayout(main_layout)

        # 1. 入口文件
        grp_file = QGroupBox("入口文件")
        l_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setPlaceholderText("选择主程序 .py 文件")
        self.txt_file.setReadOnly(True)
        btn_file = QPushButton("浏览")
        btn_file.setFixedWidth(80)
        btn_file.clicked.connect(self.select_file)
        l_file.addWidget(self.txt_file)
        l_file.addWidget(btn_file)
        grp_file.setLayout(l_file)
        main_layout.addWidget(grp_file)

        # 2. 环境
        grp_env = QGroupBox("编译环境")
        l_env = QVBoxLayout()
        l_env.setSpacing(8)
        
        h_env_opt = QHBoxLayout()
        self.rb_auto = QRadioButton("自动检测 (venv/conda)")
        self.rb_auto.setChecked(True)
        self.rb_auto.toggled.connect(self.detect_env)
        self.rb_manual = QRadioButton("手动指定")
        self.rb_manual.toggled.connect(self.manual_env)
        h_env_opt.addWidget(self.rb_auto)
        h_env_opt.addWidget(self.rb_manual)
        h_env_opt.addStretch()
        l_env.addLayout(h_env_opt)
        
        self.lbl_env_status = QLabel(f"检测路径: {self.env_manager.python_path}")
        self.lbl_env_status.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-left: 2px;")
        l_env.addWidget(self.lbl_env_status)
        grp_env.setLayout(l_env)
        main_layout.addWidget(grp_env)

        # 3. 资源设置 (合并输出与图标)
        grp_res = QGroupBox("资源与输出")
        l_res = QVBoxLayout()
        l_res.setSpacing(12)
        
        # 输出行
        h_out = QHBoxLayout()
        self.txt_out = QLineEdit()
        self.txt_out.setPlaceholderText("输出目录 (默认 dist_output)")
        btn_out = QPushButton("选择目录")
        btn_out.setFixedWidth(80)
        btn_out.clicked.connect(self.select_out)
        h_out.addWidget(QLabel("输出位置:"))
        h_out.addWidget(self.txt_out)
        h_out.addWidget(btn_out)
        
        # 图标行
        h_icon = QHBoxLayout()
        self.txt_icon = QLineEdit()
        self.txt_icon.setPlaceholderText("应用图标 (可选)")
        btn_make = QPushButton("制作")
        btn_make.setFixedWidth(60)
        btn_make.clicked.connect(self.open_icon_maker)
        btn_sel = QPushButton("选择")
        btn_sel.setFixedWidth(60)
        btn_sel.clicked.connect(self.select_icon)
        
        h_icon.addWidget(QLabel("应用图标:"))
        h_icon.addWidget(self.txt_icon)
        h_icon.addWidget(btn_make)
        h_icon.addWidget(btn_sel)
        
        l_res.addLayout(h_out)
        l_res.addLayout(h_icon)
        grp_res.setLayout(l_res)
        main_layout.addWidget(grp_res)

        # 4. 引擎选项
        grp_tool = QGroupBox("构建选项")
        l_tool = QHBoxLayout()
        
        v_engine = QVBoxLayout()
        self.rb_nuitka = QRadioButton("Nuitka 编译器")
        self.rb_nuitka.setChecked(True)
        self.rb_pyinstaller = QRadioButton("PyInstaller 打包器")
        v_engine.addWidget(self.rb_nuitka)
        v_engine.addWidget(self.rb_pyinstaller)
        
        v_opts = QVBoxLayout()
        self.chk_noconsole = QCheckBox("隐藏控制台 (No Console)")
        self.chk_noconsole.setChecked(True)
        self.chk_upx = QCheckBox("UPX 压缩 (需 tools 支持)")
        self.chk_upx.setChecked(True)
        v_opts.addWidget(self.chk_noconsole)
        v_opts.addWidget(self.chk_upx)
        
        l_tool.addLayout(v_engine)
        l_tool.addStretch()
        l_tool.addLayout(v_opts)
        l_tool.addStretch()
        grp_tool.setLayout(l_tool)
        main_layout.addWidget(grp_tool)

        # 5. 操作区
        h_action = QHBoxLayout()
        h_action.setSpacing(20)
        
        self.lbl_timer = QLabel("00:00")
        self.lbl_timer.setObjectName("TimerLabel")
        self.lbl_timer.setVisible(False)
        
        self.btn_run = QPushButton("立即打包")
        self.btn_run.setObjectName("PrimaryBtn") # 样式 ID
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.setFixedHeight(48)
        self.btn_run.setMinimumWidth(180)
        self.btn_run.clicked.connect(self.start_process)
        
        # 给开始按钮加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(41, 128, 185, 80)) # 蓝色阴影
        shadow.setOffset(0, 4)
        self.btn_run.setGraphicsEffect(shadow)
        
        h_action.addStretch()
        h_action.addWidget(self.lbl_timer)
        h_action.addWidget(self.btn_run)
        main_layout.addLayout(h_action)

        # 6. 日志
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Ready...")
        main_layout.addWidget(self.txt_log)

    # --- 逻辑 ---
    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Python (*.py)")
        if f:
            self.txt_file.setText(f)
            if not self.txt_out.text():
                self.txt_out.setText(os.path.join(os.path.dirname(f), "dist_output"))
            if self.rb_auto.isChecked(): self.detect_env()

    def select_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择目录")
        if d: self.txt_out.setText(d)

    def select_icon(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择图标", "", "Icon (*.ico)")
        if f: self.txt_icon.setText(f)

    def open_icon_maker(self):
        if not HAS_PILLOW:
            QMessageBox.warning(self, "提示", "请先安装 Pillow")
            return
        out_dir = self.txt_out.text()
        if not out_dir: out_dir = os.getcwd()
        IconGeneratorDialog(self, self.on_icon_created, default_save_dir=out_dir).exec()

    def on_icon_created(self, path):
        self.txt_icon.setText(path)
        self.log(f"图标已就绪: {path}")

    def detect_env(self):
        if not self.rb_auto.isChecked(): return
        base = os.path.dirname(self.txt_file.text()) if self.txt_file.text() else os.getcwd()
        found = False
        for d in ["venv", ".venv", "env"]:
            p = os.path.join(base, d)
            if os.path.exists(p):
                exe = os.path.join(p, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(p, "bin", "python")
                if os.path.exists(exe):
                    self.env_manager.set_python_path(exe)
                    self.lbl_env_status.setText(f"自动检测: {exe}")
                    found = True
                    break
        if not found:
            self.env_manager.set_python_path(sys.executable)
            self.lbl_env_status.setText(f"全局环境: {sys.executable}")

    def manual_env(self):
        if not self.rb_manual.isChecked(): return
        f, _ = QFileDialog.getOpenFileName(self, "选择 python.exe", "", "Executable (*.exe)")
        if f:
            self.env_manager.set_python_path(f)
            self.lbl_env_status.setText(f"手动指定: {f}")
        else:
            self.rb_auto.setChecked(True)

    def update_timer(self):
        if self.is_running:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_timer.setText(f"{mins:02d}:{secs:02d}")

    def log(self, msg):
        self.txt_log.append(msg.strip())
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    def start_process(self):
        target = self.txt_file.text()
        out = self.txt_out.text()
        if not target: return QMessageBox.warning(self, "提示", "请选择 .py 文件")
        if not out: return QMessageBox.warning(self, "提示", "请选择输出目录")
        
        self.btn_run.setEnabled(False)
        self.btn_run.setText("正在构建...")
        self.txt_log.clear()
        
        self.start_time = time.time()
        self.is_running = True
        self.lbl_timer.setVisible(True)
        self.lbl_timer.setText("00:00")
        self.timer.start(1000)

        threading.Thread(target=self.run_logic, daemon=True).start()

    # 信号桥接
    worker_signals = WorkerSignals()
    def signal_log(self, text):
        QTimer.singleShot(0, lambda: self.append_log_slot(text))
    def append_log_slot(self, text):
        self.log(text)
    def process_finished_slot(self, success):
        self.timer.stop()
        self.is_running = False
        self.btn_run.setEnabled(True)
        self.btn_run.setText("立即打包")
        
        if success:
            self.log("\n>>> 构建成功 <<<")
            QMessageBox.information(self, "完成", "打包成功！")
            try: os.startfile(self.txt_out.text())
            except: pass
        else:
            self.log("\n>>> 构建失败 <<<")
            QMessageBox.critical(self, "错误", "打包失败，请查看日志")

    def run_logic(self):
        try:
            target = self.txt_file.text()
            out = self.txt_out.text()
            icon = self.txt_icon.text()
            nocon = self.chk_noconsole.isChecked()
            upx = self.chk_upx.isChecked()
            
            tool = PyInstallerTool(self.env_manager) if self.rb_pyinstaller.isChecked() else NuitkaTool(self.env_manager)
            
            if not tool.check_installed():
                self.signal_log(f"安装依赖 {tool.name}...")
                self.env_manager.install_package(tool.module_name, self.worker_signals.log)

            cmd, env, _ = tool.get_build_info(target, out, nocon, icon, upx)
            self.signal_log(f"执行引擎: {tool.name}\n")
            
            runner = ToolRunner(cmd, env)
            runner.signals.log.connect(self.append_log_slot)
            runner.signals.finished.connect(self.process_finished_slot)
            runner.run()
        except Exception as e:
            self.signal_log(f"Error: {e}")
            self.process_finished_slot(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    # 启用高分屏支持
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    w = PackerWindow()
    w.show()
    sys.exit(app.exec())