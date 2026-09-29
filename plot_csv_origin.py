"""Plot selected numeric CSV columns in Origin's embedded Python."""

import argparse
import csv
import math
from pathlib import Path


# 第一次试用 Origin 时，只需修改下面三项。
DEFAULT_FILE = Path(__file__).with_name("sample_measurements.csv")
DEFAULT_X = "time_s"
DEFAULT_Y = "temperature_C"


def read_xy(file_path: Path, x_column: str, y_column: str):
    """Read and validate two numeric columns before creating Origin objects."""
    if x_column == y_column:
        raise ValueError("X 列与 Y 列必须不同。")
    if not file_path.is_file():
        raise FileNotFoundError(f"找不到数据文件：{file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers or len(headers) != len(set(headers)):
            raise ValueError("CSV 表头为空或包含重名列。")
        missing = [name for name in (x_column, y_column) if name not in headers]
        if missing:
            raise ValueError(f"找不到列 {missing}；可选列：{headers}")

        x_values, y_values = [], []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"第 {row_number} 行比表头多出字段。")
            try:
                x_value = float(row[x_column])
                y_value = float(row[y_column])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"第 {row_number} 行的 X/Y 值为空或不是数字。") from exc
            if not (math.isfinite(x_value) and math.isfinite(y_value)):
                raise ValueError(f"第 {row_number} 行的 X/Y 值必须是有限数字。")
            x_values.append(x_value)
            y_values.append(y_value)

    if len(x_values) < 2:
        raise ValueError("至少需要两行有效数据。")
    return x_values, y_values


def list_columns(file_path: Path):
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        headers = next(csv.reader(handle), [])
    if not headers:
        raise ValueError("CSV 文件没有表头。")
    return headers


def plot_csv(file_path, x_column, y_column, kind="scatter", output_path=None):
    """Create an Origin worksheet and XY graph, then optionally export PNG."""
    file_path = Path(file_path).expanduser().resolve()
    x_values, y_values = read_xy(file_path, x_column, y_column)
    if kind not in {"scatter", "line", "line+symbol"}:
        raise ValueError("kind 只能是 scatter、line 或 line+symbol。")

    try:
        import originpro as op
    except ImportError as exc:
        raise RuntimeError("绘图需要在 Origin 的内置 Python 中运行，并提供 originpro。") from exc

    worksheet = op.new_sheet()
    worksheet.from_list(0, x_values, lname=x_column, axis="X")
    worksheet.from_list(1, y_values, lname=y_column, axis="Y")

    graph = op.new_graph(template="scatter")
    layer = graph[0]
    plot_type = {"scatter": "s", "line": "l", "line+symbol": "y"}[kind]
    layer.add_plot(worksheet, coly=1, colx=0, type=plot_type)
    layer.axis("x").title = x_column
    layer.axis("y").title = y_column
    layer.rescale()

    if output_path is not None:
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        exported = graph.save_fig(str(output_path), type="png", width=1200)
        if not exported:
            raise RuntimeError("Origin 已绘图，但 PNG 导出失败。")
        print(f"PNG：{exported}")
    print(f"已在 Origin 中绘制 {len(x_values)} 个点：{y_column} vs {x_column}")
    return graph


def main():
    parser = argparse.ArgumentParser(description="选择 CSV 的 X/Y 数值列并在 Origin 中绘图")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="CSV 文件路径")
    parser.add_argument("--x", default=DEFAULT_X, help="X 列表头")
    parser.add_argument("--y", default=DEFAULT_Y, help="Y 列表头")
    parser.add_argument("--kind", choices=["scatter", "line", "line+symbol"], default="scatter")
    parser.add_argument("--output", type=Path, help="可选的 PNG 输出路径；不指定则不导出")
    parser.add_argument("--list-columns", action="store_true", help="只列出可选列，不启动 Origin")
    parser.add_argument("--check-only", action="store_true", help="只检查 X/Y 数据，不启动 Origin")
    args = parser.parse_args()

    if args.list_columns:
        print("可选列：" + ", ".join(list_columns(args.file)))
        return
    if args.check_only:
        x_values, _ = read_xy(args.file, args.x, args.y)
        print(f"检查通过：{len(x_values)} 个点；X={args.x}，Y={args.y}")
        return

    plot_csv(args.file, args.x, args.y, args.kind, args.output)


if __name__ == "__main__":
    main()
