"""Detect headers and read CSV/TXT tables with arbitrary preamble lines."""

import csv
from pathlib import Path


def split_line(line, delimiter):
    return next(csv.reader((line,), delimiter=delimiter)) if delimiter else line.split()


def is_numeric(value):
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def detect_table(lines):
    """Find a labelled row followed by a matching numeric data row."""
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        candidates = []
        for delimiter in ("\t", ",", ";", None):
            fields = [field.strip() for field in split_line(line, delimiter)]
            if len(fields) < 2 or any(not field for field in fields) or len(fields) != len(set(fields)):
                continue
            if all(is_numeric(field) for field in fields):
                continue
            next_index = next((j for j in range(index + 1, len(lines)) if lines[j].strip()), None)
            if next_index is None:
                continue
            sample = split_line(lines[next_index], delimiter)
            if len(sample) != len(fields) or sum(is_numeric(cell) for cell in sample) < 2:
                continue
            candidates.append((delimiter, fields))
        if candidates:
            candidates.sort(key=lambda item: item[0] is None)
            delimiter, headers = candidates[0]
            return index, delimiter, headers
    raise ValueError("未能自动识别表头。请检查文件是否包含至少两列的列名，且后面有列数一致的数值数据行。")


def read_table_info(path: Path, encoding="utf-8-sig"):
    with Path(path).open("r", encoding=encoding, newline="") as handle:
        lines = handle.readlines()
    index, delimiter, headers = detect_table(lines)
    return lines, index, delimiter, validate_headers(headers)


def read_metadata(path: Path, encoding="utf-8-sig"):
    """Keep nonblank preamble lines for traceability, without local paths."""
    lines, index, _, _ = read_table_info(path, encoding)
    return [line.strip() for line in lines[:index] if line.strip()]


def iter_table_rows(handle):
    """Yield (physical line number, fields), starting at a detected header."""
    lines = handle.readlines()
    index, delimiter, _ = detect_table(lines)
    if delimiter is None:
        for line_number, line in enumerate(lines[index:], start=index + 1):
            fields = line.split()
            if fields:
                yield line_number, fields
    else:
        reader = csv.reader(lines[index:], delimiter=delimiter)
        for fields in reader:
            if any(field.strip() for field in fields):
                yield index + reader.line_num, fields


def validate_headers(headers):
    if not headers or any(not name.strip() for name in headers) or len(headers) != len(set(headers)):
        raise ValueError("表头必须包含非空且不重复的列名。")
    return headers


def read_headers(path: Path, encoding="utf-8-sig"):
    _, _, _, headers = read_table_info(path, encoding)
    return headers
