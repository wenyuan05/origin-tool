# Windows 上安装 Python（给首次使用者）

本工具的一键启动文件需要 **64 位 Python 3.11**。安装 Python 只需做一次；电脑上已有其他版本的 Python 也不必卸载。

## 1. 下载

点击 Python 官网提供的 [Python 3.11.9 Windows 64 位安装包](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)，下载 `python-3.11.9-amd64.exe`。也可以进入[官方发布页](https://www.python.org/downloads/release/python-3119/)，向下找到 **Files → Windows installer (64-bit)**。不要选 32 位版或 embeddable package。

> Python 3.11.9 是 3.11 系列最后一个提供 Windows 安装程序的版本。后续的 3.11 安全更新没有这种安装程序；若电脑已经装有其他可用的 64 位 Python 3.11，不必换成 3.11.9。

## 2. 安装

1. 双击下载的安装文件。
2. 保留 **Python Launcher**、**pip** 和 **tcl/tk and IDLE**（图形窗口需要 tkinter）这些安装项。一般直接点 **Install Now** 即可；如选 **Customize installation**，不要取消这些项目。
3. 如果看到 **Add python.exe to PATH**，可以勾选；本工具使用 `py -3.11`，不依赖这个选项。
4. 等待安装完成，再关闭安装窗口。

## 3. 启动绘图工具

下载或解压本项目，进入能看到 `README.md` 和 `一键启动.cmd` 的文件夹，双击 **一键启动.cmd**。首次运行会联网安装工具依赖，完成后出现选列窗口。绘图时还需要电脑上已安装并授权 Origin。

## 安装后仍提示找不到 Python？

先关闭旧的命令窗口，再双击 `一键启动.cmd`。若仍失败，可以按 **Win + R**、输入 `cmd`、回车，然后逐行输入：

```text
py -3.11 --version
py -3.11 -c "import struct, tkinter; print(struct.calcsize('P') * 8)"
```

第一行应显示 `Python 3.11.x`，第二行应显示 `64`。如果 `py` 无法识别，重新运行 Python 安装程序并确认安装 **Python Launcher**；如果版本不对，请确认下载的是 3.11 的 64 位安装包。安装依赖时若报网络错误，确认联网后再次双击启动文件即可重试。

安装选项和 `py` 命令可参考 [Python 官方 Windows 使用说明](https://docs.python.org/3.11/using/windows.html)。
