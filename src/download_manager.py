#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 下载管理模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import re
import json
import time
import shutil
import zipfile
import logging
import requests
import threading
from queue import Queue
from urllib.parse import urljoin, urlparse
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from bs4 import BeautifulSoup


class VersionLoaderThread(QThread):
    """版本加载线程，用于异步获取可用的Blender版本列表"""
    
    # 信号定义
    version_loaded_signal = pyqtSignal(list)  # 版本列表加载完成信号(版本列表)
    version_info_signal = pyqtSignal(object)  # 单个版本信息加载完成信号(版本信息)
    progress_signal = pyqtSignal(str)  # 进度信息信号(消息)
    error_signal = pyqtSignal(str)  # 错误信号(错误信息)
    
    def __init__(self, download_manager, json_file='blender_versions.json'):
        super().__init__()
        self.download_manager = download_manager
        self.is_canceled = False
        self.versions = []
        self.json_file = json_file
        
    def run(self):
        """线程执行函数"""
        try:
            self.progress_signal.emit("正在获取可用的Blender版本...")
            
            # 从JSON文件加载版本信息
            self.progress_signal.emit("正在从JSON文件加载版本信息...")
            versions = self.download_manager.load_versions_from_json(self.json_file)
            
            # 检查是否取消
            if self.is_canceled:
                return
                
            # 发送版本信息
            for version_info in versions:
                self.versions.append(version_info)
                self.version_info_signal.emit(version_info)
                
                # 模拟加载延迟，使界面更流畅
                import time
                time.sleep(0.01)
                
                if self.is_canceled:
                    return
            
            # 如果没有获取到任何版本，尝试使用缓存
            if not self.versions and self.download_manager.version_cache:
                self.progress_signal.emit("使用缓存的版本列表")
                for version, info in self.download_manager.version_cache.items():
                    self.versions.append(info)
                    self.version_info_signal.emit(info)
            
            # 发送最终的版本列表
            if self.versions:
                self.progress_signal.emit(f"共找到 {len(self.versions)} 个可用版本")
                self.version_loaded_signal.emit(self.versions)
            else:
                self.error_signal.emit("没有找到可用版本")
        
        except Exception as e:
            self.error_signal.emit(f"获取Blender版本列表出错: {str(e)}")
            
            # 尝试使用缓存
            if self.download_manager.version_cache:
                self.progress_signal.emit("使用缓存的版本列表")
                for version, info in self.download_manager.version_cache.items():
                    self.versions.append(info)
                    self.version_info_signal.emit(info)
                self.version_loaded_signal.emit(self.versions)
    
    def cancel(self):
        """取消加载"""
        self.is_canceled = True


