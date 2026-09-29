# X / 左 Y / 右 Y 选列示例

日常操作请看 [README.md](README.md)。本示例数据在 [sample_instrument_export.csv](sample_instrument_export.csv)，有 10 列，只选 time_s、temperature_C、pressure_kPa 这三列绘图。

在 GUI 中选：

| CSV 列 | 用途 |
| --- | --- |
| time_s | X |
| temperature_C | 左 Y |
| pressure_kPa | 右 Y |
| 其他 7 列 | 忽略 |

只画一条曲线时，也可以只选 time_s → X、temperature_C → 左 Y，并把右 Y 留空。左右 Y 各可选任意多列，总共至少一列。

若不想打开 GUI，修改 [plot_config.json](plot_config.json)：

~~~json
{
  "data_file": "sample_instrument_export.csv",
  "encoding": "utf-8-sig",
  "x": "time_s",
  "left_y": ["temperature_C"],
  "right_y": ["pressure_kPa"],
  "kind": "line+symbol",
  "output_project": "instrument_plot.opju",
  "export_png": false
}
~~~

kind 可填 scatter、line 或 line+symbol。左右 Y 可以用 [] 表示不选；两边不可同时为空。encoding 可按仪器 CSV 改为 gb18030。
默认不导出 PNG；将 export_png 改为 true 才会在工程旁生成同名预览图。如需单独指定图片位置，再添加 output_png 路径。
