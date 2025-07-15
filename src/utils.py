#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 通用工具模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import json
import shutil
import tempfile
import platform
import subprocess


def read_json_file(file_path, default=None):
    """读取JSON文件
    
    Args:
        file_path: 文件路径
        default: 默认值，如果文件不存在或读取出错
        
    Returns:
        dict: JSON数据
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"读取JSON文件出错: {str(e)}")
    
    return default or {}


def write_json_file(file_path, data):
    """写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        
    Returns:
        bool: 是否成功
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"写入JSON文件出错: {str(e)}")
        return False


def get_system_info():
    """获取系统信息
    
    Returns:
        dict: 系统信息
    """
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'executable': sys.executable
    }
    
    return info


def open_directory(path):
    """打开文件夹
    
    Args:
        path: 文件夹路径
        
    Returns:
        bool: 是否成功打开
    """
    try:
        if os.path.exists(path):
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
            return True
        return False
    except Exception as e:
        print(f"打开文件夹出错: {str(e)}")
        return False


def create_backup(file_path, backup_dir=None):
    """创建文件备份
    
    Args:
        file_path: 要备份的文件路径
        backup_dir: 备份目录，默认为None使用临时目录
        
    Returns:
        str: 备份文件路径，失败则返回None
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        # 如果没有指定备份目录，则使用临时目录
        if backup_dir is None:
            backup_dir = os.path.join(tempfile.gettempdir(), "vortex_backup")
        
        # 确保备份目录存在
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 创建备份文件名
        file_name = os.path.basename(file_path)
        import time
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_file = os.path.join(backup_dir, f"{file_name}.{timestamp}.bak")
        
        # 复制文件
        shutil.copy2(file_path, backup_file)
        
        return backup_file
    except Exception as e:
        print(f"创建备份出错: {str(e)}")
        return None


def is_admin():
    """检查是否以管理员权限运行
    
    Returns:
        bool: 是否是管理员权限
    """
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:  # Unix-like
            return os.geteuid() == 0
    except:
        return False


def get_exe_directory():
    """获取可执行文件目录
    
    Returns:
        str: 可执行文件目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包的情况
        return os.path.dirname(sys.executable)
    else:
        # 脚本运行的情况
        return os.path.dirname(os.path.abspath(__file__))


def ensure_directory(directory):
    """确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 是否成功创建
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        print(f"创建目录出错: {str(e)}")
        return False


# 测试代码
if __name__ == "__main__":
    # 测试系统信息
    info = get_system_info()
    print(json.dumps(info, indent=4, ensure_ascii=False))
    
    # 测试目录创建
    test_dir = "test_dir"
    if ensure_directory(test_dir):
        print(f"成功创建目录: {test_dir}")
    
    # 测试JSON读写
    test_data = {"name": "测试", "version": 1}
    test_file = os.path.join(test_dir, "test.json")
    
    if write_json_file(test_file, test_data):
        print(f"成功写入JSON文件: {test_file}")
    
    read_data = read_json_file(test_file)
    print(f"读取JSON文件: {read_data}")
    
    # 测试备份
    backup_file = create_backup(test_file)
    if backup_file:
        print(f"成功创建备份: {backup_file}")
    
    # 清理测试文件
    shutil.rmtree(test_dir, ignore_errors=True) 