# 文件分组生成 Origin 工程

从 CSV/TXT 中选择数据列，按文件分组生成可编辑的 Origin `.opju` 工程。每组可以单独设置“组内叠加”：勾选后，同组文件画在一张图；不勾选，每个文件分别成图。一个工程可以包含多个分组，各组可以选择不同的 X、左 Y、右 Y 列。

## 准备

- Windows，已安装并授权 Origin/OriginPro 2021 或更新版本。
- 64 位 CPython 3.8–3.14；双击 [一键启动.cmd](一键启动.cmd) 会寻找可用版本、创建 `.venv` 并安装依赖。首次安装需要联网。没有 Python 时参见 [Python 安装教程](docs/PYTHON_INSTALL.md)。

## 日常使用

双击 [一键启动.cmd](一键启动.cmd)，或运行：

~~~powershell
.\.venv\Scripts\python.exe .\app\group_plot_gui.py
~~~

1. 创建分组，并在每组内添加一个或多个 CSV/TXT 文件。分组名可以随时修改。
2. 按需要勾选“组内叠加”。例如把多个光谱文件放一组并关闭叠加，每份光谱单独出图；把多个电学文件放另一组并开启叠加，得到电学对比图。
3. 在每组的共同列名中选一个 X、至少一个 Y；左 Y 和右 Y 都可以选多列。不同组可以有不同列结构。选择 `.opju` 保存位置并点击“生成工程”。

每组的数据保存在一张 Origin 工作表内，各文件的原始列并排放置。不同文件的行数或 X 点位可以不同；短列的后续行留空。图中的每条曲线引用各自文件的 X 列。文件名和表头前的测量说明写入工程的 `Source_Info` 便签，不写入电脑绝对路径。

## 表头识别

程序不依赖固定表头行号，会跳过空行和前置说明，寻找后面紧跟列数一致数值数据的表头。识别失败时会提示检查文件内容或编码。支持制表符、逗号、分号和连续空白分隔；连续空白分隔时列名不能含空格。数据行需要与表头列数一致。选作 X 的列不能有空值或 NaN；Y 列允许少量 NaN，但至少需要两个有效数值。

## 无窗口运行

[group_config_example.json](config/group_config_example.json) 展示两个分组，一个分图，一个叠加：

~~~powershell
.\.venv\Scripts\python.exe .\app\group_workflow.py --config .\config\group_config_example.json --check-only
.\.venv\Scripts\python.exe .\app\group_workflow.py --config .\config\group_config_example.json --overwrite
~~~

配置中的相对路径以配置文件所在目录为准。`--check-only` 只检查文件与选列，不启动 Origin。已有目标文件时，命令行默认拒绝覆盖；明确需要覆盖时加 `--overwrite`。

## 示例与旧流程

- `examples/sample_spectrum_device_a.txt` 和 `b.txt`：光谱示例。
- `examples/sample_spectrum_device_a-Electrical.txt` 和 `b-Electrical.txt`：有空白表头前行、不同数据长度及 NaN 的示例。
- 旧的单类选列窗口可运行 [origin_plot_gui.py](app/origin_plot_gui.py)；对应配置见 [plot_config.json](config/plot_config.json)。

项目依赖见 [requirements.txt](requirements.txt)。Excel 文件请先另存为 CSV 或 TXT。Origin 自动化服务需要在本机可启动并有有效授权。
