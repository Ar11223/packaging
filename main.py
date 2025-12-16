import sys
import os
import subprocess
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QRadioButton, 
                             QCheckBox, QTextEdit, QFileDialog, QComboBox, QSlider, 
                             QMessageBox, QDialog, QFrame, QButtonGroup, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QCursor, QIcon

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
    QMainWindow { background-color: #f0f2f5; }
    QWidget { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; color: #333; }

    /* 卡片容器 */
    QFrame#Card {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e1e4e8;
    }

    /* 标题 */
    QLabel#CardTitle {
        font-weight: bold;
        font-size: 14px;
        color: #2c3e50;
        padding-bottom: 5px;
    }

    /* 输入框 */
    QLineEdit {
        border: 1px solid #dcdfe6;
        border-radius: 6px;
        padding: 8px 10px;
        background-color: #f9faFc;
    }
    QLineEdit:focus {
        border: 1px solid #409eff;
        background-color: #fff;
    }

    /* 通用按钮 (浏览/选择) */
    QPushButton#GhostBtn {
        background-color: #ffffff;
        border: 1px solid #dcdfe6;
        border-radius: 6px;
        color: #606266;
        padding: 7px 12px;
        font-weight: 500;
    }
    QPushButton#GhostBtn:hover {
        background-color: #ecf5ff;
        border-color: #c6e2ff;
        color: #409eff;
    }

    /* 编译器选择器 */
    QRadioButton#CompilerBtn {
        background-color: #f4f6f8;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 10px 15px;
        color: #555;
        font-weight: bold;
        text-align: left;
    }
    QRadioButton#CompilerBtn::indicator { width: 0; height: 0; }
    QRadioButton#CompilerBtn:checked {
        background-color: #ecf5ff;
        border: 1px solid #409eff;
        color: #409eff;
    }
    QRadioButton#CompilerBtn:hover {
        border-color: #b3d8ff;
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
        border-bottom: 2px solid #409eff;
        font-weight: bold;
    }

    /* 立即打包大按钮 */
    QPushButton#PrimaryBtn {
        background-color: #2980b9; 
        border: none;
        border-radius: 8px;
        color: white;
        font-size: 16px;
        font-weight: bold;
        padding: 12px;
    }
    QPushButton#PrimaryBtn:hover { background-color: #3498db; }
    QPushButton#PrimaryBtn:pressed { background-color: #1f618d; }
    QPushButton#PrimaryBtn:disabled { background-color: #bdc3c7; }

    /* 成功按钮 */
    QPushButton#SuccessBtn {
        background-color: #00b894;
        border: none;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        padding: 8px 20px;
    }
    QPushButton#SuccessBtn:hover { background-color: #55efc4; }

    /* 滑动开关 (Toggle Switch) */
    QCheckBox#Toggle {
        spacing: 10px;
        color: #606266;
    }
    QCheckBox#Toggle::indicator {
        width: 36px;
        height: 20px;
        border-radius: 10px;
        background-color: #dcdfe6;
    }
    QCheckBox#Toggle::indicator:checked {
        background-color: #409eff;
        image: url(none); 
        border-left: 16px solid transparent;
    }

    /* 底部日志 */
    QTextEdit#LogArea {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: none;
        border-radius: 0 0 0 0;
        font-family: Consolas, "Courier New", monospace;
        font-size: 12px;
        padding: 12px;
    }
    
    /* 计时器 */
    QLabel#Timer {
        font-size: 24px;
        font-weight: 300;
        color: #0984e3;
        font-family: "Segoe UI Light";
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

