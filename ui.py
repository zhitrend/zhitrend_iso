import os
import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar,
    QGroupBox, QFileDialog, QMessageBox, QDialog, QMenuBar,
    QMenu, QAction, QActionGroup, QListWidget, QListWidgetItem,
    QStatusBar, QFrame, QStyle, QProxyStyle, QFormLayout, QRadioButton, QCheckBox, 
    QDialogButtonBox, QSpinBox
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from usb_maker import USBMaker, t, set_language  # 导入翻译函数
import time
import json
import logging
import platform
import re
import hashlib
import zlib
import tempfile
import shutil

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('admin_privileges'))  # 使用翻译
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f4f8;
                border-radius: 10px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 图标和标题
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon.fromTheme('dialog-password', QIcon(':/icons/password-icon.png')).pixmap(48, 48))
        title_label = QLabel(t('need_admin_privileges'))  # 使用翻译
        title_label.setFont(QFont('San Francisco', 16, QFont.Bold))
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 说明文本
        desc_label = QLabel(t('enter_admin_password'))  # 使用翻译
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(t('enter_admin_password'))  # 使用翻译
        layout.addWidget(self.password_input)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton(t('cancel'))  # 使用翻译
        confirm_btn = QPushButton(t('confirm'))  # 使用翻译
        
        cancel_btn.clicked.connect(self.reject)
        confirm_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setFixedSize(400, 250)

    def get_password(self):
        return self.password_input.text()

class CustomComboBoxStyle(QProxyStyle):
    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QStyle.CC_ComboBox:
            # 使用系统默认的下拉箭头绘制
            self.proxy().drawComplexControl(control, option, painter, widget)
            return
        super().drawComplexControl(control, option, painter, widget)

class AdvancedOptionsDialog(QDialog):
    def __init__(self, parent=None, current_options=None):
        super().__init__(parent)
        self.setWindowTitle(t('advanced.write_method'))
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # 写入方式
        write_method_group = QGroupBox(t('advanced.write_method'))
        write_method_layout = QVBoxLayout()
        
        self.dd_radio = QRadioButton(t('advanced.dd'))
        self.iso9660_radio = QRadioButton(t('advanced.iso9660'))
        
        if current_options and current_options['write_method'] == 'iso9660':
            self.iso9660_radio.setChecked(True)
        else:
            self.dd_radio.setChecked(True)
        
        write_method_layout.addWidget(self.dd_radio)
        write_method_layout.addWidget(self.iso9660_radio)
        write_method_group.setLayout(write_method_layout)
        layout.addWidget(write_method_group)
        
        # 验证选项
        verify_group = QGroupBox("验证选项")
        verify_layout = QVBoxLayout()
        
        self.verify_after_write = QCheckBox(t('advanced.verify_after_write'))
        self.verify_after_write.setChecked(current_options.get('verify_after_write', True))
        verify_layout.addWidget(self.verify_after_write)
        
        self.skip_verify = QCheckBox(t('advanced.skip_verify'))
        self.skip_verify.setChecked(current_options.get('skip_verify', False))
        verify_layout.addWidget(self.skip_verify)
        
        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QVBoxLayout()
        
        # 缓冲区大小
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel(t('advanced.buffer_size')))
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(1, 32768)  # 1KB to 32MB
        self.buffer_size.setValue(current_options.get('buffer_size', 4096))
        self.buffer_size.setSuffix(" KB")
        buffer_layout.addWidget(self.buffer_size)
        advanced_layout.addLayout(buffer_layout)
        
        # 压缩选项
        self.compression = QCheckBox(t('advanced.compression'))
        self.compression.setChecked(current_options.get('compression', False))
        advanced_layout.addWidget(self.compression)
        
        # UEFI选项
        self.force_uefi = QCheckBox(t('advanced.force_uefi'))
        self.force_uefi.setChecked(current_options.get('force_uefi', False))
        advanced_layout.addWidget(self.force_uefi)
        
        # 保留数据选项
        self.preserve_data = QCheckBox(t('advanced.preserve_data'))
        self.preserve_data.setChecked(current_options.get('preserve_data', False))
        advanced_layout.addWidget(self.preserve_data)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_options(self):
        """获取设置的选项"""
        return {
            'write_method': 'iso9660' if self.iso9660_radio.isChecked() else 'dd',
            'verify_after_write': self.verify_after_write.isChecked(),
            'skip_verify': self.skip_verify.isChecked(),
            'buffer_size': self.buffer_size.value(),
            'compression': self.compression.isChecked(),
            'force_uefi': self.force_uefi.isChecked(),
            'preserve_data': self.preserve_data.isChecked()
        }

class BootConfigDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("启动配置编辑器")
        self.setFixedWidth(500)
        
        layout = QVBoxLayout()
        
        # 启动类型信息
        type_group = QGroupBox("启动类型")
        type_layout = QVBoxLayout()
        
        self.type_label = QLabel(f"当前类型: {config['type'].upper()}")
        type_layout.addWidget(self.type_label)
        
        if config['hybrid']:
            type_layout.addWidget(QLabel("支持UEFI和Legacy启动"))
        elif config['uefi']:
            type_layout.addWidget(QLabel("仅支持UEFI启动"))
        elif config['bootloader']:
            type_layout.addWidget(QLabel("仅支持Legacy启动"))
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # 启动项列表
        entries_group = QGroupBox("启动项")
        entries_layout = QVBoxLayout()
        
        self.entries_list = QListWidget()
        for entry in config['entries']:
            self.entries_list.addItem(entry)
        entries_layout.addWidget(self.entries_list)
        
        # 设置默认启动项
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("默认启动项:"))
        self.default_combo = QComboBox()
        self.default_combo.addItems(config['entries'])
        default_layout.addWidget(self.default_combo)
        entries_layout.addLayout(default_layout)
        
        entries_group.setLayout(entries_layout)
        layout.addWidget(entries_group)
        
        # 超时设置
        timeout_group = QGroupBox("启动设置")
        timeout_layout = QHBoxLayout()
        
        timeout_layout.addWidget(QLabel("启动等待时间:"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 60)
        self.timeout_spin.setValue(5)  # 默认5秒
        self.timeout_spin.setSuffix(" 秒")
        timeout_layout.addWidget(self.timeout_spin)
        
        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        """获取配置更新"""
        return {
            'default_entry': self.default_combo.currentText(),
            'grub_timeout': self.timeout_spin.value()
        }


class RepairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("启动修复工具")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 说明文字
        info_label = QLabel(
            "此工具可以帮助修复启动引导问题。\n"
            "支持修复以下问题：\n"
            "- UEFI启动文件丢失\n"
            "- GRUB配置损坏\n"
            "- Syslinux引导损坏\n"
            "\n修复过程不会影响U盘中的其他数据。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # 开始按钮
        self.repair_button = QPushButton("开始修复")
        layout.addWidget(self.repair_button)
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)


class PartitionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分区管理")
        self.setFixedWidth(600)
        
        layout = QVBoxLayout()
        
        # 分区表类型
        type_group = QGroupBox("分区表类型")
        type_layout = QHBoxLayout()
        
        self.gpt_radio = QRadioButton("GPT")
        self.mbr_radio = QRadioButton("MBR")
        self.gpt_radio.setChecked(True)
        
        type_layout.addWidget(self.gpt_radio)
        type_layout.addWidget(self.mbr_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # 分区列表
        partitions_group = QGroupBox("分区列表")
        partitions_layout = QVBoxLayout()
        
        self.partitions_list = QListWidget()
        partitions_layout.addWidget(self.partitions_list)
        
        # 分区操作按钮
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("添加分区")
        add_button.clicked.connect(self.add_partition)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("编辑分区")
        edit_button.clicked.connect(self.edit_partition)
        buttons_layout.addWidget(edit_button)
        
        remove_button = QPushButton("删除分区")
        remove_button.clicked.connect(self.remove_partition)
        buttons_layout.addWidget(remove_button)
        
        partitions_layout.addLayout(buttons_layout)
        partitions_group.setLayout(partitions_layout)
        layout.addWidget(partitions_group)
        
        # 进度条和状态
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # 确定取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.partitions = []
    
    def add_partition(self):
        """添加新分区"""
        dialog = PartitionEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            partition = dialog.get_partition()
            self.partitions.append(partition)
            self.update_partition_list()
    
    def edit_partition(self):
        """编辑选中的分区"""
        current = self.partitions_list.currentRow()
        if current >= 0:
            dialog = PartitionEditDialog(self, self.partitions[current])
            if dialog.exec_() == QDialog.Accepted:
                self.partitions[current] = dialog.get_partition()
                self.update_partition_list()
    
    def remove_partition(self):
        """删除选中的分区"""
        current = self.partitions_list.currentRow()
        if current >= 0:
            self.partitions.pop(current)
            self.update_partition_list()
    
    def update_partition_list(self):
        """更新分区列表显示"""
        self.partitions_list.clear()
        for part in self.partitions:
            self.partitions_list.addItem(
                f"{part['size']} - {part['format'].upper()} "
                f"({'EFI' if part['type'] == 'efi' else '数据'})"
            )
    
    def get_config(self):
        """获取分区配置"""
        return {
            'type': 'gpt' if self.gpt_radio.isChecked() else 'mbr',
            'partitions': self.partitions
        }


class PartitionEditDialog(QDialog):
    def __init__(self, parent=None, partition=None):
        super().__init__(parent)
        self.setWindowTitle("分区设置")
        self.setFixedWidth(400)
        
        layout = QFormLayout()
        
        # 分区大小
        self.size_edit = QLineEdit()
        self.size_edit.setPlaceholderText("例如：1G, 500M")
        if partition:
            self.size_edit.setText(partition['size'])
        layout.addRow("分区大小:", self.size_edit)
        
        # 分区类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(['数据分区', 'EFI分区'])
        if partition and partition['type'] == 'efi':
            self.type_combo.setCurrentText('EFI分区')
        layout.addRow("分区类型:", self.type_combo)
        
        # 文件系统
        self.format_combo = QComboBox()
        self.format_combo.addItems(['FAT32', 'NTFS', 'ExFAT', 'EXT4'])
        if partition:
            self.format_combo.setCurrentText(partition['format'].upper())
        layout.addRow("文件系统:", self.format_combo)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_partition(self):
        """获取分区设置"""
        return {
            'size': self.size_edit.text(),
            'type': 'efi' if self.type_combo.currentText() == 'EFI分区' else 'data',
            'format': self.format_combo.currentText().lower()
        }


class HybridISODialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("混合ISO设置")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # 选项
        options_group = QGroupBox("写入选项")
        options_layout = QVBoxLayout()
        
        self.verify = QCheckBox("写入后验证")
        self.verify.setChecked(True)
        options_layout.addWidget(self.verify)
        
        self.force_hybrid = QCheckBox("强制混合模式")
        options_layout.addWidget(self.force_hybrid)
        
        # 缓冲区大小
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel("缓冲区大小:"))
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(1, 64)
        self.buffer_size.setValue(1)
        self.buffer_size.setSuffix(" MB")
        buffer_layout.addWidget(self.buffer_size)
        options_layout.addLayout(buffer_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 转换选项
        convert_group = QGroupBox("ISO转换")
        convert_layout = QVBoxLayout()
        
        self.convert_button = QPushButton("转换为混合ISO")
        convert_layout.addWidget(self.convert_button)
        
        convert_group.setLayout(convert_layout)
        layout.addWidget(convert_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_options(self):
        """获取写入选项"""
        return {
            'verify': self.verify.isChecked(),
            'force_hybrid': self.force_hybrid.isChecked(),
            'buffer_size': self.buffer_size.value() * 1024 * 1024
        }


class ISOListDialog(QDialog):
    def __init__(self, parent=None, iso_files=None):
        super().__init__(parent)
        self.setWindowTitle("ISO文件列表")
        self.setFixedWidth(600)
        
        layout = QVBoxLayout()
        
        # ISO列表
        self.iso_list = QListWidget()
        if iso_files:
            for iso in iso_files:
                self.add_iso_item(iso)
        layout.addWidget(self.iso_list)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新列表")
        refresh_button.clicked.connect(self.refresh_list)
        layout.addWidget(refresh_button)
        
        # 确定取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.usb_maker = parent.usb_maker if parent else None
    
    def add_iso_item(self, iso_path):
        """添加ISO项目到列表"""
        if self.usb_maker:
            info = self.usb_maker.analyze_iso(iso_path)
            
            # 创建列表项
            item = QListWidgetItem()
            
            # 创建小部件显示详细信息
            widget = QWidget()
            layout = QVBoxLayout()
            
            # 文件名和路径
            name_label = QLabel(f"<b>{info['name']}</b>")
            path_label = QLabel(info['path'])
            path_label.setStyleSheet("color: gray;")
            
            # 文件大小
            size_str = self.format_size(info['size'])
            size_label = QLabel(f"大小: {size_str}")
            
            # 类型信息
            type_str = []
            if info['bootable']:
                type_str.append("可启动")
            if info['uefi']:
                type_str.append("UEFI")
            if info['hybrid']:
                type_str.append("混合")
            
            type_label = QLabel("类型: " + (", ".join(type_str) if type_str else "普通ISO"))
            
            # 添加所有标签
            layout.addWidget(name_label)
            layout.addWidget(path_label)
            layout.addWidget(size_label)
            layout.addWidget(type_label)
            
            widget.setLayout(layout)
            
            # 设置项目大小
            item.setSizeHint(widget.sizeHint())
            
            # 添加到列表
            self.iso_list.addItem(item)
            self.iso_list.setItemWidget(item, widget)
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def refresh_list(self):
        """刷新ISO列表"""
        if self.usb_maker:
            self.iso_list.clear()
            iso_files = self.usb_maker.scan_for_isos()
            for iso in iso_files:
                self.add_iso_item(iso)
    
    def get_selected_iso(self):
        """获取选中的ISO文件路径"""
        current = self.iso_list.currentItem()
        if current:
            widget = self.iso_list.itemWidget(current)
            # 路径在第二个标签中
            return widget.layout().itemAt(1).widget().text()
        return None


class LoadingDialog(QDialog):
    """加载对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请稍候")
        self.setFixedSize(200, 100)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        
        # 加载提示
        self.label = QLabel("正在扫描设备...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 设置为循环模式
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
    
    def set_message(self, message):
        """设置提示消息"""
        self.label.setText(message)


class ClickableLineEdit(QLineEdit):
    """可点击的输入框"""
    clicked = pyqtSignal()  # 自定义点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手型
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发送点击信号
        super().mousePressEvent(event)


class USBMakerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智潮磅礴科技有限公司 USB启动盘制作工具")
        self.setMinimumSize(800, 600)
        
        # 初始化USB制作器
        self.usb_maker = USBMaker()
        
        # 设置应用图标
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'icon.svg')))
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # 添加Logo
        logo_label = QLabel()
        logo_pixmap = QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'logo.svg')).pixmap(QSize(200, 60))
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)
        
        # 添加标题
        title_label = QLabel("专业USB启动盘制作工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建文件选择区域
        file_group = QGroupBox("选择ISO文件")
        file_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        file_layout = QHBoxLayout()
        
        self.iso_path = ClickableLineEdit()
        self.iso_path.setPlaceholderText("点击此处或使用浏览按钮选择ISO文件...")
        self.iso_path.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:hover {
                border-color: #bdc3c7;
                background: #f9f9f9;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background: white;
            }
        """)
        self.iso_path.textChanged.connect(self.update_button_states)
        self.iso_path.clicked.connect(self.select_iso)  # 连接点击信号
        
        self.select_iso_btn = QPushButton("浏览")
        self.select_iso_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:pressed {
                background: #2472a4;
            }
        """)
        self.select_iso_btn.clicked.connect(self.select_iso)
        
        file_layout.addWidget(self.iso_path)
        file_layout.addWidget(self.select_iso_btn)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 创建设备选择区域
        device_group = QGroupBox("选择目标设备")
        device_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        device_layout = QHBoxLayout()
        
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(resources/down-arrow.svg);
                width: 12px;
                height: 12px;
            }
        """)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:pressed {
                background: #219a52;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_usb_drives)
        
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_btn)
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)
        
        # 创建进度区域
        progress_group = QGroupBox("写入进度")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                margin-top: 5px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加速度和剩余时间标签
        self.speed_label = QLabel("速度: 0 MB/s")
        self.time_label = QLabel("预计剩余时间: --")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.speed_label)
        progress_layout.addWidget(self.time_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 创建操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_btn = QPushButton("开始写入")
        self.start_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 40px;
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:pressed {
                background: #a93226;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_writing)
        
        self.verify_btn = QPushButton("验证")
        self.verify_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 40px;
                background: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
            QPushButton:pressed {
                background: #7d3c98;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.verify_btn.clicked.connect(self.verify_iso)
        
        button_layout.addStretch()
        button_layout.addWidget(self.verify_btn)
        button_layout.addWidget(self.start_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 添加状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #e0e0e0;
                padding: 5px;
                font-size: 12px;
                color: #7f8c8d;
            }
        """)
        
        # 设置主布局
        main_widget.setLayout(main_layout)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 初始化USB设备列表
        self.refresh_usb_drives()
        
        # 更新按钮状态
        self.update_button_states()
        
        # 应用主题
        self.apply_theme()
        
        # 连接信号
        self.usb_maker.status_signal.connect(lambda msg: self.status_label.setText(msg))
        self.usb_maker.error_signal.connect(self.show_error)
        self.usb_maker.progress_signal.connect(self.progress_bar.setValue)
        self.usb_maker.speed_signal.connect(lambda speed: self.speed_label.setText(f"速度: {speed}"))
        self.usb_maker.remaining_time_signal.connect(lambda time: self.time_label.setText(f"预计剩余时间: {time}"))
    
    def show_error(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
    
    def refresh_usb_drives(self):
        """刷新USB设备列表"""
        loading = LoadingDialog(self)
        loading.set_message("正在扫描USB设备...")
        loading.show()
        QApplication.processEvents()
        
        try:
            drives = self.usb_maker.get_usb_drives()
            self.device_combo.clear()
            
            if drives:
                self.device_combo.addItems(drives)
            else:
                self.device_combo.addItem('未检测到USB设备')
        finally:
            loading.close()
        
        self.update_button_states()
    
    def select_iso(self):
        """选择ISO文件"""
        loading = LoadingDialog(self)
        loading.set_message("正在扫描ISO文件...")
        loading.show()
        QApplication.processEvents()
        
        try:
            # 先尝试显示已发现的ISO列表
            dialog = ISOListDialog(self)
            dialog.refresh_list()
            
            if dialog.exec_() == QDialog.Accepted:
                iso_path = dialog.get_selected_iso()
                if iso_path:
                    self.iso_path.setText(iso_path)
                    self.update_button_states()
                    return
            
            # 如果用户取消或没有选择，显示文件选择对话框
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "选择ISO文件",
                "",
                "ISO文件 (*.iso);;所有文件 (*.*)"
            )
            
            if file_name:
                self.iso_path.setText(file_name)
                self.update_button_states()
        finally:
            loading.close()
    
    def start_writing(self):
        """开始写入"""
        if not self.iso_path.text():
            QMessageBox.warning(self, '警告', '请先选择ISO文件！')
            return
        
        if not self.device_combo.currentText() or self.device_combo.currentText() == '未检测到USB设备':
            QMessageBox.warning(self, '警告', '请先选择USB设备！')
            return
        
        reply = QMessageBox.warning(
            self,
            '警告',
            f'即将向 {self.device_combo.currentText()} 写入ISO文件，此操作将清除设备上的所有数据！\n\n确定要继续吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setValue(0)
            self.status_label.setText('正在写入...')
            self.start_btn.setEnabled(False)
            self.verify_btn.setEnabled(False)
            
            # 在新线程中执行写入
            def write_thread():
                success = self.usb_maker.write_iso_to_usb(
                    self.iso_path.text(),
                    self.device_combo.currentText()
                )
                
                if success:
                    self.status_label.setText('写入完成！')
                else:
                    self.status_label.setText('写入失败！')
                
                self.start_btn.setEnabled(True)
                self.verify_btn.setEnabled(True)
            
            threading.Thread(target=write_thread, daemon=True).start()
    
    def verify_iso(self):
        """验证ISO文件"""
        if not self.iso_path.text():
            QMessageBox.warning(self, '警告', '请先选择ISO文件！')
            return
        
        self.progress_bar.setValue(0)
        self.status_label.setText('正在验证...')
        self.start_btn.setEnabled(False)
        self.verify_btn.setEnabled(False)
        
        # 在新线程中执行验证
        def verify_thread():
            success, info = self.usb_maker.verify_iso_integrity(self.iso_path.text())
            
            if success:
                QMessageBox.information(self, "验证结果", info)
            else:
                QMessageBox.warning(self, "验证失败", info)
            
            self.status_label.setText('验证完成！')
            self.start_btn.setEnabled(True)
            self.verify_btn.setEnabled(True)
        
        threading.Thread(target=verify_thread, daemon=True).start()
    
    def update_button_states(self):
        """更新按钮状态"""
        has_iso = bool(self.iso_path.text())
        has_device = bool(self.device_combo.currentText() and self.device_combo.currentText() != '未检测到USB设备')
        
        self.start_btn.setEnabled(has_iso and has_device)
        self.verify_btn.setEnabled(has_iso)
    
    def apply_theme(self):
        """应用主题"""
        # 这里可以根据需要实现深色/浅色主题切换
        pass
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            QMenuBar::item {
                padding: 8px 12px;
                color: #2c3e50;
            }
            QMenuBar::item:selected {
                background-color: #f5f6fa;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 20px;
                color: #2c3e50;
            }
            QMenu::item:selected {
                background-color: #f5f6fa;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e0e0;
                margin: 5px 0;
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 新建菜单项
        new_action = QAction('新建', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # 打开菜单项
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # 保存菜单项
        save_action = QAction('保存', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # 退出菜单项
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        # 首选项菜单项
        preferences_action = QAction('首选项', self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        # 主题子菜单
        theme_menu = view_menu.addMenu('主题')
        theme_group = QActionGroup(self)
        
        # 主题选项
        light_theme = QAction('浅色', self, checkable=True)
        dark_theme = QAction('深色', self, checkable=True)
        system_theme = QAction('跟随系统', self, checkable=True)
        
        theme_group.addAction(light_theme)
        theme_group.addAction(dark_theme)
        theme_group.addAction(system_theme)
        
        theme_menu.addAction(light_theme)
        theme_menu.addAction(dark_theme)
        theme_menu.addAction(system_theme)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        # 验证工具菜单项
        verify_action = QAction('验证工具', self)
        verify_action.triggered.connect(self.show_verify_tools)
        tools_menu.addAction(verify_action)
        
        # 分区工具菜单项
        partition_action = QAction('分区工具', self)
        partition_action.triggered.connect(self.show_partition_tools)
        tools_menu.addAction(partition_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 文档菜单项
        docs_action = QAction('文档', self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        # 关于菜单项
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def new_project(self):
        """创建新项目"""
        pass
    
    def open_project(self):
        """打开项目"""
        pass
    
    def save_project(self):
        """保存项目"""
        pass
    
    def show_preferences(self):
        """显示首选项对话框"""
        prefs_dialog = PreferencesDialog(self)
        prefs_dialog.exec_()
    
    def show_verify_tools(self):
        """显示验证工具"""
        verify_dialog = VerifyToolsDialog(self)
        verify_dialog.exec_()
    
    def show_partition_tools(self):
        """显示分区工具"""
        partition_dialog = PartitionToolsDialog(self)
        partition_dialog.exec_()
    
    def show_documentation(self):
        """显示文档"""
        docs_dialog = DocumentationDialog(self)
        docs_dialog.exec_()

    def show_about(self):
        """显示关于对话框"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle('关于')
        about_dialog.setFixedSize(400, 300)
        about_dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'logo.svg')).pixmap(QSize(200, 60))
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # 版本信息
        version_label = QLabel('版本 1.0.0')
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet('font-size: 14px;')
        layout.addWidget(version_label)
        
        # 版权信息
        copyright_label = QLabel(' 2024 智潮磅礴科技有限公司. 保留所有权利.')
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet('font-size: 12px; color: #7f8c8d;')
        layout.addWidget(copyright_label)
        
        # 描述
        desc_label = QLabel('智潮磅礴科技有限公司出品的USB启动盘制作工具是一款专业的系统启动盘制作软件，'
                          '支持多种系统镜像格式，提供简单易用的操作界面和强大的功能特性。')
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet('font-size: 12px; color: #7f8c8d; margin: 20px 0;')
        layout.addWidget(desc_label)
        
        # 确定按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        ok_button.setStyleSheet("""
            QPushButton {
                padding: 8px 30px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:pressed {
                background: #2472a4;
            }
        """)
        ok_button.clicked.connect(about_dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        about_dialog.setLayout(layout)
        about_dialog.exec_()


class PreferencesDialog(QDialog):
    """首选项对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("首选项")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 常规设置
        general_group = QGroupBox("常规")
        general_layout = QFormLayout()
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        general_layout.addRow("语言:", self.language_combo)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        general_layout.addRow("主题:", self.theme_combo)
        
        # 自动检查更新
        self.auto_update = QCheckBox("自动检查更新")
        general_layout.addRow(self.auto_update)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # 写入设置
        write_group = QGroupBox("写入")
        write_layout = QFormLayout()
        
        # 验证选项
        self.verify_after_write = QCheckBox("写入后验证")
        write_layout.addRow(self.verify_after_write)
        
        # 缓冲区大小
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(1, 64)
        self.buffer_size.setValue(4)
        self.buffer_size.setSuffix(" MB")
        write_layout.addRow("缓冲区大小:", self.buffer_size)
        
        write_group.setLayout(write_layout)
        layout.addWidget(write_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

class VerifyToolsDialog(QDialog):
    """验证工具对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("验证工具")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 验证选项
        options_group = QGroupBox("验证选项")
        options_layout = QVBoxLayout()
        
        self.verify_checksum = QRadioButton("校验和验证")
        self.verify_content = QRadioButton("完整性验证")
        self.verify_both = QRadioButton("全面验证")
        self.verify_both.setChecked(True)
        
        options_layout.addWidget(self.verify_checksum)
        options_layout.addWidget(self.verify_content)
        options_layout.addWidget(self.verify_both)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 进度显示
        progress_group = QGroupBox("验证进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("准备就绪")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始验证")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class PartitionToolsDialog(QDialog):
    """分区工具对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分区工具")
        self.setFixedSize(800, 500)
        
        layout = QVBoxLayout()
        
        # 设备选择
        device_group = QGroupBox("设备")
        device_layout = QHBoxLayout()
        
        self.device_combo = QComboBox()
        self.refresh_button = QPushButton("刷新")
        
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_button)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # 分区列表
        partitions_group = QGroupBox("分区")
        partitions_layout = QVBoxLayout()
        
        self.partitions_list = QListWidget()
        
        partitions_layout.addWidget(self.partitions_list)
        
        # 分区操作按钮
        partition_buttons = QHBoxLayout()
        
        self.add_button = QPushButton("添加")
        self.delete_button = QPushButton("删除")
        self.format_button = QPushButton("格式化")
        
        partition_buttons.addWidget(self.add_button)
        partition_buttons.addWidget(self.delete_button)
        partition_buttons.addWidget(self.format_button)
        
        partitions_layout.addLayout(partition_buttons)
        
        partitions_group.setLayout(partitions_layout)
        layout.addWidget(partitions_group)
        
        # 分区详情
        details_group = QGroupBox("分区详情")
        details_layout = QFormLayout()
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 1024)
        self.size_spin.setSuffix(" GB")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["NTFS", "FAT32", "exFAT", "ext4"])
        
        self.label_edit = QLineEdit()
        
        details_layout.addRow("大小:", self.size_spin)
        details_layout.addRow("类型:", self.type_combo)
        details_layout.addRow("卷标:", self.label_edit)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Close,
            Qt.Horizontal, self
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

