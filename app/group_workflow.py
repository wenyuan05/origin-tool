"""Build an Origin project from configurable file groups."""

import argparse
import csv
import json
import math
from pathlib import Path

from plot_dual_y_origin import selected_columns
from table_text import read_full_table


COLORS = ("#2463A7", "#D05B2C", "#1B8A92", "#B38A19", "#624AA0", "#BB3F68")
KINDS = {"scatter": "s", "line": "l", "line+symbol": "y"}


def prepare_groups(groups, encoding="utf-8-sig"):
    """Validate every group and file before starting Origin."""
    if not isinstance(groups, list) or not groups:
        raise ValueError("至少创建一个文件分组。")
    prepared = []
    seen_files = set()
    seen_names = set()
    for group in groups:
        name = str(group.get("name", "")).strip()
        if not name or name in seen_names:
            raise ValueError("分组名必须非空且不重复。")
        seen_names.add(name)
        overlay = group.get("overlay", False)
        if not isinstance(overlay, bool):
            raise ValueError(f"{name} 的 overlay 必须是 true 或 false。")
        if group.get("kind", "line") not in KINDS:
            raise ValueError(f"{name} 的 kind 只能是 scatter、line 或 line+symbol。")
        names = selected_columns(group)
        paths = group.get("files")
        if not isinstance(paths, list) or not paths:
            raise ValueError(f"{name} 至少需要一个文件。")
        sources = []
        for raw_path in paths:
            path = Path(raw_path).expanduser().resolve()
            if path in seen_files:
                raise ValueError(f"文件不能重复加入分组：{path}")
            seen_files.add(path)
            try:
                headers, columns, metadata = read_full_table(path, encoding)
            except (OSError, UnicodeError, ValueError, csv.Error) as exc:
                raise ValueError(f"{name} / {path.name}：{exc}") from exc
            missing = [column for column in names if column not in headers]
            if missing:
                raise ValueError(f"{name} / {path.name} 缺少选定列：{missing}")
            for column_name in names:
                values = columns[headers.index(column_name)]
                if not all(isinstance(value, float) for value in values):
                    raise ValueError(f"{name} / {path.name} 的 {column_name} 含非数字。")
                if any(math.isinf(value) for value in values):
                    raise ValueError(f"{name} / {path.name} 的 {column_name} 包含无穷大。")
                if column_name == group["x"] and not all(math.isfinite(value) for value in values):
                    raise ValueError(f"{name} / {path.name} 的 X 列 {column_name} 不能有空值或 NaN。")
                if column_name != group["x"] and sum(math.isfinite(value) for value in values) < 2:
                    raise ValueError(f"{name} / {path.name} 的 Y 列 {column_name} 至少需要两个有效数值。")
            sources.append({"path": path, "headers": headers, "columns": columns, "metadata": metadata})
        prepared.append({"name": name, "overlay": overlay, "kind": group.get("kind", "line"),
                         "x": group["x"], "left_y": group["left_y"], "right_y": group["right_y"], "sources": sources})
    return prepared


def add_group_sheet(op, group, first):
    sheet = (op.find_sheet() or op.new_sheet()) if first else op.new_sheet()
    if sheet is None:
        raise RuntimeError(f"Origin 未能创建分组工作表：{group['name']}")
    sheet.get_book().lname = group["name"]
    mappings = []
    column_index = 0
    for source_index, source in enumerate(group["sources"], start=1):
        start = column_index
        source_label = f"{source_index}. {source['path'].name}"
        for header, values in zip(source["headers"], source["columns"]):
            sheet.from_list(column_index, values, lname=f"{source_label} | {header}", comments=source["path"].name)
            column_index += 1
        mappings.append({"label": source_label, "indices": {name: start + i for i, name in enumerate(source["headers"])}})
    return sheet, mappings


def plot_group(op, sheet, mappings, group, title):
    graph = op.new_graph(template="scatter")
    graph.lname = title
    left_layer = graph[0]
    right_layer = graph.add_layer(2) if group["left_y"] and group["right_y"] else None
    if group["left_y"] and group["right_y"] and right_layer is None:
        raise RuntimeError(f"Origin 未能创建 {title} 的右 Y 轴。")
    left_layer.axis("x").title = group["x"]
    left_count = right_count = 0
    legend_entries = []
    for source_index, mapping in enumerate(mappings):
        x_index = mapping["indices"][group["x"]]
        for name in group["left_y"]:
            left_count += 1
            curve = left_layer.add_plot(sheet, coly=mapping["indices"][name], colx=x_index, type=KINDS[group["kind"]])
            curve.color = COLORS[source_index % len(COLORS)]
            legend_entries.append(f"\\l(1.{left_count}) {mapping['label']} — {name} (左 Y)")
        for name in group["right_y"]:
            layer = right_layer or left_layer
            right_count += 1
            curve = layer.add_plot(sheet, coly=mapping["indices"][name], colx=x_index, type=KINDS[group["kind"]])
            curve.color = COLORS[source_index % len(COLORS)]
            layer_number = 2 if right_layer else 1
            plot_number = right_count if right_layer else left_count + right_count
            legend_entries.append(f"\\l({layer_number}.{plot_number}) {mapping['label']} — {name} (右 Y)")
    if group["left_y"]:
        left_layer.axis("y").title = ", ".join(group["left_y"])
    if group["right_y"]:
        if not right_layer:
            left_layer.set_int("y.showAxes", 2)
            left_layer.set_int("y.showLabels", 2)
        (right_layer or left_layer).axis("y2").title = ", ".join(group["right_y"])
    left_layer.rescale()
    if right_layer:
        right_layer.rescale()
    legend = left_layer.label("Legend")
    if legend:
        legend.text = "\n".join(legend_entries)
    return graph


def run_groups(groups, output_project, overwrite=False, op=None):
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
        for group_index, group in enumerate(groups):
            sheet, mappings = add_group_sheet(op, group, first=group_index == 0)
            if group["overlay"]:
                plot_group(op, sheet, mappings, group, group["name"])
            else:
                for mapping in mappings:
                    plot_group(op, sheet, [mapping], group, f"{group['name']} - {mapping['label']}")
            notes.append(f"分组：{group['name']}；组内叠加：{'是' if group['overlay'] else '否'}")
            for source in group["sources"]:
                notes.extend([f"  文件：{source['path'].name}", *[f"    {line}" for line in source["metadata"]]])
            notes.append("")
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
    parser = argparse.ArgumentParser(description="按文件分组生成 Origin 工程")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    base = config_path.parent
    raw_groups = []
    for group in config["groups"]:
        raw_groups.append({**group, "files": [base / path for path in group["files"]]})
    groups = prepare_groups(raw_groups, config.get("encoding", "utf-8-sig"))
    print("检查通过：" + "；".join(f"{group['name']} {len(group['sources'])} 份文件" for group in groups))
    if not args.check_only:
        print(f"Origin 工程：{run_groups(groups, base / config['output_project'], overwrite=args.overwrite)}")


if __name__ == "__main__":
    main()
