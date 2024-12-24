import os
import sys
import threading
import re
import subprocess
import platform
import hashlib
import time
import json
import requests
import humanize
import darkdetect
import urllib3
import semver
from packaging import version
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QSettings
from PyQt5.QtWidgets import QMessageBox

# 国际化支持
import i18n
i18n.load_path.append('./locales')
i18n.set('fallback', 'en')
i18n.set('filename_format', '{locale}.{format}')

# 配置日志
import logging
logging.basicConfig(
    filename='/tmp/usb_maker.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class USBMaker(QObject):
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    speed_signal = pyqtSignal(str)
    remaining_time_signal = pyqtSignal(str)
    update_available_signal = pyqtSignal(str)
    iso_recommendations_signal = pyqtSignal(list)

    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.settings = QSettings('Zhitrend', 'USBMaker')
        
        # 初始化国际化
        self.init_internationalization()
        
        # 初始化主题
        self.init_theme()
        
        # 初始化网络功能
        self.init_network_features()

    def init_internationalization(self):
        """初始化国际化支持"""
        # 从系统设置读取语言
        current_lang = self.settings.value('language', 'en')
        i18n.set('locale', current_lang)

    def init_theme(self):
        """初始化主题"""
        # 自动检测系统主题
        theme = 'dark' if darkdetect.isDark() else 'light'
        self.settings.setValue('theme', theme)

    def init_network_features(self):
        """初始化网络相关功能"""
        # 检查更新间隔
        self.last_update_check = self.settings.value('last_update_check', 0, type=int)
        
        # 匿名使用统计
        self.usage_stats_enabled = self.settings.value('usage_stats', True, type=bool)
        
        # 启动后台线程进行更新检查和ISO推荐
        update_thread = threading.Thread(target=self.background_network_tasks)
        update_thread.daemon = True
        update_thread.start()

    def background_network_tasks(self):
        """后台网络任务"""
        try:
            # 检查更新
            self.check_for_updates()
            
            # 获取ISO推荐
            self.get_iso_recommendations()
            
            # 发送匿名使用统计
            if self.usage_stats_enabled:
                self.send_usage_stats()
        except Exception as e:
            self.logger.error(f"后台网络任务出错: {e}")

    def check_for_updates(self):
        """检查软件更新"""
        try:
            # 当前版本
            current_version = '1.0.0'
            
            # 检查更新的API
            response = requests.get('https://api.zhitrend.com/usb-maker/latest-version')
            latest_version = response.json()['version']
            
            # 比较版本
            if version.parse(latest_version) > version.parse(current_version):
                # 发送更新可用信号
                self.update_available_signal.emit(latest_version)
                
                # 记录更新检查时间
                self.settings.setValue('last_update_check', int(time.time()))
        except Exception as e:
            self.logger.warning(f"检查更新失败: {e}")

    def get_iso_recommendations(self):
        """获取ISO镜像推荐"""
        try:
            # 获取推荐的ISO镜像列表
            response = requests.get('https://api.zhitrend.com/usb-maker/iso-recommendations')
            iso_list = response.json()['isos']
            
            # 发送推荐信号
            self.iso_recommendations_signal.emit(iso_list)
        except Exception as e:
            self.logger.warning(f"获取ISO推荐失败: {e}")

    def send_usage_stats(self):
        """发送匿名使用统计"""
        try:
            # 收集基本系统信息
            stats = {
                'os': platform.system(),
                'os_version': platform.version(),
                'python_version': platform.python_version(),
                'app_version': '1.0.0'
            }
            
            # 发送统计数据
            requests.post('https://api.zhitrend.com/usb-maker/usage-stats', json=stats)
        except Exception as e:
            self.logger.warning(f"发送使用统计失败: {e}")

    def download_iso(self, iso_url, save_path):
        """下载ISO文件"""
        def download_thread():
            try:
                # 开始下载
                response = requests.get(iso_url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024  # 1 KB
                downloaded = 0

                with open(save_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        downloaded += len(data)
                        
                        # 计算进度
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            
                            def update_progress():
                                self.progress_signal.emit(progress)
                            
                            QTimer.singleShot(0, update_progress)

                # 下载完成
                def emit_success():
                    self.status_signal.emit("ISO下载成功")
                    self.progress_signal.emit(100)
                
                QTimer.singleShot(0, emit_success)

            except Exception as e:
                error_msg = f"ISO下载失败: {e}"
                self.logger.error(error_msg)
                
                def emit_error():
                    self.error_signal.emit(error_msg)
                
                QTimer.singleShot(0, emit_error)

        # 在新线程中执行下载
        thread = threading.Thread(target=download_thread)
        thread.start()

    def generate_download_link(self, iso_info):
        """根据ISO信息生成下载链接"""
        # 可以根据不同的ISO类型生成对应的下载链接
        base_url = "https://mirrors.example.com/"
        return f"{base_url}{iso_info['filename']}"

    def verify_download(self, file_path, expected_hash):
        """验证下载文件的完整性"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            return file_hash == expected_hash
        except Exception as e:
            self.logger.error(f"文件校验失败: {e}")
            return False

    def get_sudo_command(self):
        """获取跨平台的提权命令"""
        system = platform.system().lower()
        if system == 'darwin':  # macOS
            return ['sudo', '-S']
        elif system == 'linux':
            return ['sudo', '-S']
        elif system == 'windows':
            # Windows不直接支持sudo，可能需要特殊处理
            return []
        else:
            raise OSError(f"不支持的操作系统: {system}")

    def get_dd_command(self, iso_path, usb_device):
        """获取跨平台的dd命令"""
        system = platform.system().lower()
        if system in ['darwin', 'linux']:
            return [
                *self.get_sudo_command(),
                'dd', 
                f'if={iso_path}', 
                f'of={usb_device}', 
                'bs=1m', 
                'status=progress'
            ]
        elif system == 'windows':
            # Windows使用powershell的dd等效命令
            return [
                'powershell', 
                '-Command', 
                f'dd if="{iso_path}" of="{usb_device}" bs=1m'
            ]
        else:
            raise OSError(f"不支持的操作系统: {system}")

    def list_usb_drives(self):
        """列出可用的USB驱动器"""
        system = platform.system().lower()
        drives = []

        if system == 'windows':
            import win32api
            import win32file
            
            # 获取所有逻辑驱动器
            all_drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            
            for drive in all_drives:
                try:
                    # 检查驱动器类型
                    drive_type = win32file.GetDriveType(drive)
                    
                    # 可移动驱动器
                    if drive_type == win32file.DRIVE_REMOVABLE:
                        drives.append({
                            'path': drive,
                            'label': drive,
                            'size': self.get_drive_size(drive)
                        })
                except Exception as e:
                    self.logger.warning(f"检查驱动器 {drive} 时出错: {e}")
        
        elif system == 'darwin':
            import subprocess
            
            # macOS使用diskutil list
            try:
                output = subprocess.check_output(['diskutil', 'list'], universal_newlines=True)
                for line in output.split('\n'):
                    if '/dev/disk' in line and 'external' in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            device = parts[1]
                            drives.append({
                                'path': f'/dev/disk{device}',
                                'label': f'Disk {device}',
                                'size': self.get_drive_size(f'/dev/disk{device}')
                            })
            except Exception as e:
                self.logger.warning(f"列出USB驱动器时出错: {e}")
        
        elif system == 'linux':
            import pyudev
            
            context = pyudev.Context()
            for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
                if device.get('ID_BUS') == 'usb':
                    drives.append({
                        'path': device.device_node,
                        'label': device.get('ID_VENDOR', 'Unknown'),
                        'size': self.get_drive_size(device.device_node)
                    })
        
        return drives

    def get_drive_size(self, drive_path):
        """获取驱动器大小"""
        system = platform.system().lower()
        
        if system == 'windows':
            import win32api
            try:
                free_bytes = win32api.GetDiskFreeSpaceEx(drive_path)[1]
                total_bytes = win32api.GetDiskFreeSpaceEx(drive_path)[2]
                return total_bytes
            except Exception as e:
                self.logger.warning(f"获取Windows驱动器 {drive_path} 大小出错: {e}")
                return 0
        
        elif system == 'darwin':
            import subprocess
            try:
                output = subprocess.check_output(['diskutil', 'info', drive_path], universal_newlines=True)
                for line in output.split('\n'):
                    if 'Total Size:' in line:
                        # 解析大小，例如 "Total Size:           15.99 GB (15728640000 Bytes)"
                        size_match = re.search(r'\((\d+)\s*Bytes\)', line)
                        if size_match:
                            return int(size_match.group(1))
            except Exception as e:
                self.logger.warning(f"获取macOS驱动器 {drive_path} 大小出错: {e}")
                return 0
        
        elif system == 'linux':
            import os
            try:
                st = os.statvfs(drive_path)
                return st.f_blocks * st.f_frsize
            except Exception as e:
                self.logger.warning(f"获取Linux驱动器 {drive_path} 大小出错: {e}")
                return 0
        
        return 0

    def get_disk_size(self, disk_path):
        """尝试多种方法获取磁盘大小"""
        try:
            # 方法1：使用diskutil info
            detailed_info = subprocess.check_output(['diskutil', 'info', disk_path], universal_newlines=True)
            size_match = re.search(r'Total Size:\s*(.+)', detailed_info)
            if size_match:
                return size_match.group(1).strip()
            
            # 方法2：使用diskutil list
            list_output = subprocess.check_output(['diskutil', 'list', disk_path], universal_newlines=True)
            size_match = re.search(r'(\d+\.\d+\s*[BKMGT]B)', list_output)
            if size_match:
                return size_match.group(1)
            
            # 方法3：使用system_profiler
            try:
                profile_output = subprocess.check_output(['system_profiler', 'SPUSBDataType'], universal_newlines=True)
                size_match = re.search(rf'{disk_path}.*?Size:\s*(.+)', profile_output, re.DOTALL)
                if size_match:
                    return size_match.group(1).strip()
            except:
                pass
            
            # 方法4：使用df命令
            try:
                df_output = subprocess.check_output(['df', '-h'], universal_newlines=True)
                size_match = re.search(rf'{disk_path}s\d+\s+(\d+\.\d+\w+)', df_output)
                if size_match:
                    return size_match.group(1)
            except:
                pass
            
            return '未知大小'
        
        except Exception as e:
            self.logger.error(f"获取磁盘大小失败: {e}")
            return '未知大小'

    def get_usb_drives(self):
        """获取可用的U盘列表"""
        try:
            # 使用diskutil list获取所有磁盘信息
            result = subprocess.check_output(['diskutil', 'list'], universal_newlines=True)
            
            # 存储U盘信息的列表
            usb_drives = []
            
            # 逐行分析
            for line in result.split('\n'):
                # 查找外部物理磁盘
                if '/dev/disk' in line and 'external' in line.lower():
                    # 提取磁盘号
                    disk_match = re.search(r'/dev/disk(\d+)', line)
                    if disk_match:
                        disk_number = disk_match.group(1)
                        disk_path = f'/dev/disk{disk_number}'
                        
                        # 获取磁盘详细信息
                        try:
                            # 获取磁盘大小
                            disk_size = self.get_disk_size(disk_path)
                            
                            # 尝试获取卷名
                            volume_name = 'Unnamed'
                            try:
                                # 使用mount命令获取挂载的卷名
                                mount_output = subprocess.check_output(['mount'], universal_newlines=True)
                                volume_match = re.search(rf'{disk_path}s\d+\s+on\s+(.+)\s+\(', mount_output)
                                if volume_match:
                                    volume_name = os.path.basename(volume_match.group(1).strip())
                            except:
                                pass
                            
                            # 获取详细信息
                            detailed_info = subprocess.check_output(['diskutil', 'info', disk_path], universal_newlines=True)
                            
                            # 检查文件系统
                            fs_match = re.search(r'File System Personality:\s*(.+)', detailed_info)
                            fs_type = fs_match.group(1).strip() if fs_match else 'Unknown'
                            
                            # 如果文件系统是Unknown，尝试从分区信息获取
                            if fs_type == 'Unknown':
                                partitions_output = subprocess.check_output(['diskutil', 'list', disk_path], universal_newlines=True)
                                fs_matches = re.findall(r'\d+:\s+(\w+)\s+', partitions_output)
                                for match in fs_matches:
                                    if match.lower() in ['microsoft', 'fat', 'exfat', 'apfs', 'hfs']:
                                        fs_type = match
                                        break
                            
                            # 组合显示信息
                            display_name = f"{volume_name} ({disk_path}) - {disk_size} [{fs_type}]"
                            usb_drives.append((disk_path, display_name))
                        
                        except subprocess.CalledProcessError:
                            # 如果获取详细信息失败，使用磁盘路径
                            usb_drives.append((disk_path, f"{disk_path} - 未知大小 [未知文件系统]"))
            
            # 返回可用的U盘列表
            return [name for _, name in usb_drives] if usb_drives else ['未找到U盘']
        
        except Exception as e:
            error_msg = f"获取U盘列表失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_signal.emit(error_msg)
            return ['未找到U盘']

    def validate_iso(self, iso_path):
        """校验ISO文件完整性"""
        try:
            # 计算SHA256
            sha256_hash = hashlib.sha256()
            with open(iso_path, "rb") as f:
                # 分块读取以支持大文件
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            # 记录哈希值
            file_hash = sha256_hash.hexdigest()
            self.logger.info(f"ISO文件哈希值: {file_hash}")
            
            # 可选：与在线数据库对比
            return self.check_iso_hash_online(file_hash)
        except Exception as e:
            self.logger.error(f"ISO文件校验失败: {e}")
            return False

    def check_iso_hash_online(self, file_hash):
        """在线校验ISO文件哈希"""
        try:
            # 模拟在线哈希数据库查询
            response = requests.get(f'https://hash-db.example.com/check?hash={file_hash}')
            return response.json().get('valid', False)
        except Exception as e:
            self.logger.warning(f"在线哈希校验失败: {e}")
            return True  # 默认信任本地校验

    def check_disk_safety(self, disk_path):
        """检查磁盘安全性"""
        try:
            # 检查是否为可移动设备
            if not self.is_removable_device(disk_path):
                raise ValueError(f"警告：{disk_path} 不是可移动设备！")
            
            # 检查剩余空间
            total_space = self.get_drive_size(disk_path)
            free_space = self.get_free_space(disk_path)
            
            if free_space < total_space * 0.1:  # 低于10%空间
                self.logger.warning(f"磁盘 {disk_path} 剩余空间不足")
            
            return True
        except Exception as e:
            self.error_signal.emit(str(e))
            return False

    def is_removable_device(self, disk_path):
        """判断是否为可移动设备"""
        system = platform.system().lower()
        
        if system == 'windows':
            import win32file
            return win32file.GetDriveType(disk_path) == win32file.DRIVE_REMOVABLE
        
        elif system == 'darwin':
            try:
                output = subprocess.check_output(['diskutil', 'info', disk_path], universal_newlines=True)
                return 'Removable Media' in output
            except:
                return False
        
        elif system == 'linux':
            import pyudev
            context = pyudev.Context()
            device = pyudev.Device.from_device_file(context, disk_path)
            return device.get('ID_BUS') == 'usb'

    def get_free_space(self, disk_path):
        """获取磁盘剩余空间"""
        system = platform.system().lower()
        
        if system == 'windows':
            import win32api
            free_bytes = win32api.GetDiskFreeSpaceEx(disk_path)[0]
            return free_bytes
        
        elif system == 'darwin':
            import subprocess
            try:
                output = subprocess.check_output(['df', '-k', disk_path], universal_newlines=True)
                lines = output.strip().split('\n')
                free_kb = int(lines[1].split()[3])
                return free_kb * 1024
            except:
                return 0
        
        elif system == 'linux':
            import os
            st = os.statvfs(disk_path)
            return st.f_bavail * st.f_frsize

    def format_usb(self, disk_path, filesystem_type='FAT32'):
        """格式化U盘"""
        system = platform.system().lower()
        
        try:
            if system == 'windows':
                # Windows格式化
                subprocess.run(['format', disk_path, '/fs:' + filesystem_type, '/q'], check=True)
            
            elif system == 'darwin':
                # macOS格式化
                subprocess.run(['diskutil', 'eraseDisk', filesystem_type, 'USBDISK', disk_path], check=True)
            
            elif system == 'linux':
                # Linux格式化
                subprocess.run(['mkfs.' + filesystem_type.lower(), disk_path], check=True)
            
            self.status_signal.emit(f"成功格式化 {disk_path} 为 {filesystem_type}")
            return True
        
        except Exception as e:
            self.error_signal.emit(f"格式化失败: {e}")
            return False

    def create_bootable_usb(self, iso_path, usb_device_display):
        """制作启动盘的增强版本"""
        def run_dd():
            try:
                # 校验ISO文件
                if not self.validate_iso(iso_path):
                    raise ValueError("ISO文件校验失败")
                
                # 安全检查
                if not self.check_disk_safety(usb_device_display):
                    raise ValueError("磁盘安全检查未通过")
                
                # 格式化磁盘
                self.format_usb(usb_device_display)
                
                # 获取ISO文件大小
                iso_size = os.path.getsize(iso_path)
                
                # 记录开始时间
                start_time = time.time()
                last_copied = 0
                
                # 执行dd命令
                dd_command = self.get_dd_command(iso_path, usb_device_display)
                
                process = subprocess.Popen(
                    dd_command, 
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    universal_newlines=True
                )
                
                # 实时跟踪进度
                while True:
                    stderr_line = process.stderr.readline()
                    
                    if stderr_line:
                        # 解析进度
                        progress_match = re.search(r'(\d+)\s*bytes', stderr_line)
                        if progress_match:
                            current_copied = int(progress_match.group(1))
                            
                            # 计算进度百分比
                            progress = min(int((current_copied / iso_size) * 100), 100)
                            
                            # 计算传输速度
                            current_time = time.time()
                            time_diff = current_time - start_time
                            speed = (current_copied - last_copied) / time_diff if time_diff > 0 else 0
                            
                            # 估算剩余时间
                            remaining_bytes = iso_size - current_copied
                            remaining_time = remaining_bytes / speed if speed > 0 else 0
                            
                            # 发送信号
                            def update_progress():
                                self.progress_signal.emit(progress)
                                self.speed_signal.emit(humanize.naturalsize(speed) + '/s')
                                self.remaining_time_signal.emit(humanize.precisedelta(remaining_time))
                            
                            QTimer.singleShot(0, update_progress)
                            
                            last_copied = current_copied
                            start_time = current_time
                    
                    # 检查进程是否结束
                    if process.poll() is not None:
                        break
                
                # 检查命令执行结果
                if process.returncode == 0:
                    def emit_success():
                        self.status_signal.emit("启动盘制作成功！")
                        self.progress_signal.emit(100)
                    
                    QTimer.singleShot(0, emit_success)
                else:
                    # 获取错误输出
                    _, stderr = process.communicate()
                    error_msg = f"启动盘制作失败：{stderr}"
                    self.logger.error(error_msg)
                    
                    def emit_error():
                        self.error_signal.emit(error_msg)
                    
                    QTimer.singleShot(0, emit_error)
            
            except Exception as e:
                error_msg = f"制作启动盘出错: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                def emit_error():
                    self.error_signal.emit(error_msg)
                
                QTimer.singleShot(0, emit_error)
        
        # 在新线程中执行
        thread = threading.Thread(target=run_dd)
        thread.start()
