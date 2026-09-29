"""Read simple header-based CSV and delimited TXT tables."""

import csv
from itertools import chain
from pathlib import Path


METADATA_PREFIXES = ("Measurement Time:", "Device Area:")


def read_metadata(path: Path, encoding="utf-8-sig"):
    """Return recognized preamble lines without treating them as table rows."""
    lines = []
    with Path(path).open("r", encoding=encoding, newline="") as handle:
        for line in handle:
            if not line.lstrip().startswith(METADATA_PREFIXES):
                break
            lines.append(line.strip())
    return lines


def iter_table_rows(handle):
    """Yield (physical line number, fields), skipping known instrument metadata."""
    offset = 0
    first_line = handle.readline()
    while first_line and first_line.lstrip().startswith(METADATA_PREFIXES):
        offset += 1
        first_line = handle.readline()
    if not first_line:
        return
    delimiters = ("\t", ",", ";")
    field_counts = [len(next(csv.reader((first_line,), delimiter=mark))) for mark in delimiters]
    best = max(range(len(delimiters)), key=field_counts.__getitem__)
    delimiter = delimiters[best] if field_counts[best] > 1 else None
    lines = chain((first_line,), handle)
    if delimiter is None:
        for line_number, line in enumerate(lines, start=offset + 1):
            fields = line.split()
            if fields:
                yield line_number, fields
    else:
        reader = csv.reader(lines, delimiter=delimiter)
        for fields in reader:
            if fields:
                yield offset + reader.line_num, fields


def validate_headers(headers):
    if not headers or any(not name.strip() for name in headers) or len(headers) != len(set(headers)):
        raise ValueError("数据文件首行必须是非空且不重复的列名。")
    return headers


def read_headers(path: Path, encoding="utf-8-sig"):
    with Path(path).open("r", encoding=encoding, newline="") as handle:
        _, headers = next(iter_table_rows(handle), (0, []))
    return validate_headers(headers)
