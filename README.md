# CSV/TXT 数据生成 Origin 工程

这个工具从普通 Python 启动选列窗口，读取一个或多个仪器 CSV/TXT 中选定的 X、左 Y 和右 Y 列，调用本机 Origin 自动生成包含数据工作表和可编辑图窗的 .opju 工程。多文件可叠加到一张图，或每个文件各出一张图。需要时可勾选导出 .png 预览图，默认不导出。无需先打开 Origin 界面。未选中的数据列不会进入工程。

## 依赖（首次安装）

- Windows，已安装并授权 Origin/OriginPro 2021 或更新版本。
- 已安装的 64 位 CPython 3.8–3.14；一键启动会寻找可用版本。首次安装可按 [Python 安装教程](docs/PYTHON_INSTALL.md) 操作。
- 项目依赖见 requirements.txt：originpro，安装时会带上 OriginExt。图形窗口使用 Python 标准库 tkinter，CSV 读取不需 pandas。

将项目文件夹复制或解压到任意位置，双击 [一键启动.cmd](一键启动.cmd) 即可。首次启动会从电脑已有的兼容 Python 中选择一个，在项目文件夹里创建 `.venv` 并安装依赖，需要联网；以后会复用这个环境。电脑还需安装 Origin；若缺少可用 Python 或安装失败，窗口会显示错误并停留，便于查看原因。

也可以在 PowerShell 7 中手动安装。以下以已安装 Python 3.14 为例；请将 `3.14` 换成自己电脑上的兼容版本：

~~~powershell
cd "你的 Origin_tool 文件夹路径"
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

若电脑没有 `py` 启动器、但 `python` 命令指向兼容版本，一键启动也会使用它。虚拟环境装在本目录，不修改全局 Python；已有可用的 `.venv` 会继续复用。

## 分享给其他人

可以把此文件夹中的脚本、说明、配置、`requirements.txt` 和示例 CSV 打包为 ZIP；若使用 Git，可把仓库推送到你选择的平台，让对方克隆。`.venv`、`__pycache__` 和本地生成的工程/图片不必打包，对方按上面的步骤在自己的电脑上安装依赖。对方若只需查看已完成的图，直接发送生成的 `.opju`；若还需快速预览，可同时发送同名 `.png`。生成的工程已经包含选中的数据列。

## 日常使用

双击 [一键启动.cmd](一键启动.cmd)（或 `start_gui.cmd`），也可以在 PowerShell 7 中执行：

~~~powershell
.\.venv\Scripts\python.exe .\app\origin_plot_gui.py
~~~

1. 点“添加文件…”选择一个或多个 CSV/TXT；也可以多次添加、移除选中项。若中文表头乱码，试把编码切换为 gb18030。
2. 在共同列名中为所有文件指定同一套“忽略 / X / 左 Y / 右 Y”；需要恰好 1 列 X、至少 1 列 Y。各文件的 X 点位可以不同。
3. 多文件出图选“叠加对比”或“分别出图”。选择 .opju 保存位置；需要预览图时勾选 PNG，再点“生成工程”。若输出文件已存在，窗口会先询问是否覆盖。

`examples/` 中的 sample_instrument_export.csv 和 sample_instrument_export.txt 是同一份 10 列模拟仪器数据，分别使用逗号和制表符分隔，其中几列是无关数据或文字，适合先试用。示例映射：time_s → X，temperature_C → 左 Y，pressure_kPa → 右 Y。工程内写入这三列数值，因此日后打开工程无需原数据文件的路径。

`examples/sample_spectrum_device_a.txt` 和 `sample_spectrum_device_b.txt` 模拟器件光谱文件：前两行是测量信息，第 3 行是制表符表头，后面是数字。选 `Wavelength(nm)` 为 X，并按偏压选择左右 Y。多文件时每个器件的数据保存在独立工作簿；叠加图的图例带文件名。测量信息和文件名会保存到工程的 `Source_Info` 便签，便签不记录电脑上的绝对路径。`separate` 模式会在同一工程生成多个图窗。若同时导出 PNG，`overlay` 得到一张图片，`separate` 得到按序号命名的多张图片。

## 不打开窗口，直接按配置生成

编辑 [plot_config.json](config/plot_config.json) 的文件路径与列名后运行。配置中的相对路径以 `config/` 为基准；默认工程保存到 `outputs/`，且只生成 `.opju`。如需 PNG，将 `export_png` 改为 `true`，`output_png` 可省略（默认与工程同名）或指定单独路径：

~~~powershell
.\.venv\Scripts\python.exe .\app\plot_dual_y_origin.py --check-only
.\.venv\Scripts\python.exe .\app\plot_dual_y_origin.py
~~~

第一次只检查 CSV 和选列，不启动 Origin；第二次在后台生成工程。已有目标文件时，命令行默认拒绝覆盖；明确要覆盖时加 --overwrite。路径可写成绝对路径，或相对于配置文件所在目录的路径。

多文件配置参见 [multi_spectrum_example.json](config/multi_spectrum_example.json)：用 `data_files` 数组代替单个 `data_file`，再用 `plot_mode` 选择 `overlay` 或 `separate`。多文件共用列名与绘图方式，各文件分别解析，不要求 X 数值逐行相同。例如：

~~~powershell
.\.venv\Scripts\python.exe .\app\plot_dual_y_origin.py --config .\config\multi_spectrum_example.json --check-only
~~~

## 文件夹与限制

- `app/`：GUI、绘图脚本与 CSV/TXT 读取代码。
- `config/`：无窗口模式的默认配置。
- `examples/`：10 列 CSV/TXT 模拟仪器数据，以及早期的 4 列试用数据。
- `docs/`：[Python 安装教程](docs/PYTHON_INSTALL.md)、双 Y 选列示例和 [Origin 手动画图速查](docs/QUICK_START.md)。
- `outputs/`：默认工程输出位置；程序会自动创建，Git 不收录其中的生成文件。

`app/plot_csv_origin.py` 是早期在 Origin 内手动画单 Y 图的示例，当前自动工程流程不需要它。

普通 CSV/TXT 的首行必须是列名；光谱 TXT 可在表头前包含 `Measurement Time:` 和 `Device Area:` 两行测量信息，这两行会从表格中跳过，并保存到工程便签，数据从表头开始解析。CSV/TXT 可使用制表符、逗号、分号或连续空白分隔；连续空白分隔时列名不能含空格。文件的后续行应使用相同分隔方式；无需绘图的列可以是文字。多文件需具有所选列名。Excel 文件请先另存为 CSV 或文本文件。需要本机 Origin 自动化服务可启动并有有效授权；若保存失败，命令行会报错，GUI 会显示错误。

实现依据：[Origin 外部 Python 说明](https://docs.originlab.com/externalpython/)、[官方 .opju 保存示例](https://docs.originlab.com/externalpython/external-python-code-samples/)。