class DocumentationDialog(QDialog):
    """文档对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文档")
        self.setFixedSize(800, 600)
        
        layout = QVBoxLayout()
        
        # 文档内容
        content = QLabel()
        content.setWordWrap(True)
        content.setText("""
# 智潮磅礴科技 USB启动盘制作工具使用说明

## 1. 基本使用
### 1.1 选择ISO文件
- 方式一：点击"浏览"按钮从文件浏览器中选择ISO文件
- 方式二：直接在输入框中输入或粘贴ISO文件的完整路径
- 方式三：从最近使用的ISO文件列表中选择

### 1.2 选择目标设备
1. 从下拉列表中选择要写入的USB设备
2. 如果设备未显示，点击"刷新"按钮重新扫描
3. 请注意设备的容量信息，确保足够存储ISO文件

### 1.3 开始写入
1. 确认ISO文件和目标设备无误后，点击"开始写入"
2. 在弹出的警告对话框中确认操作
3. 等待写入完成，期间请勿移除设备

### 1.4 验证
- 写入完成后建议进行验证，确保数据完整性
- 可以在写入前通过验证工具预先检查ISO文件

## 2. 高级功能
### 2.1 验证工具
- 校验和验证：快速验证文件是否被修改
- 完整性验证：详细检查文件内容
- 全面验证：同时进行上述两种验证

