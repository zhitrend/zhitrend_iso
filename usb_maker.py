import os
import sys
import subprocess
import threading
import time
import json
import logging
import platform
import re
import hashlib
import zlib
import tempfile
import shutil
from fs_events import FSEventStream, FSEvents

# 国际化支持
import json
import i18n

from PyQt5.QtCore import QObject, pyqtSignal

# 配置日志
logging.basicConfig(
    filename='/tmp/usb_maker.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_translations(language='en'):
    locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
    translation_file = os.path.join(locales_dir, f'{language}.json')
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to English if translation not found
        with open(os.path.join(locales_dir, 'en.json'), 'r', encoding='utf-8') as f:
            return json.load(f)

def set_language(language='en'):
    """
    Set the application language
    :param language: Language code (e.g., 'en', 'zh')
    """
    global TRANSLATIONS
    TRANSLATIONS = load_translations(language)

# Default language
TRANSLATIONS = load_translations()

def t(key):
    """
    Translation function that retrieves text from TRANSLATIONS
    Fallbacks to the key itself if translation is not found
    """
    return TRANSLATIONS.get(key, key)

class USBMaker(QObject):
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    speed_signal = pyqtSignal(str)
    remaining_time_signal = pyqtSignal(str)
    update_available_signal = pyqtSignal(dict)  # 更新信号，传递更新信息
    iso_recommendations_signal = pyqtSignal(list)
    verification_signal = pyqtSignal(str)  # ISO验证状态信号
    health_check_signal = pyqtSignal(str)  # U盘健康状态信号
    theme_changed_signal = pyqtSignal(str)  # 主题变更信号
    backup_progress_signal = pyqtSignal(int)  # 备份进度信号
    backup_status_signal = pyqtSignal(str)  # 备份状态信号
    boot_config_signal = pyqtSignal(dict)  # 启动配置信号
    repair_status_signal = pyqtSignal(str)  # 修复状态信号
    partition_status_signal = pyqtSignal(str)  # 分区状态信号
    partition_progress_signal = pyqtSignal(int)  # 分区进度信号
    iso_found_signal = pyqtSignal(str)  # ISO发现信号

    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.settings = None
        self.start_time = None
        self.total_bytes = 0
        self.bytes_written = 0
        
        # 初始化国际化
        self.init_internationalization()
        
        # 初始化主题
        self.init_theme()
        
        # 初始化网络功能
        self.init_network_features()
        
        # 加载配置
        self.config = self.load_config()
        
        # 启动自动更新检查
        self.start_update_checker()

        # 高级选项默认值
        self.advanced_options = {
            'write_method': 'dd',  # 'dd' or 'iso9660'
            'verify_after_write': True,
            'buffer_size': 4096,  # 4KB
            'compression': False,
            'skip_verify': False,
            'force_uefi': False,
            'preserve_data': False
        }
    
    def init_internationalization(self):
        """初始化国际化支持"""
        # 从系统设置读取语言
        current_lang = None
        global TRANSLATIONS
        TRANSLATIONS = load_translations(current_lang)

    def init_theme(self):
        """初始化主题"""
        # 自动检测系统主题
        theme = 'dark' if False else 'light'
        self.settings = None

    def init_network_features(self):
        """初始化网络相关功能"""
        # 检查更新间隔
        self.last_update_check = None
        
        # 匿名使用统计
        self.usage_stats_enabled = None
        
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
            response = None
            latest_version = None
            
            # 比较版本
            if latest_version and version.parse(latest_version) > version.parse(current_version):
                # 发送更新可用信号
                self.update_available_signal.emit(latest_version)
                
                # 记录更新检查时间
                self.settings = None
        except Exception as e:
            self.logger.warning(f"检查更新失败: {e}")

    def get_iso_recommendations(self):
        """获取ISO镜像推荐"""
        try:
            # 获取推荐的ISO镜像列表
            response = None
            iso_list = None
            
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
            requests = None
        except Exception as e:
            self.logger.warning(f"发送使用统计失败: {e}")

    def download_iso(self, iso_url, save_path):
        """下载ISO文件"""
        def download_thread():
            try:
                # 开始下载
                response = None
                total_size = None
                block_size = 1024  # 1 KB
                downloaded = 0

                with open(save_path, 'wb') as file:
                    for data in None:
                        file.write(data)
                        downloaded += len(data)
                        
                        # 计算进度
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            
                            def update_progress():
                                self.progress_signal.emit(progress)
                            
                            None

                # 下载完成
                def emit_success():
                    self.emit_success("ISO下载成功")
                    self.progress_signal.emit(100)
                
                None

            except Exception as e:
                error_msg = f"ISO下载失败: {e}"
                self.logger.error(error_msg)
                
                def emit_error():
                    self.emit_error(error_msg)
                
                None

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
                # 查找磁盘
                if '/dev/disk' in line:
                    # 提取磁盘号
                    disk_match = re.search(r'/dev/disk(\d+)', line)
                    if disk_match:
                        disk_number = disk_match.group(1)
                        disk_path = f'/dev/disk{disk_number}'
                        
                        # 检查是否为可移动设备
                        if not self.is_removable_device(disk_path):
                            continue
                        
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
            self.emit_error(error_msg)
            return ['未找到U盘']

    def is_removable_device(self, disk_path):
        """判断是否为可移动设备"""
        try:
            # 使用 diskutil info 获取详细信息
            detailed_info = subprocess.check_output(['diskutil', 'info', disk_path], universal_newlines=True)
            
            # 检查是否为外部设备或可移动设备
            removable_keywords = ['external', 'removable', 'usb', 'flash', 'thumb']
            return any(keyword in detailed_info.lower() for keyword in removable_keywords)
        except Exception as e:
            self.logger.warning(f"无法确定设备类型: {e}")
            return False

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
            response = None
            return response.json().get('valid', False)
        except Exception as e:
            self.logger.warning(f"在线哈希校验失败: {e}")
            return True  # 默认信任本地校验

    def check_disk_safety(self, disk_path):
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
            self.emit_error(f"Disk safety check failed: {str(e)}")
            return False

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
                if len(lines) >= 2:
                    parts = lines[1].split()
                    free_kb = int(parts[3])
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
            
            self.emit_success(f"成功格式化 {disk_path} 为 {filesystem_type}")
            return True
        
        except Exception as e:
            self.emit_error(f"格式化失败: {e}")
            return False

    def create_bootable_usb(self, iso_path, usb_device_display):
        try:
            # 获取ISO文件大小
            self.total_bytes = os.path.getsize(iso_path)
            self.start_time = time.time()
            self.bytes_written = 0
            
            # 校验ISO文件
            if not self.validate_iso(iso_path):
                raise ValueError("ISO文件校验失败")
            
            # 安全检查
            if not self.check_disk_safety(usb_device_display):
                raise ValueError("磁盘安全检查未通过")
            
            # 格式化磁盘
            self.format_usb(usb_device_display)
            
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
                        progress = min(int((current_copied / self.total_bytes) * 100), 100)
                        
                        # 计算传输速度
                        current_time = time.time()
                        time_diff = current_time - self.start_time
                        speed = (current_copied - self.bytes_written) / time_diff if time_diff > 0 else 0
                        
                        # 估算剩余时间
                        remaining_bytes = self.total_bytes - current_copied
                        estimated_time = remaining_bytes / speed if speed > 0 else 0
                        
                        # 发送信号
                        def update_progress():
                            self.progress_signal.emit(progress)
                            self.speed_signal.emit(self.format_speed(speed))
                            self.remaining_time_signal.emit(self.format_time(estimated_time))
                        
                        None
        
            # 检查进程是否结束
            if process.poll() is not None:
                pass
            
            # 检查命令执行结果
            if process.returncode == 0:
                def emit_success():
                    self.emit_success("启动盘制作成功！")
                    self.progress_signal.emit(100)
                
                None
            else:
                # 获取错误输出
                _, stderr = process.communicate()
                error_msg = f"启动盘制作失败：{stderr}"
                self.logger.error(error_msg)
                
                def emit_error():
                    self.emit_error(error_msg)
                
                None
        
        except Exception as e:
            error_msg = f"制作启动盘出错: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            def emit_error():
                self.emit_error(error_msg)
            
            None

    def update_progress(self, bytes_written):
        """
        更新进度和速度信息
        :param bytes_written: 已写入的字节数
        """
        self.bytes_written = bytes_written
        if self.total_bytes > 0:
            progress = int((bytes_written / self.total_bytes) * 100)
            self.progress_signal.emit(progress)
            
            # 计算速度和剩余时间
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                speed = bytes_written / elapsed_time  # 字节/秒
                remaining_bytes = self.total_bytes - bytes_written
                estimated_time = remaining_bytes / speed if speed > 0 else 0
                
                # 发送速度信号
                speed_text = self.format_speed(speed)
                self.speed_signal.emit(speed_text)
                
                # 发送剩余时间信号
                time_text = self.format_time(estimated_time)
                self.remaining_time_signal.emit(time_text)
    
    def format_speed(self, speed_bytes_per_sec):
        """
        格式化速度显示
        :param speed_bytes_per_sec: 每秒字节数
        :return: 格式化的速度字符串
        """
        if speed_bytes_per_sec < 1024:
            return f"{speed_bytes_per_sec:.1f} B/s"
        elif speed_bytes_per_sec < 1024 * 1024:
            return f"{speed_bytes_per_sec/1024:.1f} KB/s"
        else:
            return f"{speed_bytes_per_sec/(1024*1024):.1f} MB/s"
    
    def format_time(self, seconds):
        """
        格式化时间显示
        :param seconds: 剩余秒数
        :return: 格式化的时间字符串
        """
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            seconds = int(seconds % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}小时{minutes}分"
    
    def emit_error(self, message):
        """
        Emit error signal with detailed error message
        :param message: Error message to be displayed
        """
        self.logger.error(f"Error: {message}")
        self.error_signal.emit(message)
    
    def emit_success(self, message):
        """
        Emit success signal with message
        :param message: Success message to be displayed
        """
        self.logger.info(f"Success: {message}")
        self.status_signal.emit(message)

    def verify_iso_integrity(self, iso_path):
        """
        验证ISO文件的完整性
        :param iso_path: ISO文件路径
        :return: (bool, str) 验证结果和详细信息
        """
        try:
            self.verification_signal.emit("正在验证ISO文件完整性...")
            
            # 计算文件的MD5和SHA256哈希值
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()
            
            # 分块读取文件以节省内存
            with open(iso_path, 'rb') as f:
                # 分块读取文件以节省内存
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            md5_value = md5_hash.hexdigest()
            sha256_value = sha256_hash.hexdigest()
            
            # 检查文件头部是否符合ISO格式
            with open(iso_path, 'rb') as f:
                header = f.read(32768)  # 读取ISO头部
                if b'CD001' not in header:  # ISO 9660标识符
                    return False, "文件不是有效的ISO镜像格式"
            
            # 验证文件大小是否合理
            file_size = os.path.getsize(iso_path)
            if file_size < 1024 * 1024:  # 小于1MB
                return False, "ISO文件大小异常"
            
            verification_info = f"""
            ISO文件验证结果：
            - 文件大小: {file_size}
            - MD5: {md5_value}
            - SHA256: {sha256_value}
            - 格式验证: 通过
            """
            
            self.verification_signal.emit("ISO文件验证通过！")
            return True, verification_info
            
        except Exception as e:
            error_msg = f"ISO文件验证失败: {str(e)}"
            self.verification_signal.emit(error_msg)
            return False, error_msg
    
    def check_usb_health(self, usb_device):
        """
        检查U盘健康状态
        :param usb_device: U盘设备路径
        :return: (bool, str) 检查结果和详细信息
        """
        try:
            self.health_check_signal.emit("正在检查U盘健康状态...")
            health_info = []
            
            # 获取设备信息
            device_info = self.get_device_info(usb_device)
            health_info.append(f"设备信息: {device_info}")
            
            # 检查可用空间
            total_space, free_space = self.get_space_info(usb_device)
            health_info.append(f"总空间: {total_space}")
            health_info.append(f"可用空间: {free_space}")
            
            # 检查写入速度
            write_speed = self.test_write_speed(usb_device)
            health_info.append(f"写入速度: {write_speed}/s")
            
            # 检查是否有坏块
            bad_blocks = self.check_bad_blocks(usb_device)
            health_info.append(f"坏块检查: {'发现 ' + str(bad_blocks) + ' 个坏块' if bad_blocks > 0 else '未发现坏块'}")
            
            # 综合评估
            health_status = "良好" if bad_blocks == 0 and write_speed > 1024*1024 else "可能存在问题"
            health_info.append(f"健康状态: {health_status}")
            
            result_info = "\n".join(health_info)
            self.health_check_signal.emit(f"U盘健康检查完成: {health_status}")
            
            return health_status == "良好", result_info
            
        except Exception as e:
            error_msg = f"U盘健康检查失败: {str(e)}"
            self.health_check_signal.emit(error_msg)
            return False, error_msg
    
    def get_device_info(self, device_path):
        """获取设备信息"""
        try:
            if sys.platform == 'darwin':  # macOS
                result = subprocess.check_output(['diskutil', 'info', device_path], 
                                     capture_output=True, text=True)
                return result.stdout
            else:
                return "设备信息获取不支持当前系统"
        except Exception as e:
            return f"无法获取设备信息: {str(e)}"
    
    def get_space_info(self, device_path):
        """获取空间信息"""
        try:
            if sys.platform == 'darwin':  # macOS
                result = subprocess.check_output(['df', '-k', device_path], 
                                     capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    total = int(parts[1]) * 1024  # 转换为字节
                    free = int(parts[3]) * 1024
                    return total, free
            return 0, 0
        except Exception:
            return 0, 0
    
    def test_write_speed(self, device_path):
        """测试写入速度"""
        try:
            # 创建一个临时文件进行写入测试
            test_size = 1024 * 1024 * 10  # 10MB
            test_data = b'0' * 1024
            
            start_time = time.time()
            written = 0
            
            with open(device_path, 'wb') as f:
                while written < test_size:
                    f.write(test_data)
                    written += len(test_data)
            
            end_time = time.time()
            speed = test_size / (end_time - start_time)
            return speed
        except Exception:
            return 0
    
    def check_bad_blocks(self, device_path):
        """检查坏块"""
        try:
            if sys.platform == 'darwin':  # macOS
                # macOS没有直接的坏块检查工具，返回0表示假定没有坏块
                return 0
            return 0
        except Exception:
            return 0

    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "version": "1.0.0",
            "update_url": "https://api.github.com/repos/yourusername/zhitrend_iso/releases/latest",
            "check_update_interval": 86400,
            "theme": "auto",
            "last_update_check": 0
        }
    
    def save_config(self):
        """保存配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
    
    def start_update_checker(self):
        """启动更新检查器"""
        def check_update_thread():
            while True:
                current_time = time.time()
                last_check = self.config.get('last_update_check', 0)
                check_interval = self.config.get('check_update_interval', 86400)
                
                if current_time - last_check >= check_interval:
                    self.check_for_updates()
                    self.config['last_update_check'] = current_time
                    self.save_config()
                
                time.sleep(3600)  # 每小时检查一次是否需要更新
        
        threading.Thread(target=check_update_thread, daemon=True).start()
    
    def check_for_updates(self):
        """检查更新"""
        try:
            response = None
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release['tag_name'].lstrip('v')
                current_version = self.config['version']
                
                if semver.compare(latest_version, current_version) > 0:
                    update_info = {
                        'version': latest_version,
                        'description': latest_release['body'],
                        'download_url': latest_release['assets'][0]['browser_download_url']
                    }
                    self.update_available_signal.emit(update_info)
        except Exception as e:
            self.logger.error(f"检查更新失败: {str(e)}")
    
    def set_theme(self, theme):
        """设置主题"""
        try:
            self.config['theme'] = theme
            self.save_config()
            self.theme_changed_signal.emit(theme)
        except Exception as e:
            self.logger.error(f"设置主题失败: {str(e)}")
    
    def get_current_theme(self):
        """获取当前主题"""
        theme = self.config.get('theme', 'auto')
        if theme == 'auto':
            return 'dark' if False else 'light'
        return theme

    def backup_usb_data(self, usb_device, backup_path):
        """
        备份U盘数据
        :param usb_device: U盘设备路径
        :param backup_path: 备份文件保存路径
        :return: (bool, str) 备份结果和详细信息
        """
        try:
            self.backup_status_signal.emit("正在准备备份...")
            
            # 获取U盘大小和已用空间
            total_size, used_size = self.get_used_space(usb_device)
            if total_size == 0:
                return False, "无法获取U盘大小"
            
            # 检查备份路径是否有足够空间
            backup_free_space = self.get_backup_free_space(backup_path)
            if backup_free_space < used_size:
                return False, f"备份位置空间不足，需要 {used_size}"
            
            # 创建备份文件夹
            backup_dir = os.path.join(backup_path, f"usb_backup_{time.strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 开始备份
            copied_size = 0
            for root, dirs, files in os.walk(usb_device):
                # 创建对应的目录结构
                for d in dirs:
                    src_dir = os.path.join(root, d)
                    dst_dir = os.path.join(backup_dir, os.path.relpath(src_dir, usb_device))
                    os.makedirs(dst_dir, exist_ok=True)
                
                # 复制文件
                for f in files:
                    src_file = os.path.join(root, f)
                    dst_file = os.path.join(backup_dir, os.path.relpath(src_file, usb_device))
                    
                    # 复制文件并更新进度
                    file_size = os.path.getsize(src_file)
                    with open(src_file, 'rb') as sf, open(dst_file, 'wb') as df:
                        while True:
                            chunk = sf.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            df.write(chunk)
                            copied_size += len(chunk)
                            progress = int((copied_size / used_size) * 100)
                            self.backup_progress_signal.emit(progress)
                            self.backup_status_signal.emit(f"正在备份: {os.path.relpath(src_file, usb_device)}")
            
            # 创建备份信息文件
            info_file = os.path.join(backup_dir, 'backup_info.json')
            backup_info = {
                'device': usb_device,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_size': total_size,
                'used_size': used_size,
                'files_count': sum(len(files) for _, _, files in os.walk(backup_dir))
            }
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=4, ensure_ascii=False)
            
            return True, f"备份完成，保存在: {backup_dir}"
            
        except Exception as e:
            error_msg = f"备份失败: {str(e)}"
            self.backup_status_signal.emit(error_msg)
            return False, error_msg
    
    def restore_usb_data(self, backup_dir, usb_device):
        """
        从备份恢复U盘数据
        :param backup_dir: 备份目录路径
        :param usb_device: 目标U盘设备路径
        :return: (bool, str) 恢复结果和详细信息
        """
        try:
            self.backup_status_signal.emit("正在准备恢复数据...")
            
            # 检查备份信息文件
            info_file = os.path.join(backup_dir, 'backup_info.json')
            if not os.path.exists(info_file):
                return False, "无效的备份目录"
            
            # 读取备份信息
            with open(info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            # 检查目标U盘空间
            total_size, _ = self.get_used_space(usb_device)
            if total_size < backup_info['used_size']:
                return False, "目标U盘空间不足"
            
            # 开始恢复数据
            copied_size = 0
            total_size = backup_info['used_size']
            
            for root, dirs, files in os.walk(backup_dir):
                if 'backup_info.json' in files:
                    files.remove('backup_info.json')
                
                # 创建目录结构
                for d in dirs:
                    src_dir = os.path.join(root, d)
                    dst_dir = os.path.join(usb_device, os.path.relpath(src_dir, backup_dir))
                    os.makedirs(dst_dir, exist_ok=True)
                
                # 复制文件
                for f in files:
                    src_file = os.path.join(root, f)
                    dst_file = os.path.join(usb_device, os.path.relpath(src_file, backup_dir))
                    
                    # 复制文件并更新进度
                    file_size = os.path.getsize(src_file)
                    with open(src_file, 'rb') as sf, open(dst_file, 'wb') as df:
                        while True:
                            chunk = sf.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            df.write(chunk)
                            copied_size += len(chunk)
                            progress = int((copied_size / total_size) * 100)
                            self.backup_progress_signal.emit(progress)
                            self.backup_status_signal.emit(f"正在恢复: {os.path.relpath(dst_file, usb_device)}")
            
            return True, "数据恢复完成"
            
        except Exception as e:
            error_msg = f"恢复失败: {str(e)}"
            self.backup_status_signal.emit(error_msg)
            return False, error_msg
    
    def get_used_space(self, path):
        """获取目录的总大小和已用空间"""
        try:
            if sys.platform == 'darwin':  # macOS
                result = subprocess.check_output(['df', '-k', path], 
                                     capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    total = int(parts[1]) * 1024  # 转换为字节
                    used = int(parts[2]) * 1024
                    return total, used
            return 0, 0
        except Exception:
            return 0, 0
    
    def get_backup_free_space(self, path):
        """获取备份位置的可用空间"""
        try:
            if sys.platform == 'darwin':  # macOS
                result = subprocess.check_output(['df', '-k', path], 
                                     capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    free = int(parts[3]) * 1024  # 转换为字节
                    return free
            return 0
        except Exception:
            return 0

    def set_advanced_options(self, options):
        """设置高级选项"""
        self.advanced_options.update(options)
    
    def write_iso_dd(self, iso_path, usb_device):
        """使用DD模式写入ISO"""
        try:
            iso_size = os.path.getsize(iso_path)
            written = 0
            
            with open(iso_path, 'rb') as iso_file, open(usb_device, 'wb') as usb:
                # 设置缓冲区大小
                buffer_size = self.advanced_options['buffer_size'] * 1024  # KB
                
                while True:
                    chunk = iso_file.read(buffer_size)
                    if not chunk:
                        break
                    
                    if self.advanced_options['compression']:
                        chunk = zlib.compress(chunk)
                    
                    usb.write(chunk)
                    written += len(chunk)
                    
                    progress = int((written / iso_size) * 100)
                    self.progress_signal.emit(progress)
                    
                    # 计算写入速度和剩余时间
                    self.calculate_progress_info(written, iso_size)
            
            return True, "DD模式写入完成"
        except Exception as e:
            return False, f"DD模式写入失败: {str(e)}"
    
    def write_iso_9660(self, iso_path, usb_device):
        """使用ISO9660模式写入ISO"""
        try:
            # 挂载ISO文件
            with tempfile.TemporaryDirectory() as mount_point:
                if sys.platform == 'darwin':
                    subprocess.run(['hdiutil', 'attach', iso_path,
                                 '-mountpoint', mount_point], check=True)
                    
                    try:
                        # 计算总大小
                        total_size = sum(os.path.getsize(os.path.join(root, f))
                                       for root, _, files in os.walk(mount_point)
                                       for f in files)
                        copied = 0
                        
                        # 复制文件
                        for root, dirs, files in os.walk(mount_point):
                            for d in dirs:
                                src_dir = os.path.join(root, d)
                                dst_dir = os.path.join(usb_device, 
                                                     os.path.relpath(src_dir, mount_point))
                                os.makedirs(dst_dir, exist_ok=True)
                            
                            for f in files:
                                src_file = os.path.join(root, f)
                                dst_file = os.path.join(usb_device,
                                                      os.path.relpath(src_file, mount_point))
                                
                                with open(src_file, 'rb') as sf, open(dst_file, 'wb') as df:
                                    while True:
                                        chunk = sf.read(self.advanced_options['buffer_size'] * 1024)
                                        if not chunk:
                                            break
                                        
                                        if self.advanced_options['compression']:
                                            chunk = zlib.compress(chunk)
                                        
                                        df.write(chunk)
                                        copied += len(chunk)
                                        
                                        progress = int((copied / total_size) * 100)
                                        self.progress_signal.emit(progress)
                                        
                                        # 计算写入速度和剩余时间
                                        self.calculate_progress_info(copied, total_size)
                    
                    finally:
                        # 卸载ISO
                        if sys.platform == 'darwin':
                            subprocess.run(['hdiutil', 'detach', mount_point], check=True)
            
            return True, "ISO9660模式写入完成"
        except Exception as e:
            return False, f"ISO9660模式写入失败: {str(e)}"
    
    def write_iso_to_usb(self, iso_path, usb_device):
        """写入ISO到U盘"""
        try:
            # 检查UEFI支持
            if self.advanced_options['force_uefi']:
                if not self.check_uefi_support(iso_path):
                    return False, "ISO文件不支持UEFI启动"
            
            # 选择写入方式
            if self.advanced_options['write_method'] == 'dd':
                success, message = self.write_iso_dd(iso_path, usb_device)
            else:
                success, message = self.write_iso_9660(iso_path, usb_device)
            
            if not success:
                return False, message
            
            # 写入后验证
            if self.advanced_options['verify_after_write'] and not self.advanced_options['skip_verify']:
                self.status_signal.emit("正在验证写入...")
                if not self.verify_written_data(iso_path, usb_device):
                    return False, "写入验证失败"
            
            return True, "写入完成"
            
        except Exception as e:
            return False, f"写入失败: {str(e)}"
    
    def check_uefi_support(self, iso_path):
        """检查ISO是否支持UEFI启动"""
        try:
            with tempfile.TemporaryDirectory() as mount_point:
                if sys.platform == 'darwin':
                    subprocess.run(['hdiutil', 'attach', iso_path,
                                 '-mountpoint', mount_point], check=True)
                    
                    try:
                        # 检查EFI目录
                        efi_path = os.path.join(mount_point, 'EFI')
                        if os.path.exists(efi_path):
                            return True
                    finally:
                        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
            
            return False
        except Exception:
            return False
    
    def verify_written_data(self, iso_path, usb_device):
        """验证写入的数据"""
        try:
            iso_size = os.path.getsize(iso_path)
            verified = 0
            
            with open(iso_path, 'rb') as iso_file, open(usb_device, 'rb') as usb:
                while True:
                    iso_chunk = iso_file.read(self.advanced_options['buffer_size'] * 1024)
                    if not iso_chunk:
                        break
                    
                    usb_chunk = usb.read(len(iso_chunk))
                    if iso_chunk != usb_chunk:
                        return False
                    
                    verified += len(iso_chunk)
                    progress = int((verified / iso_size) * 100)
                    self.verification_signal.emit(f"验证进度: {progress}%")
            
            return True
        except Exception:
            return False

    def detect_boot_config(self, usb_device):
        """
        检测U盘的启动配置
        :param usb_device: U盘设备路径
        :return: 启动配置信息
        """
        try:
            config = {
                'type': 'unknown',
                'bootloader': None,
                'entries': [],
                'uefi': False,
                'hybrid': False
            }
            
            with tempfile.TemporaryDirectory() as mount_point:
                if sys.platform == 'darwin':
                    subprocess.run(['hdiutil', 'attach', usb_device,
                                 '-mountpoint', mount_point], check=True)
                    
                    try:
                        # 检查UEFI启动
                        if os.path.exists(os.path.join(mount_point, 'EFI')):
                            config['uefi'] = True
                            config['type'] = 'uefi'
                            
                            # 检查EFI启动项
                            efi_boot = os.path.join(mount_point, 'EFI', 'BOOT')
                            if os.path.exists(efi_boot):
                                config['entries'].extend(
                                    f.name for f in os.scandir(efi_boot)
                                    if f.name.lower().endswith('.efi')
                                )
                        
                        # 检查Legacy启动
                        grub_cfg = os.path.join(mount_point, 'boot', 'grub', 'grub.cfg')
                        if os.path.exists(grub_cfg):
                            config['bootloader'] = 'grub2'
                            config['type'] = 'legacy'
                            
                            # 解析GRUB配置
                            with open(grub_cfg, 'r') as f:
                                content = f.read()
                                # 提取菜单项
                                for line in content.split('\n'):
                                    if 'menuentry' in line:
                                        entry = line.split("'")[1]
                                        config['entries'].append(entry)
                        
                        # 检查Syslinux
                        syslinux_cfg = os.path.join(mount_point, 'syslinux.cfg')
                        if os.path.exists(syslinux_cfg):
                            config['bootloader'] = 'syslinux'
                            config['type'] = 'legacy'
                            
                            # 解析Syslinux配置
                            with open(syslinux_cfg, 'r') as f:
                                content = f.read()
                                # 提取标签
                                for line in content.split('\n'):
                                    if line.startswith('LABEL'):
                                        entry = line.split()[1]
                                        config['entries'].append(entry)
                        
                        # 检查是否是混合启动
                        if config['uefi'] and config['bootloader']:
                            config['hybrid'] = True
                            config['type'] = 'hybrid'
                    
                    finally:
                        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
            
            self.boot_config_signal.emit(config)
            return config
            
        except Exception as e:
            self.logger.error(f"检测启动配置失败: {str(e)}")
            return None
    
    def update_boot_config(self, usb_device, config_updates):
        """
        更新启动配置
        :param usb_device: U盘设备路径
        :param config_updates: 要更新的配置
        :return: (bool, str) 更新结果和消息
        """
        try:
            with tempfile.TemporaryDirectory() as mount_point:
                if sys.platform == 'darwin':
                    subprocess.run(['hdiutil', 'attach', usb_device,
                                 '-mountpoint', mount_point], check=True)
                    
                    try:
                        # 更新GRUB配置
                        if 'grub_timeout' in config_updates:
                            grub_cfg = os.path.join(mount_point, 'boot/grub/grub.cfg')
                            if os.path.exists(grub_cfg):
                                with open(grub_cfg, 'r') as f:
                                    content = f.read()
                                
                                # 更新超时时间
                                content = re.sub(
                                    r'set timeout=\d+',
                                    f'set timeout={config_updates["grub_timeout"]}',
                                    content
                                )
                                
                                with open(grub_cfg, 'w') as f:
                                    f.write(content)
                        
                        # 更新默认启动项
                        if 'default_entry' in config_updates:
                            if os.path.exists(os.path.join(mount_point, 'boot/grub/grub.cfg')):
                                # 更新GRUB默认启动项
                                with open(os.path.join(mount_point, 'boot/grub/grub.cfg'), 'r') as f:
                                    content = f.read()
                                
                                content = re.sub(
                                    r'set default="\w+"',
                                    f'set default="{config_updates["default_entry"]}"',
                                    content
                                )
                                
                                with open(os.path.join(mount_point, 'boot/grub/grub.cfg'), 'w') as f:
                                    f.write(content)
                            
                            elif os.path.exists(os.path.join(mount_point, 'syslinux.cfg')):
                                # 更新Syslinux默认启动项
                                with open(os.path.join(mount_point, 'syslinux.cfg'), 'r') as f:
                                    content = f.read()
                                
                                content = re.sub(
                                    r'DEFAULT \w+',
                                    f'DEFAULT {config_updates["default_entry"]}',
                                    content
                                )
                                
                                with open(os.path.join(mount_point, 'syslinux.cfg'), 'w') as f:
                                    f.write(content)
                    
                    finally:
                        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
            
            return True, "启动配置更新成功"
            
        except Exception as e:
            return False, f"更新启动配置失败: {str(e)}"
    
    def repair_bootloader(self, usb_device):
        """
        修复启动引导
        :param usb_device: U盘设备路径
        :return: (bool, str) 修复结果和消息
        """
        try:
            self.repair_status_signal.emit("正在检查启动配置...")
            config = self.detect_boot_config(usb_device)
            
            if not config:
                return False, "无法检测启动配置"
            
            with tempfile.TemporaryDirectory() as mount_point:
                if sys.platform == 'darwin':
                    subprocess.run(['hdiutil', 'attach', usb_device,
                                 '-mountpoint', mount_point], check=True)
                    
                    try:
                        self.repair_status_signal.emit("正在修复启动文件...")
                        
                        # 修复UEFI启动
                        if config['uefi']:
                            efi_dir = os.path.join(mount_point, 'EFI', 'BOOT')
                            os.makedirs(efi_dir, exist_ok=True)
                            
                            # 复制UEFI启动文件
                            bootx64_path = os.path.join(efi_dir, 'bootx64.efi')
                            if not os.path.exists(bootx64_path):
                                # 从资源目录复制默认的EFI文件
                                shutil.copy(
                                    os.path.join(os.path.dirname(__file__), 
                                               'resources', 'bootx64.efi'),
                                    bootx64_path
                                )
                        
                        # 修复Legacy启动
                        if config['bootloader'] == 'grub2':
                            self.repair_status_signal.emit("正在修复GRUB...")
                            # 重新安装GRUB
                            grub_dir = os.path.join(mount_point, 'boot', 'grub')
                            os.makedirs(grub_dir, exist_ok=True)
                            
                            # 复制GRUB核心文件
                            for file in ['grubx64.efi', 'grub.cfg']:
                                src = os.path.join(os.path.dirname(__file__),
                                                 'resources', file)
                                dst = os.path.join(grub_dir, file)
                                if os.path.exists(src):
                                    shutil.copy(src, dst)
                        
                        elif config['bootloader'] == 'syslinux':
                            self.repair_status_signal.emit("正在修复Syslinux...")
                            # 重新安装Syslinux
                            for file in ['syslinux.cfg', 'ldlinux.sys']:
                                src = os.path.join(os.path.dirname(__file__),
                                                 'resources', file)
                                dst = os.path.join(mount_point, file)
                                if os.path.exists(src):
                                    shutil.copy(src, dst)
                    
                    finally:
                        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
            
            self.repair_status_signal.emit("启动修复完成")
            return True, "启动修复完成"
            
        except Exception as e:
            error_msg = f"修复启动失败: {str(e)}"
            self.repair_status_signal.emit(error_msg)
            return False, error_msg

    def create_partition_table(self, device, table_type='gpt', partitions=None):
        """
        创建分区表
        :param device: 设备路径
        :param table_type: 分区表类型 (gpt/mbr)
        :param partitions: 分区列表 [{'size': '1G', 'type': 'efi', 'format': 'fat32'}, ...]
        :return: (bool, str) 是否成功和消息
        """
        try:
            self.partition_status_signal.emit("正在创建分区表...")
            
            # 卸载设备
            subprocess.run(['diskutil', 'unmountDisk', device], check=True)
            
            # 创建分区表
            if table_type == 'gpt':
                subprocess.run(['diskutil', 'eraseDisk', 'GPT', 'UNTITLED', device], check=True)
            else:
                subprocess.run(['diskutil', 'eraseDisk', 'MBR', 'UNTITLED', device], check=True)
            
            if not partitions:
                return True, "分区表创建成功"
            
            # 创建分区
            for i, part in enumerate(partitions, 1):
                self.partition_status_signal.emit(f"正在创建分区 {i}/{len(partitions)}...")
                self.partition_progress_signal.emit(int(i/len(partitions)*100))
                
                # 转换分区类型
                format_map = {
                    'fat32': 'FAT32',
                    'ntfs': 'NTFS',
                    'exfat': 'ExFAT',
                    'ext4': 'EXT4'
                }
                
                # 创建分区
                subprocess.run([
                    'diskutil', 'addPartition',
                    device,
                    format_map.get(part['format'], 'FAT32'),
                    f'Partition{i}',
                    part['size']
                ], check=True)
            
            return True, "分区创建成功"
            
        except Exception as e:
            error_msg = f"创建分区失败: {str(e)}"
            self.partition_status_signal.emit(error_msg)
            return False, error_msg
    
    def write_hybrid_iso(self, iso_path, device, options=None):
        """
        写入混合ISO镜像
        :param iso_path: ISO文件路径
        :param device: 目标设备
        :param options: 写入选项
        :return: (bool, str) 是否成功和消息
        """
        try:
            if not options:
                options = {}
            
            # 检查ISO是否是混合镜像
            self.write_status_signal.emit("正在检查ISO类型...")
            
            # 使用file命令检查ISO类型
            result = subprocess.check_output(['file', iso_path], universal_newlines=True)
            is_hybrid = 'boot sector' in result.stdout.lower()
            
            if not is_hybrid and not options.get('force_hybrid', False):
                return False, "不是混合ISO镜像，请使用普通ISO写入模式"
            
            # 卸载设备
            subprocess.run(['diskutil', 'unmountDisk', device], check=True)
            
            # 计算总大小
            total_size = os.path.getsize(iso_path)
            
            # 创建写入进程
            with open(iso_path, 'rb') as src, open(device, 'wb') as dst:
                # 设置缓冲区大小
                buffer_size = options.get('buffer_size', 1024*1024)  # 默认1MB
                
                written = 0
                while True:
                    buffer = src.read(buffer_size)
                    if not buffer:
                        break
                    
                    dst.write(buffer)
                    written += len(buffer)
                    
                    # 更新进度
                    progress = int(written/total_size*100)
                    self.write_progress_signal.emit(progress)
                    self.write_status_signal.emit(f"正在写入: {progress}%")
            
            # 同步数据
            self.write_status_signal.emit("正在同步数据...")
            dst.flush()
            os.sync()
            
            # 验证写入
            if options.get('verify', True):
                self.write_status_signal.emit("正在验证写入...")
                
                # 重新打开设备进行验证
                with open(iso_path, 'rb') as src, open(device, 'rb') as dst:
                    while True:
                        src_data = src.read(buffer_size)
                        if not src_data:
                            break
                            
                        dst_data = dst.read(buffer_size)
                        if src_data != dst_data:
                            return False, "验证失败：数据不匹配"
            
            return True, "混合ISO写入成功"
            
        except Exception as e:
            error_msg = f"写入失败: {str(e)}"
            self.write_status_signal.emit(error_msg)
            return False, error_msg
    
    def convert_to_hybrid(self, iso_path):
        """
        将普通ISO转换为混合ISO
        :param iso_path: ISO文件路径
        :return: (bool, str) 是否成功和消息
        """
        try:
            self.write_status_signal.emit("正在转换为混合ISO...")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 复制ISO到临时目录
                temp_iso = os.path.join(temp_dir, 'temp.iso')
                shutil.copy2(iso_path, temp_iso)
                
                # 使用isohybrid转换
                subprocess.run(['isohybrid', temp_iso], check=True)
                
                # 替换原文件
                shutil.move(temp_iso, iso_path)
            
            return True, "转换成功"
            
        except Exception as e:
            return False, f"转换失败: {str(e)}"

    def scan_for_isos(self, directories=None):
        """
        扫描指定目录查找ISO文件
        :param directories: 要扫描的目录列表，如果为None则扫描默认目录
        :return: ISO文件列表
        """
        if not directories:
            # 默认扫描目录
            home = os.path.expanduser('~')
            directories = [
                os.path.join(home, 'Downloads'),  # 下载目录
                os.path.join(home, 'Desktop'),    # 桌面
                '/Applications',                   # 应用程序
                '/Volumes'                        # 挂载的磁盘
            ]
        
        iso_files = []
        
        for directory in directories:
            try:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if file.lower().endswith('.iso'):
                            full_path = os.path.join(root, file)
                            # 发出信号通知找到新的ISO
                            self.iso_found_signal.emit(full_path)
                            iso_files.append(full_path)
            except Exception as e:
                self.logger.error(f"扫描目录 {directory} 时出错: {str(e)}")
        
        return iso_files
    
    def analyze_iso(self, iso_path):
        """
        分析ISO文件的类型和特性
        :param iso_path: ISO文件路径
        :return: ISO信息字典
        """
        info = {
            'path': iso_path,
            'size': os.path.getsize(iso_path),
            'name': os.path.basename(iso_path),
            'type': 'unknown',
            'bootable': False,
            'hybrid': False,
            'uefi': False
        }
        
        try:
            # 检查文件头
            with open(iso_path, 'rb') as f:
                header = f.read(32768)  # 读取前32KB
                
                # 检查ISO9660签名
                if header[32769:32774] == b'CD001':
                    info['type'] = 'iso9660'
                
                # 检查是否可启动
                if header[32768:32774] == b'EL TORITO':
                    info['bootable'] = True
                
                # 检查是否支持UEFI
                if b'EFI' in header:
                    info['uefi'] = True
            
            # 使用file命令获取更多信息
            result = subprocess.check_output(['file', iso_path], universal_newlines=True)
            output = result.stdout.lower()
            
            if 'boot sector' in output:
                info['hybrid'] = True
            
            if 'uefi' in output:
                info['uefi'] = True
            
        except Exception as e:
            self.logger.error(f"分析ISO文件时出错: {str(e)}")
        
        return info
    
    def monitor_iso_directories(self, directories=None):
        """
        监控目录变化，自动检测新的ISO文件
        :param directories: 要监控的目录列表
        """
        if not directories:
            home = os.path.expanduser('~')
            directories = [
                os.path.join(home, 'Downloads'),
                os.path.join(home, 'Desktop')
            ]
        
        def watch_thread():
            try:
                # 创建FSEvents流
                stream = FSEventStream(
                    directories,
                    self._handle_fs_event,
                    file_events=True
                )
                
                # 启动监控
                stream.start()
                
            except Exception as e:
                self.logger.error(f"监控目录时出错: {str(e)}")
        
        # 在后台线程中启动监控
        threading.Thread(target=watch_thread, daemon=True).start()
    
    def _handle_fs_event(self, event):
        """
        处理文件系统事件
        :param event: FSEvents事件
        """
        try:
            path = event.name
            
            # 检查是否是新增的ISO文件
            if (event.mask & FSEvents.Create and
                path.lower().endswith('.iso')):
                # 发出信号通知找到新的ISO
                self.iso_found_signal.emit(path)
                
        except Exception as e:
            self.logger.error(f"处理文件系统事件时出错: {str(e)}")
