# CSV/TXT 数据生成 Origin 工程

这个工具从普通 Python 启动一个临时选列窗口，读取仪器 CSV/TXT 中选定的 X、左 Y 和右 Y 列，调用本机 Origin 自动生成包含数据工作表和可编辑图窗的 .opju 工程。需要时可勾选导出同名 .png 预览图，默认不导出。无需先打开 Origin 界面。未选中的数据列不会进入工程。

## 依赖（首次安装）

- Windows，已安装并授权 Origin/OriginPro 2021 或更新版本。
- 64 位 Python 3.11（其他受 OriginExt 支持的 Python 版本也可使用）。
- 项目依赖见 requirements.txt：originpro，安装时会带上 OriginExt。图形窗口使用 Python 标准库 tkinter，CSV 读取不需 pandas。

将项目文件夹复制或解压到任意位置，双击 [一键启动.cmd](一键启动.cmd) 即可。首次启动会在项目文件夹里创建 `.venv` 并安装依赖，需要联网；以后双击同一个文件即可打开选列窗口。电脑需先安装 64 位 Python 3.11 和 Origin；若缺少 Python 或安装失败，窗口会显示错误并停留，便于查看原因。

也可以在 PowerShell 7 中手动安装：

~~~powershell
cd "你的 Origin_tool 文件夹路径"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

如果 py -3.11 不可用，可换成另一套 64 位且与 OriginExt wheel 兼容的 Python。虚拟环境装在本目录，不修改全局 Python。

## 分享给其他人

可以把此文件夹中的脚本、说明、配置、`requirements.txt` 和示例 CSV 打包为 ZIP；若使用 Git，可把仓库推送到你选择的平台，让对方克隆。`.venv`、`__pycache__` 和本地生成的工程/图片不必打包，对方按上面的步骤在自己的电脑上安装依赖。对方若只需查看已完成的图，直接发送生成的 `.opju`；若还需快速预览，可同时发送同名 `.png`。生成的工程已经包含选中的数据列。

## 日常使用

双击 [一键启动.cmd](一键启动.cmd)（或 `start_gui.cmd`），也可以在 PowerShell 7 中执行：

~~~powershell
.\.venv\Scripts\python.exe .\app\origin_plot_gui.py
~~~

1. 点“选择文件…”，选择 CSV 或 TXT；若中文表头乱码，试把编码切换为 gb18030。
2. 每列选“忽略 / X / 左 Y / 右 Y”。需要恰好 1 列 X、至少 1 列 Y；左右 Y 可各选 0 列或多列。
3. 选择 .opju 保存位置；需要预览图时勾选“同时导出 PNG 预览图”，再点“生成工程”。若本次要生成的文件已存在，窗口会先询问是否覆盖。

`examples/` 中的 sample_instrument_export.csv 和 sample_instrument_export.txt 是同一份 10 列模拟仪器数据，分别使用逗号和制表符分隔，其中几列是无关数据或文字，适合先试用。示例映射：time_s → X，temperature_C → 左 Y，pressure_kPa → 右 Y。工程内写入这三列数值，因此日后打开工程无需原数据文件的路径。

## 不打开窗口，直接按配置生成

编辑 [plot_config.json](config/plot_config.json) 的文件路径与列名后运行。配置中的相对路径以 `config/` 为基准；默认工程保存到 `outputs/`，且只生成 `.opju`。如需 PNG，将 `export_png` 改为 `true`，`output_png` 可省略（默认与工程同名）或指定单独路径：

~~~powershell
.\.venv\Scripts\python.exe .\app\plot_dual_y_origin.py --check-only
.\.venv\Scripts\python.exe .\app\plot_dual_y_origin.py
~~~

第一次只检查 CSV 和选列，不启动 Origin；第二次在后台生成工程。已有目标文件时，命令行默认拒绝覆盖；明确要覆盖时加 --overwrite。路径可写成绝对路径，或相对于配置文件所在目录的路径。

## 文件夹与限制

- `app/`：GUI、绘图脚本与 CSV/TXT 读取代码。
- `config/`：无窗口模式的默认配置。
- `examples/`：10 列 CSV/TXT 模拟仪器数据，以及早期的 4 列试用数据。
- `docs/`：双 Y 选列示例和 [Origin 手动画图速查](docs/QUICK_START.md)。
- `outputs/`：默认工程输出位置；程序会自动创建，Git 不收录其中的生成文件。

`app/plot_csv_origin.py` 是早期在 Origin 内手动画单 Y 图的示例，当前自动工程流程不需要它。

输入文件首行必须是列名。CSV/TXT 可使用制表符、逗号、分号或连续空白分隔；连续空白分隔时列名不能含空格。文件的后续行应使用相同分隔方式；无需绘图的列可以是文字。Excel 文件请先另存为 CSV 或文本文件。需要本机 Origin 自动化服务可启动并有有效授权；若保存失败，命令行会报错，GUI 会显示错误。

实现依据：[Origin 外部 Python 说明](https://docs.originlab.com/externalpython/)、[官方 .opju 保存示例](https://docs.originlab.com/externalpython/external-python-code-samples/)。
