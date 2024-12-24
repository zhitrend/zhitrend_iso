import subprocess
import os
import threading
import re
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/usb_maker.log',
    filemode='w'
)

class USBMaker(QObject):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

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
                
                # 打印调试信息
                self.logger.info(f"获取的sudo密码长度: {len(sudo_password)}")
                
                # 使用正则表达式精确提取磁盘路径
                path_match = re.search(r'\((/dev/disk\d+)\)', usb_device_display)
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
                
                # 使用shell执行dd命令
                dd_command = f"echo '{sudo_password}' | sudo -S dd if='{iso_path}' of='{usb_device}' bs=1m status=progress"
                
                self.logger.info(f"执行命令: {dd_command}")

                # 使用subprocess.Popen执行命令
                process = subprocess.Popen(
                    dd_command, 
                    shell=True,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    universal_newlines=True
                )

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
