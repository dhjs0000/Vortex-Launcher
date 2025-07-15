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

import sys
import os
import shutil
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QMessageBox,
    QListWidgetItem, QMenu, QMenuBar, QDialog, QCheckBox,
    QLineEdit, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTabWidget, QTextEdit
)
from PyQt6.QtGui import QAction, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize


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
        
        version_label = QLabel("Beta 1.0.0")
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'blender_paths' in config:
                        self.parent.blender_paths = config['blender_paths']
                        self.parent.updateVersionList()
                        self.parent.saveConfig()
                        QMessageBox.information(self, "成功", "配置已成功导入")
                    else:
                        QMessageBox.warning(self, "警告", "配置文件格式不正确")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置文件时出错: {str(e)}")
    
    def export_config(self):
        """导出配置文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            try:
                config = {'blender_paths': self.parent.blender_paths}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "成功", "配置已成功导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置文件时出错: {str(e)}")


class VortexLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blender_paths = []
        self.config_file = "config.json"
        self.config = {
            'blender_paths': [],
            'auto_detect': False,
            'auto_detect_path': '',
            'quick_launch': False
        }
        
        self.initUI()
        self.loadConfig()
        
        # 如果启用自动检测，则执行自动检测
        if self.config.get('auto_detect', False):
            self.autoDetectBlender()
    
    def initUI(self):
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
        self.add_button.clicked.connect(self.addBlender)
        self.delete_button.clicked.connect(self.deleteBlender)
        self.uninstall_button.clicked.connect(self.uninstallBlender)
        self.launch_button.clicked.connect(self.launchBlender)
        
        # 添加按钮到布局
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.uninstall_button)
        button_layout.addWidget(self.launch_button)
        
        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        config_menu = QMenu("配置", self)
        settings_action = QAction("设置", self)
        config_file_action = QAction("配置文件", self)
        config_menu.addAction(settings_action)
        config_menu.addAction(config_file_action)
        
        add_config_action = QAction("添加配置文件", self)
        export_config_action = QAction("导出配置文件", self)
        import_config_action = QAction("导入配置文件", self)
        exit_action = QAction("退出", self)
        
        file_menu.addAction(add_config_action)
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
        add_config_action.triggered.connect(self.show_config_file)
        export_config_action.triggered.connect(self.export_config)
        import_config_action.triggered.connect(self.import_config)
        exit_action.triggered.connect(self.close)
        
        add_blender_action.triggered.connect(self.addBlender)
        delete_blender_action.triggered.connect(self.deleteBlender)
        uninstall_blender_action.triggered.connect(self.uninstallBlender)
        launch_blender_action.triggered.connect(self.launchBlender)
        
        about_action.triggered.connect(self.show_about)
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.saveConfig()
            # 如果启用自动检测，则执行自动检测
            if self.config.get('auto_detect', False):
                self.autoDetectBlender()
    
    def show_config_file(self):
        """显示配置文件对话框"""
        dialog = ConfigFileDialog(self)
        dialog.exec()
    
    def export_config(self):
        """导出配置文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            try:
                config_to_save = self.config.copy()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_to_save, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "成功", "配置已成功导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置文件时出错: {str(e)}")
    
    def import_config(self):
        """导入配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                    if 'blender_paths' in imported_config:
                        self.config.update(imported_config)
                        self.blender_paths = self.config['blender_paths']
                        self.updateVersionList()
                        self.saveConfig()
                        QMessageBox.information(self, "成功", "配置已成功导入")
                    else:
                        QMessageBox.warning(self, "警告", "配置文件格式不正确")
            except Exception as e:
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
            
            launch_action.triggered.connect(self.launchBlender)
            delete_action.triggered.connect(self.deleteBlender)
            uninstall_action.triggered.connect(self.uninstallBlender)
            
            context_menu.addAction(launch_action)
            context_menu.addAction(delete_action)
            context_menu.addAction(uninstall_action)
            
            context_menu.exec(QCursor.pos())
    
    def on_table_double_clicked(self, index):
        """表格双击事件"""
        if self.config.get('quick_launch', False):
            self.launchBlender()

    def loadConfig(self):
        """从配置文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    self.blender_paths = self.config['blender_paths']
                    self.updateVersionList()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法加载配置文件: {str(e)}")

    def saveConfig(self):
        """保存配置到文件"""
        try:
            self.config['blender_paths'] = self.blender_paths
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法保存配置文件: {str(e)}")

    def updateVersionList(self):
        """更新版本表格"""
        self.version_table.setRowCount(0)
        for path in self.blender_paths:
            # 提取Blender版本名称，通常是文件夹名
            version_name = os.path.basename(path)
            
            row = self.version_table.rowCount()
            self.version_table.insertRow(row)
            self.version_table.setItem(row, 0, QTableWidgetItem(version_name))
            self.version_table.setItem(row, 1, QTableWidgetItem(path))
    
    def autoDetectBlender(self):
        """自动检测Blender安装目录"""
        if not self.config.get('auto_detect', False) or not self.config.get('auto_detect_path'):
            return
        
        auto_detect_path = self.config.get('auto_detect_path')
        if not os.path.exists(auto_detect_path):
            QMessageBox.warning(self, "警告", f"指定的自动检测目录不存在: {auto_detect_path}")
            return
        
        try:
            # 查找目录下的所有子目录
            subdirs = [os.path.join(auto_detect_path, d) for d in os.listdir(auto_detect_path) 
                      if os.path.isdir(os.path.join(auto_detect_path, d))]
            
            # 检查每个子目录是否为Blender安装目录
            for subdir in subdirs:
                blender_exe = os.path.join(subdir, "blender.exe")
                if os.path.exists(blender_exe):
                    # 如果是Blender目录且不在列表中，则添加
                    if subdir not in self.blender_paths:
                        self.blender_paths.append(subdir)
            
            # 更新版本列表
            self.updateVersionList()
            self.saveConfig()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"自动检测Blender时出错: {str(e)}")

    def addBlender(self):
        """添加Blender地址"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择Blender安装目录", "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # 确认是Blender目录（简单检查，可能需要更复杂的验证）
            blender_exe = os.path.join(directory, "blender.exe")
            if os.path.exists(blender_exe):
                if directory not in self.blender_paths:
                    self.blender_paths.append(directory)
                    self.updateVersionList()
                    self.saveConfig()
                else:
                    QMessageBox.information(self, "信息", "该Blender路径已存在")
            else:
                QMessageBox.warning(self, "警告", "所选目录不是有效的Blender安装目录")

    def deleteBlender(self):
        """从列表中删除Blender地址"""
        current_row = self.version_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "确认", "确定要从列表中删除此Blender地址吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.blender_paths[current_row]
                self.updateVersionList()
                self.saveConfig()
        else:
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")

    def uninstallBlender(self):
        """卸载Blender（删除文件夹）"""
        current_row = self.version_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.warning(
                self, "警告",
                "确定要卸载此Blender版本吗？这将删除整个Blender目录！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    path = self.blender_paths[current_row]
                    shutil.rmtree(path)
                    del self.blender_paths[current_row]
                    self.updateVersionList()
                    self.saveConfig()
                    QMessageBox.information(self, "成功", "Blender已成功卸载")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"卸载失败: {str(e)}")
        else:
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")

    def launchBlender(self):
        """启动选中的Blender版本"""
        current_row = self.version_table.currentRow()
        if current_row >= 0:
            try:
                path = self.blender_paths[current_row]
                blender_exe = os.path.join(path, "blender.exe")
                if os.path.exists(blender_exe):
                    os.startfile(blender_exe)
                else:
                    QMessageBox.warning(self, "警告", "找不到blender.exe")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
        else:
            QMessageBox.information(self, "信息", "请先选择一个Blender版本")


def main():
    app = QApplication(sys.argv)
    window = VortexLauncher()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 