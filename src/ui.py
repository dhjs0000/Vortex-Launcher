#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 用户界面模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QMenuBar, QDialog, QCheckBox,
    QLineEdit, QGridLayout, QTabWidget, QTextEdit,
    QSpinBox, QProgressBar
)
from PyQt6.QtGui import QAction, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, QDateTime

from src.log import LogViewerDialog, LogSettingsDialog
from src.blender_manager import BlenderManager
from src.download_manager import DownloadManager, BlenderVersionInfo


class AboutDialog(QDialog):
    """关于对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 标题和版本
        title_label = QLabel("Vortex-Launcher")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        
        version_label = QLabel("Beta 1.1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 12pt;")
        
        # 作者和联系方式
        author_label = QLabel("作者: dhjs0000")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        email_label = QLabel("联系方式: dhjsIIII@foxmail.com")
        email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 版权信息
        copyright_label = QLabel("版权所有 © 2025 dhjs0000")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # GPL 许可证信息
        license_info = QTextEdit()
        license_info.setReadOnly(True)
        license_info.setText("本软件采用GNU通用公共许可证v3 (GPL-3.0)发布。\n\n"
                           "这意味着您可以自由地使用、修改和分发本软件，但您分发的任何衍生作品\n"
                           "也必须在GPL-3.0下发布并开放源代码。\n\n"
                           "完整的许可证文本可在软件根目录的LICENSE文件中找到。")
        
        # 添加所有部件到布局
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addSpacing(20)
        layout.addWidget(author_label)
        layout.addWidget(email_label)
        layout.addSpacing(10)
        layout.addWidget(copyright_label)
        layout.addSpacing(20)
        layout.addWidget(license_info)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)


class VersionEditDialog(QDialog):
    """版本编辑对话框"""
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("编辑版本信息")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # 版本信息
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("路径:"), 0, 0)
        path_label = QLabel(info['path'])
        path_label.setWordWrap(True)
        form_layout.addWidget(path_label, 0, 1)
        
        form_layout.addWidget(QLabel("当前版本:"), 1, 0)
        current_version = QLabel(info['version'])
        form_layout.addWidget(current_version, 1, 1)
        
        form_layout.addWidget(QLabel("新版本:"), 2, 0)
        self.version_edit = QLineEdit(info['version'])
        form_layout.addWidget(self.version_edit, 2, 1)
        
        layout.addLayout(form_layout)
        
        # 说明文本
        note_label = QLabel("注意: 这里只修改显示的版本名称，不会影响实际的Blender版本。")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # 创建选项卡
        tabs = QTabWidget()
        
        # 文件选项卡
        file_tab = QWidget()
        file_layout = QGridLayout(file_tab)
        
        # 自动获取设置
        self.auto_detect = QCheckBox("启用自动获取指定目录下Blender版本")
        self.auto_detect.setChecked(config.get('auto_detect', False))
        
        # 指定目录
        self.auto_detect_path = QLineEdit()
        self.auto_detect_path.setText(config.get('auto_detect_path', ''))
        self.auto_detect_path.setEnabled(self.auto_detect.isChecked())
        
        # 连接信号
        self.auto_detect.toggled.connect(self.auto_detect_path.setEnabled)
        
        # 添加到文件布局
        file_layout.addWidget(self.auto_detect, 0, 0, 1, 2)
        file_layout.addWidget(QLabel("指定目录:"), 1, 0)
        file_layout.addWidget(self.auto_detect_path, 1, 1)
        
        # 浏览按钮
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_directory)
        file_layout.addWidget(browse_button, 1, 2)
        
        # 编辑选项卡
        edit_tab = QWidget()
        edit_layout = QVBoxLayout(edit_tab)
        
        # 快速启动设置
        self.quick_launch = QCheckBox("启用快速启动模式（双击栏目启动Blender）")
        self.quick_launch.setChecked(config.get('quick_launch', False))
        
        # 添加到编辑布局
        edit_layout.addWidget(self.quick_launch)
        edit_layout.addStretch()
        
        # 下载选项卡
        download_tab = QWidget()
        download_layout = QGridLayout(download_tab)
        
        # 下载目录
        download_layout.addWidget(QLabel("下载目录:"), 0, 0)
        self.download_dir = QLineEdit()
        self.download_dir.setText(config.get('download_dir', 'downloads'))
        download_layout.addWidget(self.download_dir, 0, 1)
        
        # 浏览下载目录按钮
        download_browse_button = QPushButton("浏览...")
        download_browse_button.clicked.connect(self.browse_download_directory)
        download_layout.addWidget(download_browse_button, 0, 2)
        
        # 第三方下载源设置
        self.use_mirror = QCheckBox("使用第三方下载源")
        self.use_mirror.setChecked(config.get('use_mirror', True))
        download_layout.addWidget(self.use_mirror, 1, 0, 1, 3)
        
        download_layout.addWidget(QLabel("下载源地址:"), 2, 0)
        self.mirror_url = QLineEdit()
        self.mirror_url.setText(config.get('mirror_url', 'https://mirrors.aliyun.com/blender/'))
        self.mirror_url.setEnabled(self.use_mirror.isChecked())
        download_layout.addWidget(self.mirror_url, 2, 1, 1, 2)
        
        # 连接信号
        self.use_mirror.toggled.connect(self.mirror_url.setEnabled)
        
        # 多线程下载设置
        self.use_multi_thread = QCheckBox("使用多线程下载")
        self.use_multi_thread.setChecked(config.get('use_multi_thread', True))
        download_layout.addWidget(self.use_multi_thread, 3, 0, 1, 3)
        
        download_layout.addWidget(QLabel("下载线程数:"), 4, 0)
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 32)
        self.thread_count.setValue(config.get('thread_count', 10))
        self.thread_count.setEnabled(self.use_multi_thread.isChecked())
        download_layout.addWidget(self.thread_count, 4, 1)
        
        # 连接信号
        self.use_multi_thread.toggled.connect(self.thread_count.setEnabled)
        
        # 代理设置
        self.use_proxy = QCheckBox("使用系统代理")
        self.use_proxy.setChecked(config.get('use_proxy', False))
        download_layout.addWidget(self.use_proxy, 5, 0, 1, 3)
        
        download_layout.addWidget(QLabel("代理地址:"), 6, 0)
        self.proxy = QLineEdit()
        self.proxy.setText(config.get('proxy', ''))
        self.proxy.setEnabled(self.use_proxy.isChecked())
        self.proxy.setPlaceholderText("例如: http://127.0.0.1:7890")
        download_layout.addWidget(self.proxy, 6, 1, 1, 2)
        
        # 连接信号
        self.use_proxy.toggled.connect(self.proxy.setEnabled)
        
        # 添加空白行填充
        download_layout.addWidget(QWidget(), 7, 0)
        download_layout.setRowStretch(7, 1)
        
        # 添加选项卡
        tabs.addTab(file_tab, "文件")
        tabs.addTab(edit_tab, "编辑")
        tabs.addTab(download_tab, "下载")
        
        layout.addWidget(tabs)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择Blender安装目录", self.auto_detect_path.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.auto_detect_path.setText(directory)
            
    def browse_download_directory(self):
        """浏览下载目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_dir.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.download_dir.setText(directory)

    def save_settings(self):
        """保存设置"""
        # 文件设置
        self.config['auto_detect'] = self.auto_detect.isChecked()
        self.config['auto_detect_path'] = self.auto_detect_path.text()
        
        # 编辑设置
        self.config['quick_launch'] = self.quick_launch.isChecked()
        
        # 下载设置
        self.config['download_dir'] = self.download_dir.text()
        self.config['use_mirror'] = self.use_mirror.isChecked()
        self.config['mirror_url'] = self.mirror_url.text()
        self.config['use_multi_thread'] = self.use_multi_thread.isChecked()
        self.config['thread_count'] = self.thread_count.value()
        self.config['use_proxy'] = self.use_proxy.isChecked()
        self.config['proxy'] = self.proxy.text()
        
        self.accept()


