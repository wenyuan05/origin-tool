"""Read simple header-based CSV and delimited TXT tables."""

import csv
from itertools import chain
from pathlib import Path


def iter_table_rows(handle):
    """Yield (physical line number, fields), detecting the first line's separator."""
    first_line = handle.readline()
    if not first_line:
        return
    delimiters = ("\t", ",", ";")
    field_counts = [len(next(csv.reader((first_line,), delimiter=mark))) for mark in delimiters]
    best = max(range(len(delimiters)), key=field_counts.__getitem__)
    delimiter = delimiters[best] if field_counts[best] > 1 else None
    lines = chain((first_line,), handle)
    if delimiter is None:
        for line_number, line in enumerate(lines, start=1):
            fields = line.split()
            if fields:
                yield line_number, fields
    else:
        reader = csv.reader(lines, delimiter=delimiter)
        for fields in reader:
            if fields:
                yield reader.line_num, fields


def validate_headers(headers):
    if not headers or any(not name.strip() for name in headers) or len(headers) != len(set(headers)):
        raise ValueError("数据文件首行必须是非空且不重复的列名。")
    return headers


def read_headers(path: Path, encoding="utf-8-sig"):
    with Path(path).open("r", encoding=encoding, newline="") as handle:
        _, headers = next(iter_table_rows(handle), (0, []))
    return validate_headers(headers)
