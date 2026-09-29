# Windows 上安装 Python（给首次使用者）

本工具支持电脑上已有的 **64 位 CPython 3.8–3.14**，不要求大家安装同一版本。先双击项目根目录的 `一键启动.cmd`；只要找到兼容版本，它会自动创建项目专用环境并安装依赖。已有可用的 `.venv` 会继续复用。

## 找不到可用 Python 时

1. 在 [Python 官方发布页](https://www.python.org/downloads/release/python-3147/)的 **Files** 表格中选择 **Windows installer (64-bit)**。也可以直接下载 [Python 3.14.7 官方 64 位安装包](https://www.python.org/ftp/python/3.14.7/python-3.14.7-amd64.exe)。不要选 32 位版或 embeddable package。
2. 双击安装包。保留 **Python Launcher**、**pip** 和 **tcl/tk and IDLE**（选列窗口需要 tkinter）这些安装项；一般直接点 **Install Now** 即可。如果看到 **Add python.exe to PATH**，可以勾选，方便在没有 Python Launcher 时也能找到 Python。
3. 安装结束后，再双击 `一键启动.cmd`。首次运行需要联网安装 `originpro` / `OriginExt`；绘图还需要本机安装并授权 Origin。

当前依赖的 [OriginExt 1.2.5](https://pypi.org/project/OriginExt/1.2.5/#files) 为 Windows 64 位 CPython 3.8–3.14 提供了安装包。脚本会检查 Python 版本、位数以及 `tkinter`、`venv`，再创建 `.venv`。电脑上装有多个版本时，不必卸载其他版本。

## 如果仍无法启动

- 提示找不到兼容 Python：安装后重新双击启动文件；如果 `py` 不可用，确认安装时保留了 **Python Launcher**，或让兼容的 `python.exe` 能从命令行找到。
- 提示已有 `.venv` 无法运行：在文件管理器中把项目内的 `.venv` 文件夹重命名为 `.venv.old`，再双击启动文件创建新环境。原文件夹会保留。
- 依赖下载失败：检查网络连接，然后重新双击启动文件。

愿意检查版本时，可按 **Win + R**、输入 `cmd`、回车，然后输入 `py --list-paths`；若没有 `py`，试 `python --version`。更多安装说明见 [Python 官方 Windows 文档](https://docs.python.org/3/using/windows.html)。