class ConfigFileDialog(QDialog):
    """配置文件对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("配置文件")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # 配置文件操作按钮
        button_layout = QHBoxLayout()
        
        import_button = QPushButton("导入配置")
        export_button = QPushButton("导出配置")
        
        import_button.clicked.connect(self.import_config)
        export_button.clicked.connect(self.export_config)
        
        button_layout.addWidget(import_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        
        layout.addStretch()
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(layout)
        
    def import_config(self):
        """导入配置文件"""
        if not hasattr(self.parent, "import_config"):
            QMessageBox.warning(self, "警告", "父窗口未实现导入配置方法")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            self.parent.import_config(file_path)
    
    def export_config(self):
        """导出配置文件"""
        if not hasattr(self.parent, "export_config"):
            QMessageBox.warning(self, "警告", "父窗口未实现导出配置方法")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            self.parent.export_config(file_path)


class DownloadDialog(QDialog):
    """下载Blender对话框"""
    def __init__(self, download_manager, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.download_manager = download_manager
        
        self.setWindowTitle("下载Blender")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        # 版本信息
        self.versions = []
        self.current_download = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 版本列表
        version_layout = QVBoxLayout()
        version_layout.addWidget(QLabel("可用版本:"))
        
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(4)
        self.version_table.setHorizontalHeaderLabels(["版本", "构建日期", "大小", "描述"])
        self.version_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.version_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.version_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.version_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.version_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.version_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.version_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        version_layout.addWidget(self.version_table)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新版本列表")
        refresh_button.clicked.connect(self.refresh_versions)
        version_layout.addWidget(refresh_button)
        
        layout.addLayout(version_layout)
        
        # 下载进度
        progress_group_layout = QVBoxLayout()
        progress_group_layout.addWidget(QLabel("下载进度:"))
        
        self.download_label = QLabel("未开始下载")
        progress_group_layout.addWidget(self.download_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_group_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_group_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("下载选中版本")
        self.download_button.clicked.connect(self.download_selected)
        self.download_button.setEnabled(False)
        
        self.install_button = QPushButton("下载并安装")
        self.install_button.clicked.connect(self.download_and_install)
        self.install_button.setEnabled(False)
        
        self.cancel_button = QPushButton("取消下载")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.version_table.itemSelectionChanged.connect(self.on_selection_change)
        self.download_manager.version_list_updated.connect(self.update_version_table)
        self.download_manager.download_progress.connect(self.update_progress)
        self.download_manager.download_finished.connect(self.download_finished)
        self.download_manager.download_error.connect(self.download_error)
        
        # 初始加载版本
        self.refresh_versions()
        
    def refresh_versions(self):
        """刷新版本列表"""
        from PyQt6.QtCore import QTimer
        # 禁用按钮
        self.download_button.setEnabled(False)
        self.install_button.setEnabled(False)
        
        # 清空表格
        self.version_table.setRowCount(0)
        self.download_label.setText("正在获取版本信息...")
        
        # 异步获取版本列表
        QTimer.singleShot(100, self.download_manager.get_available_versions)
        
    def update_version_table(self, versions):
        """更新版本表格"""
        self.versions = versions
        self.version_table.setRowCount(0)
        
        for version_info in versions:
            row = self.version_table.rowCount()
            self.version_table.insertRow(row)
            
            self.version_table.setItem(row, 0, QTableWidgetItem(version_info.version))
            self.version_table.setItem(row, 1, QTableWidgetItem(version_info.build_date or ""))
            self.version_table.setItem(row, 2, QTableWidgetItem(version_info.size or "未知"))
            self.version_table.setItem(row, 3, QTableWidgetItem(version_info.description or ""))
            
        self.download_label.setText(f"共找到 {len(versions)} 个可用版本")
        
    def on_selection_change(self):
        """选择变化事件"""
        has_selection = len(self.version_table.selectedItems()) > 0
        self.download_button.setEnabled(has_selection)
        self.install_button.setEnabled(has_selection)
        
    def download_selected(self):
        """下载选中版本"""
        selected_row = self.version_table.currentRow()
        if selected_row >= 0 and selected_row < len(self.versions):
            version_info = self.versions[selected_row]
            
            # 开始下载
            self.current_download = self.download_manager.download_blender(version_info)
            
            if self.current_download:
                self.download_label.setText(f"正在下载 Blender {version_info.version}...")
                self.download_button.setEnabled(False)
                self.install_button.setEnabled(False)
                self.cancel_button.setEnabled(True)
                self.progress_bar.setValue(0)
    
    def download_and_install(self):
        """下载并安装所选版本"""
        selected_row = self.version_table.currentRow()
        if selected_row >= 0 and selected_row < len(self.versions):
            version_info = self.versions[selected_row]
            
            # 开始下载
            self.current_download = self.download_manager.download_blender(version_info)
            
            if self.current_download:
                self.download_label.setText(f"正在下载 Blender {version_info.version}...")
                self.download_button.setEnabled(False)
                self.install_button.setEnabled(False)
                self.cancel_button.setEnabled(True)
                self.progress_bar.setValue(0)
                
                # 标记为安装
                self.install_after_download = True
            
    def cancel_download(self):
        """取消下载"""
        if self.current_download:
            self.download_manager.cancel_download(self.current_download)
            self.download_label.setText("下载已取消")
            self.current_download = None
            self.download_button.setEnabled(True)
            self.install_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.progress_bar.setValue(0)
            
    def update_progress(self, download_id, current, total):
        """更新下载进度"""
        if self.current_download and download_id == self.current_download:
            if total > 0:
                progress = int(current / total * 100)
                self.progress_bar.setValue(progress)
                
                # 显示下载速度和剩余时间
                
                current_time = QDateTime.currentMSecsSinceEpoch()
                if not hasattr(self, 'last_update_time'):
                    self.last_update_time = current_time
                    self.last_update_bytes = 0
                
                # 计算下载速度 (每秒)
                time_diff = current_time - self.last_update_time
                if time_diff > 1000:  # 每秒更新一次
                    bytes_diff = current - self.last_update_bytes
                    speed = bytes_diff / (time_diff / 1000)  # 字节/秒
                    
                    # 计算剩余时间
                    remaining_bytes = total - current
                    if speed > 0:
                        remaining_time = remaining_bytes / speed  # 秒
                        
                        # 格式化显示
                        speed_str = self._format_speed(speed)
                        time_str = self._format_time(remaining_time)
                        
                        self.download_label.setText(f"下载中: {current}/{total} 字节 ({progress}%) - {speed_str}, 剩余时间: {time_str}")
                    
                    # 更新上次更新时间和字节数
                    self.last_update_time = current_time
                    self.last_update_bytes = current
    
    def download_finished(self, download_id, save_path):
        """下载完成"""
        if self.current_download and download_id == self.current_download:
            self.download_label.setText(f"下载完成: {save_path}")
            self.progress_bar.setValue(100)
            self.cancel_button.setEnabled(False)
            self.download_button.setEnabled(True)
            self.install_button.setEnabled(True)
            
            # 检查是否需要安装
            if hasattr(self, 'install_after_download') and self.install_after_download:
                self.install_after_download = False
                self.install_downloaded(save_path)
            
    def download_error(self, download_id, error):
        """下载错误"""
        if self.current_download and download_id == self.current_download:
            self.download_label.setText(f"下载错误: {error}")
            self.cancel_button.setEnabled(False)
            self.download_button.setEnabled(True)
            self.install_button.setEnabled(True)
            
    def install_downloaded(self, zip_path):
        """安装下载的Blender"""
        # 如果主窗口存在并实现了add_blender方法
        if self.parent and hasattr(self.parent, 'blender_manager'):
            # 显示等待消息
            self.download_label.setText("正在解压安装包...")
            self.progress_bar.setRange(0, 0)  # 显示忙碌状态
            
            # 异步解压并安装
            
            class InstallThread(QThread):
                finished_signal = pyqtSignal(str)
                error_signal = pyqtSignal(str)
                
                def __init__(self, download_manager, zip_path):
                    super().__init__()
                    self.download_manager = download_manager
                    self.zip_path = zip_path
                    
                def run(self):
                    try:
                        # 解压Blender
                        blender_dir = self.download_manager.extract_blender(self.zip_path)
                        if blender_dir:
                            self.finished_signal.emit(blender_dir)
                        else:
                            self.error_signal.emit("解压失败，无法获取Blender目录")
                    except Exception as e:
                        self.error_signal.emit(str(e))
            
            # 创建并启动线程
            self.install_thread = InstallThread(self.download_manager, zip_path)
            self.install_thread.finished_signal.connect(self.on_install_finished)
            self.install_thread.error_signal.connect(self.on_install_error)
            self.install_thread.start()
        
    def on_install_finished(self, blender_dir):
        """安装完成"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        # 添加到Blender管理器
        if self.parent and hasattr(self.parent, 'blender_manager'):
            success, message = self.parent.blender_manager.add_blender(blender_dir)
            if success:
                self.download_label.setText(f"安装成功: {blender_dir}")
                # 更新版本表格
                if hasattr(self.parent, 'update_version_table'):
                    self.parent.update_version_table()
                
                # 提示用户
                QMessageBox.information(self, "成功", f"Blender已成功安装: {message}")
            else:
                self.download_label.setText(f"添加失败: {message}")
                QMessageBox.warning(self, "警告", f"Blender添加失败: {message}")
        
    def on_install_error(self, error):
        """安装错误"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.download_label.setText(f"安装错误: {error}")
        QMessageBox.critical(self, "错误", f"安装Blender时出错: {error}")
    
    def _format_speed(self, bytes_per_second):
        """格式化下载速度"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.2f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.2f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"
    
    def _format_time(self, seconds):
        """格式化时间"""
        if seconds < 60:
            return f"{int(seconds)} 秒"
        elif seconds < 3600:
            return f"{int(seconds // 60)} 分 {int(seconds % 60)} 秒"
        else:
            return f"{int(seconds // 3600)} 小时 {int((seconds % 3600) // 60)} 分"