### 2.2 分区工具
- 分区管理：添加、删除、格式化分区
- 支持的文件系统：
  * NTFS：适用于Windows系统
  * FAT32：通用性好，单文件最大4GB
  * exFAT：突破FAT32限制，适合大文件
  * ext4：适用于Linux系统

### 2.3 其他功能
- 多语言支持：
  * 简体中文
  * English
- 主题切换：
  * 浅色主题
  * 深色主题
  * 跟随系统
- 性能优化：
  * 可调整缓冲区大小
  * 支持写入后自动验证

## 3. 注意事项
### 3.1 数据安全
1. 写入过程会清除USB设备上的所有数据
2. 开始写入前请务必备份重要文件
3. 写入过程中请勿：
   - 移除USB设备
   - 关闭程序
   - 休眠/关机

### 3.2 设备选择
1. 建议使用品牌USB设备
2. 设备容量应大于ISO文件大小
3. 尽量使用USB 3.0及以上接口
4. 避免使用老旧或损坏的设备

### 3.3 写入过程
1. 写入速度受多种因素影响：
   - USB设备读写速度
   - USB接口版本
   - ISO文件大小
   - 系统资源占用
2. 大文件写入可能需要较长时间
3. 进度条会实时显示：
   - 当前进度
   - 剩余时间
   - 写入速度

