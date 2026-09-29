"""Pick spectrum and electrical files, devices, plot groups, and columns."""

import csv
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from device_workflow import prepare_workflow, run_workflow
from merge_devices import infer_device_name
from table_text import read_headers


class FilePanel:
    def __init__(self, parent, label, kind, changed):
        self.kind = kind
        self.changed = changed
        self.entries = []
        box = ttk.LabelFrame(parent, text=label, padding=6)
        box.pack(fill="both", expand=True, pady=4)
        actions = ttk.Frame(box)
        actions.pack(fill="x")
        ttk.Button(actions, text=f"添加{label}…", command=self.add_files).pack(side="left")
        ttk.Label(actions, text="同名图组叠加；不同名图组分开画。器件名用于配对。", foreground="#555555").pack(side="left", padx=12)
        canvas = tk.Canvas(box, height=140, highlightthickness=0)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.rows = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        self.redraw()

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title=f"选择{self.kind}数据文件（可多选）",
            filetypes=[("表格数据", "*.txt *.csv"), ("所有文件", "*.*")],
        )
        for value in paths:
            path = Path(value).resolve()
            if any(entry["path"] == path for entry in self.entries):
                continue
            device = infer_device_name(path)
            group = f"{device} 光谱" if self.kind == "光谱" else "电学对比"
            self.entries.append({"path": path, "device_var": tk.StringVar(value=device), "group_var": tk.StringVar(value=group)})
        if paths:
            self.redraw()
            self.changed()

    def remove(self, entry):
        self.entries.remove(entry)
        self.redraw()
        self.changed()

    def redraw(self):
        for child in self.rows.winfo_children():
            child.destroy()
        for column, label in enumerate(("数据文件", "器件名（可修改）", "图组名（可修改）", "")):
            ttk.Label(self.rows, text=label).grid(row=0, column=column, sticky="w", padx=5)
        self.rows.columnconfigure(0, weight=1)
        for row, entry in enumerate(self.entries, start=1):
            ttk.Label(self.rows, text=entry["path"].name).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Entry(self.rows, textvariable=entry["device_var"], width=24).grid(row=row, column=1, padx=5, pady=2)
            ttk.Entry(self.rows, textvariable=entry["group_var"], width=24).grid(row=row, column=2, padx=5, pady=2)
            ttk.Button(self.rows, text="移除", command=lambda item=entry: self.remove(item)).grid(row=row, column=3, padx=5, pady=2)

    def values(self):
        return [{"path": entry["path"], "device": entry["device_var"].get(), "plot_group": entry["group_var"].get()} for entry in self.entries]


class ColumnPanel:
    def __init__(self, parent, label):
        box = ttk.LabelFrame(parent, text=f"{label}选列", padding=6)
        box.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(box, text="一个 X；左 Y、右 Y 至少选一列").pack(anchor="w")
        canvas = tk.Canvas(box, height=230, highlightthickness=0)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.rows = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.rows.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        self.choices = {}
        self.label = label

    def load(self, paths, encoding):
        for child in self.rows.winfo_children():
            child.destroy()
        previous = {name: var.get() for name, var in self.choices.items()}
        self.choices = {}
        if not paths:
            ttk.Label(self.rows, text="添加文件后显示共同列名。", foreground="#555555").pack(anchor="w")
            return
        headers = read_headers(paths[0], encoding)
        common = set(headers)
        for path in paths[1:]:
            common.intersection_update(read_headers(path, encoding))
        headers = [name for name in headers if name in common]
        if not headers:
            raise ValueError(f"{self.label}文件没有共同列名；请检查文件分类。")
        for column, label in enumerate(("数据列", "忽略", "X", "左 Y", "右 Y")):
            ttk.Label(self.rows, text=label).grid(row=0, column=column, padx=5, sticky="w")
        self.rows.columnconfigure(0, weight=1)
        default_x = "Wavelength(nm)" if self.label == "光谱" else "Voltage(V)"
        default_left = "Current density(mA/cm2)" if self.label == "电学" else (headers[1] if len(headers) > 1 else "")
        default_right = "Luminance(cd/m2)" if self.label == "电学" else ""
        for row, name in enumerate(headers, start=1):
            role = previous.get(name)
            if role is None:
                role = "x" if name == default_x else "left" if name == default_left else "right" if name == default_right else "ignore"
            variable = tk.StringVar(value=role)
            self.choices[name] = variable
            ttk.Label(self.rows, text=name).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            for column, value in enumerate(("ignore", "x", "left", "right"), start=1):
                ttk.Radiobutton(self.rows, variable=variable, value=value, command=lambda key=name, chosen=value: self.set_role(key, chosen)).grid(row=row, column=column, padx=5)

    def set_role(self, name, role):
        if role == "x":
            for other, variable in self.choices.items():
                if other != name and variable.get() == "x":
                    variable.set("ignore")

    def config(self):
        roles = {name: variable.get() for name, variable in self.choices.items()}
        x = [name for name, role in roles.items() if role == "x"]
        left = [name for name, role in roles.items() if role == "left"]
        right = [name for name, role in roles.items() if role == "right"]
        if len(x) != 1 or not (left or right):
            raise ValueError(f"{self.label}需要一个 X 和至少一个 Y。")
        return {"x": x[0], "left_y": left, "right_y": right, "kind": "line"}