class LaunchingDialog(QDialog):
    """启动等待界面，用于显示Vortex-Launcher启动进度"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在启动Vortex-Launcher")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # 布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("正在启动 Vortex-Launcher")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # 进度指示
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # 设置为确定状态
        layout.addWidget(self.progress_bar)
        
        # 状态文本
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 启动定时器
        from PyQt6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(50)  # 每50毫秒更新一次
        
        # 进度相关
        self.current_progress = 0
        self.target_progress = 0
        self.step = 1
        self.tasks = [
            "正在加载配置...",
            "正在初始化日志系统...",
            "正在检查环境...",
            "正在初始化界面组件...",
            "正在加载Blender版本信息...",
            "正在检查下载设置...",
            "正在连接信号与槽...",
            "准备就绪!"
        ]
        self.current_task = 0
        
    def _update_progress(self):
        """更新进度"""
        # 增加当前进度
        if self.current_progress < self.target_progress:
            self.current_progress += self.step
            self.progress_bar.setValue(self.current_progress)
            
        # 如果达到目标进度，设置下一个任务
        elif self.current_task < len(self.tasks) - 1:
            self.current_task += 1
            self.status_label.setText(self.tasks[self.current_task])
            self.target_progress = int((self.current_task + 1) * 100 / len(self.tasks))
            
        # 如果所有任务完成，关闭对话框
        elif self.current_progress >= 100:
            self.timer.stop()
            # 延迟关闭
            QTimer.singleShot(500, self.accept)
    
    def set_progress(self, value, message=None):
        """设置进度值和消息
        
        Args:
            value: 进度值 (0-100)
            message: 状态消息
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
    
    def start_task(self, task_index=None):
        """开始指定任务
        
        Args:
            task_index: 任务索引，如果为None则自动选择下一个任务
        """
        if task_index is not None:
            self.current_task = min(task_index, len(self.tasks) - 1)
        else:
            self.current_task += 1
            
        if self.current_task < len(self.tasks):
            self.status_label.setText(self.tasks[self.current_task])
            self.target_progress = int((self.current_task + 1) * 100 / len(self.tasks))


