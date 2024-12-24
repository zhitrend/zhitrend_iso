import subprocess
import os
import threading
import re
from PyQt5.QtCore import QObject, pyqtSignal

class USBMaker(QObject):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def get_usb_drives(self):
        """获取可用的U盘列表"""
        try:
            # 使用diskutil list获取所有磁盘信息
            result = subprocess.check_output(['diskutil', 'list'], universal_newlines=True)
            print("Disk List Raw Output:\n", result)
            
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
                            detailed_info = subprocess.check_output(['diskutil', 'info', disk_path], universal_newlines=True)
                            print(f"Detailed Info for {disk_path}:\n", detailed_info)
                            
                            # 精确匹配各种信息
                            name_patterns = [
                                r'Volume Name:\s*(.+)',
                                r'Media Name:\s*(.+)',
                                r'Disk Name:\s*(.+)'
                            ]
                            
                            disk_name = None
                            for pattern in name_patterns:
                                name_match = re.search(pattern, detailed_info)
                                if name_match:
                                    disk_name = name_match.group(1).strip()
                                    break
                            
                            # 大小匹配
                            size_patterns = [
                                r'Total Size:\s*(.+)',
                                r'Disk Size:\s*(.+)',
                                r'Size:\s*(.+)'
                            ]
                            
                            disk_size = None
                            for pattern in size_patterns:
                                size_match = re.search(pattern, detailed_info)
                                if size_match:
                                    disk_size = size_match.group(1).strip()
                                    break
                            
                            # 文件系统匹配
                            fs_patterns = [
                                r'File System Personality:\s*(.+)',
                                r'Type:\s*(.+)'
                            ]
                            
                            fs_type = 'Unknown'
                            for pattern in fs_patterns:
                                fs_match = re.search(pattern, detailed_info)
                                if fs_match:
                                    fs_type = fs_match.group(1).strip()
                                    break
                            
                            # 如果没有找到名称，使用默认名称
                            disk_name = disk_name or f'U盘 {disk_number}'
                            disk_size = disk_size or '未知大小'
                            
                            # 组合显示信息
                            display_name = f"{disk_name} ({disk_path}) - {disk_size} [{fs_type}]"
                            print(f"Parsed Drive Info: {display_name}")
                            
                            usb_drives.append((disk_path, display_name))
                        
                        except subprocess.CalledProcessError as e:
                            print(f"Error getting disk info for {disk_path}: {e}")
                            # 如果获取详细信息失败，使用磁盘路径
                            usb_drives.append((disk_path, disk_path))
            
            # 返回可用的U盘列表
            return [name for _, name in usb_drives]
        
        except Exception as e:
            error_msg = f"获取U盘列表失败: {str(e)}"
            print(error_msg)
            self.error_signal.emit(error_msg)
            return []

    def create_bootable_usb(self, iso_path, usb_device_display):
        """制作启动盘"""
        def run_dd():
            try:
                # 使用正则表达式精确提取磁盘路径
                path_match = re.search(r'\((/dev/disk\d+)\)', usb_device_display)
                if not path_match:
                    raise ValueError(f"无法从 {usb_device_display} 提取磁盘路径")
                
                usb_device = path_match.group(1)
                print(f"准备写入磁盘: {usb_device}")
                
                # 尝试卸载U盘的所有分区
                try:
                    # 获取U盘的所有分区
                    partitions_output = subprocess.check_output(['diskutil', 'list', usb_device], universal_newlines=True)
                    partition_matches = re.findall(r'(/dev/disk\d+s\d+)', partitions_output)
                    
                    # 逐个卸载分区
                    for partition in partition_matches:
                        try:
                            subprocess.run(['diskutil', 'unmount', partition], check=True)
                            print(f"成功卸载分区: {partition}")
                        except subprocess.CalledProcessError:
                            print(f"无法卸载分区: {partition}")
                except Exception as e:
                    print(f"获取分区失败: {e}")
                
                # 卸载整个磁盘
                subprocess.run(['diskutil', 'unmountDisk', usb_device], check=True)
                
                # 使用dd命令写入
                total_size = os.path.getsize(iso_path)
                dd_command = [
                    'sudo', 'dd', 
                    f'if={iso_path}', 
                    f'of={usb_device}', 
                    'bs=1m'
                ]

                process = subprocess.Popen(dd_command, 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, 
                                           universal_newlines=True)

                while True:
                    output = process.stderr.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if 'copied' in output:
                        try:
                            copied_size = int(output.split()[0].replace(',', ''))
                            progress = int((copied_size / total_size) * 100)
                            self.progress_signal.emit(progress)
                        except:
                            pass

                if process.returncode == 0:
                    self.status_signal.emit("启动盘制作成功！")
                else:
                    self.error_signal.emit("启动盘制作失败")

            except Exception as e:
                error_msg = f"制作启动盘出错: {str(e)}"
                print(error_msg)
                self.error_signal.emit(error_msg)

        # 在新线程中执行
        thread = threading.Thread(target=run_dd)
        thread.start()
