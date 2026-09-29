# 器件光谱与电学数据生成 Origin 工程

工具从普通 Python 启动窗口，读取一个或多个 CSV/TXT，自动生成包含数据表和可编辑图窗的 `.opju`。支持光谱文件、电学文件、器件匹配和图组控制。

## 环境

- Windows，已安装并授权 Origin/OriginPro 2021 或更新版本。
- 64 位 CPython 3.8–3.14；双击 [一键启动.cmd](一键启动.cmd) 会自动选择并创建 `.venv`。
- 依赖见 [requirements.txt](requirements.txt)。首次启动需要联网安装 `originpro` / `OriginExt`。

## 日常使用

双击 [一键启动.cmd](一键启动.cmd)，或执行：

~~~powershell
.\.venv\Scripts\python.exe .\app\device_plot_gui.py
~~~

1. 在“光谱”和“电学”区域分别添加文件。文件名会自动推断器件名，也可以手动修改；相同器件名表示同一器件的不同数据来源。
2. 为每个文件填写图组名。同名图组叠加到同一张图，不同图组分别生成图窗。默认光谱按器件分图，电学默认使用“电学对比”图组。
3. 在各自的选列区指定一个 X、左 Y 和右 Y。需要至少一个 Y；左右 Y 可以各选任意数量。
4. 选择 `.opju` 保存位置并生成工程。所有结果放在同一个工程中。

光谱文件通常一个器件一份文件，每个图组生成一张光谱图。电学文件会合并到同一张“电学数据合并”工作表；每个文件的列保持自己的行顺序，行数不同的列留空，绘图时每条曲线使用自己的 X 列。

## 表头与数据识别

表头识别不依赖固定行号。程序会跳过空行和前置说明，寻找“非空、不重复列名，且后面紧跟列数一致数值数据”的行；识别失败时窗口会提示检查文件内容或编码。支持制表符、逗号、分号和连续空白分隔。`Measurement Time:`、`Device Area:` 等前置信息会写入工程的 `Source_Info` 便签，便签不记录电脑绝对路径。

## 无窗口配置运行

完整示例见 [device_workflow_example.json](config/device_workflow_example.json)：

~~~powershell
.\.venv\Scripts\python.exe .\app\device_workflow.py --config .\config\device_workflow_example.json --check-only
.\.venv\Scripts\python.exe .\app\device_workflow.py --config .\config\device_workflow_example.json --overwrite
~~~

配置中的 `spectrum_files` 和 `electrical_files` 每项可填写 `path`、`device`、`plot_group`。同一 `plot_group` 叠加，不同 `plot_group` 分图。`spectrum_plot` 和 `electrical_plot` 分别保存两类数据的选列。

旧的单类流程仍可使用：[plot_config.json](config/plot_config.json)、[plot_dual_y_origin.py](app/plot_dual_y_origin.py)。

## 示例文件

- `examples/sample_spectrum_device_a.txt` / `b.txt`：带前置测量信息的光谱文件。
- `examples/sample_spectrum_device_a-Electrical.txt` / `b-Electrical.txt`：表头前有空行的电学文件，包含 `NaN` 示例。
- [device_workflow_example.json](config/device_workflow_example.json)：完整光谱+电学工程配置。

## 限制

选作绘图的 X、Y 列必须是数字；各数据行需要与表头列数一致。Excel 文件请先另存为 CSV 或 TXT。生成工程需要本机 Origin 自动化服务可启动并有有效授权。