class DownloadWorker(QThread):
    """下载工作线程"""
    
    # 信号定义
    progress_signal = pyqtSignal(int, str, int, int)  # 进度信号(线程ID, 文件名, 当前进度, 总大小)
    finished_signal = pyqtSignal(int, str)  # 完成信号(线程ID, 文件名)
    error_signal = pyqtSignal(int, str, str)  # 错误信号(线程ID, 文件名, 错误信息)
    
    def __init__(self, thread_id, url, save_path, headers=None, proxies=None):
        super().__init__()
        self.thread_id = thread_id
        self.url = url
        self.save_path = save_path
        self.headers = headers or {}
        self.proxies = proxies
        self.is_canceled = False
        
    def run(self):
        """线程执行函数"""
        try:
            response = requests.get(
                self.url, 
                headers=self.headers,
                proxies=self.proxies,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # 获取文件大小
            file_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            # 创建临时文件
            temp_path = f"{self.save_path}.part"
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_canceled:
                        break
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress_signal.emit(self.thread_id, os.path.basename(self.save_path), downloaded, file_size)
                        
            if self.is_canceled:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return
                
            # 重命名临时文件为最终文件
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
            os.rename(temp_path, self.save_path)
            
            self.finished_signal.emit(self.thread_id, os.path.basename(self.save_path))
            
        except Exception as e:
            self.error_signal.emit(self.thread_id, os.path.basename(self.save_path), str(e))
            if os.path.exists(f"{self.save_path}.part"):
                os.remove(f"{self.save_path}.part")
    
    def cancel(self):
        """取消下载"""
        self.is_canceled = True


class ChunkDownloader(QObject):
    """分块下载器，用于多线程分段下载大文件"""
    
    # 信号定义
    progress_signal = pyqtSignal(int, int)  # 进度信号(当前进度, 总大小)
    finished_signal = pyqtSignal(str)  # 完成信号(文件路径)
    error_signal = pyqtSignal(str)  # 错误信号(错误信息)
    
    def __init__(self, url, save_path, chunk_count=10, headers=None, proxies=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.chunk_count = chunk_count
        self.headers = headers or {}
        self.proxies = proxies
        self.workers = []
        self.mutex = QMutex()
        self.downloaded_chunks = []
        self.is_canceled = False
        self.temp_dir = f"{save_path}.chunks"
        self.total_size = 0
        self.downloaded_size = 0
        
    def start(self):
        """开始下载"""
        try:
            # 创建临时目录
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)
                
            # 获取文件大小
            response = requests.head(
                self.url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=10
            )
            response.raise_for_status()
            
            self.total_size = int(response.headers.get('Content-Length', 0))
            if self.total_size <= 0:
                self.error_signal.emit("无法获取文件大小信息")
                return
                
            # 计算每个块的大小
            chunk_size = self.total_size // self.chunk_count
            
            # 创建下载线程
            for i in range(self.chunk_count):
                start = i * chunk_size
                end = (i + 1) * chunk_size - 1 if i < self.chunk_count - 1 else self.total_size - 1
                
                chunk_path = os.path.join(self.temp_dir, f"chunk_{i}")
                headers = self.headers.copy()
                headers['Range'] = f'bytes={start}-{end}'
                
                worker = QThread()
                worker.run = self._download_chunk(i, headers, chunk_path, end - start + 1)
                worker.finished.connect(lambda i=i, path=chunk_path: self._on_chunk_finished(i, path))
                
                self.workers.append(worker)
                worker.start()
        
        except Exception as e:
            self.error_signal.emit(f"开始下载出错: {str(e)}")
            self._cleanup()
            
    def _download_chunk(self, chunk_id, headers, chunk_path, chunk_size):
        """下载块函数"""
        def run():
            try:
                response = requests.get(
                    self.url, 
                    headers=headers,
                    proxies=self.proxies,
                    stream=True,
                    timeout=30
                )
                response.raise_for_status()
                
                downloaded = 0
                
                with open(chunk_path, 'wb') as f:
                    for data in response.iter_content(chunk_size=8192):
                        if self.is_canceled:
                            break
                            
                        if data:
                            f.write(data)
                            downloaded += len(data)
                            
                            # 更新总下载进度
                            self.mutex.lock()
                            self.downloaded_size += len(data)
                            self.progress_signal.emit(self.downloaded_size, self.total_size)
                            self.mutex.unlock()
            
            except Exception as e:
                self.error_signal.emit(f"下载块 {chunk_id} 出错: {str(e)}")
        
        return run
    
    def _on_chunk_finished(self, chunk_id, chunk_path):
        """块下载完成回调"""
        if self.is_canceled:
            return
            
        self.mutex.lock()
        self.downloaded_chunks.append((chunk_id, chunk_path))
        
        # 检查是否所有块都已下载完成
        if len(self.downloaded_chunks) == self.chunk_count:
            self._merge_chunks()
        
        self.mutex.unlock()
    
    def _merge_chunks(self):
        """合并所有块"""
        try:
            # 按ID排序
            self.downloaded_chunks.sort(key=lambda x: x[0])
            
            # 创建目标目录
            target_dir = os.path.dirname(self.save_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # 合并块
            with open(self.save_path, 'wb') as outfile:
                for _, chunk_path in self.downloaded_chunks:
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
            
            # 清理
            self._cleanup()
            
            self.finished_signal.emit(self.save_path)
        
        except Exception as e:
            self.error_signal.emit(f"合并文件块出错: {str(e)}")
            self._cleanup()
    
    def _cleanup(self):
        """清理临时文件和目录"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def cancel(self):
        """取消下载"""
        self.is_canceled = True
        for worker in self.workers:
            worker.terminate()
        self._cleanup()


class BlenderVersionInfo:
    """Blender版本信息"""
    
    def __init__(self, version, build_date=None, url=None, size=None, description=None, changes=None):
        self.version = version
        self.build_date = build_date
        self.url = url
        self.size = size
        self.description = description
        self.changes = changes  # 版本更新说明
    
    def __str__(self):
        return f"Blender {self.version} ({self.build_date}) - {self.size}"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'version': self.version,
            'build_date': self.build_date,
            'url': self.url,
            'size': self.size,
            'description': self.description,
            'changes': self.changes
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        return cls(
            version=data.get('version'),
            build_date=data.get('build_date'),
            url=data.get('url'),
            size=data.get('size'),
            description=data.get('description'),
            changes=data.get('changes')
        )


class DownloadManager(QObject):
    """下载管理器"""
    
    # 信号定义
    download_progress = pyqtSignal(str, int, int)  # 下载进度(文件名, 当前进度, 总大小)
    download_finished = pyqtSignal(str, str)  # 下载完成(文件名, 保存路径)
    download_error = pyqtSignal(str, str)  # 下载错误(文件名, 错误信息)
    download_all_finished = pyqtSignal()  # 所有下载完成
    version_list_updated = pyqtSignal(list)  # 版本列表更新(版本列表)
    
    def __init__(self, config=None, logger=None):
        super().__init__()
        self.config = config or {}
        self.logger = logger or logging.getLogger("DownloadManager")
        
        # 下载配置
        self.download_dir = self.config.get('download_dir', 'downloads')
        self.use_mirror = self.config.get('use_mirror', True)
        self.mirror_url = self.config.get('mirror_url', 'https://mirrors.aliyun.com/blender/')
        self.use_multi_thread = self.config.get('use_multi_thread', True)
        self.thread_count = self.config.get('thread_count', 10)
        self.use_proxy = self.config.get('use_proxy', False)
        
        # 官方下载地址
        self.official_url = 'https://www.blender.org/download/'
        
        # 代理配置
        self.proxies = None
        if self.use_proxy:
            proxy = self.config.get('proxy', '')
            if proxy:
                self.proxies = {
                    'http': proxy,
                    'https': proxy
                }
        
        # 创建下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # 当前下载任务
        self.current_downloads = {}
        
        # 版本缓存
        self.version_cache_file = os.path.join(self.download_dir, 'version_cache.json')
        self.version_cache = {}
        self.load_version_cache()
    
    def load_version_cache(self):
        """加载版本缓存"""
        try:
            if os.path.exists(self.version_cache_file):
                with open(self.version_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    for version, data in cache_data.items():
                        self.version_cache[version] = BlenderVersionInfo.from_dict(data)
                    
                    self.logger.info(f"已加载 {len(self.version_cache)} 个版本缓存")
        except Exception as e:
            self.logger.error(f"加载版本缓存出错: {str(e)}")
    
    def save_version_cache(self):
        """保存版本缓存"""
        try:
            cache_data = {}
            for version, info in self.version_cache.items():
                cache_data[version] = info.to_dict()
                
            with open(self.version_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=4)
                
            self.logger.info("版本缓存已保存")
        except Exception as e:
            self.logger.error(f"保存版本缓存出错: {str(e)}")
    
    def load_versions_from_json(self, json_file='blender_versions.json'):
        """从JSON文件加载版本信息
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            list: 版本信息列表
        """
        try:
            self.logger.info(f"从JSON文件加载版本信息: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            versions = []
            for version_data in data.get('versions', []):
                # 替换下载URL中的{URL}为实际的镜像源地址
                download_url = version_data.get('download_url', '')
                if download_url and '{URL}' in download_url:
                    download_url = download_url.replace('{URL}', self.mirror_url.rstrip('/'))
                
                version_info = BlenderVersionInfo(
                    version=version_data.get('version'),
                    build_date=version_data.get('build_date'),
                    url=download_url,  # 使用替换后的URL
                    size=version_data.get('size'),
                    description=version_data.get('description'),
                    changes=version_data.get('changes')
                )
                versions.append(version_info)
                
                # 更新缓存
                self.version_cache[version_info.version] = version_info
                
            self.logger.info(f"从JSON文件加载了 {len(versions)} 个版本")
            return versions
            
        except Exception as e:
            self.logger.error(f"加载JSON版本信息出错: {str(e)}")
            return []

    def _get_versions_from_direct_download(self):
        """直接从下载目录获取所有版本列表"""
        versions = []
        try:
            # 直接从下载目录获取版本列表
            release_url = self.config.get('mirror_url', 'https://mirrors.aliyun.com/blender/release/')
            
            self.logger.info(f"正在直接访问Blender下载目录: {release_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 获取所有版本目录
            releases_resp = requests.get(
                release_url, 
                headers=headers,
                timeout=20, 
                proxies=self.proxies
            )
            releases_resp.raise_for_status()
            
            releases_soup = BeautifulSoup(releases_resp.text, 'html.parser')
            release_links = releases_soup.find_all('a')
            
            # 查找Blender版本目录
            blender_versions = []
            for link in release_links:
                href = link.get('href')
                if href and href.startswith('Blender') and href.endswith('/'):
                    version_match = re.search(r'Blender(\d+\.\d+)', href)
                    if version_match:
                        blender_versions.append((version_match.group(1), href))
            
            self.logger.info(f"找到 {len(blender_versions)} 个Blender版本目录")
            
            # 按版本号排序
            blender_versions.sort(
                key=lambda v: [int(n) for n in v[0].split('.')], 
                reverse=True
            )
            
            # 处理所有的版本，获取子版本
            for major_version, dir_href in blender_versions:
                version_url = urljoin(release_url, dir_href)
                self.logger.info(f"获取主版本 {major_version} 的子版本信息")
                
                try:
                    # 获取版本目录内容
                    version_resp = requests.get(
                        version_url, 
                        headers=headers,
                        timeout=20, 
                        proxies=self.proxies
                    )
                    version_resp.raise_for_status()
                    
                    version_soup = BeautifulSoup(version_resp.text, 'html.parser')
                    file_links = version_soup.find_all('a')
                    
                    # 查找Windows版本文件
                    subversions = []
                    for link in file_links:
                        href = link.get('href')
                        if href and 'windows' in href.lower() and href.endswith('.zip'):
                            # 提取完整版本号
                            full_version_match = re.search(r'blender-(\d+\.\d+\.\d+)-', href)
                            if full_version_match:
                                full_version = full_version_match.group(1)
                                file_url = urljoin(version_url, href)
                                
                                # 获取文件大小和日期
                                size = "未知"
                                date = "未知"
                                parent_row = link.parent.parent
                                if parent_row:
                                    size_cell = parent_row.find_next('td', class_='size')
                                    date_cell = parent_row.find_next('td', class_='date')
                                    if size_cell:
                                        size = size_cell.text.strip()
                                    if date_cell:
                                        date = date_cell.text.strip()
                                
                                subversions.append((full_version, file_url, size, date))
                    
                    # 按子版本号排序
                    subversions.sort(
                        key=lambda v: [int(n) if n.isdigit() else 0 for n in v[0].split('.')], 
                        reverse=True
                    )
                    
                    # 添加所有子版本
                    for full_version, file_url, size, date in subversions:
                        # 创建版本信息对象
                        version_info = BlenderVersionInfo(
                            version=full_version,
                            url=file_url,
                            size=size,
                            build_date=date,
                            description=f"Blender {full_version} Windows 64位版本"
                        )
                        
                        versions.append(version_info)
                        
                        # 更新缓存
                        self.version_cache[full_version] = version_info
                    
                    self.logger.info(f"主版本 {major_version} 下找到 {len(subversions)} 个子版本")
                    
                except Exception as e:
                    self.logger.error(f"获取版本 {major_version} 的子版本信息出错: {str(e)}")
            
            self.logger.info(f"从官方下载目录获取到 {len(versions)} 个可用版本")
            return versions
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接下载目录失败: {str(e)}")
            return []
        except requests.exceptions.Timeout as e:
            self.logger.error(f"连接下载目录超时: {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求下载目录出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"从官方网站获取版本列表出错: {str(e)}")
            return []

    def get_download_url(self, version_info):
        """获取指定版本的下载链接
        
        在用户点击下载按钮时调用此方法获取实际下载链接
        
        Args:
            version_info: 版本信息对象
            
        Returns:
            str: 下载链接，如果获取失败则返回None
        """
        try:
            if not version_info.url:
                self.logger.error("版本信息中没有URL")
                return None
                
            # 如果URL已经是下载链接（以.zip或.msi结尾），则直接返回
            if version_info.url.endswith('.zip') or version_info.url.endswith('.msi'):
                return version_info.url
                
            # 否则，获取版本目录，查找Windows下载链接
            self.logger.info(f"获取版本 {version_info.version} 的下载链接: {version_info.url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            version_resp = requests.get(
                version_info.url, 
                headers=headers,
                timeout=20, 
                proxies=self.proxies
            )
            version_resp.raise_for_status()
            
            version_soup = BeautifulSoup(version_resp.text, 'html.parser')
            file_links = version_soup.find_all('a')
            
            # 查找Windows版本
            windows_files = []
            for link in file_links:
                href = link.get('href')
                if href and 'windows' in href.lower() and 'x64' in href.lower() and href.endswith('.zip'):
                    version_match = re.search(r'blender-(\d+\.\d+\.\d+)-', href)
                    if version_match:
                        exact_version = version_match.group(1)
                        # 检查版本前两个数字是否匹配
                        major_version = version_info.version.split('.')[0]
                        if exact_version.startswith(major_version):
                            windows_files.append((exact_version, href))
            
            self.logger.info(f"在版本 {version_info.version} 中找到 {len(windows_files)} 个Windows下载文件")
            
            if not windows_files:
                self.logger.warning(f"未找到版本 {version_info.version} 的Windows下载文件")
                return None
                
            # 按版本号排序
            windows_files.sort(
                key=lambda v: [int(n) if n.isdigit() else 0 for n in v[0].split('.')], 
                reverse=True
            )
            
            # 获取最新版本的下载链接
            exact_version, file_href = windows_files[0]
            file_url = urljoin(version_info.url, file_href)
            
            # 获取文件大小
            try:
                head_resp = requests.head(
                    file_url, 
                    timeout=10, 
                    proxies=self.proxies,
                    headers=headers
                )
                if head_resp.status_code == 200:
                    size_bytes = int(head_resp.headers.get('Content-Length', 0))
                    file_size = self._format_size(size_bytes)
                    self.logger.info(f"版本 {exact_version} 文件大小: {file_size}")
                    # 更新版本信息
                    version_info.size = file_size
            except Exception as e:
                self.logger.warning(f"获取文件大小失败: {str(e)}")
            
            # 更新版本信息
            version_info.version = exact_version
            version_info.description = f"Blender {exact_version} Windows 64位版本"
            
            self.logger.info(f"获取到版本 {exact_version} 的Windows下载链接: {file_url}")
            return file_url
            
        except Exception as e:
            self.logger.error(f"获取下载链接失败: {str(e)}")
            return None

    def get_available_versions(self):
        """获取可用的Blender版本列表"""
        try:
            self.logger.info("开始获取可用的Blender版本...")
            
            all_versions = []
            
            # 首先尝试直接从下载页面获取
            direct_versions = self._get_versions_from_direct_download()
            if direct_versions:
                all_versions.extend(direct_versions)
                self.logger.info(f"从直接下载获取到 {len(direct_versions)} 个版本")
            
            # 尝试从镜像获取
            if self.use_mirror and not all_versions:
                self.logger.info(f"尝试从镜像 {self.mirror_url} 获取版本信息...")
                mirror_versions = self._get_versions_from_mirror()
                if mirror_versions:
                    all_versions.extend(mirror_versions)
                    self.logger.info(f"从镜像获取到 {len(mirror_versions)} 个版本")
            
            # 如果前两种方法都失败，尝试从官网获取
            if not all_versions:
                self.logger.info("正在从官方网站获取版本信息...")
                official_versions = self._get_versions_from_official()
                if official_versions:
                    all_versions.extend(official_versions)
                    self.logger.info(f"从官方网站获取到 {len(official_versions)} 个版本")
            
            # 去重并排序
            unique_versions = {}
            for version in all_versions:
                if version.version not in unique_versions:
                    unique_versions[version.version] = version
            
            # 转换回列表
            versions = list(unique_versions.values())
            
            # 按版本号排序（降序）
            versions.sort(
                key=lambda v: [int(n) if n.isdigit() else 0 for n in v.version.split('.')], 
                reverse=True
            )
            
            # 更新缓存并发送信号
            for version in versions:
                self.version_cache[version.version] = version
            
            # 保存缓存
            self.save_version_cache()
            
            # 如果没有获取到任何版本，尝试使用缓存
            if not versions and self.version_cache:
                self.logger.info("使用缓存的版本列表")
                versions = list(self.version_cache.values())
            
            # 发送信号
            if versions:
                self.logger.info(f"共找到 {len(versions)} 个可用版本")
                self.version_list_updated.emit(versions)
            else:
                self.logger.warning("没有找到可用版本")
            
            return versions
        
        except Exception as e:
            self.logger.error(f"获取Blender版本列表出错: {str(e)}")
            
            # 尝试使用缓存
            if self.version_cache:
                self.logger.info("使用缓存的版本列表")
                versions = list(self.version_cache.values())
                self.version_list_updated.emit(versions)
                return versions
            
            return []
    
    def _get_versions_from_mirror(self):
        """从镜像网站获取版本列表"""
        versions = []
        try:
            # 发送请求
            self.logger.info(f"正在连接镜像站点: {self.mirror_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                self.mirror_url, 
                headers=headers,
                timeout=15, 
                proxies=self.proxies
            )
            response.raise_for_status()
            
            # 解析HTML
            self.logger.info("正在解析镜像站点HTML内容...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找版本链接
            links = soup.find_all('a')
            version_pattern = re.compile(r'blender-(\d+\.\d+)')
            
            found_versions = []
            for link in links:
                href = link.get('href')
                if href and version_pattern.search(href):
                    version_match = version_pattern.search(href)
                    if version_match:
                        version = version_match.group(1)
                        found_versions.append((version, href))
            
            self.logger.info(f"在镜像站点找到 {len(found_versions)} 个版本目录")
            
            # 按版本号排序（降序）
            found_versions.sort(key=lambda x: [int(n) for n in x[0].split('.')], reverse=True)
            
            # 获取最新的5个版本
            latest_versions = found_versions[:5]
            self.logger.info(f"准备获取最新的 {len(latest_versions)} 个版本详情")
            
            # 获取子页面
            for version, href in latest_versions:
                sub_url = urljoin(self.mirror_url, href)
                self.logger.info(f"正在获取版本 {version} 的详情: {sub_url}")
                sub_versions = self._get_versions_from_mirror_subpage(sub_url, version)
                if sub_versions:
                    versions.extend(sub_versions)
            
            self.logger.info(f"从镜像站点共获取到 {len(versions)} 个可用版本")
            return versions
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接镜像站点失败: {str(e)}")
            return []
        except requests.exceptions.Timeout as e:
            self.logger.error(f"连接镜像站点超时: {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求镜像站点出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"从镜像获取版本列表出错: {str(e)}")
            return []
    
    def _get_versions_from_mirror_subpage(self, url, base_version):
        """从镜像子页面获取具体版本"""
        versions = []
        try:
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=15, 
                proxies=self.proxies
            )
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找版本链接
            links = soup.find_all('a')
            version_pattern = re.compile(r'blender-(\d+\.\d+\.\d+)-windows-x64.zip')
            
            found_versions = []
            for link in links:
                href = link.get('href')
                if href and version_pattern.search(href):
                    version_match = version_pattern.search(href)
                    if version_match:
                        version_str = version_match.group(1)
                        found_versions.append((version_str, href))
            
            self.logger.info(f"在版本 {base_version} 目录中找到 {len(found_versions)} 个Windows版本")
            
            # 按版本号排序（降序）
            found_versions.sort(key=lambda x: [int(n) for n in x[0].split('.')], reverse=True)
            
            # 获取最新的3个版本
            latest_versions = found_versions[:3]
            
            for version_str, href in latest_versions:
                # 获取文件信息
                file_url = urljoin(url, href)
                file_size = "未知"
                
                # 尝试获取文件大小
                try:
                    head_resp = requests.head(
                        file_url, 
                        timeout=10, 
                        proxies=self.proxies,
                        headers=headers
                    )
                    if head_resp.status_code == 200:
                        size_bytes = int(head_resp.headers.get('Content-Length', 0))
                        file_size = self._format_size(size_bytes)
                        self.logger.info(f"版本 {version_str} 文件大小: {file_size}")
                except Exception as e:
                    self.logger.warning(f"获取版本 {version_str} 文件大小失败: {str(e)}")
                
                # 创建版本信息对象
                version_info = BlenderVersionInfo(
                    version=version_str,
                    url=file_url,
                    size=file_size,
                    description=f"Blender {version_str} Windows 64位版本"
                )
                
                versions.append(version_info)
                self.logger.info(f"添加版本: {version_str}, URL: {file_url}")
            
            return versions
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接镜像子页面失败: {str(e)}")
            return []
        except requests.exceptions.Timeout as e:
            self.logger.error(f"连接镜像子页面超时: {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求镜像子页面出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"从镜像子页面获取版本列表出错: {str(e)}")
            return []
    
    def _get_versions_from_official(self):
        """从官方网站获取版本列表"""
        versions = []
        try:
            # 发送请求
            self.logger.info(f"正在连接官方网站: {self.official_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                self.official_url, 
                headers=headers,
                timeout=20, 
                proxies=self.proxies
            )
            response.raise_for_status()
            
            # 解析HTML
            self.logger.info("正在解析官方网站HTML内容...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 调试信息：记录页面内容
            self.logger.debug(f"官方页面标题: {soup.title.string if soup.title else '无标题'}")
            
            # 查找下载按钮
            download_links = soup.select('a.Button.Button--download')
            self.logger.info(f"找到 {len(download_links)} 个下载按钮")
            
            # 如果没有找到按钮，尝试其他选择器
            if not download_links:
                download_links = soup.select('a.button.button--download')
                self.logger.info(f"尝试备用选择器，找到 {len(download_links)} 个下载按钮")
            
            # 如果还是没找到，尝试更通用的方法
            if not download_links:
                download_links = []
                for link in soup.find_all('a'):
                    if link.get('href') and 'download' in link.get('href').lower():
                        if 'blender' in link.get_text().lower():
                            download_links.append(link)
                self.logger.info(f"尝试通用查找方法，找到 {len(download_links)} 个可能的下载链接")
            
            version_pattern = re.compile(r'Blender (\d+\.\d+\.\d+)')
            
            for link in download_links:
                text = link.get_text()
                version_match = version_pattern.search(text)
                
                if version_match:
                    version_str = version_match.group(1)
                    
                    # 获取下载页链接
                    href = link.get('href')
                    if href:
                        download_page_url = href
                        self.logger.info(f"找到版本 {version_str} 的下载页面: {download_page_url}")
                        
                        # 将链接转为绝对URL
                        if not download_page_url.startswith('http'):
                            download_page_url = urljoin(self.official_url, download_page_url)
                        
                        # 获取Windows下载URL
                        windows_url = self._get_windows_download_url(download_page_url)
                        
                        if windows_url:
                            self.logger.info(f"找到版本 {version_str} 的Windows下载链接: {windows_url}")
                            
                            # 创建版本信息对象
                            version_info = BlenderVersionInfo(
                                version=version_str,
                                url=windows_url,
                                description=f"Blender {version_str} Windows 64位版本"
                            )
                            
                            versions.append(version_info)
                        else:
                            self.logger.warning(f"未能获取版本 {version_str} 的Windows下载链接")
            
            self.logger.info(f"从官方网站获取到 {len(versions)} 个可用版本")
            return versions
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接官方网站失败: {str(e)}")
            return []
        except requests.exceptions.Timeout as e:
            self.logger.error(f"连接官方网站超时: {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求官方网站出错: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"从官方网站获取版本列表出错: {str(e)}")
            return []
    
    def _get_windows_download_url(self, download_page_url):
        """获取Windows下载URL"""
        try:
            # 发送请求
            self.logger.info(f"正在获取下载页面: {download_page_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                download_page_url, 
                headers=headers,
                timeout=15, 
                proxies=self.proxies
            )
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            self.logger.info(f"成功获取页面, 页面标题: {soup.title.string if soup.title else '无标题'}")
            
            # 首先尝试查找直接包含Windows下载链接的按钮
            download_buttons = soup.find_all('a', text=lambda t: t and 'Download' in t)
            self.logger.info(f"找到 {len(download_buttons)} 个下载按钮")
            
            # 查找包含Windows相关文本的下载按钮
            for button in download_buttons:
                # 检查按钮及其周围是否有Windows相关文本
                button_text = button.get_text()
                if 'Windows' in button_text:
                    href = button.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin(download_page_url, href)
                        self.logger.info(f"找到Windows下载按钮链接: {href}")
                        return href
                
                # 检查按钮周围的元素
                parent = button.parent
                if parent:
                    parent_text = parent.get_text()
                    if 'Windows' in parent_text:
                        href = button.get('href')
                        if href:
                            if not href.startswith('http'):
                                href = urljoin(download_page_url, href)
                            self.logger.info(f"找到Windows下载按钮(父元素)链接: {href}")
                            return href
            
            # 如果没找到，尝试更通用的方法，查找所有链接
            self.logger.info("未找到直接的Windows下载按钮，尝试查找所有链接")
            all_links = soup.find_all('a')
            
            # 首先尝试查找明确的Windows安装程序链接
            for link in all_links:
                href = link.get('href')
                if not href:
                    continue
                
                href_lower = href.lower()
                # 检查是否是明确的Windows安装包链接
                if ('windows' in href_lower or 'win64' in href_lower) and (href_lower.endswith('.zip') or href_lower.endswith('.msi')):
                    if not href.startswith('http'):
                        href = urljoin(download_page_url, href)
                    self.logger.info(f"找到Windows安装包链接: {href}")
                    return href
            
            # 如果仍未找到，尝试查找所有下载链接并判断是否包含Windows相关信息
            for link in all_links:
                href = link.get('href')
                if not href:
                    continue
                
                link_text = link.get_text().lower()
                href_lower = href.lower()
                
                # 如果链接文本包含Windows或链接指向.zip/.msi文件
                if ('windows' in link_text or 'win64' in link_text or 
                    'windows' in href_lower or 'win64' in href_lower):
                    if not href.startswith('http'):
                        href = urljoin(download_page_url, href)
                    self.logger.info(f"找到可能的Windows相关链接: {href}")
                    return href
            
            # 如果所有方法都失败，记录错误并返回None
            self.logger.warning(f"在下载页面未找到Windows下载链接: {download_page_url}")
            return None
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"连接下载页面失败: {str(e)}")
            return None
        except requests.exceptions.Timeout as e:
            self.logger.error(f"连接下载页面超时: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求下载页面出错: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"获取Windows下载URL出错: {str(e)}")
            return None
    
    def download_blender(self, version_info):
        """下载指定版本的Blender
        
        Args:
            version_info: 版本信息对象
            
        Returns:
            str: 下载ID，用于标识下载任务，如果下载失败则返回None
        """
        try:
            # 获取实际下载URL
            download_url = None
            if version_info.url.endswith('.zip') or version_info.url.endswith('.msi'):
                download_url = version_info.url
            else:
                download_url = self.get_download_url(version_info)
            
            if not download_url:
                self.logger.error(f"无法获取版本 {version_info.version} 的下载链接")
                self.download_error.emit(version_info.version, "无法获取下载链接")
                return None
                
            # 使用原始的下载逻辑，但使用新获取的URL
            version_info.url = download_url
            
            # 以下为原始下载逻辑
            download_id = version_info.version
            
            # 检查下载目录
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)
            
            # 设置保存路径
            file_name = os.path.basename(version_info.url)
            save_path = os.path.join(self.download_dir, file_name)
            
            self.logger.info(f"开始下载 {download_id}，URL: {version_info.url}")
            
            # 如果已有下载任务，先取消
            if download_id in self.current_downloads:
                self.cancel_download(download_id)
            
            # 使用多线程下载
            if self.use_multi_thread and version_info.url.endswith('.zip'):
                # 创建分块下载器
                downloader = ChunkDownloader(
                    url=version_info.url,
                    save_path=save_path,
                    chunk_count=self.thread_count,
                    proxies=self.proxies
                )
                
                # 连接信号
                downloader.progress_signal.connect(
                    lambda current, total: self.download_progress.emit(download_id, current, total)
                )
                downloader.finished_signal.connect(
                    lambda path: self._on_download_finished(download_id, path)
                )
                downloader.error_signal.connect(
                    lambda error: self.download_error.emit(download_id, error)
                )
                
                # 保存下载器
                self.current_downloads[download_id] = {
                    'downloader': downloader,
                    'version_info': version_info,
                    'save_path': save_path
                }
                
                # 开始下载
                downloader.start()
            
            else:
                # 使用单线程下载
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                worker = DownloadWorker(
                    thread_id=0,
                    url=version_info.url,
                    save_path=save_path,
                    headers=headers,
                    proxies=self.proxies
                )
                
                # 连接信号
                worker.progress_signal.connect(
                    lambda tid, filename, current, total: self.download_progress.emit(download_id, current, total)
                )
                worker.finished_signal.connect(
                    lambda tid, filename: self._on_download_finished(download_id, save_path)
                )
                worker.error_signal.connect(
                    lambda tid, filename, error: self.download_error.emit(download_id, error)
                )
                
                # 保存下载器
                self.current_downloads[download_id] = {
                    'downloader': worker,
                    'version_info': version_info,
                    'save_path': save_path
                }
                
                # 开始下载
                worker.start()
            
            return download_id
            
        except Exception as e:
            self.logger.error(f"开始下载 {version_info.version} 时出错: {str(e)}")
            self.download_error.emit(version_info.version, str(e))
            return None
    
    def _on_download_finished(self, download_id, save_path):
        """下载完成回调"""
        if download_id not in self.current_downloads:
            return
            
        version_info = self.current_downloads[download_id]['version_info']
        self.logger.info(f"下载完成: {version_info.version}, 保存路径: {save_path}")
        
        # 发送下载完成信号
        self.download_finished.emit(download_id, save_path)
        
        # 检查是否所有下载都已完成
        self.current_downloads.pop(download_id, None)
        if not self.current_downloads:
            self.download_all_finished.emit()
    
    def cancel_download(self, download_id):
        """取消下载
        
        Args:
            download_id: 下载ID
            
        Returns:
            bool: 是否成功取消
        """
        if download_id in self.current_downloads:
            download = self.current_downloads[download_id]
            downloader = download['downloader']
            
            # 取消下载
            if hasattr(downloader, 'cancel'):
                downloader.cancel()
            elif isinstance(downloader, QThread):
                downloader.terminate()
            
            # 删除临时文件
            save_path = download['save_path']
            temp_path = f"{save_path}.part"
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # 清理下载记录
            self.current_downloads.pop(download_id, None)
            
            self.logger.info(f"已取消下载: {download_id}")
            return True
        
        return False
    
    def extract_blender(self, zip_path, extract_dir=None):
        """解压Blender安装包
        
        Args:
            zip_path: ZIP文件路径
            extract_dir: 解压目标目录，默认为下载目录
            
        Returns:
            str: 解压后的Blender目录路径，失败则返回None
        """
        try:
            if not os.path.exists(zip_path):
                self.logger.error(f"解压失败，文件不存在: {zip_path}")
                return None
            
            # 默认解压到下载目录
            if extract_dir is None:
                extract_dir = self.download_dir
            
            # 确保解压目录存在
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            
            self.logger.info(f"开始解压: {zip_path} 到 {extract_dir}")
            
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取ZIP文件中的根目录名称
                root_dirs = set()
                for name in zip_ref.namelist():
                    parts = name.split('/')
                    if len(parts) > 1:
                        root_dirs.add(parts[0])
                
                # 检查是否有根目录
                if len(root_dirs) != 1:
                    # 如果没有单个根目录，创建一个目录
                    blender_dirname = os.path.basename(zip_path).replace('.zip', '')
                    extract_target = os.path.join(extract_dir, blender_dirname)
                    
                    if os.path.exists(extract_target):
                        shutil.rmtree(extract_target)
                    
                    os.makedirs(extract_target)
                    zip_ref.extractall(extract_target)
                    blender_dir = extract_target
                else:
                    # 如果有单个根目录，直接解压
                    zip_ref.extractall(extract_dir)
                    blender_dir = os.path.join(extract_dir, list(root_dirs)[0])
            
            self.logger.info(f"解压完成，Blender目录: {blender_dir}")
            return blender_dir
            
        except Exception as e:
            self.logger.error(f"解压文件出错: {str(e)}")
            return None
    
    def update_config(self, config):
        """更新配置
        
        Args:
            config: 新的配置字典
        """
        self.config.update(config)
        
        # 更新下载配置
        self.download_dir = self.config.get('download_dir', 'downloads')
        self.use_mirror = self.config.get('use_mirror', True)
        self.mirror_url = self.config.get('mirror_url', 'https://mirrors.aliyun.com/blender/')
        self.use_multi_thread = self.config.get('use_multi_thread', True)
        self.thread_count = self.config.get('thread_count', 10)
        self.use_proxy = self.config.get('use_proxy', False)
        
        # 更新代理配置
        self.proxies = None
        if self.use_proxy:
            proxy = self.config.get('proxy', '')
            if proxy:
                self.proxies = {
                    'http': proxy,
                    'https': proxy
                }
        
        # 创建下载目录
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def _format_size(self, size_bytes):
        """格式化文件大小
        
        Args:
            size_bytes: 字节大小
            
        Returns:
            str: 格式化后的大小
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


# 测试代码
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建下载管理器
    config = {
        'download_dir': 'downloads',
        'use_mirror': True,
        'mirror_url': 'https://mirrors.aliyun.com/blender/',
        'use_multi_thread': True,
        'thread_count': 10,
        'use_proxy': False
    }
    
    manager = DownloadManager(config)
    
    # 连接信号
    manager.download_progress.connect(lambda download_id, current, total: print(f"下载进度: {download_id} - {current}/{total} ({current/total*100:.2f}%)"))
    manager.download_finished.connect(lambda download_id, path: print(f"下载完成: {download_id} - {path}"))
    manager.download_error.connect(lambda download_id, error: print(f"下载错误: {download_id} - {error}"))
    manager.version_list_updated.connect(lambda versions: print(f"版本列表更新: {len(versions)} 个版本"))
    
    # 获取版本列表
    versions = manager.get_available_versions()
    
    # 如果有版本，下载第一个
    if versions:
        download_id = manager.download_blender(versions[0])
        print(f"开始下载: {download_id}")
    
    sys.exit(app.exec()) 