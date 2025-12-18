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
import shutil
import glob
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
    /* 全局设定 - 简约大气的商务风格 */
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #f5f7fa, stop:1 #e8ecf1);
    }
    QWidget {
        font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
        font-size: 13px;
        color: #2c3e50;
    }

    /* 卡片容器 - 精致阴影与圆角 */
    QFrame#Card {
        background-color: #ffffff;
        border-radius: 12px;
        border: none;
    }

    /* 标题 - 更专业的排版 */
    QLabel#CardTitle {
        font-weight: 600;
        font-size: 15px;
        color: #1a2332;
        padding-bottom: 8px;
        letter-spacing: 0.5px;
    }

    /* 输入框 - 极简商务风 */
    QLineEdit {
        border: 1px solid #d8dde6;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #f9fafb;
        color: #2c3e50;
        selection-background-color: #4a90e2;
    }
    QLineEdit:focus {
        border: 2px solid #4a90e2;
        background-color: #ffffff;
        padding: 9px 13px;
    }
    QLineEdit:read-only {
        background-color: #f5f7fa;
        color: #7f8c8d;
    }

    /* 通用按钮 - 现代扁平化 */
    QPushButton#GhostBtn {
        background-color: transparent;
        border: 2px solid #5d9cec;
        border-radius: 8px;
        color: #5d9cec;
        padding: 9px 20px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    QPushButton#GhostBtn:hover {
        background-color: #5d9cec;
        border-color: #5d9cec;
        color: #ffffff;
    }
    QPushButton#GhostBtn:pressed {
        background-color: #4a8dd9;
        border-color: #4a8dd9;
    }

    /* 编译器选择器 - 卡片式设计 */
    QRadioButton#CompilerBtn {
        background-color: #f8f9fb;
        border: 2px solid #e4e7ed;
        border-radius: 10px;
        padding: 14px 18px;
        color: #606266;
        font-weight: 600;
        text-align: left;
    }
    QRadioButton#CompilerBtn::indicator { width: 0; height: 0; }
    QRadioButton#CompilerBtn:checked {
        background-color: #ecf5ff;
        border: 2px solid #5d9cec;
        color: #5d9cec;
    }
    QRadioButton#CompilerBtn:hover {
        border-color: #a0cfff;
        background-color: #f4f9ff;
    }

    /* 分段控制器 - 精致的商务风格 */
    QFrame#SegmentedControlFrame {
        border: 2px solid #e4e7ed;
        border-radius: 10px;
        background-color: #f5f7fa;
        padding: 2px;
    }

    QRadioButton#SegmentedControlBtn {
        background-color: transparent;
        border: none;
        padding: 10px 24px;
        color: #606266;
        font-weight: 500;
        min-width: 100px;
    }
    QRadioButton#SegmentedControlBtn::indicator { width: 0; height: 0; }
    QRadioButton#SegmentedControlBtn:hover {
        color: #4a90e2;
    }
    QRadioButton#SegmentedControlBtn:checked {
        background-color: #5d9cec;
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }

    /* 立即打包大按钮 - 高级渐变 */
    QPushButton#PrimaryBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #5d9cec, stop:1 #4fc3f7);
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 17px;
        font-weight: 600;
        padding: 16px;
        letter-spacing: 1px;
    }
    QPushButton#PrimaryBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #6daef5, stop:1 #5fd4ff);
    }
    QPushButton#PrimaryBtn:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #4a8dd9, stop:1 #3eb3e5);
    }
    QPushButton#PrimaryBtn:disabled {
        background: #d5dce6;
        color: #b0b8c1;
    }

    /* 成功按钮 */
    QPushButton#SuccessBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #52c41a, stop:1 #73d13d);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 10px 24px;
        letter-spacing: 0.5px;
    }
    QPushButton#SuccessBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #6dd42a, stop:1 #8ee44d);
    }
    QPushButton#SuccessBtn:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #42b40a, stop:1 #63c42d);
    }

    /* 取消/危险按钮 */
    QPushButton#DangerBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #ed5565, stop:1 #da4453);
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 17px;
        font-weight: 600;
        padding: 16px;
        letter-spacing: 1px;
    }
    QPushButton#DangerBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #fc6575, stop:1 #ea5463);
    }
    QPushButton#DangerBtn:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #dc4555, stop:1 #ca3443);
    }

    /* 底部日志 - 专业终端风格 */
    QTextEdit#LogArea {
        background-color: #2c3e50;
        color: #ecf0f1;
        border: none;
        border-radius: 10px;
        font-family: "Consolas", "Monaco", "Courier New", monospace;
        font-size: 12px;
        padding: 16px;
    }
    
    /* 计时器 - 优雅细腻 */
    QLabel#Timer {
        font-size: 28px;
        font-weight: 300;
        color: #5d9cec;
        font-family: "Segoe UI Light", "Microsoft YaHei UI Light";
        letter-spacing: 2px;
    }
    
    /* 下拉选择框 - 现代设计 */
    QComboBox {
        border: 1px solid #d8dde6;
        border-radius: 8px;
        padding: 10px 14px;
        background-color: #f9fafb;
        selection-background-color: #e8f4fd;
        color: #2c3e50;
    }
    QComboBox:focus {
        border: 2px solid #5d9cec;
        padding: 9px 13px;
        background-color: #ffffff;
    }
    QComboBox::drop-down {
        border: none;
        background-color: transparent;
        width: 20px;
    }
    QComboBox::down-arrow {
        image: url(none);
    }
    QComboBox QAbstractItemView {
        border: 1px solid #d8dde6;
        border-radius: 8px;
        background-color: #ffffff;
        selection-background-color: #e8f4fd;
        selection-color: #2c3e50;
        padding: 4px;
    }

    /* 滑块 - 精致设计 */
    QSlider::groove:horizontal {
        height: 4px;
        background: #e4e7ed;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #5d9cec;
        width: 18px;
        height: 18px;
        border-radius: 9px;
        margin: -7px 0;
        border: 2px solid #ffffff;
    }
    QSlider::handle:horizontal:hover {
        background: #4fc3f7;
        width: 20px;
        height: 20px;
        margin: -8px 0;
    }
    QSlider::add-page:horizontal {
        background: #d5dce6;
        border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        background: #5d9cec;
        border-radius: 2px;
    }