class BlenderLaunchDialog(QDialog):
    """Blender启动等待界面"""
    
    def __init__(self, version_info, blender_manager, index, parent=None):
        super().__init__(parent)
        self.version_info = version_info
        self.blender_manager = blender_manager
        self.blender_index = index
        self.setWindowTitle("正在启动Blender")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # 布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(f"正在启动 Blender {version_info['version']}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # 进度指示
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为忙碌状态
        layout.addWidget(self.progress_bar)
        
        # 状态文本
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.cancel_launch)
        layout.addWidget(cancel_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        
        # 启动定时器，延迟启动
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self.start_blender)
        
        # 用于存储进程
        self.process = None
        self.canceled = False
        
    def start_blender(self):
        """启动Blender"""
        # 更新状态
        self.status_label.setText("正在启动Blender...")
        
        # 使用线程启动Blender
        
        class LaunchThread(QThread):
            started_signal = pyqtSignal(object)
            finished_signal = pyqtSignal()
            error_signal = pyqtSignal(str)
            
            def __init__(self, blender_manager, index):
                super().__init__()
                self.blender_manager = blender_manager
                self.index = index
                
            def run(self):
                try:
                    # 启动Blender
                    success, message = self.blender_manager.launch_blender(self.index)
                    if success:
                        # 尝试获取进程，使用超时和重试机制
                        import time
                        max_attempts = 10
                        for attempt in range(max_attempts):
                            process = self.blender_manager.get_running_process(self.index)
                            if process:
                                self.started_signal.emit(process)
                                return
                            else:
                                # 等待100ms后再次尝试
                                time.sleep(0.1)
                                
                        # 如果所有尝试都失败
                        self.error_signal.emit("启动成功但无法获取进程，请检查Blender是否正常运行")
                    else:
                        self.error_signal.emit(message)
                except Exception as e:
                    self.error_signal.emit(str(e))
                
        # 创建并启动线程
        self.launch_thread = LaunchThread(self.blender_manager, self.blender_index)
        self.launch_thread.started_signal.connect(self.on_blender_started)
        self.launch_thread.error_signal.connect(self.on_launch_error)
        self.launch_thread.start()
    
    def on_blender_started(self, process):
        """Blender启动完成"""
        if self.canceled:
            return
            
        self.process = process
        self.status_label.setText("Blender已启动!")
        
        # 延迟关闭
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, self.accept)
    
    def on_launch_error(self, error):
        """启动错误"""
        if self.canceled:
            return
            
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "启动失败", f"启动Blender时出错: {error}")
        self.reject()
        
    def cancel_launch(self):
        """取消启动"""
        self.canceled = True
        
        if self.process:
            # 终止进程
            try:
                self.process.terminate()
            except:
                pass
        
        # 终止启动线程
        if hasattr(self, 'launch_thread') and self.launch_thread.isRunning():
            self.launch_thread.terminate()
            self.launch_thread.wait()
        
        self.reject()


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self, config, log_manager, blender_manager):
        super().__init__()
        self.config = config
        self.log_manager = log_manager
        self.blender_manager = blender_manager
        
        # 创建日志记录器
        self.logger = self.log_manager.get_logger("MainWindow", "vortex")
        
        # 创建下载管理器
        self.download_manager = DownloadManager(config, self.log_manager.get_logger("DownloadManager", "vortex"))
        
        self.logger.info("正在初始化主窗口...")
        self.initUI()
        self.logger.info("主窗口初始化完成")

    def initUI(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle('Vortex Launcher')
        self.setGeometry(300, 300, 800, 500)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建版本表格（表格显示添加的Blender路径）
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(2)
        self.version_table.setHorizontalHeaderLabels(["版本名称", "安装路径"])
        self.version_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.version_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.version_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.version_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.version_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.version_table.setMinimumHeight(300)
        self.version_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.version_table.customContextMenuRequested.connect(self.show_context_menu)
        self.version_table.doubleClicked.connect(self.on_table_double_clicked)
        
        main_layout.addWidget(QLabel("Blender版本:"))
        main_layout.addWidget(self.version_table)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建五个按钮
        self.add_button = QPushButton("添加Blender地址")
        self.delete_button = QPushButton("删除Blender地址")
        self.uninstall_button = QPushButton("卸载Blender")
        self.launch_button = QPushButton("启动Blender")
        self.download_button = QPushButton("下载Blender")
        
        # 连接按钮信号
        self.add_button.clicked.connect(self.add_blender)
        self.delete_button.clicked.connect(self.delete_blender)
        self.uninstall_button.clicked.connect(self.uninstall_blender)
        self.launch_button.clicked.connect(self.launch_blender)
        self.download_button.clicked.connect(self.show_download_dialog)
        
        # 添加按钮到布局
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.uninstall_button)
        button_layout.addWidget(self.launch_button)
        button_layout.addWidget(self.download_button)
        
        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)
        
        # 更新版本列表
        self.update_version_table()
        
        # 如果启用自动检测，则执行自动检测
        if self.config.get('auto_detect', False):
            self.logger.info("执行自动检测...")
            self.blender_manager.auto_detect_blender()
            self.update_version_table()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        config_menu = QMenu("配置", self)
        settings_action = QAction("设置", self)
        config_file_action = QAction("配置文件", self)
        log_settings_action = QAction("日志设置", self)
        config_menu.addAction(settings_action)
        config_menu.addAction(config_file_action)
        config_menu.addAction(log_settings_action)
        
        view_logs_action = QAction("查看日志", self)
        export_config_action = QAction("导出配置文件", self)
        import_config_action = QAction("导入配置文件", self)
        exit_action = QAction("退出", self)
        
        file_menu.addAction(view_logs_action)
        file_menu.addSeparator()
        file_menu.addAction(export_config_action)
        file_menu.addAction(import_config_action)
        file_menu.addSeparator()
        file_menu.addMenu(config_menu)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        add_blender_action = QAction("添加Blender地址", self)
        delete_blender_action = QAction("删除Blender地址", self)
        uninstall_blender_action = QAction("卸载Blender", self)
        launch_blender_action = QAction("启动Blender", self)
        download_blender_action = QAction("下载Blender", self)
        edit_version_action = QAction("编辑版本信息", self)
        
        edit_menu.addAction(add_blender_action)
        edit_menu.addAction(delete_blender_action)
        edit_menu.addAction(uninstall_blender_action)
        edit_menu.addAction(launch_blender_action)
        edit_menu.addSeparator()
        edit_menu.addAction(download_blender_action)
        edit_menu.addAction(edit_version_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        
        help_menu.addAction(about_action)
        
        # 连接菜单动作
        settings_action.triggered.connect(self.show_settings)
        config_file_action.triggered.connect(self.show_config_file)
        log_settings_action.triggered.connect(self.show_log_settings)
        view_logs_action.triggered.connect(self.view_logs)
        export_config_action.triggered.connect(lambda: self.export_config())
        import_config_action.triggered.connect(lambda: self.import_config())
        exit_action.triggered.connect(self.close)
        
        add_blender_action.triggered.connect(self.add_blender)
        delete_blender_action.triggered.connect(self.delete_blender)
        uninstall_blender_action.triggered.connect(self.uninstall_blender)
        launch_blender_action.triggered.connect(self.launch_blender)
        download_blender_action.triggered.connect(self.show_download_dialog)
        edit_version_action.triggered.connect(self.edit_version)
        
        about_action.triggered.connect(self.show_about)

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # 更新配置
            self.config['auto_detect'] = dialog.auto_detect.isChecked()
            self.config['auto_detect_path'] = dialog.auto_detect_path.text()
            self.config['quick_launch'] = dialog.quick_launch.isChecked()
            
            # 更新下载配置
            self.config['download_dir'] = dialog.download_dir.text()
            self.config['use_mirror'] = dialog.use_mirror.isChecked()
            self.config['mirror_url'] = dialog.mirror_url.text()
            self.config['use_multi_thread'] = dialog.use_multi_thread.isChecked()
            self.config['thread_count'] = dialog.thread_count.value()
            self.config['use_proxy'] = dialog.use_proxy.isChecked()
            self.config['proxy'] = dialog.proxy.text()
            
            # 更新下载管理器配置
            self.download_manager.update_config(self.config)
            
            # 如果启用自动检测，则执行自动检测
            if self.config.get('auto_detect', False):
                self.logger.info("执行自动检测...")
                self.blender_manager.auto_detect_blender(self.config.get('auto_detect_path'))
                self.update_version_table()

    def show_config_file(self):
        """显示配置文件对话框"""
        dialog = ConfigFileDialog(self)
        dialog.exec()

    def show_log_settings(self):
        """显示日志设置对话框"""
        dialog = LogSettingsDialog(self.config.get('log_config', {}), self)
        dialog.config_updated.connect(self.update_log_config)
        dialog.exec()

    def update_log_config(self, log_config):
        """更新日志配置"""
        self.config['log_config'] = log_config
        self.log_manager.update_config(log_config)
        self.logger.info("日志配置已更新")

    def view_logs(self):
        """查看日志"""
        dialog = LogViewerDialog(self.log_manager, self)
        dialog.exec()

    def export_config(self, file_path=None):
        """导出配置文件"""
        if file_path is None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存配置文件", "", "JSON 文件 (*.json)"
            )
        
        if file_path:
            try:
                self.logger.info(f"导出配置到文件: {file_path}")
                # 确保blender_paths是最新的
                self.config['blender_paths'] = self.blender_manager.blender_paths
                
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "成功", "配置已成功导出")
            except Exception as e:
                self.logger.error(f"导出配置时出错: {str(e)}")
                QMessageBox.critical(self, "错误", f"导出配置文件时出错: {str(e)}")

    def import_config(self, file_path=None):
        """导入配置文件"""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择配置文件", "", "JSON 文件 (*.json)"
            )
        
        if file_path:
            try:
                self.logger.info(f"从文件导入配置: {file_path}")
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                    
                # 更新配置
                self.config.update(imported_config)
                
                # 更新blender_paths
                self.blender_manager.blender_paths = self.config.get('blender_paths', [])
                
                # 如果有日志配置，更新日志管理器
                if 'log_config' in self.config:
                    self.log_manager.update_config(self.config['log_config'])
                
                # 更新版本列表
                self.update_version_table()
                
                QMessageBox.information(self, "成功", "配置已成功导入")
            except Exception as e:
                self.logger.error(f"导入配置时出错: {str(e)}")
                QMessageBox.critical(self, "错误", f"导入配置文件时出错: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取当前选中的行
        current_row = self.version_table.currentRow()
        
        if current_row >= 0:
            context_menu = QMenu(self)
            
            launch_action = QAction("启动", self)
            delete_action = QAction("删除", self)
            uninstall_action = QAction("卸载", self)
            edit_action = QAction("编辑", self)
            
            launch_action.triggered.connect(self.launch_blender)
            delete_action.triggered.connect(self.delete_blender)
            uninstall_action.triggered.connect(self.uninstall_blender)
            edit_action.triggered.connect(self.edit_version)
            
            context_menu.addAction(launch_action)
            context_menu.addAction(edit_action)
            context_menu.addAction(delete_action)
            context_menu.addAction(uninstall_action)
            
            context_menu.exec(QCursor.pos())

    def on_table_double_clicked(self, index):
        """表格双击事件"""
        if self.config.get('quick_launch', False):
            self.launch_blender()

    def update_version_table(self):
        """更新版本表格"""
        self.logger.debug("更新版本表格")
        self.version_table.setRowCount(0)
        
        for idx, path in enumerate(self.blender_manager.blender_paths):
            # 获取Blender信息
            info = self.blender_manager.get_blender_info(idx)
            if info:
                row = self.version_table.rowCount()
                self.version_table.insertRow(row)
                self.version_table.setItem(row, 0, QTableWidgetItem(info['version']))
                self.version_table.setItem(row, 1, QTableWidgetItem(info['path']))

    def add_blender(self):
        """添加Blender地址"""
        self.logger.info("添加Blender地址")
        directory = QFileDialog.getExistingDirectory(
            self, "选择Blender安装目录", "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            success, message = self.blender_manager.add_blender(directory)
            if success:
                self.logger.info(f"成功添加Blender地址: {directory}")
                self.update_version_table()
                QMessageBox.information(self, "成功", message)
            else:
                self.logger.warning(f"添加Blender地址失败: {message}")
                QMessageBox.warning(self, "警告", message)

    def delete_blender(self):
        """从列表中删除Blender地址"""
        current_row = self.version_table.currentRow()
        self.logger.info(f"删除Blender地址，行: {current_row}")
        
        if current_row >= 0:
            path = self.blender_manager.blender_paths[current_row]
            reply = QMessageBox.question(
                self, "确认", f"确定要从列表中删除此Blender地址吗？\n{path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.blender_manager.remove_blender(current_row)
                if success:
                    self.logger.info(f"成功删除Blender地址: {path}")
                    self.update_version_table()
                else:
                    self.logger.warning(f"删除Blender地址失败: {message}")
                    QMessageBox.warning(self, "警告", message)
        else:
            self.logger.warning("尝试删除Blender地址，但没有选择任何行")
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")

    def uninstall_blender(self):
        """卸载Blender（删除文件夹）"""
        current_row = self.version_table.currentRow()
        self.logger.info(f"卸载Blender，行: {current_row}")
        
        if current_row >= 0:
            path = self.blender_manager.blender_paths[current_row]
            reply = QMessageBox.warning(
                self, "警告",
                f"确定要卸载此Blender版本吗？这将删除整个Blender目录！\n{path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.blender_manager.uninstall_blender(current_row)
                if success:
                    self.logger.info(f"成功卸载Blender: {path}")
                    self.update_version_table()
                    QMessageBox.information(self, "成功", "Blender已成功卸载")
                else:
                    self.logger.warning(f"卸载Blender失败: {message}")
                    QMessageBox.warning(self, "警告", message)
        else:
            self.logger.warning("尝试卸载Blender，但没有选择任何行")
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")

    def launch_blender(self):
        """启动选中的Blender版本"""
        current_row = self.version_table.currentRow()
        self.logger.info(f"启动Blender，行: {current_row}")
        
        if current_row >= 0:
            path = self.blender_manager.blender_paths[current_row]
            # 获取版本信息
            info = self.blender_manager.get_blender_info(current_row)
            if info:
                # 显示启动等待界面
                dialog = BlenderLaunchDialog(info, self.blender_manager, current_row, self)
                result = dialog.exec()
                
                # 如果启动成功
                if result == QDialog.DialogCode.Accepted:
                    self.logger.info(f"成功启动Blender: {path}")
            else:
                # 如果没有获取到版本信息，使用旧方式启动
                success, message = self.blender_manager.launch_blender(current_row)
                if not success:
                    self.logger.warning(f"启动Blender失败: {message}")
                    QMessageBox.warning(self, "警告", message)
                else:
                    self.logger.info(f"成功启动Blender: {path}")
        else:
            self.logger.warning("尝试启动Blender，但没有选择任何行")
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")

    def show_download_dialog(self):
        """显示下载Blender对话框"""
        self.logger.info("打开下载Blender对话框")
        dialog = DownloadDialog(self.download_manager, self)
        dialog.exec()
        
    def edit_version(self):
        """编辑版本信息"""
        # 获取当前选中的行
        current_row = self.version_table.currentRow()
        self.logger.info(f"编辑版本信息，行: {current_row}")
        
        if current_row >= 0:
            # 获取当前版本信息
            info = self.blender_manager.get_blender_info(current_row)
            if info:
                # 创建编辑对话框
                dialog = VersionEditDialog(info, self)
                if dialog.exec():
                    # 获取新的版本信息
                    new_version = dialog.version_edit.text()
                    
                    # 更新版本信息
                    self.blender_manager.update_version_info(current_row, new_version)
                    
                    # 刷新表格
                    self.update_version_table()
                    
                    self.logger.info(f"版本信息已更新: {info['path']} -> {new_version}")
        else:
            self.logger.warning("尝试编辑版本信息，但没有选择任何行")
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")
    
    def closeEvent(self, event):
        """关闭事件，保存配置"""
        self.logger.info("保存配置并退出")
        # 确保blender_paths是最新的
        self.config['blender_paths'] = self.blender_manager.blender_paths
        
        # 保存配置
        import json
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"保存配置时出错: {str(e)}")
            QMessageBox.warning(self, "警告", f"保存配置时出错: {str(e)}")
        
        event.accept()


# 测试代码
if __name__ == "__main__":
    import sys
    import json
    from PyQt6.QtWidgets import QApplication
    from src.log import LogManager
    from src.blender_manager import BlenderManager
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 加载配置
    config = {}
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        pass
    
    # 创建日志管理器
    log_manager = LogManager(config.get('log_config', {}))
    
    # 创建Blender管理器
    blender_manager = BlenderManager(config, log_manager.get_logger("BlenderManager", "vortex"))
    
    # 创建主窗口
    window = MainWindow(config, log_manager, blender_manager)
    window.show()
    
    sys.exit(app.exec()) 