# Origin 画图速查（第一次使用）

目标：把 `sample_measurements.csv` 的 **时间**画在横轴、**温度**画在纵轴。

1. **导入数据**：打开 Origin，点顶部菜单 **Data → Connect to File → Text/CSV**，选 `F:\Project\Origin_tool\sample_measurements.csv`，确认导入选项。看到四列数字的表格就算成功。
2. **指定横轴**：在表格里，右键 `time_s` 所在的整列列头（A 列），选 **Set As → X**。列头应显示 `A(X)`。
3. **指定纵轴**：右键 `temperature_C` 所在的整列列头（C 列），选 **Set As → Y**。列头应显示 `C(Y)`。
4. **出图**：单击 `temperature_C` 的列头，选顶部菜单 **Plot → Basic 2D → Scatter**。会弹出一个散点图窗口。

**想换 X/Y：**回到表格，右键新列的列头并分别设为 **X**、**Y**，再单击 Y 列列头画图。第一次建议先完成上面四步；例如下一次可试 `voltage_V`（B 列）对 `pressure_kPa`（D 列）。

**如果横轴显示为 1、2、3……：**通常是 X 列没有指定成功；回表格检查列头是否显示 `(X)`，重新选中 Y 列画图。

**想试自动绘图：**在 Origin 的 **Window → Script Window** 输入并回车：

```text
run -pyf "F:\Project\Origin_tool\plot_csv_origin.py";
```

脚本默认画相同的时间—温度散点图，并导出 `F:\Project\Origin_tool\origin_test_plot.png`。如需改列，编辑脚本开头的 `DEFAULT_X` 和 `DEFAULT_Y`。
