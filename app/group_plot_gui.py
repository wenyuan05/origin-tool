"""Simple file groups with an overlay switch per group."""

import csv
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from group_workflow import prepare_groups, run_groups
from table_text import read_headers


class GroupPicker:
    def __init__(self, root):
        self.root = root
        root.title("文件分组 → Origin 工程")
        root.geometry("1050x760")
        root.minsize(800, 580)
        self.groups = []
        self.active = None
        self.column_vars = {}
        self.result = None
        self.encoding = tk.StringVar(value="utf-8-sig")
        self.output = tk.StringVar(value=str(TOOL_DIR.parent / "outputs" / "grouped_plot.opju"))
        self.status = tk.StringVar(value="创建分组并添加文件。")
        self._build_ui()
        self.add_group()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="按文件分组绘图", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="每组独立选列；勾选“组内叠加”会把该组文件画在同一张图。", foreground="#555555").pack(anchor="w", pady=(2, 8))
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        side = ttk.Frame(body, width=200)
        side.pack(side="left", fill="y", padx=(0, 10))
        ttk.Label(side, text="文件分组").pack(anchor="w")
        self.group_list = tk.Listbox(side, width=25, exportselection=False)
        self.group_list.pack(fill="both", expand=True, pady=5)
        self.group_list.bind("<<ListboxSelect>>", self.select_group)
        ttk.Button(side, text="添加分组", command=self.add_group).pack(fill="x")
        ttk.Button(side, text="删除选中分组", command=self.remove_group).pack(fill="x", pady=4)

        detail = ttk.Frame(body)
        detail.pack(side="left", fill="both", expand=True)
        row = ttk.Frame(detail)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="分组名").pack(side="left")
        self.name_entry = ttk.Entry(row, width=34)
        self.name_entry.pack(side="left", padx=6, fill="x", expand=True)
        self.overlay_check = ttk.Checkbutton(row, text="组内叠加")
        self.overlay_check.pack(side="left", padx=8)
        ttk.Label(row, text="图形").pack(side="left")
        self.kind_combo = ttk.Combobox(row, values=("line", "scatter", "line+symbol"), width=14, state="readonly")
        self.kind_combo.pack(side="left", padx=6)

        files_box = ttk.LabelFrame(detail, text="本组文件", padding=6)
        files_box.pack(fill="x", pady=5)
        self.file_list = tk.Listbox(files_box, height=5, exportselection=False)
        self.file_list.pack(side="left", fill="x", expand=True)
        file_actions = ttk.Frame(files_box)
        file_actions.pack(side="left", padx=6)
        ttk.Button(file_actions, text="添加文件…", command=self.add_files).pack(fill="x")
        ttk.Button(file_actions, text="移除选中", command=self.remove_file).pack(fill="x", pady=5)

        options = ttk.Frame(detail)
        options.pack(fill="x", pady=5)
        ttk.Label(options, text="文件编码").pack(side="left")
        encoding_combo = ttk.Combobox(options, textvariable=self.encoding, values=("utf-8-sig", "gb18030"), width=13, state="readonly")
        encoding_combo.pack(side="left", padx=6)
        encoding_combo.bind("<<ComboboxSelected>>", lambda event: self.refresh_columns())
        ttk.Label(options, text="一个 X；左 Y 和右 Y 至少选一列。", foreground="#555555").pack(side="left", padx=10)

        columns_box = ttk.LabelFrame(detail, text="本组选列", padding=6)
        columns_box.pack(fill="both", expand=True)
        canvas = tk.Canvas(columns_box, highlightthickness=0)
        scrollbar = ttk.Scrollbar(columns_box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.columns_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.columns_frame, anchor="nw")
        self.columns_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(canvas_window, width=event.width))

        output_row = ttk.Frame(outer)
        output_row.pack(fill="x", pady=(10, 5))
        ttk.Label(output_row, text="工程 OPJU").pack(side="left")
        ttk.Entry(output_row, textvariable=self.output).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(output_row, text="保存位置…", command=self.choose_output).pack(side="left")
        actions = ttk.Frame(outer)
        actions.pack(fill="x")
        ttk.Label(actions, textvariable=self.status).pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="取消", command=self.root.destroy).pack(side="right", padx=5)
        ttk.Button(actions, text="生成工程", command=self.confirm).pack(side="right")

    def add_group(self):
        self.save_roles()
        name = tk.StringVar(value=f"分组 {len(self.groups) + 1}")
        group = {"name": name, "overlay": tk.BooleanVar(value=True), "kind": tk.StringVar(value="line"), "files": [], "roles": {}}
        name.trace_add("write", lambda *_: self.update_group_names())
        self.groups.append(group)
        self.update_group_names()
        self.group_list.selection_clear(0, "end")
        self.group_list.selection_set(len(self.groups) - 1)
        self.show_group(len(self.groups) - 1)

    def remove_group(self):
        if self.active is None:
            return
        index = self.active
        self.groups.pop(index)
        self.active = None
        self.update_group_names()
        if self.groups:
            next_index = min(index, len(self.groups) - 1)
            self.group_list.selection_set(next_index)
            self.show_group(next_index)
        else:
            self.name_entry.configure(textvariable=tk.StringVar())
            self.file_list.delete(0, "end")
            self.clear_columns()

    def update_group_names(self):
        selected = self.group_list.curselection()
        self.group_list.delete(0, "end")
        for group in self.groups:
            self.group_list.insert("end", group["name"].get() or "（未命名）")
        if selected and selected[0] < len(self.groups):
            self.group_list.selection_set(selected[0])

    def select_group(self, _event):
        selection = self.group_list.curselection()
        if selection and selection[0] != self.active:
            self.save_roles()
            self.show_group(selection[0])

    def show_group(self, index):
        self.active = index
        group = self.groups[index]
        self.name_entry.configure(textvariable=group["name"])
        self.overlay_check.configure(variable=group["overlay"])
        self.kind_combo.configure(textvariable=group["kind"])
        self.refresh_files()
        self.refresh_columns(preserve_current=False)

    def refresh_files(self):
        self.file_list.delete(0, "end")
        if self.active is not None:
            for path in self.groups[self.active]["files"]:
                self.file_list.insert("end", str(path))

    def add_files(self):
        if self.active is None:
            self.add_group()
        paths = filedialog.askopenfilenames(parent=self.root, title="添加本组数据文件（可多选）",
                                             filetypes=[("表格数据", "*.csv *.txt"), ("所有文件", "*.*")])
        if not paths:
            return
        group = self.groups[self.active]
        existing = {path for item in self.groups for path in item["files"]}
        for path_text in paths:
            path = Path(path_text).resolve()
            if path in existing:
                messagebox.showwarning("文件重复", f"文件已在某个分组中：\n{path}", parent=self.root)
                continue
            group["files"].append(path)
            existing.add(path)
        self.refresh_files()
        self.refresh_columns()

    def remove_file(self):
        selected = self.file_list.curselection()
        if self.active is None or not selected:
            return
        self.save_roles()
        self.groups[self.active]["files"].pop(selected[0])
        self.refresh_files()
        self.refresh_columns()

    def save_roles(self):
        if self.active is not None:
            self.groups[self.active]["roles"] = {name: var.get() for name, var in self.column_vars.items()}

    def clear_columns(self):
        for child in self.columns_frame.winfo_children():
            child.destroy()
        self.column_vars = {}

    def refresh_columns(self, preserve_current=True):
        if preserve_current:
            self.save_roles()
        self.clear_columns()
        if self.active is None:
            return
        group = self.groups[self.active]
        paths = group["files"]
        if not paths:
            ttk.Label(self.columns_frame, text="添加文件后显示列名。", foreground="#555555").pack(anchor="w")
            return
        try:
            headers = read_headers(paths[0], self.encoding.get())
            shared = set(headers)
            for path in paths[1:]:
                shared.intersection_update(read_headers(path, self.encoding.get()))
            headers = [name for name in headers if name in shared]
            if not headers:
                raise ValueError("本组文件没有共同列名。请把不同格式文件放进不同分组。")
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            self.status.set("读取列名失败。")
            messagebox.showerror("无法识别表头", str(exc), parent=self.root)
            return
        for column, label in enumerate(("数据列", "忽略", "X", "左 Y", "右 Y")):
            ttk.Label(self.columns_frame, text=label).grid(row=0, column=column, padx=6, sticky="w")
        self.columns_frame.columnconfigure(0, weight=1)
        default_x = next((name for name in headers if name.lower().startswith(("wavelength", "voltage", "time"))), headers[0])
        default_y = next((name for name in headers if name != default_x), "")
        for row, name in enumerate(headers, start=1):
            role = group["roles"].get(name, "x" if name == default_x else "left" if name == default_y else "ignore")
            variable = tk.StringVar(value=role)
            self.column_vars[name] = variable
            ttk.Label(self.columns_frame, text=name).grid(row=row, column=0, sticky="w", padx=6, pady=2)
            for column, value in enumerate(("ignore", "x", "left", "right"), start=1):
                ttk.Radiobutton(self.columns_frame, variable=variable, value=value,
                                command=lambda key=name, chosen=value: self.set_role(key, chosen)).grid(row=row, column=column, padx=6)
        self.status.set(f"{group['name'].get()}：{len(paths)} 个文件、{len(headers)} 个共同列。")

    def set_role(self, name, role):
        if role == "x":
            for other, variable in self.column_vars.items():
                if other != name and variable.get() == "x":
                    variable.set("ignore")

    def choose_output(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="保存 Origin 工程", defaultextension=".opju",
                                            filetypes=[("Origin 工程", "*.opju")])
        if path:
            self.output.set(path)

    def confirm(self):
        self.save_roles()
        raw_groups = []
        for item in self.groups:
            roles = item["roles"]
            x = [name for name, role in roles.items() if role == "x"]
            left = [name for name, role in roles.items() if role == "left"]
            right = [name for name, role in roles.items() if role == "right"]
            if len(x) != 1 or not (left or right):
                messagebox.showwarning("请完成选列", f"{item['name'].get()} 需要一个 X 和至少一个 Y。", parent=self.root)
                return
            raw_groups.append({"name": item["name"].get(), "overlay": item["overlay"].get(), "kind": item["kind"].get(),
                               "files": item["files"].copy(), "x": x[0], "left_y": left, "right_y": right})
        output = Path(self.output.get()).expanduser().resolve()
        try:
            prepared = prepare_groups(raw_groups, self.encoding.get())
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            messagebox.showerror("数据检查失败", str(exc), parent=self.root)
            return
        if output.suffix.lower() != ".opju":
            messagebox.showwarning("工程位置", "请输入以 .opju 结尾的工程路径。", parent=self.root)
            return
        overwrite = output.exists()
        if overwrite and not messagebox.askyesno("确认覆盖", f"工程已存在，是否覆盖？\n{output}", parent=self.root):
            return
        self.result = (prepared, output, overwrite)
        self.root.destroy()


def main():
    root = tk.Tk()
    picker = GroupPicker(root)
    root.mainloop()
    if picker.result is None:
        return
    try:
        output = run_groups(*picker.result)
    except Exception as exc:
        dialog = tk.Tk()
        dialog.withdraw()
        messagebox.showerror("工程生成失败", str(exc), parent=dialog)
        dialog.destroy()
        raise
    dialog = tk.Tk()
    dialog.withdraw()
    messagebox.showinfo("生成完成", f"Origin 工程：\n{output}", parent=dialog)
    dialog.destroy()


if __name__ == "__main__":
    main()
