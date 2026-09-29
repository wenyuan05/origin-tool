"""Create an editable Origin project from selected CSV/TXT columns via external Python."""

import csv
import json
import math
from pathlib import Path

from table_text import iter_table_rows, read_metadata, validate_headers


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "plot_config.json"


def selected_columns(config):
    """Validate one X and any nonzero number of Y columns on either side."""
    if not isinstance(config["x"], str) or not config["x"].strip():
        raise ValueError("配置 x 必须是一个非空列名。")
    for key in ("left_y", "right_y"):
        if not isinstance(config[key], list) or not all(
            isinstance(name, str) and name.strip() for name in config[key]
        ):
            raise ValueError(f"配置 {key} 必须是列名列表，可以为空。")
    if not config["left_y"] and not config["right_y"]:
        raise ValueError("左 Y 和右 Y 至少需要选择一列。")
    names = [config["x"], *config["left_y"], *config["right_y"]]
    if len(names) != len(set(names)):
        raise ValueError("X、左 Y、右 Y 的列名不能重复。")
    return names


def load_config(config_path=CONFIG_FILE):
    config_path = Path(config_path).resolve()
    with config_path.open("r", encoding="utf-8-sig") as handle:
        config = json.load(handle)
    base = config_path.parent
    required = ("x", "left_y", "right_y", "output_project")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"配置缺少字段：{', '.join(missing)}")

    for key in ("output_project",):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f"配置 {key} 必须是非空文字。")
    selected_columns(config)
    files = config.get("data_files", [config["data_file"]] if "data_file" in config else None)
    if not isinstance(files, list) or not files or not all(isinstance(p, str) and p.strip() for p in files):
        raise ValueError("配置 data_files 必须是至少包含一个文件路径的列表，或提供 data_file。")
    config["data_files"] = [(base / p).resolve() for p in files]
    if len(config["data_files"]) != len(set(config["data_files"])):
        raise ValueError("数据文件不能重复。")
    config["data_file"] = config["data_files"][0]
    config["output_project"] = (base / config["output_project"]).resolve()
    if config["output_project"].suffix.lower() != ".opju":
        raise ValueError("output_project 必须以 .opju 结尾。")
    config["export_png"] = config.get("export_png", False)
    if not isinstance(config["export_png"], bool):
        raise ValueError("export_png 必须是 true 或 false。")
    if config["export_png"]:
        output_png = config.get("output_png", str(config["output_project"].with_suffix(".png")))
        if not isinstance(output_png, str) or not output_png.strip():
            raise ValueError("output_png 必须是非空文字。")
        config["output_png"] = (base / output_png).resolve()
        if config["output_png"].suffix.lower() != ".png":
            raise ValueError("output_png 必须以 .png 结尾。")
    config["kind"] = config.get("kind", "line+symbol")
    if config["kind"] not in {"scatter", "line", "line+symbol"}:
        raise ValueError("kind 只能是 scatter、line 或 line+symbol。")
    config["encoding"] = config.get("encoding", "utf-8-sig")
    config["plot_mode"] = config.get("plot_mode", "overlay")
    if config["plot_mode"] not in {"overlay", "separate"}:
        raise ValueError("plot_mode 只能是 overlay 或 separate。")
    return config


def read_selected(config, path=None):
    """Read only configured columns; unrelated instrument columns may contain text."""
    path = Path(path or config["data_file"])
    if not path.is_file():
        raise FileNotFoundError(f"找不到数据文件：{path}")
    names = selected_columns(config)
    values = {name: [] for name in names}
    with path.open("r", encoding=config["encoding"], newline="") as handle:
        rows = iter_table_rows(handle)
        _, headers = next(rows, (0, []))
        validate_headers(headers)
        missing = [name for name in names if name not in headers]
        if missing:
            raise ValueError(f"数据文件缺少列 {missing}；现有列：{headers}")
        column_indices = {name: headers.index(name) for name in names}
        for row_number, row in rows:
            if len(row) > len(headers):
                raise ValueError(f"第 {row_number} 行比表头多出字段。")
            for name in names:
                try:
                    value = float(row[column_indices[name]])
                except (IndexError, TypeError, ValueError) as exc:
                    raise ValueError(f"第 {row_number} 行的 {name} 为空或不是数字。") from exc
                if not math.isfinite(value):
                    raise ValueError(f"第 {row_number} 行的 {name} 必须是有限数字。")
                values[name].append(value)
    if len(values[config["x"]]) < 2:
        raise ValueError("至少需要两行有效数据。")
    return values


