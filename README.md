# USB启动盘制作工具 (MacOS)

## 项目简介
这是一个专为macOS用户开发的简单、高效的USB启动盘制作工具。支持将ISO镜像文件快速、安全地写入U盘，制作系统启动盘。

## 主要特性
- 现代化图形界面
- 自动检测可用U盘
- 支持各种ISO镜像文件
- 安全的磁盘写入流程
- 实时写入进度显示

## 系统要求
- macOS 10.15+
- Python 3.7+
- PyQt5
- 管理员权限

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法
1. 选择ISO文件
2. 选择目标U盘
3. 点击"开始制作启动盘"

## 注意事项
- 制作启动盘将清除U盘上的所有数据
- 需要管理员权限
- 请谨慎操作

## 运行程序
```bash
python main.py
```

## 故障排除
- 确保U盘已正确连接
- 检查ISO文件是否完整
- 以管理员权限运行

## 许可证
MIT License

## 贡献
欢迎提交Issues和Pull Requests！

## 联系
如有任何问题，请提交GitHub Issues
