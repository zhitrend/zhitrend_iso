import os
import sys
import threading
import re
import subprocess
import platform
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

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

    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)

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

    def create_bootable_usb(self, iso_path, usb_device_display):
        """制作启动盘"""
        def run_dd():
            try:
                # 检查sudo密码是否存在
                sudo_password = os.environ.get('SUDO_PASSWORD', '')
                
                # 使用正则表达式精确提取磁盘路径
                path_match = re.search(r'\((/dev/\w+\d*)\)', usb_device_display)
                if not path_match:
                    raise ValueError(f"无法从 {usb_device_display} 提取磁盘路径")
                
                usb_device = path_match.group(1)
                self.logger.info(f"准备写入磁盘: {usb_device}")
                
                # 检查ISO文件是否存在且可读
                if not os.path.exists(iso_path):
                    raise FileNotFoundError(f"ISO文件不存在: {iso_path}")
                
                if not os.access(iso_path, os.R_OK):
                    raise PermissionError(f"无法读取ISO文件: {iso_path}")
                
                # 获取ISO文件大小
                iso_size = os.path.getsize(iso_path)
                self.logger.info(f"ISO文件大小: {iso_size} 字节")
                
                # 获取跨平台命令
                dd_command = self.get_dd_command(iso_path, usb_device)
                
                if not dd_command:
                    raise OSError("当前操作系统不支持直接制作启动盘")
                
                self.logger.info(f"执行命令: {' '.join(dd_command)}")

                # 使用subprocess执行命令
                process = subprocess.Popen(
                    dd_command, 
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    universal_newlines=True
                )

                # 发送密码
                if 'sudo' in dd_command:
                    process.stdin.write(sudo_password + '\n')
                    process.stdin.flush()

                # 实时跟踪进度
                while True:
                    # 读取stderr输出
                    stderr_line = process.stderr.readline()
                    
                    # 记录所有输出
                    if stderr_line:
                        self.logger.info(f"dd输出: {stderr_line.strip()}")
                        
                        # 解析进度信息
                        progress_match = re.search(r'(\d+)\s*bytes', stderr_line)
                        if progress_match:
                            try:
                                current_copied = int(progress_match.group(1))
                                progress = min(int((current_copied / iso_size) * 100), 100)
                                
                                # 在主线程中发送信号
                                def update_progress():
                                    self.progress_signal.emit(progress)
                                
                                from PyQt5.QtCore import QTimer
                                QTimer.singleShot(0, update_progress)
                            except Exception as e:
                                self.logger.error(f"进度计算错误: {e}")
                    
                    # 检查进程是否结束
                    if process.poll() is not None:
                        break

                # 检查命令执行结果
                return_code = process.returncode
                
                if return_code == 0:
                    # 在主线程中发送成功信号
                    def emit_success():
                        self.status_signal.emit("启动盘制作成功！")
                        self.progress_signal.emit(100)
                    
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(0, emit_success)
                else:
                    # 获取错误输出
                    _, stderr = process.communicate()
                    error_msg = f"启动盘制作失败：{stderr}"
                    self.logger.error(error_msg)
                    
                    # 在主线程中发送错误信号
                    def emit_error():
                        self.error_signal.emit(error_msg)
                    
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(0, emit_error)

            except Exception as e:
                error_msg = f"制作启动盘出错: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                # 在主线程中发送错误信号
                def emit_error():
                    self.error_signal.emit(error_msg)
                
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, emit_error)

        # 在新线程中执行
        thread = threading.Thread(target=run_dd)
        thread.start()
