"""Decode Windows .reg value types: hex(1) UTF-16LE strings and dword integers."""

import re


def decode_hex_string(raw: str) -> str:
    """
    Decode a hex(1) registry value (UTF-16LE) to a string.
    Strips trailing null terminator. Returns empty string on invalid/empty input.
    """
    if not raw or not raw.strip():
        return ""
    raw = raw.strip()
    parts = [p.strip() for p in re.split(r"[\s,]+", raw) if p.strip()]
    try:
        bytes_list = []
        for part in parts:
            if len(part) > 2:
                continue
            b = int(part, 16)
            if 0 <= b <= 255:
                bytes_list.append(b)
            else:
                return ""
        if not bytes_list:
            return ""
        data = bytes(bytes_list)
        s = data.decode("utf-16-le", errors="replace").rstrip("\x00")
        return s
    except (ValueError, UnicodeDecodeError):
        return ""


def decode_dword(raw: str) -> int:
    """
    Decode a dword registry value (8 hex digits) to an integer.
    Returns 0 on invalid/empty input.
    """
    if not raw or not raw.strip():
        return 0
    raw = raw.strip()
    m = re.match(r"^([0-9a-fA-F]{1,8})$", raw)
    if not m:
        return 0
    try:
        return int(m.group(1), 16)
    except ValueError:
        return 0
