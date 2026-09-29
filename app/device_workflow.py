"""Build one Origin project with per-device spectra and merged electrical data."""

import csv
import json
import math
from pathlib import Path

from merge_devices import infer_device_name, read_full_table
from plot_dual_y_origin import plot, read_selected, selected_columns


COLORS = ("#2463A7", "#D05B2C", "#1B8A92", "#B38A19", "#624AA0", "#BB3F68")


def normalize_entries(entries, kind):
    normalized = []
    seen = set()
    for entry in entries:
        path = Path(entry["path"]).expanduser().resolve()
        if path in seen:
            raise ValueError(f"同一类型的数据文件重复：{path}")
        seen.add(path)
        device = str(entry.get("device") or infer_device_name(path)).strip()
        if not device:
            raise ValueError(f"{path.name} 的器件名不能为空。")
        default_group = f"{device} 光谱" if kind == "spectrum" else "电学对比"
        plot_group = str(entry.get("plot_group") or default_group).strip()
        if not plot_group:
            raise ValueError(f"{path.name} 的图组名不能为空。")
        normalized.append({"path": path, "device": device, "plot_group": plot_group})
    return normalized


def prepare_workflow(spectrum_entries, electrical_entries, spectrum_config, electrical_config, encoding="utf-8-sig"):
    """Parse and validate both file types before starting Origin."""
    spectrum_entries = normalize_entries(spectrum_entries, "spectrum")
    electrical_entries = normalize_entries(electrical_entries, "electrical")
    if not spectrum_entries and not electrical_entries:
        raise ValueError("至少添加一份光谱或电学文件。")
    if {item["path"] for item in spectrum_entries} & {item["path"] for item in electrical_entries}:
        raise ValueError("同一个文件不能同时归入光谱和电学。")
    spectra = []
    if spectrum_entries:
        selected_columns(spectrum_config)
        for entry in spectrum_entries:
            path = entry["path"]
            try:
                config = {**spectrum_config, "data_file": path, "encoding": encoding}
                values = read_selected(config)
                _, _, metadata = read_full_table(path, encoding)
            except (OSError, UnicodeError, ValueError, csv.Error) as exc:
                raise ValueError(f"光谱 {path.name}：{exc}") from exc
            spectra.append({**entry, "name": path.name, "values": values, "metadata": metadata})
    electrical = []
    if electrical_entries:
        selected_columns(electrical_config)
        names = selected_columns(electrical_config)
        for entry in electrical_entries:
            path = entry["path"]
            try:
                headers, columns, metadata = read_full_table(path, encoding)
            except (OSError, UnicodeError, ValueError, csv.Error) as exc:
                raise ValueError(f"电学 {path.name}：{exc}") from exc
            missing = [name for name in names if name not in headers]
            if missing:
                raise ValueError(f"电学 {path.name} 缺少列：{missing}")
            for name in names:
                column = columns[headers.index(name)]
                if not all(isinstance(value, float) for value in column):
                    raise ValueError(f"电学 {path.name} 的 {name} 含非数字。")
                if name == electrical_config["x"] and not all(math.isfinite(value) for value in column):
                    raise ValueError(f"电学 {path.name} 的 X 列 {name} 不能有空值或 NaN。")
                if name != electrical_config["x"] and sum(math.isfinite(value) for value in column) < 2:
                    raise ValueError(f"电学 {path.name} 的 Y 列 {name} 至少需要两个有效数值。")
            electrical.append({**entry, "name": path.name, "headers": headers, "columns": columns, "metadata": metadata})
    return {"spectra": spectra, "electrical": electrical, "spectrum_config": spectrum_config, "electrical_config": electrical_config}


def add_electrical_sheet(op, electrical):
    """Place all devices side by side; each device retains its own row positions."""
    sheet = op.find_sheet() or op.new_sheet()
    if sheet is None:
        raise RuntimeError("Origin 未能创建电学合并工作表。")
    sheet.get_book().lname = "电学数据合并"
    mappings = []
    column_index = 0
    for source in electrical:
        start = column_index
        for header, values in zip(source["headers"], source["columns"]):
            sheet.from_list(column_index, values, lname=f"{source['device']} | {header}", comments=source["name"])
            column_index += 1
        mappings.append({"source": source, "indices": {name: start + i for i, name in enumerate(source["headers"])}})
    return sheet, mappings


