#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - Blender管理模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import shutil
import subprocess
import logging


class BlenderManager:
    """Blender管理器"""
    
    def __init__(self, config=None, logger=None):
        self.config = config or {}
        self.blender_paths = self.config.get('blender_paths', [])
        self.logger = logger or logging.getLogger("BlenderManager")
    
    def get_blender_version(self, blender_path):
        """获取Blender版本信息
        
        Args:
            blender_path: Blender安装路径
            
        Returns:
            str: Blender版本号，如果无法获取则返回文件夹名
        """
        try:
            blender_exe = os.path.join(blender_path, "blender.exe")
            if not os.path.exists(blender_exe):
                self.logger.warning(f"找不到blender.exe: {blender_exe}")
                return os.path.basename(blender_path)
            
            # 调用blender -v获取版本信息
            result = subprocess.run(
                [blender_exe, "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 解析输出获取版本号
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                if "Blender" in version_line:
                    # 通常格式为: "Blender 3.6.0"
                    return version_line.strip()
                self.logger.warning(f"无法从输出中解析Blender版本: {version_line}")
            else:
                self.logger.warning(f"获取Blender版本失败: {result.stderr}")
            
            return os.path.basename(blender_path)
        except Exception as e:
            self.logger.error(f"获取Blender版本时出错: {str(e)}")
            return os.path.basename(blender_path)
    
    def add_blender(self, blender_path):
        """添加Blender路径
        
        Args:
            blender_path: Blender安装路径
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 规范化路径
            blender_path = os.path.normpath(blender_path)
            
            # 检查是否已存在
            if blender_path in self.blender_paths:
                self.logger.info(f"Blender路径已存在: {blender_path}")
                return False, "该Blender路径已存在"
            
            # 检查是否是有效的Blender目录
            blender_exe = os.path.join(blender_path, "blender.exe")
            if not os.path.exists(blender_exe):
                self.logger.warning(f"无效的Blender目录: {blender_path}")
                return False, "所选目录不是有效的Blender安装目录"
            
            # 添加到列表
            self.blender_paths.append(blender_path)
            self.logger.info(f"添加Blender路径: {blender_path}")
            return True, "成功添加Blender路径"
        except Exception as e:
            self.logger.error(f"添加Blender路径时出错: {str(e)}")
            return False, f"添加失败: {str(e)}"
    
    def remove_blender(self, index):
        """删除Blender路径
        
        Args:
            index: 要删除的Blender索引
            
        Returns:
            bool: 是否成功删除
        """
        try:
            if 0 <= index < len(self.blender_paths):
                path = self.blender_paths[index]
                del self.blender_paths[index]
                self.logger.info(f"删除Blender路径: {path}")
                return True, "成功删除Blender路径"
            else:
                self.logger.warning(f"尝试删除无效的Blender索引: {index}")
                return False, "无效的Blender索引"
        except Exception as e:
            self.logger.error(f"删除Blender路径时出错: {str(e)}")
            return False, f"删除失败: {str(e)}"
    
    def uninstall_blender(self, index):
        """卸载Blender
        
        Args:
            index: 要卸载的Blender索引
            
        Returns:
            bool: 是否成功卸载
        """
        try:
            if 0 <= index < len(self.blender_paths):
                path = self.blender_paths[index]
                
                # 确认路径存在
                if not os.path.exists(path):
                    self.logger.warning(f"尝试卸载不存在的Blender目录: {path}")
                    del self.blender_paths[index]
                    return False, "Blender目录不存在"
                
                # 删除目录
                shutil.rmtree(path)
                del self.blender_paths[index]
                self.logger.info(f"卸载Blender: {path}")
                return True, "成功卸载Blender"
            else:
                self.logger.warning(f"尝试卸载无效的Blender索引: {index}")
                return False, "无效的Blender索引"
        except Exception as e:
            self.logger.error(f"卸载Blender时出错: {str(e)}")
            return False, f"卸载失败: {str(e)}"
    
    def launch_blender(self, index, args=None):
        """启动Blender
        
        Args:
            index: 要启动的Blender索引
            args: 附加的命令行参数
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if 0 <= index < len(self.blender_paths):
                path = self.blender_paths[index]
                blender_exe = os.path.join(path, "blender.exe")
                
                if not os.path.exists(blender_exe):
                    self.logger.warning(f"找不到blender.exe: {blender_exe}")
                    return False, "找不到blender.exe"
                
                # 准备命令行参数
                cmd = [blender_exe]
                if args:
                    cmd.extend(args)
                
                # 启动进程
                self.logger.info(f"启动Blender: {' '.join(cmd)}")
                
                # 使用Popen启动而不等待进程结束
                subprocess.Popen(cmd)
                return True, "成功启动Blender"
            else:
                self.logger.warning(f"尝试启动无效的Blender索引: {index}")
                return False, "无效的Blender索引"
        except Exception as e:
            self.logger.error(f"启动Blender时出错: {str(e)}")
            return False, f"启动失败: {str(e)}"
    
    def auto_detect_blender(self, search_dir=None):
        """自动检测Blender安装
        
        Args:
            search_dir: 搜索目录，默认为None使用配置中的目录
            
        Returns:
            list: 新添加的Blender路径列表
        """
        try:
            search_dir = search_dir or self.config.get('auto_detect_path')
            if not search_dir or not os.path.exists(search_dir):
                self.logger.warning(f"无效的自动检测目录: {search_dir}")
                return []
            
            self.logger.info(f"开始自动检测Blender: {search_dir}")
            
            # 查找目录下的所有子目录
            added_paths = []
            subdirs = [os.path.join(search_dir, d) for d in os.listdir(search_dir)
                      if os.path.isdir(os.path.join(search_dir, d))]
            
            # 检查每个子目录是否为Blender安装目录
            for subdir in subdirs:
                blender_exe = os.path.join(subdir, "blender.exe")
                if os.path.exists(blender_exe):
                    # 如果是Blender目录且不在列表中，则添加
                    if subdir not in self.blender_paths:
                        self.blender_paths.append(subdir)
                        added_paths.append(subdir)
                        self.logger.info(f"自动检测添加Blender路径: {subdir}")
            
            return added_paths
        except Exception as e:
            self.logger.error(f"自动检测Blender时出错: {str(e)}")
            return []
    
    def get_blender_info(self, index):
        """获取Blender信息
        
        Args:
            index: Blender索引
            
        Returns:
            dict: Blender信息
        """
        try:
            if 0 <= index < len(self.blender_paths):
                path = self.blender_paths[index]
                version = self.get_blender_version(path)
                return {
                    'path': path,
                    'version': version,
                    'name': os.path.basename(path),
                    'exists': os.path.exists(path)
                }
            else:
                return None
        except Exception as e:
            self.logger.error(f"获取Blender信息时出错: {str(e)}")
            return None
    
    def update_config(self):
        """更新配置
        
        Returns:
            dict: 更新后的配置
        """
        self.config['blender_paths'] = self.blender_paths
        return self.config


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("test")
    
    # 创建Blender管理器
    manager = BlenderManager(logger=logger)
    
    # 测试添加
    success, message = manager.add_blender("D:\\Blender")
    print(f"添加结果: {success}, {message}")
    
    # 测试启动
    if success:
        success, message = manager.launch_blender(0)
        print(f"启动结果: {success}, {message}") 