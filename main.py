import sys
import os
# 获取真实的 EXE 所在目录，而不是临时解压目录
# --- 修改开始: 适配 PyInstaller 单文件全打包模式 ---
if getattr(sys, 'frozen', False):
    # 判断是否是 PyInstaller 的单文件解压模式
    if hasattr(sys, '_MEIPASS'):
        # 如果是单文件模式，资源会被解压到临时目录 sys._MEIPASS 中
        BASE_DIR = sys._MEIPASS
    else:
        # 如果是 Nuitka 或 PyInstaller 的文件夹模式
        BASE_DIR = os.path.dirname(sys.executable)
else:
    # 源码运行模式
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# --- 修改结束 ---
import subprocess
import threading
import time
import ast # 导入 ast 模块
import importlib.util
import pkgutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QRadioButton, 
                             QCheckBox, QTextEdit, QFileDialog, QComboBox, QSlider, 
                             QMessageBox, QDialog, QFrame, QButtonGroup, QGraphicsDropShadowEffect,
                             QListWidget, QListWidgetItem)
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
        border-radius: 8px;
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

def _get_silent_startupinfo():
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


class EnvManager:
    # 完整的Python标准库列表（Python 3.8+）
    STANDARD_LIBS = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect',
        'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd',
        'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall',
        'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy',
        'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses',
        'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest',
        'email', 'encodings', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp',
        'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc',
        'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip',
        'hashlib', 'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib',
        'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
        'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
        'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder',
        'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers',
        'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle',
        'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib',
        'posix', 'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
        'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're',
        'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
        'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
        'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
        'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
        'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
        'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
        'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
        'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing',
        'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings',
        'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
        'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib',
        '_thread', '_winapi', 'nt', 'ntpath', 'zoneinfo', 'graphlib', 'tomllib',
    }
    
    # 导入名到pip包名的映射
    PACKAGE_MAP = {
        "PIL": "Pillow",
        "cv2": "opencv-python",
        "yaml": "PyYAML",
        "sklearn": "scikit-learn",
        "skimage": "scikit-image",
        "bs4": "beautifulsoup4",
        "dateutil": "python-dateutil",
        "serial": "pyserial",
        "usb": "pyusb",
        "Crypto": "pycryptodome",
        "OpenSSL": "pyOpenSSL",
        "wx": "wxPython",
        "nuitka": "nuitka",
        "PyInstaller": "PyInstaller",
        "PyQt5": "PyQt5",
        "PyQt6": "PyQt6",
        "PySide2": "PySide2",
        "PySide6": "PySide6",
    }
    
    CHECK_TIMEOUT = 10  # 检查包的超时时间（秒）
    INSTALL_TIMEOUT = 300  # 安装包的超时时间（秒）
    
    def __init__(self):
        self.python_path = sys.executable
        self._cached_installed_packages = None
        
    def set_python_path(self, path):
        if os.path.exists(path):
            self.python_path = path
            self._cached_installed_packages = None
            return True
        return False

    def get_python_version(self):
        try:
            result = subprocess.run(
                [self.python_path, "--version"],
                capture_output=True, text=True, check=True,
                timeout=self.CHECK_TIMEOUT,
                startupinfo=_get_silent_startupinfo()
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "版本获取超时"
        except Exception:
            return "未知版本"

    def _get_installed_packages(self, signal=None):
        """获取已安装的包列表（使用pip list缓存）"""
        if self._cached_installed_packages is not None:
            return self._cached_installed_packages
        try:
            result = subprocess.run(
                [self.python_path, "-m", "pip", "list", "--format=freeze"],
                capture_output=True, text=True,
                timeout=self.CHECK_TIMEOUT,
                startupinfo=_get_silent_startupinfo()
            )
            if result.returncode == 0:
                packages = set()
                for line in result.stdout.strip().split('\n'):
                    if '==' in line:
                        packages.add(line.split('==')[0].lower())
                self._cached_installed_packages = packages
                return packages
        except subprocess.TimeoutExpired:
            if signal: signal.emit("警告: 获取已安装包列表超时\n")
        except Exception as e:
            if signal: signal.emit(f"警告: 获取已安装包列表失败: {e}\n")
        return set()

    def install_package(self, pkg, signal):
        """安装指定的包，带超时和进度反馈"""
        pip_pkg_name = self.PACKAGE_MAP.get(pkg, pkg)
        cmd = [self.python_path, "-m", "pip", "install", pip_pkg_name]
        signal.emit(f"安装依赖: {' '.join(cmd)}\n")
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                startupinfo=_get_silent_startupinfo()
            )
            start_time = time.time()
            while True:
                if time.time() - start_time > self.INSTALL_TIMEOUT:
                    process.kill()
                    signal.emit(f"安装依赖 {pkg} 超时（超过 {self.INSTALL_TIMEOUT} 秒）\n")
                    return False
                try:
                    line = process.stdout.readline()
                    if line:
                        signal.emit(line)
                    elif process.poll() is not None:
                        break
                except Exception:
                    break
            self._cached_installed_packages = None
            if process.returncode == 0:
                signal.emit(f"依赖 {pkg} 安装成功\n")
                return True
            else:
                signal.emit(f"安装依赖 {pkg} 失败，退出码: {process.returncode}\n")
                return False
        except Exception as e:
            signal.emit(f"安装依赖 {pkg} 时发生异常: {e}\n")
            return False

    def check_package_installed(self, pkg, signal=None):
        """检查包是否已安装，使用缓存和超时机制"""
        installed_packages = self._get_installed_packages(signal)
        pip_pkg_name = self.PACKAGE_MAP.get(pkg, pkg).lower()
        if pip_pkg_name in installed_packages or pkg.lower() in installed_packages:
            return True
        try:
            result = subprocess.run(
                [self.python_path, "-c", f"import {pkg}"],
                capture_output=True, timeout=self.CHECK_TIMEOUT,
                startupinfo=_get_silent_startupinfo()
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            if signal: signal.emit(f"警告: 检查包 {pkg} 是否安装超时\n")
            return False
        except Exception:
            return False

    def parse_dependencies(self, script_path, signal):
        """解析脚本的依赖，排除标准库"""
        dependencies = set()
        all_standard_libs = self.STANDARD_LIBS.copy()
        all_standard_libs.update(sys.builtin_module_names)
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=script_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name not in all_standard_libs:
                            dependencies.add(module_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name not in all_standard_libs:
                            dependencies.add(module_name)
        except SyntaxError as e:
            signal.emit(f"脚本语法错误，无法解析依赖: {e}\n")
        except Exception as e:
            signal.emit(f"解析依赖时发生错误: {e}\n")
        return sorted(list(dependencies))
    
    def clear_cache(self):
        """清除包缓存"""
        self._cached_installed_packages = None

class BaseTool:
    def __init__(self, env): self.env = env
    def check_installed(self):
        try: subprocess.check_call([self.env.python_path, "-c", f"import {self.module_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return True
        except: return False
    def find_upx(self):
        base = BASE_DIR; tools = os.path.join(base, "tools")
        if not os.path.exists(tools): return None
        for r, d, f in os.walk(tools):
            if "upx.exe" in f: return r
        return None

class PyInstallerTool(BaseTool):
    def __init__(self, env): self.env = env; self.name = "PyInstaller"; self.module_name = "PyInstaller"
    def get_cmd(self, target, out, nocon, icon, compress_mode):
        """
        compress_mode: 0=双层压缩, 1=仅内压缩, 2=仅UPX, 3=不压缩
        """
        if not os.path.exists(out): os.makedirs(out)
        cmd = [self.env.python_path, "-m", "PyInstaller", "-F", target, "--distpath", out, "--specpath", out, "--workpath", os.path.join(out, "build_temp")]
        if nocon: cmd.append("-w")
        if icon: cmd.extend(["--icon", icon])
        
        # 压缩模式处理
        if compress_mode == 0:  # 双层压缩：内压缩 + UPX
            u = self.find_upx()
            if u: cmd.extend(["--upx-dir", u])
            else: cmd.append("--noupx")
        elif compress_mode == 1:  # 仅内压缩：禁用UPX
            cmd.append("--noupx")
        elif compress_mode == 2:  # 仅UPX：PyInstaller内压缩无法完全禁用，但启用UPX
            u = self.find_upx()
            if u: cmd.extend(["--upx-dir", u])
            else: cmd.append("--noupx")
        else:  # 不压缩：禁用UPX
            cmd.append("--noupx")
        
        return cmd, None

class NuitkaTool(BaseTool):
    def __init__(self, env): self.env = env; self.name = "Nuitka"; self.module_name = "nuitka"
    def get_cmd(self, target, out, nocon, icon, compress_mode):
        """
        compress_mode: 0=双层压缩, 1=仅内压缩, 2=仅UPX, 3=不压缩
        """
        # 1. 定位 MinGW
        base = BASE_DIR
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
            "--include-package=PyQt6",
            "--enable-plugin=tk-inter",
            
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
        
        # 压缩模式处理
        if compress_mode == 0:  # 双层压缩：内压缩 + UPX
            u = self.find_upx()
            if u:
                cmd.append("--enable-plugin=upx")
                env["PATH"] = u + os.pathsep + env["PATH"]
            else:
                cmd.append("--disable-plugin=upx")
        elif compress_mode == 1:  # 仅内压缩：禁用UPX
            cmd.append("--disable-plugin=upx")
        elif compress_mode == 2:  # 仅UPX：禁用内压缩，启用UPX
            cmd.append("--onefile-no-compression")
            u = self.find_upx()
            if u:
                cmd.append("--enable-plugin=upx")
                env["PATH"] = u + os.pathsep + env["PATH"]
            else:
                cmd.append("--disable-plugin=upx")
        else:  # 不压缩：禁用内压缩和UPX
            cmd.append("--onefile-no-compression")
            cmd.append("--disable-plugin=upx")
            
        return cmd, env

class WorkerSignals(QObject): log = pyqtSignal(str); finished = pyqtSignal(bool)
class ToolRunner(QObject):
    def __init__(self, cmd, env): super().__init__(); self.cmd = cmd; self.env = env; self.signals = WorkerSignals()
    def run(self):
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, startupinfo=startupinfo, env=self.env)
            for l in p.stdout: self.signals.log.emit(l)
            p.wait()
            self.signals.finished.emit(p.returncode == 0)
        except Exception as e: self.signals.log.emit(str(e)); self.signals.finished.emit(False)


# ===========================
# 后台依赖检查工作线程
# ===========================
class DependencyCheckSignals(QObject):
    """依赖检查信号类"""
    log = pyqtSignal(str)           # 日志输出
    progress = pyqtSignal(str)      # 进度更新
    finished = pyqtSignal(list)     # 完成，返回缺失的依赖列表
    error = pyqtSignal(str)         # 错误信息


class DependencyCheckWorker(QObject):
    """后台依赖检查工作线程"""
    def __init__(self, env_mgr, script_path):
        super().__init__()
        self.env_mgr = env_mgr
        self.script_path = script_path
        self.signals = DependencyCheckSignals()
        self._is_cancelled = False
    
    def cancel(self):
        """取消检查"""
        self._is_cancelled = True
    
    def run(self):
        """执行依赖检查"""
        try:
            self.signals.log.emit("开始检测脚本依赖...\n")
            self.signals.progress.emit("正在解析脚本...")
            
            # 解析依赖
            dependencies = self.env_mgr.parse_dependencies(self.script_path, self.signals.log)
            
            if self._is_cancelled:
                self.signals.log.emit("依赖检查已取消\n")
                self.signals.finished.emit([])
                return
            
            if not dependencies:
                self.signals.log.emit("未检测到第三方依赖\n")
                self.signals.finished.emit([])
                return
            
            self.signals.log.emit(f"检测到 {len(dependencies)} 个第三方依赖: {', '.join(dependencies)}\n")
            
            # 检查每个依赖是否已安装
            missing_deps = []
            total = len(dependencies)
            for i, dep in enumerate(dependencies):
                if self._is_cancelled:
                    self.signals.log.emit("依赖检查已取消\n")
                    self.signals.finished.emit([])
                    return
                
                self.signals.progress.emit(f"检查依赖 ({i+1}/{total}): {dep}")
                self.signals.log.emit(f"检查依赖: {dep}...")
                
                if not self.env_mgr.check_package_installed(dep, self.signals.log):
                    missing_deps.append(dep)
                    self.signals.log.emit(f" 未安装\n")
                else:
                    self.signals.log.emit(f" 已安装\n")
            
            if missing_deps:
                self.signals.log.emit(f"\n缺失依赖: {', '.join(missing_deps)}\n")
            else:
                self.signals.log.emit("\n所有依赖均已安装\n")
            
            self.signals.finished.emit(missing_deps)
            
        except Exception as e:
            self.signals.error.emit(f"依赖检查时发生错误: {str(e)}")
            self.signals.finished.emit([])


class DependencyInstallWorker(QObject):
    """后台依赖安装工作线程"""
    def __init__(self, env_mgr, packages):
        super().__init__()
        self.env_mgr = env_mgr
        self.packages = packages
        self.signals = DependencyCheckSignals()
        self._is_cancelled = False
    
    def cancel(self):
        """取消安装"""
        self._is_cancelled = True
    
    def run(self):
        """执行依赖安装"""
        try:
            total = len(self.packages)
            success_count = 0
            failed_packages = []
            
            for i, pkg in enumerate(self.packages):
                if self._is_cancelled:
                    self.signals.log.emit("依赖安装已取消\n")
                    break
                
                self.signals.progress.emit(f"安装依赖 ({i+1}/{total}): {pkg}")
                
                if self.env_mgr.install_package(pkg, self.signals.log):
                    success_count += 1
                else:
                    failed_packages.append(pkg)
            
            if failed_packages:
                self.signals.log.emit(f"\n安装完成: {success_count}/{total} 成功, 失败: {', '.join(failed_packages)}\n")
                self.signals.finished.emit(failed_packages)
            else:
                self.signals.log.emit(f"\n所有 {total} 个依赖安装成功\n")
                self.signals.finished.emit([])
                
        except Exception as e:
            self.signals.error.emit(f"依赖安装时发生错误: {str(e)}")
            self.signals.finished.emit(self.packages)

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
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, w=50, h=28):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self._on = False
        self._margin = 2
        self._thumb_radius = (h - 2 * self._margin) // 2
        self._track_radius = h // 2
        self._w, self._h = w, h

        self._thumb_x = self._margin # 初始化 _thumb_x 属性

        

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
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
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
            os.makedirs(os.path.dirname(p), exist_ok=True) # 确保输出目录存在
            self.cur.save(p, format='ICO', sizes=[(256,256),(128,128),(48,48),(16,16)])
            self.callback(p); self.accept()

# ===========================
# 依赖选择弹窗
# ===========================
class DependencySelectionDialog(QDialog):
    def __init__(self, parent, missing_dependencies):
        super().__init__(parent)
        self.setWindowTitle("选择要安装的依赖")
        self.setFixedSize(400, 450)
        self.setModal(True) # 设置为模态对话框

        self.selected_dependencies = []

        layout = QVBoxLayout(self)

        # 提示信息
        info_label = QLabel("检测到以下缺失依赖，请选择要安装的项：")
        layout.addWidget(info_label)

        # 依赖列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 5px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 5px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #c0c0c0;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            QCheckBox::indicator:hover {
                border-color: #4a90e2;
            }
            """
        )
        for dep in missing_dependencies:
            item = QListWidgetItem(self.list_widget)
            checkbox = QCheckBox(dep)
            checkbox.setChecked(True) # 默认全选
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, checkbox)
        layout.addWidget(self.list_widget)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("GhostBtn")
        self.select_all_btn.clicked.connect(lambda: self.set_all_checkboxes(True))
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.setObjectName("GhostBtn")
        self.deselect_all_btn.clicked.connect(lambda: self.set_all_checkboxes(False))
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("GhostBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.install_btn = QPushButton("安装选中依赖")
        self.install_btn.setObjectName("PrimaryBtn")
        self.install_btn.clicked.connect(self.accept_selection)
        btn_layout.addWidget(self.install_btn)
        
        layout.addLayout(btn_layout)

    def set_all_checkboxes(self, checked):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(checked)

    def accept_selection(self):
        self.selected_dependencies.clear()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                self.selected_dependencies.append(checkbox.text())
        self.accept()

# ===========================
# 主界面
# ===========================
class MainWindow(QMainWindow):
    sig_log_bridge = pyqtSignal(str) # 将信号定义为类属性
    sig_done = pyqtSignal(bool) # 定义结束信号
    sig_dep_check_done = pyqtSignal(list)  # 依赖检查完成信号
    sig_dep_install_done = pyqtSignal(list)  # 依赖安装完成信号

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Packer Pro")
        self.resize(800, 580)
        self.env_mgr = EnvManager()
        
        # 后台工作线程变量
        self._dep_check_worker = None
        self._dep_check_thread = None
        self._dep_install_worker = None
        self._dep_install_thread = None
        self._pending_start_after_install = False  # 是否在安装完成后启动打包
        
        # 自动加载 name.png 图标
        icon_path = os.path.join(BASE_DIR, "name.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.start_ts = 0
        self.sig_log_bridge.connect(self.append_log) # 连接信号到日志追加方法
        self.sig_done.connect(self.done) # 连接信号到处理函数
        self.sig_dep_check_done.connect(self._on_dep_check_done)  # 连接依赖检查完成信号
        self.sig_dep_install_done.connect(self._on_dep_install_done)  # 连接依赖安装完成信号
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_h_layout = QHBoxLayout() # 主水平布局
        main_h_layout.setContentsMargins(20, 20, 20, 20)
        main_h_layout.setSpacing(12)

        left_v_layout = QVBoxLayout() # 左侧垂直布局
        left_v_layout.setContentsMargins(0, 0, 0, 0)
        left_v_layout.setSpacing(12)

        right_v_layout = QVBoxLayout() # 右侧垂直布局
        right_v_layout.setContentsMargins(0, 0, 0, 0)
        right_v_layout.setSpacing(12)
        
        main_h_layout.addLayout(left_v_layout, 1) # 左侧占据1份空间
        main_h_layout.addLayout(right_v_layout, 1) # 右侧占据1份空间

        bottom_v_layout = QVBoxLayout() # 底部垂直布局 (用于操作区和日志)
        bottom_v_layout.setContentsMargins(20, 0, 20, 20) # 调整底部边距
        bottom_v_layout.setSpacing(12)

        layout = QVBoxLayout(central) # 整体垂直布局
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(main_h_layout, 1) # 主水平布局占据剩余空间
        layout.addLayout(bottom_v_layout, 0) # 底部布局固定高度

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
        left_v_layout.addWidget(card_file)

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

        initial_python_version = self.env_mgr.get_python_version()
        self.lbl_env = QLabel(f"{self.env_mgr.python_path} ({initial_python_version})")
        self.lbl_env.setStyleSheet("color: #606266; font-family: Consolas; font-size: 12px;")
        
        l_path.addWidget(self.lbl_env)
        l_path.addStretch()

        l_env.addWidget(bg_path) # 添加路径框到环境卡片布局中 (确保只添加一次)
        left_v_layout.addWidget(card_env)

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
        left_v_layout.addWidget(card_res)

        # 4. 选项
        card_opt = QFrame(objectName="Card")
        l_opt = QVBoxLayout(card_opt)
        l_opt.setContentsMargins(10, 10, 10, 10)
        l_opt.addWidget(QLabel("构建选项", objectName="CardTitle"))
        
        # 依赖管理区域
        card_dep = QFrame(objectName="Card")
        l_dep = QVBoxLayout(card_dep)
        l_dep.setContentsMargins(10, 10, 10, 10)
        l_dep.addWidget(QLabel("依赖管理", objectName="CardTitle"))

        h_dep_check = QHBoxLayout()
        self.chk_dep_check = ToggleSwitch(self, w=38, h=22); self.chk_dep_check.set_on(False)
        self.lbl_dep_check = QLabel("自动检测并提示安装缺失依赖")
        h_dep_check.addWidget(self.chk_dep_check); h_dep_check.addWidget(self.lbl_dep_check); h_dep_check.addStretch()
        l_dep.addLayout(h_dep_check)

        btn_check_deps = QPushButton("手动检查并安装依赖", objectName="GhostBtn")
        btn_check_deps.clicked.connect(self.check_and_install_dependencies)
        l_dep.addWidget(btn_check_deps)
        l_opt.addWidget(card_dep) # 将新的依赖管理卡片添加到构建选项布局中

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

        # 右侧布局: Nuitka 和 压缩方式选择
        v_right_column = QVBoxLayout()
        v_right_column.addWidget(self.rb_nuitka)

        # 压缩方式选择
        h_compress = QHBoxLayout()
        lbl_compress = QLabel("压缩方式:")
        self.cmb_compress = QComboBox()
        self.cmb_compress.addItems(["双层压缩", "仅内压缩", "仅UPX", "不压缩"])
        self.cmb_compress.setCurrentIndex(0)  # 默认双层压缩
        self.cmb_compress.setToolTip(
            "双层压缩：内压缩 + UPX压缩（体积最小）\n"
            "仅内压缩：仅使用打包工具自带压缩\n"
            "仅UPX：仅使用UPX压缩\n"
            "不压缩：不进行任何压缩（体积最大）"
        )
        h_compress.addWidget(lbl_compress)
        h_compress.addWidget(self.cmb_compress)
        h_compress.addStretch()
        v_right_column.addLayout(h_compress)
        v_right_column.addStretch() # 确保右侧内容向上对齐

        h_opt_main.addLayout(v_left_column)
        h_opt_main.addLayout(v_right_column)
        l_opt.addLayout(h_opt_main)
        right_v_layout.addWidget(card_opt)


        # 5. 操作区 (已拆分)

        # 计时器单独放在底部布局的顶部
        h_timer_layout = QHBoxLayout()
        h_timer_layout.addStretch()
        self.lbl_timer = QLabel("00:00", objectName="Timer"); self.lbl_timer.setVisible(False)
        h_timer_layout.addWidget(self.lbl_timer)
        h_timer_layout.addStretch()
        bottom_v_layout.addLayout(h_timer_layout)

        # 立即打包按钮移动到右侧布局的底部
        self.btn_run = QPushButton("立即打包", objectName="PrimaryBtn")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(15); shadow.setColor(QColor(41, 128, 185, 60)); shadow.setOffset(0, 4)
        self.btn_run.setGraphicsEffect(shadow)
        self.btn_run.clicked.connect(self.start)
        right_v_layout.addStretch() # 在按钮上方添加一个拉伸器，使其居底
        right_v_layout.addWidget(self.btn_run)

        # 6. 日志
        self.txt_log = QTextEdit(objectName="LogArea"); self.txt_log.setPlaceholderText("Ready..."); self.txt_log.setFixedHeight(120); self.txt_log.setReadOnly(True)
        bottom_v_layout.addWidget(self.txt_log)

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
                if os.path.exists(exe):
                    self.env_mgr.set_python_path(exe)
                    python_version = self.env_mgr.get_python_version()
                    self.lbl_env.setText(f"自动检测: {exe} ({python_version})")
                    found=True; break
        if not found:
            self.env_mgr.set_python_path(sys.executable)
            python_version = self.env_mgr.get_python_version()
            self.lbl_env.setText(f"系统全局: {sys.executable} ({python_version})")
    def man_env(self):
        if not self.rb_man.isChecked(): return
        f, _ = QFileDialog.getOpenFileName(self, "Python Exe", "", "*.exe")
        if f:
            self.env_mgr.set_python_path(f)
            python_version = self.env_mgr.get_python_version()
            self.lbl_env.setText(f"手动: {f} ({python_version})")
        else: self.rb_auto.setChecked(True)
    def tick(self):
        s = int(time.time() - self.start_ts)
        self.lbl_timer.setText(f"{s//60:02d}:{s%60:02d}")
    def append_log(self, t): self.txt_log.append(t.strip()); self.txt_log.verticalScrollBar().setValue(100000)
    # sig_log_bridge = pyqtSignal(str) # 移除此处，已在 __init__ 中定义
    def check_and_install_dependencies(self):
        """手动检查并安装依赖（使用后台线程）"""
        script_path = self.txt_file.text()
        if not script_path or not os.path.exists(script_path):
            QMessageBox.warning(self, "提示", "请先选择一个有效的入口文件。")
            return
        
        # 禁用按钮防止重复点击
        self.btn_run.setEnabled(False)
        self.btn_run.setText("检查依赖中...")
        self._pending_start_after_install = False
        
        # 启动后台依赖检查
        self._start_dep_check(script_path)
    
    def _start_dep_check(self, script_path):
        """启动后台依赖检查线程"""
        # 清除包缓存以确保获取最新状态
        self.env_mgr.clear_cache()
        
        # 创建工作线程
        self._dep_check_worker = DependencyCheckWorker(self.env_mgr, script_path)
        self._dep_check_thread = threading.Thread(target=self._run_dep_check, daemon=True)
        
        # 连接信号
        self._dep_check_worker.signals.log.connect(self.sig_log_bridge.emit)
        self._dep_check_worker.signals.progress.connect(lambda msg: self.btn_run.setText(msg))
        self._dep_check_worker.signals.finished.connect(self.sig_dep_check_done.emit)
        self._dep_check_worker.signals.error.connect(self.sig_log_bridge.emit)
        
        # 启动线程
        self._dep_check_thread.start()
    
    def _run_dep_check(self):
        """在后台线程中运行依赖检查"""
        if self._dep_check_worker:
            self._dep_check_worker.run()
    
    def _on_dep_check_done(self, missing_deps):
        """依赖检查完成回调"""
        self.btn_run.setText("立即打包")
        
        if missing_deps:
            # 显示依赖选择对话框
            dialog = DependencySelectionDialog(self, missing_deps)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_to_install = dialog.selected_dependencies
                if selected_to_install:
                    # 启动后台安装
                    self._start_dep_install(selected_to_install)
                    return  # 等待安装完成
                else:
                    self.sig_log_bridge.emit("没有选择任何依赖进行安装。\n")
                    if self._pending_start_after_install:
                        # 继续打包
                        self._do_start_packing()
                    else:
                        self.btn_run.setEnabled(True)
            else:
                self.sig_log_bridge.emit("用户取消了依赖安装。\n")
                if self._pending_start_after_install:
                    QMessageBox.warning(self, "提示", "您选择了不安装缺失依赖，打包可能会失败。")
                    self._do_start_packing()
                else:
                    self.btn_run.setEnabled(True)
        else:
            self.sig_log_bridge.emit("所有依赖均已安装。\n")
            if self._pending_start_after_install:
                # 继续打包
                self._do_start_packing()
            else:
                QMessageBox.information(self, "成功", "所有依赖均已安装。")
                self.btn_run.setEnabled(True)
    
    def _start_dep_install(self, packages):
        """启动后台依赖安装线程"""
        self.btn_run.setText("安装依赖中...")
        
        # 创建工作线程
        self._dep_install_worker = DependencyInstallWorker(self.env_mgr, packages)
        self._dep_install_thread = threading.Thread(target=self._run_dep_install, daemon=True)
        
        # 连接信号
        self._dep_install_worker.signals.log.connect(self.sig_log_bridge.emit)
        self._dep_install_worker.signals.progress.connect(lambda msg: self.btn_run.setText(msg))
        self._dep_install_worker.signals.finished.connect(self.sig_dep_install_done.emit)
        self._dep_install_worker.signals.error.connect(self.sig_log_bridge.emit)
        
        # 启动线程
        self._dep_install_thread.start()
    
    def _run_dep_install(self):
        """在后台线程中运行依赖安装"""
        if self._dep_install_worker:
            self._dep_install_worker.run()
    
    def _on_dep_install_done(self, failed_packages):
        """依赖安装完成回调"""
        self.btn_run.setText("立即打包")
        
        if failed_packages:
            self.sig_log_bridge.emit(f"以下依赖安装失败: {', '.join(failed_packages)}\n")
            if self._pending_start_after_install:
                QMessageBox.critical(self, "错误", "部分依赖安装失败，打包中止。请检查日志。")
                self.btn_run.setEnabled(True)
            else:
                QMessageBox.critical(self, "失败", "部分依赖安装失败，请检查日志。")
                self.btn_run.setEnabled(True)
        else:
            self.sig_log_bridge.emit("所有选中依赖安装完成。\n")
            if self._pending_start_after_install:
                # 继续打包
                self._do_start_packing()
            else:
                QMessageBox.information(self, "成功", "所有选中依赖安装完成！")
                self.btn_run.setEnabled(True)


    def start(self):
        """开始打包流程"""
        tgt = self.txt_file.text()
        if not tgt:
            return QMessageBox.warning(self, "!", "请选择入口文件")

        # 在开始打包前检查依赖
        if self.chk_dep_check._on:
            self.sig_log_bridge.emit("自动依赖检测已启用，开始检测...\n")
            self.btn_run.setEnabled(False)
            self.btn_run.setText("检查依赖中...")
            self._pending_start_after_install = True  # 标记在检查/安装完成后启动打包
            self._start_dep_check(tgt)
        else:
            # 直接开始打包
            self._do_start_packing()
    
    def _do_start_packing(self):
        """实际执行打包操作"""
        self.btn_run.setEnabled(False)
        self.btn_run.setText("打包构建中...")
        self.txt_log.clear()
        self.start_ts = time.time()
        self.lbl_timer.setVisible(True)
        self.timer.start(1000)
        self._pending_start_after_install = False
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        # self.sig_log_bridge.connect(self.append_log) # 信号连接已在 __init__ 中完成，无需重复
        try:
            tgt = self.txt_file.text(); out = self.txt_out.text(); icon = self.txt_icon.text(); nocon = self.chk_nocon._on
            compress_mode = self.cmb_compress.currentIndex()  # 0=双层压缩, 1=仅内压缩, 2=仅UPX, 3=不压缩
            tool = PyInstallerTool(self.env_mgr) if self.rb_pyi.isChecked() else NuitkaTool(self.env_mgr)
            
            # 仅检查打包工具，不自动安装，因为用户已经有依赖管理选项
            if not tool.check_installed():
                self.sig_log_bridge.emit(f"打包工具 {tool.name} 未安装。请通过依赖管理功能手动安装。\n")
                # 这里不自动安装，而是提示用户去手动安装，避免重复逻辑和用户体验冲突
                self.sig_done.emit(False)
                return

            cmd, env = tool.get_cmd(tgt, out, nocon, icon, compress_mode)
            self.sig_log_bridge.emit(f"Run: {' '.join(cmd)}\n")
            runner = ToolRunner(cmd, env); runner.signals.log.connect(self.sig_log_bridge.emit); runner.signals.finished.connect(self.sig_done.emit); runner.run()
        except Exception as e: self.sig_log_bridge.emit(str(e)); self.sig_done.emit(False)
    def done(self, s):
        self.timer.stop(); self.btn_run.setEnabled(True); self.btn_run.setText("立即打包")
        if s: 
            QMessageBox.information(self, "OK", "Success!"); 
            try: os.startfile(self.txt_out.text())
            except Exception as e: self.sig_log_bridge.emit(f"无法打开输出目录: {e}\n")
        else: QMessageBox.critical(self, "Err", "Failed.")
        # try: self.sig_log_bridge.disconnect() # 信号是永久连接，无需断开
        # except: pass

if __name__ == "__main__":
    # 使用类名直接调用静态/类方法，不需要实例
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    # 之后再创建实例
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    default_font = QFont("Segoe UI", 9)
    app.setFont(default_font)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())