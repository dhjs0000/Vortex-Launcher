import os
import shutil
import subprocess
from datetime import datetime
import re

def package_app():
    # 生成日期格式的构建目录
    build_date = datetime.now().strftime("%y-%m-%d")
    output_dir = os.path.join("build", build_date)
    
    # 清理历史构建文件（保留其他日期目录）
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build") and not os.path.exists(output_dir):
        # 仅删除build目录下的非日期文件夹
        for item in os.listdir("build"):
            path = os.path.join("build", item)
            if os.path.isdir(path) and not re.match(r"\d{2}-\d{2}-\d{2}", item):
                shutil.rmtree(path)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 使用PyInstaller打包
    cmd = [
        "pyinstaller",
        "-D",  # 生成目录而不是单文件
        "main.py",
        "-n", "Vortex Luncher",
        "--noconsole",
        "--icon", "webside/images/logo.png",
        "--distpath", output_dir,
        "--workpath", os.path.join(output_dir, "temp"),
        "--specpath", output_dir
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