def make_group_graph(op, sheet, mappings, config, title):
    graph = op.new_graph(template="scatter")
    graph.lname = title
    left_layer = graph[0]
    right_layer = graph.add_layer(2) if config["left_y"] and config["right_y"] else None
    if config["left_y"] and config["right_y"] and right_layer is None:
        raise RuntimeError("Origin 未能创建电学右 Y 轴图层。")
    plot_type = {"scatter": "s", "line": "l", "line+symbol": "y"}[config.get("kind", "line+symbol")]
    left_layer.axis("x").title = config["x"]
    legend_entries = []
    left_count = right_count = 0
    for device_index, item in enumerate(mappings):
        source, indices = item["source"], item["indices"]
        plot_sheet = item.get("sheet", sheet)
        x_index = indices[config["x"]]
        for name in config["left_y"]:
            left_count += 1
            curve = left_layer.add_plot(plot_sheet, coly=indices[name], colx=x_index, type=plot_type)
            curve.color = COLORS[device_index % len(COLORS)]
            legend_entries.append(f"\\l(1.{left_count}) {source['device']} — {name} (左 Y)")
        for name in config["right_y"]:
            layer = right_layer or left_layer
            right_count += 1
            curve = layer.add_plot(plot_sheet, coly=indices[name], colx=x_index, type=plot_type)
            curve.color = COLORS[device_index % len(COLORS)]
            layer_number = 2 if right_layer else 1
            plot_number = right_count if right_layer else left_count + right_count
            legend_entries.append(f"\\l({layer_number}.{plot_number}) {source['device']} — {name} (右 Y)")
    if config["left_y"]:
        left_layer.axis("y").title = ", ".join(config["left_y"])
    if config["right_y"]:
        if not right_layer:
            left_layer.set_int("y.showAxes", 2)
            left_layer.set_int("y.showLabels", 2)
        (right_layer or left_layer).axis("y2").title = ", ".join(config["right_y"])
    left_layer.rescale()
    if right_layer:
        right_layer.rescale()
    legend = left_layer.label("Legend")
    if legend:
        legend.text = "\n".join(legend_entries)
    return graph


def run_workflow(prepared, output_project, overwrite=False, op=None):
    output_project = Path(output_project).expanduser().resolve()
    if output_project.suffix.lower() != ".opju":
        raise ValueError("输出工程必须以 .opju 结尾。")
    if output_project.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_project}")
    if op is None:
        import originpro as op
    if not getattr(op, "oext", False):
        raise RuntimeError("请从普通 Python 调用本机 Origin。")
    output_project.parent.mkdir(parents=True, exist_ok=True)
    try:
        op.set_show(False)
        op.new()
        notes = []
        spectrum_groups = {}
        for index, source in enumerate(prepared["spectra"]):
            sheet = (op.find_sheet() or op.new_sheet()) if index == 0 else op.new_sheet()
            if sheet is None:
                raise RuntimeError(f"Origin 未能创建光谱工作表：{source['name']}")
            sheet.get_book().lname = f"{source['device']} 光谱"
            names = [prepared["spectrum_config"]["x"], *prepared["spectrum_config"]["left_y"], *prepared["spectrum_config"]["right_y"]]
            for column_index, name in enumerate(names):
                sheet.from_list(column_index, source["values"][name], lname=name, axis="X" if column_index == 0 else "Y")
            spectrum_groups.setdefault(source["plot_group"], []).append({
                "source": source, "sheet": sheet, "indices": {name: i for i, name in enumerate(names)},
            })
            notes.extend([f"器件：{source['device']}；类型：光谱；文件：{source['name']}", *source["metadata"], ""])
        for group_name, mappings in spectrum_groups.items():
            if len(mappings) == 1:
                item = mappings[0]
                graph = plot(prepared["spectrum_config"], item["source"]["values"], op, worksheet=item["sheet"])
                graph.lname = group_name
            else:
                make_group_graph(op, None, mappings, prepared["spectrum_config"], group_name)
        if prepared["electrical"]:
            sheet, mappings = add_electrical_sheet(op, prepared["electrical"])
            electrical_groups = {}
            for item in mappings:
                electrical_groups.setdefault(item["source"]["plot_group"], []).append(item)
            for group_name, group_mappings in electrical_groups.items():
                make_group_graph(op, sheet, group_mappings, prepared["electrical_config"], group_name)
            for source in prepared["electrical"]:
                notes.extend([f"器件：{source['device']}；类型：电学；文件：{source['name']}", *source["metadata"], ""])
        note = op.new_notes("Source_Info")
        if note is None:
            raise RuntimeError("Origin 未能创建数据源信息便签。")
        note.text = "\n".join(notes)
        op.wait()
        if not op.save(str(output_project)) or not output_project.is_file() or output_project.stat().st_size == 0:
            raise RuntimeError("Origin 未能保存有效的 .opju 工程文件。")
    finally:
        op.exit()
    return output_project


def main():
    import argparse

    parser = argparse.ArgumentParser(description="按器件生成光谱图、电学合并表与电学图")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    spectra = [{"path": base / entry["path"], "device": entry.get("device"), "plot_group": entry.get("plot_group")} for entry in config.get("spectrum_files", [])]
    electrical = [{"path": base / entry["path"], "device": entry.get("device"), "plot_group": entry.get("plot_group")} for entry in config.get("electrical_files", [])]
    prepared = prepare_workflow(spectra, electrical, config.get("spectrum_plot", {}), config.get("electrical_plot", {}), config.get("encoding", "utf-8-sig"))
    print(f"检查通过：{len(prepared['spectra'])} 份光谱、{len(prepared['electrical'])} 份电学文件。")
    if not args.check_only:
        result = run_workflow(prepared, base / config["output_project"], args.overwrite)
        print(f"Origin 工程：{result}")


if __name__ == "__main__":
    main()
