import os
import shutil
import zipfile
import time

class BackupManager:
    def __init__(self, source_dir, backup_dir):
        # 初始化备份类，传入源目录和备份目录
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        self.backup_history = []
        # 初始化备份历史列表
        self.backups = {}

    def backup_blender(self, path, name, progress_callback=None):
        """备份Blender文件
        
        Args:
            path: Blender路径
            name: Blender名称
            progress_callback: 进度回调函数，接收参数(进度值, 状态文本, 详情文本)
            
        Returns:
            tuple: (成功标志, 消息)
        """
        try:
            # 创建备份目录（如果不存在）
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
                
            # 创建备份文件名
            backup_name = f"{name}_{time.strftime('%Y%m%d_%H%M%S')}.zip"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # 创建zip文件备份
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历源目录
                file_count = 0
                total_files = 0
                
                # 先计算总文件数
                for root, dirs, files in os.walk(path):
                    total_files += len(files)
                
                # 如果有回调函数，更新进度
                if progress_callback:
                    progress_callback(20, "开始压缩文件...", f"共 {total_files} 个文件")
                
                # 开始压缩文件
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 添加文件到zip
                        zipf.write(file_path, os.path.relpath(file_path, path))
                        
                        # 更新进度
                        file_count += 1
                        if progress_callback and total_files > 0:
                            progress = 20 + int(file_count / total_files * 70)  # 20%-90%的进度
                            progress_callback(progress, "正在备份文件...", f"已处理 {file_count}/{total_files} 个文件")

            # 添加备份信息到历史记录
            self.backup_history.append({
                "name": backup_name,
                "path": backup_path,
                "date": time.strftime('%Y-%m-%d %H:%M:%S')
            })

            # 如果有回调函数，更新最终进度
            if progress_callback:
                progress_callback(95, "完成备份", "正在验证备份文件...")
            
            # 获取文件大小
            file_size = os.path.getsize(backup_path)
            size_str = self._format_size(file_size)

            return True, f"备份成功：{backup_path}\n大小：{size_str}"
        except Exception as e:
            return False, f"备份失败: {str(e)}"
            
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

    def restore_backup(self, backup_path, restore_dir):
        try:
            if not os.path.exists(backup_path):
                return False, f"备份文件不存在：{backup_path}"

            if not os.path.exists(restore_dir):
                os.makedirs(restore_dir)
                
            # 从zip文件中还原
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            return True, "还原成功"
        except Exception as e:
            return False, f"还原失败：{str(e)}"

    def list_backups(self):
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    backups.append({
                        "name": file,
                        "size": os.path.getsize(file_path),
                        "date": time.ctime(os.path.getmtime(file_path))
                    })
            return backups
        except Exception as e:
            return f"Error listing backups: {str(e)}"

    def delete_backup(self, backup_name):
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                os.remove(backup_path)
                # Remove from history
                self.backup_history = [b for b in self.backup_history if b["name"] != backup_name]
                return True, f"备份 {backup_name} 已成功删除"
            else:
                return False, f"备份文件不存在: {backup_name}"
        except Exception as e:
            return False, f"删除备份时出错: {str(e)}"

    def rename_backup(self, old_name, new_name):
        """重命名备份文件
        
        Args:
            old_name: 原备份文件名
            new_name: 新备份文件名
            
        Returns:
            tuple: (成功标志, 消息)
        """
        try:
            # 检查文件名是否合法
            if not new_name.endswith('.zip'):
                new_name += '.zip'
                
            # 检查新文件名是否已存在
            new_path = os.path.join(self.backup_dir, new_name)
            if os.path.exists(new_path):
                return False, f"文件名 {new_name} 已存在"
                
            # 获取原文件路径
            old_path = os.path.join(self.backup_dir, old_name)
            if not os.path.exists(old_path):
                return False, f"原备份文件不存在: {old_name}"
                
            # 重命名文件
            os.rename(old_path, new_path)
            
            # 更新历史记录
            for backup in self.backup_history:
                if backup["name"] == old_name:
                    backup["name"] = new_name
                    backup["path"] = new_path
                    
            return True, f"备份已重命名为 {new_name}"
        except Exception as e:
            return False, f"重命名备份时出错: {str(e)}"

    def get_backup_history(self):
        return self.backup_history

    def get_latest_backup(self):
        if self.backup_history:
            return self.backup_history[-1]
        return None

    def get_backup_size(self, backup_name):
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                return os.path.getsize(backup_path)
            return 0
        except Exception as e:
            return 0

    def get_backup_date(self, backup_name):
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                return time.ctime(os.path.getmtime(backup_path))
            return ""
        except Exception as e:
            return ""

    def get_backups(self):
        """获取所有备份的信息"""
        try:
            backups = {}
            if not os.path.exists(self.backup_dir):
                return backups
                
            for file in os.listdir(self.backup_dir):
                if file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        # 格式化文件大小
                        if file_size < 1024:
                            size_str = f"{file_size}B"
                        elif file_size < 1024 * 1024:
                            size_str = f"{file_size / 1024:.2f}KB"
                        elif file_size < 1024 * 1024 * 1024:
                            size_str = f"{file_size / (1024 * 1024):.2f}MB"
                        else:
                            size_str = f"{file_size / (1024 * 1024 * 1024):.2f}GB"
                        
                        backups[file] = {
                            'name': file,
                            'path': file_path,
                            'size': size_str,
                            'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                        }
            return backups
        except Exception as e:
            print(f"获取备份列表出错: {str(e)}")
            return {}


# Example usage
if __name__ == "__main__":
    source = "path/to/source/directory"
    backup_dir = "path/to/backup/directory"

    backup_manager = BackupManager(source, backup_dir)

    # Create backup
    print(backup_manager.create_backup())

    # List backups
    print(backup_manager.list_backups())

    # Restore backup
    # print(backup_manager.restore_backup("backup_file.zip"))

    # Delete backup
    # print(blender_manager.delete_backup("backup_file.zip"))
    # print(backup_manager.delete_backup("backup_file.zip"))


