import os
import shutil
import subprocess
import sys
import platform
import time
import threading
from datetime import datetime
import src

Suffix = None

if src.__channel__ != "Release":
    Suffix = f"({src.__channel__})"
else:
    Suffix = ""

# 应用名称
app_name = f"Vortex Luncher{Suffix}"

# 进度动画类
class ProgressIndicator:
    def __init__(self, desc="构建中"):
        self.desc = desc
        self.running = False
        self.spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        self.thread = None
        self.counter = 0
        self.start_time = None
    
    def spin(self):
        self.start_time = time.time()
        while self.running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            hours, mins = divmod(mins, 60)
            timeformat = f"{hours:02d}:{mins:02d}:{secs:02d}"
            
            sys.stdout.write(f"\r{self.desc} {self.spinner[self.counter % len(self.spinner)]} [{timeformat}]")
            sys.stdout.flush()
            self.counter += 1
            time.sleep(0.1)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 80 + "\r")  # 清除进度指示器
        sys.stdout.flush()

def package_app(target_os=None):
    """打包应用程序"""
    # 检测当前操作系统
    current_os = platform.system().lower()
    if current_os == "darwin":
        current_os = "macos"
    
    # 如果没有指定目标系统，则使用当前系统
    if target_os is None:
        target_os = current_os
    
    # 规范化目标系统名称
    target_os = target_os.lower()
    
    # 检查是否尝试跨平台构建
    if target_os != current_os:
        print(f"\n警告: PyInstaller不支持跨平台构建!")
        print(f"当前系统: {current_os.capitalize()}")
        print(f"目标系统: {target_os.capitalize()}")
        print("您只能构建当前运行的操作系统的可执行文件。")
        print("如果您需要构建其他平台的可执行文件，请在相应的操作系统上运行此脚本。")
        
        user_input = input("\n是否继续使用当前系统进行构建? (y/n): ")
        if user_input.lower() != 'y':
            print("构建已取消")
            return None
        
        print(f"\n将使用当前系统 ({current_os}) 进行构建，而不是请求的 {target_os} 系统。")
        target_os = current_os
    
    # 生成日期格式的构建目录
    build_date = datetime.now().strftime("%y-%m-%d %H-%M-%S")
    output_dir = os.path.join("build", build_date)
    
    # 清理历史构建文件（保留其他日期目录）
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 复制thirdparty到目标目录
    thirdparty_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thirdparty")
    if os.path.exists(thirdparty_dir):
        target_licenses = os.path.join(f"{output_dir}\\{current_os}\\{app_name}", "licenses")
        os.makedirs(target_licenses, exist_ok=True)
        try:
            for item in os.listdir(thirdparty_dir):
                src_path = os.path.join(thirdparty_dir, item)
                dst_path = os.path.join(target_licenses, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"复制thirdparty时出错: {str(e)}")
    else:
        print("警告: 未找到thirdparty目录，跳过复制thirdparty步骤。")
    
    # 获取当前脚本所在的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 根据目标系统设置图标和其他特定参数，使用绝对路径
    icon_path = os.path.join(current_dir, "webside", "images", "2.0logo.ico") if target_os == "windows" else os.path.join(current_dir, "webside", "images", "logo.png")
    
    # 特定于操作系统的参数
    os_specific_args = []
    
    if target_os == "windows":
        os_specific_args.extend(["--noconsole"])
        output_subdir = os.path.join(output_dir, "windows")
    elif target_os == "darwin" or target_os == "macos":
        os_specific_args.extend(["--noconsole", "--osx-bundle-identifier", "com.vortexlauncher.app"])
        output_subdir = os.path.join(output_dir, "macos")
    elif target_os == "linux":
        output_subdir = os.path.join(output_dir, "linux")
    else:
        print(f"不支持的目标系统: {target_os}")
        return
    
    # 创建特定于操作系统的输出目录
    os.makedirs(output_subdir, exist_ok=True)
    
    # 基本PyInstaller命令
    cmd = [
        "pyinstaller",
        "-F",  # 创建单个文件
        "main.py",
        "-n", app_name,
        "--icon", icon_path,
        "--distpath", output_subdir,
        "--workpath", os.path.join(output_dir, f"temp_{target_os}"),
        "--specpath", output_dir,
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--collect-all", "PyQt6"
    ]
    
    # 添加特定于操作系统的参数
    cmd.extend(os_specific_args)
    
    # 执行打包命令，显示实时进度
    print(f"开始为 {target_os} 构建...")
    print("这可能需要几分钟时间，请耐心等待...")
    print("-" * 60)
    
    # 启动进度指示器
    progress = ProgressIndicator(f"正在为 {target_os} 构建")
    progress.start()
    
    try:
        # 直接显示输出，不捕获
        process = subprocess.run(cmd, check=True)
        progress.stop()
        print(f"PyInstaller构建完成！")
    except subprocess.CalledProcessError as e:
        progress.stop()
        print(f"构建失败，错误码: {e.returncode}")
        return None
    except KeyboardInterrupt:
        progress.stop()
        print("\n构建被用户中断")
        return None
    finally:
        progress.stop()
    
    print("-" * 60)
    
    # 复制DLL文件到输出目录
    dlls_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dlls")
    if os.path.exists(dlls_dir):
        print("正在复制DLL文件...")
        target_bin = os.path.join(output_subdir, app_name)
        try:
            for item in os.listdir(dlls_dir):
                src_path = os.path.join(dlls_dir, item)
                dst_path = os.path.join(target_bin, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"复制DLL文件时出错: {str(e)}")
    
    # 创建启动批处理文件
    print("正在创建启动脚本...")
    batch_content = """@echo off
setlocal
echo 正在检查运行环境...
if not exist "%ProgramFiles(x86)%\\Microsoft Visual Studio\\Shared\\VC\\Tools\\MSVC" (
    echo 未检测到Visual C++运行库，正在安装...
    if exist "vcredist_x86.exe" (
        start /wait vcredist_x86.exe /install /quiet /norestart
    )
    if exist "vcredist_x64.exe" (
        start /wait vcredist_x64.exe /install /quiet /norestart
    )
) else (
    echo Visual C++运行库已安装
)
echo 正在启动程序...
start "" "%~dp0{0}.exe"
endlocal
""".format(app_name)
    
    with open(os.path.join(output_subdir, "启动.bat"), "w") as f:
        f.write(batch_content)
    
    # 清理临时文件
    print("正在清理临时文件...")
    temp_dir = os.path.join(output_dir, f"temp_{target_os}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # 删除.spec文件
    spec_file = os.path.join(output_dir, f"{app_name}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    print(f"✅ {target_os} 构建完成，输出目录：{output_subdir}")
    return output_subdir


def build_all():
    """构建所有平台版本"""
    # 获取当前操作系统
    current_os = platform.system().lower()
    if current_os == "darwin":
        current_os = "macos"
    
    print("\n注意: PyInstaller只能构建当前操作系统的可执行文件。")
    print(f"当前系统是 {current_os.capitalize()}，因此只能构建 {current_os.capitalize()} 版本。")
    print("如需构建其他平台的可执行文件，请在相应的操作系统上运行此脚本。\n")
    
    # 只构建当前平台
    print(f"=== 开始构建 {current_os.capitalize()} 版本 ===")
    output_dir = package_app(current_os)
    
    if output_dir:
        print(f"\n=== 构建完成 ===")
        print(f"{current_os.capitalize()} 版本: {output_dir}")
    else:
        print("\n=== 构建失败 ===")


if __name__ == "__main__":
    # 显示跨平台构建限制信息
    print("\n=== Vortex Launcher 构建工具 ===")
    print("注意: PyInstaller只能构建当前操作系统的可执行文件。")
    print("如需构建其他平台的可执行文件，请在相应的操作系统上运行此脚本。\n")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target in ["windows", "win", "w"]:
            package_app("windows")
        elif target in ["macos", "mac", "m", "darwin"]:
            package_app("macos")
        elif target in ["linux", "l"]:
            package_app("linux")
        elif target in ["all", "a"]:
            build_all()
        else:
            print(f"不支持的目标系统: {target}")
            print("用法: python build.py [windows|macos|linux|all]")
    else:
        # 默认构建当前系统版本
        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "macos"
        elif current_os == "windows":
            current_os = "windows"
        elif current_os == "linux":
            current_os = "linux"
        else:
            print(f"不支持的操作系统: {current_os}")
            sys.exit(1)
        
        package_app(current_os)

