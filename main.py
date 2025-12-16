import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import sys
import os
import subprocess
import threading

# ===========================
# 配置常量
# ===========================
MINGW_DIR_NAME = "mingw64"


# ===========================
# 1. 异步进程执行器
# ===========================
def run_command(cmd, log_callback, env=None):
    """
    执行命令并实时捕获输出
    """
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if env is None:
            env = os.environ.copy()

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            startupinfo=startupinfo,
            env=env
        )

        for line in process.stdout:
            log_callback(line)

        process.wait()
        return process.returncode == 0
    except Exception as e:
        log_callback(f"执行出错: {str(e)}\n")
        return False


# ===========================
# 2. 环境管理器
# ===========================
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
# 3. 打包工具策略类 (已修改支持 No Console)
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

    def get_build_info(self, target_file, output_dir, no_console):
        """
        返回 (cmd_list, env_dict)
        :param target_file: 入口文件
        :param output_dir: 输出目录
        :param no_console: Boolean, 是否去除黑窗口
        """
        raise NotImplementedError


class PyInstallerTool(BaseTool):
    def __init__(self, env_manager):
        super().__init__(env_manager)
        self.name = "PyInstaller"
        self.module_name = "PyInstaller"

    def get_build_info(self, target_file, output_dir, no_console):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cmd = [
            self.env.python_path, "-m", "PyInstaller",
            "-F",             # 单文件
            target_file,
            "--distpath", output_dir,
            "--specpath", output_dir,
            "--workpath", os.path.join(output_dir, "build_temp"),
        ]

        # --- 核心修改：去除控制台 ---
        if no_console:
            cmd.append("-w")  # -w 等同于 --noconsole

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

    def get_build_info(self, target_file, output_dir, no_console):
        # 1. 定位本地 MinGW64
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mingw_bin = os.path.join(base_dir, "tools", MINGW_DIR_NAME, "mingw64", "bin")

        if not os.path.exists(mingw_bin):
            mingw_bin_fallback = os.path.join(base_dir, "tools", MINGW_DIR_NAME, "bin")
            if os.path.exists(mingw_bin_fallback):
                mingw_bin = mingw_bin_fallback

        # 2. 注入环境变量
        custom_env = os.environ.copy()
        found_compiler = False
        if os.path.exists(mingw_bin) and os.path.exists(os.path.join(mingw_bin, "gcc.exe")):
            custom_env["PATH"] = mingw_bin + os.pathsep + custom_env["PATH"]
            found_compiler = True

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 3. 构建命令
        cmd = [
            self.env.python_path,
            "-m", "nuitka",
            "--standalone",
            "--onefile",
            "--enable-plugin=tk-inter",
            "--assume-yes-for-downloads",
            "--remove-output",
            f"--output-dir={output_dir}",
            target_file
        ]

        # --- 核心修改：去除控制台 ---
        if no_console:
            cmd.append("--windows-disable-console")

        return cmd, custom_env, found_compiler, mingw_bin