def read_sources(config):
    """Read each source independently so X grids need not match."""
    files = config["data_files"] if "data_files" in config else [config["data_file"]]
    if not files:
        raise ValueError("至少需要一个数据文件。")
    sources = []
    seen = set()
    for path in map(Path, files):
        path = path.resolve()
        if path in seen:
            raise ValueError(f"数据文件重复：{path}")
        seen.add(path)
        try:
            values = read_selected(config, path)
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            raise ValueError(f"{path.name}：{exc}") from exc
        sources.append({"path": path, "label": path.stem, "metadata": read_metadata(path, config["encoding"]), "values": values})
    labels = [source["label"] for source in sources]
    for index, source in enumerate(sources):
        if labels.count(source["label"]) > 1:
            source["label"] = f"{source['label']} ({index + 1})"
    return sources


def plot(config, values, op, worksheet=None):
    """Populate an Origin workbook and graph in the supplied automation session."""
    selected_columns(config)
    x_name = config["x"]
    y_names = [*config["left_y"], *config["right_y"]]
    # op.new() usually provides an empty Book1; reuse it in the saved project.
    worksheet = worksheet or op.find_sheet() or op.new_sheet()
    worksheet.from_list(0, values[x_name], lname=x_name, axis="X")
    for col_index, name in enumerate(y_names, start=1):
        worksheet.from_list(col_index, values[name], lname=name, axis="Y")

    graph = op.new_graph(template="scatter")
    left_layer = graph[0]
    plot_type = {"scatter": "s", "line": "l", "line+symbol": "y"}[config["kind"]]
    legend_entries = []
    left_colors = ("#2463A7", "#1B8A92", "#624AA0", "#386D43")
    right_colors = ("#D05B2C", "#B38A19", "#BB3F68", "#8A5B3C")
    left_layer.axis("x").title = x_name
    if config["left_y"]:
        for plot_index, name in enumerate(config["left_y"], start=1):
            curve = left_layer.add_plot(worksheet, coly=plot_index, colx=0, type=plot_type)
            curve.color = left_colors[(plot_index - 1) % len(left_colors)]
            legend_entries.append(f"\\l(1.{plot_index}) {name} (左 Y)")
        left_layer.axis("y").title = ", ".join(config["left_y"])

    if config["right_y"] and config["left_y"]:
        right_layer = graph.add_layer(2)  # Right Y; X linked 1:1 to layer 1.
        if right_layer is None:
            raise RuntimeError("Origin 未能创建右 Y 轴图层。")
        right_start = 1 + len(config["left_y"])
        for plot_index, name in enumerate(config["right_y"], start=1):
            col_index = right_start + plot_index - 1
            curve = right_layer.add_plot(worksheet, coly=col_index, colx=0, type=plot_type)
            curve.color = right_colors[(plot_index - 1) % len(right_colors)]
            legend_entries.append(f"\\l(2.{plot_index}) {name} (右 Y)")
        right_layer.axis("y2").title = ", ".join(config["right_y"])
        left_layer.rescale()
        right_layer.rescale()
    elif config["right_y"]:
        for plot_index, name in enumerate(config["right_y"], start=1):
            curve = left_layer.add_plot(worksheet, coly=plot_index, colx=0, type=plot_type)
            curve.color = right_colors[(plot_index - 1) % len(right_colors)]
            legend_entries.append(f"\\l(1.{plot_index}) {name} (右 Y)")
        # Same scale, shown only on the right when there is no left-Y series.
        left_layer.set_int("y.showAxes", 2)
        left_layer.set_int("y.showLabels", 2)
        left_layer.axis("y2").title = ", ".join(config["right_y"])
        left_layer.rescale()
    else:
        left_layer.rescale()

    legend = left_layer.label("Legend")
    if legend:
        legend.text = "\n".join(legend_entries)
    return graph


