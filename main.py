#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - Blender版本管理器
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

## 测试用代码
import os, sys
from PyQt6.QtCore import QLibraryInfo, qVersion, PYQT_VERSION_STR
import PyInstaller

plugin_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
print("Qt plugin path:", plugin_path)

# 如果打包后路径变了，手动加
if hasattr(sys, "_MEIPASS"):
    plugin_path = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    print("Fixed plugin path to:", plugin_path)
try:
    print("PyInstaller version:", PyInstaller.__version__)
except ImportError:
    print("PyInstaller not found")

# Print PyQt6 version
print("PyQt6 version:", qVersion())

# Print PyQt6-Qt6 version
print("PyQt6-Qt6 version:", PYQT_VERSION_STR)


import os
import sys
import json
import argparse
from PyQt6.QtWidgets import QApplication

# 添加当前目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.log import LogManager
from src.blender_manager import BlenderManager
from src.ui import MainWindow
from src.utils import read_json_file, write_json_file, ensure_directory
import src

def parse_arguments():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="Vortex-Launcher - Blender版本管理器")
    parser.add_argument('--config', '-c', help='配置文件路径', default='config.json')
    parser.add_argument('--log-level', '-l', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='日志级别', default='INFO')
    parser.add_argument('--version', '-v', action='version', version=f'Vortex-Launcher {src.__version__}')
    
    # CLI 模式相关参数
    parser.add_argument('--cli', action='store_true', help='以命令行模式运行，不启动图形界面')
    
    # CLI 子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='CLI命令')
    
    # list 命令 - 列出已安装的Blender版本
    list_parser = subparsers.add_parser('list', help='列出已安装的Blender版本')
    
    # run 命令 - 启动指定的Blender版本
    run_parser = subparsers.add_parser('run', help='启动指定的Blender版本')
    run_parser.add_argument('index', type=int, help='Blender版本索引（从0开始）')
    run_parser.add_argument('--args', help='传递给Blender的额外参数')
    
    # list-available 命令 - 列出可下载的Blender版本
    list_available_parser = subparsers.add_parser('list-available', help='列出可下载的Blender版本')
    
    # download 命令 - 下载指定的Blender版本
    download_parser = subparsers.add_parser('download', help='下载指定的Blender版本')
    download_parser.add_argument('version', help='要下载的Blender版本号')
    
    # add 命令 - 添加本地Blender路径
    add_parser = subparsers.add_parser('add', help='添加本地Blender路径')
    add_parser.add_argument('path', help='Blender安装路径')
    
    # remove 命令 - 移除已添加的Blender
    remove_parser = subparsers.add_parser('remove', help='移除已添加的Blender')
    remove_parser.add_argument('index', type=int, help='要移除的Blender索引（从0开始）')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 加载配置
    config = read_json_file(args.config, default={})
    
    # 确保日志目录存在
    log_config = config.get('log_config', {})
    log_dir = log_config.get('log_dir', 'logs')
    ensure_directory(log_dir)
    
    # 创建日志管理器
    log_manager = LogManager(log_config)
    
    # 获取程序日志记录器
    logger = log_manager.get_logger("VortexLauncher", "vortex")
    logger.info("Vortex-Launcher 启动")
    
    # 命令行模式
    if args.cli:
        logger.info("以命令行模式运行")
        
        # 如果没有指定命令，显示帮助
        if not args.command:
            print("错误: 请指定要执行的命令。使用 --help 查看帮助。")
            return 1
        
        # 导入CLI模块并执行命令
        from src.cli import CLI
        cli = CLI(config, log_manager)
        
        try:
            exit_code = cli.execute(args)
        except Exception as e:
            logger.error(f"执行命令时出错: {str(e)}")
            print(f"错误: {str(e)}")
            exit_code = 1
        
        # 保存配置
        config['blender_paths'] = cli.blender_manager.blender_paths
        write_json_file(args.config, config)
        
        # 保存使用时长数据
        logger.info("保存使用时长统计数据")
        cli.blender_manager.usage_tracker.save_usage_data()
        
        # 压缩旧日志文件
        log_manager.compress_old_logs()
        
        logger.info(f"Vortex-Launcher CLI 退出，退出码: {exit_code}")
        return exit_code
    
    # 图形界面模式
    else:
        logger.info("以图形界面模式运行")
        
        # 创建QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Vortex-Launcher")
        app.setApplicationVersion(src.__version__)
        
        # 显示启动界面
        from src.ui import LaunchingDialog
        splash = LaunchingDialog()
        splash.show()
        
        # 处理事件，确保界面显示
        app.processEvents()
        
        # 更新启动进度
        splash.set_progress(10, "正在加载配置...")
        app.processEvents()
        
        # 创建Blender管理器
        splash.set_progress(30, "正在初始化Blender管理器...")
        app.processEvents()
        blender_manager = BlenderManager(config, log_manager.get_logger("BlenderManager", "vortex"))
        
        # 创建下载管理器
        splash.set_progress(50, "正在初始化下载管理器...")
        app.processEvents()
        
        # 准备创建主窗口
        splash.set_progress(70, "正在初始化用户界面...")
        app.processEvents()

        # 创建主窗口
        window = MainWindow(config, log_manager, blender_manager)
        
        # 完成启动
        splash.set_progress(100, "启动完成!")
        app.processEvents()
        
        # 关闭启动画面，显示主窗口
        splash.accept()
        window.show()
        
        # 运行应用
        exit_code = app.exec()
        
        # 保存配置
        config['blender_paths'] = blender_manager.blender_paths
        write_json_file(args.config, config)
        
        # 保存使用时长数据
        logger.info("保存使用时长统计数据")
        blender_manager.usage_tracker.save_usage_data()
        
        # 压缩旧日志文件
        log_manager.compress_old_logs()
        
        logger.info(f"Vortex-Launcher GUI 退出，退出码: {exit_code}")
        return exit_code


if __name__ == "__main__":
    sys.exit(main()) 