"""

MINGW_DIR_NAME = "mingw64"

# ===========================
# 编译器后端检测
# ===========================
def detect_msvc():
    """检测系统是否安装了 MSVC (Visual Studio)"""
    try:
        # 方法1: 检查 vswhere 工具
        vswhere_paths = [
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
            r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe",
        ]
        for vswhere in vswhere_paths:
            if os.path.exists(vswhere):
                result = subprocess.run(
                    [vswhere, "-latest", "-property", "installationPath"],
                    capture_output=True, text=True, timeout=10,
                    startupinfo=_get_silent_startupinfo()
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
        
        # 方法2: 检查环境变量
        if os.environ.get("VCINSTALLDIR") or os.environ.get("VS140COMNTOOLS"):
            return True
        
        # 方法3: 尝试运行 cl.exe
        result = subprocess.run(
            ["where", "cl.exe"],
            capture_output=True, text=True, timeout=5,
            startupinfo=_get_silent_startupinfo()
        )
        if result.returncode == 0:
            return True
            
    except Exception:
        pass
    return False

def detect_mingw():
    """检测系统是否安装了 MinGW"""
    try:
        # 方法1: 检查内置的 MinGW
        base = BASE_DIR
        mingw_paths = [
            os.path.join(base, "tools", MINGW_DIR_NAME, "mingw64", "bin", "gcc.exe"),
            os.path.join(base, "tools", MINGW_DIR_NAME, "bin", "gcc.exe"),
        ]
        for p in mingw_paths:
            if os.path.exists(p):
                return "builtin", os.path.dirname(p)
        
        # 方法2: 检查系统 PATH 中的 MinGW
        result = subprocess.run(
            ["where", "gcc.exe"],
            capture_output=True, text=True, timeout=5,
            startupinfo=_get_silent_startupinfo()
        )
        if result.returncode == 0:
            gcc_path = result.stdout.strip().split('\n')[0]
            return "system", os.path.dirname(gcc_path)
            
    except Exception:
        pass
    return None, None

def get_available_backends():
    """获取可用的编译后端列表"""
    backends = ["自动选择"]
    
    has_msvc = detect_msvc()
    mingw_type, mingw_path = detect_mingw()
    
    if has_msvc:
        backends.append("MSVC (Visual Studio)")
    if mingw_type:
        if mingw_type == "builtin":
            backends.append("MinGW64 (内置)")
        else:
            backends.append("MinGW64 (系统)")
    
    # 总是添加这两个选项，让用户可以强制选择（即使需要下载）
    if "MSVC (Visual Studio)" not in backends:
        backends.append("MSVC (需要安装)")
    if "MinGW64 (内置)" not in backends and "MinGW64 (系统)" not in backends:
        backends.append("MinGW64 (需下载)")
    
    return backends, has_msvc, (mingw_type, mingw_path)

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

    # 清华大学 PyPI 镜像源
    TSINGHUA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"
    
    def install_package(self, pkg, signal):
        """安装指定的包，带超时和进度反馈，使用清华镜像源加速"""
        pip_pkg_name = self.PACKAGE_MAP.get(pkg, pkg)
        cmd = [self.python_path, "-m", "pip", "install", pip_pkg_name,
               "-i", self.TSINGHUA_MIRROR, "--trusted-host", "pypi.tuna.tsinghua.edu.cn"]
        signal.emit(f"安装依赖 (使用清华源): {' '.join(cmd)}\n")
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
    # GUI 框架检测映射
    # 注意：PySide6 对 Nuitka 的支持比 PyQt6 更好，建议优先使用 PySide6
    GUI_FRAMEWORKS = {
        'PyQt6': {'plugin': 'pyqt6', 'qt_plugins': 'sensible,styles,platforms', 'package': 'PyQt6', 'warning': 'PyQt6 在 Nuitka 中的支持不完美（如 Qt 线程问题），建议改用 PySide6'},
        'PyQt5': {'plugin': 'pyqt5', 'qt_plugins': 'sensible,styles,platforms', 'package': 'PyQt5'},
        'PySide6': {'plugin': 'pyside6', 'qt_plugins': 'sensible,styles,platforms', 'package': 'PySide6', 'preferred': True},
        'PySide2': {'plugin': 'pyside2', 'qt_plugins': 'sensible,styles,platforms', 'package': 'PySide2'},
        'tkinter': {'plugin': 'tk-inter', 'package': 'tkinter'},
        'wx': {'plugin': 'wx', 'package': 'wx'},
    }
    
    def __init__(self, env, backend_choice=0, parallel_jobs=None):
        self.env = env
        self.name = "Nuitka"
        self.module_name = "nuitka"
        self.backend_choice = backend_choice  # 0=自动, 1=MSVC, 2=MinGW
        self.parallel_jobs = parallel_jobs  # 并行编译任务数
    
    def set_backend(self, choice):
        """设置编译后端选择"""
        self.backend_choice = choice
    
    def _get_cpu_count(self):
        """获取 CPU 核心数"""
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except Exception:
            return 4  # 默认 4 核
    
    def _detect_gui_frameworks(self, target, signal=None):
        """检测目标脚本使用的 GUI 框架"""
        detected = []
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=target)
            
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            for framework in self.GUI_FRAMEWORKS.keys():
                if framework in imports:
                    detected.append(framework)
                    # 如果检测到框架有警告信息，输出到日志
                    config = self.GUI_FRAMEWORKS[framework]
                    if signal and 'warning' in config:
                        signal.emit(f"⚠️  {config['warning']}\n")
        except Exception:
            pass
        return detected
    
    def get_cmd(self, target, out, nocon, icon, compress_mode):
        """
        compress_mode: 0=双层压缩, 1=仅内压缩, 2=仅UPX, 3=不压缩
        """
        env = os.environ.copy()
        
        # 1. 根据用户选择确定编译后端
        use_msvc = False
        use_mingw = False
        mingw_path = None
        
        if self.backend_choice == 0:  # 自动选择
            # 优先使用 MSVC（如果已安装），其次使用 MinGW
            if detect_msvc():
                use_msvc = True
            else:
                mingw_type, mingw_path = detect_mingw()
                if mingw_type:
                    use_mingw = True
                else:
                    # 都没有，让 Nuitka 自动处理（可能会下载）
                    use_mingw = True  # 默认使用 MinGW
        elif self.backend_choice == 1:  # MSVC
            use_msvc = True
        else:  # MinGW
            use_mingw = True
            _, mingw_path = detect_mingw()
        
        # 2. 如果使用 MinGW 且有路径，注入环境变量
        if use_mingw and mingw_path and os.path.exists(mingw_path):
            env["PATH"] = mingw_path + os.pathsep + env["PATH"]
            
        # 3. 准备输出
        if not os.path.exists(out): os.makedirs(out)
        
        # 4. 计算并行编译任务数
        jobs = self.parallel_jobs if self.parallel_jobs else self._get_cpu_count()
        
        # 5. 自动检测 GUI 框架（传入 signal 以便输出警告）
        detected_guis = self._detect_gui_frameworks(target)
        
        # 6. 构建命令
        cmd = [
            self.env.python_path,
            "-m", "nuitka",
            "--standalone",
            "--onefile",
            
            # --- 性能优化：并行编译 ---
            f"--jobs={jobs}",
            
            # --- 排除不需要的测试模块以减小体积和加快打包速度 ---
            "--nofollow-import-to=pytest",
            "--nofollow-import-to=unittest",
            "--nofollow-import-to=_pytest",
            "--nofollow-import-to=hypothesis",
            
            "--assume-yes-for-downloads",
            "--remove-output",
            f"--output-dir={out}",
            target
        ]
        
        # 7. 根据检测到的 GUI 框架动态添加插件
        for gui in detected_guis:
            if gui in self.GUI_FRAMEWORKS:
                config = self.GUI_FRAMEWORKS[gui]
                plugin_arg = f"--enable-plugin={config['plugin']}"
                if plugin_arg not in cmd:
                    cmd.insert(cmd.index("--assume-yes-for-downloads"), plugin_arg)
                
                # Qt 框架需要额外的插件配置
                if 'qt_plugins' in config:
                    qt_arg = f"--include-qt-plugins={config['qt_plugins']}"
                    if qt_arg not in cmd:
                        cmd.insert(cmd.index("--assume-yes-for-downloads"), qt_arg)
                    pkg_arg = f"--include-package={config['package']}"
                    if pkg_arg not in cmd:
                        cmd.insert(cmd.index("--assume-yes-for-downloads"), pkg_arg)
        
        # 8. 如果没有检测到 tkinter，则排除它以加快打包速度
        if 'tkinter' not in detected_guis:
            cmd.insert(cmd.index("--assume-yes-for-downloads"), "--nofollow-import-to=tkinter")

        # 7. 添加编译后端参数
        if use_msvc:
            cmd.append("--msvc=latest")
        elif use_mingw:
            cmd.append("--mingw64")
        # 如果都不指定，让 Nuitka 自动选择

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

class WorkerSignals(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)
    cancelled = pyqtSignal()  # 新增：取消信号


class ToolRunner(QObject):
    def __init__(self, cmd, env):
        super().__init__()
        self.cmd = cmd
        self.env = env
        self.signals = WorkerSignals()
        self._process = None
        self._cancelled = False
    
    @property
    def is_running(self):
        """检查进程是否正在运行"""
        return self._process is not None and self._process.poll() is None
    
    def terminate(self):
        """终止打包进程"""
        self._cancelled = True
        if self._process is not None:
            try:
                # 在 Windows 上终止进程树
                if sys.platform == "win32":
                    # 使用 taskkill 终止进程树
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self._process.pid)],
                        capture_output=True,
                        startupinfo=_get_silent_startupinfo()
                    )
                else:
                    # Unix 系统使用 SIGTERM
                    import signal
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process = None
                self.signals.cancelled.emit()
                return True
            except Exception as e:
                self.signals.log.emit(f"终止进程时出错: {e}\n")
                return False
        return False
    
    def run(self):
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self._process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startupinfo,
                env=self.env
            )
            
            # 逐行读取输出
            for line in self._process.stdout:
                if self._cancelled:
                    break
                self.signals.log.emit(line)
            
            self._process.wait()
            
            if self._cancelled:
                self.signals.log.emit("打包已被用户取消\n")
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(self._process.returncode == 0)
                
        except Exception as e:
            if not self._cancelled:
                self.signals.log.emit(str(e))
                self.signals.finished.emit(False)


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
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
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

        

        # 颜色 - 商务风配色
        self._track_off_color = "#d5dce6"
        self._track_on_color  = "#5d9cec"
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
        
        layout = QHBoxLayout(self)
        self.lbl_prev = QLabel("暂无图片"); self.lbl_prev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prev.setStyleSheet("background: #ffffff; border-radius: 10px; border: 1px solid #e4e7ed; color: #95a5a6; font-size: 13px;")
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
        btn_ok = QPushButton("✅ 生成并使用")
        btn_ok.setObjectName("SuccessBtn")
        btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ok.clicked.connect(self.apply)
        # 确保按钮应用正确的样式
        btn_ok.setStyle(btn_ok.style())
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
    sig_cancelled = pyqtSignal()  # 新增：打包取消信号
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
        
        # 打包进程相关
        self._current_runner = None  # 当前运行的 ToolRunner
        self._is_packing = False  # 是否正在打包
        
        # 自动加载 name.png 图标
        icon_path = os.path.join(BASE_DIR, "name.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.timer = QTimer(); self.timer.timeout.connect(self.tick); self.start_ts = 0
        self.sig_log_bridge.connect(self.append_log) # 连接信号到日志追加方法
        self.sig_done.connect(self.done) # 连接信号到处理函数
        self.sig_cancelled.connect(self._on_cancelled)  # 连接取消信号
        self.sig_dep_check_done.connect(self._on_dep_check_done)  # 连接依赖检查完成信号
        self.sig_dep_install_done.connect(self._on_dep_install_done)  # 连接依赖安装完成信号
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_h_layout = QHBoxLayout() # 主水平布局
        main_h_layout.setContentsMargins(24, 24, 24, 20)
        main_h_layout.setSpacing(16)

        left_v_layout = QVBoxLayout() # 左侧垂直布局
        left_v_layout.setContentsMargins(0, 0, 0, 0)
        left_v_layout.setSpacing(16)

        right_v_layout = QVBoxLayout() # 右侧垂直布局
        right_v_layout.setContentsMargins(0, 0, 0, 0)
        right_v_layout.setSpacing(16)
        
        main_h_layout.addLayout(left_v_layout, 1) # 左侧占据1份空间
        main_h_layout.addLayout(right_v_layout, 1) # 右侧占据1份空间

        bottom_v_layout = QVBoxLayout() # 底部垂直布局 (用于操作区和日志)
        bottom_v_layout.setContentsMargins(24, 0, 24, 24) # 调整底部边距
        bottom_v_layout.setSpacing(16)

        layout = QVBoxLayout(central) # 整体垂直布局
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(main_h_layout, 1) # 主水平布局占据剩余空间
        layout.addLayout(bottom_v_layout, 0) # 底部布局固定高度

        # 1. 入口文件
        card_file = QFrame(objectName="Card")
        l_file = QVBoxLayout(card_file)
        l_file.setContentsMargins(18, 16, 18, 18)
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
        l_env.setContentsMargins(18, 16, 18, 18)
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
        bg_path.setStyleSheet("background: #f5f7fa; border-radius: 8px; padding: 12px; border: 1px solid #e4e7ed;")
        
        l_path = QHBoxLayout(bg_path)
        l_path.setContentsMargins(8, 0, 8, 0)

        initial_python_version = self.env_mgr.get_python_version()
        self.lbl_env = QLabel(f"{self.env_mgr.python_path} ({initial_python_version})")
        self.lbl_env.setStyleSheet("color: #5a6c7d; font-family: 'Consolas', 'Monaco', monospace; font-size: 11.5px;")
        
        l_path.addWidget(self.lbl_env)
        l_path.addStretch()

        l_env.addWidget(bg_path) # 添加路径框到环境卡片布局中 (确保只添加一次)
        left_v_layout.addWidget(card_env)

        # 3. 资源
        card_res = QFrame(objectName="Card")
        l_res = QVBoxLayout(card_res)
        l_res.setContentsMargins(18, 16, 18, 18)
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
        l_opt.setContentsMargins(18, 16, 18, 18)
        l_opt.addWidget(QLabel("构建选项", objectName="CardTitle"))
        
        # 依赖管理区域
        card_dep = QFrame(objectName="Card")
        l_dep = QVBoxLayout(card_dep)
        l_dep.setContentsMargins(16, 14, 16, 16)
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
        self.cmb_compress.setCurrentIndex(3)  # 默认不压缩（速度最快）
        self.cmb_compress.setToolTip(
            "双层压缩：内压缩 + UPX压缩（体积最小，速度最慢，可能需要10分钟以上）\n"
            "仅内压缩：仅使用 zstandard 压缩（体积较小，但压缩 Qt 库很慢）\n"
            "仅UPX：仅使用UPX压缩（速度较慢）\n"
            "不压缩：不进行任何压缩（速度最快，推荐开发调试时使用）"
        )
        h_compress.addWidget(lbl_compress)
        h_compress.addWidget(self.cmb_compress)
        h_compress.addStretch()
        v_right_column.addLayout(h_compress)
        
        # 编译后端选择（仅 Nuitka 使用）
        h_backend = QHBoxLayout()
        lbl_backend = QLabel("编译后端:")
        self.cmb_backend = QComboBox()
        self._update_backend_options()  # 初始化可用后端
        self.cmb_backend.setToolTip(
            "自动选择：优先使用 MSVC（如已安装），否则使用 MinGW\n"
            "MSVC：使用 Visual Studio 编译器（需安装 VS）\n"
            "MinGW64：使用 GCC 编译器（内置或需下载）\n\n"
            "提示：使用 MSVC 可避免下载 MinGW，编译速度更快"
        )
        h_backend.addWidget(lbl_backend)
        h_backend.addWidget(self.cmb_backend)
        h_backend.addStretch()
        v_right_column.addLayout(h_backend)
        
        # 并行编译任务数设置
        h_jobs = QHBoxLayout()
        lbl_jobs = QLabel("并行任务:")
        self.cmb_jobs = QComboBox()
        # 获取 CPU 核心数并设置选项
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
        except Exception:
            cpu_count = 4
        self.cmb_jobs.addItem("自动", 0)  # 0 表示自动
        for i in [1, 2, 4, 6, 8, 12, 16]:
            if i <= cpu_count * 2:  # 最多显示到 CPU 核心数的 2 倍
                self.cmb_jobs.addItem(str(i), i)
        self.cmb_jobs.setCurrentIndex(0)  # 默认自动
        self.cmb_jobs.setToolTip(
            f"并行编译任务数（检测到 {cpu_count} 个 CPU 核心）\n"
            "自动：使用所有 CPU 核心\n"
            "数字越大编译越快，但占用更多内存\n"
            "建议：CPU 核心数或稍多一点"
        )
        h_jobs.addWidget(lbl_jobs)
        h_jobs.addWidget(self.cmb_jobs)
        h_jobs.addStretch()
        v_right_column.addLayout(h_jobs)
        
        # GUI 框架自动检测提示
        h_gui_hint = QHBoxLayout()
        lbl_gui_hint = QLabel("💡 GUI框架自动检测")
        lbl_gui_hint.setStyleSheet("color: #909399; font-size: 11px;")
        lbl_gui_hint.setToolTip(
            "自动检测目标脚本使用的 GUI 框架\n"
            "支持: PyQt6, PyQt5, PySide6, PySide2, tkinter, wxPython\n"
            "无需手动配置，未使用的框架会自动排除以加快打包速度\n\n"
            "⚠️ 重要提示：\n"
            "Nuitka 对 PySide6 的支持优于 PyQt6\n"
            "如果使用 PyQt6 遇到问题（如线程不工作），建议切换到 PySide6"
        )
        h_gui_hint.addWidget(lbl_gui_hint)
        h_gui_hint.addStretch()
        v_right_column.addLayout(h_gui_hint)
        
        # 编译器切换时更新后端选项的可见性
        self.rb_nuitka.toggled.connect(self._on_compiler_changed)
        self.rb_pyi.toggled.connect(self._on_compiler_changed)
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
        self._btn_run_shadow = QGraphicsDropShadowEffect()
        self._btn_run_shadow.setBlurRadius(20)
        self._btn_run_shadow.setColor(QColor(93, 156, 236, 80))
        self._btn_run_shadow.setOffset(0, 6)
        self.btn_run.setGraphicsEffect(self._btn_run_shadow)
        self.btn_run.clicked.connect(self._on_btn_run_clicked)
        right_v_layout.addStretch() # 在按钮上方添加一个拉伸器，使其居底
        right_v_layout.addWidget(self.btn_run)

        # 6. 日志
        self.txt_log = QTextEdit(objectName="LogArea"); self.txt_log.setPlaceholderText("Ready..."); self.txt_log.setMinimumHeight(150); self.txt_log.setMaximumHeight(300); self.txt_log.setReadOnly(True)
        bottom_v_layout.addWidget(self.txt_log)

    def _update_backend_options(self):
        """更新编译后端选项"""
        self.cmb_backend.clear()
        backends, has_msvc, (mingw_type, mingw_path) = get_available_backends()
        self.cmb_backend.addItems(backends)
        
        # 更新工具提示以显示检测结果
        status_lines = ["编译器检测结果:"]
        if has_msvc:
            status_lines.append("✓ MSVC (Visual Studio) - 已安装")
        else:
            status_lines.append("✗ MSVC (Visual Studio) - 未安装")
        
        if mingw_type == "builtin":
            status_lines.append(f"✓ MinGW64 (内置) - {mingw_path}")
        elif mingw_type == "system":
            status_lines.append(f"✓ MinGW64 (系统) - {mingw_path}")
        else:
            status_lines.append("✗ MinGW64 - 未找到（选择时会自动下载）")
        
        status_lines.append("")
        status_lines.append("自动选择：优先 MSVC，其次 MinGW")
        status_lines.append("提示：使用 MSVC 可避免下载 MinGW")
        
        self.cmb_backend.setToolTip("\n".join(status_lines))
    
    def _on_compiler_changed(self):
        """编译器选择变化时的处理"""
        is_nuitka = self.rb_nuitka.isChecked()
        # 只有 Nuitka 才显示编译后端选项
        self.cmb_backend.setEnabled(is_nuitka)
        if is_nuitka:
            self._update_backend_options()  # 刷新检测结果

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
    def append_log(self, t):
        self.txt_log.append(t.strip())
        # 确保滚动到底部
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
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


    def _on_btn_run_clicked(self):
        """处理打包按钮点击事件"""
        if self._is_packing:
            # 正在打包，执行取消操作
            self.cancel_packing()
        else:
            # 未在打包，执行开始操作
            self.start()
    
    def _set_btn_to_cancel_mode(self):
        """将按钮设置为取消模式"""
        self.btn_run.setText("⏹ 取消打包")
        self.btn_run.setObjectName("DangerBtn")
        self.btn_run.setStyle(self.btn_run.style())  # 刷新样式
        self._btn_run_shadow.setColor(QColor(237, 85, 101, 80))  # 红色阴影
        self.btn_run.setEnabled(True)
    
    def _set_btn_to_normal_mode(self):
        """将按钮恢复为正常模式"""
        self.btn_run.setText("立即打包")
        self.btn_run.setObjectName("PrimaryBtn")
        self.btn_run.setStyle(self.btn_run.style())  # 刷新样式
        self._btn_run_shadow.setColor(QColor(93, 156, 236, 80))  # 蓝色阴影
        self.btn_run.setEnabled(True)
    
    def cancel_packing(self):
        """取消打包操作"""
        if self._current_runner and self._current_runner.is_running:
            self.sig_log_bridge.emit("\n⚠️ 正在终止打包进程...\n")
            self.btn_run.setEnabled(False)
            self.btn_run.setText("正在取消...")
            if self._current_runner.terminate():
                self.sig_log_bridge.emit("✓ 打包进程已终止\n")
                # 清理临时文件
                self._cleanup_temp_files()
                # 重置状态（停止计时器、恢复按钮）
                self._reset_after_packing()
            else:
                self.sig_log_bridge.emit("✗ 终止进程失败，请手动结束\n")
                self._reset_after_packing()
        else:
            self.sig_log_bridge.emit("没有正在运行的打包进程\n")
            self._reset_after_packing()
    
    def _cleanup_temp_files(self):
        """清理打包产生的临时文件"""
        out_dir = self.txt_out.text()
        entry_file = self.txt_file.text()
        
        self.sig_log_bridge.emit("正在清理临时文件...\n")
        cleaned_count = 0
        
        try:
            # 获取入口文件名（不含扩展名）
            if entry_file:
                base_name = os.path.splitext(os.path.basename(entry_file))[0]
                source_dir = os.path.dirname(entry_file)
            else:
                base_name = None
                source_dir = None
            
            # 需要检查的目录列表
            dirs_to_check = []
            if out_dir and os.path.exists(out_dir):
                dirs_to_check.append(out_dir)
            if source_dir and os.path.exists(source_dir) and source_dir != out_dir:
                dirs_to_check.append(source_dir)
            
            if not dirs_to_check:
                self.sig_log_bridge.emit("没有找到可检查的目录，跳过清理\n")
                return
            
            for check_dir in dirs_to_check:
                # 清理 PyInstaller 临时文件
                # 1. build_temp 目录
                build_temp = os.path.join(check_dir, "build_temp")
                if os.path.exists(build_temp):
                    shutil.rmtree(build_temp, ignore_errors=True)
                    self.sig_log_bridge.emit(f"  已删除: {build_temp}\n")
                    cleaned_count += 1
                
                # 2. .spec 文件
                for spec_file in glob.glob(os.path.join(check_dir, "*.spec")):
                    try:
                        os.remove(spec_file)
                        self.sig_log_bridge.emit(f"  已删除: {spec_file}\n")
                        cleaned_count += 1
                    except Exception:
                        pass
                
                # 清理 Nuitka 临时文件
                if base_name:
                    # 1. *.build 目录
                    build_dir = os.path.join(check_dir, f"{base_name}.build")
                    if os.path.exists(build_dir):
                        shutil.rmtree(build_dir, ignore_errors=True)
                        self.sig_log_bridge.emit(f"  已删除: {build_dir}\n")
                        cleaned_count += 1
                    
                    # 2. *.onefile-build 目录
                    onefile_build = os.path.join(check_dir, f"{base_name}.onefile-build")
                    if os.path.exists(onefile_build):
                        shutil.rmtree(onefile_build, ignore_errors=True)
                        self.sig_log_bridge.emit(f"  已删除: {onefile_build}\n")
                        cleaned_count += 1
                    
                    # 3. *.dist 目录
                    dist_dir = os.path.join(check_dir, f"{base_name}.dist")
                    if os.path.exists(dist_dir):
                        shutil.rmtree(dist_dir, ignore_errors=True)
                        self.sig_log_bridge.emit(f"  已删除: {dist_dir}\n")
                        cleaned_count += 1
                
                # 通用清理：查找所有 .build 和 .onefile-build 目录
                for pattern in ["*.build", "*.onefile-build", "*.dist"]:
                    for path in glob.glob(os.path.join(check_dir, pattern)):
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                            self.sig_log_bridge.emit(f"  已删除: {path}\n")
                            cleaned_count += 1
            
            if cleaned_count > 0:
                self.sig_log_bridge.emit(f"✓ 已清理 {cleaned_count} 个临时文件/目录\n")
            else:
                self.sig_log_bridge.emit("没有找到需要清理的临时文件（可能打包进程在生成文件前已终止）\n")
                
        except Exception as e:
            self.sig_log_bridge.emit(f"清理临时文件时出错: {e}\n")
    
    def _on_cancelled(self):
        """打包被取消后的处理"""
        self._reset_after_packing()
        self.sig_log_bridge.emit("打包已取消\n")
    
    def _reset_after_packing(self):
        """打包结束后重置状态"""
        self._is_packing = False
        self._current_runner = None
        self.timer.stop()
        self._set_btn_to_normal_mode()

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
        self._is_packing = True
        self.txt_log.clear()
        self.start_ts = time.time()
        self.lbl_timer.setVisible(True)
        self.timer.start(1000)
        self._pending_start_after_install = False
        
        # 设置按钮为取消模式
        self._set_btn_to_cancel_mode()
        
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            tgt = self.txt_file.text()
            out = self.txt_out.text()
            icon = self.txt_icon.text()
            nocon = self.chk_nocon._on
            compress_mode = self.cmb_compress.currentIndex()  # 0=双层压缩, 1=仅内压缩, 2=仅UPX, 3=不压缩
            
            # 获取编译后端选择
            backend_choice = 0  # 默认自动
            parallel_jobs = None
            
            if self.rb_nuitka.isChecked():
                backend_text = self.cmb_backend.currentText()
                if "MSVC" in backend_text:
                    backend_choice = 1
                elif "MinGW" in backend_text:
                    backend_choice = 2
                
                # 获取并行任务数
                jobs_data = self.cmb_jobs.currentData()
                if jobs_data and jobs_data > 0:
                    parallel_jobs = jobs_data
            
            tool = PyInstallerTool(self.env_mgr) if self.rb_pyi.isChecked() else NuitkaTool(self.env_mgr, backend_choice, parallel_jobs)
            
            # 仅检查打包工具，不自动安装，因为用户已经有依赖管理选项
            if not tool.check_installed():
                self.sig_log_bridge.emit(f"打包工具 {tool.name} 未安装。请通过依赖管理功能手动安装。\n")
                self.sig_done.emit(False)
                return

            # 如果使用 Nuitka，提前检测 GUI 框架并给出警告
            if isinstance(tool, NuitkaTool):
                detected_guis = tool._detect_gui_frameworks(tgt, self.sig_log_bridge)
                if detected_guis:
                    self.sig_log_bridge.emit(f"检测到 GUI 框架: {', '.join(detected_guis)}\n")

            cmd, env = tool.get_cmd(tgt, out, nocon, icon, compress_mode)
            self.sig_log_bridge.emit(f"Run: {' '.join(cmd)}\n")
            
            # 创建 runner 并保存引用
            runner = ToolRunner(cmd, env)
            self._current_runner = runner
            
            # 连接信号
            runner.signals.log.connect(self.sig_log_bridge.emit)
            runner.signals.finished.connect(self.sig_done.emit)
            runner.signals.cancelled.connect(self.sig_cancelled.emit)
            
            # 运行
            runner.run()
            
        except Exception as e:
            self.sig_log_bridge.emit(str(e))
            self.sig_done.emit(False)
    
    def done(self, success):
        """打包完成处理"""
        self._reset_after_packing()
        
        if success:
            QMessageBox.information(self, "完成", "打包成功！")
            try:
                os.startfile(self.txt_out.text())
            except Exception as e:
                self.sig_log_bridge.emit(f"无法打开输出目录: {e}\n")
        else:
            QMessageBox.critical(self, "错误", "打包失败，请检查日志。")

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