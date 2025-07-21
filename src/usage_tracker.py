#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 使用时长记录模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import json
import time
import logging
import datetime
import hashlib
import base64
import hmac
import uuid
import platform
import getpass
import shutil
from pathlib import Path
from datetime import datetime, date

class UsageTracker:
    """Blender使用时长记录类"""
    
    def __init__(self, config=None, logger=None):
        """初始化使用时长追踪器
        
        Args:
            config: 配置字典
            logger: 日志记录器
        """
        self.config = config or {}
        self.logger = logger or logging.getLogger("UsageTracker")
        
        # 创建数据目录
        try:
            # 使用记录文件路径，确保保存在用户可写的目录下
            default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
            Path(default_path).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"使用数据目录: {default_path}")
        except Exception as e:
            self.logger.error(f"创建数据目录失败: {str(e)}")
            # 尝试使用用户目录作为备用
            user_home = os.path.expanduser("~")
            default_path = os.path.join(user_home, ".vortex-launcher", "data")
            try:
                Path(default_path).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"使用备用数据目录: {default_path}")
            except Exception as e2:
                self.logger.error(f"创建备用数据目录失败: {str(e2)}")
                default_path = "."  # 最后使用当前目录
        
        self.usage_file = self.config.get('usage_file', os.path.join(default_path, 'usage_stats.json'))
        self.logger.info(f"使用统计文件路径: {self.usage_file}")
        
        # 数据验证状态
        self.verification_status = False
        
        # 生成基于硬件和系统的唯一密钥（无法跨系统伪造）
        self._secret_key = self._generate_system_bound_key()
        
        # 记录数据
        self.usage_data = {
            'total_time': 0,           # 总使用时长(秒)
            'daily_usage': {},         # 每日使用时长 {日期: 时长}
            'version_usage': {},       # 版本使用时长 {版本: 时长}
            'last_update': None,       # 最后更新时间
            'system_id': self._get_system_id(),  # 系统标识符
            'checksum': None,          # 数据校验和
        }
        
        # 当前使用会话
        self.current_sessions = {}     # {索引: {开始时间, 版本}}
        
        # 加载使用记录
        self.load_usage_data()
    
    def _get_system_id(self):
        """获取系统标识符（基于机器特性，但不包含敏感个人信息）"""
        # 使用多种系统属性创建唯一ID
        system_info = [
            platform.node(),  # 计算机网络名称
            platform.machine(),  # 机器类型
            platform.processor(),  # 处理器名称
            platform.system(),  # 操作系统名称
            str(uuid.getnode()),  # MAC地址数字表示
        ]
        # 哈希系统信息生成唯一ID
        hasher = hashlib.sha256()
        hasher.update("|".join(system_info).encode('utf-8'))
        return hasher.hexdigest()[:16]  # 取前16个字符作为ID
    
    def _generate_system_bound_key(self):
        """生成绑定到当前系统的密钥"""
        # 基本常量密钥
        base_key = "VortexLauncherStatisticsKey2025"
        
        # 系统相关信息，创建一个与系统绑定的唯一密钥
        system_info = [
            platform.system(),  # 操作系统名称
            platform.release(),  # 操作系统版本
            platform.machine(),  # 机器类型
            getpass.getuser(),  # 用户名
            str(uuid.getnode()),  # MAC地址的整数表示
            platform.processor()  # 处理器类型
        ]
        
        # 组合信息
        combined = base_key + "|" + "|".join(system_info)
        
        # 使用SHA256创建最终密钥
        hasher = hashlib.sha256()
        hasher.update(combined.encode('utf-8'))
        return hasher.hexdigest()
    
    def load_usage_data(self):
        """加载使用记录数据"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 保存原始校验和
                    original_checksum = data.get('checksum')
                    
                    # 将日期字符串转换回日期对象
                    if 'daily_usage' in data:
                        daily_usage = {}
                        for date_str, time_value in data['daily_usage'].items():
                            daily_usage[date_str] = time_value
                        data['daily_usage'] = daily_usage
                    
                    # 更新记录数据
                    self.usage_data.update(data)
                    self.logger.info(f"已加载使用记录数据: 总时长 {self.format_time(self.usage_data['total_time'])}")
                    
                    # 验证数据
                    self.verification_status = self._verify_data(original_checksum)
                    if self.verification_status:
                        self.logger.info("使用时长数据验证通过")
                    else:
                        self.logger.warning("使用时长数据验证失败，数据可能已被篡改")
            else:
                self.logger.info("使用记录文件不存在，将创建新的记录")
                # 生成第一次校验和
                self._generate_checksum()
                self.verification_status = True
        except Exception as e:
            self.logger.error(f"加载使用记录数据失败: {str(e)}")
            
    def save_usage_data(self):
        """保存使用记录数据"""
        try:
            # 更新最后更新时间
            self.usage_data['last_update'] = datetime.now().isoformat()
            
            # 更新系统ID（如果发生变化）
            current_system_id = self._get_system_id()
            if self.usage_data.get('system_id') != current_system_id:
                self.logger.info(f"系统ID已更新: {self.usage_data.get('system_id')} -> {current_system_id}")
                self.usage_data['system_id'] = current_system_id
            
            # 生成并更新校验和
            checksum = self._generate_checksum()
            if not checksum:
                self.logger.error("生成校验和失败，无法保存使用记录")
                return False
            
            # 确保目录存在
            directory = os.path.dirname(self.usage_file)
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            # 创建临时文件先写入
            temp_file = self.usage_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=4)
                
            # 确保文件写入成功后再替换
            if os.path.exists(temp_file):
                # 如果存在旧文件，尝试创建备份
                if os.path.exists(self.usage_file):
                    backup_file = self.usage_file + ".bak"
                    try:
                        shutil.copy2(self.usage_file, backup_file)
                    except Exception as e:
                        self.logger.warning(f"创建备份文件失败: {str(e)}")
                
                # 将临时文件重命名为正式文件
                os.replace(temp_file, self.usage_file)
                self.logger.info(f"已保存使用记录数据: {self.usage_file}")
                
                self.verification_status = True
                return True
            else:
                self.logger.error("临时文件创建失败，无法保存使用记录")
                return False
                
        except Exception as e:
            self.logger.error(f"保存使用记录数据失败: {str(e)}")
            # 尝试使用备用路径
            try:
                backup_path = os.path.join(os.path.expanduser("~"), ".vortex-launcher-backup.json")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.usage_data, f, ensure_ascii=False, indent=4)
                self.logger.info(f"已将使用记录数据保存到备用位置: {backup_path}")
            except Exception as e2:
                self.logger.error(f"备用保存也失败: {str(e2)}")
            return False
            
    def _generate_checksum(self):
        """生成数据校验和，使用HMAC-SHA256增强安全性"""
        try:
            # 创建数据副本并移除现有校验和
            data_copy = self.usage_data.copy()
            data_copy.pop('checksum', None)
            
            # 将数据转换为排序后的JSON字符串
            data_str = json.dumps(data_copy, sort_keys=True)
            
            # 使用标准HMAC方法生成校验和（更安全）
            digest_maker = hmac.new(
                self._secret_key.encode('utf-8'),
                data_str.encode('utf-8'),
                hashlib.sha256
            )
            checksum = base64.b64encode(digest_maker.digest()).decode('utf-8')
            
            # 更新校验和
            self.usage_data['checksum'] = checksum
            
            self.logger.debug("已生成校验和")
            return checksum
        except Exception as e:
            self.logger.error(f"生成校验和时出错: {str(e)}")
            return None
        
    def _verify_data(self, stored_checksum):
        """验证数据完整性
        
        Args:
            stored_checksum: 存储的校验和
            
        Returns:
            bool: 数据是否完整
        """
        try:
            if not stored_checksum:
                self.logger.warning("校验和为空，验证失败")
                return False
            
            # 检查系统ID是否匹配
            system_id = self.usage_data.get('system_id')
            current_system_id = self._get_system_id()
            
            if system_id != current_system_id:
                self.logger.warning(f"系统ID不匹配，可能在不同机器上加载: 存储的={system_id}, 当前的={current_system_id}")
                # 我们仍继续验证，但记录警告
            
            # 创建数据副本并移除现有校验和
            data_copy = self.usage_data.copy()
            data_copy.pop('checksum', None)
            
            # 将数据转换为排序后的JSON字符串
            data_str = json.dumps(data_copy, sort_keys=True)
            
            # 使用标准HMAC方法生成校验和
            digest_maker = hmac.new(
                self._secret_key.encode('utf-8'),
                data_str.encode('utf-8'),
                hashlib.sha256
            )
            current_checksum = base64.b64encode(digest_maker.digest()).decode('utf-8')
            
            # 使用恒定时间比较方法比较校验和（防止时序攻击）
            is_valid = hmac.compare_digest(stored_checksum, current_checksum)
            
            if is_valid:
                self.logger.debug("数据验证成功")
            else:
                self.logger.warning("数据验证失败，校验和不匹配")
                
            return is_valid
        except Exception as e:
            self.logger.error(f"验证数据时出错: {str(e)}")
            return False
    
    def start_session(self, index, version):
        """开始记录Blender使用会话
        
        Args:
            index: Blender索引
            version: Blender版本
        """
        self.logger.info(f"开始记录使用会话: 索引={index}, 版本={version}")
        
        self.current_sessions[index] = {
            'start_time': time.time(),
            'version': version
        }
        
    def end_session(self, index):
        """结束Blender使用会话
        
        Args:
            index: Blender索引
            
        Returns:
            float: 会话持续时间(秒)
        """
        if index not in self.current_sessions:
            self.logger.warning(f"找不到索引{index}的使用会话")
            return 0
            
        session = self.current_sessions.pop(index)
        start_time = session['start_time']
        version = session['version']
        
        # 计算会话时长
        end_time = time.time()
        duration = end_time - start_time
        
        self.logger.info(f"结束使用会话: 索引={index}, 版本={version}, 时长={self.format_time(duration)}")
        
        # 更新使用记录
        self._update_usage_data(duration, version)
        
        # 保存使用记录
        self.save_usage_data()
        
        return duration
    
    def _update_usage_data(self, duration, version):
        """更新使用记录数据
        
        Args:
            duration: 持续时间(秒)
            version: Blender版本
        """
        # 更新总使用时长
        self.usage_data['total_time'] += duration
        
        # 更新今日使用时长
        today = date.today().isoformat()
        if today not in self.usage_data['daily_usage']:
            self.usage_data['daily_usage'][today] = 0
        self.usage_data['daily_usage'][today] += duration
        
        # 更新版本使用时长
        if version not in self.usage_data['version_usage']:
            self.usage_data['version_usage'][version] = 0
        self.usage_data['version_usage'][version] += duration
    
    def get_total_time(self):
        """获取总使用时长
        
        Returns:
            float: 总使用时长(秒)
        """
        return self.usage_data['total_time']
    
    def get_today_time(self):
        """获取今日使用时长
        
        Returns:
            float: 今日使用时长(秒)
        """
        today = date.today().isoformat()
        return self.usage_data['daily_usage'].get(today, 0)
    
    def get_version_time(self, version):
        """获取指定版本的使用时长
        
        Args:
            version: Blender版本
            
        Returns:
            float: 版本使用时长(秒)
        """
        return self.usage_data['version_usage'].get(version, 0)
    
    def get_usage_summary(self):
        """获取使用记录摘要
        
        Returns:
            dict: 使用记录摘要
        """
        today_time = self.get_today_time()
        
        # 按使用时长排序版本
        sorted_versions = sorted(
            self.usage_data['version_usage'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 取前5个最常用版本
        top_versions = sorted_versions[:5]
        
        return {
            'total_time': self.usage_data['total_time'],
            'today_time': today_time,
            'top_versions': top_versions
        }
    
    def check_active_sessions(self, blender_manager=None):
        """检查所有活动会话，关闭已经结束的会话
        
        Args:
            blender_manager: Blender管理器实例，用于检查进程状态
            
        Returns:
            int: 关闭的会话数量
        """
        closed_count = 0
        
        # 复制键列表，避免在迭代中修改字典
        indexes = list(self.current_sessions.keys())
        
        for index in indexes:
            # 检查进程是否仍在运行
            process_running = False
            
            # 如果提供了BlenderManager实例，使用它来检查进程
            if blender_manager and hasattr(blender_manager, 'get_running_process'):
                process = blender_manager.get_running_process(index)
                process_running = (process is not None)
            
            # 如果进程已经结束，关闭会话
            if index in self.current_sessions and not process_running:
                self.logger.info(f"检测到会话 {index} 已结束，关闭会话")
                self.end_session(index)
                closed_count += 1
                
        return closed_count
        
    def auto_save_timer(self, blender_manager=None):
        """定期自动保存使用时长数据并检查会话状态
        
        Args:
            blender_manager: Blender管理器实例
        """
        # 检查活动会话
        self.check_active_sessions(blender_manager)
        
        # 如果有活动会话，保存数据
        if self.current_sessions:
            self.logger.info("自动保存使用时长数据")
            self.save_usage_data()
    
    @staticmethod
    def format_time(seconds):
        """格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时间字符串
        """
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分钟"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}小时{minutes}分钟" 