# ===========================
# 图标制作弹窗
# ===========================
class IconDialog(QDialog):
    def __init__(self, parent, callback, default_dir):
        super().__init__(parent)
        self.setWindowTitle("图标工作台")
        self.setFixedSize(650, 400)
        self.callback = callback; self.default_dir = default_dir; self.img_path = None; self.zoom = 1.0
        self.setStyleSheet("background-color: white;")
        layout = QHBoxLayout(self)
        self.lbl_prev = QLabel("暂无图片"); self.lbl_prev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prev.setStyleSheet("background: #f8f9fa; border-radius: 8px; color: #999;")
        layout.addWidget(self.lbl_prev, 5)
        ctrl = QVBoxLayout()
        btn_open = QPushButton("📂 打开图片"); btn_open.clicked.connect(self.load); btn_open.setObjectName("GhostBtn")
        ctrl.addWidget(btn_open)
        ctrl.addWidget(QLabel("形状:"))
        self.cmb = QComboBox(); self.cmb.addItems(["圆角", "方", "圆", "心"]); self.cmb.currentIndexChanged.connect(self.refresh)
        ctrl.addWidget(self.cmb)
        ctrl.addWidget(QLabel("缩放:"))
        self.sld = QSlider(Qt.Orientation.Horizontal); self.sld.setRange(50,200); self.sld.setValue(100); self.sld.valueChanged.connect(self.slide)
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
        self.cur = IconProcessor.create_shaped_icon(self.img_path, map_s[self.cmb.currentIndex()], 256, self.zoom)
        if self.cur:
            d = self.cur.convert("RGBA").tobytes("raw", "RGBA")
            q = QImage(d, self.cur.size[0], self.cur.size[1], QImage.Format.Format_RGBA8888)
            self.lbl_prev.setPixmap(QPixmap.fromImage(q).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(12)

        # 1. 入口文件
        card_file = QFrame(objectName="Card")
        l_file = QVBoxLayout(card_file)
        l_file.setContentsMargins(15, 15, 15, 15)
        l_file.addWidget(QLabel("入口文件", objectName="CardTitle"))
        h_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setPlaceholderText("选择主程序 .py 文件")
        self.txt_file.setReadOnly(True)
        btn_file = QPushButton("📁", objectName="GhostBtn"); btn_file.setFixedSize(40, 36); btn_file.clicked.connect(self.sel_file)
        h_file.addWidget(self.txt_file); h_file.addWidget(btn_file)
        l_file.addLayout(h_file)
        layout.addWidget(card_file)

        # 2. 环境
        card_env = QFrame(objectName="Card")
        l_env = QVBoxLayout(card_env)
        l_env.setContentsMargins(15, 10, 15, 15)
        h_tab = QHBoxLayout()
        h_tab.setSpacing(0)
        self.rb_auto = QRadioButton("自动检测", objectName="TabBtn"); self.rb_auto.setChecked(True); self.rb_auto.toggled.connect(self.detect_env)
        self.rb_man = QRadioButton("手动指定", objectName="TabBtn"); self.rb_man.toggled.connect(self.man_env)
        h_tab.addWidget(self.rb_auto); h_tab.addWidget(self.rb_man); h_tab.addStretch()
        l_env.addLayout(h_tab)
        bg_path = QFrame()
        bg_path.setStyleSheet("background: #f8f9fa; border-radius: 6px; padding: 8px;")
        l_path = QHBoxLayout(bg_path); l_path.setContentsMargins(5, 0, 5, 0)
        self.lbl_env = QLabel(f"{self.env_mgr.python_path}"); self.lbl_env.setStyleSheet("color: #606266; font-family: Consolas; font-size: 12px;")
        l_path.addWidget(QLabel("🐍")); l_path.addWidget(self.lbl_env); l_path.addStretch()
        self.lbl_check = QLabel("✔"); self.lbl_check.setStyleSheet("color: #67c23a; font-weight: bold;")
        l_path.addWidget(self.lbl_check)
        l_env.addWidget(bg_path)
        layout.addWidget(card_env)

        # 3. 资源
        card_res = QFrame(objectName="Card")
        l_res = QVBoxLayout(card_res)
        l_res.setContentsMargins(15, 15, 15, 15)
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
        l_opt.setContentsMargins(15, 15, 15, 15)
        l_opt.addWidget(QLabel("构建选项", objectName="CardTitle"))
        h_opt_main = QHBoxLayout()
        v_compiler = QVBoxLayout()
        self.bg_comp = QButtonGroup()
        self.rb_nuitka = QRadioButton("Nuitka 编译器\n(高性能，推荐)", objectName="CompilerBtn"); self.rb_nuitka.setChecked(True)
        self.rb_pyi = QRadioButton("PyInstaller 打包器\n(兼容性好)", objectName="CompilerBtn")
        self.bg_comp.addButton(self.rb_nuitka); self.bg_comp.addButton(self.rb_pyi)
        v_compiler.addWidget(self.rb_nuitka); v_compiler.addWidget(self.rb_pyi)
        v_switches = QVBoxLayout()
        v_switches.setContentsMargins(20, 0, 0, 0)
        self.chk_nocon = QCheckBox("隐藏控制台 (No Console)", objectName="Toggle"); self.chk_nocon.setChecked(True)
        self.chk_upx = QCheckBox("UPX 压缩 (需 tools 支持)", objectName="Toggle"); self.chk_upx.setChecked(True)
        v_switches.addStretch(); v_switches.addWidget(self.chk_nocon); v_switches.addSpacing(12); v_switches.addWidget(self.chk_upx); v_switches.addStretch()
        h_opt_main.addLayout(v_compiler, 4); h_opt_main.addLayout(v_switches, 6)
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
            tgt = self.txt_file.text(); out = self.txt_out.text(); icon = self.txt_icon.text(); nocon = self.chk_nocon.isChecked(); upx = self.chk_upx.isChecked()
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
    
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())