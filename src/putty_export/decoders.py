"""Decode Windows .reg value types into Python values.

This module handles the two value types produced by the PuTTY registry export:
``hex(1)`` (UTF-16LE encoded strings) and ``dword`` (32-bit integers). Other
registry value types are not used by the parser.
"""

import re


def decode_hex_string(raw: str) -> str:
    """Decode a ``hex(1)`` registry value (UTF-16LE) to a string.

    The raw value is a comma- or space-separated list of hex bytes (e.g.
    ``73,00,68,00,00,00``). Bytes are decoded as UTF-16LE and a trailing
    null terminator is stripped. Invalid or empty input yields an empty string.

    :param raw: Comma- or space-separated hex bytes string from a .reg file.
    :type raw: str
    :returns: Decoded string, or empty string if input is invalid or empty.
    :rtype: str
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
    """Decode a ``dword`` registry value to an integer.

    The raw value is a hexadecimal string of up to 8 digits (e.g. ``00000016``
    for 22). Invalid or empty input yields 0.

    :param raw: Hex string (up to 8 digits) from a .reg file.
    :type raw: str
    :returns: Decoded integer, or 0 if input is invalid or empty.
    :rtype: int
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
