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
import threading


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
    
    def launch_blender(self, index, args=None, capture_output=True):
        """启动Blender
        
        Args:
            index: 要启动的Blender索引
            args: 附加的命令行参数
            capture_output: 是否捕获输出用于日志
            
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
                
                # 使用不同方式启动Blender
                if capture_output:
                    # 捕获标准输出和标准错误
                    self.logger.info("启动Blender（捕获输出）...")
                    
                    # 直接创建进程，而不是在线程中创建
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=1,  # 行缓冲
                        universal_newlines=False,  # 使用二进制模式，我们会在_capture_output中处理编码
                        creationflags=subprocess.CREATE_NO_WINDOW  # 不显示控制台窗口
                    )
                    
                    # 存储进程对象
                    if not hasattr(self, '_processes'):
                        self._processes = {}
                    self._processes[index] = process
                    
                    self.logger.info(f"已创建进程，PID: {process.pid}")
                    
                    # 使用子线程读取输出
                    thread = threading.Thread(
                        target=self._capture_output,
                        args=(process, index),
                        daemon=True
                    )
                    thread.start()
                    
                    # 等待线程启动
                    import time
                    time.sleep(0.1)
                    
                else:
                    # 不捕获输出，直接启动
                    self.logger.info("启动Blender（不捕获输出）...")
                    process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NO_WINDOW  # 不显示控制台窗口
                    )
                    # 存储进程对象
                    if not hasattr(self, '_processes'):
                        self._processes = {}
                    self._processes[index] = process
                    
                    self.logger.info(f"已创建进程，PID: {process.pid}")
                
                return True, "成功启动Blender"
            else:
                self.logger.warning(f"尝试启动无效的Blender索引: {index}")
                return False, "无效的Blender索引"
        except Exception as e:
            self.logger.error(f"启动Blender时出错: {str(e)}")
            return False, f"启动失败: {str(e)}"
    
    def get_running_process(self, index):
        """获取正在运行的Blender进程
        
        Args:
            index: Blender索引
            
        Returns:
            subprocess.Popen: 进程对象，如果不存在则返回None
        """
        if hasattr(self, '_processes') and index in self._processes:
            process = self._processes[index]
            # 检查进程是否仍在运行
            if process.poll() is None:
                return process
            else:
                # 进程已结束，清理
                del self._processes[index]
        return None
    
    def _run_with_output_capture(self, cmd, index):
        """在子线程中运行进程并捕获输出
        
        Args:
            cmd: 命令行参数列表
            index: Blender索引
        """
        import threading
        
        try:
            # 创建日志记录器
            blender_logger = None
            combined_logger = None
            
            # 获取BlenderManager的日志处理器
            if hasattr(self.logger, 'parent'):
                logger_parent = self.logger.parent
                if hasattr(logger_parent, 'handlers'):
                    # 创建特定的日志记录器
                    import logging
                    
                    # Blender专用日志记录器
                    blender_logger = logging.getLogger(f"Blender_{index}")
                    blender_logger.setLevel(logging.DEBUG)
                    
                    # 清除已有的处理器
                    if blender_logger.hasHandlers():
                        for handler in blender_logger.handlers[:]:
                            blender_logger.removeHandler(handler)
                    
                    # 添加处理器
                    for handler in logger_parent.handlers:
                        if isinstance(handler, logging.FileHandler):
                            # 为Blender创建新的日志文件
                            log_dir = os.path.dirname(handler.baseFilename)
                            if not os.path.exists(log_dir):
                                os.makedirs(log_dir)
                            
                            # 创建时间戳
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
                            
                            # 创建Blender专用日志文件
                            blender_log_file = os.path.join(log_dir, f"blender-{timestamp}.log")
                            blender_handler = logging.FileHandler(blender_log_file, encoding='utf-8')
                            blender_formatter = logging.Formatter(
                                '%(asctime)s [Blender] [%(levelname)s] %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S'
                            )
                            blender_handler.setFormatter(blender_formatter)
                            blender_logger.addHandler(blender_handler)
                            
                            # 创建组合日志文件
                            combined_log_file = os.path.join(log_dir, f"combined-{timestamp}.log")
                            combined_logger = logging.getLogger(f"Combined_{index}")
                            combined_logger.setLevel(logging.DEBUG)
                            
                            # 清除已有的处理器
                            if combined_logger.hasHandlers():
                                for handler in combined_logger.handlers[:]:
                                    combined_logger.removeHandler(handler)
                            
                            # 添加组合日志处理器
                            combined_handler = logging.FileHandler(combined_log_file, encoding='utf-8')
                            combined_formatter = logging.Formatter(
                                '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S'
                            )
                            combined_handler.setFormatter(combined_formatter)
                            combined_logger.addHandler(combined_handler)
                            
                            break
            
            # 启动进程，捕获输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8'  # 明确指定UTF-8编码
            )
            
            # 存储进程对象
            if not hasattr(self, '_processes'):
                self._processes = {}
            self._processes[index] = process
            
            # 读取输出
            for line in process.stdout:
                line = line.strip()
                if line:
                    # 记录到Blender日志
                    if blender_logger:
                        if "error" in line.lower():
                            blender_logger.error(line)
                            if combined_logger:
                                combined_logger.error(f"[Blender] {line}")
                        elif "warning" in line.lower():
                            blender_logger.warning(line)
                            if combined_logger:
                                combined_logger.warning(f"[Blender] {line}")
                        else:
                            blender_logger.info(line)
                            if combined_logger:
                                combined_logger.info(f"[Blender] {line}")
                    else:
                        # 如果没有特定的日志记录器，使用常规记录器
                        self.logger.info(f"[Blender输出] {line}")
            
            # 等待进程结束
            process.wait()
            
            # 清理进程引用
            if hasattr(self, '_processes') and index in self._processes:
                del self._processes[index]
            
        except Exception as e:
            self.logger.error(f"捕获Blender输出时出错: {str(e)}")
            
            # 确保进程终止
            if 'process' in locals():
                try:
                    process.terminate()
                except:
                    pass
                
                # 清理进程引用
                if hasattr(self, '_processes') and index in self._processes:
                    del self._processes[index]
    
    def _capture_output(self, process, index):
        """在子线程中捕获进程输出
        
        Args:
            process: 进程对象
            index: Blender索引
        """
        try:
            # 创建日志记录器
            blender_logger = None
            combined_logger = None
            
            # 创建特定的日志记录器
            import logging
            import datetime
            
            # 确保日志目录存在
            log_dir = "logs"
            if hasattr(self.logger, 'parent') and self.logger.parent:
                for handler in self.logger.parent.handlers:
                    if isinstance(handler, logging.FileHandler):
                        log_dir = os.path.dirname(handler.baseFilename)
                        break
            
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 创建时间戳
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
            
            # 创建Blender专用日志文件
            blender_log_file = os.path.join(log_dir, f"blender-{timestamp}.log")
            blender_logger = logging.getLogger(f"Blender_{index}")
            blender_logger.setLevel(logging.DEBUG)
            
            # 清除已有的处理器
            if blender_logger.hasHandlers():
                for handler in blender_logger.handlers[:]:
                    blender_logger.removeHandler(handler)
            
            # 添加文件处理器
            blender_handler = logging.FileHandler(blender_log_file, encoding='utf-8', mode='w')
            blender_formatter = logging.Formatter(
                '%(asctime)s [Blender] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            blender_handler.setFormatter(blender_formatter)
            blender_logger.addHandler(blender_handler)
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(blender_formatter)
            blender_logger.addHandler(console_handler)
            
            # 创建组合日志文件
            combined_log_file = os.path.join(log_dir, f"combined-{timestamp}.log")
            combined_logger = logging.getLogger(f"Combined_{index}")
            combined_logger.setLevel(logging.DEBUG)
            
            # 清除已有的处理器
            if combined_logger.hasHandlers():
                for handler in combined_logger.handlers[:]:
                    combined_logger.removeHandler(handler)
            
            # 添加组合日志处理器
            combined_handler = logging.FileHandler(combined_log_file, encoding='utf-8', mode='w')
            combined_formatter = logging.Formatter(
                '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            combined_handler.setFormatter(combined_formatter)
            combined_logger.addHandler(combined_handler)
            
            self.logger.info(f"已创建Blender日志文件: {blender_log_file}")
            self.logger.info(f"已创建组合日志文件: {combined_log_file}")
            
            # 记录开始读取日志
            self.logger.info(f"开始捕获Blender输出 (索引: {index}, PID: {process.pid})")
            blender_logger.info(f"开始捕获Blender输出 (PID: {process.pid})")
            
            # 尝试直接读取输出流，使用多种编码
            encodings = ['utf-8', 'gbk', 'latin-1', 'cp936']
            lines_read = 0
            
            # 尝试不同的读取方法
            try:
                self.logger.info(f"尝试使用方法1读取Blender输出流")
                
                import io
                import time
                
                # 为了更可靠地读取输出，使用一个缓冲区
                buffer = b''
                
                # 直接读取原始字节流
                if hasattr(process.stdout, 'buffer'):
                    stdout_buffer = process.stdout.buffer
                else:
                    # 如果没有buffer属性，可能已经是二进制模式
                    stdout_buffer = process.stdout
                
                while process.poll() is None:  # 只要进程在运行
                    # 读取一部分数据
                    try:
                        chunk = stdout_buffer.read(1024)
                        if not chunk:  # 如果没有数据，等待一下再继续
                            time.sleep(0.1)
                            continue
                            
                        buffer += chunk
                        
                        # 检查是否有完整的行
                        while b'\n' in buffer:
                            # 获取一行数据
                            line_bytes, buffer = buffer.split(b'\n', 1)
                            
                            # 尝试不同编码解码
                            decoded_line = None
                            last_error = None
                            
                            for encoding in encodings:
                                try:
                                    decoded_line = line_bytes.decode(encoding).strip()
                                    self.logger.debug(f"成功使用{encoding}解码")
                                    break
                                except UnicodeDecodeError as e:
                                    last_error = e
                                    continue
                            
                            # 如果所有编码都失败，使用latin-1作为后备
                            if decoded_line is None:
                                self.logger.warning(f"所有编码解析失败，使用latin-1替代: {str(last_error)}")
                                decoded_line = line_bytes.decode('latin-1', errors='replace').strip()
                            
                            if decoded_line:
                                lines_read += 1
                                # 记录到Blender日志
                                if "error" in decoded_line.lower():
                                    blender_logger.error(decoded_line)
                                    if combined_logger:
                                        combined_logger.error(f"[Blender] {decoded_line}")
                                elif "warning" in decoded_line.lower():
                                    blender_logger.warning(decoded_line)
                                    if combined_logger:
                                        combined_logger.warning(f"[Blender] {decoded_line}")
                                else:
                                    blender_logger.info(decoded_line)
                                    if combined_logger:
                                        combined_logger.info(f"[Blender] {decoded_line}")
                    except Exception as read_error:
                        self.logger.warning(f"读取输出时出错: {str(read_error)}")
                        time.sleep(0.1)
                
                # 处理剩余的缓冲区
                if buffer:
                    decoded_line = None
                    for encoding in encodings:
                        try:
                            decoded_line = buffer.decode(encoding).strip()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if decoded_line is None:
                        decoded_line = buffer.decode('latin-1', errors='replace').strip()
                    
                    if decoded_line:
                        lines_read += 1
                        blender_logger.info(decoded_line)
                        if combined_logger:
                            combined_logger.info(f"[Blender] {decoded_line}")
                
            except Exception as e:
                self.logger.error(f"使用方法1读取Blender输出时出错: {str(e)}")
                blender_logger.error(f"使用方法1读取Blender输出时出错: {str(e)}")
                
                # 方法2：尝试使用readlines方法
                self.logger.info("切换到备用方法2读取Blender输出")
                blender_logger.info("切换到备用方法2读取Blender输出")
                
                try:
                    # 确保stdout已经初始化
                    if process.stdout and not process.stdout.closed:
                        for line in iter(process.stdout.readline, ''):
                            if not line:
                                break
                                
                            if isinstance(line, bytes):
                                # 尝试不同编码
                                decoded_line = None
                                for encoding in encodings:
                                    try:
                                        decoded_line = line.decode(encoding).strip()
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                if decoded_line is None:
                                    # 如果所有编码都失败，使用latin-1作为后备
                                    decoded_line = line.decode('latin-1', errors='replace').strip()
                            else:
                                decoded_line = line.strip()
                                
                            if decoded_line:
                                lines_read += 1
                                # 记录到Blender日志
                                if "error" in decoded_line.lower():
                                    blender_logger.error(decoded_line)
                                    if combined_logger:
                                        combined_logger.error(f"[Blender] {decoded_line}")
                                elif "warning" in decoded_line.lower():
                                    blender_logger.warning(decoded_line)
                                    if combined_logger:
                                        combined_logger.warning(f"[Blender] {decoded_line}")
                                else:
                                    blender_logger.info(decoded_line)
                                    if combined_logger:
                                        combined_logger.info(f"[Blender] {decoded_line}")
                                        
                except Exception as e2:
                    self.logger.error(f"使用方法2读取Blender输出时出错: {str(e2)}")
                    blender_logger.error(f"使用方法2读取Blender输出时出错: {str(e2)}")
                    
                    # 方法3：最后的尝试，使用communicate方法
                    self.logger.info("切换到最后方法3读取Blender输出")
                    blender_logger.info("切换到最后方法3读取Blender输出")
                    
                    try:
                        # 如果进程还在运行
                        if process.poll() is None:
                            output, error = process.communicate()
                            
                            if output:
                                # 尝试解码
                                decoded_output = None
                                for encoding in encodings:
                                    try:
                                        if isinstance(output, bytes):
                                            decoded_output = output.decode(encoding)
                                        else:
                                            decoded_output = output
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                if decoded_output is None:
                                    # 如果所有编码都失败，使用latin-1作为后备
                                    decoded_output = output.decode('latin-1', errors='replace') if isinstance(output, bytes) else output
                                
                                # 记录输出
                                for line in decoded_output.splitlines():
                                    line = line.strip()
                                    if line:
                                        lines_read += 1
                                        if "error" in line.lower():
                                            blender_logger.error(line)
                                            if combined_logger:
                                                combined_logger.error(f"[Blender] {line}")
                                        elif "warning" in line.lower():
                                            blender_logger.warning(line)
                                            if combined_logger:
                                                combined_logger.warning(f"[Blender] {line}")
                                        else:
                                            blender_logger.info(line)
                                            if combined_logger:
                                                combined_logger.info(f"[Blender] {line}")
                    except Exception as e3:
                        self.logger.error(f"使用方法3读取Blender输出时出错: {str(e3)}")
                        blender_logger.error(f"使用方法3读取Blender输出时出错: {str(e3)}")
            
            # 等待进程结束
            process.wait()
            
            # 记录进程退出信息
            exit_message = f"Blender进程已退出 (索引: {index}, 读取了{lines_read}行日志)"
            self.logger.info(exit_message)
            blender_logger.info(exit_message)
            if combined_logger:
                combined_logger.info(exit_message)
            
            # 确保日志被写入文件
            for handler in blender_logger.handlers:
                handler.flush()
            if combined_logger:
                for handler in combined_logger.handlers:
                    handler.flush()
            
            # 清理进程引用
            if hasattr(self, '_processes') and index in self._processes:
                del self._processes[index]
            
        except Exception as e:
            self.logger.error(f"捕获Blender输出时出错: {str(e)}")
            
            # 清理进程引用
            if hasattr(self, '_processes') and index in self._processes:
                del self._processes[index]
    
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