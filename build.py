import os
import shutil
import subprocess
from datetime import datetime
import re
import sys
import platform
import src

Suffix = None

if src.__channel__ != "Release":
    Suffix = f"({src.__channel__})"
else:
    Suffix = ""

# 应用名称
app_name = f"Vortex Luncher{Suffix}"

def package_app(target_os=None):
    """
    打包应用程序
    
    Args:
        target_os: 目标操作系统，可以是 'windows', 'macos', 'linux' 或 None (当前系统)
    """
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
        shutil.copytree(thirdparty_dir, os.path.join(f"output_dir\\{current_os}\\{app_name}", "licenses"))
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
        "-D",  # 创建一个目录而不是单个文件
        "main.py",
        "-n", app_name,
        "--icon", icon_path,
        "--distpath", output_subdir,
        "--workpath", os.path.join(output_dir, f"temp_{target_os}"),
        "--specpath", output_dir,
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "--hidden-import", "psutil"
    ]
    
    # 添加特定于操作系统的参数
    cmd.extend(os_specific_args)
    
    # 执行打包命令
    print(f"开始为 {target_os} 构建...")
    result = subprocess.run(cmd, text=True)
    
    # 输出构建日志
    log_file = os.path.join(output_subdir, f"build_log_{target_os}.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout or "")
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr or "")
    
    # 清理临时文件
    temp_dir = os.path.join(output_dir, f"temp_{target_os}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # 删除.spec文件
    spec_file = os.path.join(output_dir, f"{app_name}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    print(f"{target_os} 构建完成，输出目录：{output_subdir}")
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

