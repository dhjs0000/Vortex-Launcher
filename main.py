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
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize


class VortexLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blender_paths = []
        self.config_file = "config.json"
        self.initUI()
        self.loadConfig()

    def initUI(self):
        # 设置窗口基本属性
        self.setWindowTitle('Vortex Launcher')
        self.setGeometry(300, 300, 600, 400)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建版本栏（列表显示添加的Blender路径）
        self.version_list = QListWidget()
        self.version_list.setMinimumHeight(200)
        main_layout.addWidget(QLabel("Blender版本:"))
        main_layout.addWidget(self.version_list)
        
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

    def loadConfig(self):
        """从配置文件加载Blender路径"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'blender_paths' in config:
                        self.blender_paths = config['blender_paths']
                        self.updateVersionList()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法加载配置文件: {str(e)}")

    def saveConfig(self):
        """保存配置到文件"""
        try:
            config = {'blender_paths': self.blender_paths}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法保存配置文件: {str(e)}")

    def updateVersionList(self):
        """更新版本列表"""
        self.version_list.clear()
        for path in self.blender_paths:
            # 提取Blender版本名称，通常是文件夹名
            version_name = os.path.basename(path)
            item = QListWidgetItem(f"{version_name} - {path}")
            self.version_list.addItem(item)

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
        current_row = self.version_list.currentRow()
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
        current_row = self.version_list.currentRow()
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
        current_row = self.version_list.currentRow()
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