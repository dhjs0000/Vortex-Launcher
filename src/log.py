#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Vortex-Launcher - 日志管理模块
# Copyright (C) 2025 dhjs0000
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import logging
import datetime
import time
import gzip
import shutil
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QTabWidget, QWidget, QGridLayout, QCheckBox, QLineEdit,
    QSpinBox, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QDir


class LogHighlighter(QSyntaxHighlighter):
    """日志语法高亮器"""
    
    def __init__(self, parent=None):
        super(LogHighlighter, self).__init__(parent)
        
        self.highlighting_rules = []
        
        # 错误格式
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(255, 0, 0))  # 红色
        error_format.setFontWeight(QFont.Weight.Bold)
        error_pattern = QRegularExpression(r'ERROR|Error|error|Exception|EXCEPTION|exception')
        self.highlighting_rules.append((error_pattern, error_format))
        
        # 警告格式
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 165, 0))  # 橙色
        warning_pattern = QRegularExpression(r'WARNING|Warning|warning')
        self.highlighting_rules.append((warning_pattern, warning_format))
        
        # 信息格式
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 128, 0))  # 绿色
        info_pattern = QRegularExpression(r'INFO|Info|info')
        self.highlighting_rules.append((info_pattern, info_format))
        
        # 调试格式
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))  # 灰色
        debug_pattern = QRegularExpression(r'DEBUG|Debug|debug')
        self.highlighting_rules.append((debug_pattern, debug_format))
        
        # Vortex标识
        vortex_format = QTextCharFormat()
        vortex_format.setForeground(QColor(0, 0, 255))  # 蓝色
        vortex_format.setFontWeight(QFont.Weight.Bold)
        vortex_pattern = QRegularExpression(r'Vortex-Launcher')
        self.highlighting_rules.append((vortex_pattern, vortex_format))
        
        # Blender标识
        blender_format = QTextCharFormat()
        blender_format.setForeground(QColor(128, 0, 128))  # 紫色
        blender_format.setFontWeight(QFont.Weight.Bold)
        blender_pattern = QRegularExpression(r'Blender')
        self.highlighting_rules.append((blender_pattern, blender_format))
    
    def highlightBlock(self, text):
        """高亮文本块"""
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class LogManager:
    """日志管理器"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.loggers = {}
        self.log_dir = self.config.get('log_dir', 'logs')
        self.log_name_format = self.config.get('log_name_format', '%Y-%m-%d-%H%M%S')
        self.max_log_size = self.config.get('max_log_size', 10 * 1024 * 1024)  # 默认10MB
        self.compress_logs = self.config.get('compress_logs', False)
        self.enabled = self.config.get('log_enabled', True)
        
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def get_logger(self, name, log_type='combined'):
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            log_type: 日志类型，可以是'vortex'、'blender'或'combined'
        
        Returns:
            logging.Logger: 日志记录器对象
        """
        if not self.enabled:
            # 如果日志功能被禁用，返回一个空的日志记录器
            logger = logging.getLogger(name)
            if logger.hasHandlers():
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
            logger.addHandler(logging.NullHandler())
            return logger
        
        # 检查是否已经创建了该记录器
        logger_key = f"{name}_{log_type}"
        if logger_key in self.loggers:
            return self.loggers[logger_key]
        
        # 创建日志记录器
        logger = logging.getLogger(logger_key)
        logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        if logger.hasHandlers():
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
        
        # 创建文件名
        timestamp = datetime.datetime.now().strftime(self.log_name_format)
        if log_type == 'vortex':
            filename = f"vortex-{timestamp}.log"
        elif log_type == 'blender':
            filename = f"blender-{timestamp}.log"
        else:  # combined
            filename = f"combined-{timestamp}.log"
        
        log_path = os.path.join(self.log_dir, filename)
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_log_size,
            backupCount=5,
            encoding='utf-8'
        )
        
        # 设置格式
        if log_type == 'vortex':
            formatter = logging.Formatter(
                '%(asctime)s [Vortex-Launcher] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        elif log_type == 'blender':
            formatter = logging.Formatter(
                '%(asctime)s [Blender] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:  # combined
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 如果是终端运行，添加控制台输出
        if not hasattr(sys, 'frozen'):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 存储日志记录器
        self.loggers[logger_key] = logger
        return logger
    
    def get_log_files(self):
        """获取所有日志文件
        
        Returns:
            dict: 按照日志类型分类的日志文件列表
        """
        if not os.path.exists(self.log_dir):
            return {'vortex': [], 'blender': [], 'combined': []}
        
        log_files = {'vortex': [], 'blender': [], 'combined': []}
        for file in os.listdir(self.log_dir):
            if file.endswith('.log') or file.endswith('.log.gz'):
                if file.startswith('vortex-'):
                    log_files['vortex'].append(file)
                elif file.startswith('blender-'):
                    log_files['blender'].append(file)
                elif file.startswith('combined-'):
                    log_files['combined'].append(file)
        
        # 按照时间排序
        for log_type in log_files:
            log_files[log_type].sort(reverse=True)
        
        return log_files
    
    def compress_old_logs(self):
        """压缩旧日志文件"""
        if not self.compress_logs:
            return
        
        for file in os.listdir(self.log_dir):
            if file.endswith('.log') and not file.endswith('.log.gz'):
                log_path = os.path.join(self.log_dir, file)
                # 判断文件是否是今天创建的
                file_time = os.path.getctime(log_path)
                now = time.time()
                # 如果文件创建时间超过24小时，则压缩
                if now - file_time > 86400:  # 24小时 = 86400秒
                    with open(log_path, 'rb') as f_in:
                        with gzip.open(f"{log_path}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(log_path)
    
    def read_log_file(self, filename):
        """读取日志文件内容
        
        Args:
            filename: 日志文件名
        
        Returns:
            str: 日志文件内容
        """
        file_path = os.path.join(self.log_dir, filename)
        if not os.path.exists(file_path):
            return "日志文件不存在"
        
        try:
            if filename.endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    return f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            return f"读取日志文件时出错: {str(e)}"
    
    def update_config(self, config):
        """更新日志配置
        
        Args:
            config: 新的配置字典
        """
        self.config.update(config)
        self.log_dir = self.config.get('log_dir', 'logs')
        self.log_name_format = self.config.get('log_name_format', '%Y-%m-%d-%H%M%S')
        self.max_log_size = self.config.get('max_log_size', 10 * 1024 * 1024)
        self.compress_logs = self.config.get('compress_logs', False)
        self.enabled = self.config.get('log_enabled', True)
        
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 清空现有记录器，让其重新创建
        self.loggers = {}


class LogViewerDialog(QDialog):
    """日志查看器对话框"""
    
    def __init__(self, log_manager, parent=None):
        super().__init__(parent)
        self.log_manager = log_manager
        self.setWindowTitle("日志查看器")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
        self.load_log_files()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧树形视图
        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabel("日志文件")
        self.log_tree.setMinimumWidth(200)
        self.log_tree.itemClicked.connect(self.on_log_item_clicked)
        
        # 右侧文本编辑器
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # 创建语法高亮器
        self.highlighter = LogHighlighter(self.log_text.document())
        
        # 添加到分割器
        splitter.addWidget(self.log_tree)
        splitter.addWidget(self.log_text)
        splitter.setSizes([200, 600])
        
        # 添加分割器到布局
        layout.addWidget(splitter)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_log_files)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_log_files(self):
        """加载日志文件列表"""
        self.log_tree.clear()
        
        # 获取所有日志文件
        log_files = self.log_manager.get_log_files()
        
        # 创建Vortex-Launcher日志节点
        vortex_item = QTreeWidgetItem(self.log_tree, ["Vortex-Launcher 日志"])
        for file in log_files['vortex']:
            QTreeWidgetItem(vortex_item, [file])
        
        # 创建Blender日志节点
        blender_item = QTreeWidgetItem(self.log_tree, ["Blender 日志"])
        for file in log_files['blender']:
            QTreeWidgetItem(blender_item, [file])
        
        # 创建组合日志节点
        combined_item = QTreeWidgetItem(self.log_tree, ["组合日志"])
        for file in log_files['combined']:
            QTreeWidgetItem(combined_item, [file])
        
        # 展开所有节点
        self.log_tree.expandAll()
    
    def on_log_item_clicked(self, item, column):
        """点击日志项"""
        # 检查是否是日志文件（即有父节点的项）
        if item.parent() is not None:
            filename = item.text(0)
            self.log_text.setText(self.log_manager.read_log_file(filename))


class LogSettingsDialog(QDialog):
    """日志设置对话框"""
    
    config_updated = pyqtSignal(dict)
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.setWindowTitle("日志设置")
        self.setMinimumSize(500, 300)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 创建设置网格
        grid_layout = QGridLayout()
        
        # 是否启用日志
        self.log_enabled = QCheckBox("启用日志功能")
        self.log_enabled.setChecked(self.config.get('log_enabled', True))
        grid_layout.addWidget(self.log_enabled, 0, 0, 1, 2)
        
        # 日志文件路径
        grid_layout.addWidget(QLabel("日志文件路径:"), 1, 0)
        self.log_dir = QLineEdit()
        self.log_dir.setText(self.config.get('log_dir', 'logs'))
        grid_layout.addWidget(self.log_dir, 1, 1)
        
        # 浏览按钮
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_log_dir)
        grid_layout.addWidget(browse_button, 1, 2)
        
        # 日志文件名格式
        grid_layout.addWidget(QLabel("日志文件名格式:"), 2, 0)
        self.log_name_format = QLineEdit()
        self.log_name_format.setText(self.config.get('log_name_format', '%Y-%m-%d-%H%M%S'))
        self.log_name_format.setToolTip("使用Python的datetime格式，例如：%Y-%m-%d-%H%M%S")
        grid_layout.addWidget(self.log_name_format, 2, 1, 1, 2)
        
        # 日志文件大小
        grid_layout.addWidget(QLabel("日志文件大小(MB):"), 3, 0)
        self.max_log_size = QSpinBox()
        self.max_log_size.setRange(1, 100)
        self.max_log_size.setValue(int(self.config.get('max_log_size', 10 * 1024 * 1024) / (1024 * 1024)))
        grid_layout.addWidget(self.max_log_size, 3, 1, 1, 2)
        
        # 是否压缩
        self.compress_logs = QCheckBox("压缩旧日志文件")
        self.compress_logs.setChecked(self.config.get('compress_logs', False))
        grid_layout.addWidget(self.compress_logs, 4, 0, 1, 2)
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
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
    
    def browse_log_dir(self):
        """浏览日志目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择日志目录", self.log_dir.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.log_dir.setText(directory)
    
    def save_settings(self):
        """保存设置"""
        try:
            # 检查日志目录是否存在，不存在则创建
            log_dir = self.log_dir.text()
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 更新配置
            self.config['log_enabled'] = self.log_enabled.isChecked()
            self.config['log_dir'] = log_dir
            self.config['log_name_format'] = self.log_name_format.text()
            self.config['max_log_size'] = self.max_log_size.value() * 1024 * 1024
            self.config['compress_logs'] = self.compress_logs.isChecked()
            
            # 发出信号
            self.config_updated.emit(self.config)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置时出错: {str(e)}")


# 测试代码
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建日志管理器
    log_manager = LogManager()
    
    # 获取日志记录器
    vortex_logger = log_manager.get_logger("test", "vortex")
    blender_logger = log_manager.get_logger("test", "blender")
    combined_logger = log_manager.get_logger("test", "combined")
    
    # 写入一些日志
    vortex_logger.debug("这是一个调试信息")
    vortex_logger.info("这是一个信息")
    vortex_logger.warning("这是一个警告")
    vortex_logger.error("这是一个错误")
    
    blender_logger.debug("这是一个Blender调试信息")
    blender_logger.info("这是一个Blender信息")
    blender_logger.warning("这是一个Blender警告")
    blender_logger.error("这是一个Blender错误")
    
    combined_logger.debug("这是一个组合调试信息")
    combined_logger.info("这是一个组合信息")
    combined_logger.warning("这是一个组合警告")
    combined_logger.error("这是一个组合错误")
    
    # 显示日志查看器
    dialog = LogViewerDialog(log_manager)
    dialog.exec() 