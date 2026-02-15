"""Parse Windows .reg files into a structure keyed by full key path and value name.

Reads a Windows Registry Editor (.reg) text file and produces a nested dict:
``result[full_key_path][value_name] = decoded_value``. Only ``dword`` and
``hex(1)`` value types are decoded (to int and UTF-16LE string respectively);
other types are ignored. File encoding is detected from BOM: UTF-16-LE
(``\\xff\\xfe``), UTF-16-BE (``\\xfe\\xff``), or UTF-8 if no BOM.
"""

import re
from pathlib import Path
from typing import Any

from putty_export.decoders import decode_dword, decode_hex_string

# Match key line: [\Software\SimonTatham\PuTTY\Sessions\SessionName]
KEY_LINE = re.compile(r"^\[(.*)\]$")
# Match value line: "Name"=dword:00000001 or "Name"=hex(1):00,00,...
VALUE_LINE = re.compile(r'^"([^"]+)"=(dword|hex\(1\)):(.+)$')


def parse_reg_file(path: str | Path) -> dict[str, dict[str, Any]]:
    """Parse a .reg file and return a nested dict of key paths to value names to decoded values.

    :param path: Path to the .reg file (string or pathlib.Path).
    :type path: str | Path
    :returns: Nested dict: ``result[full_key_path][value_name]`` is the decoded value (int for
        ``dword``, str for ``hex(1)``).
    :rtype: dict[str, dict[str, Any]]
    :raises OSError: If the file cannot be opened or read (e.g. file not found, permission error).
    """
    path = Path(path)
    result: dict[str, dict[str, Any]] = {}
    current_key: str | None = None

    with open(path, "rb") as f:
        first = f.read(2)
        if first == b"\xff\xfe":
            encoding = "utf-16-le"
        elif first == b"\xfe\xff":
            encoding = "utf-16"
        else:
            encoding = "utf-8"
            f.seek(0)

    with open(path, encoding=encoding, errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            key_m = KEY_LINE.match(line)
            if key_m:
                current_key = key_m.group(1).strip()
                if current_key and current_key not in result:
                    result[current_key] = {}
                continue

            if current_key is None:
                continue

            value_m = VALUE_LINE.match(line)
            if value_m:
                name, vtype, raw_value = value_m.group(1), value_m.group(2), value_m.group(3)
                if vtype == "dword":
                    result[current_key][name] = decode_dword(raw_value)
                elif vtype == "hex(1)":
                    result[current_key][name] = decode_hex_string(raw_value)

    return result
