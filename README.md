# ISO to USB Maker

## 功能描述
这是一个macOS下的USB启动盘制作工具，可以将ISO镜像文件直接写入U盘，制作可启动的USB驱动器。

## 特性
- 简单的图形界面
- 自动检测可用U盘
- 实时显示写入进度
- 支持各种ISO镜像文件

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用说明
1. 选择ISO文件
2. 选择目标U盘
3. 点击"开始制作启动盘"

## 注意事项
- 制作启动盘将清除U盘上的所有数据
- 需要管理员权限
- 请谨慎操作

## 运行
```bash
python main.py
```

## 许可
MIT License