## 4. 常见问题
### 4.1 写入速度慢
可能原因：
- USB设备本身速度限制
- 使用了USB 2.0接口
- 系统资源不足
- 设备质量问题

解决方法：
1. 使用USB 3.0及以上接口
2. 关闭其他占用资源的程序
3. 更换性能更好的USB设备
4. 检查系统资源使用情况

### 4.2 写入失败
常见原因：
- USB设备连接不稳定
- ISO文件损坏
- 设备写保护
- 系统权限不足

解决方法：
1. 检查USB连接
2. 验证ISO文件完整性
3. 检查设备是否写保护
4. 以管理员身份运行
5. 尝试其他USB端口
6. 更换USB设备

### 4.3 无法识别设备
可能原因：
- 设备未正确连接
- 驱动程序问题
- 设备已损坏
- 系统不支持

解决方法：
1. 重新插拔设备
2. 点击刷新按钮
3. 检查设备管理器
4. 更新驱动程序
5. 尝试其他USB端口

## 5. 技术支持
如果您在使用过程中遇到问题，请通过以下方式获取帮助：

### 5.1 在线支持
- 官方网站：www.zhitrend.com
- 技术论坛：forum.zhitrend.com
- 在线文档：docs.zhitrend.com

### 5.2 联系我们
- 技术支持邮箱：support@zhitrend.com
- 客服热线：400-xxx-xxxx
- 工作时间拨打技术支持热线：周一至周五 9:00-18:00

### 5.3 更新升级
- 自动检查更新
- 访问官网下载最新版本
- 关注官方公众号获取更新通知

## 6. 关于我们
智潮磅礴科技有限公司专注于系统工具开发，致力于为用户提供专业、高效、可靠的软件解决方案。我们的产品以稳定性和易用性著称，得到了广大用户的信赖。

### 6.1 公司简介
- 成立时间：2024年
- 主营业务：系统工具开发
- 技术优势：专业团队、技术创新

### 6.2 联系方式
- 公司地址：xxx省xxx市xxx区
- 邮政编码：xxxxxx
- 商务合作：business@zhitrend.com

### 6.3 版权声明
Copyright 2024 智潮磅礴科技有限公司
保留所有权利。未经许可，不得复制、修改或传播本软件的任何部分。
""")
        
        # 添加滚动条
        scroll = QListWidget()
        scroll.addItem(QListWidgetItem(content.text()))
        layout.addWidget(scroll)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    usb_maker_app = USBMakerApp()
    usb_maker_app.show()
    sys.exit(app.exec_())
