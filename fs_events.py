import os
import threading
import subprocess
import shlex

class FSEvents:
    """事件类型常量"""
    Create = 'Created'
    Delete = 'Removed'
    Modify = 'Updated'

class FSEventStream:
    """文件系统事件监控类"""
    
    def __init__(self, paths, callback, file_events=True):
        """
        初始化FSEventStream
        :param paths: 要监控的路径列表
        :param callback: 事件回调函数
        :param file_events: 是否监控文件级别事件（此参数保留用于兼容性）
        """
        self.paths = paths
        self.callback = callback
        self.process = None
        self.thread = None
        self.running = False
    
    def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                if self.process:
                    self.process.kill()
        
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
    
    def _monitor_thread(self):
        """监控线程"""
        try:
            # 构建 fswatch 命令
            cmd = ['fswatch', '-0']
            for path in self.paths:
                if os.path.exists(path):
                    cmd.append(shlex.quote(path))
            
            # 启动 fswatch 进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 读取输出
            while self.running:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                # 处理事件
                path = line.strip('\0\n')
                if path.lower().endswith('.iso'):
                    event = type('Event', (), {
                        'name': path,
                        'mask': FSEvents.Create
                    })
                    if self.callback:
                        self.callback(event)
        
        except Exception as e:
            print(f"监控错误: {str(e)}")
        
        finally:
            self.running = False
    
    def __del__(self):
        """析构函数，确保停止监控"""
        self.stop()