class DevicePicker:
    def __init__(self, root):
        self.root = root
        root.title("器件光谱与电学数据 → Origin 工程")
        root.geometry("1130x900")
        root.minsize(900, 680)
        self.result = None
        self.encoding_var = tk.StringVar(value="utf-8-sig")
        self.output_var = tk.StringVar(value=str(TOOL_DIR.parent / "outputs" / "device_plots.opju"))
        self.status_var = tk.StringVar(value="添加文件；相同图组叠加，不同图组分别出图。")
        outer = ttk.Frame(root, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="器件光谱与电学数据", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="文件名自动推断器件；可手动修改。光谱默认每器件一图，电学默认叠加；图组可逐文件调整。", foreground="#555555").pack(anchor="w", pady=(2, 8))
        self.spectra = FilePanel(outer, "光谱", "光谱", self.refresh)
        self.electrical = FilePanel(outer, "电学", "电学", self.refresh)
        row = ttk.Frame(outer)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text="文件编码").pack(side="left")
        combo = ttk.Combobox(row, textvariable=self.encoding_var, values=("utf-8-sig", "gb18030"), width=12, state="readonly")
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Label(row, text="电学文件会合到同一张工作表；光谱各自保留数据表。", foreground="#555555").pack(side="left", padx=12)
        columns = ttk.Frame(outer)
        columns.pack(fill="both", expand=True)
        self.spectrum_columns = ColumnPanel(columns, "光谱")
        self.electrical_columns = ColumnPanel(columns, "电学")
        self.refresh()
        output = ttk.Frame(outer)
        output.pack(fill="x", pady=8)
        ttk.Label(output, text="工程 OPJU").pack(side="left")
        ttk.Entry(output, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(output, text="保存位置…", command=self.choose_output).pack(side="left")
        actions = ttk.Frame(outer)
        actions.pack(fill="x")
        ttk.Label(actions, textvariable=self.status_var).pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="取消", command=root.destroy).pack(side="right", padx=5)
        ttk.Button(actions, text="生成工程", command=self.confirm).pack(side="right")

    def refresh(self):
        try:
            self.spectrum_columns.load([entry["path"] for entry in self.spectra.entries], self.encoding_var.get())
            self.electrical_columns.load([entry["path"] for entry in self.electrical.entries], self.encoding_var.get())
            self.status_var.set(f"已添加 {len(self.spectra.entries)} 份光谱、{len(self.electrical.entries)} 份电学文件。")
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            self.status_var.set("读取列名失败；可检查文件分类或编码。")
            messagebox.showerror("无法识别表头", str(exc), parent=self.root)

    def choose_output(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="保存 Origin 工程", defaultextension=".opju", filetypes=[("Origin 工程", "*.opju")])
        if path:
            self.output_var.set(path)

    def confirm(self):
        spectrum_entries = self.spectra.values()
        electrical_entries = self.electrical.values()
        if not spectrum_entries and not electrical_entries:
            messagebox.showwarning("数据文件", "请至少添加一份光谱或电学文件。", parent=self.root)
            return
        output = Path(self.output_var.get()).expanduser().resolve()
        if output.suffix.lower() != ".opju":
            messagebox.showwarning("工程位置", "请输入以 .opju 结尾的工程路径。", parent=self.root)
            return
        try:
            spectrum_config = self.spectrum_columns.config() if spectrum_entries else {}
            electrical_config = self.electrical_columns.config() if electrical_entries else {}
            prepared = prepare_workflow(spectrum_entries, electrical_entries, spectrum_config, electrical_config, self.encoding_var.get())
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            messagebox.showerror("数据检查失败", str(exc), parent=self.root)
            return
        overwrite = output.exists()
        if overwrite and not messagebox.askyesno("确认覆盖", f"工程已存在，是否覆盖？\n{output}", parent=self.root):
            return
        self.result = (prepared, output, overwrite)
        self.root.destroy()


def main():
    root = tk.Tk()
    picker = DevicePicker(root)
    root.mainloop()
    if picker.result is None:
        return
    try:
        result = run_workflow(*picker.result)
    except Exception as exc:
        dialog = tk.Tk()
        dialog.withdraw()
        messagebox.showerror("工程生成失败", str(exc), parent=dialog)
        dialog.destroy()
        raise
    dialog = tk.Tk()
    dialog.withdraw()
    messagebox.showinfo("生成完成", f"Origin 工程：\n{result}", parent=dialog)
    dialog.destroy()


if __name__ == "__main__":
    main()
