"""Standalone CSV/TXT column picker that generates an Origin .opju project."""

import csv
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from plot_dual_y_origin import load_config, read_selected, run_external
from table_text import read_headers


class PlotPicker:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV/TXT → Origin 工程")
        self.root.geometry("840x650")
        self.root.minsize(680, 500)
        self.result = None
        self.column_choices = {}
        self.x_column = None

        try:
            default = load_config()
        except (OSError, ValueError) as exc:
            messagebox.showerror("配置错误", str(exc), parent=root)
            default = {}
        self.file_var = tk.StringVar(value=str(default.get("data_file", "")))
        self.output_var = tk.StringVar(value=str(default.get("output_project", "")))
        self.encoding_var = tk.StringVar(value=default.get("encoding", "utf-8-sig"))
        self.kind_var = tk.StringVar(value=default.get("kind", "line+symbol"))
        self.export_png_var = tk.BooleanVar(value=default.get("export_png", False))
        self.status_var = tk.StringVar(value="选择 CSV 或 TXT，再指定一个 X 列和至少一个 Y 列。")

        self._build_ui()
        if self.file_var.get():
            self.load_columns(default, show_error=False)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="CSV/TXT 数据生成 Origin 工程", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w")
        ttk.Label(outer, text="只画你选中的列；左右 Y 轴可各选 0 列或多列。", foreground="#555555").pack(anchor="w", pady=(3, 12))

        file_row = ttk.Frame(outer)
        file_row.pack(fill="x", pady=3)
        ttk.Label(file_row, text="数据文件", width=10).pack(side="left")
        ttk.Entry(file_row, textvariable=self.file_var).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(file_row, text="选择文件…", command=self.choose_file).pack(side="left", padx=(0, 5))
        ttk.Button(file_row, text="读取列", command=self.load_columns).pack(side="left")

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(8, 8))
        ttk.Label(options, text="编码", width=10).pack(side="left")
        encoding = ttk.Combobox(options, textvariable=self.encoding_var, width=15, state="readonly")
        encoding["values"] = ("utf-8-sig", "gb18030")
        encoding.pack(side="left", padx=(5, 18))
        encoding.bind("<<ComboboxSelected>>", lambda event: self.load_columns())
        ttk.Label(options, text="图形").pack(side="left")
        kind = ttk.Combobox(options, textvariable=self.kind_var, width=17, state="readonly")
        kind["values"] = ("scatter", "line", "line+symbol")
        kind.pack(side="left", padx=5)

        ttk.Label(outer, text="每列点一个用途；只要至少选择一个 Y，就能画图。", foreground="#555555").pack(anchor="w", pady=(4, 5))
        table_box = ttk.Frame(outer)
        table_box.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(table_box, borderwidth=0, highlightthickness=1, highlightbackground="#cccccc")
        scrollbar = ttk.Scrollbar(table_box, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.columns_frame = ttk.Frame(self.canvas, padding=5)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.columns_frame, anchor="nw")
        self.columns_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=event.width))
        self.canvas.bind("<MouseWheel>", self._mouse_wheel)

        output_row = ttk.Frame(outer)
        output_row.pack(fill="x", pady=(10, 4))
        ttk.Label(output_row, text="工程 OPJU", width=10).pack(side="left")
        ttk.Entry(output_row, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(output_row, text="保存位置…", command=self.choose_output).pack(side="left")

        ttk.Checkbutton(outer, text="同时导出 PNG 预览图", variable=self.export_png_var).pack(anchor="w", pady=(4, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Label(actions, textvariable=self.status_var, foreground="#444444").pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="取消", command=self.root.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(actions, text="生成工程", command=self.confirm).pack(side="right")

    def _mouse_wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def choose_file(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="选择仪器导出的 CSV 或 TXT",
            filetypes=[("表格数据", "*.csv *.txt"), ("CSV 数据", "*.csv"), ("TXT 数据", "*.txt"), ("所有文件", "*.*")],
        )
        if path:
            self.file_var.set(path)
            self.output_var.set(str(Path(path).with_name(Path(path).stem + "_plot.opju")))
            self.load_columns()

    def choose_output(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="保存 Origin 工程", defaultextension=".opju",
            filetypes=[("Origin 工程", "*.opju")], initialfile=Path(self.output_var.get()).name or "plot.opju",
        )
        if path:
            self.output_var.set(path)

    def load_columns(self, preselect=None, show_error=True):
        path = Path(self.file_var.get()).expanduser()
        try:
            headers = read_headers(path, self.encoding_var.get())
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            self.status_var.set("读取列失败。")
            if show_error:
                messagebox.showerror("无法读取数据文件", str(exc), parent=self.root)
            return

        for child in self.columns_frame.winfo_children():
            child.destroy()
        self.column_choices.clear()
        self.x_column = None
        headings = ("数据列名", "忽略", "X", "左 Y", "右 Y")
        for col, label in enumerate(headings):
            ttk.Label(self.columns_frame, text=label, font=("Microsoft YaHei UI", 9, "bold")).grid(
                row=0, column=col, sticky="w" if col == 0 else "", padx=8, pady=5
            )
        self.columns_frame.columnconfigure(0, weight=1)
        for row, name in enumerate(headers, start=1):
            selected = "ignore"
            if preselect:
                if name == preselect.get("x"):
                    selected = "x"
                    self.x_column = name
                elif name in preselect.get("left_y", []):
                    selected = "left"
                elif name in preselect.get("right_y", []):
                    selected = "right"
            choice = tk.StringVar(value=selected)
            self.column_choices[name] = choice
            ttk.Label(self.columns_frame, text=name).grid(row=row, column=0, sticky="w", padx=8, pady=2)
            for col, value in enumerate(("ignore", "x", "left", "right"), start=1):
                ttk.Radiobutton(
                    self.columns_frame, variable=choice, value=value,
                    command=lambda column=name, role=value: self._set_role(column, role),
                ).grid(row=row, column=col, padx=8, pady=2)
        self.canvas.yview_moveto(0)
        self.status_var.set(f"已读取 {len(headers)} 列；请选择一个 X 和至少一个 Y。")

    def _set_role(self, column, role):
        if role == "x":
            if self.x_column and self.x_column != column and self.x_column in self.column_choices:
                self.column_choices[self.x_column].set("ignore")
            self.x_column = column
        elif self.x_column == column:
            self.x_column = None

    def confirm(self):
        selected = {name: choice.get() for name, choice in self.column_choices.items()}
        x_columns = [name for name, role in selected.items() if role == "x"]
        left = [name for name, role in selected.items() if role == "left"]
        right = [name for name, role in selected.items() if role == "right"]
        if len(x_columns) != 1 or not (left or right):
            messagebox.showwarning("请完成选列", "需要恰好一个 X，且左 Y 或右 Y 至少一列。", parent=self.root)
            return
        output_text = self.output_var.get().strip()
        if not output_text or Path(output_text).suffix.lower() != ".opju":
            messagebox.showwarning("工程位置", "请输入以 .opju 结尾的工程路径。", parent=self.root)
            return
        project_path = Path(output_text).expanduser().resolve()
        export_png = self.export_png_var.get()
        png_path = project_path.with_suffix(".png") if export_png else None
        output_paths = (project_path, png_path) if png_path else (project_path,)
        existing = [path.name for path in output_paths if path.exists()]
        overwrite = bool(existing)
        if existing and not messagebox.askyesno(
            "确认覆盖", "以下文件已存在，是否覆盖？\n" + "\n".join(existing), parent=self.root
        ):
            return
        config = {
            "data_file": Path(self.file_var.get()).expanduser().resolve(),
            "encoding": self.encoding_var.get(),
            "x": x_columns[0],
            "left_y": left,
            "right_y": right,
            "kind": self.kind_var.get(),
            "output_project": project_path,
            "export_png": export_png,
        }
        if png_path:
            config["output_png"] = png_path
        try:
            values = read_selected(config)
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            messagebox.showerror("数据检查失败", str(exc), parent=self.root)
            return
        self.result = (config, values, overwrite)
        self.root.destroy()


def main():
    root = tk.Tk()
    picker = PlotPicker(root)
    root.mainloop()
    if picker.result is None:
        return
    try:
        config, values, overwrite = picker.result
        project_path, png_path = run_external(config, values, overwrite=overwrite)
    except Exception as exc:
        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror("工程生成失败", str(exc), parent=error_root)
        error_root.destroy()
        raise
    success_root = tk.Tk()
    success_root.withdraw()
    success_text = f"Origin 工程：\n{project_path}"
    if png_path:
        success_text += f"\n\n预览 PNG：\n{png_path}"
    messagebox.showinfo("生成完成", success_text, parent=success_root)
    success_root.destroy()


if __name__ == "__main__":
    main()