# ===========================
# 4. GUI 主程序
# ===========================
class PackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 聚合打包工具 (支持无窗口模式)")
        self.root.geometry("900x750")

        self.env_manager = EnvManager()
        self.target_file = ""
        self.output_dir = ""

        self.setup_ui()

    def setup_ui(self):
        # --- 1. 文件选择 ---
        frame_file = ttk.LabelFrame(self.root, text="1. 选择入口文件 (.py)")
        frame_file.pack(fill="x", padx=10, pady=5)

        self.lbl_file = ttk.Label(frame_file, text="未选择文件")
        self.lbl_file.pack(side="left", padx=5)
        ttk.Button(frame_file, text="浏览...", command=self.select_file).pack(side="right", padx=5)

        # --- 2. 环境配置 ---
        frame_env = ttk.LabelFrame(self.root, text="2. 环境配置")
        frame_env.pack(fill="x", padx=10, pady=5)

        self.var_env_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(frame_env, text="自动检测 (优先 venv)", variable=self.var_env_mode, value="auto",
                        command=self.update_env_display).pack(anchor="w")
        ttk.Radiobutton(frame_env, text="手动指定 python.exe", variable=self.var_env_mode, value="manual",
                        command=self.manual_select_env).pack(anchor="w")

        self.lbl_current_env = ttk.Label(frame_env, text=f"当前环境: {self.env_manager.python_path}", foreground="blue")
        self.lbl_current_env.pack(fill="x", padx=5, pady=5)

        # --- 3. 输出配置 ---
        frame_output = ttk.LabelFrame(self.root, text="3. 输出配置")
        frame_output.pack(fill="x", padx=10, pady=5)
        
        self.var_out_path = tk.StringVar()
        self.entry_out = ttk.Entry(frame_output, textvariable=self.var_out_path)
        self.entry_out.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        ttk.Button(frame_output, text="选择输出文件夹...", command=self.select_output_dir).pack(side="right", padx=5)

        # --- 4. 工具选择与选项 ---
        frame_tool = ttk.LabelFrame(self.root, text="4. 工具与选项")
        frame_tool.pack(fill="x", padx=10, pady=5)

        # 工具选择
        self.var_tool = tk.StringVar(value="nuitka")
        ttk.Radiobutton(frame_tool, text="Nuitka (推荐)", variable=self.var_tool, value="nuitka").pack(side="left", padx=10)
        ttk.Radiobutton(frame_tool, text="PyInstaller", variable=self.var_tool, value="pyinstaller").pack(side="left", padx=10)
        
        # 分隔线
        ttk.Separator(frame_tool, orient="vertical").pack(side="left", fill="y", padx=10, pady=2)

        # 新增：是否去除黑窗口 (默认为 True，即去除)
        self.var_noconsole = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_tool, text="去除黑窗口 (No Console)", variable=self.var_noconsole).pack(side="left", padx=10)

        # --- 5. 操作 ---
        frame_action = ttk.Frame(self.root)
        frame_action.pack(fill="x", padx=10, pady=10)
        self.btn_run = ttk.Button(frame_action, text="开始打包", command=self.start_process_thread)
        self.btn_run.pack(fill="x", ipady=8)

        # --- 6. 日志 ---
        self.txt_log = scrolledtext.ScrolledText(self.root, height=15, state='normal')
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, message):
        self.txt_log.insert(tk.END, message)
        self.txt_log.see(tk.END)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.target_file = path
            self.lbl_file.config(text=path)
            
            if not self.var_out_path.get():
                default_dist = os.path.join(os.path.dirname(path), "dist_output")
                self.var_out_path.set(default_dist)
                
            if self.var_env_mode.get() == "auto":
                self.detect_venv(os.path.dirname(path))

    def select_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.var_out_path.set(path)

    def detect_venv(self, base_dir):
        potential_dirs = ["venv", ".venv", "env"]
        found_env = False
        for d in potential_dirs:
            venv_path = os.path.join(base_dir, d)
            if os.path.exists(venv_path):
                if os.name == 'nt':
                    exe = os.path.join(venv_path, "Scripts", "python.exe")
                else:
                    exe = os.path.join(venv_path, "bin", "python")

                if os.path.exists(exe):
                    self.env_manager.set_python_path(exe)
                    self.update_env_display(f"自动检测到虚拟环境: {exe}")
                    found_env = True
                    break
        
        if not found_env:
            self.env_manager.set_python_path(sys.executable)
            self.update_env_display(f"未检测到虚拟环境，使用全局: {sys.executable}")

    def manual_select_env(self):
        path = filedialog.askopenfilename(title="选择 python.exe", filetypes=[("Executable", "*.exe"), ("All", "*")])
        if path:
            self.env_manager.set_python_path(path)
            self.update_env_display()

    def update_env_display(self, msg=None):
        if msg:
            self.lbl_current_env.config(text=msg)
        else:
            self.lbl_current_env.config(text=f"当前环境: {self.env_manager.python_path}")

    def start_process_thread(self):
        if not self.target_file:
            messagebox.showerror("错误", "请先选择入口文件")
            return
        
        out_dir = self.var_out_path.get()
        if not out_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        self.btn_run.config(state="disabled")
        self.txt_log.delete(1.0, tk.END)
        threading.Thread(target=self.run_logic, args=(out_dir,), daemon=True).start()

    def run_logic(self, output_dir):
        tool_type = self.var_tool.get()
        # 获取用户是否选择了去除黑窗口
        is_noconsole = self.var_noconsole.get()

        if tool_type == "pyinstaller":
            tool = PyInstallerTool(self.env_manager)
        elif tool_type == "nuitka":
            tool = NuitkaTool(self.env_manager)
        else:
            return

        self.log(f"=== 开始流程: {tool.name} ===\n")
        self.log(f"目标路径: {output_dir}\n")
        self.log(f"模式: {'无控制台 (No Console)' if is_noconsole else '带控制台 (Debug Mode)'}\n\n")
        
        # 1. 兼容性检查
        is_compat, msg = tool.check_compatibility()
        if not is_compat:
            self.log(f"{msg}\n")

        # 2. 依赖检查
        if not tool.check_installed():
            self.log(f"正在安装 {tool.name}...\n")
            success = self.env_manager.run_pip_install(tool.module_name, self.log)
            if not success:
                self.log("依赖安装失败。\n")
                self.btn_run.config(state="normal")
                return
        
        # 3. 准备命令 (传入 is_noconsole)
        if isinstance(tool, NuitkaTool):
            cmd, custom_env, found_compiler, mingw_path = tool.get_build_info(self.target_file, output_dir, is_noconsole)
            if found_compiler:
                self.log(f"使用编译器: {mingw_path}\n")
            else:
                self.log("警告：未找到本地 MinGW，Nuitka 将尝试下载。\n")
        else:
            cmd, custom_env = tool.get_build_info(self.target_file, output_dir, is_noconsole)

        # 4. 执行
        self.log(f"命令: {' '.join(cmd)}\n")
        self.log("-" * 40 + "\n")
        
        success = run_command(cmd, self.log, env=custom_env)

        if success:
            self.log("\n>>> 打包成功! <<<\n")
            try:
                os.startfile(output_dir)
            except:
                pass
        else:
            self.log("\n>>> 打包失败 <<<\n")

        self.btn_run.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = PackerApp(root)
    root.mainloop()