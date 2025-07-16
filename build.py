import os
import shutil
import subprocess
from datetime import datetime
import re

def package_app():
    # 生成日期格式的构建目录
    build_date = datetime.now().strftime("%y-%m-%d %H-%M-%S")
    output_dir = os.path.join("build", build_date)
    
    # 清理历史构建文件（保留其他日期目录）
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 使用PyInstaller打包
    cmd = [
    "pyinstaller",
    "-D",
    "main.py",
    "-n", "Vortex Luncher",
    "--noconsole",
    "--icon", "../../webside/images/logo.ico",
    "--distpath", output_dir,
    "--workpath", os.path.join(output_dir, "temp"),
    "--specpath", output_dir,
    "--hidden-import", "requests",
    "--hidden-import", "bs4",
    "--collect-all", "PyQt6",
    "--collect-all", "PyQt6-Qt6"
    ]
    
    # 执行打包命令
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 输出构建日志
    with open(os.path.join(output_dir, "build_log.txt"), "w") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)
    
    # 清理临时文件
    temp_dir = os.path.join(output_dir, "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # 删除.spec文件
    spec_file = os.path.join(output_dir, "main.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    print(f"打包完成，输出目录：{output_dir}")

if __name__ == "__main__":
    package_app()