def plot_sources(config, sources, op):
    """Put every source in its own workbook and create overlay or separate graphs."""
    notes = [f"{source['label']}\n" + "\n".join(source.get("metadata", [])) for source in sources]
    if any(source.get("metadata") for source in sources):
        note = op.new_notes("Source_Info")
        if note is None:
            raise RuntimeError("Origin 未能保存数据源测量信息。")
        note.text = "\n\n".join(notes)
    if len(sources) == 1:
        return [plot(config, sources[0]["values"], op)]
    sheets = []
    names = [config["x"], *config["left_y"], *config["right_y"]]
    for index, source in enumerate(sources):
        sheet = (op.find_sheet() or op.new_sheet()) if index == 0 else op.new_sheet()
        if sheet is None:
            raise RuntimeError(f"Origin 未能创建数据表：{source['label']}")
        sheet.get_book().lname = source["label"]
        for column, name in enumerate(names):
            sheet.from_list(column, source["values"][name], lname=name, axis="X" if column == 0 else "Y")
        sheets.append(sheet)
    if config.get("plot_mode", "overlay") == "separate":
        graphs = []
        for source, sheet in zip(sources, sheets):
            graph = plot(config, source["values"], op, worksheet=sheet)
            graph.lname = source["label"]
            graphs.append(graph)
        return graphs

    graph = op.new_graph(template="scatter")
    graph.lname = "多器件叠加对比"
    left_layer = graph[0]
    right_layer = graph.add_layer(2) if config["left_y"] and config["right_y"] else None
    if config["left_y"] and config["right_y"] and right_layer is None:
        raise RuntimeError("Origin 未能创建右 Y 轴图层。")
    plot_type = {"scatter": "s", "line": "l", "line+symbol": "y"}[config["kind"]]
    left_layer.axis("x").title = config["x"]
    legend_entries = []
    left_count = right_count = 0
    colors = ("#2463A7", "#D05B2C", "#1B8A92", "#B38A19", "#624AA0", "#BB3F68")
    for source_index, (source, sheet) in enumerate(zip(sources, sheets)):
        for column, name in enumerate(config["left_y"], start=1):
            left_count += 1
            curve = left_layer.add_plot(sheet, coly=column, colx=0, type=plot_type)
            curve.color = colors[source_index % len(colors)]
            legend_entries.append(f"\\l(1.{left_count}) {source['label']} — {name} (左 Y)")
        for column, name in enumerate(config["right_y"], start=1 + len(config["left_y"])):
            layer = right_layer or left_layer
            right_count += 1
            curve = layer.add_plot(sheet, coly=column, colx=0, type=plot_type)
            curve.color = colors[source_index % len(colors)]
            layer_index = 2 if right_layer else 1
            plot_index = right_count if right_layer else left_count + right_count
            legend_entries.append(f"\\l({layer_index}.{plot_index}) {source['label']} — {name} (右 Y)")
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
    return [graph]


def run_external(config, values, overwrite=False, op=None):
    """Use a separate Origin automation session and optionally export PNG."""
    project_path = Path(config["output_project"]).resolve()
    export_png = config.get("export_png", False)
    if not isinstance(export_png, bool):
        raise ValueError("export_png 必须是 true 或 false。")
    png_path = None
    if export_png:
        png_path = Path(config.get("output_png", project_path.with_suffix(".png"))).resolve()
    if project_path.suffix.lower() != ".opju" or (png_path and png_path.suffix.lower() != ".png"):
        raise ValueError("输出路径扩展名不正确。")
    multi = isinstance(values, list)
    sources = values if multi else [{"label": Path(config["data_file"]).stem, "values": values}]
    png_paths = []
    if png_path:
        if len(sources) > 1 and config.get("plot_mode", "overlay") == "separate":
            png_paths = [png_path.with_name(f"{png_path.stem}_{i + 1:02d}{png_path.suffix}") for i in range(len(sources))]
        else:
            png_paths = [png_path]
    output_paths = (project_path, *png_paths)
    existing = [str(path) for path in output_paths if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("输出文件已存在：" + "、".join(existing))

    if op is None:
        try:
            import originpro as op
        except ImportError as exc:
            raise RuntimeError(
                "外部 Python 缺少 originpro；请按 README 使用项目虚拟环境安装依赖。"
            ) from exc
    if not getattr(op, "oext", False):
        raise RuntimeError("请从普通 Python 运行本脚本；这里需要外部版 originpro。")

    project_path.parent.mkdir(parents=True, exist_ok=True)
    for path in png_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # No op.attach(): the automation session stays separate from a user's open project.
        op.set_show(False)
        op.new()
        graphs = plot_sources(config, sources, op) if multi else [plot(config, values, op)]
        op.wait()
        if not op.save(str(project_path)) or not project_path.is_file() or project_path.stat().st_size == 0:
            raise RuntimeError("Origin 未能保存有效的 .opju 工程文件。")
        for graph, path in zip(graphs, png_paths):
            exported = graph.save_fig(str(path), type="png", width=1200)
            if not exported or not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"工程已保存到 {project_path}，但 PNG 导出失败：{path}")
    finally:
        op.exit()

    print(f"已绘制 {len(sources)} 个数据源；X={config['x']}；左 Y={config['left_y']}；右 Y={config['right_y']}")
    print(f"Origin 工程：{project_path}")
    for path in png_paths:
        print(f"PNG：{path}")
    return project_path, png_paths


def main():
    import argparse

    parser = argparse.ArgumentParser(description="从 CSV/TXT 生成含工作表和图窗的 Origin .opju 工程")
    parser.add_argument("--config", type=Path, default=CONFIG_FILE, help="JSON 配置文件")
    parser.add_argument("--check-only", action="store_true", help="只检查数据和列配置，不启动 Origin")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出文件")
    args = parser.parse_args()
    config = load_config(args.config)
    values = read_sources(config)
    if args.check_only:
        print(f"检查通过：{len(values)} 个数据源；" + "；".join(f"{item['path'].name} {len(item['values'][config['x']])} 行" for item in values))
    else:
        run_external(config, values, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
