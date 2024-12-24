import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QComboBox, 
                             QProgressBar, QWidget, QMessageBox, QFrame, QDialog,
                             QLineEdit, QDialogButtonBox, QStyle, QProxyStyle)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import os
import subprocess
from usb_maker import USBMaker, t, set_language  # 导入翻译函数

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

class USBMakerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('app_name'))  # 使用翻译
        self.setGeometry(300, 300, 600, 400)
        
        # 当前语言状态
        self.current_language = 'en'  # 默认英语
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow { background-color: #f4f6f9; }
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border-radius: 5px; 
                padding: 8px 16px; 
            }
            QPushButton:hover { background-color: #2980b9; }
            
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 20px 5px 5px;  /* 右侧留出空间给箭头 */
                background-color: white;
                color: #2c3e50;
            }
            QComboBox::down-arrow {
                color: #2c3e50;
                width: 20px;
            }
            QComboBox::down-arrow:before {
                content: "▼";  /* Unicode 下拉箭头 */
                font-size: 12px;
                position: absolute;
                right: 8px;
                top: 50%;
                transform: translateY(-50%);
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
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

        # 顶部布局，包含语言切换按钮
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 标题布局
        title_layout = QHBoxLayout()
        
        # 标题图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(':/icons/usb-icon.png').pixmap(QSize(48, 48)))
        
        # 标题文字
        title_label = QLabel(t('app_name'))
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # 关于按钮和语言切换按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 关于按钮
        self.about_btn = QPushButton(t('about'))
        self.about_btn.clicked.connect(self.show_about_dialog)
        self.about_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 语言切换按钮（使用文字）
        self.language_btn = QPushButton('🌏')  # 直接使用表情符号
        self.language_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: transparent;
                border: none;
                padding: 5px;
                border-radius: 50%;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setToolTip(t('switch_language'))
        
        # 将关于按钮和地球按钮添加到布局
        button_layout.addWidget(self.about_btn)
        button_layout.addWidget(self.language_btn)
        
        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # ISO文件选择
        iso_layout = QHBoxLayout()
        self.iso_label = QLabel(t('select_iso_file'))  # 使用翻译
        self.iso_path = QLabel(t('no_file_selected'))  # 使用翻译
        self.iso_path.setStyleSheet("""
            color: #7f8c8d; 
            font-style: italic;
            background-color: #f1f3f5;
            padding: 8px 12px;
            border-radius: 6px;
        """)
        self.select_iso_btn = QPushButton(t('browse'))  # 使用翻译
        self.select_iso_btn.setIcon(QIcon.fromTheme('document-open'))
        self.select_iso_btn.clicked.connect(self.select_iso_file)
        self.select_iso_btn.setToolTip(t('select_iso_tooltip'))  # 使用翻译
        
        iso_layout.addWidget(self.iso_label)
        iso_layout.addWidget(self.iso_path, stretch=3)
        iso_layout.addWidget(self.select_iso_btn)
        main_layout.addLayout(iso_layout)

        # U盘选择
        usb_layout = QHBoxLayout()
        self.usb_label = QLabel(t('select_usb'))  # 使用翻译
        self.usb_combo = QComboBox()
        self.usb_combo.setStyle(CustomComboBoxStyle())
        self.usb_combo.setPlaceholderText(t('select_usb_placeholder'))  # 使用翻译
        self.usb_combo.currentIndexChanged.connect(self.update_button_states)  # 在U盘选择时触发按钮状态更新
        self.refresh_usb_btn = QPushButton(t('refresh'))  # 使用翻译
        self.refresh_usb_btn.setIcon(QIcon.fromTheme('view-refresh'))
        self.refresh_usb_btn.clicked.connect(self.refresh_usb_drives)
        self.refresh_usb_btn.setToolTip(t('refresh_usb_tooltip'))  # 使用翻译
        
        usb_layout.addWidget(self.usb_label)
        usb_layout.addWidget(self.usb_combo, stretch=3)
        usb_layout.addWidget(self.refresh_usb_btn)
        main_layout.addLayout(usb_layout)

        # 进度条
        progress_layout = QVBoxLayout()
        progress_label = QLabel(t('progress'))  # 使用翻译
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
        self.make_btn = QPushButton(t('start_process'))  # 使用翻译
        self.make_btn.setIcon(QIcon.fromTheme('media-playback-start'))
        self.make_btn.clicked.connect(self.start_usb_maker)
        self.make_btn.setToolTip(t('start_process_tooltip'))  # 使用翻译
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.make_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 底部版权信息
        copyright_label = QLabel(t('copyright_info'))  # 使用翻译
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

    def toggle_language(self):
        """切换语言"""
        # 在英文和中文之间切换
        new_language = 'zh' if self.current_language == 'en' else 'en'
        set_language(new_language)
        self.current_language = new_language
        
        # 重新设置所有文本
        self.setWindowTitle(t('app_name'))
        self.iso_label.setText(t('select_iso_file'))
        self.iso_path.setText(t('no_file_selected'))
        self.select_iso_btn.setText(t('browse'))
        self.select_iso_btn.setToolTip(t('select_iso_tooltip'))
        
        self.usb_label.setText(t('select_usb'))
        self.usb_combo.setPlaceholderText(t('select_usb_placeholder'))
        self.refresh_usb_btn.setText(t('refresh'))
        self.refresh_usb_btn.setToolTip(t('refresh_usb_tooltip'))
        
        self.make_btn.setText(t('start_process'))
        self.make_btn.setToolTip(t('start_process_tooltip'))
        
        self.about_btn.setText(t('about'))
        # self.language_btn.setToolTip(t('switch_language'))

    def select_iso_file(self):
        """选择ISO文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, t('select_iso_file'), '', 'ISO Files (*.iso)')
        if file_path:
            self.iso_path.setText(file_path)
            self.iso_path.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.update_button_states()

    def refresh_usb_drives(self):
        """刷新可用的USB驱动器"""
        drives = self.usb_maker.get_usb_drives()  # 使用 get_usb_drives 方法
        self.usb_combo.clear()
        
        if drives and drives[0] != t('no_usb_found'):
            self.usb_combo.addItems(drives)
            self.usb_combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #2ecc71;
                    border-radius: 4px;
                    padding: 5px 20px 5px 5px;  /* 右侧留出空间给箭头 */
                    background-color: white;
                    color: #2c3e50;
                }
                QComboBox::down-arrow {
                    color: #2c3e50;
                    width: 20px;
                }
                QComboBox::down-arrow:before {
                    content: "▼";  /* Unicode 下拉箭头 */
                    font-size: 12px;
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left-width: 1px;
                    border-left-color: #2ecc71;
                    border-left-style: solid;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    selection-background-color: #2ecc71;
                    selection-color: white;
                }
            """)
        else:
            self.usb_combo.addItem(t('no_usb_found'))
            self.usb_combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                    padding: 5px 20px 5px 5px;  /* 右侧留出空间给箭头 */
                    background-color: white;
                    color: #e74c3c;
                }
                QComboBox::down-arrow {
                    color: #e74c3c;
                    width: 20px;
                }
                QComboBox::down-arrow:before {
                    content: "▼";  /* Unicode 下拉箭头 */
                    font-size: 12px;
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left-width: 1px;
                    border-left-color: #e74c3c;
                    border-left-style: solid;
                    border-top-right-radius: 4px;
                    border-bottom-right-radius: 4px;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    selection-background-color: #e74c3c;
                    selection-color: white;
                }
            """)
        
        self.update_button_states()

    def start_usb_maker(self):
        """开始制作启动盘"""
        # 自定义密码对话框
        password_dialog = PasswordDialog(self)
        
        if password_dialog.exec_() == QDialog.Accepted:
            # 获取密码
            password = password_dialog.get_password()
            
            # 设置环境变量，强制设置
            os.environ['SUDO_PASSWORD'] = password
            
            # 获取选中的ISO文件和U盘
            iso_path = self.iso_path.text()
            usb_device = self.usb_combo.currentText()
            
            # 重置进度条
            self.progress_bar.setValue(0)
            
            # 开始制作启动盘
            self.usb_maker.create_bootable_usb(iso_path, usb_device)
        else:
            QMessageBox.warning(self, t('error'), t('no_admin_password'))  # 使用翻译

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def show_status(self, message):
        """显示状态消息"""
        QMessageBox.information(self, t('info'), message)

    def show_error(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, t('error'), message)

    def update_button_states(self):
        """控制按钮状态"""
        if (self.iso_path.text() != t('no_file_selected') and 
            self.usb_combo.currentText() != t('no_usb_found')):
            self.make_btn.setEnabled(True)
        else:
            self.make_btn.setEnabled(False)

    def show_about_dialog(self):
        """显示关于对话框"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle(t('about'))  # 使用翻译
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
        title_label = QLabel(t('app_name'))  # 使用翻译
        title_label.setFont(QFont('San Francisco', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel(t('version_info'))  # 使用翻译
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 公司信息
        company_label = QLabel(t('company_info'))  # 使用翻译
        company_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(company_label)
        
        # 联系方式
        contact_label = QLabel(t('contact_info'))  # 使用翻译
        contact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(contact_label)
        
        # 公司网站
        website_label = QLabel(t('website_info'))  # 使用翻译
        website_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(website_label)
        
        # 描述
        desc_label = QLabel(t('app_description'))  # 使用翻译
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 确定按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('ok'))  # 使用翻译
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
