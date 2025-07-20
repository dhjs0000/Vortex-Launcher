from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton, 
    QTableWidgetItem, QHeaderView, QMessageBox, QMenu, QInputDialog,
    QLabel, QWidget, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor, QFont
import os
import subprocess
import psutil
from src.backup import BackupManager
import re
import time


class BackupProgressDialog(QDialog):
    """备份进度对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("备份进度")
        self.setFixedSize(400, 150)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在准备备份...")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 详细信息标签
        self.detail_label = QLabel("")
        layout.addWidget(self.detail_label)
        
        self.setLayout(layout)
    
    def update_progress(self, value, status="", detail=""):
        """更新进度"""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if detail:
            self.detail_label.setText(detail)
    
    def set_complete(self, success, message):
        """设置完成状态"""
        if success:
            self.status_label.setText("备份完成")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText("备份失败")
        self.detail_label.setText(message)


class BackupWorker(QThread):
    """备份工作线程"""
    
    progress_signal = pyqtSignal(int, str, str)  # 进度, 状态, 详情
    finished_signal = pyqtSignal(bool, str)  # 成功, 消息
    
    def __init__(self, blender_path, blender_name, backup_manager):
        super().__init__()
        self.blender_path = blender_path
        self.blender_name = blender_name
        self.backup_manager = backup_manager
        self.is_canceled = False
    
    def run(self):
        """执行备份"""
        try:
            self.progress_signal.emit(5, "正在准备备份...", "检查目录和文件")
            
            # 检查源目录是否存在
            if not os.path.exists(self.blender_path):
                self.finished_signal.emit(False, f"源目录不存在: {self.blender_path}")
                return
            
            # 进度回调函数
            def update_progress(value, status, detail):
                self.progress_signal.emit(value, status, detail)
            
            # 调用备份管理器执行备份，传入进度回调函数
            success, message = self.backup_manager.backup_blender(
                self.blender_path, 
                self.blender_name,
                update_progress
            )
            
            # 发送完成信号
            self.finished_signal.emit(success, message)
            
        except Exception as e:
            self.finished_signal.emit(False, f"备份过程中出错: {str(e)}")
    
    def cancel(self):
        """取消备份"""
        self.is_canceled = True


class BackupManagerDialog(QDialog):
    def __init__(self, parent=None, blenderName=None, blenderPath=None):
        super().__init__(parent)
        
        # 获取Blender版本号
        version = self._extract_version_from_path(blenderPath)
        
        # 设置备份路径为 AppData\Roaming\Blender Foundation\Blender\大版本号
        self.appdata_path = os.path.join(os.environ.get('APPDATA', ''), 'Blender Foundation', 'Blender')
        if version:
            self.appdata_source_dir = os.path.join(self.appdata_path, version)
            backup_dir = os.path.join(self.appdata_path, f"{version}_backup")
        else:
            self.appdata_source_dir = os.path.join(self.appdata_path, os.path.basename(blenderPath))
            backup_dir = os.path.join(self.appdata_path, f"{os.path.basename(blenderPath)}_backup")
        
        # 确保备份目录存在
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir, exist_ok=True)
            except Exception as e:
                print(f"创建备份目录失败: {str(e)}")
                # 如果创建失败，使用默认路径
                backup_dir = os.path.join(os.path.dirname(blenderPath), f"{blenderName}_backup")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)
        
        # 初始化备份管理器，使用AppData目录作为源目录
        self.BackupManager = BackupManager(self.appdata_source_dir, backup_dir)
        self.setWindowTitle("备份管理器")
        self.resize(800, 600)
        self.blenderName = blenderName
        self.blenderPath = blenderPath
        self.backup_dir = backup_dir
        self.version = version

        layout = QVBoxLayout()

        # 显示备份路径信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("源路径:"))
        source_label = QLabel(self.appdata_source_dir)
        source_label.setWordWrap(True)
        info_layout.addWidget(source_label)
        layout.addLayout(info_layout)
        
        # 显示备份路径信息
        backup_info_layout = QHBoxLayout()
        backup_info_layout.addWidget(QLabel("备份保存路径:"))
        path_label = QLabel(self.backup_dir)
        path_label.setWordWrap(True)
        backup_info_layout.addWidget(path_label)
        layout.addLayout(backup_info_layout)
        
        # 添加提示信息
        self._add_startup_file_tip(layout)

        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "日期", "大小", "地址"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建按钮
        backup_button = QPushButton("备份用户文件")
        restore_button = QPushButton("还原用户文件")
        delete_button = QPushButton("删除备份")
        rename_button = QPushButton("重命名备份")
        open_path_button = QPushButton("打开文件位置")
        
        # 连接按钮信号
        backup_button.clicked.connect(self.backup_selected)
        restore_button.clicked.connect(self.restore_selected)
        delete_button.clicked.connect(self.delete_selected)
        rename_button.clicked.connect(self.rename_selected)
        open_path_button.clicked.connect(self.open_file_path)
        
        # 添加按钮到布局
        button_layout.addWidget(backup_button)
        button_layout.addWidget(restore_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(rename_button)
        button_layout.addWidget(open_path_button)
        
        # 添加按钮布局到主布局
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 检查AppData目录是否存在
        if not os.path.exists(self.appdata_source_dir):
            QMessageBox.warning(
                self, 
                "警告", 
                f"Blender用户数据目录不存在：\n{self.appdata_source_dir}\n\n请先启动Blender创建配置文件。"
            )
        
        self.update_table()
    
    def _add_startup_file_tip(self, layout):
        """添加文件提示"""
        # 创建提示框
        tip_layout = QVBoxLayout()
        tip_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建提示容器
        tip_container = QWidget()
        tip_container.setStyleSheet("background-color: #EDF6FF; border: 1px solid #A0C8F0; border-radius: 5px;")
        tip_container_layout = QVBoxLayout(tip_container)
        tip_container_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建提示标签
        tip_label = QLabel(f"提示: 此功能用于备份和还原Blender的用户数据文件")
        tip_label.setStyleSheet("color: #0066CC; font-weight: bold; background: transparent;")
        tip_container_layout.addWidget(tip_label)
        
        # 创建说明标签
        info_label = QLabel(
            "用户数据文件包含Blender的用户配置、偏好设置、快捷键、附加组件设置等个人数据。"
            "备份这些文件可以在重装系统或更换电脑时恢复您的Blender个性化设置。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #000000; background: transparent;")
        tip_container_layout.addWidget(info_label)
        
        # 创建路径标签
        path_label = QLabel(f"用户数据路径: {self.appdata_source_dir}")
        path_label.setStyleSheet("color: #000000; background-color: #FFFFFF; padding: 8px; border: 1px solid #A0C8F0; border-radius: 3px;")
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_label.setWordWrap(True)
        tip_container_layout.addWidget(path_label)
        
        # 添加打开路径按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        open_button = QPushButton("打开用户数据目录")
        open_button.setStyleSheet("background-color: #0078D7; color: white; padding: 5px 15px; border: none; border-radius: 3px;")
        open_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_button.clicked.connect(self._open_appdata_path)
        button_layout.addWidget(open_button)
        
        tip_container_layout.addLayout(button_layout)
        
        # 添加到主布局
        tip_layout.addWidget(tip_container)
        
        # 添加分隔线
        separator = QLabel()
        separator.setFrameShape(QLabel.Shape.HLine)
        separator.setFrameShadow(QLabel.Shadow.Sunken)
        separator.setStyleSheet("margin-top: 5px; margin-bottom: 5px;")
        
        # 添加到主布局
        layout.addLayout(tip_layout)
        layout.addWidget(separator)
    
    def _open_appdata_path(self):
        """打开用户数据目录"""
        try:
            # 确保路径存在
            if not os.path.exists(self.appdata_source_dir):
                os.makedirs(self.appdata_source_dir, exist_ok=True)
                QMessageBox.information(self, "信息", f"已创建用户数据目录: {self.appdata_source_dir}")
            
            # 打开路径
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer', self.appdata_source_dir])
            elif os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
                subprocess.Popen(['open', self.appdata_source_dir])
            elif os.name == 'posix':  # Linux
                subprocess.Popen(['xdg-open', self.appdata_source_dir])
            else:
                QMessageBox.warning(self, "警告", "不支持的操作系统")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开文件位置失败: {str(e)}")

    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取当前选中的行
        current_row = self.table.currentRow()
        
        # 创建菜单
        context_menu = QMenu(self)
        
        # 添加备份按钮（无需选中行）
        backup_action = context_menu.addAction("进行备份")
        
        # 如果选中了行，添加与选中行相关的菜单项
        if current_row >= 0:
            context_menu.addSeparator()
            restore_action = context_menu.addAction("还原备份")
            rename_action = context_menu.addAction("重命名备份")
            delete_action = context_menu.addAction("删除备份")
            context_menu.addSeparator()
            open_path_action = context_menu.addAction("打开文件位置")
        
        # 显示菜单
        action = context_menu.exec(QCursor.pos())
        
        # 处理菜单动作
        if action == backup_action:
            self.backup_selected()
        elif current_row >= 0:  # 只有在选中行的情况下才处理这些操作
            if action == restore_action:
                self.restore_selected()
            elif action == rename_action:
                self.rename_selected()
            elif action == delete_action:
                self.delete_selected()
            elif action == open_path_action:
                self.open_file_path()
    
    def _extract_version_from_path(self, blender_path):
        """从Blender路径中提取版本号"""
        try:
            # 尝试从路径中提取版本号
            path_parts = blender_path.split(os.sep)
            for part in path_parts:
                # 匹配版本号模式，如 3.6, 4.0 等
                version_match = re.search(r'(\d+\.\d+)', part)
                if version_match:
                    return version_match.group(1)
            
            # 如果路径中没有找到，尝试从blender.exe获取版本
            blender_exe = os.path.join(blender_path, "blender.exe")
            if os.path.exists(blender_exe):
                import subprocess
                try:
                    result = subprocess.run(
                        [blender_exe, "-v"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10
                    )
                    if result.returncode == 0:
                        # 解析版本号
                        version_match = re.search(r'Blender (\d+\.\d+)', result.stdout)
                        if version_match:
                            return version_match.group(1)
                except:
                    pass
            
            return None
        except:
            return None

    def update_table(self):
        # 清空表格中的所有行
        self.table.setRowCount(0)
        # 获取备份信息
        backups = self.BackupManager.get_backups()
        # 遍历备份信息
        for name, info in backups.items():
            # 获取表格的行数
            row = self.table.rowCount()
            # 在表格中插入一行
            self.table.insertRow(row)
            # 在表格的第一列中插入备份名称
            self.table.setItem(row, 0, QTableWidgetItem(name))
            # 在表格的第二列中插入备份日期
            self.table.setItem(row, 1, QTableWidgetItem(info['date']))
            # 在表格的第三列中插入备份大小
            self.table.setItem(row, 2, QTableWidgetItem(info['size']))
            # 在表格的第四列中插入备份路径
            self.table.setItem(row, 3, QTableWidgetItem(info['path']))

    def backup_selected(self):
        """执行AppData备份操作"""
        # 检查AppData目录是否存在
        if not os.path.exists(self.appdata_source_dir):
            QMessageBox.warning(
                self, 
                "警告", 
                f"用户数据目录不存在：\n{self.appdata_source_dir}\n\n请先启动Blender创建配置文件。"
            )
            return
            
        # 检查AppData目录是否为空
        if not os.listdir(self.appdata_source_dir):
            QMessageBox.warning(
                self, 
                "警告", 
                f"用户数据目录为空：\n{self.appdata_source_dir}\n\n请先启动Blender创建配置文件。"
            )
            return
        
        # 创建进度对话框
        progress_dialog = BackupProgressDialog(self)
        progress_dialog.show()
        QApplication.processEvents()  # 确保对话框显示
        
        # 创建备份工作线程
        self.backup_worker = BackupWorker(self.appdata_source_dir, self.blenderName, self.BackupManager)
        
        # 连接信号
        self.backup_worker.progress_signal.connect(progress_dialog.update_progress)
        self.backup_worker.finished_signal.connect(progress_dialog.set_complete)
        self.backup_worker.finished_signal.connect(self._on_backup_finished)
        
        # 开始备份
        self.backup_worker.start()
        
        # 等待备份完成
        progress_dialog.exec()
        
        # 清理工作线程
        if hasattr(self, 'backup_worker'):
            self.backup_worker.wait()  # 等待线程结束
            self.backup_worker.deleteLater()
    
    def _on_backup_finished(self, success, message):
        """备份完成回调"""
        if success:
            QMessageBox.information(self, "成功", f"用户数据备份成功！\n{message}")
            # 更新表格
            self.update_table()
        else:
            QMessageBox.warning(self, "失败", f"用户数据备份失败：{message}")

    def restore_selected(self):
        """还原选中的AppData备份"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # 获取备份文件名和路径
            backup_name = self.table.item(current_row, 0).text()
            backup_path = self.table.item(current_row, 3).text()
            
            # 确认是否还原
            reply = QMessageBox.question(
                self, "确认还原", 
                f"确定要还原用户数据备份 {backup_name} 吗？\n这将覆盖当前的用户数据文件！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 检查Blender是否正在运行
                blender_running = False
                for proc in psutil.process_iter(['name']):
                    if 'blender' in proc.info['name'].lower():
                        blender_running = True
                        break
                
                if blender_running:
                    warning_reply = QMessageBox.warning(
                        self, 
                        "警告", 
                        "检测到Blender正在运行。还原用户数据文件需要关闭Blender。\n\n是否继续？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if warning_reply != QMessageBox.StandardButton.Yes:
                        return
                
                # 执行还原操作
                success, message = self.BackupManager.restore_backup(backup_path, self.appdata_source_dir)
                if success:
                    QMessageBox.information(self, "成功", "用户数据文件还原成功")
                else:
                    QMessageBox.warning(self, "失败", message)
        else:
            QMessageBox.information(self, "信息", "请先选择一个备份")

    def delete_selected(self):
        """删除选中的备份"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # 获取备份文件名
            backup_name = self.table.item(current_row, 0).text()
            
            # 确认是否删除
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除备份 {backup_name} 吗？\n此操作不可恢复！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 执行删除操作
                success, message = self.BackupManager.delete_backup(backup_name)
                if success:
                    QMessageBox.information(self, "成功", message)
                    # 更新表格
                    self.update_table()
                else:
                    QMessageBox.warning(self, "失败", message)
        else:
            QMessageBox.information(self, "信息", "请先选择一个备份")

    def rename_selected(self):
        """重命名选中的备份"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # 获取备份文件名
            old_name = self.table.item(current_row, 0).text()
            
            # 弹出输入对话框
            new_name, ok = QInputDialog.getText(
                self, "重命名备份", 
                "请输入新的备份名称：", 
                text=old_name
            )
            
            if ok and new_name:
                # 执行重命名操作
                success, message = self.BackupManager.rename_backup(old_name, new_name)
                if success:
                    QMessageBox.information(self, "成功", message)
                    # 更新表格
                    self.update_table()
                else:
                    QMessageBox.warning(self, "失败", message)
        else:
            QMessageBox.information(self, "信息", "请先选择一个备份")

    def open_file_path(self):
        """打开文件所在位置"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # 获取备份文件路径
            file_path = self.table.item(current_row, 3).text()
            
            # 获取文件所在目录
            dir_path = os.path.dirname(file_path)
            
            # 检查目录是否存在
            if os.path.exists(dir_path):
                try:
                    # 在Windows上使用explorer打开文件夹
                    if os.name == 'nt':
                        subprocess.Popen(['explorer', dir_path])
                    # 在macOS上使用open命令
                    elif os.name == 'posix' and os.uname().sysname == 'Darwin':
                        subprocess.Popen(['open', dir_path])
                    # 在Linux上使用xdg-open
                    elif os.name == 'posix':
                        subprocess.Popen(['xdg-open', dir_path])
                    else:
                        QMessageBox.warning(self, "警告", "不支持的操作系统")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"打开文件位置失败: {str(e)}")
            else:
                QMessageBox.warning(self, "错误", f"文件夹不存在: {dir_path}")
        else:
            QMessageBox.information(self, "信息", "请先选择一个备份")
