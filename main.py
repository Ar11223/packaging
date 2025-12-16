import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import sys
import os
import subprocess
import threading

# ===========================
# 依赖检查：Pillow (用于图标处理)
# ===========================
try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ===========================
# 配置常量
# ===========================
MINGW_DIR_NAME = "mingw64"


# ===========================
# 1. 图像处理核心 (IconProcessor)
# ===========================
class IconProcessor:
    @staticmethod
    def create_shaped_icon(image_path, shape='rounded', size=256, zoom=1.0):
        """
        读取图片并应用形状遮罩 + 缩放处理
        :param zoom: 缩放比例 (0.5 - 2.0)
        """
        if not HAS_PILLOW:
            return None

        try:
            # 打开并转换为 RGBA
            img = Image.open(image_path).convert("RGBA")
            
            # --- 1. 缩放处理 ---
            orig_w, orig_h = img.size
            base_scale = max(size / orig_w, size / orig_h)
            final_scale = base_scale * zoom
            
            new_w = int(orig_w * final_scale)
            new_h = int(orig_h * final_scale)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # --- 2. 创建画布并居中 ---
            background = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            paste_x = (size - new_w) // 2
            paste_y = (size - new_h) // 2
            background.paste(img, (paste_x, paste_y))
            img = background 

            # --- 3. 创建遮罩 ---
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

            # --- 4. 应用遮罩 ---
            output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            output.paste(img, (0, 0), mask=mask)
            return output
            
        except Exception as e:
            print(f"图像处理错误: {e}")
            return None


