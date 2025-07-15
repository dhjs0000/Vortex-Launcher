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
    parser.add_argument('--version', '-v', action='version', version='Vortex-Launcher Beta 1.1.0')
    
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
    
    # 创建QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Vortex-Launcher")
    app.setApplicationVersion("Beta 1.1.0")
    
    # 创建Blender管理器
    blender_manager = BlenderManager(config, log_manager.get_logger("BlenderManager", "vortex"))
    
    # 创建主窗口
    window = MainWindow(config, log_manager, blender_manager)
    window.show()
    
    # 运行应用
    exit_code = app.exec()
    
    # 保存配置
    config['blender_paths'] = blender_manager.blender_paths
    write_json_file(args.config, config)
    
    # 压缩旧日志文件
    log_manager.compress_old_logs()
    
    logger.info(f"Vortex-Launcher 退出，退出码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 