import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QComboBox, 
                             QProgressBar, QWidget, QMessageBox, QFrame, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from usb_maker import USBMaker

class USBMakerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('USB 启动盘制作工具')
        self.setGeometry(300, 300, 600, 400)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6f9;
                font-family: 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                font-weight: 500;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                text-transform: uppercase;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #2980b9;
                transform: translateY(-2px);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                background-color: #21618c;
                transform: translateY(1px);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
                box-shadow: none;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #e0e4e8;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: #2c3e50;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 40px;
                border-left-width: 1px;
                border-left-color: #e0e4e8;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down-arrow.png);
                width: 20px;
                height: 20px;
            }
            QProgressBar {
                border: 2px solid #e0e4e8;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                height: 25px;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                width: 10px;
                margin: 0.5px;
                border-radius: 5px;
            }
            QFrame.line {
                color: #e0e4e8;
                height: 2px;
            }
            QToolTip {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon.fromTheme('drive-removable-media', QIcon(':/icons/usb-icon.png')))
        
        # 创建中心窗口和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)  # 增加边距
        main_layout.setSpacing(20)  # 增加组件间距
        central_widget.setLayout(main_layout)

        # 标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon.fromTheme('drive-removable-media', QIcon(':/icons/usb-icon.png')).pixmap(64, 64))
        title_label = QLabel('USB 启动盘制作工具')
        title_label.setFont(QFont('San Francisco', 22, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        
        title_layout.addStretch()
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # ISO文件选择
        iso_layout = QHBoxLayout()
        self.iso_label = QLabel('选择ISO文件:')
        self.iso_path = QLabel('未选择文件')
        self.iso_path.setStyleSheet("""
            color: #7f8c8d; 
            font-style: italic;
            background-color: #f1f3f5;
            padding: 8px 12px;
            border-radius: 6px;
        """)
        self.select_iso_btn = QPushButton('浏览')
        self.select_iso_btn.setIcon(QIcon.fromTheme('document-open'))
        self.select_iso_btn.clicked.connect(self.select_iso_file)
        self.select_iso_btn.setToolTip('选择要制作启动盘的ISO文件')
        
        iso_layout.addWidget(self.iso_label)
        iso_layout.addWidget(self.iso_path, stretch=3)
        iso_layout.addWidget(self.select_iso_btn)
        main_layout.addLayout(iso_layout)

        # U盘选择
        usb_layout = QHBoxLayout()
        self.usb_label = QLabel('选择U盘:')
        self.usb_combo = QComboBox()
        self.usb_combo.setPlaceholderText('请选择U盘')
        self.refresh_usb_btn = QPushButton('刷新')
        self.refresh_usb_btn.setIcon(QIcon.fromTheme('view-refresh'))
        self.refresh_usb_btn.clicked.connect(self.refresh_usb_drives)
        self.refresh_usb_btn.setToolTip('重新扫描可用U盘')
        
        usb_layout.addWidget(self.usb_label)
        usb_layout.addWidget(self.usb_combo, stretch=3)
        usb_layout.addWidget(self.refresh_usb_btn)
        main_layout.addLayout(usb_layout)

        # 进度条
        progress_layout = QVBoxLayout()
        progress_label = QLabel('写入进度:')
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%p%')
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e4e8;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                height: 25px;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                width: 10px;
                margin: 0.5px;
                border-radius: 5px;
            }
        """)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)

        # 制作按钮
        btn_layout = QHBoxLayout()
        self.make_btn = QPushButton('开始制作启动盘')
        self.make_btn.setIcon(QIcon.fromTheme('media-playback-start'))
        self.make_btn.clicked.connect(self.start_usb_maker)
        self.make_btn.setToolTip('开始将ISO文件写入选定的U盘')
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.make_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 关于按钮
        about_layout = QHBoxLayout()
        self.about_btn = QPushButton('关于')
        self.about_btn.clicked.connect(self.show_about_dialog)
        about_layout.addStretch()
        about_layout.addWidget(self.about_btn)
        about_layout.addStretch()
        main_layout.addLayout(about_layout)

        # 底部版权信息
        copyright_label = QLabel(' 2024 上海智潮磅礴科技有限公司 | USB启动盘制作工具 v1.0')
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 20px;
        """)
        main_layout.addWidget(copyright_label)

        # 初始化USB制作器
        self.usb_maker = USBMaker()
        self.usb_maker.progress_signal.connect(self.update_progress)
        self.usb_maker.status_signal.connect(self.show_status)
        self.usb_maker.error_signal.connect(self.show_error)

        # 初始化U盘列表
        self.refresh_usb_drives()

        # 控制按钮状态
        self.update_button_states()

    def select_iso_file(self):
        """选择ISO文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择ISO文件', '', 'ISO Files (*.iso)')
        if file_path:
            self.iso_path.setText(file_path)
            self.iso_path.setStyleSheet("color: #2ecc71; font-weight: bold;")

    def refresh_usb_drives(self):
        """刷新U盘列表"""
        self.usb_combo.clear()
        drives = self.usb_maker.get_usb_drives()
        if drives:
            self.usb_combo.addItems(drives)
            self.usb_combo.setStyleSheet("color: #2ecc71;")
        else:
            self.usb_combo.addItem('未找到U盘')
            self.usb_combo.setStyleSheet("color: #e74c3c;")

    def start_usb_maker(self):
        """开始制作启动盘"""
        iso_path = self.iso_path.text()
        usb_device = self.usb_combo.currentText()

        if iso_path == '未选择文件':
            QMessageBox.warning(self, '错误', '请先选择ISO文件')
            return

        if usb_device == '未找到U盘':
            QMessageBox.warning(self, '错误', '请选择有效的U盘')
            return

        # 弹出确认对话框
        reply = QMessageBox.question(self, '确认', 
                                     f'确定要将{iso_path}写入{usb_device}吗？\n这将清除U盘上的所有数据！', 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setValue(0)
            self.usb_maker.create_bootable_usb(iso_path, usb_device)

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def show_status(self, message):
        """显示状态消息"""
        QMessageBox.information(self, '提示', message)

    def show_error(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, '错误', message)

    def update_button_states(self):
        """控制按钮状态"""
        if self.iso_path.text() != '未选择文件' and self.usb_combo.currentText() != '未找到U盘':
            self.make_btn.setEnabled(True)
        else:
            self.make_btn.setEnabled(False)

    def show_about_dialog(self):
        """显示关于对话框"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle('关于')
        about_dialog.setStyleSheet("""
            QDialog {
                background-color: #f4f6f9;
                font-family: 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel('USB启动盘制作工具')
        title_label.setFont(QFont('San Francisco', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel('版本 1.0')
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 公司信息
        company_label = QLabel('上海智潮磅礴科技有限公司')
        company_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(company_label)
        
        # 联系方式
        contact_label = QLabel('联系邮箱：zhitrend@gmail.com')
        contact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(contact_label)
        
        # 描述
        desc_label = QLabel('专业的USB启动盘制作工具，简单、高效、安全')
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 确定按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(about_dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        about_dialog.setLayout(layout)
        about_dialog.exec_()

def main():
    app = QApplication(sys.argv)
    window = USBMakerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
