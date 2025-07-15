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
    QLineEdit, QGridLayout, QTabWidget, QTextEdit
)
from PyQt6.QtGui import QAction, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize

from src.log import LogViewerDialog, LogSettingsDialog
from src.blender_manager import BlenderManager


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
        
        # 添加选项卡
        tabs.addTab(file_tab, "文件")
        tabs.addTab(edit_tab, "编辑")
        
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

    def save_settings(self):
        """保存设置"""
        self.config['auto_detect'] = self.auto_detect.isChecked()
        self.config['auto_detect_path'] = self.auto_detect_path.text()
        self.config['quick_launch'] = self.quick_launch.isChecked()
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


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self, config, log_manager, blender_manager):
        super().__init__()
        self.config = config
        self.log_manager = log_manager
        self.blender_manager = blender_manager
        
        # 创建日志记录器
        self.logger = self.log_manager.get_logger("MainWindow", "vortex")
        
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
        
        # 创建四个按钮
        self.add_button = QPushButton("添加Blender地址")
        self.delete_button = QPushButton("删除Blender地址")
        self.uninstall_button = QPushButton("卸载Blender")
        self.launch_button = QPushButton("启动Blender")
        
        # 连接按钮信号
        self.add_button.clicked.connect(self.add_blender)
        self.delete_button.clicked.connect(self.delete_blender)
        self.uninstall_button.clicked.connect(self.uninstall_blender)
        self.launch_button.clicked.connect(self.launch_blender)
        
        # 添加按钮到布局
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.uninstall_button)
        button_layout.addWidget(self.launch_button)
        
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
        
        edit_menu.addAction(add_blender_action)
        edit_menu.addAction(delete_blender_action)
        edit_menu.addAction(uninstall_blender_action)
        edit_menu.addAction(launch_blender_action)
        
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
        
        about_action.triggered.connect(self.show_about)

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # 更新配置
            self.config['auto_detect'] = dialog.auto_detect.isChecked()
            self.config['auto_detect_path'] = dialog.auto_detect_path.text()
            self.config['quick_launch'] = dialog.quick_launch.isChecked()
            
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
            
            launch_action.triggered.connect(self.launch_blender)
            delete_action.triggered.connect(self.delete_blender)
            uninstall_action.triggered.connect(self.uninstall_blender)
            
            context_menu.addAction(launch_action)
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
            success, message = self.blender_manager.launch_blender(current_row)
            
            if not success:
                self.logger.warning(f"启动Blender失败: {message}")
                QMessageBox.warning(self, "警告", message)
            else:
                self.logger.info(f"成功启动Blender: {path}")
        else:
            self.logger.warning("尝试启动Blender，但没有选择任何行")
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