# ===========================
# 2. 图标生成器弹窗 (IconGeneratorDialog)
# ===========================
class IconGeneratorDialog:
    def __init__(self, parent, callback, default_save_dir="."):
        self.top = tk.Toplevel(parent)
        self.top.title("图标工作台")
        self.top.geometry("700x520")
        self.top.resizable(False, False)
        
        self.callback = callback
        self.default_save_dir = default_save_dir
        self.source_image_path = None
        self.preview_image_obj = None 
        self.processed_pil_image = None 
        self.zoom_val = 1.0
        
        if not HAS_PILLOW:
            tk.Label(self.top, text="错误: 未安装 Pillow 库。\n请运行 pip install Pillow", fg="red").pack(pady=20)
            return

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.top)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # === 左侧：预览区 ===
        left_frame = ttk.LabelFrame(main_frame, text=" 实时预览 ")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        canvas_container = ttk.Frame(left_frame)
        canvas_container.pack(expand=True, fill="both")
        
        self.canvas_size = 280
        self.canvas = tk.Canvas(canvas_container, width=self.canvas_size, height=self.canvas_size, bg="#f0f0f0", bd=0, highlightthickness=0)
        self.canvas.pack(anchor="center", expand=True)
        
        self.draw_dashed_box()
        self.lbl_hint = self.canvas.create_text(self.canvas_size/2, self.canvas_size/2, text="请打开图片", fill="#999")
        self.preview_item = None

        # === 右侧：设置区 ===
        right_frame = ttk.Frame(main_frame, width=240)
        right_frame.pack(side="right", fill="y")
        right_frame.pack_propagate(False)
        
        # 1. 打开图片
        self.btn_open = ttk.Button(right_frame, text="📂 打开图片 (PNG/JPG)", command=self.load_image)
        self.btn_open.pack(fill="x", pady=(0, 20), ipady=5)
        
        # 2. 形状选择
        ttk.Label(right_frame, text="图标形状:").pack(anchor="w", pady=(0, 5))
        self.var_shape = tk.StringVar(value="rounded")
        self.combo_shape = ttk.Combobox(right_frame, textvariable=self.var_shape, state="readonly")
        self.combo_shape['values'] = ("圆角方形 (Rounded)", "正方形 (Square)", "圆形 (Circle)", "心形 (Heart)")
        self.shape_map = {
            "圆角方形 (Rounded)": "rounded",
            "正方形 (Square)": "square",
            "圆形 (Circle)": "circle",
            "心形 (Heart)": "heart"
        }
        self.combo_shape.current(0)
        self.combo_shape.pack(fill="x", pady=(0, 15))
        self.combo_shape.bind("<<ComboboxSelected>>", self.update_preview)
        
        # 3. 缩放
        ttk.Label(right_frame, text="缩放/裁剪:").pack(anchor="w", pady=(0, 5))
        self.slider = ttk.Scale(right_frame, from_=0.5, to=2.0, value=1.0, command=self.on_slider_change)
        self.slider.pack(fill="x", pady=(0, 20))
        
        # 4. 选项
        self.var_transparent = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(right_frame, text="保留透明背景", variable=self.var_transparent, state="disabled")
        chk.pack(anchor="w", pady=(0, 20))
        
        ttk.Separator(right_frame, orient="horizontal").pack(fill="x", pady=(20, 20))
        
        # 5. 底部按钮
        ttk.Button(right_frame, text="仅导出 ICO...", command=self.export_ico).pack(fill="x", pady=(0, 10))
        
        self.btn_apply = tk.Button(right_frame, text="✅ 使用此图标", bg="#28a745", fg="white", 
                                   font=("微软雅黑", 10, "bold"), relief="flat", cursor="hand2",
                                   command=self.apply_icon)
        self.btn_apply.pack(fill="x", ipady=8)
        
        display_dir = "当前目录"
        if self.default_save_dir and os.path.exists(self.default_save_dir):
            display_dir = os.path.basename(self.default_save_dir)
            
        self.lbl_path_hint = ttk.Label(right_frame, text=f"将保存至: {display_dir}/icon.ico", 
                                       font=("Arial", 8), foreground="#666", wraplength=230)
        self.lbl_path_hint.pack(pady=(10, 0))

    def draw_dashed_box(self):
        pad = (self.canvas_size - 256) / 2
        self.canvas.create_rectangle(pad, pad, self.canvas_size-pad, self.canvas_size-pad, 
                                     outline="#ccc", width=2, dash=(5, 5))

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp")])
        if path:
            self.source_image_path = path
            self.slider.set(1.0)
            self.canvas.delete(self.lbl_hint)
            self.update_preview()

    def on_slider_change(self, value):
        self.zoom_val = float(value)
        self.update_preview()

    def update_preview(self, event=None):
        if not self.source_image_path:
            return
        shape_text = self.combo_shape.get()
        shape_val = self.shape_map.get(shape_text, "rounded")
        
        self.processed_pil_image = IconProcessor.create_shaped_icon(
            self.source_image_path, shape=shape_val, size=256, zoom=self.zoom_val
        )
        
        if self.processed_pil_image:
            self.preview_image_obj = ImageTk.PhotoImage(self.processed_pil_image)
            center = self.canvas_size / 2
            if self.preview_item:
                self.canvas.itemconfig(self.preview_item, image=self.preview_image_obj)
            else:
                self.preview_item = self.canvas.create_image(center, center, image=self.preview_image_obj)

    def export_ico(self):
        if not self.processed_pil_image:
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".ico", filetypes=[("Icon File", "*.ico")])
        if save_path:
            try:
                self.processed_pil_image.save(save_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                messagebox.showinfo("成功", f"图标已导出: {save_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

    def apply_icon(self):
        if not self.processed_pil_image:
            return
        try:
            save_dir = self.default_save_dir
            if not save_dir or not os.path.exists(save_dir):
                save_dir = os.path.dirname(os.path.abspath(__file__))
            else:
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
            
            save_path = os.path.join(save_dir, "icon.ico")
            self.processed_pil_image.save(save_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            
            if self.callback:
                self.callback(save_path)
            self.top.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"应用图标失败: {str(e)}")


# ===========================
# 3. 系统核心类 (执行与环境)
# ===========================
def run_command(cmd, log_callback, env=None):
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if env is None:
            env = os.environ.copy()

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
            startupinfo=startupinfo, env=env
        )

        for line in process.stdout:
            log_callback(line)
        process.wait()
        return process.returncode == 0
    except Exception as e:
        log_callback(f"执行出错: {str(e)}\n")
        return False

class EnvManager:
    def __init__(self):
        self.python_path = sys.executable

    def set_python_path(self, path):
        if os.path.exists(path):
            self.python_path = path
            return True
        return False

    def run_pip_install(self, package_name, log_callback):
        cmd = [self.python_path, "-m", "pip", "install", package_name]
        log_callback(f"正在安装依赖: {' '.join(cmd)}\n")
        return run_command(cmd, log_callback, env=None)

    def get_version(self):
        try:
            output = subprocess.check_output([self.python_path, "--version"], text=True)
            return output.strip()
        except:
            return "Unknown"


# ===========================
# 4. 打包工具类 (支持 UPX)
# ===========================
class BaseTool:
    def __init__(self, env_manager):
        self.env = env_manager
        self.name = "Base"
        self.module_name = "base"

    def check_installed(self):
        try:
            subprocess.check_call(
                [self.env.python_path, "-c", f"import {self.module_name}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def check_compatibility(self):
        return True, "兼容"
    
    # 辅助方法：查找 tools 目录下的 upx.exe
    def find_upx_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tools_dir = os.path.join(base_dir, "tools")
        
        if not os.path.exists(tools_dir):
            return None
            
        # 遍历 tools 目录寻找 upx.exe
        for root, dirs, files in os.walk(tools_dir):
            if "upx.exe" in files:
                return root # 返回包含 upx.exe 的目录路径
        return None

class PyInstallerTool(BaseTool):
    def __init__(self, env_manager):
        super().__init__(env_manager)
        self.name = "PyInstaller"
        self.module_name = "PyInstaller"

    def get_build_info(self, target_file, output_dir, no_console, icon_path, use_upx):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cmd = [
            self.env.python_path, "-m", "PyInstaller",
            "-F", target_file,
            "--distpath", output_dir,
            "--specpath", output_dir,
            "--workpath", os.path.join(output_dir, "build_temp"),
        ]
        if no_console:
            cmd.append("-w")
        if icon_path and os.path.exists(icon_path):
            cmd.extend(["--icon", icon_path])
        
        # UPX 配置
        if use_upx:
            upx_dir = self.find_upx_path()
            if upx_dir:
                cmd.extend(["--upx-dir", upx_dir])
            else:
                print("Warning: UPX enabled but not found in tools.")
        else:
             cmd.append("--noupx")

        return cmd, None

class NuitkaTool(BaseTool):
    def __init__(self, env_manager):
        super().__init__(env_manager)
        self.name = "Nuitka"
        self.module_name = "nuitka"

    def check_compatibility(self):
        ver_str = self.env.get_version()
        if "3.13" in ver_str or "3.14" in ver_str:
            return False, f"警告: Nuitka 可能尚不支持 {ver_str}，建议使用 3.10-3.12"
        return True, "兼容"

    def get_build_info(self, target_file, output_dir, no_console, icon_path, use_upx):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mingw_bin = os.path.join(base_dir, "tools", MINGW_DIR_NAME, "mingw64", "bin")

        if not os.path.exists(mingw_bin):
            mingw_bin_fallback = os.path.join(base_dir, "tools", MINGW_DIR_NAME, "bin")
            if os.path.exists(mingw_bin_fallback):
                mingw_bin = mingw_bin_fallback

        custom_env = os.environ.copy()
        found_compiler = False
        if os.path.exists(mingw_bin) and os.path.join(mingw_bin, "gcc.exe"):
            custom_env["PATH"] = mingw_bin + os.pathsep + custom_env["PATH"]
            found_compiler = True

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cmd = [
            self.env.python_path, "-m", "nuitka",
            "--standalone", "--onefile",
            "--enable-plugin=tk-inter",
            "--assume-yes-for-downloads",
            "--remove-output",
            f"--output-dir={output_dir}",
            target_file
        ]
        if no_console:
            cmd.append("--windows-disable-console")
        if icon_path and os.path.exists(icon_path):
            cmd.append(f"--windows-icon-from-ico={icon_path}")
        
        # UPX 配置
        upx_found_path = None
        if use_upx:
            upx_dir = self.find_upx_path()
            if upx_dir:
                cmd.append("--enable-plugin=upx")
                # 将 UPX 路径注入 PATH，Nuitka 会自动检测
                custom_env["PATH"] = upx_dir + os.pathsep + custom_env["PATH"]
                upx_found_path = upx_dir
            else:
                # 如果没找到，Nuitka 可能会报错或跳过，这里可以选择添加 --disable-plugin=upx
                pass
        else:
            cmd.append("--disable-plugin=upx")
        
        return cmd, custom_env, found_compiler, mingw_bin, upx_found_path


# ===========================
# 5. 主程序界面 (PackerApp)
# ===========================
class PackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 聚合打包工具 Pro (UPX版)")
        self.root.geometry("900x850") # 增加高度

        self.env_manager = EnvManager()
        self.target_file = ""
        self.icon_path = "" 

        self.setup_ui()
        if not HAS_PILLOW:
            messagebox.showwarning("缺少依赖", "检测到未安装 Pillow 库，'制作图标'功能将不可用。\n建议打包前先运行: pip install Pillow")

    def setup_ui(self):
        # 1. 文件选择
        f1 = ttk.LabelFrame(self.root, text="1. 选择入口文件")
        f1.pack(fill="x", padx=10, pady=5)
        self.lbl_file = ttk.Label(f1, text="未选择文件")
        self.lbl_file.pack(side="left", padx=5)
        ttk.Button(f1, text="浏览...", command=self.select_file).pack(side="right", padx=5)

        # 2. 环境
        f2 = ttk.LabelFrame(self.root, text="2. 环境配置")
        f2.pack(fill="x", padx=10, pady=5)
        self.var_env_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(f2, text="自动检测 (优先 venv)", variable=self.var_env_mode, value="auto", command=self.detect_env_trigger).pack(anchor="w")
        ttk.Radiobutton(f2, text="手动指定 python.exe", variable=self.var_env_mode, value="manual", command=self.manual_env).pack(anchor="w")
        self.lbl_env = ttk.Label(f2, text=f"当前: {self.env_manager.python_path}", foreground="blue")
        self.lbl_env.pack(fill="x", padx=5, pady=2)

        # 3. 输出
        f3 = ttk.LabelFrame(self.root, text="3. 输出目录")
        f3.pack(fill="x", padx=10, pady=5)
        self.var_out = tk.StringVar()
        ttk.Entry(f3, textvariable=self.var_out).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(f3, text="浏览...", command=self.select_out).pack(side="right", padx=5)

        # 4. 图标
        f4 = ttk.LabelFrame(self.root, text="4. 图标设置")
        f4.pack(fill="x", padx=10, pady=5)
        self.var_icon = tk.StringVar()
        ttk.Entry(f4, textvariable=self.var_icon).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(f4, text="制作图标...", command=self.open_icon_maker).pack(side="right", padx=2)
        ttk.Button(f4, text="选择图标...", command=self.select_icon).pack(side="right", padx=2)

        # 5. 工具
        f5 = ttk.LabelFrame(self.root, text="5. 打包工具与选项")
        f5.pack(fill="x", padx=10, pady=5)
        self.var_tool = tk.StringVar(value="nuitka")
        ttk.Radiobutton(f5, text="Nuitka (高性能)", variable=self.var_tool, value="nuitka").pack(side="left", padx=10)
        ttk.Radiobutton(f5, text="PyInstaller", variable=self.var_tool, value="pyinstaller").pack(side="left", padx=10)
        
        ttk.Separator(f5, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # 选项列
        self.var_noconsole = tk.BooleanVar(value=True)
        ttk.Checkbutton(f5, text="去除黑窗口 (No Console)", variable=self.var_noconsole).pack(side="left", padx=10)
        
        self.var_upx = tk.BooleanVar(value=True)
        ttk.Checkbutton(f5, text="开启 UPX 压缩 (减小体积)", variable=self.var_upx).pack(side="left", padx=10)

        # 6. 运行
        f6 = ttk.Frame(self.root)
        f6.pack(fill="x", padx=10, pady=10)
        self.btn_run = ttk.Button(f6, text="开始打包", command=self.start_thread)
        self.btn_run.pack(fill="x", ipady=8)

        # 7. 日志
        self.log_txt = scrolledtext.ScrolledText(self.root, height=10)
        self.log_txt.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, msg):
        self.log_txt.insert(tk.END, msg)
        self.log_txt.see(tk.END)

    def select_file(self):
        p = filedialog.askopenfilename(filetypes=[("Python", "*.py")])
        if p:
            self.target_file = p
            self.lbl_file.config(text=p)
            if not self.var_out.get():
                self.var_out.set(os.path.join(os.path.dirname(p), "dist_output"))
            if self.var_env_mode.get() == "auto":
                self.detect_venv(os.path.dirname(p))

    def select_out(self):
        p = filedialog.askdirectory()
        if p: self.var_out.set(p)

    def select_icon(self):
        p = filedialog.askopenfilename(filetypes=[("Icon", "*.ico")])
        if p: self.var_icon.set(p)

    def open_icon_maker(self):
        if not HAS_PILLOW:
            messagebox.showerror("错误", "需安装 Pillow")
            return
        out_dir = self.var_out.get()
        if not out_dir: 
            out_dir = os.path.dirname(os.path.abspath(__file__))
        IconGeneratorDialog(self.root, self.on_icon_made, default_save_dir=out_dir)

    def on_icon_made(self, path):
        self.var_icon.set(path)
        self.log(f"图标已生成并选中: {path}\n")

    def detect_env_trigger(self):
        if self.target_file: self.detect_venv(os.path.dirname(self.target_file))
        else: self.detect_venv(os.getcwd())

    def detect_venv(self, base):
        found = False
        for d in ["venv", ".venv", "env"]:
            p = os.path.join(base, d)
            if os.path.exists(p):
                exe = os.path.join(p, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(p, "bin", "python")
                if os.path.exists(exe):
                    self.env_manager.set_python_path(exe)
                    self.lbl_env.config(text=f"自动检测: {exe}")
                    found = True
                    break
        if not found:
            self.env_manager.set_python_path(sys.executable)
            self.lbl_env.config(text=f"使用全局: {sys.executable}")

    def manual_env(self):
        p = filedialog.askopenfilename(title="python.exe", filetypes=[("Exe", "*.exe")])
        if p:
            self.env_manager.set_python_path(p)
            self.lbl_env.config(text=f"手动: {p}")

    def start_thread(self):
        if not self.target_file: return messagebox.showerror("错误", "请选文件")
        if not self.var_out.get(): return messagebox.showerror("错误", "请选输出目录")
        self.btn_run.config(state="disabled")
        self.log_txt.delete(1.0, tk.END)
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        out = self.var_out.get()
        ico = self.var_icon.get()
        nocon = self.var_noconsole.get()
        use_upx = self.var_upx.get()
        
        tool = PyInstallerTool(self.env_manager) if self.var_tool.get() == "pyinstaller" else NuitkaTool(self.env_manager)
        
        self.log(f"=== {tool.name} 开始 ===\n")
        
        if not tool.check_installed():
            self.log(f"正在安装 {tool.name}...\n")
            if not self.env_manager.run_pip_install(tool.module_name, self.log):
                self.btn_run.config(state="normal")
                return

        if isinstance(tool, NuitkaTool):
            # 获取构建信息，包含UPX路径
            cmd, env, found_cc, mingw, upx_path = tool.get_build_info(self.target_file, out, nocon, ico, use_upx)
            
            if not found_cc: 
                self.log("提示：未找到本地 MinGW，Nuitka 将尝试下载。\n")
            if use_upx:
                if upx_path:
                    self.log(f"已启用 UPX 压缩，使用本地路径: {upx_path}\n")
                else:
                    self.log("警告：勾选了 UPX 但未在 tools 目录中找到 upx.exe，Nuitka 将尝试自动寻找或忽略。\n")
        else:
            # PyInstaller
            cmd, env = tool.get_build_info(self.target_file, out, nocon, ico, use_upx)
            if use_upx and "--upx-dir" not in cmd:
                 self.log("警告：勾选了 UPX 但未在 tools 目录中找到 upx.exe，PyInstaller 可能无法压缩。\n")
            elif use_upx:
                 self.log("已启用 UPX 压缩 (PyInstaller)\n")

        self.log(f"命令: {' '.join(cmd)}\n\n")
        if run_command(cmd, self.log, env):
            self.log("\n>>> 成功! <<<\n")
            try: os.startfile(out)
            except: pass
        else:
            self.log("\n>>> 失败 <<<\n")
        self.btn_run.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = PackerApp(root)
    root.mainloop()