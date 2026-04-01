# QNX Automation Tool

一个用于连接 QNX 设备并执行 shell 命令的自动化工具。

## 功能特点

- 通过 ADB root 获取设备权限
- 使用 busybox telnet 连接到 QNX 设备
- 支持批量执行命令
- 支持交互式模式
- 支持从脚本文件读取命令
- 生成独立可执行文件，无需 Python 环境

## 安装要求

1. **ADB (Android Debug Bridge)**: 确保已安装 Android SDK platform-tools
2. **Python 3.6+** (仅用于从源码运行)
3. **网络连接**: 确保主机可以访问 QNX 设备

## 使用方法

### 方式一：使用可执行文件（推荐）

```bash
# Linux
./dist/qnx_automation [选项]

# Windows
dist\qnx_automation.exe [选项]
```

### 方式二：使用 Python 运行

```bash
python qnx_automation.py [选项]
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--ip` | QNX 设备 IP 地址 | 192.168.118.2 |
| `--port` | Telnet 端口 | 23 |
| `--username` | 用户名 | root |
| `--password` | 密码 | mQx@r7PLv#Nf |
| `--command`, `-c` | 要执行的命令（可多次指定） | - |
| `--script`, `-s` | 包含命令的脚本文件 | - |
| `--interactive`, `-i` | 交互模式 | False |

## 使用示例

### 1. 执行单个命令

```bash
./qnx_automation -c "ls -la"
```

### 2. 执行多个命令

```bash
./qnx_automation -c "pwd" -c "uname -a" -c "ps aux"
```

### 3. 从脚本文件执行命令

创建 `commands.txt`:
```
# 这是注释
ps aux
netstat -an
df -h
```

执行:
```bash
./qnx_automation -s commands.txt
```

### 4. 指定不同的设备 IP

```bash
./qnx_automation --ip 192.168.1.100 -c "whoami"
```

### 5. 交互模式

```bash
./qnx_automation -i
```

## 工作流程

1. 执行 `adb root` 获取 root 权限
2. 验证 `adb shell` 连接
3. 通过 `busybox telnet` 连接到 QNX 设备
4. 自动登录（使用提供的凭据）
5. 执行指定的命令
6. 显示结果并断开连接

## 构建可执行文件

如果需要重新构建可执行文件：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建
pyinstaller --onefile --name qnx_automation qnx_automation.py

# 可执行文件将生成在 dist/ 目录
```

## 注意事项

- 确保 QNX 设备已启用 telnet 服务
- 确保设备上安装了 busybox
- 首次连接可能需要较长时间
- 某些命令的输出可能会被缓冲

## 故障排除

### adb 未找到
```
[-] adb not found. Please ensure Android SDK platform-tools is installed.
```
解决方案：安装 Android SDK platform-tools 并将其添加到 PATH

### 连接超时
```
[-] adb root timed out
```
解决方案：检查设备连接状态，确保 USB 调试已启用

### Telnet 连接失败
```
[-] Telnet connection failed
```
解决方案：
- 确认 QNX 设备的 IP 地址正确
- 确认 telnet 服务正在运行
- 检查防火墙设置

## 安全警告

⚠️ **重要**: 本工具包含硬编码的凭据。在生产环境中使用时：
- 不要将包含敏感信息的脚本分发给他人
- 考虑使用环境变量或配置文件存储凭据
- 确保网络连接的安全性

## 许可证

MIT License
