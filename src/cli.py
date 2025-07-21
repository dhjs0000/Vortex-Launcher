#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 命令行界面模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import time
import logging
from .utils import read_json_file, write_json_file
from .blender_manager import BlenderManager
from .download_manager import DownloadManager

class CLI:
    """命令行界面处理类"""
    
    def __init__(self, config, log_manager):
        """初始化CLI
        
        Args:
            config: 配置字典
            log_manager: 日志管理器
        """
        self.config = config
        self.log_manager = log_manager
        self.logger = log_manager.get_logger("CLI", "vortex")
        
        # 创建Blender管理器
        self.logger.info("正在初始化Blender管理器...")
        self.blender_manager = BlenderManager(config, log_manager.get_logger("BlenderManager", "vortex"))
        
        # 创建下载管理器
        self.logger.info("正在初始化下载管理器...")
        self.download_manager = DownloadManager(config, log_manager.get_logger("DownloadManager", "vortex"))
    
    def execute(self, args):
        """执行命令行命令
        
        Args:
            args: 解析后的命令行参数
            
        Returns:
            int: 退出码
        """
        # 根据命令执行相应操作
        if args.command == 'list':
            return self.list_blender()
        elif args.command == 'run':
            return self.run_blender(args.index, args.args)
        elif args.command == 'list-available':
            return self.list_available()
        elif args.command == 'download':
            return self.download_blender(args.version)
        elif args.command == 'add':
            return self.add_blender(args.path)
        elif args.command == 'remove':
            return self.remove_blender(args.index)
        else:
            self.logger.error(f"未知命令: {args.command}")
            print("错误: 未知命令。请使用 --help 查看帮助。")
            return 1
    
    def list_blender(self):
        """列出已安装的Blender版本
        
        Returns:
            int: 退出码
        """
        self.logger.info("列出已安装的Blender版本")
        
        if not self.blender_manager.blender_paths:
            print("未找到已安装的Blender版本")
            return 0
        
        print("已安装的Blender版本:")
        print("-" * 60)
        print(f"{'索引':^5} | {'版本':^15} | {'路径'}")
        print("-" * 60)
        
        for i, path in enumerate(self.blender_manager.blender_paths):
            info = self.blender_manager.get_blender_info(i)
            version = info.get('version', '未知') if info else '未知'
            print(f"{i:^5} | {version:^15} | {path}")
        
        return 0
    
    def run_blender(self, index, args_str=None):
        """启动指定的Blender版本
        
        Args:
            index: Blender版本索引
            args_str: 传递给Blender的额外参数
            
        Returns:
            int: 退出码
        """
        self.logger.info(f"启动Blender，索引: {index}，参数: {args_str}")
        
        # 检查索引是否有效
        if index < 0 or index >= len(self.blender_manager.blender_paths):
            self.logger.error(f"无效的Blender索引: {index}")
            print(f"错误: 索引 {index} 超出范围，请使用 'list' 命令查看可用的版本")
            return 1
        
        # 解析参数
        args = None
        if args_str:
            import shlex
            try:
                args = shlex.split(args_str)
                self.logger.info(f"解析额外参数: {args}")
            except Exception as e:
                self.logger.warning(f"解析参数时出错: {str(e)}")
                print(f"警告: 解析参数时出错: {str(e)}")
        
        # 启动Blender
        success, message = self.blender_manager.launch_blender(index, args, capture_output=False)
        
        if not success:
            self.logger.error(f"启动Blender失败: {message}")
            print(f"错误: {message}")
            return 1
        
        print(f"已成功启动Blender，路径: {self.blender_manager.blender_paths[index]}")
        return 0
    
    def list_available(self):
        """列出可下载的Blender版本
        
        Returns:
            int: 退出码
        """
        self.logger.info("列出可下载的Blender版本")
        print("正在获取可下载的Blender版本列表...")
        
        # 获取版本列表
        versions = self.download_manager.get_available_versions()
        
        if not versions:
            print("未找到可下载的Blender版本")
            return 1
        
        # 显示版本列表
        print(f"找到 {len(versions)} 个可下载的Blender版本:")
        print("-" * 70)
        print(f"{'版本':^10} | {'构建日期':^15} | {'大小':^10} | {'描述'}")
        print("-" * 70)
        
        for i, version in enumerate(versions):
            print(f"{version.version:^10} | {version.build_date or '未知':^15} | {version.size or '未知':^10} | {version.description or ''}")
        
        return 0
    
    def download_blender(self, version):
        """下载指定的Blender版本
        
        Args:
            version: 要下载的版本号
            
        Returns:
            int: 退出码
        """
        self.logger.info(f"下载Blender版本: {version}")
        print(f"正在查找Blender版本: {version}...")
        
        # 获取版本列表
        versions = self.download_manager.get_available_versions()
        
        if not versions:
            print("未找到可下载的Blender版本")
            return 1
        
        # 查找指定版本
        version_info = None
        for v in versions:
            if v.version == version:
                version_info = v
                break
        
        if not version_info:
            self.logger.error(f"未找到版本: {version}")
            print(f"错误: 未找到版本 {version}，请使用 'list-available' 命令查看可用版本")
            return 1
        
        # 开始下载
        print(f"开始下载 Blender {version_info.version}...")
        download_id = self.download_manager.download_blender(version_info)
        
        if not download_id:
            self.logger.error("下载失败")
            print("错误: 下载失败，请检查日志获取详细信息")
            return 1
        
        # 等待下载完成
        last_progress = 0
        download_info = self.download_manager.current_downloads.get(download_id)
        
        if not download_info:
            self.logger.error("无法获取下载信息")
            print("错误: 无法获取下载信息")
            return 1
        
        save_path = download_info['save_path']
        
        print("下载进度: 0%")
        
        # 监控下载进度
        while download_id in self.download_manager.current_downloads:
            time.sleep(1)
            
            # 检查是否已经下载完成
            if not os.path.exists(f"{save_path}.part"):
                break
            
            # 获取当前文件大小
            try:
                current_size = os.path.getsize(f"{save_path}.part")
                if version_info.size:
                    # 尝试将大小转换为字节
                    import re
                    size_match = re.search(r'(\d+\.?\d*)\s*([KMG]B)', version_info.size)
                    if size_match:
                        size_val = float(size_match.group(1))
                        unit = size_match.group(2)
                        
                        if unit == 'KB':
                            total_size = size_val * 1024
                        elif unit == 'MB':
                            total_size = size_val * 1024 * 1024
                        elif unit == 'GB':
                            total_size = size_val * 1024 * 1024 * 1024
                        else:
                            total_size = 0
                        
                        if total_size > 0:
                            progress = int(current_size / total_size * 100)
                            if progress > last_progress + 5:
                                last_progress = progress
                                print(f"下载进度: {progress}%")
            except Exception as e:
                self.logger.warning(f"获取下载进度时出错: {str(e)}")
        
        # 检查下载结果
        if not os.path.exists(save_path):
            self.logger.error("下载失败")
            print("错误: 下载失败，请检查日志获取详细信息")
            return 1
        
        print(f"Blender {version} 下载完成: {save_path}")
        
        # 解压文件
        print("正在解压文件...")
        blender_dir = self.download_manager.extract_blender(save_path)
        
        if not blender_dir:
            self.logger.error("解压失败")
            print("错误: 解压失败，请检查日志获取详细信息")
            return 1
        
        # 添加到Blender列表
        success, message = self.blender_manager.add_blender(blender_dir)
        
        if not success:
            self.logger.error(f"添加Blender失败: {message}")
            print(f"警告: 添加Blender到列表失败: {message}")
        else:
            print(f"已将 Blender {version} 添加到列表")
        
        return 0
    
    def add_blender(self, path):
        """添加本地Blender路径
        
        Args:
            path: Blender安装路径
            
        Returns:
            int: 退出码
        """
        self.logger.info(f"添加Blender路径: {path}")
        
        # 检查路径是否存在
        if not os.path.exists(path):
            self.logger.error(f"路径不存在: {path}")
            print(f"错误: 路径不存在: {path}")
            return 1
        
        # 添加到Blender列表
        success, message = self.blender_manager.add_blender(path)
        
        if not success:
            self.logger.error(f"添加Blender失败: {message}")
            print(f"错误: {message}")
            return 1
        
        # 保存配置
        self.config['blender_paths'] = self.blender_manager.blender_paths
        write_json_file('config.json', self.config)
        
        print(f"已成功添加Blender路径: {path}")
        return 0
    
    def remove_blender(self, index):
        """移除已添加的Blender
        
        Args:
            index: 要移除的Blender索引
            
        Returns:
            int: 退出码
        """
        self.logger.info(f"移除Blender，索引: {index}")
        
        # 检查索引是否有效
        if index < 0 or index >= len(self.blender_manager.blender_paths):
            self.logger.error(f"无效的Blender索引: {index}")
            print(f"错误: 索引 {index} 超出范围，请使用 'list' 命令查看可用的版本")
            return 1
        
        # 获取路径
        path = self.blender_manager.blender_paths[index]
        
        # 移除Blender
        self.blender_manager.blender_paths.pop(index)
        
        # 保存配置
        self.config['blender_paths'] = self.blender_manager.blender_paths
        write_json_file('config.json', self.config)
        
        print(f"已成功移除Blender路径: {path}")
        return 0 