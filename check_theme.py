#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Theme Check Tool - 检查qt_material主题是否可用
# 此脚本用于测试qt_material库是否可以在PyQt6环境中正常工作

import sys
import os
import traceback

def main():
    """主函数"""
    print("开始检查qt_material主题兼容性...")
    print(f"Python版本: {sys.version}")
    
    # 检查PyQt6
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        print("PyQt6已安装且可用")
        pyqt_version = "6"
    except ImportError:
        print("PyQt6未安装或无法导入")
        try:
            from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
            from PyQt5.QtCore import Qt
            print("PyQt5已安装且可用")
            pyqt_version = "5"
        except ImportError:
            print("PyQt5也未安装，无法继续测试")
            return 1
    
    # 检查qt_material
    try:
        from qt_material import apply_stylesheet, list_themes
        print("qt_material库已安装且可用")
        
        # 打印可用主题列表
        themes = list_themes()
        print(f"可用主题: {len(themes)}个")
        for theme in themes:
            print(f"  - {theme}")
    except ImportError as e:
        print(f"qt_material库未安装或无法导入: {e}")
        print("请使用pip install qt-material安装")
        return 1
    except Exception as e:
        print(f"加载qt_material主题列表时出错: {e}")
        traceback.print_exc()
        return 1
    
    # 创建应用测试主题
    app = QApplication([])
    app.setApplicationName("主题测试工具")
    
    # 设置环境变量，尝试兼容PyQt6
    if pyqt_version == "6":
        print("设置环境变量以增强PyQt6兼容性...")
        os.environ['QT_API'] = 'pyqt6'
    
    # 创建主窗口
    window = QWidget()
    window.setWindowTitle("主题测试")
    window.setMinimumSize(500, 300)
    
    layout = QVBoxLayout(window)
    
    # 标题
    title = QLabel("qt_material主题测试")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 18pt; font-weight: bold;")
    layout.addWidget(title)
    
    # 添加说明
    info = QLabel("这是一个测试窗口，用于检查qt_material主题是否正确应用。\n"
                  "如果看到Material风格的界面，说明主题已成功应用。")
    info.setAlignment(Qt.AlignmentFlag.AlignCenter)
    info.setWordWrap(True)
    layout.addWidget(info)
    
    # 添加几个按钮来测试样式
    button1 = QPushButton("测试按钮 1")
    button2 = QPushButton("测试按钮 2")
    button3 = QPushButton("测试按钮 3")
    
    layout.addWidget(button1)
    layout.addWidget(button2)
    layout.addWidget(button3)
    
    # 应用dark_blue主题作为测试
    try:
        print("正在应用dark_blue主题...")
        apply_stylesheet(app, theme='dark_blue')
        print("主题应用完成")
    except Exception as e:
        print(f"应用主题时出错: {e}")
        traceback.print_exc()
        return 1
    
    # 显示窗口
    window.show()
    
    print("窗口已显示，请查看主题是否正确应用")
    print("如果主题应用成功，您应该能看到带有蓝色调的深色Material设计界面")
    print("测试完成后关闭窗口即可退出测试程序")
    
    # 运行应用
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 