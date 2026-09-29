# CSV 数据生成 Origin 工程

这个工具从普通 Python 启动一个临时选列窗口，读取仪器 CSV 中选定的 X、左 Y 和右 Y 列，调用本机 Origin 自动生成包含数据工作表和可编辑图窗的 .opju 工程，并另外导出同名 .png 预览图。无需先打开 Origin 界面。未选中的 CSV 列不会进入工程。

## 依赖（首次安装）

- Windows，已安装并授权 Origin/OriginPro 2021 或更新版本。本机已检测到 Origin 2026b。
- 64 位 Python 3.11（本机已安装；其他受 OriginExt 支持的 Python 版本也可使用）。
- 项目依赖见 requirements.txt：originpro，安装时会带上 OriginExt。图形窗口使用 Python 标准库 tkinter，CSV 读取不需 pandas。

在 PowerShell 7 中执行一次：

~~~powershell
cd F:\Project\Origin_tool
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

如果 py -3.11 不可用，可换成另一套 64 位且与 OriginExt wheel 兼容的 Python。虚拟环境装在本目录，不修改全局 Python。

## 日常使用

双击 [start_gui.cmd](start_gui.cmd)，或在 PowerShell 7 中执行：

~~~powershell
F:\Project\Origin_tool\.venv\Scripts\python.exe F:\Project\Origin_tool\origin_plot_gui.py
~~~

1. 点“选择文件…”，选择 CSV；若中文表头乱码，试把编码切换为 gb18030。
2. 每列选“忽略 / X / 左 Y / 右 Y”。需要恰好 1 列 X、至少 1 列 Y；左右 Y 可各选 0 列或多列。
3. 选择 .opju 保存位置，点“生成工程”。同名 PNG 会放在工程旁边。若同名文件已存在，窗口会先询问是否覆盖。

自带的 sample_instrument_export.csv 有 10 列，其中几列是无关数据或文字，适合先试用。示例映射：time_s → X，temperature_C → 左 Y，pressure_kPa → 右 Y。工程内写入这三列数值，因此日后打开工程无需原 CSV 的路径。

## 不打开窗口，直接按配置生成

编辑 [plot_config.json](plot_config.json) 的文件路径与列名后运行：

~~~powershell
F:\Project\Origin_tool\.venv\Scripts\python.exe F:\Project\Origin_tool\plot_dual_y_origin.py --check-only
F:\Project\Origin_tool\.venv\Scripts\python.exe F:\Project\Origin_tool\plot_dual_y_origin.py
~~~

第一次只检查 CSV 和选列，不启动 Origin；第二次在后台生成工程。已有目标文件时，命令行默认拒绝覆盖；明确要覆盖时加 --overwrite。路径可写成绝对路径，或相对于配置文件所在目录的路径。

## 文件与限制

- origin_plot_gui.py：外部 Python 的选列窗口。
- plot_dual_y_origin.py：数据检查、Origin 绘图和 .opju / PNG 保存。
- plot_config.json：无窗口模式的默认配置。
- sample_instrument_export.csv：10 列模拟仪器数据；sample_measurements.csv：早期的 4 列试用数据。
- plot_csv_origin.py、QUICK_START.md：早期在 Origin 内手动画单 Y 图的示例，当前自动工程流程不需要它们。

目前输入支持逗号分隔的 CSV；如仪器输出 Excel/TSV，请先另存为 CSV。需要本机 Origin 自动化服务可启动并有有效授权；若保存失败，命令行会报错，GUI 会显示错误。

实现依据：[Origin 外部 Python 说明](https://docs.originlab.com/externalpython/)、[官方 .opju 保存示例](https://docs.originlab.com/externalpython/external-python-code-samples/)。
