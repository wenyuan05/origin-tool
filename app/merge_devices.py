"""Parse complete instrument tables and infer device names from filenames."""

import csv
import math
import re
from pathlib import Path

from table_text import iter_table_rows, read_metadata, validate_headers


TYPE_SUFFIX = re.compile(
    r"(?:[-_ ]+(?:spectrum|spectra|electrical|electric|jv|iv|el|pl|luminance|current|voltage|efficiency|eqe))+$",
    re.IGNORECASE,
)


def infer_device_name(path):
    """Conservatively remove common trailing measurement names."""
    stem = Path(path).stem.strip()
    return TYPE_SUFFIX.sub("", stem).strip("-_ ") or stem


def read_full_table(path, encoding="utf-8-sig"):
    """Read all columns and keep the file's own row count and preamble."""
    path = Path(path)
    with path.open("r", encoding=encoding, newline="") as handle:
        rows = iter_table_rows(handle)
        _, headers = next(rows, (0, []))
        validate_headers(headers)
        columns = [[] for _ in headers]
        for line_number, row in rows:
            if len(row) != len(headers):
                raise ValueError(f"{path.name} 第 {line_number} 行有 {len(row)} 列，应为 {len(headers)} 列。")
            for column, value in zip(columns, row):
                column.append(value.strip())
    if not columns or len(columns[0]) < 2:
        raise ValueError(f"{path.name} 至少需要两行数据。")
    typed = []
    for column in columns:
        try:
            typed.append([float(value) if value else math.nan for value in column])
        except ValueError:
            typed.append(column)
    return headers, typed, read_metadata(path, encoding)
